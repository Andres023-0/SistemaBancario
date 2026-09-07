"""
=============================================================================
PRUEBA DE LA FASE 8 — repositorios (Usuario, Cuenta, Prestamo)
=============================================================================
Este script crea datos de dominio REALES (un usuario, una cuenta con
movimientos, un préstamo con un pago y un abono), los guarda a través de
los repositorios en banco.db, y luego los vuelve a leer COMO SI el sistema
se hubiera reiniciado — para comprobar que nada se pierde ni se corrompe.

Correr con: python test_fase8.py
=============================================================================
"""

from flask import Flask
from database import init_db, crear_tablas

app = Flask(__name__)
init_db(app)
crear_tablas(app)

with app.app_context():
    import usuario_repository as ur
    import cuenta_repository as cr
    import prestamo_repository as pr
    from usuario import Usuario
    from cuenta import Cuenta
    from prestamo_strategy import Prestamo, EstrategiaInteresProducer

    # 1) Crear usuario de dominio real (con sus reglas normales)
    u = Usuario('Camila Torres', '900111222', '3111111111', 'camila@test.com')
    u.verificar_kyc()
    u.establecer_password('claveSegura123')

    # 2) Crear cuenta, operar (depósito/retiro), y bloquearla
    c1 = Cuenta('7001', 'ahorros', 0)
    u.agregar_cuenta(c1)
    c1.depositar(1000000, 'web')
    c1.retirar(50000, 'cajero')
    c1.bloquear('prueba fase 8')

    # 3) Crear préstamo real y pagar una cuota + un abono
    estrategia = EstrategiaInteresProducer.get('fijo')
    p1 = Prestamo('900111222', '7001', 2000000, 12, 18.0, estrategia)
    p1.registrar_pago(p1.calcular_monto_real_cuota())
    p1.registrar_abono_manual(150000)

    # 4) GUARDAR todo a través de los repositorios
    ur.guardar(u)
    cr.guardar(c1, documento=u.documento)
    pr.guardar(p1)

    print('\n=== GUARDADO COMPLETO ===\n')

with app.app_context():
    # 5) Simular un reinicio: leer TODO de vuelta desde la BD
    u2 = ur.obtener('900111222')
    print('Usuario recargado:', u2.nombre, '| KYC:', u2.verificado_kyc)
    print('Password verifica correctamente:', u2.verificar_password('claveSegura123'))
    print('Cuentas del usuario:', [c.numero for c in u2.cuentas])

    c2 = cr.obtener('7001')
    print('\nCuenta recargada:', c2.numero, '| Saldo:', c2.saldo, '| Tipo:', c2.tipo)
    print('Estado:', c2.get_estado().get_nombre(), '| Motivo:', c2.get_estado().get_motivo())
    print('Movimientos recargados:', len(c2.transacciones))
    for m in c2.transacciones:
        print('  -', m)

    p2 = pr.obtener(p1.id)
    print('\nPrestamo recargado:', p2.id, '| Estado:', p2.estado, '| Cuota:', p2.cuota_mensual)
    print('Cuotas pagadas:', p2.cuotas_pagadas, '| Total pagado:', p2.total_pagado)
    print('Pagos recargados:', p2.pagos)

    # 6) Verificar que el objeto recargado SIGUE funcionando como objeto de dominio
    print('\n¿Puede seguir operando el objeto recargado? Intentando depositar en cuenta bloqueada...')
    try:
        c2.depositar(1000, 'web')
        print('‼ ERROR: debió haber sido rechazado por el patrón STATE')
    except ValueError as e:
        print('✅ Rechazado correctamente por el patrón STATE:', e)
