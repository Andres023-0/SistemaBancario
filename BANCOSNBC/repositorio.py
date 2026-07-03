"""
repositorio.py — FASE 2.3

Puente entre las clases de dominio ya existentes (Usuario, Cuenta,
Prestamo, Sucursal...) y las tablas de Supabase. Ninguna clase de
dominio (los 16 patrones) se modifica desde aquí: este módulo solo
lee y escribe sus atributos públicos.

Diseño "fail-safe" (mismo espíritu que @requiere_api_key en api.py):
    - Si SUPABASE_URL / SUPABASE_SECRET_KEY no están definidas
      (supabase_config.PERSISTENCIA_ACTIVA == False), todas las
      funciones de este módulo son no-ops seguros: cargar_*() retornan
      listas vacías y guardar_*() no hacen nada. El sistema completo
      sigue funcionando 100% en memoria, igual que antes de la Fase 2.
    - Si Supabase está configurado pero una llamada puntual falla
      (red caída, fila duplicada, etc.), se registra un WARNING en el
      Logger y la operación de negocio en memoria NO se revierte ni se
      interrumpe: la persistencia es un efecto secundario, nunca debe
      tumbar una transacción bancaria ya validada en memoria.
"""

from supabase_config import get_client, PERSISTENCIA_ACTIVA
from logger import Logger

_log = Logger.get_instancia()


def _safe(operacion, *args, **kwargs):
    """Ejecuta una operación contra Supabase sin propagar excepciones."""
    if not PERSISTENCIA_ACTIVA:
        return None
    try:
        return operacion(*args, **kwargs)
    except Exception as e:
        _log.log(f"[REPOSITORIO] ⚠ Error de persistencia: {e}", nivel="WARNING")
        return None


# =============================================================================
# SUCURSALES
# =============================================================================

def sincronizar_sucursales(nombres: list) -> dict:
    """
    Garantiza que las sucursales predeterminadas (ConfigBanco) existan
    en Supabase (upsert por nombre, único) y retorna {nombre: id},
    necesario como FK al guardar cuentas.
    Si la persistencia está desactivada, retorna {} (sin romper nada;
    el resto del sistema sigue usando índices en memoria como siempre).
    """
    def _op():
        client = get_client()
        client.table("sucursales").upsert(
            [{"nombre": n} for n in nombres], on_conflict="nombre"
        ).execute()
        res = client.table("sucursales").select("id,nombre").execute()
        return {fila["nombre"]: fila["id"] for fila in res.data}
    return _safe(_op) or {}


def cargar_sucursales() -> list:
    """Retorna [{'id':.., 'nombre':..}, ...] o [] si no hay persistencia."""
    def _op():
        return get_client().table("sucursales").select("id,nombre").execute().data
    return _safe(_op) or []


# =============================================================================
# USUARIOS
# =============================================================================

def guardar_usuario(usuario) -> None:
    """Upsert completo — Usuario siempre trae todos sus atributos."""
    def _op():
        get_client().table("usuarios").upsert({
            "documento":      usuario.documento,
            "nombre":         usuario.nombre,
            "celular":        usuario.celular,
            "correo":         usuario.correo,
            "verificado_kyc": usuario.verificado_kyc,
        }, on_conflict="documento").execute()
    _safe(_op)


def cargar_usuarios() -> list:
    def _op():
        return get_client().table("usuarios").select("*").execute().data
    return _safe(_op) or []


def eliminar_usuario(documento: str) -> None:
    """
    Borra el usuario. Con la migración Fase 2 (ON DELETE CASCADE),
    Supabase borra automáticamente sus cuentas, transacciones y
    préstamos asociados — igual que hace UsuarioFacade.eliminar_usuario()
    en memoria.
    """
    def _op():
        get_client().table("usuarios").delete().eq("documento", documento).execute()
    _safe(_op)


# =============================================================================
# CUENTAS
# =============================================================================

def guardar_cuenta(cuenta, documento: str, sucursal_id) -> None:
    """
    Upsert completo — usar SOLO al crear la cuenta (tenemos todos los
    datos: documento y sucursal_id). Para actualizar saldo/estado tras
    una operación, usar actualizar_cuenta() (evita pisar NOT NULL con
    payloads parciales).
    """
    def _op():
        get_client().table("cuentas").upsert({
            "numero":      cuenta.numero,
            "documento":   documento,
            "sucursal_id": sucursal_id,
            "tipo":        cuenta.tipo,
            "saldo":       cuenta.saldo,
            "estado":      cuenta.get_estado().get_nombre(),
        }, on_conflict="numero").execute()
    _safe(_op)


def actualizar_cuenta(numero: str, saldo: float, estado: str = None) -> None:
    """Actualiza solo saldo (y opcionalmente estado) de una cuenta existente."""
    def _op():
        payload = {"saldo": saldo}
        if estado is not None:
            payload["estado"] = estado
        get_client().table("cuentas").update(payload).eq("numero", numero).execute()
    _safe(_op)


def cargar_cuentas() -> list:
    def _op():
        return get_client().table("cuentas").select("*").execute().data
    return _safe(_op) or []


# =============================================================================
# TRANSACCIONES
# =============================================================================

def guardar_transaccion(tipo: str, monto: float, canal: str,
                         cuenta_origen: str, cuenta_destino: str = None,
                         alertas: list = None) -> None:
    def _op():
        get_client().table("transacciones").insert({
            "tipo":           tipo,
            "monto":          monto,
            "canal":          canal,
            "cuenta_origen":  cuenta_origen,
            "cuenta_destino": cuenta_destino,
            "alertas_fraude": alertas or [],
        }).execute()
    _safe(_op)


def cargar_transacciones(numero_cuenta: str = None) -> list:
    """
    Sin argumento: retorna TODO el historial (para reconstruir el
    estado de arranque). Con numero_cuenta: solo las de esa cuenta,
    como origen o como destino.
    """
    def _op():
        client = get_client()
        query = client.table("transacciones").select("*").order("creado_en")
        if numero_cuenta:
            query = query.or_(
                f"cuenta_origen.eq.{numero_cuenta},cuenta_destino.eq.{numero_cuenta}"
            )
        return query.execute().data
    return _safe(_op) or []


# =============================================================================
# PRÉSTAMOS
# =============================================================================

def _prestamo_a_payload(prestamo) -> dict:
    return {
        "id":              prestamo.id,
        "documento":       prestamo.documento,
        "numero_cuenta":   prestamo.numero_cuenta,
        "monto":           prestamo.monto,
        "num_cuotas":      prestamo.num_cuotas,
        "tasa_anual":      prestamo.tasa_anual,
        "tipo_interes":    prestamo.get_estrategia().get_tipo(),
        "cuota_mensual":   prestamo.cuota_mensual,
        "total_intereses": prestamo.total_intereses,
        "total_a_pagar":   prestamo.total_a_pagar,
        "saldo_pendiente": round(prestamo.total_a_pagar - prestamo.total_pagado, 2),
        "cuotas_pagadas":  prestamo.cuotas_pagadas,
        "total_pagado":    prestamo.total_pagado,
        "estado":          prestamo.estado,
        "pagos":           prestamo.pagos,
    }


def guardar_prestamo(prestamo) -> None:
    """Insert inicial al crear un préstamo nuevo."""
    def _op():
        get_client().table("prestamos").insert(_prestamo_a_payload(prestamo)).execute()
    _safe(_op)


def actualizar_prestamo(prestamo) -> None:
    """Update completo tras cada pago de cuota o abono libre."""
    def _op():
        payload = _prestamo_a_payload(prestamo)
        payload.pop("id")
        get_client().table("prestamos").update(payload).eq("id", prestamo.id).execute()
    _safe(_op)


def cargar_prestamos() -> list:
    def _op():
        return get_client().table("prestamos").select("*").execute().data
    return _safe(_op) or []
