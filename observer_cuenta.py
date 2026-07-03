from abc import ABC, abstractmethod
from logger import Logger
from config_banco import ConfigBanco


# =============================================================================
# PATRÓN OBSERVER — Semana 14
#
# Aplicado sobre la clase Cuenta (Sujeto / Subject).
# Cada vez que una Cuenta ejecuta depositar(), retirar() o transferir(),
# notifica automáticamente a todos sus observadores suscritos.
#
# Participantes del patrón en este sistema:
#   - ObservadorCuenta       → Observer (interfaz abstracta)
#   - Cuenta                 → Subject (Sujeto concreto — en cuenta.py)
#   - ObservadorFraude       → ConcreteObserver A
#   - ObservadorSaldoCritico → ConcreteObserver B
#   - ObservadorLogMovimiento→ ConcreteObserver C
#
# Qué resuelve vs la versión anterior:
#   ANTES: OperacionBancaria.ejecutar() llamaba explícitamente a
#          DetectorFraude.get_instancia().evaluar(...) en el paso 3.
#          Si se quería agregar nueva lógica post-operación (ej: reportes,
#          alertas admin), había que modificar operacion_bridge.py → OCP violado.
#
#   AHORA: Cuenta publica el evento "movimiento_realizado" y cada observador
#          reacciona de forma independiente. Agregar un nuevo comportamiento
#          = crear una clase nueva y suscribirla. Ninguna clase existente
#          se toca → OCP respetado.
#
# Coexistencia con patrones anteriores:
#   - El DetectorFraude (Singleton) sigue existiendo sin cambios.
#     ObservadorFraude simplemente lo invoca como reacción al evento,
#     en lugar de que OperacionBancaria lo llame directamente.
#   - El Adapter (notificador_adapter.py) sigue funcionando igual.
#   - El Bridge (operacion_bridge.py) conserva su flujo, pero el paso 3
#     (fraude) se delega al Observer para mostrar el desacoplamiento.
# =============================================================================


# =============================================================================
# INTERFAZ OBSERVER — Componente abstracto
# Define el contrato que todos los observadores deben cumplir.
# El Sujeto (Cuenta) solo conoce esta interfaz, nunca las clases concretas.
# =============================================================================

class ObservadorCuenta(ABC):
    """
    Interfaz abstracta del patrón Observer para eventos de cuenta.

    El método update() recibe un diccionario con el contexto del evento:
        {
            "tipo":           str   — "deposito", "retiro", "transferencia"
            "monto":          float — monto de la operación
            "canal":          str   — "web", "movil", "cajero"
            "cuenta_origen":  Cuenta
            "cuenta_destino": Cuenta | None  (solo en transferencias)
            "saldo_nuevo":    float — saldo de la cuenta origen tras la operación
        }

    Cada observador concreto decide qué hacer con esos datos.
    El Sujeto no sabe ni le importa cómo reacciona cada uno.
    """

    @abstractmethod
    def update(self, evento: dict) -> None:
        """
        Método de callback invocado por el Sujeto cuando ocurre un movimiento.
        Parámetro evento: diccionario con el contexto completo del movimiento.
        """
        pass

    @abstractmethod
    def get_nombre(self) -> str:
        """Nombre identificador del observador (para logs y depuración)."""
        pass


# =============================================================================
# OBSERVADORES CONCRETOS
# Cada uno tiene una única responsabilidad.
# Ninguno sabe qué tipo de cuenta lo notificó ni qué otros observadores
# están suscritos — el desacoplamiento es total.
# =============================================================================

class ObservadorFraude(ObservadorCuenta):
    """
    ConcreteObserver A — Detección de fraude reactiva.

    ANTES: OperacionBancaria.ejecutar() llamaba DetectorFraude.evaluar()
           directamente en su paso 3, acoplando el Bridge al Singleton.
    AHORA: ObservadorFraude escucha el evento de movimiento y delega al
           DetectorFraude. El Bridge ya no necesita saber que el detector
           existe — solo ejecuta la operación y publica el evento.

    Si el detector genera alertas, las registra en el Logger con nivel
    WARNING. No bloquea (el bloqueo ocurre antes, en la validación del
    Bridge); aquí se trata de auditoría post-operación de riesgo.
    """

    def get_nombre(self) -> str:
        return "ObservadorFraude"

    def update(self, evento: dict) -> None:
        from detector_fraude import DetectorFraude

        logger  = Logger.get_instancia()
        cuenta  = evento["cuenta_origen"]
        monto   = evento["monto"]
        canal   = evento["canal"]
        tipo    = evento["tipo"]
        destino = evento.get("cuenta_destino")

        logger.log(
            f"[OBSERVER-FRAUDE] Evaluando riesgo post-operación — "
            f"cuenta: {cuenta.numero} | tipo: {tipo} | monto: ${monto:,.2f}",
            nivel="INFO"
        )

        detector = DetectorFraude.get_instancia()
        es_segura, alertas = detector.evaluar(cuenta, monto, canal, tipo, destino)

        if not es_segura:
            logger.log(
                f"[OBSERVER-FRAUDE] ⚠️  Se detectaron {len(alertas)} alerta(s) "
                f"en la operación ya ejecutada — registradas para auditoría:",
                nivel="WARNING"
            )
            for alerta in alertas:
                logger.log(f"  • {alerta}", nivel="WARNING")
        else:
            logger.log(
                f"[OBSERVER-FRAUDE] ✅ Sin alertas de riesgo detectadas.",
                nivel="INFO"
            )


class ObservadorSaldoCritico(ObservadorCuenta):
    """
    ConcreteObserver B — Vigilancia de saldo mínimo.

    Reacciona cuando el saldo de la cuenta cae por debajo del umbral
    definido en ConfigBanco.get_saldo_critico() (por defecto $1.000).

    Este comportamiento no existía antes: no había ningún mecanismo que
    alertara proactivamente al detectar un saldo peligrosamente bajo.
    Con Observer se agrega sin modificar ninguna clase existente.

    Solo actúa en retiros y transferencias (un depósito nunca reduce el saldo).
    """

    def get_nombre(self) -> str:
        return "ObservadorSaldoCritico"

    def update(self, evento: dict) -> None:
        tipo   = evento["tipo"]
        cuenta = evento["cuenta_origen"]
        saldo  = evento["saldo_nuevo"]

        # Solo aplica en operaciones que reducen el saldo
        if tipo not in ("retiro", "transferencia"):
            return

        umbral = ConfigBanco.get_instancia().get_saldo_critico()
        logger = Logger.get_instancia()

        if saldo <= umbral:
            logger.log(
                f"[OBSERVER-SALDO-CRITICO] 🔴 ALERTA: La cuenta {cuenta.numero} "
                f"tiene un saldo de ${saldo:,.2f}, por debajo del umbral crítico "
                f"de ${umbral:,.2f}. Se recomienda revisar.",
                nivel="WARNING"
            )
        else:
            logger.log(
                f"[OBSERVER-SALDO-CRITICO] ✅ Saldo cuenta {cuenta.numero}: "
                f"${saldo:,.2f} — dentro del umbral seguro (>${umbral:,.2f}).",
                nivel="INFO"
            )


class ObservadorLogMovimiento(ObservadorCuenta):
    """
    ConcreteObserver C — Registro detallado de movimientos.

    Genera una entrada de log estructurada después de cada operación,
    con toda la información relevante del evento. Independiente del
    Logger interno de Cuenta (que solo registra el dict de transacción);
    este observador genera un resumen legible orientado a auditoría.

    Analogía con la presentación: es el equivalente al LogWriter del
    sistema de monitoreo de servidores — registra el evento sin importar
    qué hacen los otros observadores.
    """

    def get_nombre(self) -> str:
        return "ObservadorLogMovimiento"

    def update(self, evento: dict) -> None:
        logger  = Logger.get_instancia()
        tipo    = evento["tipo"]
        monto   = evento["monto"]
        canal   = evento["canal"]
        cuenta  = evento["cuenta_origen"]
        saldo   = evento["saldo_nuevo"]
        destino = evento.get("cuenta_destino")

        destino_info = (
            f" → cuenta destino: {destino.numero}"
            if destino else ""
        )
        usuario = getattr(cuenta, '_usuario_ref', None)
        nombre_usuario = usuario.nombre if usuario else "desconocido"

        logger.log(
            f"[OBSERVER-LOG] 📋 MOVIMIENTO REGISTRADO — "
            f"Usuario: {nombre_usuario} | "
            f"Tipo: {tipo.upper()} | "
            f"Monto: ${monto:,.2f} | "
            f"Canal: {canal.upper()} | "
            f"Cuenta: {cuenta.numero}{destino_info} | "
            f"Saldo resultante: ${saldo:,.2f}",
            nivel="INFO"
        )


# =============================================================================
# PRODUCTOR DE OBSERVADORES — punto de entrada único
# Sigue el mismo patrón de los otros Producers del sistema
# (CanalFactoryProducer, CanalBancarioProducer, NotificadorAdapterProducer).
# El cliente nunca instancia observadores directamente.
# =============================================================================

class ObservadorProducer:
    """
    Construye y retorna los observadores predeterminados del sistema.

    Uso típico al crear una cuenta (en CuentaBuilder.build()):
        for obs in ObservadorProducer.get_observadores_default():
            cuenta.suscribir(obs)

    También permite obtener observadores individuales por nombre para
    suscripciones selectivas en tiempo de ejecución.
    """

    _catalogo = {
        "fraude":        ObservadorFraude,
        "saldo_critico": ObservadorSaldoCritico,
        "log":           ObservadorLogMovimiento,
    }

    @staticmethod
    def get_observador(nombre: str) -> ObservadorCuenta:
        """
        Retorna una nueva instancia del observador solicitado.
        Lanza ValueError si el nombre no es válido.
        """
        clase = ObservadorProducer._catalogo.get(nombre.lower())
        if clase is None:
            disponibles = list(ObservadorProducer._catalogo.keys())
            raise ValueError(
                f"Observador no soportado: '{nombre}'. "
                f"Disponibles: {disponibles}"
            )
        return clase()

    @staticmethod
    def get_observadores_default() -> list:
        """
        Retorna la lista completa de observadores que se suscriben
        automáticamente a cada cuenta al ser construida por el Builder.
        Orden: fraude → saldo_critico → log
        """
        return [
            ObservadorFraude(),
            ObservadorSaldoCritico(),
            ObservadorLogMovimiento(),
        ]

    @staticmethod
    def listar_disponibles() -> list:
        """Retorna los nombres de todos los observadores registrados."""
        return list(ObservadorProducer._catalogo.keys())