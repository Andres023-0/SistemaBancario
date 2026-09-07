"""
=============================================================================
BASE DE DATOS — FASE 6
=============================================================================
Antes de esta fase, TODO el estado del banco (usuarios, cuentas, saldos,
movimientos, préstamos) vivía únicamente en objetos de Python en memoria
(listas dentro de Banco, GestorPrestamos, etc.). Cada vez que se reiniciaba
api.py, todo se perdía y seed.py volvía a crear los mismos datos de prueba
desde cero.

Este módulo centraliza la conexión a una base de datos real (SQLite) usando
Flask-SQLAlchemy. Es intencionalmente pequeño: solo configura la conexión.
Las tablas se definen en models.py, y la conexión con la app de Flask se
hace en la Fase 12 (api.py llamará a init_db(app) una sola vez al arrancar).

Por qué SQLite:
  - Es un solo archivo (banco.db) en el propio proyecto, sin necesidad de
    instalar ni levantar un servidor de base de datos aparte — apropiado
    para el alcance académico de este proyecto.
  - SQLAlchemy se usa igual que con PostgreSQL/MySQL, así que si más
    adelante se quiere migrar a un motor más robusto, el cambio real es
    solo la URI de conexión (ver RUTA_BD abajo), no el código de los
    modelos ni de los repositorios.
=============================================================================
"""

import os
from flask_sqlalchemy import SQLAlchemy

# Objeto central de SQLAlchemy. Se importa desde models.py (para declarar
# las tablas) y desde api.py (para conectarlo a la app de Flask en Fase 12).
db = SQLAlchemy()

# Archivo físico de la base de datos, en la misma carpeta que api.py.
RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco.db")


def init_db(app):
    """
    Conecta la instancia de Flask con SQLAlchemy.
    Se llamará UNA sola vez desde api.py (Fase 12), justo después de crear
    la app de Flask y antes de registrar las rutas.
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{RUTA_BD}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)


def crear_tablas(app):
    """
    Crea físicamente las tablas en banco.db a partir de los modelos
    definidos en models.py, si todavía no existen.

    NOTA: esto es suficiente mientras el esquema no cambie. En cuanto el
    proyecto tenga datos reales que no se puedan perder, los cambios de
    esquema deberían hacerse con migraciones (Flask-Migrate / Alembic,
    ver Fase 12) en vez de con create_all(), que no sabe modificar tablas
    ya existentes.
    """
    with app.app_context():
        import models  # noqa: F401 (registra las tablas en el metadata de `db`)
        db.create_all()
