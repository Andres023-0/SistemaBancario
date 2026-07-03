
from abc import ABC, abstractmethod
from logger import Logger


# =============================================================================
# PRODUCTOS ABSTRACTOS
# Definen la interfaz de cada "producto" que la fábrica puede crear
# =============================================================================

class Validador(ABC):
    """Producto abstracto A: valida una operación según reglas del canal"""
    @abstractmethod
    def validar(self, monto: float, tipo: str) -> tuple[bool, str]:
        """Retorna (es_valido, mensaje)"""
        pass


class Notificador(ABC):
    """Producto abstracto B: notifica al usuario sobre la operación"""
    @abstractmethod
    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        pass


class LimiteCanal(ABC):
    """Producto abstracto C: define límites de monto por canal"""
    @abstractmethod
    def get_limite_maximo(self) -> float:
        pass

    @abstractmethod
    def get_limite_minimo(self) -> float:
        pass

    @abstractmethod
    def get_nombre_canal(self) -> str:
        pass


# =============================================================================
# PRODUCTOS CONCRETOS - FAMILIA WEB
# =============================================================================

class ValidadorWeb(Validador):
    """Web permite montos altos, valida sesión activa"""
    _MAXIMO = 50_000_000.0
    _MINIMO = 1_000.0

    def validar(self, monto: float, tipo: str) -> tuple[bool, str]:
        if monto > self._MAXIMO:
            return False, f"Web no permite {tipo} mayores a ${self._MAXIMO:,.0f}"
        if monto < self._MINIMO:
            return False, f"Monto mínimo por Web es ${self._MINIMO:,.0f}"
        return True, "Validación Web exitosa"

class NotificadorWeb(Notificador):
    """Notifica mediante email/notificación en pantalla"""
    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        logger = Logger.get_instancia()
        logger.log(
            f"📧 [EMAIL] {tipo.upper()} de ${monto:,.2f} procesado "
            f"en cuenta {cuenta_numero} — Confirmación enviada al correo registrado",
            nivel="INFO"
        )


class LimiteCanalWeb(LimiteCanal):
    def get_limite_maximo(self) -> float:
        return 50_000_000.0   # 50 millones

    def get_limite_minimo(self) -> float:
        return 1_000.0        # 1.000 mínimo

    def get_nombre_canal(self) -> str:
        return "Web"


# =============================================================================
# PRODUCTOS CONCRETOS - FAMILIA MÓVIL
# =============================================================================

class ValidadorMovil(Validador):
    """Móvil restringe montos para mayor seguridad"""
    def validar(self, monto: float, tipo: str) -> tuple[bool, str]:
        limite = LimiteCanalMovil().get_limite_maximo()
        if monto > limite:
            return False, f"App Móvil no permite {tipo} mayores a ${limite:,.0f}"
        if monto < LimiteCanalMovil().get_limite_minimo():
            return False, f"Monto mínimo por Móvil es ${LimiteCanalMovil().get_limite_minimo():,.0f}"
        return True, "Validación Móvil exitosa"


class NotificadorMovil(Notificador):
    """Notifica mediante push notification y SMS"""
    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        logger = Logger.get_instancia()
        logger.log(
            f"📲 [PUSH + SMS] {tipo.upper()} de ${monto:,.2f} en cuenta "
            f"{cuenta_numero} — Notificación push y SMS enviados al celular",
            nivel="INFO"
        )


class LimiteCanalMovil(LimiteCanal):
    def get_limite_maximo(self) -> float:
        return 5_000_000.0    # 5 millones

    def get_limite_minimo(self) -> float:
        return 1_000.0

    def get_nombre_canal(self) -> str:
        return "Móvil"


# =============================================================================
# PRODUCTOS CONCRETOS - FAMILIA CAJERO
# =============================================================================

class ValidadorCajero(Validador):
    """Cajero solo permite retiros y depósitos, no transferencias"""
    _MAXIMO = 2_000_000.0
    _MINIMO = 10_000.0

    def validar(self, monto: float, tipo: str) -> tuple[bool, str]:
        if tipo == "transferencia":
            return False, "El cajero físico no permite transferencias entre cuentas"
        if monto > self._MAXIMO:
            return False, f"Cajero no permite {tipo} mayores a ${self._MAXIMO:,.0f}"
        if monto < self._MINIMO:
            return False, f"Monto mínimo en cajero es ${self._MINIMO:,.0f}"
        return True, "Validación Cajero exitosa"


class NotificadorCajero(Notificador):
    """Notifica mediante voucher físico impreso"""
    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        logger = Logger.get_instancia()
        logger.log(
            f"🧾 [VOUCHER] {tipo.upper()} de ${monto:,.2f} en cuenta "
            f"{cuenta_numero} — Comprobante impreso en cajero",
            nivel="INFO"
        )


class LimiteCanalCajero(LimiteCanal):
    def get_limite_maximo(self) -> float:
        return 2_000_000.0    # 2 millones

    def get_limite_minimo(self) -> float:
        return 10_000.0       # 10.000 mínimo (billetes)

    def get_nombre_canal(self) -> str:
        return "Cajero"


# =============================================================================
# ABSTRACT FACTORY
# Declara los métodos de creación para cada producto de la familia
# =============================================================================

class AbstractCanalFactory(ABC):
    """
    Fábrica abstracta: declara métodos para crear cada producto de la familia.
    Cada canal concreto implementa esta interfaz produciendo su familia completa.
    """

    @abstractmethod
    def crear_validador(self) -> Validador:
        pass

    @abstractmethod
    def crear_notificador(self) -> Notificador:
        pass

    @abstractmethod
    def crear_limite(self) -> LimiteCanal:
        pass


# =============================================================================
# FÁBRICAS CONCRETAS — una por canal (familia completa y coherente)
# =============================================================================

class WebFactory(AbstractCanalFactory):
    """Fábrica concreta: produce la familia completa para el canal Web"""

    def crear_validador(self) -> Validador:
        return ValidadorWeb()

    def crear_notificador(self) -> Notificador:
        return NotificadorWeb()

    def crear_limite(self) -> LimiteCanal:
        return LimiteCanalWeb()


class MovilFactory(AbstractCanalFactory):
    """Fábrica concreta: produce la familia completa para el canal Móvil"""

    def crear_validador(self) -> Validador:
        return ValidadorMovil()

    def crear_notificador(self) -> Notificador:
        return NotificadorMovil()

    def crear_limite(self) -> LimiteCanal:
        return LimiteCanalMovil()


class CajeroFactory(AbstractCanalFactory):
    """Fábrica concreta: produce la familia completa para el canal Cajero"""

    def crear_validador(self) -> Validador:
        return ValidadorCajero()

    def crear_notificador(self) -> Notificador:
        return NotificadorCajero()

    def crear_limite(self) -> LimiteCanal:
        return LimiteCanalCajero()


# =============================================================================
# PRODUCTOR DE FÁBRICAS — punto de entrada para obtener la fábrica correcta
# El cliente solo llama a CanalFactoryProducer.get_factory(canal)
# =============================================================================

class CanalFactoryProducer:
    """
    Equivalente al FactoryProducer del diagrama de la Semana 5.
    Devuelve la fábrica concreta correcta según el canal solicitado.
    El cliente nunca instancia directamente WebFactory, MovilFactory, etc.
    """
    _fabricas = {
        "web":    WebFactory(),
        "movil":  MovilFactory(),
        "cajero": CajeroFactory(),
    }

    @staticmethod
    def get_factory(canal: str) -> AbstractCanalFactory:
        factory = CanalFactoryProducer._fabricas.get(canal.lower())
        if factory is None:
            raise ValueError(f"Canal no soportado: '{canal}'. Canales válidos: web, movil, cajero")
        return factory
