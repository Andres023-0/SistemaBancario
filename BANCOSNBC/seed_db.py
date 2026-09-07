"""
=============================================================================
SIEMBRA DE DATOS DE PRUEBA — FASE 11
=============================================================================
Antes de esta fase, seed.py y seed_prestamos.py se ejecutaban en CADA
arranque de api.py, porque todo vivía en memoria y había que reconstruirlo
siempre desde cero. Ahora que Banco y GestorPrestamos cargan sus datos
desde banco.db (Fase 9), volver a correr esos mismos seeds en cada arranque
duplicaría usuarios, cuentas y préstamos.

Este script:
  1. Se corre UNA SOLA VEZ, a mano (python seed_db.py) — no se llama desde
     api.py.
  2. Revisa si la base de datos ya tiene usuarios. Si los tiene, no hace
     nada (protección contra ejecutarlo dos veces por error).
  3. Si está vacía, llama a cargar_datos_prueba() (de seed.py) y
     cargar_prestamos_seed() (de seed_prestamos.py) — el mismo contenido de
     siempre (13 usuarios, sus cuentas, ~60 movimientos históricos, y 7
     préstamos), sin necesidad de reescribir esos datos.

Uso:
    python seed_db.py
=============================================================================
"""

from flask import Flask
from database import init_db, crear_tablas


def sembrar_si_esta_vacia():
    app = Flask(__name__)
    init_db(app)
    crear_tablas(app)

    with app.app_context():
        import usuario_repository as ur
        import administrador_repository as ar
        from banco import Banco
        from seed import cargar_datos_prueba
        from seed_prestamos import cargar_prestamos_seed

        # ── Admin: se siembra siempre (es idempotente por sí solo) ──────────
        ar.sembrar_admin_por_defecto()

        # ── Usuarios/cuentas/préstamos: solo si la BD está realmente vacía ──
        if ur.listar_todos(incluir_cuentas=False):
            print(
                "⚠  La base de datos ya tiene usuarios registrados — "
                "no se vuelve a sembrar (para no duplicar datos)."
            )
            print("   Si de verdad quieres reiniciar todo, borra banco.db y corre este script de nuevo.")
            return

        banco = Banco()  # con la BD vacía, arranca sin usuarios (normal)
        cargar_datos_prueba(banco)
        cargar_prestamos_seed(banco)

        print("\n✅ Siembra completa. banco.db ya tiene los datos de prueba de siempre.")


if __name__ == "__main__":
    sembrar_si_esta_vacia()
