"""
=============================================================================
REPOSITORIO DE PRÉSTAMO — FASE 8
=============================================================================
Traduce en ambos sentidos entre:
  - models.Prestamo / models.PagoPrestamo → filas de las tablas `prestamos`
    y `pagos_prestamo` (solo datos)
  - prestamo_strategy.Prestamo            → el objeto de dominio real, con
    su patrón STRATEGY (self._estrategia) y sus métodos registrar_pago(),
    registrar_abono_manual(), etc.

Punto delicado: Prestamo.__init__() SIEMPRE recalcula cuota_mensual,
total_intereses y total_a_pagar a partir de la estrategia. Si reconstruimos
un préstamo llamando a __init__() normalmente, esos valores se recalculan
de cero — lo cual es un problema real para InteresEstrategiaVariable, cuyo
resultado depende de constantes (DTF simulado, spread) que podrían cambiar
en el código con el tiempo. Para que un préstamo cargado desde la BD refleje
EXACTAMENTE lo que se guardó (y no lo que la fórmula daría hoy), este
repositorio construye el objeto con `Prestamo.__new__()` y asigna cada
atributo manualmente, sin pasar por __init__().
=============================================================================
"""

from datetime import datetime

import models
from database import db
from prestamo_strategy import Prestamo as PrestamoDominio, EstrategiaInteresProducer

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# GUARDAR
# =============================================================================
def guardar(prestamo: PrestamoDominio) -> None:
    fila = db.session.get(models.Prestamo, prestamo.id)
    if fila is None:
        fila = models.Prestamo(id=prestamo.id)
        db.session.add(fila)

    fila.documento        = prestamo.documento
    fila.numero_cuenta    = prestamo.numero_cuenta
    fila.monto            = prestamo.monto
    fila.num_cuotas       = prestamo.num_cuotas
    fila.tasa_anual       = prestamo.tasa_anual
    fila.tipo_interes     = prestamo.get_estrategia().get_tipo()
    fila.cuota_mensual    = prestamo.cuota_mensual
    fila.total_intereses  = prestamo.total_intereses
    fila.total_a_pagar    = prestamo.total_a_pagar
    fila.cuotas_pagadas   = prestamo.cuotas_pagadas
    fila.total_pagado     = prestamo.total_pagado
    fila.estado           = prestamo.estado
    fila.fecha_creacion   = datetime.strptime(prestamo.fecha_creacion, FORMATO_FECHA)

    # Resincronizar pagos: igual que con los movimientos de cuenta, se
    # reemplazan todos por los que hay actualmente en prestamo.pagos.
    models.PagoPrestamo.query.filter_by(prestamo_id=prestamo.id).delete()
    for pago in prestamo.pagos:
        db.session.add(models.PagoPrestamo(
            prestamo_id=prestamo.id,
            numero_cuota=str(pago["numero_cuota"]),
            tipo=pago["tipo"],
            monto=pago["monto"],
            fecha=datetime.strptime(pago["fecha"], FORMATO_FECHA),
        ))

    db.session.commit()


# =============================================================================
# OBTENER
# =============================================================================
def _reconstruir(fila: "models.Prestamo") -> PrestamoDominio:
    p = PrestamoDominio.__new__(PrestamoDominio)  # bypass __init__ (ver nota arriba)

    p.id              = fila.id
    p.documento       = fila.documento
    p.numero_cuenta   = fila.numero_cuenta
    p.monto           = float(fila.monto)
    p.num_cuotas      = fila.num_cuotas
    p.tasa_anual      = float(fila.tasa_anual)
    p._estrategia     = EstrategiaInteresProducer.get(fila.tipo_interes)

    p.cuota_mensual   = float(fila.cuota_mensual)
    p.total_intereses = float(fila.total_intereses)
    p.total_a_pagar   = float(fila.total_a_pagar)
    p.cuotas_pagadas  = fila.cuotas_pagadas
    p.total_pagado    = float(fila.total_pagado)
    p.estado          = fila.estado
    p.fecha_creacion  = fila.fecha_creacion.strftime(FORMATO_FECHA)

    pagos = models.PagoPrestamo.query.filter_by(
        prestamo_id=fila.id
    ).order_by(models.PagoPrestamo.fecha).all()

    # NOTA: el diccionario de pago en memoria (ver registrar_pago() y
    # registrar_abono_manual() en prestamo_strategy.py) trae además
    # monto_cuota, abonos_aplicados, cuotas_restantes y total_pagado — son
    # datos derivables (se pueden recalcular a partir del préstamo) que no
    # se persisten aquí para no duplicar información. Los 4 campos que sí
    # se guardan son los que consume usuario.html en el detalle de préstamo.
    p.pagos = [
        {
            "numero_cuota": pg.numero_cuota,
            "tipo":         pg.tipo,
            "monto":        float(pg.monto),
            "fecha":        pg.fecha.strftime(FORMATO_FECHA),
        }
        for pg in pagos
    ]

    return p


def obtener(id_prestamo: str) -> PrestamoDominio | None:
    fila = db.session.get(models.Prestamo, id_prestamo)
    if fila is None:
        return None
    return _reconstruir(fila)


def listar_por_cuenta(numero_cuenta: str) -> list:
    filas = models.Prestamo.query.filter_by(numero_cuenta=numero_cuenta).all()
    return [_reconstruir(f) for f in filas]


def listar_todos() -> list:
    filas = models.Prestamo.query.all()
    return [_reconstruir(f) for f in filas]
