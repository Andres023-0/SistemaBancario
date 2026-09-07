import threading
from sucursal import Sucursal
from config_banco import ConfigBanco


class SucursalesManager:
    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        import sucursal_repository as sr

        filas = sr.listar_todas()
        if not filas:
            # FASE 9: primera vez que arranca contra esta base de datos —
            # sembrar las sucursales definidas en ConfigBanco (antes esto
            # pasaba en cada arranque, en memoria; ahora solo pasa una vez).
            config = ConfigBanco.get_instancia()
            for nombre in config.get_sucursales():
                sr.guardar(nombre)
            filas = sr.listar_todas()

        # Reconstruir los objetos de dominio Sucursal, y guardar aparte el
        # id de base de datos de cada una (Sucursal no tiene id propio).
        self._sucursales = []
        self._ids_por_nombre = {}
        for id_bd, nombre in filas:
            s = Sucursal(nombre)
            self._sucursales.append(s)
            self._ids_por_nombre[nombre] = id_bd

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

    def id_de(self, sucursal: Sucursal):
        """
        FASE 9: id real en la base de datos de una Sucursal de dominio.
        Lo usa Banco.__init__() para saber a qué Sucursal pertenece cada
        cuenta cargada, y usuario_facade.crear_cuenta() para guardar el
        sucursal_id correcto en cuenta_repository.guardar().
        """
        return self._ids_por_nombre.get(sucursal.nombre)

    def agregar_sucursal(self, nombre):
        if not nombre or not isinstance(nombre, str):
            raise ValueError("Nombre de sucursal inválido")
        if any(s.nombre.lower() == nombre.lower() for s in self._sucursales):
            print(f"Sucursal '{nombre}' ya existe.")
            return

        import sucursal_repository as sr
        id_bd = sr.guardar(nombre)

        nueva = Sucursal(nombre)
        self._sucursales.append(nueva)
        self._ids_por_nombre[nombre] = id_bd
        print(f"Nueva sucursal agregada: {nombre}")
