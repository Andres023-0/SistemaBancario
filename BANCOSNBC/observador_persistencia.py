"""
=============================================================================
OBSERVADOR DE PERSISTENCIA — FASE 9
=============================================================================
ConcreteObserver del patrón Observer ya existente en observer_cuenta.py.
Antes de esta fase, Cuenta.transacciones y Cuenta._saldo solo vivían en
memoria; el único registro de "lo que pasó" era el Logger. A partir de
ahora, cada vez que una cuenta ejecuta depositar(), retirar() o
transferir(), este observador guarda el estado resultante en banco.db —
sin que cuenta.py, operacion_bridge.py ni api.py tengan que saber que
existe una base de datos detrás.

Por qué esto encaja perfectamente con el patrón Observer que ya tenían:
es exactamente el mismo mecanismo que usa ObservadorFraude o
ObservadorLogMovimiento — una reacción más a la notificación, sin tocar
ninguna clase existente (Open/Closed Principle, tal como ya lo aprovecha
el resto de observadores del proyecto).

IMPORTANTE: al igual que los repositorios de la Fase 8, update() necesita
ejecutarse dentro de un contexto de aplicación de Flask activo. A partir de
la Fase 12 (api.py conectado a Flask-SQLAlchemy), cada petición HTTP ya
corre dentro de ese contexto automáticamente — no hay que hacer nada
especial para que esto funcione en producción.
=============================================================================
"""

from observer_cuenta import ObservadorCuenta
from logger import Logger


class ObservadorPersistencia(ObservadorCuenta):
    """
    ConcreteObserver — guarda la cuenta afectada en la base de datos
    después de cada movimiento.

    No necesita saber el documento del titular: la cuenta ya existe en la
    base de datos desde que se creó (usuario_facade.crear_cuenta() la
    guarda con su documento la primera vez), así que aquí solo se
    actualiza saldo, estado e historial de movimientos.
    """

    def get_nombre(self) -> str:
        return "ObservadorPersistencia"

    def update(self, evento: dict) -> None:
        import cuenta_repository  # import perezoso: evita ciclos de import

        cuenta = evento["cuenta_origen"]
        try:
            cuenta_repository.guardar(cuenta)
        except Exception as e:
            # Si la base de datos falla, la operación bancaria YA se
            # ejecutó en memoria (igual que fraude o saldo crítico nunca
            # bloquean la operación) — se deja constancia en el log para
            # que un admin pueda revisar la inconsistencia, en vez de
            # tumbar la petición HTTP a mitad de una transferencia.
            Logger.get_instancia().log(
                f"[PERSISTENCIA] ⚠️  No se pudo guardar la cuenta "
                f"{cuenta.numero} en la base de datos: {e}",
                nivel="WARNING"
            )
