from banco import Banco
from logger import Logger
from sucursales_manager import SucursalesManager
from cuenta_prototype import CuentaPrototypeRegistry
from cuenta_builder import CuentaBuilder
from operacion_decorator import OperacionDecoratorProducer
from operacion_factory import DepositoFactory, RetiroFactory, TransferenciaFactory
from transaccion import Transaccion

# ── FACADE (Semana 10) ────────────────────────────────────────────────────────
from operacion_facade import OperacionFacade
from usuario_facade import UsuarioFacade

# ── OBSERVER (Semana 14) ──────────────────────────────────────────────────────
from observer_cuenta import ObservadorProducer


# =============================================================================
# INICIALIZACIÓN
# =============================================================================

logger         = Logger.get_instancia()
banco          = Banco()
op_facade      = OperacionFacade(banco)
usuario_facade = UsuarioFacade(banco)

logger.log("¡Bienvenido al Sistema Bancario Core!")
sucursales = SucursalesManager.get_instancia().sucursales
logger.log(f"Sucursales disponibles: {[s.nombre for s in sucursales]}")

# ── FASE 2: bootstrap de estado (reconstruye desde Supabase o siembra) ────────
import estado_inicial
estado_inicial.inicializar_estado(banco, usuario_facade)


# =============================================================================
# HELPERS DE ENTRADA
# =============================================================================

def mostrar_menu():
    logger.log("\n" + "=" * 65)
    logger.log("          SISTEMA BANCARIO CORE - BUCARAMANGA")
    logger.log("=" * 65)
    logger.log("=== OPERACIONES BÁSICAS ===")
    logger.log("1.  Registrar nuevo usuario")
    logger.log("2.  Verificar KYC de un usuario")
    logger.log("3.  Crear nueva cuenta para un usuario")
    logger.log("4.  Depositar dinero")
    logger.log("5.  Retirar dinero")
    logger.log("6.  Transferir entre cuentas")
    logger.log("\n=== CONSULTAS Y GESTIÓN ===")
    logger.log("7.  Consultar saldo e historial de una cuenta")
    logger.log("8.  Consultar saldos totales de usuario")
    logger.log("9.  Ver todos los usuarios existentes")
    logger.log("10. Ver sucursales y cuentas asociadas")
    logger.log("\n=== PATRONES DE DISEÑO (Demostración) ===")
    logger.log("11. Registrar cuenta como prototipo")
    logger.log("12. Clonar cuenta desde prototipo")
    logger.log("13. Configurar decoradores activos")
    logger.log("14. Demostrar Decorator")
    logger.log("17. Demostrar Observer ")
    logger.log("\n=== HERRAMIENTAS DE DESARROLLO ===")
    logger.log("15. Eliminar usuario")
    logger.log("16. Ver logs del sistema")
    logger.log("0.  Salir")
    logger.log("=" * 65)
    return input("Seleccione una opción (0-17): ").strip()


def pedir_monto(prompt):
    while True:
        monto_str = input(prompt).strip()
        try:
            monto = float(monto_str)
            if monto <= 0:
                logger.log("El monto debe ser mayor que cero.", nivel="WARNING")
                continue
            return monto
        except ValueError:
            logger.log("Ingrese un número válido (ej: 50000).", nivel="WARNING")


def pedir_canal():
    logger.log("\nCanales disponibles:")
    logger.log("-" * 40)
    logger.log("1. Web")
    logger.log("2. Móvil")
    logger.log("3. Cajero")
    logger.log("-" * 40)
    while True:
        seleccion = input("Seleccione el número del canal (1-3): ").strip()
        if seleccion == "1":
            return "web"
        elif seleccion == "2":
            return "movil"
        elif seleccion == "3":
            return "cajero"
        else:
            logger.log("Por favor ingrese 1, 2 o 3.", nivel="WARNING")


def pedir_sucursal():
    sucursales = usuario_facade.get_sucursales()
    logger.log("\nSucursales disponibles:")
    logger.log("-" * 40)
    for i, s in enumerate(sucursales, 1):
        logger.log(f"{i}. {s.nombre}")
    logger.log("-" * 40)
    while True:
        try:
            sel = int(input(f"Seleccione sucursal (1-{len(sucursales)}): "))
            if 1 <= sel <= len(sucursales):
                return sucursales[sel - 1], sel
            logger.log(f"Ingrese un número entre 1 y {len(sucursales)}.", nivel="WARNING")
        except ValueError:
            logger.log("Entrada inválida. Debe ingresar un número.", nivel="WARNING")


# =============================================================================
# BUCLE PRINCIPAL
# =============================================================================

if __name__ == "__main__":

    while True:
        opcion = mostrar_menu()

        # ── 0. Salir ──────────────────────────────────────────────────────────
        if opcion == "0":
            logger.log("\nGracias por usar el Sistema Bancario. ¡Hasta pronto!")
            break

        # ── 1. Registrar nuevo usuario ────────────────────────────────────────
        elif opcion == "1":
            nombre    = input("Nombre completo: ").strip()
            documento = input("Número de documento (cédula): ").strip()
            celular   = input("Número de celular (ej: +573001234567): ").strip()
            correo    = input("Correo electrónico: ").strip()
            usuario_facade.registrar_usuario(nombre, documento, celular, correo)

        # ── 2. Verificar KYC ──────────────────────────────────────────────────
        elif opcion == "2":
            documento = input("Documento del usuario: ").strip()
            usuario_facade.verificar_kyc(documento)

        # ── 3. Crear nueva cuenta ─────────────────────────────────────────────
        elif opcion == "3":
            documento = input("Documento del usuario: ").strip()
            numero    = input("Número de cuenta (ej: 3001): ").strip()

            logger.log("\nTipos de cuenta disponibles:")
            logger.log("-" * 40)
            logger.log("1. Corriente")
            logger.log("2. Ahorros")
            logger.log("-" * 40)
            tipo_seleccionado = None
            while tipo_seleccionado is None:
                sel = input("Seleccione el tipo (1-2): ").strip()
                if sel == "1":
                    tipo_seleccionado = "corriente"
                elif sel == "2":
                    tipo_seleccionado = "ahorros"
                else:
                    logger.log("Por favor ingrese 1 o 2.", nivel="WARNING")

            saldo_inicial = pedir_monto("Saldo inicial ($): ")
            _, indice_suc = pedir_sucursal()

            usuario_facade.crear_cuenta(
                documento, numero, tipo_seleccionado, saldo_inicial, indice_suc
            )

        # ── 4. Depositar ──────────────────────────────────────────────────────
        elif opcion == "4":
            numero_cuenta = input("Número de cuenta: ").strip()
            monto         = pedir_monto("Monto a depositar: ")
            canal         = pedir_canal()
            op_facade.depositar(numero_cuenta, monto, canal)

        # ── 5. Retirar ────────────────────────────────────────────────────────
        elif opcion == "5":
            numero_cuenta = input("Número de cuenta: ").strip()
            monto         = pedir_monto("Monto a retirar: ")
            canal         = pedir_canal()
            op_facade.retirar(numero_cuenta, monto, canal)

        # ── 6. Transferir ─────────────────────────────────────────────────────
        elif opcion == "6":
            origen_num  = input("Número de cuenta origen: ").strip()
            destino_num = input("Número de cuenta destino: ").strip()
            monto       = pedir_monto("Monto a transferir: ")
            canal       = pedir_canal()
            op_facade.transferir(origen_num, destino_num, monto, canal)

        # ── 7. Consultar saldo e historial ────────────────────────────────────
        elif opcion == "7":
            numero_cuenta = input("Número de cuenta: ").strip()
            op_facade.consultar_cuenta(numero_cuenta)

        # ── 8. Saldos totales de usuario ──────────────────────────────────────
        elif opcion == "8":
            documento = input("Documento del usuario: ").strip()
            op_facade.consultar_saldos_usuario(documento)

        # ── 9. Ver todos los usuarios ─────────────────────────────────────────
        elif opcion == "9":
            usuario_facade.listar_usuarios()

        # ── 10. Ver sucursales y cuentas ──────────────────────────────────────
        elif opcion == "10":
            logger.log("\n=== SUCURSALES Y CUENTAS ASOCIADAS ===")
            for sucursal in SucursalesManager.get_instancia().sucursales:
                logger.log(f"\nSucursal: {sucursal.nombre}")
                if sucursal.cuentas:
                    logger.log(f"  Cuentas asociadas ({len(sucursal.cuentas)}):")
                    for cuenta in sucursal.cuentas:
                        logger.log(
                            f"    - {cuenta.numero} ({cuenta.tipo}) "
                            f"| Saldo: ${cuenta.saldo:,.2f}"
                        )
                else:
                    logger.log("  No tiene cuentas asociadas aún.")
            logger.log("=" * 50)

        # ── 11. Registrar prototipo ───────────────────────────────────────────
        elif opcion == "11":
            logger.log("\n=== REGISTRAR PROTOTIPO ===")
            numero_cuenta = input("Número de cuenta a usar como prototipo: ").strip()
            cuenta = banco.buscar_cuenta_por_numero(numero_cuenta)
            if not cuenta:
                logger.log("Cuenta no encontrada.", nivel="WARNING")
                continue
            existentes = CuentaPrototypeRegistry.listar()
            if existentes:
                logger.log(f"Prototipos ya registrados: {existentes}", nivel="INFO")
            nombre_proto = input("Nombre clave para este prototipo (ej: ahorros_estandar): ").strip()
            if not nombre_proto:
                logger.log("❌ El nombre no puede estar vacío.", nivel="ERROR")
                continue
            try:
                CuentaPrototypeRegistry.registrar(nombre_proto, cuenta)
                logger.log(
                    f"✅ Cuenta {numero_cuenta} registrada como prototipo '{nombre_proto}'.",
                    nivel="SUCCESS"
                )
                CuentaPrototypeRegistry.mostrar_todos()
            except ValueError as e:
                logger.log(f"❌ Error: {e}", nivel="ERROR")

        # ── 12. Clonar cuenta desde prototipo ─────────────────────────────────
        elif opcion == "12":
            logger.log("\n=== CLONAR CUENTA DESDE PROTOTIPO ===")
            prototipos = CuentaPrototypeRegistry.listar()
            if not prototipos:
                logger.log(
                    "❌ No hay prototipos registrados. Use la opción 11 primero.",
                    nivel="WARNING"
                )
                continue
            logger.log("Prototipos disponibles:")
            logger.log("-" * 40)
            CuentaPrototypeRegistry.mostrar_todos()
            logger.log("-" * 40)
            nombre_proto = input("Nombre del prototipo a usar: ").strip()
            try:
                cuenta_origen = CuentaPrototypeRegistry.get(nombre_proto)
            except ValueError as e:
                logger.log(f"❌ {e}", nivel="ERROR")
                continue

            documento = input("Documento del usuario para la cuenta clonada: ").strip()
            usuario   = banco.buscar_usuario_por_documento(documento)
            if not usuario:
                logger.log("Usuario no encontrado.", nivel="WARNING")
                continue
            if not usuario.verificado_kyc:
                logger.log("❌ El usuario debe tener KYC verificado.", nivel="ERROR")
                continue

            nuevo_numero = input("Número para la cuenta clonada (ej: 3002): ").strip()
            if banco.buscar_cuenta_por_numero(nuevo_numero):
                logger.log("❌ Ese número de cuenta ya existe.", nivel="WARNING")
                continue

            sucursal_obj, _ = pedir_sucursal()
            try:
                cuenta_clonada = (
                    CuentaBuilder()
                    .numero(nuevo_numero)
                    .asociar_usuario(usuario)
                    .asociar_sucursal(sucursal_obj)
                    .clone_desde(cuenta_origen)
                )
                logger.log(
                    f"✅ Cuenta {nuevo_numero} creada exitosamente por clonación.",
                    nivel="SUCCESS"
                )
                logger.log(f"   Tipo heredado: {cuenta_clonada.tipo}")
                logger.log(f"   Saldo heredado: ${cuenta_clonada.saldo:,.2f}")
            except ValueError as e:
                logger.log(f"❌ Error al clonar: {e}", nivel="ERROR")

        # ── 13. Configurar decoradores activos ────────────────────────────────
        elif opcion == "13":
            logger.log("\n=== CONFIGURAR DECORADORES ACTIVOS [DECORATOR] ===")
            logger.log("-" * 50)
            logger.log("Decoradores disponibles:")
            logger.log("  tiempo    — mide milisegundos de cada operación")
            logger.log("  auditoria — registra usuario, cuenta y resultado")
            logger.log("  reintento — reintenta ante errores técnicos")
            logger.log("-" * 50)
            logger.log(
                f"Decoradores activos actualmente: {Transaccion.DECORADORES_ACTIVOS}",
                nivel="INFO"
            )
            logger.log("Opciones:")
            logger.log("  1. Solo tiempo")
            logger.log("  2. Solo auditoría")
            logger.log("  3. Tiempo + Auditoría  (recomendado)")
            logger.log("  4. Auditoría + Reintento")
            logger.log("  5. Tiempo + Auditoría + Reintento  (máxima cobertura)")
            logger.log("  6. Sin decoradores  (comportamiento original)")
            logger.log("-" * 50)
            configuraciones = {
                "1": ["tiempo"],
                "2": ["auditoria"],
                "3": ["tiempo", "auditoria"],
                "4": ["auditoria", "reintento"],
                "5": ["tiempo", "auditoria", "reintento"],
                "6": [],
            }
            seleccion = input("Seleccione configuración (1-6): ").strip()
            if seleccion in configuraciones:
                Transaccion.DECORADORES_ACTIVOS = configuraciones[seleccion]
                nuevos = Transaccion.DECORADORES_ACTIVOS
                if nuevos:
                    logger.log(f"✅ Decoradores actualizados: {nuevos}", nivel="SUCCESS")
                else:
                    logger.log("✅ Decoradores desactivados.", nivel="SUCCESS")
            else:
                logger.log("Opción inválida.", nivel="WARNING")

        # ── 14. Demostrar Decorator ───────────────────────────────────────────
        elif opcion == "14":
            logger.log("\n=== DEMOSTRACIÓN PATRÓN DECORATOR ===")
            logger.log("-" * 50)
            logger.log(
                "Esta opción usa procesar_sin_bridge() para ver los decoradores.",
                nivel="INFO"
            )
            logger.log(
                f"Decoradores activos: {Transaccion.DECORADORES_ACTIVOS}",
                nivel="INFO"
            )
            logger.log("-" * 50)
            numero_cuenta = input("Número de cuenta: ").strip()
            cuenta = banco.buscar_cuenta_por_numero(numero_cuenta)
            if not cuenta:
                logger.log("Cuenta no encontrada.", nivel="WARNING")
                continue

            logger.log("\nTipo de operación:")
            logger.log("  1. Depósito")
            logger.log("  2. Retiro")
            sel_tipo = input("Seleccione (1-2): ").strip()
            tipo_op  = "deposito" if sel_tipo == "1" else "retiro" if sel_tipo == "2" else None
            if not tipo_op:
                logger.log("Opción inválida.", nivel="WARNING")
                continue

            monto = pedir_monto("Monto ($): ")
            canal = pedir_canal()
            logger.log("\n" + "─" * 50)
            logger.log("[DECORATOR] Iniciando flujo con decoradores apilados...")
            logger.log("─" * 50)
            exito = Transaccion.procesar_sin_bridge(
                cuenta_origen=cuenta, monto=monto, canal=canal, tipo=tipo_op
            )
            logger.log("─" * 50)
            if exito:
                logger.log("✅ Operación completada con decoradores activos.", nivel="SUCCESS")
                logger.log(f"Saldo actual: ${cuenta.saldo:,.2f}")
            else:
                logger.log("❌ Operación no completada.", nivel="ERROR")

        # ── 15. Eliminar usuario ──────────────────────────────────────────────
        elif opcion == "15":
            logger.log("\n=== ELIMINAR USUARIO DEL SISTEMA ===")
            documento = input("Ingrese el número de documento del usuario a eliminar: ").strip()

            usuario = banco.buscar_usuario_por_documento(documento)
            if not usuario:
                logger.log("❌ No se encontró ningún usuario con ese documento.", nivel="ERROR")
                continue

            logger.log(f"\nUsuario encontrado:")
            logger.log(f"   Nombre:   {usuario.nombre}")
            logger.log(f"   KYC:      {'Verificado' if usuario.verificado_kyc else 'No verificado'}")
            logger.log(f"   Cuentas:  {len(usuario.cuentas)}")
            if usuario.cuentas:
                logger.log("   ¡ADVERTENCIA! Cuentas que serán desvinculadas:")
                for cuenta in usuario.cuentas:
                    logger.log(f"     - {cuenta.numero} ({cuenta.tipo}): ${cuenta.saldo:,.2f}")

            confirm = input(
                "\n¿Está completamente seguro? (Escriba 'ELIMINAR' en mayúsculas): "
            ).strip()
            if confirm != "ELIMINAR":
                logger.log("Operación cancelada por el usuario.", nivel="WARNING")
                continue

            usuario_facade.eliminar_usuario(documento)

        # ── 16. Ver logs del sistema ──────────────────────────────────────────
        elif opcion == "16":
            logs = Logger.get_instancia().get_logs()
            logger.log("\n=== REGISTRO DE LOGS DEL SISTEMA ===")
            if logs:
                for entry in logs:
                    print(entry)
            else:
                logger.log("No hay logs aún.")
            logger.log("=" * 50)

        # ── 17. Demostrar Observer ────────────────────────────────────────────
        elif opcion == "17":
            logger.log("\n=== DEMOSTRACIÓN PATRÓN OBSERVER [Semana 14] ===")
            logger.log("-" * 60)
            logger.log(
                "Cada cuenta tiene suscritos 3 observadores desde su creación:\n"
                "  1. ObservadorFraude       — evalúa riesgo post-operación\n"
                "  2. ObservadorSaldoCritico — alerta si el saldo baja del umbral\n"
                "  3. ObservadorLogMovimiento— registra el evento con detalle",
                nivel="INFO"
            )
            logger.log("-" * 60)

            numero_cuenta = input("Número de cuenta para la demo (ej: 1001): ").strip()
            cuenta = banco.buscar_cuenta_por_numero(numero_cuenta)
            if not cuenta:
                logger.log("Cuenta no encontrada.", nivel="WARNING")
                continue

            logger.log(
                f"\nCuenta {cuenta.numero} — observadores activos: "
                f"{len(cuenta._observadores)}",
                nivel="INFO"
            )
            for obs in cuenta._observadores:
                logger.log(f"  → {obs.get_nombre()}", nivel="INFO")

            logger.log("\nOpciones de demostración:")
            logger.log("  1. Depósito normal   (sin alertas esperadas)")
            logger.log("  2. Retiro que deja saldo crítico  (activa ObservadorSaldoCritico)")
            logger.log("  3. Desuscribir un observador y operar sin él")
            logger.log("  4. Volver al menú principal")
            logger.log("-" * 60)

            sub_op = input("Seleccione (1-4): ").strip()

            if sub_op == "1":
                # ── Demo A: depósito normal, los 3 observadores reaccionan ───
                monto = pedir_monto("Monto a depositar ($): ")
                canal = pedir_canal()
                logger.log("\n" + "─" * 60)
                logger.log("[OBSERVER] Ejecutando depósito — se notificarán los 3 observadores...")
                logger.log("─" * 60)
                cuenta.depositar(monto, canal)
                logger.log("─" * 60)
                logger.log(
                    f"✅ Depósito completado. Saldo: ${cuenta.saldo:,.2f}\n"
                    f"   Revisar arriba las reacciones de cada observador.",
                    nivel="SUCCESS"
                )

            elif sub_op == "2":
                # ── Demo B: retiro que deja saldo por debajo del umbral crítico
                saldo_actual = cuenta.saldo
                umbral = 1_000.0
                monto_sugerido = max(saldo_actual - umbral + 1, 1.0)
                logger.log(
                    f"\nSaldo actual: ${saldo_actual:,.2f} | "
                    f"Umbral crítico: ${umbral:,.2f}",
                    nivel="INFO"
                )
                logger.log(
                    f"Para activar la alerta, retire más de ${saldo_actual - umbral:,.2f}",
                    nivel="INFO"
                )
                monto = pedir_monto("Monto a retirar ($): ")
                canal = pedir_canal()
                logger.log("\n" + "─" * 60)
                logger.log("[OBSERVER] Ejecutando retiro — ObservadorSaldoCritico activará alerta...")
                logger.log("─" * 60)
                try:
                    cuenta.retirar(monto, canal)
                    logger.log("─" * 60)
                    logger.log(
                        f"✅ Retiro completado. Saldo resultante: ${cuenta.saldo:,.2f}",
                        nivel="SUCCESS"
                    )
                except ValueError as e:
                    logger.log(f"❌ {e}", nivel="ERROR")

            elif sub_op == "3":
                # ── Demo C: desuscribir un observador y ver que ya no reacciona
                logger.log("\nObservadores activos actualmente:")
                for i, obs in enumerate(cuenta._observadores, 1):
                    logger.log(f"  {i}. {obs.get_nombre()}")
                logger.log("-" * 40)
                disponibles = ObservadorProducer.listar_disponibles()
                logger.log(f"Nombres válidos para desuscribir: {disponibles}")
                nombre_obs = input("Nombre del observador a desuscribir: ").strip()

                # Buscar el observador en la lista de la cuenta
                obs_encontrado = next(
                    (o for o in cuenta._observadores
                     if nombre_obs.lower() in o.get_nombre().lower()),
                    None
                )
                if not obs_encontrado:
                    logger.log(
                        f"❌ No se encontró un observador con ese nombre en la cuenta.",
                        nivel="WARNING"
                    )
                else:
                    cuenta.desuscribir(obs_encontrado)
                    logger.log(
                        f"\nObservadores restantes: {len(cuenta._observadores)}",
                        nivel="INFO"
                    )
                    monto = pedir_monto("\nAhora ingrese un monto a depositar para verificar: ")
                    canal = pedir_canal()
                    logger.log("\n" + "─" * 60)
                    logger.log(f"[OBSERVER] Solo {len(cuenta._observadores)} observador(es) recibirán el evento...")
                    logger.log("─" * 60)
                    cuenta.depositar(monto, canal)
                    logger.log("─" * 60)
                    logger.log(
                        f"✅ Operación completada. El observador desuscrito no reaccionó.",
                        nivel="SUCCESS"
                    )
                    # Volver a suscribir para no dejar la cuenta incompleta
                    cuenta.suscribir(obs_encontrado)
                    logger.log(
                        f"[OBSERVER] {obs_encontrado.get_nombre()} re-suscrito automáticamente.",
                        nivel="INFO"
                    )

            elif sub_op == "4":
                continue

            else:
                logger.log("Opción inválida.", nivel="WARNING")

        else:
            logger.log("Opción inválida. Intente de nuevo.", nivel="WARNING")