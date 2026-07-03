import time
from abc import ABC
from operacion import Operacion
from logger import Logger


# =============================================================================
# PATRÓN DECORATOR — aplicado sobre la interfaz Operacion
#
# OperacionDecorator es el Decorator base: implementa la misma interfaz
# que los concretos (Operacion) y guarda una referencia a otro Operacion.
# Esa referencia es el "envoltorio" — el puente entre la capa decoradora
# y el objeto decorado.
#
# Las subclases concretas (LogTiempoDecorator, AuditoriaDecorator,
# ReintentoDecorator) solo añaden su comportamiento antes o después de
# delegar a self._operacion.ejecutar(). Nunca saben si están envolviendo
# un OperacionDeposito concreto u otro Decorator apilado encima.
#
# Resultado: comportamientos transversales (logging de tiempo, auditoría,
# reintentos) se activan envolviéndolos en tiempo de ejecución, sin
# modificar ninguna clase de operación existente — OCP cumplido.
#
# Coexiste con operacion_factory.py (Factory Method) y operacion_bridge.py
# (Bridge) sin reemplazarlos. Son patrones en dimensiones distintas:
#   - Factory Method  → decide QUÉ operación crear
#   - Bridge          → une operación con canal en tiempo de ejecución
#   - Decorator       → agrega comportamiento al objeto ya creado
# =============================================================================


# =============================================================================
# DECORATOR BASE
# Implementa Operacion para ser transparente al cliente.
# Guarda la referencia al objeto envuelto y delega por defecto.
# =============================================================================

class OperacionDecorator(Operacion, ABC):
    """
    Decorator base del patrón.

    Implementa Operacion (misma interfaz que OperacionDeposito, OperacionRetiro
    y OperacionTransferencia) para que el cliente no distinga entre un objeto
    concreto y uno decorado.

    Guarda self._operacion: la referencia al objeto envuelto. Puede ser un
    concreto o cualquier otro Decorator — el apilado es transparente.

    Uso:
        op = AuditoriaDecorator(LogTiempoDecorator(OperacionDeposito()))
        op.ejecutar(cuenta, 200_000, "web")
    """

    def __init__(self, operacion: Operacion):
        self._operacion = operacion

    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        """
        Comportamiento por defecto: delegar sin agregar nada.
        Las subclases sobreescriben este método añadiendo su capa
        antes y/o después de llamar a self._operacion.ejecutar().
        """
        return self._operacion.ejecutar(cuenta_origen, monto, canal, cuenta_destino)


# =============================================================================
# DECORADORES CONCRETOS
# Cada uno tiene una única responsabilidad transversal.
# Ninguno sabe qué tipo de operación está envolviendo.
# =============================================================================

class LogTiempoDecorator(OperacionDecorator):
    """
    Decorator concreto A — Logging de tiempo de ejecución.

    Mide cuántos milisegundos tarda la operación completa y registra
    el resultado en el Logger Singleton. No modifica el resultado de
    la operación ni su flujo — solo agrega observabilidad.
    Útil para detectar operaciones lentas en producción.
    """

    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        logger = Logger.get_instancia()

        nombre_op = type(self._operacion).__name__
        logger.log(
            f"[DECORATOR-TIEMPO] Iniciando medición — "
            f"operación: {nombre_op} | cuenta: {cuenta_origen.numero} | "
            f"monto: ${monto:,.2f} | canal: {canal}",
            nivel="INFO"
        )

        inicio = time.perf_counter()
        resultado = self._operacion.ejecutar(cuenta_origen, monto, canal, cuenta_destino)
        duracion_ms = (time.perf_counter() - inicio) * 1000

        logger.log(
            f"[DECORATOR-TIEMPO] {nombre_op} finalizada en {duracion_ms:.2f}ms "
            f"— resultado: {'EXITOSA' if resultado else 'RECHAZADA'}",
            nivel="SUCCESS" if resultado else "WARNING"
        )

        return resultado


class AuditoriaDecorator(OperacionDecorator):
    """
    Decorator concreto B — Registro de auditoría.

    Registra antes y después de cada operación: quién la solicitó,
    sobre qué cuenta, el monto, el canal y el resultado final.
    En producción real este registro iría a una tabla de auditoría
    inmutable (append-only) para cumplimiento regulatorio bancario.

    Obtiene el nombre del usuario desde cuenta._usuario_ref, la misma
    referencia que el Builder guarda al construir la cuenta y que el
    Adapter usa para notificaciones — sin acoplamiento adicional.
    """

    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        logger = Logger.get_instancia()

        usuario = getattr(cuenta_origen, '_usuario_ref', None)
        nombre_usuario = usuario.nombre   if usuario else "usuario desconocido"
        documento      = usuario.documento if usuario else "N/A"

        destino_info = (
            f" → cuenta destino {cuenta_destino.numero}"
            if cuenta_destino else ""
        )

        logger.log(
            f"[DECORATOR-AUDITORIA] INICIO — "
            f"Usuario: {nombre_usuario} (doc: {documento}) | "
            f"Cuenta origen: {cuenta_origen.numero}{destino_info} | "
            f"Monto: ${monto:,.2f} | Canal: {canal}",
            nivel="INFO"
        )

        resultado = self._operacion.ejecutar(cuenta_origen, monto, canal, cuenta_destino)

        saldo_actual = cuenta_origen.saldo
        logger.log(
            f"[DECORATOR-AUDITORIA] FIN — "
            f"Operación {'APROBADA' if resultado else 'RECHAZADA'} | "
            f"Saldo resultante cuenta {cuenta_origen.numero}: ${saldo_actual:,.2f}",
            nivel="SUCCESS" if resultado else "WARNING"
        )

        return resultado


class ReintentoDecorator(OperacionDecorator):
    """
    Decorator concreto C — Política de reintentos ante errores técnicos.

    Reintenta la operación hasta max_intentos veces cuando ocurre una
    excepción inesperada (error de red, timeout en integración externa,
    error transitorio). No reintenta si la operación fue rechazada por
    reglas de negocio (saldo insuficiente, límite de canal, fraude) —
    esos casos retornan False sin lanzar excepción y no deben reintentarse.

    El retardo entre intentos crece linealmente (intento × 0.1s) para
    no saturar el sistema en caso de fallo sostenido.

    Parámetro max_intentos: configurable al instanciar el decorator.
    Valor por defecto: 3 intentos.
    """

    def __init__(self, operacion: Operacion, max_intentos: int = 3):
        super().__init__(operacion)
        if max_intentos < 1:
            raise ValueError("max_intentos debe ser al menos 1")
        self._max_intentos = max_intentos

    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        logger = Logger.get_instancia()

        for intento in range(1, self._max_intentos + 1):
            try:
                resultado = self._operacion.ejecutar(
                    cuenta_origen, monto, canal, cuenta_destino
                )
                if intento > 1:
                    logger.log(
                        f"[DECORATOR-REINTENTO] Operación exitosa en intento {intento}",
                        nivel="SUCCESS"
                    )
                return resultado

            except Exception as e:
                logger.log(
                    f"[DECORATOR-REINTENTO] Intento {intento}/{self._max_intentos} "
                    f"falló con error técnico: {e}",
                    nivel="WARNING"
                )
                if intento < self._max_intentos:
                    time.sleep(intento * 0.1)

        logger.log(
            f"[DECORATOR-REINTENTO] Todos los {self._max_intentos} intentos "
            f"fallaron — operación abortada",
            nivel="ERROR"
        )
        return False


# =============================================================================
# PRODUCTOR DE DECORADORES — punto de entrada único
# El cliente nunca construye la cadena manualmente.
# Sigue el mismo patrón de los otros Producers del sistema:
# CanalFactoryProducer, CanalBancarioProducer, NotificadorAdapterProducer.
# =============================================================================

class OperacionDecoratorProducer:
    """
    Punto de entrada único para construir operaciones decoradas.
    El cliente (Transaccion) nunca instancia los decoradores directamente:
    solo llama a OperacionDecoratorProducer.aplicar(operacion, decoradores).

    Parámetros:
        operacion   — objeto Operacion base, creado por la fábrica correspondiente
        decoradores — lista de strings con los nombres de decoradores a apilar,
                      en orden de adentro hacia afuera.
                      Opciones válidas: "tiempo", "auditoria", "reintento"
        kwargs      — parámetros opcionales para decoradores configurables
                      (ej: max_intentos=5 para ReintentoDecorator)

    Ejemplo:
        base = DepositoFactory().crear_operacion()
        op   = OperacionDecoratorProducer.aplicar(base, ["tiempo", "auditoria"])
        op.ejecutar(cuenta, 200_000, "web")
    """

    _decoradores_disponibles = {
        "tiempo":    LogTiempoDecorator,
        "auditoria": AuditoriaDecorator,
        "reintento": ReintentoDecorator,
    }

    @staticmethod
    def aplicar(
        operacion: Operacion,
        decoradores: list[str],
        **kwargs
    ) -> Operacion:
        """
        Apila los decoradores indicados sobre la operación base.
        El primero de la lista queda más cerca del objeto base.
        El último queda en la capa exterior (se ejecuta primero).

        Si la lista está vacía, devuelve el objeto original sin modificar.
        Lanza ValueError si algún nombre de decorator no es válido.
        """
        logger = Logger.get_instancia()

        if not decoradores:
            return operacion

        for nombre in decoradores:
            clase = OperacionDecoratorProducer._decoradores_disponibles.get(nombre.lower())
            if clase is None:
                disponibles = list(OperacionDecoratorProducer._decoradores_disponibles.keys())
                raise ValueError(
                    f"Decorator no soportado: '{nombre}'. "
                    f"Disponibles: {disponibles}"
                )

            if nombre.lower() == "reintento" and "max_intentos" in kwargs:
                operacion = clase(operacion, max_intentos=kwargs["max_intentos"])
            else:
                operacion = clase(operacion)

            logger.log(
                f"[DECORATOR] '{nombre}' aplicado",
                nivel="INFO"
            )

        return operacion