"""
=============================================================================
MODELOS DE BASE DE DATOS — FASE 6
=============================================================================
Aquí se define el ESQUEMA de la base de datos (las tablas), usando
Flask-SQLAlchemy. Estas clases son distintas de las clases de dominio que
ya existen en el proyecto (Usuario en usuario.py, Cuenta en cuenta.py,
Prestamo en prestamo_strategy.py, etc.) — por eso llevan el prefijo
"Modelo": para poder importar ambas en el mismo archivo sin choque de
nombres, por ejemplo:

    from usuario import Usuario as UsuarioDominio   # objeto con lógica de negocio
    from models  import Usuario as UsuarioBD        # fila de la tabla usuarios

Esta separación es deliberada (se completa en la Fase 8): los repositorios
serán los únicos que traduzcan entre "fila de la tabla" y "objeto de
dominio con sus métodos" (depositar(), verificar_kyc(), etc.). Por ahora,
en la Fase 6, estas clases SOLO describen el esquema — no tienen ninguna
lógica bancaria todavía.
=============================================================================
"""

from datetime import datetime
from database import db


# =============================================================================
# USUARIOS
# =============================================================================
class Usuario(db.Model):
    __tablename__ = "usuarios"

    documento       = db.Column(db.String(20), primary_key=True)
    nombre          = db.Column(db.String(120), nullable=False)
    celular         = db.Column(db.String(20),  default="")
    correo          = db.Column(db.String(120), default="")
    password_hash   = db.Column(db.String(64),  nullable=True)   # SHA-256 hex = 64 chars
    verificado_kyc  = db.Column(db.Boolean, nullable=False, default=False)

    cuentas = db.relationship("Cuenta", backref="titular", lazy=True)

    def __repr__(self):
        return f"<UsuarioBD {self.documento} - {self.nombre}>"


# =============================================================================
# ADMINISTRADORES
# =============================================================================
# Reemplaza las constantes ADMIN_USUARIO / _ADMIN_PASSWORD_HASH que hoy
# viven hardcodeadas en auth_session.py (se migran en la Fase 10).
# =============================================================================
class Administrador(db.Model):
    __tablename__ = "administradores"

    usuario       = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f"<AdministradorBD {self.usuario}>"


# =============================================================================
# SUCURSALES
# =============================================================================
class Sucursal(db.Model):
    __tablename__ = "sucursales"

    id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)

    cuentas = db.relationship("Cuenta", backref="sucursal", lazy=True)

    def __repr__(self):
        return f"<SucursalBD {self.id} - {self.nombre}>"


# =============================================================================
# CUENTAS
# =============================================================================
# El campo `estado` guarda el NOMBRE del estado (patrón State: activa /
# bloqueada / suspendida / cerrada). `motivo_estado` solo aplica a
# bloqueada/suspendida (coincide con el `motivo` que ya manejan
# EstadoBloqueada y EstadoSuspendida en estado_cuenta.py).
# =============================================================================
class Cuenta(db.Model):
    __tablename__ = "cuentas"

    numero          = db.Column(db.String(20), primary_key=True)
    documento       = db.Column(db.String(20), db.ForeignKey("usuarios.documento"), nullable=False)
    sucursal_id     = db.Column(db.Integer, db.ForeignKey("sucursales.id"), nullable=True)

    tipo            = db.Column(db.String(20), nullable=False)   # "corriente" | "ahorros"
    saldo           = db.Column(db.Numeric(14, 2), nullable=False, default=0)

    estado          = db.Column(db.String(20), nullable=False, default="activa")
    motivo_estado   = db.Column(db.String(200), nullable=True)

    fecha_creacion  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    movimientos = db.relationship("Movimiento", backref="cuenta", lazy=True,
                                   order_by="Movimiento.fecha")
    prestamos   = db.relationship("Prestamo", backref="cuenta", lazy=True)

    def __repr__(self):
        return f"<CuentaBD {self.numero} - {self.tipo} - ${self.saldo}>"


# =============================================================================
# MOVIMIENTOS (historial de depósitos, retiros y transferencias)
# =============================================================================
class Movimiento(db.Model):
    __tablename__ = "movimientos"

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cuenta_numero     = db.Column(db.String(20), db.ForeignKey("cuentas.numero"), nullable=False)

    tipo              = db.Column(db.String(20), nullable=False)   # deposito | retiro | transferencia
    monto             = db.Column(db.Numeric(14, 2), nullable=False)
    canal             = db.Column(db.String(20), nullable=False)   # web | movil | cajero
    saldo_resultante  = db.Column(db.Numeric(14, 2), nullable=False)

    # Solo se llena cuando tipo == "transferencia" (a qué cuenta fue).
    cuenta_destino    = db.Column(db.String(20), nullable=True)

    fecha             = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<MovimientoBD {self.tipo} ${self.monto} cuenta {self.cuenta_numero}>"


# =============================================================================
# PRÉSTAMOS
# =============================================================================
# El id es un string corto (uuid4()[:8].upper()) porque así ya se generan
# en prestamo_strategy.py — se conserva el mismo formato para no romper
# los préstamos existentes al migrar los datos de seed_prestamos.py.
# =============================================================================
class Prestamo(db.Model):
    __tablename__ = "prestamos"

    id                = db.Column(db.String(8), primary_key=True)
    documento         = db.Column(db.String(20), db.ForeignKey("usuarios.documento"), nullable=False)
    numero_cuenta     = db.Column(db.String(20), db.ForeignKey("cuentas.numero"), nullable=False)

    monto             = db.Column(db.Numeric(14, 2), nullable=False)
    num_cuotas        = db.Column(db.Integer, nullable=False)
    tasa_anual        = db.Column(db.Numeric(6, 4), nullable=False)
    tipo_interes      = db.Column(db.String(20), nullable=False)   # "fijo" | "variable"

    cuota_mensual     = db.Column(db.Numeric(14, 2), nullable=False)
    total_intereses   = db.Column(db.Numeric(14, 2), nullable=False)
    total_a_pagar     = db.Column(db.Numeric(14, 2), nullable=False)

    cuotas_pagadas    = db.Column(db.Integer, nullable=False, default=0)
    total_pagado      = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    estado            = db.Column(db.String(20), nullable=False, default="activo")  # activo | pagado

    fecha_creacion    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    pagos = db.relationship("PagoPrestamo", backref="prestamo", lazy=True,
                             order_by="PagoPrestamo.fecha")

    def __repr__(self):
        return f"<PrestamoBD {self.id} - ${self.monto} - {self.estado}>"


# =============================================================================
# PAGOS Y ABONOS DE PRÉSTAMOS
# =============================================================================
class PagoPrestamo(db.Model):
    __tablename__ = "pagos_prestamo"

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prestamo_id    = db.Column(db.String(8), db.ForeignKey("prestamos.id"), nullable=False)

    # FASE 8: se detectó al construir el repositorio que Prestamo.registrar_abono_manual()
    # usa valores como "Abono #1" en vez de un número de cuota — por eso este campo es
    # texto y no entero, aunque para las cuotas formales sí guarde un número ("3").
    numero_cuota   = db.Column(db.String(30), nullable=False)
    tipo           = db.Column(db.String(20), nullable=False)   # "cuota" | "manual" (abono libre)
    monto          = db.Column(db.Numeric(14, 2), nullable=False)
    fecha          = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<PagoPrestamoBD prestamo={self.prestamo_id} cuota={self.numero_cuota}>"
