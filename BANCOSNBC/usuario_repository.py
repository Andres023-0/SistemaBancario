"""
=============================================================================
REPOSITORIO DE USUARIO — FASE 8
=============================================================================
Traduce en ambos sentidos entre:
  - models.Usuario   → una fila de la tabla `usuarios` (solo datos, sin lógica)
  - usuario.Usuario   → el objeto de dominio real, con .verificar_kyc(),
                        .agregar_cuenta(), etc.

Esta es la ÚNICA parte del sistema que conoce ambos mundos a la vez. El
resto del proyecto (banco.py, usuario_facade.py, api.py) seguirá trabajando
solo con usuario.Usuario, sin saber que por debajo hay una base de datos.

IMPORTANTE: todas las funciones de este módulo deben llamarse dentro de un
contexto de aplicación de Flask (`with app.app_context(): ...`), porque
usan `models.db.session` para hablar con la base de datos. Esto se resuelve
solo en la Fase 12, cuando api.py ya esté conectado a Flask-SQLAlchemy; por
ahora, para pruebas sueltas, hay que abrir el contexto manualmente.
=============================================================================
"""

import models
from database import db
from usuario import Usuario as UsuarioDominio

# Se importa perezosamente dentro de las funciones que lo necesitan, para
# evitar un import circular: cuenta_repository también podría necesitar
# cosas de aquí en el futuro.


def guardar(usuario: UsuarioDominio) -> None:
    """
    Inserta o actualiza (upsert) un Usuario de dominio en la tabla `usuarios`.
    No toca sus cuentas — eso lo hace cuenta_repository.guardar() por
    separado, una cuenta a la vez.
    """
    fila = db.session.get(models.Usuario, usuario.documento)
    if fila is None:
        fila = models.Usuario(documento=usuario.documento)
        db.session.add(fila)

    fila.nombre         = usuario.nombre
    fila.celular        = usuario.celular
    fila.correo         = usuario.correo
    fila.password_hash  = usuario.password_hash
    fila.verificado_kyc = usuario.verificado_kyc

    db.session.commit()


def obtener(documento: str, incluir_cuentas: bool = True) -> UsuarioDominio | None:
    """
    Reconstruye un usuario.Usuario a partir de la fila `documento` de la BD.

    Por defecto también reconstruye sus cuentas (incluir_cuentas=True),
    porque banco.buscar_cuenta_por_numero() recorre usuario.cuentas — sin
    esto, un usuario recién cargado se vería como si no tuviera cuentas.

    Nota de diseño: para poblar `.cuentas` y `.verificado_kyc` con datos que
    ya sabemos válidos (vienen de la BD), no usamos agregar_cuenta() ni
    verificar_kyc() — esos métodos existen para aplicar REGLAS DE NEGOCIO
    al crear datos nuevos (ej. exigir KYC antes de aceptar una cuenta), no
    para simplemente reflejar datos que ya existían.
    """
    fila = db.session.get(models.Usuario, documento)
    if fila is None:
        return None

    u = UsuarioDominio(fila.nombre, fila.documento, fila.celular, fila.correo)
    u.verificado_kyc = fila.verificado_kyc
    u.password_hash  = fila.password_hash

    if incluir_cuentas:
        import cuenta_repository
        u.cuentas = cuenta_repository.listar_por_documento(documento)

    return u


def listar_todos(incluir_cuentas: bool = True) -> list:
    """Reconstruye TODOS los usuarios — equivalente a lo que hoy es banco.usuarios."""
    documentos = [fila.documento for fila in models.Usuario.query.all()]
    return [obtener(doc, incluir_cuentas=incluir_cuentas) for doc in documentos]


def eliminar(documento: str) -> bool:
    """
    Elimina un usuario y, en cascada, sus cuentas (que a su vez deberían
    haber sido validadas como sin saldo antes de llegar aquí — esa regla
    de negocio vive en usuario_facade.py, no en el repositorio).
    """
    fila = db.session.get(models.Usuario, documento)
    if fila is None:
        return False
    db.session.delete(fila)
    db.session.commit()
    return True


def existe(documento: str) -> bool:
    return db.session.get(models.Usuario, documento) is not None
