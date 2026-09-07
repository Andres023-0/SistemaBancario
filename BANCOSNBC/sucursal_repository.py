"""
=============================================================================
REPOSITORIO DE SUCURSAL — FASE 9
=============================================================================
Más simple que los otros repositorios: sucursal.Sucursal (objeto de
dominio) solo tiene un nombre y una lista de cuentas asociadas — no tiene
un id propio. Por eso este repositorio no "reconstruye" objetos Sucursal
completos; solo administra los nombres y sus ids en la base de datos.
Quien sí reconstruye los objetos Sucursal de dominio es SucursalesManager,
usando estos nombres.
=============================================================================
"""

import models
from database import db


def guardar(nombre: str) -> int:
    """Inserta la sucursal si no existe todavía. Retorna su id en la BD."""
    fila = models.Sucursal.query.filter_by(nombre=nombre).first()
    if fila is None:
        fila = models.Sucursal(nombre=nombre)
        db.session.add(fila)
        db.session.commit()
    return fila.id


def listar_todas() -> list:
    """Retorna [(id, nombre), ...] en el orden en que se crearon."""
    filas = models.Sucursal.query.order_by(models.Sucursal.id).all()
    return [(f.id, f.nombre) for f in filas]


def obtener_id_por_nombre(nombre: str):
    fila = models.Sucursal.query.filter_by(nombre=nombre).first()
    return fila.id if fila else None
