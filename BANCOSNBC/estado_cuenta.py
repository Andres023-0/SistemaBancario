from abc import ABC, abstractmethod
from logger import Logger


# =============================================================================
# PATRÓN STATE — Semana 15
#
# Aplicado sobre la clase Cuenta (Contexto / Context).
# Cada vez que se intenta ejecutar una operación bancaria sobre una cuenta,
# el comportamiento depende del estado actual de la cuenta:
#   - Activa     → permite depósitos, retiros y transferencias
#   - Bloqueada  → rechaza todas las operaciones (fraude detectado)
#   - Suspendida → solo permite depósitos (revisión administrativa)
#   - Cerrada    → rechaza todo permanentemente (estado terminal)
#
# Participantes del patrón en este sistema:
#   - EstadoCuenta       → State (interfaz abstracta)
#   - Cuenta             → Context (Contexto — en cuenta.py)
#   - EstadoActiva       → ConcreteState A
#   - EstadoBloqueada    → ConcreteState B
#   - EstadoSuspendida   → ConcreteState C
#   - EstadoCerrada      → ConcreteState D (terminal)
#
# Qué resuelve vs la versión sin State:
#   SIN STATE: habría que agregar if-else dentro de depositar(),
#              retirar() y transferir() de Cuenta para verificar el estado.
#              Al agregar un nuevo estado habría que tocar TODOS los métodos
#              → OCP violado.
#
#   CON STATE: cada EstadoCuenta concreto decide qué permite y qué rechaza.
#              Agregar un nuevo estado = crear una clase nueva sin tocar nada
#              existente → OCP respetado.
#
# Integración con Observer:
#   ObservadorFraude (observer_cuenta.py) puede disparar una transición
#   Activa → Bloqueada cuando detecta riesgo alto, usando
#   cuenta.bloquear("motivo") desde fuera, sin modificar ningún observador
#   ni ningún método de operación existente.
# =============================================================================


# =============================================================================
# INTERFAZ STATE — Contrato que todos los estados deben cumplir
# =============================================================================

class EstadoCuenta(ABC):
    """
    Interfaz abstracta del patrón State para cuentas bancarias.

    Declara las operaciones que el Contexto (Cuenta) puede delegar.
    Cada estado concreto implementa qué está permitido y qué no.

    Los métodos retornan (permitido: bool, mensaje: str) para que el
    Contexto pueda informar al sistema sin conocer la lógica de cada estado.
    """

    @abstractmethod
    def puede_depositar(self) -> tuple:
        pass

    @abstractmethod
    def puede_retirar(self) -> tuple:
        pass

    @abstractmethod
    def puede_transferir(self) -> tuple:
        pass

    @abstractmethod
    def get_nombre(self) -> str:
        """Nombre del estado para logs, API y frontend."""
        pass

    @abstractmethod
    def get_descripcion(self) -> str:
        """Descripción corta del estado para mostrar en la UI."""
        pass

    def get_color(self) -> str:
        """Color CSS asociado al estado (para el badge del frontend)."""
        return "gris"


# =============================================================================
# ESTADOS CONCRETOS
# =============================================================================

class EstadoActiva(EstadoCuenta):
    """
    ConcreteState A — Cuenta operativa normal.
    Permite depósitos, retiros y transferencias sin restricciones de estado.
    Es el estado inicial de toda cuenta creada por el Builder.
    """

    def puede_depositar(self) -> tuple:
        return True, "Cuenta activa — depósito permitido"

    def puede_retirar(self) -> tuple:
        return True, "Cuenta activa — retiro permitido"

    def puede_transferir(self) -> tuple:
        return True, "Cuenta activa — transferencia permitida"

    def get_nombre(self) -> str:
        return "activa"

    def get_descripcion(self) -> str:
        return "Cuenta operativa — todas las operaciones habilitadas"

    def get_color(self) -> str:
        return "verde"


class EstadoBloqueada(EstadoCuenta):
    """
    ConcreteState B — Cuenta bloqueada por detección de fraude.
    Rechaza TODAS las operaciones hasta que un administrador la reactiva.
    """

    def __init__(self, motivo: str = "fraude detectado"):
        self._motivo = motivo

    def puede_depositar(self) -> tuple:
        return False, f"Cuenta BLOQUEADA — {self._motivo}. Contacte al banco."

    def puede_retirar(self) -> tuple:
        return False, f"Cuenta BLOQUEADA — {self._motivo}. Contacte al banco."

    def puede_transferir(self) -> tuple:
        return False, f"Cuenta BLOQUEADA — {self._motivo}. Contacte al banco."

    def get_nombre(self) -> str:
        return "bloqueada"

    def get_descripcion(self) -> str:
        return f"Cuenta bloqueada: {self._motivo}"

    def get_color(self) -> str:
        return "rojo"

    def get_motivo(self) -> str:
        return self._motivo


class EstadoSuspendida(EstadoCuenta):
    """
    ConcreteState C — Cuenta suspendida por revisión administrativa.
    Solo permite depósitos. Retiros y transferencias bloqueados.
    """

    def __init__(self, motivo: str = "revisión administrativa"):
        self._motivo = motivo

    def puede_depositar(self) -> tuple:
        return True, "Cuenta suspendida — solo depósitos permitidos"

    def puede_retirar(self) -> tuple:
        return False, f"Cuenta SUSPENDIDA — {self._motivo}. No se permiten retiros."

    def puede_transferir(self) -> tuple:
        return False, f"Cuenta SUSPENDIDA — {self._motivo}. No se permiten transferencias."

    def get_nombre(self) -> str:
        return "suspendida"

    def get_descripcion(self) -> str:
        return f"Cuenta suspendida: {self._motivo}"

    def get_color(self) -> str:
        return "naranja"

    def get_motivo(self) -> str:
        return self._motivo


class EstadoCerrada(EstadoCuenta):
    """
    ConcreteState D — Cuenta cerrada permanentemente (estado terminal).
    Rechaza TODAS las operaciones sin excepción.
    """

    def puede_depositar(self) -> tuple:
        return False, "Cuenta CERRADA permanentemente — no se aceptan operaciones."

    def puede_retirar(self) -> tuple:
        return False, "Cuenta CERRADA permanentemente — no se aceptan operaciones."

    def puede_transferir(self) -> tuple:
        return False, "Cuenta CERRADA permanentemente — no se aceptan operaciones."

    def get_nombre(self) -> str:
        return "cerrada"

    def get_descripcion(self) -> str:
        return "Cuenta cerrada definitivamente"

    def get_color(self) -> str:
        return "gris"


# =============================================================================
# PRODUCTOR DE ESTADOS — punto de entrada único
# =============================================================================

class EstadoCuentaProducer:
    """
    Retorna instancias de EstadoCuenta por nombre.
    El cliente (Cuenta, api.py) nunca instancia estados directamente.

    Uso en api.py:
        nuevo_estado = EstadoCuentaProducer.get("bloqueada", motivo="fraude")
        cuenta.set_estado(nuevo_estado)
    """

    @staticmethod
    def get(nombre: str, motivo: str = "") -> EstadoCuenta:
        nombre = nombre.lower()
        if nombre == "activa":
            return EstadoActiva()
        elif nombre == "bloqueada":
            return EstadoBloqueada(motivo or "fraude detectado")
        elif nombre == "suspendida":
            return EstadoSuspendida(motivo or "revisión administrativa")
        elif nombre == "cerrada":
            return EstadoCerrada()
        else:
            raise ValueError(
                f"Estado no soportado: '{nombre}'. "
                f"Válidos: activa, bloqueada, suspendida, cerrada"
            )

    @staticmethod
    def listar_disponibles() -> list:
        return ["activa", "bloqueada", "suspendida", "cerrada"]
