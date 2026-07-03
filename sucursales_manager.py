import threading
from sucursal import Sucursal
from config_banco import ConfigBanco

class SucursalesManager:
    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        config = ConfigBanco.get_instancia()
        self._sucursales = [Sucursal(nombre) for nombre in config.get_sucursales()]

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = SucursalesManager()
        return cls._instancia

    @property
    def sucursales(self):
        return self._sucursales.copy()

    def agregar_sucursal(self, nombre):
        if not nombre or not isinstance(nombre, str):
            raise ValueError("Nombre de sucursal inválido")
        if any(s.nombre.lower() == nombre.lower() for s in self._sucursales):
            print(f"Sucursal '{nombre}' ya existe.")
            return
        self._sucursales.append(Sucursal(nombre))
        print(f"Nueva sucursal agregada: {nombre}")