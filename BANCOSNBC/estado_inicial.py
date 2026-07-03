"""
estado_inicial.py — FASE 2.4

Bootstrap del estado en memoria al arrancar el servidor (api.py) o la
CLI (main.py). No es una clase de dominio: solo orquesta, en el orden
correcto, las clases ya existentes (UsuarioFacade, CuentaBuilder vía
facade, Prestamo, EstadoCuenta...) usando los datos que repositorio.py
trae de Supabase.

Comportamiento:
    - Si Supabase tiene usuarios guardados → reconstruye el estado
      completo desde ahí (usuarios, cuentas, saldos, estados, historial
      de transacciones, préstamos) y NO vuelve a correr el seed.
    - Si Supabase está vacío (primera vez) o la persistencia está
      desactivada (sin variables de entorno) → corre el seed de
      siempre (seed.py + seed_prestamos.py), exactamente como hacía
      api.py/main.py antes de la Fase 2. Si además hay persistencia
      activa, guarda ese seed en Supabase para que la próxima vez el
      servidor ya arranque reconstruyendo en vez de re-sembrando.
"""

from logger import Logger
import repositorio
from supabase_config import PERSISTENCIA_ACTIVA
from config_banco import ConfigBanco

_log = Logger.get_instancia()


def _mapa_indice_por_sucursal_id(id_a_nombre: dict, nombres_orden: list) -> dict:
    """sucursal_id (Supabase) → índice 1-based que espera UsuarioFacade.crear_cuenta()."""
    nombre_a_indice = {nombre: i + 1 for i, nombre in enumerate(nombres_orden)}
    return {
        sid: nombre_a_indice[nombre]
        for sid, nombre in id_a_nombre.items()
        if nombre in nombre_a_indice
    }


def _reconstruir_desde_supabase(banco, usuario_facade) -> bool:
    """Retorna True si reconstruyó datos, False si Supabase estaba vacío."""
    filas_usuarios = repositorio.cargar_usuarios()
    if not filas_usuarios:
        return False

    config = ConfigBanco.get_instancia()
    nombres_sucursales = config.get_sucursales()
    id_a_nombre = {f["id"]: f["nombre"] for f in repositorio.cargar_sucursales()}
    id_a_indice = _mapa_indice_por_sucursal_id(id_a_nombre, nombres_sucursales)

    _log.log("[BOOTSTRAP] Reconstruyendo estado desde Supabase...", nivel="INFO")

    # 1) Usuarios + KYC (deben existir antes de poder crear cuentas)
    for fila in filas_usuarios:
        usuario_facade.registrar_usuario(
            nombre=fila["nombre"],
            documento=fila["documento"],
            celular=fila.get("celular") or "",
            correo=fila.get("correo") or "",
        )
        if fila.get("verificado_kyc"):
            usuario_facade.verificar_kyc(fila["documento"])

    # 2) Cuentas — se crean con el saldo real guardado (Cuenta.__init__ lo
    #    asigna directamente, sin pasar por depositar(), así no se genera
    #    una transacción falsa ni se notifica a los observadores).
    from estado_cuenta import EstadoBloqueada, EstadoSuspendida, EstadoCerrada
    fabricas_estado = {
        "bloqueada":  lambda: EstadoBloqueada("restaurado desde persistencia"),
        "suspendida": lambda: EstadoSuspendida("restaurado desde persistencia"),
        "cerrada":    lambda: EstadoCerrada(),
    }
    filas_cuentas = repositorio.cargar_cuentas()
    for fila in filas_cuentas:
        indice = id_a_indice.get(fila.get("sucursal_id"), 1)
        cuenta = usuario_facade.crear_cuenta(
            documento=fila["documento"],
            numero_cuenta=fila["numero"],
            tipo=fila["tipo"],
            saldo_inicial=float(fila["saldo"]),
            indice_sucursal=indice,
        )
        if cuenta is None:
            _log.log(f"[BOOTSTRAP] ⚠ No se pudo recrear cuenta {fila['numero']}.", nivel="WARNING")
            continue
        fabrica = fabricas_estado.get(fila.get("estado", "activa"))
        if fabrica:
            cuenta.set_estado(fabrica())

    # 3) Historial de transacciones — solo repuebla cuenta.transacciones
    #    para los endpoints de consulta; no vuelve a mover dinero.
    for fila_tx in repositorio.cargar_transacciones():
        tipo, monto, canal = fila_tx["tipo"], float(fila_tx["monto"]), fila_tx["canal"]
        fecha = fila_tx.get("creado_en", "")
        origen_num  = fila_tx.get("cuenta_origen")
        destino_num = fila_tx.get("cuenta_destino")

        cuenta_origen = banco.buscar_cuenta_por_numero(origen_num) if origen_num else None
        if cuenta_origen:
            cuenta_origen.transacciones.append({
                "fecha": fecha, "tipo": tipo, "monto": monto,
                "canal": canal, "saldo_final": cuenta_origen.saldo,
            })

        if tipo == "transferencia" and destino_num:
            cuenta_destino = banco.buscar_cuenta_por_numero(destino_num)
            if cuenta_destino:
                cuenta_destino.transacciones.append({
                    "fecha": fecha, "tipo": "deposito", "monto": monto,
                    "canal": canal, "saldo_final": cuenta_destino.saldo,
                })

    # 4) Préstamos
    from prestamo_strategy import EstrategiaInteresProducer, GestorPrestamos, Prestamo
    gestor = GestorPrestamos.get_instancia()
    for fila_p in repositorio.cargar_prestamos():
        try:
            estrategia = EstrategiaInteresProducer.get(fila_p["tipo_interes"])
            prestamo = Prestamo(
                documento_usuario=fila_p["documento"],
                numero_cuenta=fila_p["numero_cuenta"],
                monto=float(fila_p["monto"]),
                num_cuotas=fila_p["num_cuotas"],
                tasa_anual=float(fila_p["tasa_anual"]),
                estrategia=estrategia,
            )
            prestamo.id             = fila_p["id"]
            prestamo.cuotas_pagadas = fila_p.get("cuotas_pagadas", 0)
            prestamo.total_pagado   = float(fila_p.get("total_pagado", 0))
            prestamo.estado         = fila_p.get("estado", "activo")
            prestamo.pagos          = fila_p.get("pagos", [])
            prestamo.fecha_creacion = fila_p.get("creado_en", prestamo.fecha_creacion)
            gestor.agregar(prestamo)
        except Exception as e:
            _log.log(f"[BOOTSTRAP] ⚠ No se pudo recrear préstamo {fila_p.get('id')}: {e}", nivel="WARNING")

    _log.log(
        f"[BOOTSTRAP] ✅ Reconstruidos: {len(filas_usuarios)} usuario(s), "
        f"{len(filas_cuentas)} cuenta(s), {len(gestor.get_todos())} préstamo(s).",
        nivel="SUCCESS",
    )
    return True


def _sembrar_y_persistir(banco) -> None:
    """Corre el seed original (sin cambios) y, si hay persistencia activa, lo guarda."""
    from seed import cargar_datos_prueba
    from seed_prestamos import cargar_prestamos_seed

    cargar_datos_prueba(banco)
    cargar_prestamos_seed(banco)

    if not PERSISTENCIA_ACTIVA:
        return

    _log.log("[BOOTSTRAP] Persistiendo datos semilla en Supabase...", nivel="INFO")

    config = ConfigBanco.get_instancia()
    ids_sucursal = repositorio.sincronizar_sucursales(config.get_sucursales())

    for usuario in banco.usuarios:
        repositorio.guardar_usuario(usuario)
        for cuenta in usuario.cuentas:
            sucursal = next((s for s in banco.sucursales if cuenta in s._cuentas), None)
            sucursal_id = ids_sucursal.get(sucursal.nombre) if sucursal else None
            repositorio.guardar_cuenta(cuenta, usuario.documento, sucursal_id)
            for mov in cuenta.transacciones:
                repositorio.guardar_transaccion(
                    tipo=mov["tipo"], monto=mov["monto"], canal=mov["canal"],
                    cuenta_origen=cuenta.numero,
                )

    from prestamo_strategy import GestorPrestamos
    for prestamo in GestorPrestamos.get_instancia().get_todos():
        repositorio.guardar_prestamo(prestamo)

    _log.log("[BOOTSTRAP] ✅ Datos semilla persistidos en Supabase.", nivel="SUCCESS")


def inicializar_estado(banco, usuario_facade) -> None:
    """
    Punto de entrada único. Llamar UNA vez al arrancar api.py o main.py,
    inmediatamente después de crear Banco() y UsuarioFacade(banco), en
    reemplazo de las llamadas directas a cargar_datos_prueba()/
    cargar_prestamos_seed().
    """
    if PERSISTENCIA_ACTIVA:
        if _reconstruir_desde_supabase(banco, usuario_facade):
            return
        _log.log(
            "[BOOTSTRAP] Supabase configurado pero vacío — cargando datos semilla.",
            nivel="INFO",
        )
    else:
        _log.log(
            "[BOOTSTRAP] Persistencia desactivada (sin SUPABASE_URL/SUPABASE_SECRET_KEY) "
            "— modo en memoria, igual que antes de la Fase 2.",
            nivel="WARNING",
        )
    _sembrar_y_persistir(banco)
