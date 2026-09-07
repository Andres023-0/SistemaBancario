"""
=============================================================================
AUTENTICACIÓN — FASE 2
=============================================================================
Antes de esta fase, "iniciar sesión" en el sistema no existía en el
backend: login.html comparaba usuario/contraseña directamente en el
navegador (JavaScript) y guardaba el rol en sessionStorage. La API nunca
sabía quién estaba llamando, así que cualquiera podía invocar
/api/operaciones/transferir, /api/usuarios, etc. sin haber iniciado sesión,
o incluso operar cuentas ajenas con solo cambiar el número en la petición.

Este módulo agrega:
  1. hash_password()   — hashing de contraseñas (SHA-256), en vez de texto
                          plano o comparaciones hechas en el cliente.
  2. SesionManager      — SINGLETON que guarda las sesiones activas emitidas
                          por el servidor tras un login válido (token →
                          rol + cuenta asociada).
  3. requiere_sesion()  — decorador para proteger endpoints de Flask,
                          exigiendo un token válido y, opcionalmente, un rol.

Sigue siendo una implementación simple (en memoria, sin expiración por
tiempo, sin base de datos) — apropiada para el alcance académico del
proyecto — pero ahora la API sí valida identidad en cada petición sensible,
en vez de confiar ciegamente en lo que diga el frontend.
=============================================================================
"""

import hashlib
import secrets
import threading
from functools import wraps

from flask import request, g, jsonify


# =============================================================================
# HASHING DE CONTRASEÑAS
# =============================================================================
def hash_password(password: str) -> str:
    """Hash SHA-256 de una contraseña. Evita guardar/comparar texto plano."""
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


# =============================================================================
# CREDENCIALES DEL ADMINISTRADOR — FASE 10
# =============================================================================
# Antes vivían aquí mismo como dos constantes (ADMIN_USUARIO /
# _ADMIN_PASSWORD_HASH) — ya no visibles en el HTML público desde la
# Fase 2, pero seguían siendo texto fijo en el código fuente de Python.
#
# Ahora el admin es una fila más de la tabla `administradores` (ver
# administrador_repository.py). SesionManager.validar_admin() delega ahí
# en vez de comparar contra una constante local.
# =============================================================================


# =============================================================================
# SINGLETON — SesionManager
# =============================================================================
class SesionManager:
    """
    Registro en memoria de las sesiones activas del sistema.
    token -> {"rol": "admin" | "usuario", "cuenta": str | None}
    """
    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        self._sesiones = {}

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = SesionManager()
        return cls._instancia

    def crear_sesion(self, rol: str, cuenta: str = None) -> str:
        token = secrets.token_hex(24)
        self._sesiones[token] = {"rol": rol, "cuenta": cuenta}
        return token

    def obtener_sesion(self, token: str):
        return self._sesiones.get(token)

    def cerrar_sesion(self, token: str):
        self._sesiones.pop(token, None)

    def validar_admin(self, usuario: str, password: str) -> bool:
        # FASE 10: antes comparaba contra ADMIN_USUARIO/_ADMIN_PASSWORD_HASH
        # (constantes locales). Ahora consulta la tabla `administradores`.
        # Import perezoso para evitar un ciclo: administrador_repository
        # importa hash_password desde este mismo módulo.
        import administrador_repository as ar
        return ar.validar(usuario, password)


def _extraer_token() -> str:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return ""


# =============================================================================
# DECORADOR — requiere_sesion
# =============================================================================
def requiere_sesion(rol: str = None):
    """
    Protege un endpoint de Flask exigiendo un token válido.

    - Sin token o token inválido/expirado → 401.
    - Si se indica `rol` ("admin" o "usuario") y la sesión tiene otro rol → 403.
    - Si es válido, deja la sesión disponible en `flask.g.sesion` para que
      el endpoint pueda usarla (por ejemplo, para validar que un cliente
      solo opere sobre SU PROPIA cuenta).
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token  = _extraer_token()
            sesion = SesionManager.get_instancia().obtener_sesion(token) if token else None

            if not sesion:
                return jsonify({
                    "ok": False,
                    "mensaje": "No autenticado. Inicie sesión nuevamente.",
                    "data": None
                }), 401

            if rol and sesion["rol"] != rol:
                return jsonify({
                    "ok": False,
                    "mensaje": "No tiene permisos para realizar esta operación.",
                    "data": None
                }), 403

            g.sesion = sesion
            return func(*args, **kwargs)
        return wrapper
    return decorador
