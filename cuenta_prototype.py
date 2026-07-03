from cuenta import Cuenta
from logger import Logger


class CuentaPrototypeRegistry:
    """
    Patrón Prototype — Registro de prototipos.
    Actúa como catálogo de cuentas plantilla ya configuradas y válidas.
    El cliente registra una cuenta base y luego solicita clones de ella
    sin conocer los detalles internos de construcción.

    Uso:
        # Registrar un prototipo
        CuentaPrototypeRegistry.registrar("ahorros_estandar", cuenta)

        # Obtener el prototipo para clonar desde él
        proto = CuentaPrototypeRegistry.get("ahorros_estandar")

        # Clonar via Builder
        nueva = (CuentaBuilder()
            .numero("3002")
            .asociar_usuario(usuario)
            .asociar_sucursal(sucursal)
            .clone_desde(proto))
    """

    _prototipos: dict[str, Cuenta] = {}

    # ── Registro ──────────────────────────────────────────────────────────────

    @classmethod
    def registrar(cls, nombre: str, cuenta: Cuenta):
        """
        Guarda una cuenta como prototipo bajo un nombre clave.
        Si ya existía un prototipo con ese nombre, lo sobreescribe
        y notifica en el log.
        """
        if not nombre or not isinstance(nombre, str):
            raise ValueError("El nombre del prototipo no puede estar vacío")

        existia = nombre in cls._prototipos
        cls._prototipos[nombre] = cuenta

        Logger.get_instancia().log(
            f"[PROTOTYPE] Prototipo '{ nombre }' "
            f"{'actualizado' if existia else 'registrado'} — "
            f"tipo: {cuenta.tipo} | saldo: ${cuenta.saldo:,.2f}",
            nivel="INFO"
        )

    # ── Consulta ──────────────────────────────────────────────────────────────

    @classmethod
    def get(cls, nombre: str) -> Cuenta:
        """
        Retorna la cuenta prototipo registrada bajo ese nombre.
        Lanza ValueError si no existe, listando los disponibles
        para orientar al usuario.
        """
        if nombre not in cls._prototipos:
            disponibles = cls.listar()
            raise ValueError(
                f"Prototipo '{nombre}' no existe. "
                f"Disponibles: {disponibles if disponibles else '(ninguno aún)'}"
            )
        return cls._prototipos[nombre]

    @classmethod
    def listar(cls) -> list[str]:
        """Retorna los nombres de todos los prototipos registrados."""
        return list(cls._prototipos.keys())

    @classmethod
    def eliminar(cls, nombre: str):
        """
        Elimina un prototipo del registro.
        Útil si una cuenta plantilla queda obsoleta.
        """
        if nombre not in cls._prototipos:
            raise ValueError(f"Prototipo '{nombre}' no existe, no se puede eliminar")
        del cls._prototipos[nombre]
        Logger.get_instancia().log(
            f"[PROTOTYPE] Prototipo '{nombre}' eliminado del registro",
            nivel="INFO"
        )

    @classmethod
    def mostrar_todos(cls):
        """
        Imprime en el log el estado completo del registro.
        Útil para la opción de depuración del menú.
        """
        logger = Logger.get_instancia()
        if not cls._prototipos:
            logger.log("[PROTOTYPE] No hay prototipos registrados.", nivel="INFO")
            return
        logger.log(f"[PROTOTYPE] Prototipos registrados ({len(cls._prototipos)}):", nivel="INFO")
        for nombre, cuenta in cls._prototipos.items():
            logger.log(
                f"  • '{nombre}' → tipo: {cuenta.tipo} | "
                f"saldo: ${cuenta.saldo:,.2f} | "
                f"número base: {cuenta.numero}",
                nivel="INFO"
            )