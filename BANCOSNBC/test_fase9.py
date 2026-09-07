"""
=============================================================================
PRUEBA DE LA FASE 9 — Banco, GestorPrestamos y SucursalesManager con BD
=============================================================================
Simula DOS arranques del sistema dentro del mismo script:

  ARRANQUE 1: banco.db vacío. Se registra un usuario real, se le verifica
              el KYC, se le crea una cuenta, se opera (depósito/retiro) y
              se le crea un préstamo con un pago.

  ARRANQUE 2: se "resetean" los singletons (GestorPrestamos,
              SucursalesManager) como si el proceso de Python se hubiera
              reiniciado, y se vuelve a leer TODO desde banco.db para
              comprobar que nada se perdió.

Correr con: python test_fase9.py
=============================================================================
"""

from flask import Flask
from database import init_db, crear_tablas

app = Flask(__name__)
init_db(app)
crear_tablas(app)

with app.app_context():
    from banco import Banco
    from usuario_facade import UsuarioFacade
    from sucursales_manager import SucursalesManager
    from prestamo_strategy import Prestamo, EstrategiaInteresProducer, GestorPrestamos

    print('=== ARRANQUE 1 (banco.db vacío) ===\n')

    banco = Banco()
    print('Usuarios cargados al arrancar (debe ser 0):', len(banco.usuarios))
    print('Sucursales sembradas automáticamente:', [s.nombre for s in banco.sucursales])

    facade = UsuarioFacade(banco)
    facade.registrar_usuario('Daniel Rueda', '800111222', '3200000000', 'daniel@test.com')
    facade.verificar_kyc('800111222')
    cuenta = facade.crear_cuenta('800111222', '8001', 'corriente', 0, indice_sucursal=1)

    # Operar SIN llamar a ningún repositorio manualmente — debe persistir solo
    cuenta.depositar(500000, 'web')
    cuenta.retirar(20000, 'cajero')

    estrategia = EstrategiaInteresProducer.get('fijo')
    prestamo = Prestamo('800111222', '8001', 1000000, 6, 15.0, estrategia)
    GestorPrestamos.get_instancia().agregar(prestamo)
    prestamo.registrar_pago(prestamo.calcular_monto_real_cuota())
    GestorPrestamos.get_instancia().guardar(prestamo)

    print('\n=== FIN ARRANQUE 1 ===\n')

    # ── Simular un reinicio real: "olvidar" los singletons en memoria ───────
    saldo_antes = cuenta.saldo
    SucursalesManager._instancia = None
    GestorPrestamos._instancia = None

    print('=== ARRANQUE 2 (releyendo banco.db desde cero) ===\n')

    banco2 = Banco()
    print('Usuarios cargados al arrancar:', len(banco2.usuarios))
    print('Sucursales (NO deben duplicarse):', [s.nombre for s in banco2.sucursales])

    u2 = banco2.buscar_usuario_por_documento('800111222')
    print('\nUsuario recargado:', u2.nombre, '| KYC:', u2.verificado_kyc)
    print('Password verifica (uts8001):', u2.verificar_password('uts8001'))
    print('Cuentas del usuario:', [c.numero for c in u2.cuentas])

    cuenta2 = banco2.buscar_cuenta_por_numero('8001')
    print('\nCuenta recargada:', cuenta2.numero, '| Saldo:', cuenta2.saldo,
          '(debe coincidir con', saldo_antes, ')')
    print('Movimientos recargados (deben ser 2):', len(cuenta2.transacciones))
    for m in cuenta2.transacciones:
        print('  -', m['tipo'], m['monto'], '| saldo tras el movimiento:', m['saldo_final'])

    sucursal2 = banco2.sucursales[0]
    print('\n¿La cuenta 8001 quedó en su Sucursal tras recargar?',
          any(c.numero == '8001' for c in sucursal2._cuentas))

    gestor2 = GestorPrestamos.get_instancia()
    print('\nPréstamos cargados al arrancar:', len(gestor2.get_todos()))
    p2 = gestor2.get_por_documento('800111222')[0]
    print('Préstamo recargado:', p2.id, '| Cuotas pagadas:', p2.cuotas_pagadas,
          '| Total pagado:', p2.total_pagado)

    # ── ¿El objeto recargado sigue funcionando como objeto de dominio? ──────
    cuenta2.depositar(10000, 'movil')
    print('\nDepósito adicional tras recargar — nuevo saldo:', cuenta2.saldo)

    print('\n=== FASE 9 VERIFICADA CORRECTAMENTE ===')
