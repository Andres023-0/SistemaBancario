from abc import ABC, abstractmethod
from canal_bridge import CanalBancario, CanalBancarioProducer
from detector_fraude import DetectorFraude
from logger import Logger


# =============================================================================
# PATRÓN BRIDGE — Lado de la Abstracción
#
# OperacionBancaria es la Abstracción base. Contiene una referencia a un
# CanalBancario (el Implementador) — esa referencia ES el puente.
# Las subclases (Deposito, Retiro, Transferencia) son las Abstracciones
# Refinadas: solo definen QUÉ operación ejecutar, sin saber nada sobre
# cómo valida, notifica o limita cada canal.
#
# Resultado: agregar un nuevo canal (ej: CorresponsalBancario) no toca
# ninguna operación. Agregar una nueva operación (ej: Prestamo) no toca
# ningún canal. Las dos jerarquías crecen de forma independiente.
# =============================================================================


class OperacionBancaria(ABC):
    """
    Abstracción base del patrón Bridge.

    Recibe un CanalBancario en el constructor — esa es la referencia
    al Implementador (el "puente"). Toda la coordinación del flujo
    (validar → detectar fraude → operar → notificar) vive aquí,
    desacoplada del canal concreto que se esté usando.

    Uso:
        canal = CanalBancarioProducer.get_canal("web")
        op    = Deposito(canal)
        exito = op.ejecutar(cuenta, 200_000)
    """

    def __init__(self, canal: CanalBancario):
        self._canal = canal  # ← el puente: referencia al Implementador

    # ── Método plantilla: coordina el flujo completo ──────────────────────────

    def ejecutar(self, cuenta_origen, monto: float, cuenta_destino=None) -> bool:
        """
        Orquesta el flujo completo de una transacción:
          1. Muestra límites del canal
          2. Valida con las reglas del canal (Bridge → CanalBancario.validar)
          3. Evalúa riesgo de fraude (Singleton → DetectorFraude)
          4. Ejecuta la operación concreta (Factory Method → _operar)
          5. Notifica al usuario (Bridge → CanalBancario.notificar → Adapter)

        Retorna True si la operación se completó, False si fue rechazada.
        """
        logger = Logger.get_instancia()
        tipo   = self.get_tipo()

        # Paso 1: informar límites del canal activo
        logger.log(
            f"Límites {self._canal.get_nombre()}: "
            f"mín ${self._canal.get_limite_minimo():,.0f} | "
            f"máx ${self._canal.get_limite_maximo():,.0f}",
            nivel="INFO"
        )

        # Paso 2: validación de límites y restricciones del canal
        es_valido, mensaje = self._canal.validar(monto, tipo)
        if not es_valido:
            logger.log(f"❌ Validación de canal fallida: {mensaje}", nivel="ERROR")
            return False
        logger.log(f"✅ {mensaje}", nivel="INFO")

        # Paso 3: detección de fraude (Singleton, sin cambios respecto al sistema)
        detector  = DetectorFraude.get_instancia()
        nombre_canal_lower = self._canal.get_nombre().lower()
        es_segura, alertas = detector.evaluar(
            cuenta_origen, monto, nombre_canal_lower, tipo, cuenta_destino
        )
        if not es_segura:
            logger.log(
                "🚨 ALERTA DE FRAUDE EN TIEMPO REAL - TRANSACCIÓN BLOQUEADA",
                nivel="WARNING"
            )
            for alerta in alertas:
                logger.log(f"  • {alerta}", nivel="WARNING")
            return False

        # Paso 4: mostrar canal activo y ejecutar operación concreta
        emoji = {"web": "🌐", "móvil": "📱", "cajero": "🏧"}.get(
            nombre_canal_lower, "🔄"
        )
        logger.log(
            f"{emoji} Procesando {tipo.upper()} por "
            f"{self._canal.get_nombre().upper()} [Bridge]",
            nivel="INFO"
        )

        try:
            # Delega la lógica de negocio a la subclase concreta
            self._operar(cuenta_origen, monto, cuenta_destino)
            logger.log(
                f"[BRIDGE] Operación {tipo} completada exitosamente",
                nivel="SUCCESS"
            )

            # Paso 5: notificación — el canal sabe qué Adapter usar
            usuario = getattr(cuenta_origen, '_usuario_ref', None)
            self._canal.notificar(tipo, monto, cuenta_origen.numero, usuario)

            return True

        except ValueError as e:
            logger.log(f"Error al ejecutar {tipo}: {e}", nivel="ERROR")
            return False
        except Exception as e:
            logger.log(f"Error inesperado en {tipo}: {e}", nivel="ERROR")
            return False

    # ── Métodos abstractos que cada subclase debe implementar ─────────────────

    @abstractmethod
    def _operar(self, cuenta_origen, monto: float, cuenta_destino=None):
        """
        Lógica de negocio específica de la operación.
        La Abstracción base no sabe cómo depositar, retirar ni transferir;
        eso es responsabilidad exclusiva de cada Abstracción Refinada.
        """
        pass

    @abstractmethod
    def get_tipo(self) -> str:
        """
        Retorna el identificador de la operación: 'deposito', 'retiro'
        o 'transferencia'. Usado en logs, validaciones y notificaciones.
        """
        pass


# =============================================================================
# ABSTRACCIONES REFINADAS
# Cada una define solo _operar() y get_tipo(). El flujo completo
# (validar, detectar fraude, notificar) lo hereda de OperacionBancaria.
# Ninguna sabe nada de Web, Móvil ni Cajero — eso lo maneja el canal.
# =============================================================================

class Deposito(OperacionBancaria):
    """
    Abstracción Refinada: depósito bancario.
    Solo sabe que hay que llamar a cuenta.depositar().
    El canal con el que fue construida decide cómo validar y notificar.
    """

    def get_tipo(self) -> str:
        return "deposito"

    def _operar(self, cuenta_origen, monto: float, cuenta_destino=None):
        canal_nombre = self._canal.get_nombre().lower()
        cuenta_origen.depositar(monto, canal_nombre)


class Retiro(OperacionBancaria):
    """
    Abstracción Refinada: retiro bancario.
    Solo sabe que hay que llamar a cuenta.retirar().
    El canal con el que fue construida decide si el monto está permitido.
    """

    def get_tipo(self) -> str:
        return "retiro"

    def _operar(self, cuenta_origen, monto: float, cuenta_destino=None):
        canal_nombre = self._canal.get_nombre().lower()
        cuenta_origen.retirar(monto, canal_nombre)


class Transferencia(OperacionBancaria):
    """
    Abstracción Refinada: transferencia entre cuentas.
    Solo sabe que hay que llamar a cuenta.transferir().
    Si el canal es Cajero, CanalCajero.validar() la rechazará antes
    de llegar aquí — la Abstracción no necesita saber eso.
    """

    def get_tipo(self) -> str:
        return "transferencia"

    def _operar(self, cuenta_origen, monto: float, cuenta_destino=None):
        if cuenta_destino is None:
            raise ValueError("Se requiere cuenta destino para transferencia")
        canal_nombre = self._canal.get_nombre().lower()
        cuenta_origen.transferir(cuenta_destino, monto, canal_nombre)


# =============================================================================
# FÁBRICA DE OPERACIONES BRIDGE — punto de entrada para Transaccion
# Encapsula la construcción del par (Abstracción, Implementador).
# El cliente nunca instancia Deposito(CanalWeb()) directamente.
# =============================================================================

class OperacionBancariaFactory:
    """
    Construye el par correcto (OperacionBancaria, CanalBancario) a partir
    del tipo de operación y el nombre del canal como strings.
    Transaccion.procesar() lo usa como punto de entrada único al Bridge.

    Uso:
        op    = OperacionBancariaFactory.crear("deposito", "web")
        exito = op.ejecutar(cuenta, 200_000)
    """

    _clases = {
        "deposito":      Deposito,
        "retiro":        Retiro,
        "transferencia": Transferencia,
    }

    @staticmethod
    def crear(tipo: str, canal: str) -> OperacionBancaria:
        """
        Retorna una OperacionBancaria concreta ya conectada al canal correcto.
        Lanza ValueError si tipo o canal no son válidos.
        """
        clase_op = OperacionBancariaFactory._clases.get(tipo.lower())
        if clase_op is None:
            raise ValueError(
                f"Tipo de operación no soportado: '{tipo}'. "
                f"Válidos: {list(OperacionBancariaFactory._clases.keys())}"
            )

        canal_obj = CanalBancarioProducer.get_canal(canal)
        return clase_op(canal_obj)