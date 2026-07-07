from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from banco import Banco
from logger import Logger
from sucursales_manager import SucursalesManager
from cuenta_prototype import CuentaPrototypeRegistry
from cuenta_builder import CuentaBuilder
from transaccion import Transaccion
from operacion_facade import OperacionFacade
from usuario_facade import UsuarioFacade
from memento_cuenta import GestorMementos
from validacion_chain import CadenaValidacionFactory
from reporte_template import ReporteProducer

# ── FASE 2 — Persistencia (Supabase) ──────────────────────────────────────────
import repositorio
import estado_inicial
from config_banco import ConfigBanco

# =============================================================================
# FASE 1 — CONFIGURACIÓN SEGURA (variables de entorno)
#
# Todo funciona exactamente igual que antes SI NO defines estas variables
# de entorno (comportamiento por defecto = igual al original, para no romper
# nada en desarrollo). En producción, defínelas para blindar la API:
#
#   FLASK_DEBUG=0            → apaga el debugger de Werkzeug (RCE si queda en 1)
#   CORS_ORIGINS=https://tu-frontend.com,https://otro.com
#   API_KEY=una-clave-larga-y-aleatoria
#
# =============================================================================

FLASK_DEBUG  = os.environ.get("FLASK_DEBUG", "0") == "1"
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
API_KEY      = os.environ.get("API_KEY", "").strip()

app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS.split(",") if CORS_ORIGINS != "*" else "*")

# =============================================================================
# FASE 4.3 — RATE LIMITING (protección adicional contra abuso)
#
# Independiente de la autenticación (@requiere_api_key / futuro @requiere_login
# de Fase 3): limita cuántas veces se puede llamar a un endpoint sensible desde
# la misma IP en una ventana de tiempo, aunque la clave/token sea válido.
#
# Sin límites globales por defecto — solo se aplican explícitamente con
# @limiter.limit(...) en los endpoints que mueven dinero o eliminan datos,
# para no afectar el resto de la API (lectura de reportes, listados, etc.).
# =============================================================================
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.errorhandler(429)
def limite_excedido(e):
    return jsonify({
        "ok":      False,
        "mensaje": "Demasiadas solicitudes. Intenta de nuevo en unos momentos.",
        "data":    None,
    }), 429


def requiere_api_key(func):
    """
    Protege endpoints sensibles (dinero, eliminación, undo/redo).
    Si no se define API_KEY en el entorno, NO exige nada (modo dev,
    compatibilidad total con el comportamiento original).
    Si API_KEY está definida, exige header:  X-API-Key: <API_KEY>
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not API_KEY:
            return func(*args, **kwargs)
        clave_recibida = request.headers.get("X-API-Key", "")
        if clave_recibida != API_KEY:
            return jsonify({
                "ok": False,
                "mensaje": "No autorizado. Header 'X-API-Key' inválido o ausente.",
                "data": None
            }), 401
        return func(*args, **kwargs)
    return wrapper

# ── Estado global del servidor ────────────────────────────────────────────────
logger         = Logger.get_instancia()
banco          = Banco()
op_facade      = OperacionFacade(banco)
usuario_facade = UsuarioFacade(banco)

logger.log("¡Sistema Bancario Core iniciado vía API!")

# ── FASE 2: bootstrap de estado (reconstruye desde Supabase o siembra) ────────
from estado_cuenta import EstadoCuentaProducer
from command_transaccion import (
    ComandoDeposito, ComandoRetiro, ComandoTransferencia, HistorialComandos
)
from prestamo_strategy import (
    EstrategiaInteresProducer, GestorPrestamos, Prestamo
)

estado_inicial.inicializar_estado(banco, usuario_facade)

# Mapa {nombre_sucursal: id_supabase}, disponible aunque la persistencia
# esté desactivada (queda {} y las llamadas a repositorio.* son no-ops).
SUCURSAL_IDS = repositorio.sincronizar_sucursales(ConfigBanco.get_instancia().get_sucursales())


def _sucursal_id_de(cuenta):
    """Busca el id de Supabase de la sucursal que contiene esta cuenta."""
    sucursal = next((s for s in banco.sucursales if cuenta in s._cuentas), None)
    return SUCURSAL_IDS.get(sucursal.nombre) if sucursal else None


def _persistir_saldos_de_comando(datos: dict) -> None:
    """
    Sincroniza en Supabase el/los saldo(s) que un undo/redo del patrón
    Command modificó. 'datos' viene de ComandoDeposito/Retiro (una sola
    cuenta) o de ComandoTransferencia (origen + destino).
    """
    if "cuenta" in datos:
        repositorio.actualizar_cuenta(datos["cuenta"], datos["saldo_nuevo"])
    if "origen" in datos:
        repositorio.actualizar_cuenta(datos["origen"], datos["saldo_origen"])
        repositorio.actualizar_cuenta(datos["destino"], datos["saldo_destino"])


# =============================================================================
# HELPER
# =============================================================================

def ok(data=None, mensaje="Operación exitosa"):
    return jsonify({"ok": True, "mensaje": mensaje, "data": data})

def err(mensaje="Error en la operación", code=400):
    return jsonify({"ok": False, "mensaje": mensaje, "data": None}), code


# =============================================================================
# 1. REGISTRAR USUARIO
# =============================================================================
@app.route("/api/usuarios/registrar", methods=["POST"])
def registrar_usuario():
    body = request.get_json(force=True)
    nombre    = body.get("nombre", "").strip()
    documento = body.get("documento", "").strip()
    celular   = body.get("celular", "").strip()
    correo    = body.get("correo", "").strip()

    if not nombre or not documento:
        return err("Nombre y documento son obligatorios.")

    resultado = usuario_facade.registrar_usuario(nombre, documento, celular, correo)
    if resultado is None:
        return err(f"Ya existe un usuario con documento {documento}.")

    repositorio.guardar_usuario(resultado)

    return ok(
        {"nombre": resultado.nombre, "documento": resultado.documento,
         "celular": resultado.celular, "correo": resultado.correo,
         "kyc": resultado.verificado_kyc},
        f"Usuario '{nombre}' registrado exitosamente."
    )


# =============================================================================
# 2. VERIFICAR KYC
# =============================================================================
@app.route("/api/usuarios/kyc", methods=["POST"])
def verificar_kyc():
    body = request.get_json(force=True)
    documento = body.get("documento", "").strip()

    if not documento:
        return err("El documento es obligatorio.")

    resultado = usuario_facade.verificar_kyc(documento)
    if not resultado:
        return err(f"No se encontró usuario con documento {documento}.")

    usuario = banco.buscar_usuario_por_documento(documento)
    repositorio.guardar_usuario(usuario)
    return ok(
        {"nombre": usuario.nombre, "documento": usuario.documento,
         "kyc": usuario.verificado_kyc},
        f"KYC verificado para '{usuario.nombre}'."
    )


# =============================================================================
# 3. CREAR CUENTA
# =============================================================================
@app.route("/api/cuentas/crear", methods=["POST"])
def crear_cuenta():
    body = request.get_json(force=True)
    documento       = body.get("documento", "").strip()
    numero          = body.get("numero", "").strip()
    tipo            = body.get("tipo", "corriente").strip()
    saldo_inicial   = float(body.get("saldo_inicial", 0))
    indice_sucursal = int(body.get("indice_sucursal", 1))

    if not documento or not numero:
        return err("Documento y número de cuenta son obligatorios.")

    cuenta = usuario_facade.crear_cuenta(documento, numero, tipo, saldo_inicial, indice_sucursal)
    if cuenta is None:
        return err("No se pudo crear la cuenta. Verifique KYC, duplicados y datos.")

    repositorio.guardar_cuenta(cuenta, documento, _sucursal_id_de(cuenta))

    return ok(
        {"numero": cuenta.numero, "tipo": cuenta.tipo, "saldo": cuenta.saldo},
        f"Cuenta {numero} ({tipo}) creada exitosamente."
    )


# =============================================================================
# 4. DEPOSITAR
# =============================================================================
@app.route("/api/operaciones/depositar", methods=["POST"])
@requiere_api_key
def depositar():
    body   = request.get_json(force=True)
    numero = body.get("numero_cuenta", "").strip()
    monto  = float(body.get("monto", 0))
    canal  = body.get("canal", "web").strip()

    if not numero or monto <= 0:
        return err("Número de cuenta y monto positivo son obligatorios.")

    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    # ── COMMAND: encapsular y registrar en el Invoker ─────────────────────────
    cmd       = ComandoDeposito(cuenta, monto, canal)
    resultado = HistorialComandos.get_instancia().ejecutar(cmd)
    if not resultado["ok"]:
        return err(resultado["mensaje"])

    repositorio.actualizar_cuenta(numero, cuenta.saldo)
    repositorio.guardar_transaccion("deposito", monto, canal, cuenta_origen=numero)

    return ok(
        {"numero": numero, "saldo_actual": cuenta.saldo,
         "estado_invoker": HistorialComandos.get_instancia().get_estado()},
        f"Depósito de ${monto:,.2f} realizado exitosamente."
    )


# =============================================================================
# 5. RETIRAR
# =============================================================================
@app.route("/api/operaciones/retirar", methods=["POST"])
@requiere_api_key
@limiter.limit("20 per minute")
def retirar():
    body   = request.get_json(force=True)
    numero = body.get("numero_cuenta", "").strip()
    monto  = float(body.get("monto", 0))
    canal  = body.get("canal", "cajero").strip()

    if not numero or monto <= 0:
        return err("Número de cuenta y monto positivo son obligatorios.")

    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    # ── COMMAND: encapsular y registrar en el Invoker ─────────────────────────
    cmd       = ComandoRetiro(cuenta, monto, canal)
    resultado = HistorialComandos.get_instancia().ejecutar(cmd)
    if not resultado["ok"]:
        return err(resultado["mensaje"])

    repositorio.actualizar_cuenta(numero, cuenta.saldo)
    repositorio.guardar_transaccion("retiro", monto, canal, cuenta_origen=numero)

    return ok(
        {"numero": numero, "saldo_actual": cuenta.saldo,
         "estado_invoker": HistorialComandos.get_instancia().get_estado()},
        f"Retiro de ${monto:,.2f} realizado exitosamente."
    )


# =============================================================================
# 6. TRANSFERIR
# =============================================================================
@app.route("/api/operaciones/transferir", methods=["POST"])
@requiere_api_key
@limiter.limit("20 per minute")
def transferir():
    body    = request.get_json(force=True)
    origen  = body.get("numero_origen", "").strip()
    destino = body.get("numero_destino", "").strip()
    monto   = float(body.get("monto", 0))
    canal   = body.get("canal", "web").strip()

    if not origen or not destino or monto <= 0:
        return err("Cuentas origen, destino y monto positivo son obligatorios.")

    c_orig = banco.buscar_cuenta_por_numero(origen)
    c_dest = banco.buscar_cuenta_por_numero(destino)
    if not c_orig:
        return err(f"Cuenta origen {origen} no encontrada.")
    if not c_dest:
        return err(f"Cuenta destino {destino} no encontrada.")

    # ── COMMAND: encapsular y registrar en el Invoker ─────────────────────────
    cmd       = ComandoTransferencia(c_orig, c_dest, monto, canal)
    resultado = HistorialComandos.get_instancia().ejecutar(cmd)
    if not resultado["ok"]:
        return err(resultado["mensaje"])

    repositorio.actualizar_cuenta(origen, c_orig.saldo)
    repositorio.actualizar_cuenta(destino, c_dest.saldo)
    repositorio.guardar_transaccion(
        "transferencia", monto, canal, cuenta_origen=origen, cuenta_destino=destino
    )

    return ok(
        {
            "origen":  {"numero": origen,  "saldo": c_orig.saldo},
            "destino": {"numero": destino, "saldo": c_dest.saldo},
            "estado_invoker": HistorialComandos.get_instancia().get_estado()
        },
        f"Transferencia de ${monto:,.2f} realizada exitosamente."
    )


# =============================================================================
# 7. CONSULTAR MOVIMIENTOS (historial de cuenta)
# =============================================================================
@app.route("/api/cuentas/movimientos/<numero>", methods=["GET"])
def consultar_movimientos(numero):
    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    return ok({
        "numero": cuenta.numero,
        "tipo": cuenta.tipo,
        "saldo": cuenta.saldo,
        "total_movimientos": len(cuenta.transacciones),
        "movimientos": cuenta.transacciones[-20:]
    }, "Movimientos obtenidos exitosamente.")


# =============================================================================
# 8. CONSULTAR SALDOS TOTALES DE USUARIO
# =============================================================================
@app.route("/api/usuarios/saldos/<documento>", methods=["GET"])
def saldos_usuario(documento):
    usuario = banco.buscar_usuario_por_documento(documento)
    if not usuario:
        return err(f"Usuario con documento {documento} no encontrado.")

    cuentas_data = [
        {"numero": c.numero, "tipo": c.tipo, "saldo": c.get_saldo_total()}
        for c in usuario.cuentas
    ]
    total = sum(c["saldo"] for c in cuentas_data)
    return ok({
        "nombre": usuario.nombre,
        "documento": usuario.documento,
        "cuentas": cuentas_data,
        "total": total
    }, "Saldos obtenidos exitosamente.")


# =============================================================================
# 9. VER TODOS LOS USUARIOS
# =============================================================================
@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    data = []
    for u in banco.usuarios:
        data.append({
            "nombre": u.nombre,
            "documento": u.documento,
            "celular": u.celular,
            "correo": u.correo,
            "kyc": u.verificado_kyc,
            "cuentas": [
                {"numero": c.numero, "tipo": c.tipo, "saldo": c.saldo}
                for c in u.cuentas
            ]
        })
    return ok(data, f"{len(data)} usuario(s) registrados.")


# =============================================================================
# 10. VER SUCURSALES Y CUENTAS
# =============================================================================
@app.route("/api/sucursales", methods=["GET"])
def listar_sucursales():
    manager = SucursalesManager.get_instancia()
    data = []
    for s in manager.sucursales:
        data.append({
            "nombre": s.nombre,
            "saldo_total": s.get_saldo_total(),
            "total_cuentas": len(s.cuentas),
            "cuentas": [
                {"numero": c.numero, "tipo": c.tipo, "saldo": c.saldo}
                for c in s.cuentas
            ]
        })
    return ok(data, "Sucursales obtenidas exitosamente.")


# =============================================================================
# 11. REGISTRAR PROTOTIPO
# =============================================================================
@app.route("/api/prototipos/registrar", methods=["POST"])
@requiere_api_key
def registrar_prototipo():
    body          = request.get_json(force=True)
    numero_cuenta = body.get("numero_cuenta", "").strip()
    nombre_proto  = body.get("nombre_proto", "").strip()

    if not numero_cuenta or not nombre_proto:
        return err("Número de cuenta y nombre del prototipo son obligatorios.")

    cuenta = banco.buscar_cuenta_por_numero(numero_cuenta)
    if not cuenta:
        return err(f"Cuenta {numero_cuenta} no encontrada.")

    try:
        CuentaPrototypeRegistry.registrar(nombre_proto, cuenta)
        return ok(
            {"nombre": nombre_proto, "tipo": cuenta.tipo, "saldo": cuenta.saldo},
            f"Cuenta {numero_cuenta} registrada como prototipo '{nombre_proto}'."
        )
    except ValueError as e:
        return err(str(e))


# =============================================================================
# 12. CLONAR CUENTA DESDE PROTOTIPO
# =============================================================================
@app.route("/api/prototipos/clonar", methods=["POST"])
@requiere_api_key
def clonar_cuenta():
    body          = request.get_json(force=True)
    nombre_proto  = body.get("nombre_proto", "").strip()
    documento     = body.get("documento", "").strip()
    nuevo_numero  = body.get("nuevo_numero", "").strip()
    indice_suc    = int(body.get("indice_sucursal", 1))

    if not nombre_proto or not documento or not nuevo_numero:
        return err("Prototipo, documento de usuario y nuevo número son obligatorios.")

    try:
        cuenta_origen = CuentaPrototypeRegistry.get(nombre_proto)
    except ValueError as e:
        return err(str(e))

    usuario = banco.buscar_usuario_por_documento(documento)
    if not usuario:
        return err(f"Usuario con documento {documento} no encontrado.")
    if not usuario.verificado_kyc:
        return err("El usuario debe tener KYC verificado.")
    if banco.buscar_cuenta_por_numero(nuevo_numero):
        return err(f"El número de cuenta {nuevo_numero} ya existe.")

    sucursales = SucursalesManager.get_instancia().sucursales
    if not (1 <= indice_suc <= len(sucursales)):
        return err(f"Índice de sucursal inválido. Rango: 1-{len(sucursales)}.")

    sucursal = sucursales[indice_suc - 1]

    try:
        cuenta_clonada = (
            CuentaBuilder()
            .numero(nuevo_numero)
            .asociar_usuario(usuario)
            .asociar_sucursal(sucursal)
            .clone_desde(cuenta_origen)
        )
        return ok(
            {
                "numero": cuenta_clonada.numero,
                "tipo": cuenta_clonada.tipo,
                "saldo": cuenta_clonada.saldo,
                "prototipo_origen": nombre_proto
            },
            f"Cuenta {nuevo_numero} clonada exitosamente desde '{nombre_proto}'."
        )
    except ValueError as e:
        return err(str(e))


# =============================================================================
# 13. CONFIGURAR DECORADORES
# =============================================================================
@app.route("/api/decoradores/configurar", methods=["POST"])
@requiere_api_key
def configurar_decoradores():
    body = request.get_json(force=True)
    config = body.get("config", "3")

    configuraciones = {
        "1": ["tiempo"],
        "2": ["auditoria"],
        "3": ["tiempo", "auditoria"],
        "4": ["auditoria", "reintento"],
        "5": ["tiempo", "auditoria", "reintento"],
        "6": [],
    }

    if config not in configuraciones:
        return err("Configuración inválida. Use 1-6.")

    Transaccion.DECORADORES_ACTIVOS = configuraciones[config]
    nuevos = Transaccion.DECORADORES_ACTIVOS
    return ok(
        {"decoradores_activos": nuevos},
        f"Decoradores configurados: {nuevos if nuevos else 'Ninguno (modo directo)'}."
    )

@app.route("/api/decoradores/activos", methods=["GET"])
def obtener_decoradores():
    return ok(
        {"decoradores_activos": Transaccion.DECORADORES_ACTIVOS},
        "Decoradores obtenidos."
    )


# =============================================================================
# 14. TRAZABILIDAD (demostrar Decorator con procesar_sin_bridge)
# =============================================================================
@app.route("/api/decoradores/trazabilidad", methods=["POST"])
def trazabilidad():
    body   = request.get_json(force=True)
    numero = body.get("numero_cuenta", "").strip()
    monto  = float(body.get("monto", 0))
    canal  = body.get("canal", "web").strip()
    tipo   = body.get("tipo", "deposito").strip()

    if not numero or monto <= 0:
        return err("Número de cuenta y monto positivo son obligatorios.")

    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    logs_antes = len(logger.get_logs())
    exito = Transaccion.procesar_sin_bridge(
        cuenta_origen=cuenta, monto=monto, canal=canal, tipo=tipo
    )
    logs_nuevos = logger.get_logs()[logs_antes:]

    return ok(
        {
            "exito": exito,
            "saldo_actual": cuenta.saldo,
            "decoradores_usados": Transaccion.DECORADORES_ACTIVOS,
            "logs_operacion": logs_nuevos
        },
        f"Trazabilidad ejecutada. Resultado: {'EXITOSA' if exito else 'RECHAZADA'}."
    )


# =============================================================================
# 15. ELIMINAR USUARIO
# =============================================================================
@app.route("/api/usuarios/eliminar", methods=["DELETE"])
@requiere_api_key
@limiter.limit("5 per minute")
def eliminar_usuario():
    body      = request.get_json(force=True)
    documento = body.get("documento", "").strip()

    if not documento:
        return err("El documento es obligatorio.")

    usuario = banco.buscar_usuario_por_documento(documento)
    if not usuario:
        return err(f"No se encontró usuario con documento {documento}.")

    info = {
        "nombre": usuario.nombre,
        "cuentas_eliminadas": len(usuario.cuentas)
    }

    resultado = usuario_facade.eliminar_usuario(documento)
    if not resultado:
        return err("No se pudo eliminar el usuario.")

    repositorio.eliminar_usuario(documento)

    return ok(info, f"Usuario '{info['nombre']}' eliminado correctamente.")


# =============================================================================
# 16. VER LOGS
# =============================================================================
@app.route("/api/logs", methods=["GET"])
def ver_logs():
    logs = logger.get_logs()
    return ok({"logs": logs, "total": len(logs)}, f"{len(logs)} entradas de log.")


# =============================================================================
# UTILIDADES
# =============================================================================
# =============================================================================
# 17. REPORTE DE SUCURSALES (Observer + datos históricos)
# =============================================================================
@app.route("/api/reportes/sucursales", methods=["GET"])
def reporte_sucursales():
    from datetime import datetime, timedelta
    from sucursales_manager import SucursalesManager

    hoy = datetime.now().date()
    hace_30 = hoy - timedelta(days=29)

    manager = SucursalesManager.get_instancia()
    reporte = []

    for sucursal in manager.sucursales:
        # Recolectar todas las transacciones de las cuentas de esta sucursal
        movimientos_hoy   = []
        movimientos_mes   = []
        por_tipo_hoy      = {"deposito": 0, "retiro": 0, "transferencia": 0}
        por_tipo_mes      = {"deposito": 0, "retiro": 0, "transferencia": 0}
        por_canal_mes     = {"web": 0, "movil": 0, "cajero": 0}
        volumen_tipo_mes  = {"deposito": 0.0, "retiro": 0.0, "transferencia": 0.0}
        # Movimientos agrupados por día (últimos 30 días)
        dias = {}
        for i in range(30):
            d = (hace_30 + timedelta(days=i)).isoformat()
            dias[d] = 0

        for cuenta in sucursal.cuentas:
            for t in cuenta.transacciones:
                try:
                    fecha_dt = datetime.strptime(t["fecha"], "%Y-%m-%d %H:%M:%S")
                    fecha_d  = fecha_dt.date()
                except Exception:
                    continue

                tipo  = t.get("tipo", "deposito")
                canal = t.get("canal", "web")
                monto = t.get("monto", 0.0)

                # Hoy
                if fecha_d == hoy:
                    movimientos_hoy.append(t)
                    if tipo in por_tipo_hoy:
                        por_tipo_hoy[tipo] += 1

                # Último mes
                if fecha_d >= hace_30:
                    movimientos_mes.append(t)
                    if tipo in por_tipo_mes:
                        por_tipo_mes[tipo] += 1
                    if canal in por_canal_mes:
                        por_canal_mes[canal] += 1
                    if tipo in volumen_tipo_mes:
                        volumen_tipo_mes[tipo] += monto
                    clave = fecha_d.isoformat()
                    if clave in dias:
                        dias[clave] += 1

        reporte.append({
            "sucursal":        sucursal.nombre,
            "saldo_total":     sucursal.get_saldo_total(),
            "total_cuentas":   len(sucursal.cuentas),
            "hoy": {
                "total":    len(movimientos_hoy),
                "por_tipo": por_tipo_hoy,
            },
            "mes": {
                "total":       len(movimientos_mes),
                "por_tipo":    por_tipo_mes,
                "por_canal":   por_canal_mes,
                "volumen_tipo": volumen_tipo_mes,
                "por_dia":     [{"fecha": k, "cantidad": v} for k, v in sorted(dias.items())],
            }
        })

    return ok(reporte, f"Reporte de {len(reporte)} sucursal(es) generado.")


@app.route("/api/prototipos", methods=["GET"])
def listar_prototipos():
    nombres = CuentaPrototypeRegistry.listar()
    prototipos = []
    for n in nombres:
        p = CuentaPrototypeRegistry.get(n)
        prototipos.append({"nombre": n, "tipo": p.tipo, "saldo": p.saldo, "numero_base": p.numero})
    return ok(prototipos, f"{len(prototipos)} prototipo(s) registrados.")




# =============================================================================
# 18. LISTAR TODAS LAS CUENTAS CON SU ESTADO (STATE)
# =============================================================================
@app.route("/api/cuentas/estados", methods=["GET"])
def listar_estados_cuentas():
    data = []
    for usuario in banco.usuarios:
        for cuenta in usuario.cuentas:
            estado = cuenta.get_estado()
            data.append({
                "numero":      cuenta.numero,
                "tipo":        cuenta.tipo,
                "saldo":       cuenta.saldo,
                "usuario":     usuario.nombre,
                "documento":   usuario.documento,
                "estado":      estado.get_nombre(),
                "descripcion": estado.get_descripcion(),
                "color":       estado.get_color(),
            })
    return ok(data, f"{len(data)} cuenta(s) encontradas.")


# =============================================================================
# 19. CAMBIAR ESTADO DE UNA CUENTA (STATE)
# POST /api/cuentas/estado
# Body: { "numero_cuenta": "1001", "nuevo_estado": "bloqueada", "motivo": "..." }
# =============================================================================
@app.route("/api/cuentas/estado", methods=["POST"])
@requiere_api_key
def cambiar_estado_cuenta():
    body         = request.get_json(force=True)
    numero       = body.get("numero_cuenta", "").strip()
    nuevo_estado = body.get("nuevo_estado", "").strip()
    motivo       = body.get("motivo", "").strip()

    if not numero or not nuevo_estado:
        return err("Número de cuenta y nuevo estado son obligatorios.")

    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    estado_anterior = cuenta.get_estado().get_nombre()

    if estado_anterior == "cerrada":
        return err("La cuenta ya está cerrada (estado terminal). No se puede cambiar.")

    try:
        # ── MEMENTO: guardar estado actual ANTES de cambiarlo ─────────────────
        snapshot = GestorMementos.get_instancia().guardar_estado(cuenta)
        # ─────────────────────────────────────────────────────────────────────
        nuevo = EstadoCuentaProducer.get(nuevo_estado, motivo=motivo)
        cuenta.set_estado(nuevo)
    except ValueError as e:
        return err(str(e))

    repositorio.actualizar_cuenta(numero, cuenta.saldo, cuenta.get_estado().get_nombre())

    return ok(
        {
            "numero":            numero,
            "estado_anterior":   estado_anterior,
            "estado_nuevo":      cuenta.get_estado().get_nombre(),
            "descripcion":       cuenta.get_estado().get_descripcion(),
            "color":             cuenta.get_estado().get_color(),
            "snapshot_guardado": snapshot.to_dict(),
            "puede_restaurar":   True,
        },
        f"Cuenta {numero}: {estado_anterior.upper()} → {nuevo_estado.upper()}."
    )


# =============================================================================
# 20. CONSULTAR ESTADO DE UNA CUENTA (STATE)
# GET /api/cuentas/estado/<numero>
# =============================================================================
@app.route("/api/cuentas/estado/<numero>", methods=["GET"])
def consultar_estado_cuenta(numero):
    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    estado = cuenta.get_estado()
    perm_dep, msg_dep = estado.puede_depositar()
    perm_ret, msg_ret = estado.puede_retirar()
    perm_tra, msg_tra = estado.puede_transferir()

    return ok({
        "numero":      numero,
        "estado":      estado.get_nombre(),
        "descripcion": estado.get_descripcion(),
        "color":       estado.get_color(),
        "permisos": {
            "depositar":   {"permitido": perm_dep, "mensaje": msg_dep},
            "retirar":     {"permitido": perm_ret, "mensaje": msg_ret},
            "transferir":  {"permitido": perm_tra, "mensaje": msg_tra},
        }
    }, f"Estado de cuenta {numero} obtenido.")



# =============================================================================
# 21. CREAR PRÉSTAMO (STRATEGY)
# POST /api/prestamos/crear
# Body: { "documento": "123", "numero_cuenta": "1001", "monto": 5000000,
#         "num_cuotas": 12, "tasa_anual": 18.5, "tipo_interes": "fijo" }
# =============================================================================
@app.route("/api/prestamos/crear", methods=["POST"])
@requiere_api_key
def crear_prestamo():
    body          = request.get_json(force=True)
    documento     = body.get("documento", "").strip()
    num_cuenta    = body.get("numero_cuenta", "").strip()
    monto         = float(body.get("monto", 0))
    num_cuotas    = int(body.get("num_cuotas", 0))
    tasa_anual    = float(body.get("tasa_anual", 0))
    tipo_interes  = body.get("tipo_interes", "fijo").strip()

    if not documento or not num_cuenta or monto <= 0 or num_cuotas <= 0 or tasa_anual <= 0:
        return err("Todos los campos son obligatorios y deben ser positivos.")

    usuario = banco.buscar_usuario_por_documento(documento)
    if not usuario:
        return err(f"Usuario con documento {documento} no encontrado.")

    cuenta = banco.buscar_cuenta_por_numero(num_cuenta)
    if not cuenta:
        return err(f"Cuenta {num_cuenta} no encontrada.")

    # Verificar que la cuenta pertenece al usuario
    if not any(c.numero == num_cuenta for c in usuario.cuentas):
        return err(f"La cuenta {num_cuenta} no pertenece al usuario con documento {documento}.")

    try:
        estrategia = EstrategiaInteresProducer.get(tipo_interes)
    except ValueError as e:
        return err(str(e))

    prestamo = Prestamo(
        documento_usuario = documento,
        numero_cuenta     = num_cuenta,
        monto             = monto,
        num_cuotas        = num_cuotas,
        tasa_anual        = tasa_anual,
        estrategia        = estrategia,
    )

    # Depositar el monto del préstamo en la cuenta del usuario
    try:
        cuenta.depositar(monto, "web")
    except Exception as e:
        return err(f"No se pudo acreditar el préstamo en la cuenta: {e}")

    GestorPrestamos.get_instancia().agregar(prestamo)

    repositorio.actualizar_cuenta(num_cuenta, cuenta.saldo)
    repositorio.guardar_transaccion("deposito", monto, "web", cuenta_origen=num_cuenta)
    repositorio.guardar_prestamo(prestamo)

    return ok(
        prestamo.to_dict(),
        f"Préstamo {prestamo.id} creado. ${monto:,.2f} acreditados en cuenta {num_cuenta}."
    )


# =============================================================================
# 22. LISTAR TODOS LOS PRÉSTAMOS (STRATEGY)
# GET /api/prestamos
# =============================================================================
@app.route("/api/prestamos", methods=["GET"])
def listar_prestamos():
    prestamos = GestorPrestamos.get_instancia().get_todos()
    resultado = []
    for p in prestamos:
        d = p.to_dict()
        # Enriquecer con nombre del usuario
        usuario = banco.buscar_usuario_por_documento(p.documento)
        d["nombre_usuario"] = usuario.nombre if usuario else "—"
        resultado.append(d)
    return ok(resultado, f"{len(resultado)} préstamo(s) registrados.")


# =============================================================================
# 23. REGISTRAR PAGO DE CUOTA (STRATEGY)
# POST /api/prestamos/pagar
# Body: { "prestamo_id": "AB12CD34" }
# =============================================================================
@app.route("/api/prestamos/pagar", methods=["POST"])
@requiere_api_key
def pagar_cuota():
    body        = request.get_json(force=True)
    prestamo_id = body.get("prestamo_id", "").strip().upper()

    if not prestamo_id:
        return err("ID del préstamo es obligatorio.")

    prestamo = GestorPrestamos.get_instancia().get_por_id(prestamo_id)
    if not prestamo:
        return err(f"Préstamo {prestamo_id} no encontrado.")

    if prestamo.estado == "pagado":
        return err("El préstamo ya está completamente pagado.")

    cuenta = banco.buscar_cuenta_por_numero(prestamo.numero_cuenta)
    if not cuenta:
        return err(f"Cuenta {prestamo.numero_cuenta} no encontrada.")

    # ── CORRECCIÓN: calcular cuánto falta realmente descontando abonos libres
    monto_real = prestamo.calcular_monto_real_cuota()

    if monto_real == 0.0:
        # Los abonos ya cubrieron esta cuota completa — solo registrar sin cobrar
        resultado = prestamo.registrar_pago(0.0)
        if not resultado["ok"]:
            return err(resultado["mensaje"])
        repositorio.actualizar_prestamo(prestamo)
        return ok(
            {
                "prestamo_id":       prestamo_id,
                "cuota_pagada":      resultado["pago"],
                "monto_cobrado":     0.0,
                "abonos_aplicados":  resultado["pago"].get("abonos_aplicados", 0),
                "estado_prestamo":   prestamo.estado,
                "cuotas_pagadas":    prestamo.cuotas_pagadas,
                "cuotas_restantes":  prestamo.num_cuotas - prestamo.cuotas_pagadas,
                "saldo_cuenta":      cuenta.saldo,
                "total_pagado":      prestamo.total_pagado,
            },
            f"Cuota {prestamo.cuotas_pagadas}/{prestamo.num_cuotas} cubierta por abonos previos — sin cobro adicional."
        )

    # Validar saldo solo por el monto real a cobrar
    if cuenta.saldo < monto_real:
        return err(
            f"Saldo insuficiente. Saldo: ${cuenta.saldo:,.2f} | "
            f"Cuota completa: ${prestamo.cuota_mensual:,.2f} | "
            f"Ya abonado: ${prestamo.cuota_mensual - monto_real:,.2f} | "
            f"Falta cobrar: ${monto_real:,.2f}"
        )

    # Debitar solo el monto real (cuota - abonos ya aplicados)
    try:
        cuenta.retirar(monto_real, "web")
    except Exception as e:
        return err(f"No se pudo debitar la cuota: {e}")

    resultado = prestamo.registrar_pago(monto_real)
    if not resultado["ok"]:
        cuenta.depositar(monto_real, "web")
        return err(resultado["mensaje"])

    repositorio.actualizar_cuenta(prestamo.numero_cuenta, cuenta.saldo)
    repositorio.guardar_transaccion("retiro", monto_real, "web", cuenta_origen=prestamo.numero_cuenta)
    repositorio.actualizar_prestamo(prestamo)

    abonos_aplicados = resultado["pago"].get("abonos_aplicados", 0)
    msg = (
        f"Cuota {prestamo.cuotas_pagadas}/{prestamo.num_cuotas} registrada. "
        f"Cobrado: ${monto_real:,.2f}"
        + (f" (${abonos_aplicados:,.2f} cubiertos por abonos previos)." if abonos_aplicados > 0 else ".")
    )

    return ok(
        {
            "prestamo_id":       prestamo_id,
            "cuota_pagada":      resultado["pago"],
            "monto_cobrado":     monto_real,
            "abonos_aplicados":  abonos_aplicados,
            "estado_prestamo":   prestamo.estado,
            "cuotas_pagadas":    prestamo.cuotas_pagadas,
            "cuotas_restantes":  prestamo.num_cuotas - prestamo.cuotas_pagadas,
            "saldo_cuenta":      cuenta.saldo,
            "total_pagado":      prestamo.total_pagado,
        },
        msg
    )



# =============================================================================
# 25. ABONO MANUAL AL PRÉSTAMO (STRATEGY)
# POST /api/prestamos/abonar
# Body: { "prestamo_id": "AB12CD34", "monto": 300000 }
# Registra cualquier monto como abono libre, lo descuenta de la cuenta
# y lo acumula en total_pagado del préstamo.
# =============================================================================
@app.route("/api/prestamos/abonar", methods=["POST"])
@requiere_api_key
def abonar_prestamo():
    body        = request.get_json(force=True)
    prestamo_id = body.get("prestamo_id", "").strip().upper()
    monto       = float(body.get("monto", 0))

    if not prestamo_id:
        return err("ID del préstamo es obligatorio.")
    if monto <= 0:
        return err("El monto del abono debe ser positivo.")

    prestamo = GestorPrestamos.get_instancia().get_por_id(prestamo_id)
    if not prestamo:
        return err(f"Préstamo {prestamo_id} no encontrado.")

    if prestamo.estado == "pagado":
        return err("El préstamo ya está completamente pagado.")

    cuenta = banco.buscar_cuenta_por_numero(prestamo.numero_cuenta)
    if not cuenta:
        return err(f"Cuenta {prestamo.numero_cuenta} no encontrada.")

    if cuenta.saldo < monto:
        return err(
            f"Saldo insuficiente. Saldo: ${cuenta.saldo:,.2f} | "
            f"Abono solicitado: ${monto:,.2f}"
        )

    # Ajustar si el abono supera lo que queda por pagar
    saldo_prestamo = round(prestamo.total_a_pagar - prestamo.total_pagado, 2)
    if monto > saldo_prestamo:
        monto = saldo_prestamo  # no cobrar más de lo que se debe

    try:
        cuenta.retirar(monto, "web")
    except Exception as e:
        return err(f"No se pudo debitar el abono: {e}")

    resultado = prestamo.registrar_abono_manual(monto)
    if not resultado["ok"]:
        cuenta.depositar(monto, "web")
        return err(resultado["mensaje"])

    repositorio.actualizar_cuenta(prestamo.numero_cuenta, cuenta.saldo)
    repositorio.guardar_transaccion("retiro", monto, "web", cuenta_origen=prestamo.numero_cuenta)
    repositorio.actualizar_prestamo(prestamo)

    saldo_pendiente = round(prestamo.total_a_pagar - prestamo.total_pagado, 2)

    return ok(
        {
            "prestamo_id":     prestamo_id,
            "abono":           resultado["pago"],
            "total_pagado":    resultado["total_pagado"],
            "total_a_pagar":   resultado["total_a_pagar"],
            "saldo_pendiente": saldo_pendiente,
            "estado_prestamo": prestamo.estado,
            "saldo_cuenta":    cuenta.saldo,
        },
        f"Abono de ${monto:,.2f} registrado en préstamo {prestamo_id}."
    )


# =============================================================================
# 24. COMPARAR ESTRATEGIAS (STRATEGY) — utilidad para el frontend
# POST /api/prestamos/comparar
# Body: { "monto": 5000000, "num_cuotas": 12, "tasa_anual": 18.5 }
# =============================================================================
@app.route("/api/prestamos/comparar", methods=["POST"])
def comparar_estrategias():
    body       = request.get_json(force=True)
    monto      = float(body.get("monto", 0))
    num_cuotas = int(body.get("num_cuotas", 0))
    tasa_anual = float(body.get("tasa_anual", 0))

    if monto <= 0 or num_cuotas <= 0 or tasa_anual <= 0:
        return err("Monto, cuotas y tasa deben ser positivos.")

    resultado = []
    for tipo in EstrategiaInteresProducer.listar():
        estrategia = EstrategiaInteresProducer.get(tipo)
        resultado.append({
            "tipo":             tipo,
            "nombre":           estrategia.get_nombre(),
            "descripcion":      estrategia.get_descripcion(),
            "cuota_mensual":    estrategia.calcular_cuota(monto, tasa_anual, num_cuotas),
            "total_intereses":  estrategia.calcular_total_intereses(monto, tasa_anual, num_cuotas),
            "total_a_pagar":    round(monto + estrategia.calcular_total_intereses(monto, tasa_anual, num_cuotas), 2),
        })

    return ok(resultado, "Comparación de estrategias calculada.")



# =============================================================================
# ENDPOINTS PATRÓN COMMAND
# =============================================================================

# 26. DESHACER ÚLTIMO COMANDO
@app.route("/api/command/deshacer", methods=["POST"])
@requiere_api_key
def command_deshacer():
    invoker   = HistorialComandos.get_instancia()
    resultado = invoker.deshacer()
    if not resultado["ok"]:
        return err(resultado["mensaje"])
    _persistir_saldos_de_comando(resultado["datos"])
    return ok(
        {**resultado["datos"], "estado_invoker": invoker.get_estado()},
        resultado["mensaje"]
    )


# 27. REEJECUTAR ÚLTIMO DESHECHO
@app.route("/api/command/reejecutar", methods=["POST"])
@requiere_api_key
def command_reejecutar():
    invoker   = HistorialComandos.get_instancia()
    resultado = invoker.reejecutar()
    if not resultado["ok"]:
        return err(resultado["mensaje"])
    _persistir_saldos_de_comando(resultado["datos"])
    return ok(
        {**resultado["datos"], "estado_invoker": invoker.get_estado()},
        resultado["mensaje"]
    )


# 28. HISTORIAL DE COMANDOS
@app.route("/api/command/historial", methods=["GET"])
def command_historial():
    invoker   = HistorialComandos.get_instancia()
    historial = invoker.get_historial()
    estado    = invoker.get_estado()
    return ok(
        {"historial": historial, "estado": estado},
        f"{len(historial)} comando(s) en historial."
    )


# 29. LIMPIAR HISTORIAL
@app.route("/api/command/limpiar", methods=["POST"])
@requiere_api_key
def command_limpiar():
    HistorialComandos.get_instancia().limpiar()
    return ok(None, "Historial de commands limpiado.")


# =============================================================================
# PATRÓN MEMENTO — Endpoints 30 y 31
# =============================================================================

# 30. RESTAURAR ESTADO ANTERIOR (MEMENTO)
# POST /api/cuentas/estado/restaurar
# Body: { "numero_cuenta": "1001" }
@app.route("/api/cuentas/estado/restaurar", methods=["POST"])
@requiere_api_key
def restaurar_estado_cuenta():
    body   = request.get_json(force=True)
    numero = body.get("numero_cuenta", "").strip()

    if not numero:
        return err("El número de cuenta es obligatorio.")

    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    gestor = GestorMementos.get_instancia()

    if not gestor.tiene_historial(numero):
        return err(f"No hay estado anterior guardado para la cuenta {numero}.")

    estado_antes = cuenta.get_estado().get_nombre()
    resultado    = gestor.restaurar_estado(cuenta)

    if not resultado["ok"]:
        return err(resultado["mensaje"])

    repositorio.actualizar_cuenta(numero, cuenta.saldo, cuenta.get_estado().get_nombre())

    return ok(
        {
            "numero":              numero,
            "estado_anterior":     estado_antes,
            "estado_restaurado":   resultado["estado_restaurado"],
            "snapshot_fecha":      resultado["snapshot_fecha"],
            "snapshots_restantes": resultado["snapshots_restantes"],
        },
        f"Estado de cuenta {numero} restaurado: "
        f"{estado_antes.upper()} → {resultado['estado_restaurado'].upper()}."
    )


# 31. VER HISTORIAL DE SNAPSHOTS (MEMENTO)
# GET /api/cuentas/estado/historial/<numero>
@app.route("/api/cuentas/estado/historial/<numero>", methods=["GET"])
def historial_estados_cuenta(numero):
    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    gestor    = GestorMementos.get_instancia()
    historial = gestor.ver_historial(numero)

    return ok(
        {
            "numero":          numero,
            "estado_actual":   cuenta.get_estado().get_nombre(),
            "total_snapshots": gestor.total_snapshots(numero),
            "puede_restaurar": gestor.tiene_historial(numero),
            "historial":       historial,
        },
        f"Historial de estados de cuenta {numero} obtenido."
    )


# =============================================================================
# PATRÓN CHAIN OF RESPONSIBILITY — Endpoints 32 y 33
# =============================================================================

# 32. VALIDAR TRANSACCIÓN SIN EJECUTAR (CHAIN OF RESPONSIBILITY)
# POST /api/validacion/transaccion
# Body: { "numero_cuenta": "1001", "monto": 500000, "tipo": "retiro",
#         "canal": "web", "numero_destino": "" }
@app.route("/api/validacion/transaccion", methods=["POST"])
def validar_transaccion():
    body           = request.get_json(force=True)
    numero         = body.get("numero_cuenta", "").strip()
    monto          = float(body.get("monto", 0))
    tipo           = body.get("tipo", "deposito").strip()
    canal          = body.get("canal", "web").strip()
    numero_destino = body.get("numero_destino", "").strip()

    if not numero or monto <= 0:
        return err("Número de cuenta y monto positivo son obligatorios.")

    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    cuenta_destino = None
    if numero_destino:
        cuenta_destino = banco.buscar_cuenta_por_numero(numero_destino)
        if not cuenta_destino:
            return err(f"Cuenta destino {numero_destino} no encontrada.")

    resultado = CadenaValidacionFactory.validar(
        cuenta_origen  = cuenta,
        monto          = monto,
        tipo           = tipo,
        canal          = canal,
        cuenta_destino = cuenta_destino,
    )

    return ok(
        resultado.to_dict(),
        f"Cadena de validación ejecutada. "
        f"Resultado: {'APROBADA' if resultado.aprobado else f'RECHAZADA por {resultado.rechazado_por}'}."
    )


# 33. EJECUTAR CON VALIDACIÓN CHAIN (CHAIN + COMMAND)
# POST /api/validacion/ejecutar
# Body: { "numero_cuenta": "1001", "monto": 500000, "tipo": "retiro",
#         "canal": "web", "numero_destino": "" }
@app.route("/api/validacion/ejecutar", methods=["POST"])
@requiere_api_key
def ejecutar_con_chain():
    body           = request.get_json(force=True)
    numero         = body.get("numero_cuenta", "").strip()
    monto          = float(body.get("monto", 0))
    tipo           = body.get("tipo", "deposito").strip()
    canal          = body.get("canal", "web").strip()
    numero_destino = body.get("numero_destino", "").strip()

    if not numero or monto <= 0:
        return err("Número de cuenta y monto positivo son obligatorios.")

    cuenta = banco.buscar_cuenta_por_numero(numero)
    if not cuenta:
        return err(f"Cuenta {numero} no encontrada.")

    cuenta_destino = None
    if numero_destino:
        cuenta_destino = banco.buscar_cuenta_por_numero(numero_destino)
        if not cuenta_destino:
            return err(f"Cuenta destino {numero_destino} no encontrada.")

    # Paso 1: Chain of Responsibility — validar antes de ejecutar
    resultado_chain = CadenaValidacionFactory.validar(
        cuenta_origen  = cuenta,
        monto          = monto,
        tipo           = tipo,
        canal          = canal,
        cuenta_destino = cuenta_destino,
    )

    if not resultado_chain.aprobado:
        return ok(
            {
                "ejecutado":    False,
                "validacion":   resultado_chain.to_dict(),
                "saldo_actual": cuenta.saldo,
            },
            f"Transacción rechazada por Chain: {resultado_chain.rechazado_por}."
        )

    # Paso 2: Ejecutar via Command (para mantener undo/redo)
    invoker = HistorialComandos.get_instancia()
    if tipo == "deposito":
        cmd = ComandoDeposito(cuenta, monto, canal)
    elif tipo == "retiro":
        cmd = ComandoRetiro(cuenta, monto, canal)
    elif tipo == "transferencia":
        cmd = ComandoTransferencia(cuenta, cuenta_destino, monto, canal)
    else:
        return err(f"Tipo de operación no soportado: {tipo}")

    res_cmd = invoker.ejecutar(cmd)

    return ok(
        {
            "ejecutado":      res_cmd["ok"],
            "validacion":     resultado_chain.to_dict(),
            "operacion":      res_cmd.get("datos", {}),
            "saldo_actual":   cuenta.saldo,
            "estado_invoker": invoker.get_estado(),
        },
        f"Operación ejecutada tras validación completa de la cadena."
        if res_cmd["ok"] else res_cmd["mensaje"]
    )


# =============================================================================
# PATRÓN TEMPLATE METHOD — Endpoints 34 y 35
# =============================================================================

# 34. GENERAR REPORTE (TEMPLATE METHOD)
# POST /api/reportes/generar
# Body ejemplos:
#   { "tipo": "movimientos", "numero_cuenta": "1001", "periodo_dias": 30 }
#   { "tipo": "prestamos",   "documento": "1234567890", "periodo_dias": 365 }
#   { "tipo": "sucursal",    "nombre_sucursal": "Bucaramanga Centro", "periodo_dias": 30 }
#   { "tipo": "usuario",     "documento": "1234567890", "periodo_dias": 30 }
@app.route("/api/reportes/generar", methods=["POST"])
def generar_reporte():
    body    = request.get_json(force=True)
    tipo    = body.get("tipo", "").strip().lower()
    periodo = int(body.get("periodo_dias", 30))

    if not tipo:
        return err("El tipo de reporte es obligatorio.")

    try:
        generador = ReporteProducer.get(
            tipo,
            banco,
            numero_cuenta   = body.get("numero_cuenta",   ""),
            documento       = body.get("documento",        ""),
            nombre_sucursal = body.get("nombre_sucursal",  ""),
            periodo_dias    = periodo,
        )
        resultado = generador.generar()
        return ok(resultado, f"Reporte '{tipo}' generado exitosamente.")

    except ValueError as e:
        return err(str(e))
    except Exception as e:
        return err(f"Error generando reporte: {e}")


# 35. LISTAR TIPOS DE REPORTE DISPONIBLES (TEMPLATE METHOD)
# GET /api/reportes/tipos
@app.route("/api/reportes/tipos", methods=["GET"])
def listar_tipos_reporte():
    info = [
        {
            "tipo":        "movimientos",
            "descripcion": "Historial y estadísticas de una cuenta específica",
            "parametros":  ["numero_cuenta", "periodo_dias (default 30)"],
        },
        {
            "tipo":        "prestamos",
            "descripcion": "Resumen de préstamos de un usuario",
            "parametros":  ["documento", "periodo_dias (default 365)"],
        },
        {
            "tipo":        "sucursal",
            "descripcion": "Actividad consolidada de una sucursal",
            "parametros":  ["nombre_sucursal", "periodo_dias (default 30)"],
        },
        {
            "tipo":        "usuario",
            "descripcion": "Resumen completo de cuentas y movimientos de un usuario",
            "parametros":  ["documento", "periodo_dias (default 30)"],
        },
    ]
    return ok(info, f"{len(info)} tipo(s) de reporte disponibles.")


if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG, port=int(os.environ.get("PORT", 5000)))