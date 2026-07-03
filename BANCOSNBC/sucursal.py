from logger import Logger
from componente_bancario import ComponenteBancario


# =============================================================================
# PATRÓN COMPOSITE — Compuesto
#
# Sucursal ahora implementa ComponenteBancario. Como Compuesto, agrupa
# objetos Cuenta (Hojas) y delega las operaciones recursivamente:
#   - get_saldo_total() suma los saldos de todas sus cuentas hijas
#   - listar()          imprime la sucursal y luego cada cuenta con indentación
#
# El resto de la clase (agregar_cuenta, _cuentas, nombre) no cambia.
# =============================================================================


class Sucursal(ComponenteBancario):

    def __init__(self, nombre):
        if not nombre or not isinstance(nombre, str):
            raise ValueError("Nombre de sucursal inválido")
        self._nombre = nombre
        self._cuentas = []

    # ── ComponenteBancario (Compuesto) ────────────────────────────────────────

    def get_nombre(self) -> str:
        return self._nombre

    def get_saldo_total(self) -> float:
        """
        Compuesto: delega a cada Cuenta hija y acumula.
        Si no hay cuentas, retorna 0.0.
        """
        return sum(cuenta.get_saldo_total() for cuenta in self._cuentas)

    def listar(self, nivel: int = 0):
        indent = "  " * nivel
        Logger.get_instancia().log(
            f"{indent}🏦 Sucursal: {self._nombre} "
            f"| Saldo total: ${self.get_saldo_total():,.2f} "
            f"| Cuentas: {len(self._cuentas)}",
            nivel="INFO"
        )
        for cuenta in self._cuentas:
            cuenta.listar(nivel + 1)

    # ── Propiedades y métodos originales (sin cambios) ────────────────────────

    @property
    def nombre(self):
        return self._nombre

    @property
    def cuentas(self):
        return self._cuentas.copy()

    def agregar_cuenta(self, cuenta):
        if not hasattr(cuenta, 'numero'):
            raise ValueError("Objeto no es una instancia válida de Cuenta")
        if cuenta in self._cuentas:
            print(f"Cuenta {cuenta.numero} ya está asociada a {self._nombre}")
            return
        self._cuentas.append(cuenta)
        logger = Logger.get_instancia()
        logger.log(
            f"Cuenta {cuenta.numero} registrada en sucursal {self._nombre}",
            nivel="INFO"
        )