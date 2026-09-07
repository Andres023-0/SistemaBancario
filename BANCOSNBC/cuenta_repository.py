"""
=============================================================================
REPOSITORIO DE CUENTA — FASE 8
=============================================================================
Traduce en ambos sentidos entre:
  - models.Cuenta / models.Movimiento → filas de las tablas `cuentas` y
    `movimientos` (solo datos)
  - cuenta.Cuenta                     → el objeto de dominio real, con su
    patrón STATE (self._estado) y sus operaciones depositar()/retirar()/
    transferir().

Punto delicado de este repositorio: cuenta.Cuenta guarda su historial de
movimientos en una lista de Python (`self.transacciones`) que solo crece
—nunca se borra ni se edita—. Por eso, en `guardar()`, la estrategia más
simple y correcta es: reemplazar TODOS los movimientos de esa cuenta en la
BD por los que hay actualmente en memoria. Es más caro que insertar solo
"lo nuevo", pero evita duplicados y es fácil de razonar. Si más adelante el
historial de movimientos crece mucho, se puede optimizar guardando solo el
último índice ya persistido — no hace falta para el alcance de este
proyecto.

IMPORTANTE: igual que usuario_repository.py, estas funciones deben
llamarse dentro de un contexto de aplicación de Flask.
=============================================================================
"""

from datetime import datetime

import models
from database import db
from cuenta import Cuenta as CuentaDominio
from estado_cuenta import EstadoActiva, EstadoBloqueada, EstadoSuspendida, EstadoCerrada

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# Traducción del patrón STATE (objeto EstadoX ↔ string en la BD)
# =============================================================================
def _estado_a_fila(estado_obj):
    """cuenta.get_estado() (objeto) → (nombre: str, motivo: str|None) para guardar."""
    nombre = estado_obj.get_nombre()
    motivo = estado_obj.get_motivo() if hasattr(estado_obj, "get_motivo") else None
    return nombre, motivo


def _fila_a_estado(nombre: str, motivo: str | None):
    """(nombre, motivo) de la BD → objeto EstadoX real, para reconstruir la cuenta."""
    if nombre == "bloqueada":
        return EstadoBloqueada(motivo or "fraude detectado")
    if nombre == "suspendida":
        return EstadoSuspendida(motivo or "revisión administrativa")
    if nombre == "cerrada":
        return EstadoCerrada()
    return EstadoActiva()


# =============================================================================
# GUARDAR
# =============================================================================
def guardar(cuenta: CuentaDominio, documento: str = None, sucursal_id: int = None) -> None:
    """
    `documento` es obligatorio la PRIMERA vez que se guarda una cuenta nueva
    (así sabemos a qué usuario pertenece). En guardados posteriores —por
    ejemplo, desde ObservadorPersistencia después de un depósito/retiro,
    que no conoce quién es el titular— se puede omitir: se conserva el
    documento que ya tenía la fila en la base de datos.
    """
    fila = db.session.get(models.Cuenta, cuenta.numero)
    if fila is None:
        if not documento:
            raise ValueError(
                f"No se puede crear la cuenta {cuenta.numero} sin indicar el documento del titular."
            )
        fila = models.Cuenta(numero=cuenta.numero, documento=documento)
        db.session.add(fila)
    elif documento:
        fila.documento = documento

    nombre_estado, motivo_estado = _estado_a_fila(cuenta.get_estado())

    if sucursal_id is not None:
        fila.sucursal_id = sucursal_id
    fila.tipo           = cuenta.tipo
    fila.saldo          = cuenta.saldo
    fila.estado         = nombre_estado
    fila.motivo_estado  = motivo_estado

    # Resincronizar movimientos: se borran los existentes y se reinsertan
    # todos los que hay actualmente en cuenta.transacciones (ver nota arriba).
    models.Movimiento.query.filter_by(cuenta_numero=cuenta.numero).delete()
    for mov in cuenta.transacciones:
        db.session.add(models.Movimiento(
            cuenta_numero=cuenta.numero,
            tipo=mov["tipo"],
            monto=mov["monto"],
            canal=mov["canal"],
            saldo_resultante=mov["saldo_final"],
            fecha=datetime.strptime(mov["fecha"], FORMATO_FECHA),
        ))

    db.session.commit()


# =============================================================================
# OBTENER
# =============================================================================
def _reconstruir(fila: "models.Cuenta") -> CuentaDominio:
    c = CuentaDominio(fila.numero, fila.tipo, float(fila.saldo))

    # Patrón STATE: se asigna el estado directamente (sin pasar por
    # bloquear()/suspender()/etc.) para no generar una entrada de log de
    # "transición" cada vez que simplemente se está leyendo de la BD.
    c._estado = _fila_a_estado(fila.estado, fila.motivo_estado)

    from observer_cuenta import ObservadorProducer
    for observador in ObservadorProducer.get_observadores_default():
        c.suscribir(observador)

    # Historial: se reconstruye en el mismo formato de diccionario que usa
    # Cuenta._registrar(), para que el resto del sistema (que ya sabe leer
    # cuenta.transacciones) no note ninguna diferencia.
    movimientos = models.Movimiento.query.filter_by(
        cuenta_numero=fila.numero
    ).order_by(models.Movimiento.fecha).all()

    c.transacciones = [
        {
            "fecha":       mov.fecha.strftime(FORMATO_FECHA),
            "tipo":        mov.tipo,
            "monto":       float(mov.monto),
            "canal":       mov.canal,
            "saldo_final": float(mov.saldo_resultante),
        }
        for mov in movimientos
    ]

    return c


def obtener(numero: str) -> CuentaDominio | None:
    fila = db.session.get(models.Cuenta, numero)
    if fila is None:
        return None
    return _reconstruir(fila)


def listar_por_documento(documento: str) -> list:
    filas = models.Cuenta.query.filter_by(documento=documento).all()
    return [_reconstruir(f) for f in filas]


def listar_todas() -> list:
    filas = models.Cuenta.query.all()
    return [_reconstruir(f) for f in filas]


def existe(numero: str) -> bool:
    return db.session.get(models.Cuenta, numero) is not None


def mapa_sucursal_por_cuenta() -> dict:
    """
    {numero_cuenta: sucursal_id} de TODAS las cuentas. FASE 9: lo usa
    Banco.__init__() para reconstruir qué cuentas pertenecen a qué
    Sucursal de dominio al arrancar, ya que el objeto Cuenta en sí no
    guarda su sucursal (esa asociación solo existe en la tabla `cuentas`).
    """
    return {f.numero: f.sucursal_id for f in models.Cuenta.query.all()}
