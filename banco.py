from sucursales_manager import SucursalesManager
from logger import Logger
from componente_bancario import ComponenteBancario


# =============================================================================
# PATRÓN COMPOSITE — Compuesto raíz
#
# Banco ahora implementa ComponenteBancario. Como raíz del árbol, agrupa
# Sucursales (que a su vez agrupan Cuentas):
#   - get_saldo_total() suma recursivamente todas las sucursales → cuentas
#   - listar()          imprime el árbol completo: banco → sucursales → cuentas
#
# El resto de la clase (usuarios, agregar_usuario, buscar_*) no cambia.
# =============================================================================


class Banco(ComponenteBancario):

    def __init__(self):
        self.usuarios = []
        manager = SucursalesManager.get_instancia()
        self.sucursales = manager.sucursales

    # ── ComponenteBancario (Compuesto raíz) ───────────────────────────────────

    def get_nombre(self) -> str:
        return "Banco UTS"

    def get_saldo_total(self) -> float:
        """
        Compuesto raíz: delega a cada Sucursal hija, que a su vez
        delega a cada Cuenta. La recursión del Composite hace el trabajo.
        """
        return sum(sucursal.get_saldo_total() for sucursal in self.sucursales)

    def listar(self, nivel: int = 0):
        """
        Imprime el árbol completo:
          🏛 Banco UTS | Saldo total: $X
            🏦 Sucursal: Bucaramanga Centro | ...
              💳 Cuenta 1001 (corriente) | Saldo: $Y
              💳 Cuenta 1002 (ahorros)   | Saldo: $Z
            🏦 Sucursal: Floridablanca | ...
              ...
        """
        indent = "  " * nivel
        logger = Logger.get_instancia()
        logger.log(
            f"{indent}🏛  {self.get_nombre()} "
            f"| Saldo total consolidado: ${self.get_saldo_total():,.2f} "
            f"| Sucursales: {len(self.sucursales)}",
            nivel="INFO"
        )
        for sucursal in self.sucursales:
            sucursal.listar(nivel + 1)

    # ── Métodos originales (sin cambios) ──────────────────────────────────────

    def agregar_usuario(self, usuario):
        if usuario in self.usuarios:
            Logger.get_instancia().log(
                f"Usuario {usuario.nombre} ya registrado",
                nivel="WARNING"
            )
            return
        self.usuarios.append(usuario)
        Logger.get_instancia().log(
            f"Usuario {usuario.nombre} registrado en el banco",
            nivel="SUCCESS"
        )

    def buscar_usuario_por_documento(self, documento):
        for usuario in self.usuarios:
            if usuario.documento == documento:
                return usuario
        return None

    def buscar_cuenta_por_numero(self, numero_cuenta):
        for usuario in self.usuarios:
            for cuenta in usuario.cuentas:
                if cuenta.numero == numero_cuenta:
                    return cuenta
        return None