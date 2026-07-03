"""
FASE 2.2 — Configuración de Supabase vía variables de entorno.

Este módulo NO es una clase de dominio (no está en la lista de los 16
patrones). Es infraestructura pura: lee credenciales del entorno (.env
local, nunca hardcodeadas) y expone un cliente Supabase listo para usar.

Comportamiento "fail-safe": si las variables de entorno no están
definidas, PERSISTENCIA_ACTIVA queda en False y todo el sistema sigue
funcionando exactamente igual que antes de la Fase 2 (en memoria pura,
sin persistencia). Esto es lo que permite que los 32 tests existentes
sigan pasando sin tocarlos y sin necesitar credenciales reales.
"""

import os
import threading

from dotenv import load_dotenv

# Carga variables desde un archivo .env en la raíz del proyecto (si existe).
# En producción (Render, Railway, etc.) las variables ya vienen del entorno
# real y load_dotenv() simplemente no encuentra archivo y no hace nada.
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "").strip()

# La Publishable key es para el frontend (browser). El backend SIEMPRE debe
# usar la Secret key porque necesita saltarse RLS al escribir transacciones.
PERSISTENCIA_ACTIVA = bool(SUPABASE_URL and SUPABASE_SECRET_KEY)

_lock = threading.Lock()
_client = None


def get_client():
    """
    Retorna un cliente Supabase singleton, o None si la persistencia
    no está configurada (modo dev / tests).
    """
    global _client
    if not PERSISTENCIA_ACTIVA:
        return None

    if _client is None:
        with _lock:
            if _client is None:
                from supabase import create_client
                _client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    return _client
