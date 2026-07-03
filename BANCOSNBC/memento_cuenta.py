from datetime import datetime
from logger import Logger
import threading


# =============================================================================
# PATRÓN MEMENTO — Historial de estados de cuenta
#
# Permite guardar y restaurar el estado interno de una Cuenta sin exponer
# su representación interna. Aplicado sobre los cambios de estado (State)
# de cada cuenta bancaria.
#
# Participantes:
#   - MementoEstadoCuenta   → Memento (almacena el estado capturado)
#   - Cuenta                → Originator (crea y restaura desde Memento)
#                             ← se agregan métodos guardar_memento() y restaurar_memento()
#   - CaretakerCuenta       → Caretaker (gestiona la pila de mementos por cuenta)
#   - GestorMementos        → Singleton que centraliza todos los CaretakerCuenta
#
# Qué resuelve:
#   SIN MEMENTO: cambiar estado de activa → bloqueada es irreversible desde
#                el sistema sin lógica adicional en cada endpoint.
#   CON MEMENTO: antes de cada cambio de estado se guarda un snapshot.
#                El endpoint /api/cuentas/estado/restaurar revierte al anterior
#                sin necesidad de conocer los internos de Cuenta ni EstadoCuenta.
#
# Coexistencia con State:
#   El Memento NO reemplaza al State. State define qué permite cada estado.
#   Memento guarda/restaura cuál estado está activo. Son ortogonales.
# =============================================================================


# =============================================================================
# MEMENTO — Snapshot del estado de una cuenta
# =============================================================================

class MementoEstadoCuenta:
    """
    Memento: almacena una instantánea del estado de una cuenta.

    Solo el Originator (Cuenta) puede crear y leer el contenido real.
    El Caretaker solo recibe, guarda y devuelve el objeto opaco.

    Campos guardados:
        - estado_obj   : referencia al objeto EstadoCuenta activo
        - nombre_estado: string del estado (para mostrar en logs/API)
        - motivo       : motivo del estado si aplica (Bloqueada, Suspendida)
        - fecha        : timestamp del momento en que se creó el memento
        - numero_cuenta: para identificar a qué cuenta pertenece
    """

    def __init__(self, estado_obj, nombre_estado: str, motivo: str,
                 numero_cuenta: str):
        self._estado_obj    = estado_obj
        self._nombre_estado = nombre_estado
        self._motivo        = motivo
        self._numero_cuenta = numero_cuenta
        self._fecha         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Solo el Originator debería llamar estos métodos
    def _get_estado_obj(self):
        return self._estado_obj

    def _get_nombre(self):
        return self._nombre_estado

    def _get_motivo(self):
        return self._motivo

    def get_fecha(self) -> str:
        return self._fecha

    def get_numero_cuenta(self) -> str:
        return self._numero_cuenta

    def to_dict(self) -> dict:
        """Representación pública para la API (no expone internos)."""
        return {
            "numero_cuenta": self._numero_cuenta,
            "estado":        self._nombre_estado,
            "motivo":        self._motivo,
            "fecha":         self._fecha,
        }


# =============================================================================
# CARETAKER — Gestor de mementos de UNA cuenta
# =============================================================================

class CaretakerCuenta:
    """
    Caretaker: gestiona la pila de mementos de una cuenta específica.
    No inspecciona ni modifica el contenido de los mementos.
    Solo guarda, apila y entrega de vuelta al Originator.

    Límite máximo de snapshots por cuenta: MAX_HISTORIAL (default 10).
    Cuando se supera, se descarta el más antiguo (FIFO).
    """

    MAX_HISTORIAL = 10

    def __init__(self, numero_cuenta: str):
        self._numero_cuenta = numero_cuenta
        self._pila: list[MementoEstadoCuenta] = []

    def guardar(self, memento: MementoEstadoCuenta):
        """Apila un nuevo memento. Si se supera el límite, elimina el más antiguo."""
        self._pila.append(memento)
        if len(self._pila) > self.MAX_HISTORIAL:
            self._pila.pop(0)
        Logger.get_instancia().log(
            f"[MEMENTO] Snapshot guardado para cuenta {self._numero_cuenta} "
            f"| Estado: {memento._get_nombre()} "
            f"| Historial: {len(self._pila)} snapshot(s)",
            nivel="INFO"
        )

    def deshacer(self) -> MementoEstadoCuenta | None:
        """
        Extrae y retorna el último memento guardado (undo).
        Retorna None si no hay snapshots.
        """
        if not self._pila:
            Logger.get_instancia().log(
                f"[MEMENTO] No hay snapshots para restaurar en cuenta {self._numero_cuenta}.",
                nivel="WARNING"
            )
            return None
        return self._pila.pop()

    def ver_historial(self) -> list[dict]:
        """Retorna el historial completo de snapshots (de más antiguo a más reciente)."""
        return [m.to_dict() for m in self._pila]

    def tiene_historial(self) -> bool:
        return len(self._pila) > 0

    def total_snapshots(self) -> int:
        return len(self._pila)


# =============================================================================
# GESTOR DE MEMENTOS — Singleton central
# Un CaretakerCuenta por cada número de cuenta registrado en el sistema.
# =============================================================================

class GestorMementos:
    """
    Singleton que centraliza todos los CaretakerCuenta del sistema.
    El cliente (api.py) nunca instancia CaretakerCuenta directamente.

    Uso típico en api.py:
        # Antes de cambiar estado:
        GestorMementos.get_instancia().guardar_estado(cuenta)

        # Para restaurar:
        GestorMementos.get_instancia().restaurar_estado(cuenta)
    """

    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        self._caretakers: dict[str, CaretakerCuenta] = {}

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = GestorMementos()
        return cls._instancia

    def _get_caretaker(self, numero_cuenta: str) -> CaretakerCuenta:
        """Obtiene o crea el Caretaker de una cuenta."""
        if numero_cuenta not in self._caretakers:
            self._caretakers[numero_cuenta] = CaretakerCuenta(numero_cuenta)
        return self._caretakers[numero_cuenta]

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def guardar_estado(self, cuenta) -> MementoEstadoCuenta:
        """
        Originator: captura el estado actual de la cuenta y lo guarda.
        Debe llamarse ANTES de cambiar el estado.

        Retorna el memento creado (para confirmación en la API).
        """
        estado_actual = cuenta.get_estado()
        motivo = ""
        if hasattr(estado_actual, 'get_motivo'):
            motivo = estado_actual.get_motivo()

        memento = MementoEstadoCuenta(
            estado_obj    = estado_actual,
            nombre_estado = estado_actual.get_nombre(),
            motivo        = motivo,
            numero_cuenta = cuenta.numero,
        )
        self._get_caretaker(cuenta.numero).guardar(memento)
        return memento

    def restaurar_estado(self, cuenta) -> dict:
        """
        Originator: restaura el último estado guardado en la cuenta.
        Retorna dict con { ok, estado_restaurado, estado_anterior } para la API.
        """
        caretaker = self._get_caretaker(cuenta.numero)
        memento   = caretaker.deshacer()

        if memento is None:
            return {
                "ok":      False,
                "mensaje": f"No hay estado anterior para restaurar en cuenta {cuenta.numero}."
            }

        estado_anterior_nombre = cuenta.get_estado().get_nombre()

        # Restaurar el objeto estado directamente en la cuenta
        cuenta._estado = memento._get_estado_obj()

        Logger.get_instancia().log(
            f"[MEMENTO] Estado RESTAURADO en cuenta {cuenta.numero}: "
            f"{estado_anterior_nombre.upper()} → {memento._get_nombre().upper()} "
            f"| Snapshot del: {memento.get_fecha()}",
            nivel="SUCCESS"
        )

        return {
            "ok":               True,
            "mensaje":          f"Estado restaurado exitosamente.",
            "estado_anterior":  estado_anterior_nombre,
            "estado_restaurado": memento._get_nombre(),
            "snapshot_fecha":   memento.get_fecha(),
            "snapshots_restantes": caretaker.total_snapshots(),
        }

    def ver_historial(self, numero_cuenta: str) -> list[dict]:
        """Retorna el historial de snapshots de una cuenta."""
        return self._get_caretaker(numero_cuenta).ver_historial()

    def tiene_historial(self, numero_cuenta: str) -> bool:
        return self._get_caretaker(numero_cuenta).tiene_historial()

    def total_snapshots(self, numero_cuenta: str) -> int:
        return self._get_caretaker(numero_cuenta).total_snapshots()
