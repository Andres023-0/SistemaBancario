from abc import ABC, abstractmethod
from datetime import datetime
from logger import Logger
import threading


# =============================================================================
# PATRÓN COMMAND — Semana 17
#
# Encapsula operaciones bancarias (depósito, retiro, transferencia) como
# objetos Command. Cada command sabe cómo ejecutarse Y cómo deshacerse.
#
# Participantes:
#   - ComandoBancario         → Command (interfaz abstracta)
#   - ComandoDeposito         → ConcreteCommand A
#   - ComandoRetiro           → ConcreteCommand B
#   - ComandoTransferencia    → ConcreteCommand C
#   - HistorialComandos       → Invoker (Singleton)
#   - Cuenta                  → Receiver (ya existe en cuenta.py)
#
# Qué resuelve vs la solución sin Command:
#   SIN COMMAND: las operaciones son irreversibles desde el sistema.
#                Agregar auditoría/undo requiere modificar cada operación.
#   CON COMMAND: cada operación es un objeto que puede ejecutarse,
#                deshacerse y repetirse. El Invoker las registra todas
#                automáticamente sin tocar Cuenta ni Transaccion.
#
# Coexistencia con patrones anteriores:
#   - Los Commands usan cuenta.depositar/retirar/transferir (State + Observer)
#   - El Invoker se integra en api.py como nuevo endpoint
#   - Bridge y Decorator siguen activos para sus propios flujos
# =============================================================================


# =============================================================================
# INTERFAZ COMMAND
# =============================================================================

class ComandoBancario(ABC):
    """
    Interfaz abstracta del patrón Command para operaciones bancarias.

    ejecutar() realiza la operación.
    deshacer() la revierte exactamente al estado anterior.
    get_descripcion() retorna un resumen legible para el historial.
    """

    @abstractmethod
    def ejecutar(self) -> dict:
        """
        Ejecuta la operación bancaria.
        Retorna dict con { ok, mensaje, datos } para la API.
        """
        pass

    @abstractmethod
    def deshacer(self) -> dict:
        """
        Deshace la operación ejecutada.
        Solo se puede llamar después de ejecutar().
        Retorna dict con { ok, mensaje, datos }.
        """
        pass

    @abstractmethod
    def get_descripcion(self) -> str:
        """Descripción corta para mostrar en el historial."""
        pass

    @abstractmethod
    def get_tipo(self) -> str:
        """Tipo de comando: 'deposito', 'retiro', 'transferencia'."""
        pass


# =============================================================================
# CONCRETE COMMAND A — DEPÓSITO
# =============================================================================

class ComandoDeposito(ComandoBancario):
    """
    ConcreteCommand A — Encapsula un depósito bancario.

    ejecutar(): deposita el monto en la cuenta.
    deshacer(): retira el mismo monto (operación inversa exacta).

    Guarda el saldo antes del depósito para verificar consistencia
    al deshacer, aunque la operación inversa es siempre el retiro.
    """

    def __init__(self, cuenta, monto: float, canal: str = "web"):
        self._cuenta        = cuenta
        self._monto         = monto
        self._canal         = canal
        self._saldo_antes   = None    # se registra en ejecutar()
        self._ejecutado     = False
        self._fecha         = None

    def ejecutar(self) -> dict:
        if self._ejecutado:
            return {"ok": False, "mensaje": "Este comando ya fue ejecutado."}
        try:
            self._saldo_antes = self._cuenta.saldo
            self._cuenta.depositar(self._monto, self._canal)
            self._ejecutado = True
            self._fecha     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Logger.get_instancia().log(
                f"[COMMAND] Depósito ejecutado — cuenta: {self._cuenta.numero} | "
                f"monto: ${self._monto:,.2f} | saldo: ${self._cuenta.saldo:,.2f}",
                nivel="SUCCESS"
            )
            return {
                "ok":      True,
                "mensaje": f"Depósito de ${self._monto:,.2f} ejecutado.",
                "datos":   {
                    "cuenta":      self._cuenta.numero,
                    "monto":       self._monto,
                    "canal":       self._canal,
                    "saldo_nuevo": self._cuenta.saldo,
                    "fecha":       self._fecha,
                }
            }
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}

    def deshacer(self) -> dict:
        if not self._ejecutado:
            return {"ok": False, "mensaje": "No hay depósito que deshacer."}
        try:
            saldo_antes_undo = self._cuenta.saldo
            self._cuenta.retirar(self._monto, self._canal)
            self._ejecutado = False
            Logger.get_instancia().log(
                f"[COMMAND] Depósito DESHECHO — cuenta: {self._cuenta.numero} | "
                f"monto revertido: ${self._monto:,.2f} | saldo: ${self._cuenta.saldo:,.2f}",
                nivel="INFO"
            )
            return {
                "ok":      True,
                "mensaje": f"Depósito de ${self._monto:,.2f} deshecho.",
                "datos":   {
                    "cuenta":      self._cuenta.numero,
                    "monto":       self._monto,
                    "saldo_nuevo": self._cuenta.saldo,
                }
            }
        except Exception as e:
            return {"ok": False, "mensaje": f"No se pudo deshacer: {e}"}

    def get_descripcion(self) -> str:
        estado = "ejecutado" if self._ejecutado else "deshecho"
        return f"DEPÓSITO ${self._monto:,.2f} → cuenta {self._cuenta.numero} [{estado}]"

    def get_tipo(self) -> str:
        return "deposito"

    def to_dict(self) -> dict:
        return {
            "tipo":        self.get_tipo(),
            "descripcion": self.get_descripcion(),
            "cuenta":      self._cuenta.numero,
            "monto":       self._monto,
            "canal":       self._canal,
            "ejecutado":   self._ejecutado,
            "fecha":       self._fecha,
        }


# =============================================================================
# CONCRETE COMMAND B — RETIRO
# =============================================================================

class ComandoRetiro(ComandoBancario):
    """
    ConcreteCommand B — Encapsula un retiro bancario.

    ejecutar(): retira el monto de la cuenta.
    deshacer(): deposita el mismo monto (operación inversa exacta).
    """

    def __init__(self, cuenta, monto: float, canal: str = "cajero"):
        self._cuenta        = cuenta
        self._monto         = monto
        self._canal         = canal
        self._saldo_antes   = None
        self._ejecutado     = False
        self._fecha         = None

    def ejecutar(self) -> dict:
        if self._ejecutado:
            return {"ok": False, "mensaje": "Este comando ya fue ejecutado."}
        try:
            self._saldo_antes = self._cuenta.saldo
            self._cuenta.retirar(self._monto, self._canal)
            self._ejecutado = True
            self._fecha     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Logger.get_instancia().log(
                f"[COMMAND] Retiro ejecutado — cuenta: {self._cuenta.numero} | "
                f"monto: ${self._monto:,.2f} | saldo: ${self._cuenta.saldo:,.2f}",
                nivel="SUCCESS"
            )
            return {
                "ok":      True,
                "mensaje": f"Retiro de ${self._monto:,.2f} ejecutado.",
                "datos":   {
                    "cuenta":      self._cuenta.numero,
                    "monto":       self._monto,
                    "canal":       self._canal,
                    "saldo_nuevo": self._cuenta.saldo,
                    "fecha":       self._fecha,
                }
            }
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}

    def deshacer(self) -> dict:
        if not self._ejecutado:
            return {"ok": False, "mensaje": "No hay retiro que deshacer."}
        try:
            self._cuenta.depositar(self._monto, self._canal)
            self._ejecutado = False
            Logger.get_instancia().log(
                f"[COMMAND] Retiro DESHECHO — cuenta: {self._cuenta.numero} | "
                f"monto revertido: ${self._monto:,.2f} | saldo: ${self._cuenta.saldo:,.2f}",
                nivel="INFO"
            )
            return {
                "ok":      True,
                "mensaje": f"Retiro de ${self._monto:,.2f} deshecho.",
                "datos":   {
                    "cuenta":      self._cuenta.numero,
                    "monto":       self._monto,
                    "saldo_nuevo": self._cuenta.saldo,
                }
            }
        except Exception as e:
            return {"ok": False, "mensaje": f"No se pudo deshacer: {e}"}

    def get_descripcion(self) -> str:
        estado = "ejecutado" if self._ejecutado else "deshecho"
        return f"RETIRO ${self._monto:,.2f} ← cuenta {self._cuenta.numero} [{estado}]"

    def get_tipo(self) -> str:
        return "retiro"

    def to_dict(self) -> dict:
        return {
            "tipo":        self.get_tipo(),
            "descripcion": self.get_descripcion(),
            "cuenta":      self._cuenta.numero,
            "monto":       self._monto,
            "canal":       self._canal,
            "ejecutado":   self._ejecutado,
            "fecha":       self._fecha,
        }


# =============================================================================
# CONCRETE COMMAND C — TRANSFERENCIA
# =============================================================================

class ComandoTransferencia(ComandoBancario):
    """
    ConcreteCommand C — Encapsula una transferencia entre dos cuentas.

    ejecutar(): transfiere el monto de origen a destino.
    deshacer(): transfiere el mismo monto de destino a origen.

    Es el command más valioso para demostrar el patrón: deshacer una
    transferencia requiere coordinar dos cuentas simultáneamente, lo cual
    sin Command requeriría lógica adicional dispersa en la API.
    Con Command, esa lógica vive aquí, encapsulada y reutilizable.
    """

    def __init__(self, cuenta_origen, cuenta_destino, monto: float, canal: str = "web"):
        self._origen        = cuenta_origen
        self._destino       = cuenta_destino
        self._monto         = monto
        self._canal         = canal
        self._saldo_origen_antes  = None
        self._saldo_destino_antes = None
        self._ejecutado     = False
        self._fecha         = None

    def ejecutar(self) -> dict:
        if self._ejecutado:
            return {"ok": False, "mensaje": "Este comando ya fue ejecutado."}
        try:
            self._saldo_origen_antes  = self._origen.saldo
            self._saldo_destino_antes = self._destino.saldo
            self._origen.transferir(self._destino, self._monto, self._canal)
            self._ejecutado = True
            self._fecha     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Logger.get_instancia().log(
                f"[COMMAND] Transferencia ejecutada — "
                f"{self._origen.numero} → {self._destino.numero} | "
                f"monto: ${self._monto:,.2f}",
                nivel="SUCCESS"
            )
            return {
                "ok":      True,
                "mensaje": f"Transferencia de ${self._monto:,.2f} ejecutada.",
                "datos":   {
                    "origen":          self._origen.numero,
                    "destino":         self._destino.numero,
                    "monto":           self._monto,
                    "canal":           self._canal,
                    "saldo_origen":    self._origen.saldo,
                    "saldo_destino":   self._destino.saldo,
                    "fecha":           self._fecha,
                }
            }
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}

    def deshacer(self) -> dict:
        if not self._ejecutado:
            return {"ok": False, "mensaje": "No hay transferencia que deshacer."}
        try:
            # Operación inversa: destino → origen
            self._destino.transferir(self._origen, self._monto, self._canal)
            self._ejecutado = False
            Logger.get_instancia().log(
                f"[COMMAND] Transferencia DESHECHA — "
                f"{self._destino.numero} → {self._origen.numero} | "
                f"monto revertido: ${self._monto:,.2f}",
                nivel="INFO"
            )
            return {
                "ok":      True,
                "mensaje": f"Transferencia de ${self._monto:,.2f} deshecha.",
                "datos":   {
                    "origen":        self._origen.numero,
                    "destino":       self._destino.numero,
                    "monto":         self._monto,
                    "saldo_origen":  self._origen.saldo,
                    "saldo_destino": self._destino.saldo,
                }
            }
        except Exception as e:
            return {"ok": False, "mensaje": f"No se pudo deshacer: {e}"}

    def get_descripcion(self) -> str:
        estado = "ejecutado" if self._ejecutado else "deshecho"
        return (f"TRANSFERENCIA ${self._monto:,.2f} "
                f"{self._origen.numero} → {self._destino.numero} [{estado}]")

    def get_tipo(self) -> str:
        return "transferencia"

    def to_dict(self) -> dict:
        return {
            "tipo":        self.get_tipo(),
            "descripcion": self.get_descripcion(),
            "origen":      self._origen.numero,
            "destino":     self._destino.numero,
            "monto":       self._monto,
            "canal":       self._canal,
            "ejecutado":   self._ejecutado,
            "fecha":       self._fecha,
        }


# =============================================================================
# INVOKER — HistorialComandos (Singleton)
#
# Mantiene dos pilas: _ejecutados (undo stack) y _revertidos (redo stack).
# El cliente nunca ejecuta commands directamente — siempre pasa por aquí.
# Eso garantiza que TODA operación queda registrada automáticamente.
# =============================================================================

class HistorialComandos:
    """
    Invoker del patrón Command.

    Responsabilidades:
      - ejecutar(command)  → llama a command.ejecutar() y lo push al stack undo
      - deshacer()         → pop del stack undo, llama deshacer(), push al redo
      - reejecutar()       → pop del stack redo, llama ejecutar(), push al undo
      - get_historial()    → retorna todos los commands con su estado actual

    Al ejecutar un nuevo command después de deshacer, se limpia el redo stack
    (comportamiento estándar undo/redo, igual que en cualquier editor de texto).
    """

    _instancia = None
    _lock      = threading.Lock()
    MAX_HISTORIAL = 50   # máximo de commands guardados

    def __init__(self):
        self._stack_undo: list = []   # commands ejecutados (deshacer desde aquí)
        self._stack_redo: list = []   # commands deshecho (reejecutar desde aquí)

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = HistorialComandos()
        return cls._instancia

    def ejecutar(self, command: ComandoBancario) -> dict:
        """Ejecuta el command y lo registra en el stack undo."""
        resultado = command.ejecutar()
        if resultado["ok"]:
            # Limpiar redo stack al ejecutar un nuevo command
            self._stack_redo.clear()
            self._stack_undo.append(command)
            # Limitar tamaño del historial
            if len(self._stack_undo) > self.MAX_HISTORIAL:
                self._stack_undo.pop(0)
            Logger.get_instancia().log(
                f"[INVOKER] Command registrado: {command.get_descripcion()} "
                f"| Stack undo: {len(self._stack_undo)} | Stack redo: 0",
                nivel="INFO"
            )
        return resultado

    def deshacer(self) -> dict:
        """Deshace el último command ejecutado."""
        if not self._stack_undo:
            return {"ok": False, "mensaje": "No hay operaciones para deshacer."}
        command = self._stack_undo.pop()
        resultado = command.deshacer()
        if resultado["ok"]:
            self._stack_redo.append(command)
            Logger.get_instancia().log(
                f"[INVOKER] UNDO: {command.get_descripcion()} "
                f"| Stack undo: {len(self._stack_undo)} "
                f"| Stack redo: {len(self._stack_redo)}",
                nivel="INFO"
            )
        else:
            # Si falló el undo, devolver al stack
            self._stack_undo.append(command)
        return resultado

    def reejecutar(self) -> dict:
        """Reedita el último command deshecho (redo)."""
        if not self._stack_redo:
            return {"ok": False, "mensaje": "No hay operaciones para reejecutar."}
        command = self._stack_redo.pop()
        resultado = command.ejecutar()
        if resultado["ok"]:
            self._stack_undo.append(command)
            Logger.get_instancia().log(
                f"[INVOKER] REDO: {command.get_descripcion()} "
                f"| Stack undo: {len(self._stack_undo)} "
                f"| Stack redo: {len(self._stack_redo)}",
                nivel="INFO"
            )
        else:
            self._stack_redo.append(command)
        return resultado

    def get_historial(self) -> list:
        """
        Retorna todos los commands con su posición y estado actual.
        Los del stack undo están 'ejecutados'; los del redo están 'deshecho'.
        """
        historial = []
        seq = 1
        for cmd in self._stack_undo:
            d = cmd.to_dict()
            d["secuencia"] = seq
            d["en_stack"]  = "undo"
            historial.append(d)
            seq += 1
        for cmd in reversed(self._stack_redo):
            d = cmd.to_dict()
            d["secuencia"] = seq
            d["en_stack"]  = "redo"
            historial.append(d)
            seq += 1
        return historial

    def puede_deshacer(self) -> bool:
        return len(self._stack_undo) > 0

    def puede_reejecutar(self) -> bool:
        return len(self._stack_redo) > 0

    def limpiar(self):
        """Vacía ambos stacks."""
        self._stack_undo.clear()
        self._stack_redo.clear()
        Logger.get_instancia().log(
            "[INVOKER] Historial de commands limpiado.",
            nivel="INFO"
        )

    def get_estado(self) -> dict:
        return {
            "puede_deshacer":   self.puede_deshacer(),
            "puede_reejecutar": self.puede_reejecutar(),
            "total_undo":       len(self._stack_undo),
            "total_redo":       len(self._stack_redo),
            "ultimo_undo": self._stack_undo[-1].get_descripcion() if self._stack_undo else None,
            "ultimo_redo": self._stack_redo[-1].get_descripcion() if self._stack_redo else None,
        }
