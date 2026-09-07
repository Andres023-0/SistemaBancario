"""
=============================================================================
REPOSITORIO DE ADMINISTRADOR — FASE 10
=============================================================================
Antes, las credenciales del administrador vivían como dos constantes en
auth_session.py (ADMIN_USUARIO / _ADMIN_PASSWORD_HASH) — ya no visibles en
el HTML público desde la Fase 2, pero seguían siendo texto fijo en el
código fuente. Ahora son una fila más de la tabla `administradores`.

Este repositorio es más simple que los de usuario/cuenta/préstamo: no hay
una clase de dominio "Administrador" con lógica de negocio (KYC, estado,
etc.) que reconstruir — un admin es solo un usuario y un hash de
contraseña, así que se trabaja directamente con models.Administrador.
=============================================================================
"""

import models
from database import db
from auth_session import hash_password

# Credenciales de demo que YA conocías (admin / bancouts2025). Se usan solo
# para sembrar la primera fila la primera vez que arranca el sistema contra
# una base de datos vacía — no para comparar en cada login.
ADMIN_POR_DEFECTO_USUARIO   = "admin"
ADMIN_POR_DEFECTO_PASSWORD  = "bancouts2025"


def guardar(usuario: str, password_hash: str) -> None:
    """Inserta o actualiza (upsert) un administrador."""
    fila = db.session.get(models.Administrador, usuario)
    if fila is None:
        fila = models.Administrador(usuario=usuario)
        db.session.add(fila)
    fila.password_hash = password_hash
    db.session.commit()


def obtener_hash(usuario: str):
    fila = db.session.get(models.Administrador, usuario)
    return fila.password_hash if fila else None


def existe(usuario: str) -> bool:
    return db.session.get(models.Administrador, usuario) is not None


def validar(usuario: str, password: str) -> bool:
    """Retorna True solo si el usuario existe y la contraseña coincide."""
    hash_guardado = obtener_hash(usuario)
    if hash_guardado is None:
        return False
    return hash_guardado == hash_password(password)


def sembrar_admin_por_defecto() -> None:
    """
    FASE 10: si la tabla `administradores` está completamente vacía
    (primer arranque contra esta base de datos), crea la cuenta de admin
    de siempre (admin / bancouts2025) para no romper las credenciales de
    demo que ya conocías. En cualquier arranque posterior, no hace nada.

    Se llama una sola vez al iniciar la aplicación (ver Fase 12 en api.py),
    igual que SucursalesManager siembra las sucursales por defecto.
    """
    if models.Administrador.query.first() is not None:
        return
    guardar(ADMIN_POR_DEFECTO_USUARIO, hash_password(ADMIN_POR_DEFECTO_PASSWORD))
