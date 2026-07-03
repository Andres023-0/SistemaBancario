from abc import ABC, abstractmethod
from logger import Logger


# =============================================================================
# PATRÓN BRIDGE — Lado del Implementador
#
# CanalBancario es la interfaz del Implementador: define las operaciones
# de bajo nivel que cada canal concreto debe saber hacer (validar, notificar,
# informar límites). La Abstracción (OperacionBancaria) solo conoce esta
# interfaz, nunca las clases concretas — ese es el "puente".
#
# Coexiste con canal_factory.py (Abstract Factory) sin reemplazarlo.
# Son dos patrones independientes sobre el mismo dominio.
# =============================================================================


class CanalBancario(ABC):
    """
    Implementador abstracto del patrón Bridge.
    Define la interfaz que todos los canales concretos deben cumplir.
    La Abstracción (OperacionBancaria) depende solo de esta clase,
    nunca de CanalWeb, CanalMovil ni CanalCajero directamente.
    """

    @abstractmethod
    def validar(self, monto: float, tipo: str) -> tuple[bool, str]:
        """
        Valida si el monto y tipo de operación son permitidos en este canal.
        Retorna (es_valido: bool, mensaje: str).
        """
        pass

    @abstractmethod
    def notificar(self, tipo: str, monto: float, cuenta_numero: str, usuario=None):
        """
        Envía la notificación correspondiente al canal.
        Delega internamente al Adapter correcto usando los datos del usuario.
        """
        pass

    @abstractmethod
    def get_nombre(self) -> str:
        """Retorna el nombre legible del canal (ej: 'Web', 'Móvil', 'Cajero')."""
        pass

    @abstractmethod
    def get_limite_maximo(self) -> float:
        """Retorna el monto máximo permitido por transacción en este canal."""
        pass

    @abstractmethod
    def get_limite_minimo(self) -> float:
        """Retorna el monto mínimo requerido por transacción en este canal."""
        pass


# =============================================================================
# IMPLEMENTACIONES CONCRETAS
# Una por canal. Cada una encapsula las reglas propias de su canal:
# límites, restricciones por tipo de operación y mecanismo de notificación.
# =============================================================================

class CanalWeb(CanalBancario):
    """
    Implementación concreta: canal Web.
    Permite los montos más altos del sistema. Notifica por email
    usando el EmailAdapter del patrón Adapter existente.
    """
    _MAXIMO = 50_000_000.0
    _MINIMO = 1_000.0

    def validar(self, monto: float, tipo: str) -> tuple[bool, str]:
        if monto > self._MAXIMO:
            return False, f"Web no permite {tipo} mayores a ${self._MAXIMO:,.0f}"
        if monto < self._MINIMO:
            return False, f"Monto mínimo por Web es ${self._MINIMO:,.0f}"
        return True, "Validación Web exitosa"

    def notificar(self, tipo: str, monto: float, cuenta_numero: str, usuario=None):
        from notificador_adapter import NotificadorAdapterProducer
        Logger.get_instancia().log(
            f"[BRIDGE] CanalWeb delegando notificación al EmailAdapter",
            nivel="INFO"
        )
        NotificadorAdapterProducer.get_adapter("web", usuario).notificar(
            tipo, monto, cuenta_numero
        )

    def get_nombre(self) -> str:
        return "Web"

    def get_limite_maximo(self) -> float:
        return self._MAXIMO

    def get_limite_minimo(self) -> float:
        return self._MINIMO


class CanalMovil(CanalBancario):
    """
    Implementación concreta: canal Móvil.
    Límite reducido para mayor seguridad. Notifica por SMS
    usando el SMSAdapter del patrón Adapter existente.
    """
    _MAXIMO = 5_000_000.0
    _MINIMO = 1_000.0

    def validar(self, monto: float, tipo: str) -> tuple[bool, str]:
        if monto > self._MAXIMO:
            return False, f"App Móvil no permite {tipo} mayores a ${self._MAXIMO:,.0f}"
        if monto < self._MINIMO:
            return False, f"Monto mínimo por Móvil es ${self._MINIMO:,.0f}"
        return True, "Validación Móvil exitosa"

    def notificar(self, tipo: str, monto: float, cuenta_numero: str, usuario=None):
        from notificador_adapter import NotificadorAdapterProducer
        Logger.get_instancia().log(
            f"[BRIDGE] CanalMovil delegando notificación al SMSAdapter",
            nivel="INFO"
        )
        NotificadorAdapterProducer.get_adapter("movil", usuario).notificar(
            tipo, monto, cuenta_numero
        )

    def get_nombre(self) -> str:
        return "Móvil"

    def get_limite_maximo(self) -> float:
        return self._MAXIMO

    def get_limite_minimo(self) -> float:
        return self._MINIMO


class CanalCajero(CanalBancario):
    """
    Implementación concreta: canal Cajero físico.
    No permite transferencias (solo retiros y depósitos).
    Límite más bajo del sistema. Notifica con voucher físico
    usando el VoucherAdapter del patrón Adapter existente.
    """
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

    def notificar(self, tipo: str, monto: float, cuenta_numero: str, usuario=None):
        from notificador_adapter import NotificadorAdapterProducer
        Logger.get_instancia().log(
            f"[BRIDGE] CanalCajero delegando notificación al VoucherAdapter",
            nivel="INFO"
        )
        NotificadorAdapterProducer.get_adapter("cajero", usuario).notificar(
            tipo, monto, cuenta_numero
        )

    def get_nombre(self) -> str:
        return "Cajero"

    def get_limite_maximo(self) -> float:
        return self._MAXIMO

    def get_limite_minimo(self) -> float:
        return self._MINIMO


# =============================================================================
# PRODUCTOR DE CANALES — punto de entrada único
# El cliente (OperacionBancaria o Transaccion) nunca instancia
# CanalWeb, CanalMovil ni CanalCajero directamente: siempre
# pasa por CanalBancarioProducer.get_canal(nombre).
# =============================================================================

class CanalBancarioProducer:
    """
    Punto de entrada único para obtener el canal correcto por nombre.
    Equivalente en rol al CanalFactoryProducer del Abstract Factory,
    pero devuelve un CanalBancario (Implementador) en lugar de una
    AbstractCanalFactory. Las instancias son compartidas (flyweight):
    un solo objeto por canal para todo el sistema.
    """
    _canales = {
        "web":    CanalWeb(),
        "movil":  CanalMovil(),
        "cajero": CanalCajero(),
    }

    @staticmethod
    def get_canal(nombre: str) -> CanalBancario:
        canal = CanalBancarioProducer._canales.get(nombre.lower())
        if canal is None:
            raise ValueError(
                f"Canal no soportado: '{nombre}'. "
                f"Canales válidos: web, movil, cajero"
            )
        return canal