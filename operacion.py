from abc import ABC, abstractmethod

class Operacion(ABC):
    """Interfaz para las operaciones bancarias (Producto en Factory Method)"""
    @abstractmethod
    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        pass

class OperacionDeposito(Operacion):
    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        cuenta_origen.depositar(monto, canal)

class OperacionRetiro(Operacion):
    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        cuenta_origen.retirar(monto, canal)

class OperacionTransferencia(Operacion):
    def ejecutar(self, cuenta_origen, monto, canal, cuenta_destino=None):
        if cuenta_destino is None:
            raise ValueError("Se requiere cuenta destino para transferencia")
        cuenta_origen.transferir(cuenta_destino, monto, canal)