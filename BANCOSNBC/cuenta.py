from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from logger import Logger
from componente_bancario import ComponenteBancario
import copy


# =============================================================================
# PATRÓN COMPOSITE — Hoja
# PATRÓN OBSERVER   — Subject / Sujeto concreto
# PATRÓN STATE      — Context / Contexto  ← NUEVO Semana 15
#
# Cuenta ahora es también el Contexto del patrón State.
# Mantiene una referencia a un EstadoCuenta (el State actual) y delega
# la validación de permisos a ese objeto antes de ejecutar cada operación.
#
# Cambios respecto a la versión anterior (Observer):
#   + __init__:       inicializa self._estado = EstadoActiva()
#   + set_estado()    → cambia el estado interno y lo registra en log
#   + get_estado()    → retorna el objeto estado actual
#   + bloquear()      → transición a EstadoBloqueada (usado por ObservadorFraude)
#   + suspender()     → transición a EstadoSuspendida
#   + activar()       → transición a EstadoActiva
#   + cerrar()        → transición a EstadoCerrada (terminal)
#   + depositar(), retirar(), transferir() ahora consultan al estado
#     actual antes de ejecutar → si el estado rechaza, lanzan ValueError
#     con el mensaje del estado concreto.
#
# TODO lo demás (Composite, Prototype, Observer) sin cambios.
# =============================================================================


class Cuenta(ComponenteBancario):
    TIPOS_VALIDOS = {"corriente", "ahorros"}

    def __init__(self, numero: str, tipo: str = "corriente", saldo_inicial: float = 0.0):
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Use: {', '.join(self.TIPOS_VALIDOS)}")
        self.numero = numero
        self._tipo = tipo
        self._saldo = Decimal(str(saldo_inicial)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.transacciones = []

        # ── OBSERVER: lista interna de observadores suscritos ─────────────────
        self._observadores: list = []

        # ── STATE: estado inicial de toda cuenta = Activa ─────────────────────
        from estado_cuenta import EstadoActiva
        self._estado = EstadoActiva()

    # ── ComponenteBancario (Hoja) ─────────────────────────────────────────────

    def get_nombre(self) -> str:
        return f"Cuenta {self.numero} ({self._tipo})"

    def get_saldo_total(self) -> float:
        return float(self._saldo)

    def listar(self, nivel: int = 0):
        indent = "  " * nivel
        Logger.get_instancia().log(
            f"{indent}💳 {self.get_nombre()} | Saldo: ${self.get_saldo_total():,.2f} "
            f"| Estado: {self._estado.get_nombre().upper()}",
            nivel="INFO"
        )

    # ── STATE: gestión de estado ──────────────────────────────────────────────

    def set_estado(self, nuevo_estado) -> None:
        """
        Cambia el estado interno de la cuenta (setState del patrón).
        Registra la transición en el log para auditoría.
        No permite transicionar desde EstadoCerrada (estado terminal).
        """
        from estado_cuenta import EstadoCerrada
        if isinstance(self._estado, EstadoCerrada):
            Logger.get_instancia().log(
                f"[STATE] Cuenta {self.numero}: no se puede cambiar desde estado CERRADA (terminal).",
                nivel="WARNING"
            )
            return

        estado_anterior = self._estado.get_nombre()
        self._estado = nuevo_estado
        Logger.get_instancia().log(
            f"[STATE] Cuenta {self.numero}: "
            f"{estado_anterior.upper()} → {nuevo_estado.get_nombre().upper()} "
            f"| {nuevo_estado.get_descripcion()}",
            nivel="INFO"
        )

    def get_estado(self):
        """Retorna el objeto estado actual."""
        return self._estado

    def bloquear(self, motivo: str = "fraude detectado") -> None:
        """Transición explícita a EstadoBloqueada. Usado por ObservadorFraude."""
        from estado_cuenta import EstadoBloqueada
        self.set_estado(EstadoBloqueada(motivo))

    def suspender(self, motivo: str = "revisión administrativa") -> None:
        """Transición explícita a EstadoSuspendida."""
        from estado_cuenta import EstadoSuspendida
        self.set_estado(EstadoSuspendida(motivo))

    def activar(self) -> None:
        """Transición explícita a EstadoActiva (reactiva la cuenta)."""
        from estado_cuenta import EstadoActiva
        self.set_estado(EstadoActiva())

    def cerrar(self) -> None:
        """Transición explícita a EstadoCerrada (irreversible)."""
        from estado_cuenta import EstadoCerrada
        self.set_estado(EstadoCerrada())

    # ── OBSERVER: gestión de suscripciones ───────────────────────────────────

    def suscribir(self, observador) -> None:
        if observador in self._observadores:
            Logger.get_instancia().log(
                f"[OBSERVER] {observador.get_nombre()} ya está suscrito "
                f"a la cuenta {self.numero}",
                nivel="WARNING"
            )
            return
        self._observadores.append(observador)
        Logger.get_instancia().log(
            f"[OBSERVER] {observador.get_nombre()} suscrito "
            f"a la cuenta {self.numero}",
            nivel="INFO"
        )

    def desuscribir(self, observador) -> None:
        if observador in self._observadores:
            self._observadores.remove(observador)
            Logger.get_instancia().log(
                f"[OBSERVER] {observador.get_nombre()} desuscrito "
                f"de la cuenta {self.numero}",
                nivel="INFO"
            )

    def _notificar_observadores(self, tipo: str, monto: float,
                                 canal: str, cuenta_destino=None) -> None:
        evento = {
            "tipo":           tipo,
            "monto":          monto,
            "canal":          canal,
            "cuenta_origen":  self,
            "cuenta_destino": cuenta_destino,
            "saldo_nuevo":    float(self._saldo),
        }
        for observador in self._observadores:
            try:
                observador.update(evento)
            except Exception as e:
                Logger.get_instancia().log(
                    f"[OBSERVER] ⚠️  Error en {observador.get_nombre()}: {e}",
                    nivel="WARNING"
                )

    # ── Propiedades ───────────────────────────────────────────────────────────

    @property
    def saldo(self):
        return float(self._saldo)

    @property
    def tipo(self):
        return self._tipo

    # ── Operaciones bancarias — con validación STATE antes de ejecutar ─────────

    def depositar(self, monto: float, canal: str = "web"):
        # ── STATE: consultar al estado actual antes de operar ─────────────────
        permitido, mensaje = self._estado.puede_depositar()
        if not permitido:
            Logger.get_instancia().log(
                f"[STATE] Depósito rechazado en cuenta {self.numero}: {mensaje}",
                nivel="WARNING"
            )
            raise ValueError(mensaje)
        # ─────────────────────────────────────────────────────────────────────
        monto_dec = Decimal(str(monto)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if monto_dec <= 0:
            raise ValueError("Monto debe ser positivo")
        self._saldo += monto_dec
        self._registrar("deposito", monto_dec, canal)
        self._notificar_observadores("deposito", float(monto_dec), canal)

    def retirar(self, monto: float, canal: str = "cajero"):
        # ── STATE: consultar al estado actual antes de operar ─────────────────
        permitido, mensaje = self._estado.puede_retirar()
        if not permitido:
            Logger.get_instancia().log(
                f"[STATE] Retiro rechazado en cuenta {self.numero}: {mensaje}",
                nivel="WARNING"
            )
            raise ValueError(mensaje)
        # ─────────────────────────────────────────────────────────────────────
        monto_dec = Decimal(str(monto)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if monto_dec <= 0:
            raise ValueError("Monto debe ser positivo")
        if monto_dec > self._saldo:
            raise ValueError("Saldo insuficiente")
        self._saldo -= monto_dec
        self._registrar("retiro", monto_dec, canal)
        self._notificar_observadores("retiro", float(monto_dec), canal)

    def transferir(self, cuenta_destino, monto: float, canal: str = "web"):
        # ── STATE: consultar al estado actual antes de operar ─────────────────
        permitido, mensaje = self._estado.puede_transferir()
        if not permitido:
            Logger.get_instancia().log(
                f"[STATE] Transferencia rechazada en cuenta {self.numero}: {mensaje}",
                nivel="WARNING"
            )
            raise ValueError(mensaje)
        # ─────────────────────────────────────────────────────────────────────
        monto_dec = Decimal(str(monto)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.retirar(monto, canal)
        cuenta_destino.depositar(monto, canal)
        self._registrar("transferencia", monto_dec, canal)
        self._notificar_observadores("transferencia", float(monto_dec), canal, cuenta_destino)

    def _registrar(self, tipo, monto, canal):
        reg = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": tipo,
            "monto": float(monto),
            "canal": canal,
            "saldo_final": float(self._saldo)
        }
        self.transacciones.append(reg)

    # ── Patrón PROTOTYPE ──────────────────────────────────────────────────────

    def clone(self, nuevo_numero: str) -> "Cuenta":
        nueva = copy.deepcopy(self)
        nueva.numero = nuevo_numero
        nueva.transacciones = []
        nueva._observadores = []
        # El clon nace en estado Activa independientemente del origen
        from estado_cuenta import EstadoActiva
        nueva._estado = EstadoActiva()
        Logger.get_instancia().log(
            f"[PROTOTYPE] Cuenta clonada: {self.numero} → {nuevo_numero} "
            f"(tipo: {self._tipo}, saldo: ${float(self._saldo):,.2f})",
            nivel="INFO"
        )
        return nueva
