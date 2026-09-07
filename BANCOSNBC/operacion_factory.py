from abc import ABC, abstractmethod
from operacion import Operacion, OperacionDeposito, OperacionRetiro, OperacionTransferencia

class OperacionFactory(ABC):
    """Creador abstracto (Factory Method)"""
    @abstractmethod
    def crear_operacion(self) -> Operacion:
        pass

class DepositoFactory(OperacionFactory):
    def crear_operacion(self) -> Operacion:
        return OperacionDeposito()

class RetiroFactory(OperacionFactory):
    def crear_operacion(self) -> Operacion:
        return OperacionRetiro()

class TransferenciaFactory(OperacionFactory):
    def crear_operacion(self) -> Operacion:
        return OperacionTransferencia()