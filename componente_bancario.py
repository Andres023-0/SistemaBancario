from abc import ABC, abstractmethod


# =============================================================================
# PATRÓN COMPOSITE — Componente abstracto
#
# ComponenteBancario es la interfaz común que comparten tanto las Hojas
# (Cuenta) como los Compuestos (Sucursal, Banco).
# El cliente opera siempre sobre esta interfaz, sin importar si está
# tratando con una cuenta individual o con un grupo de cuentas/sucursales.
#
# Participantes del patrón en este sistema:
#   - ComponenteBancario  → Componente (esta interfaz)
#   - Cuenta              → Hoja       (no tiene hijos, retorna su propio saldo)
#   - Sucursal            → Compuesto  (agrupa Cuentas)
#   - Banco               → Compuesto raíz (agrupa Sucursales)
# =============================================================================


class ComponenteBancario(ABC):
    """
    Interfaz común del patrón Composite.
    Define las operaciones que tienen sentido tanto para hojas como compuestos.
    """

    @abstractmethod
    def get_nombre(self) -> str:
        """Retorna el nombre identificador del componente."""
        pass

    @abstractmethod
    def get_saldo_total(self) -> float:
        """
        Retorna el saldo total del componente.
        - Hoja (Cuenta):      retorna su propio saldo.
        - Compuesto (Sucursal, Banco): suma recursivamente los hijos.
        """
        pass

    @abstractmethod
    def listar(self, nivel: int = 0):
        """
        Muestra en el log la estructura del componente con indentación.
        nivel indica la profundidad en el árbol (0 = raíz).
        """
        pass