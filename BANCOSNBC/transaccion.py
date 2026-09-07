from logger import Logger
from operacion_factory import DepositoFactory, RetiroFactory, TransferenciaFactory
from canal_factory import CanalFactoryProducer                      # ← Abstract Factory (Semana 5)
from notificador_adapter import NotificadorAdapterProducer          # ← Adapter (Semana 7)
from operacion_bridge import OperacionBancariaFactory               # ← Bridge (Semana 8)
from operacion_decorator import OperacionDecoratorProducer          # ← Decorator (Semana 9)


class Transaccion:

    # Factory Method: fábricas por tipo de operación (sin cambios)
    FACTORIES = {
        "deposito":      DepositoFactory(),
        "retiro":        RetiroFactory(),
        "transferencia": TransferenciaFactory()
    }

    CANALES_VALIDOS = {"web", "movil", "cajero"}

    # =========================================================================
    # DECORADORES ACTIVOS
    # Lista de decoradores que se aplican automáticamente en procesar_sin_bridge().
    # Para activar o desactivar un comportamiento transversal, solo se modifica
    # esta lista — ninguna clase de operación se toca.
    # Orden: el primero queda más cerca del objeto base, el último es la capa
    # exterior (se ejecuta primero al invocar ejecutar()).
    # =========================================================================
    DECORADORES_ACTIVOS = ["tiempo", "auditoria"]

    @staticmethod
    def procesar(cuenta_origen, monto, canal, cuenta_destino=None, tipo="deposito"):
        logger = Logger.get_instancia()

        # ── Validación temprana ──────────────────────────────────────────────
        if canal not in Transaccion.CANALES_VALIDOS:
            logger.log(f"Canal inválido: {canal}", nivel="ERROR")
            return False

        if tipo not in Transaccion.FACTORIES:
            logger.log(f"Tipo de operación no soportado: {tipo}", nivel="ERROR")
            return False

        # ── BRIDGE: construye el par (Operación, Canal) y delega todo el flujo
        # OperacionBancariaFactory.crear() une la abstracción (qué operación)
        # con el implementador (qué canal) en tiempo de ejecución.
        # La validación de límites, detección de fraude, ejecución y
        # notificación quedan encapsuladas dentro de OperacionBancaria.ejecutar().
        logger.log(
            f"[BRIDGE] Construyendo par: operación='{tipo}' | canal='{canal}'",
            nivel="INFO"
        )
        operacion_bridge = OperacionBancariaFactory.crear(tipo, canal)
        return operacion_bridge.ejecutar(cuenta_origen, monto, cuenta_destino)

        # ── Los pasos anteriores (Abstract Factory, Singleton, Factory Method,
        #    Adapter) siguen activos — ahora viven dentro de operacion_bridge.py
        #    y canal_bridge.py, coordinados por OperacionBancaria.ejecutar().

    # =========================================================================
    # MÉTODO LEGADO — conserva el flujo original paso a paso.
    # Útil para comparar el comportamiento del Bridge contra la versión anterior
    # o para demostración en clase sin Bridge.
    # A partir de la Semana 9 integra el patrón Decorator sobre el paso 4
    # (Factory Method), demostrando que los comportamientos transversales
    # (logging de tiempo, auditoría) se añaden sin tocar las clases de operación.
    # =========================================================================

    @staticmethod
    def procesar_sin_bridge(cuenta_origen, monto, canal, cuenta_destino=None, tipo="deposito"):
        """
        Versión original de procesar(), conservada para comparación.
        Coordina manualmente Abstract Factory, Singleton, Factory Method,
        Adapter y ahora también Decorator.
        """
        logger = Logger.get_instancia()

        # ── Validación temprana ──────────────────────────────────────────────
        if canal not in Transaccion.CANALES_VALIDOS:
            logger.log(f"Canal inválido: {canal}", nivel="ERROR")
            return False

        if tipo not in Transaccion.FACTORIES:
            logger.log(f"Tipo de operación no soportado: {tipo}", nivel="ERROR")
            return False

        # ── ABSTRACT FACTORY: obtener validador y límites del canal ──────────
        canal_factory = CanalFactoryProducer.get_factory(canal)
        validador     = canal_factory.crear_validador()
        limite        = canal_factory.crear_limite()

        # ── ADAPTER: obtener notificador con datos reales del usuario ────────
        usuario     = getattr(cuenta_origen, '_usuario_ref', None)
        notificador = NotificadorAdapterProducer.get_adapter(canal, usuario)

        # Paso 1: Validación de límites del canal (Abstract Factory)
        logger.log(
            f"Límites {limite.get_nombre_canal()}: "
            f"mín ${limite.get_limite_minimo():,.0f} | "
            f"máx ${limite.get_limite_maximo():,.0f}",
            nivel="INFO"
        )

        es_valido, mensaje_validacion = validador.validar(monto, tipo)
        if not es_valido:
            logger.log(f"❌ Validación de canal fallida: {mensaje_validacion}", nivel="ERROR")
            return False

        logger.log(f"✅ {mensaje_validacion}", nivel="INFO")

        # Paso 2: Detección de fraude (Singleton — sin cambios)
        from detector_fraude import DetectorFraude
        detector = DetectorFraude.get_instancia()
        es_segura, alertas = detector.evaluar(cuenta_origen, monto, canal, tipo, cuenta_destino)

        if not es_segura:
            logger.log("🚨 ALERTA DE FRAUDE EN TIEMPO REAL - TRANSACCIÓN BLOQUEADA", nivel="WARNING")
            for alerta in alertas:
                logger.log(f"  • {alerta}", nivel="WARNING")
            return False

        # Paso 3: Mostrar canal
        emoji = {"web": "🌐", "movil": "📱", "cajero": "🏧"}.get(canal, "🔄")
        logger.log(f"{emoji} Procesando {tipo.upper()} por {limite.get_nombre_canal().upper()}", nivel="INFO")

        # Paso 4: Factory Method → Decorator → ejecutar
        #
        # La fábrica crea el objeto base exactamente igual que antes.
        # El Decorator lo envuelve en tiempo de ejecución añadiendo los
        # comportamientos transversales definidos en DECORADORES_ACTIVOS.
        # El objeto resultante sigue siendo un Operacion — el try/except
        # y la llamada a ejecutar() no cambian en absoluto.
        try:
            factory   = Transaccion.FACTORIES[tipo]
            operacion = factory.crear_operacion()                   # Factory Method (sin cambios)

            # ── DECORATOR: envolver la operación base ────────────────────────
            # OperacionDecoratorProducer.aplicar() apila los decoradores de
            # DECORADORES_ACTIVOS sobre el objeto base. Si la lista estuviera
            # vacía, devuelve el objeto original sin modificar.
            operacion = OperacionDecoratorProducer.aplicar(         # ← Decorator (Semana 9)
                operacion,
                Transaccion.DECORADORES_ACTIVOS
            )
            # ────────────────────────────────────────────────────────────────

            operacion.ejecutar(cuenta_origen, monto, canal, cuenta_destino)
            logger.log(f"Operación {tipo} completada exitosamente", nivel="SUCCESS")

            # Paso 5: Notificación via Adapter con datos reales del usuario
            notificador.notificar(tipo, monto, cuenta_origen.numero)

            return True

        except ValueError as e:
            logger.log(f"Error al ejecutar {tipo}: {e}", nivel="ERROR")
            return False
        except Exception as e:
            logger.log(f"Error inesperado en {tipo}: {e}", nivel="ERROR")
            return False