"""
=============================================================================
PRUEBA DE LA FASE 10 — administrador_repository y auth_session
=============================================================================
Verifica que:
  1. La tabla `administradores` empieza vacía.
  2. sembrar_admin_por_defecto() crea admin/bancouts2025 la primera vez.
  3. El login (SesionManager.validar_admin) funciona con la clave correcta,
     falla con una incorrecta, y falla con un usuario que no existe.
  4. Si la clave se cambia manualmente, volver a sembrar NO la resetea
     (importante: en la Fase 12 esta función se llamará en cada arranque).

Correr con: python test_fase10.py
=============================================================================
"""

from flask import Flask
from database import init_db, crear_tablas

app = Flask(__name__)
init_db(app)
crear_tablas(app)

with app.app_context():
    import administrador_repository as ar
    from auth_session import SesionManager, hash_password

    print('--- Tabla administradores vacía ---')
    print('¿Existe admin antes de sembrar?', ar.existe('admin'))

    ar.sembrar_admin_por_defecto()
    print('¿Existe admin después de sembrar?', ar.existe('admin'))

    sm = SesionManager.get_instancia()
    print()
    print('Login con contraseña correcta (bancouts2025):', sm.validar_admin('admin', 'bancouts2025'))
    print('Login con contraseña incorrecta:', sm.validar_admin('admin', 'clave_mala'))
    print('Login con usuario inexistente:', sm.validar_admin('otro_admin', 'bancouts2025'))

    # Cambiar la clave manualmente y volver a sembrar — NO debe resetearla
    ar.guardar('admin', hash_password('otraClaveNueva'))
    ar.sembrar_admin_por_defecto()

    print()
    print('--- Tras cambiar la clave manualmente y volver a sembrar ---')
    print('¿Sigue funcionando la clave nueva?', sm.validar_admin('admin', 'otraClaveNueva'))
    print('¿La clave vieja ya NO funciona?', not sm.validar_admin('admin', 'bancouts2025'))

    print('\n=== FASE 10 VERIFICADA CORRECTAMENTE ===')
