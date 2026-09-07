from sucursales_manager import SucursalesManager
from logger import Logger
from componente_bancario import ComponenteBancario


# =============================================================================
# PATRÓN COMPOSITE — Compuesto raíz
#
# Banco implementa ComponenteBancario. Como raíz del árbol, agrupa
# Sucursales (que a su vez agrupan Cuentas):
#   - get_saldo_total() suma recursivamente todas las sucursales → cuentas
#   - listar()          imprime el árbol completo: banco → sucursales → cuentas
#
# FASE 9 — PERSISTENCIA:
# Antes, self.usuarios empezaba SIEMPRE vacío (una lista nueva en cada
# arranque) y seed.py lo volvía a llenar desde cero. Ahora, al construirse,
# Banco carga los usuarios (con sus cuentas, saldos e historial ya
# reconstruidos) directamente desde la base de datos, a través de
# usuario_repository. Las búsquedas (buscar_usuario_por_documento,
# buscar_cuenta_por_numero) siguen siendo recorridos en memoria — igual de
# rápidos que antes — porque todo ya se cargó una sola vez al arrancar.
# =============================================================================


class Banco(ComponenteBancario):

    def __init__(self):
        import usuario_repository as ur
        import cuenta_repository as cr

        manager = SucursalesManager.get_instancia()
        self.sucursales = manager.sucursales

        # Cargar todos los usuarios (con sus cuentas ya reconstruidas,
        # incluido saldo, estado y todo el historial de movimientos).
        self.usuarios = ur.listar_todos()

        # Reconstruir la asociación Sucursal → Cuentas (para el Composite
        # y los reportes por sucursal). El objeto Cuenta no guarda su
        # propia sucursal, así que se usa el mapa de la tabla `cuentas`.
        mapa_sucursal = cr.mapa_sucursal_por_cuenta()
        for usuario in self.usuarios:
            for cuenta in usuario.cuentas:
                sucursal_id = mapa_sucursal.get(cuenta.numero)
                if sucursal_id is None:
                    continue
                sucursal = next(
                    (s for s in self.sucursales if manager.id_de(s) == sucursal_id),
                    None
                )
                if sucursal is not None and cuenta not in sucursal._cuentas:
                    sucursal._cuentas.append(cuenta)

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

    # ── Usuarios ───────────────────────────────────────────────────────────────

    def agregar_usuario(self, usuario):
        if usuario in self.usuarios:
            Logger.get_instancia().log(
                f"Usuario {usuario.nombre} ya registrado",
                nivel="WARNING"
            )
            return
        self.usuarios.append(usuario)

        import usuario_repository as ur
        ur.guardar(usuario)

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
