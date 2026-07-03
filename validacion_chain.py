from abc import ABC, abstractmethod
from logger import Logger
from config_banco import ConfigBanco


# =============================================================================
# PATRÓN CHAIN OF RESPONSIBILITY — Validación de transacciones
#
# Encadena manejadores de validación de forma que cada uno decide si
# aprueba, rechaza o pasa la solicitud al siguiente eslabón.
#
# Participantes:
#   - ValidadorHandler         → Handler abstracto (interfaz de la cadena)
#   - ValidadorSaldo           → ConcreteHandler A
#   - ValidadorLimiteCanal     → ConcreteHandler B
#   - ValidadorEstadoCuenta    → ConcreteHandler C
#   - ValidadorFrecuencia      → ConcreteHandler D
#   - CadenaValidacionFactory  → construye la cadena completa
#
# Qué resuelve vs la solución sin Chain:
#   SIN CHAIN: las validaciones están dispersas en detector_fraude.py,
#              canal_bridge.py y transaccion.py. Es difícil saber cuál
#              validación rechazó una operación y en qué orden se aplican.
#   CON CHAIN: cada validación es un objeto independiente con su
#              responsabilidad única. La cadena es configurable, extensible
#              y retorna exactamente cuál eslabón rechazó y por qué.
#              Perfecto para mostrar en el frontend paso a paso.
#
# Coexistencia con Bridge y Decorator:
#   Chain valida ANTES de que Bridge procese la operación.
#   Transaccion.procesar() puede invocar la cadena primero y solo si
#   todos los eslabones aprueban, delegar al Bridge.
# =============================================================================


# =============================================================================
# RESULTADO DE VALIDACIÓN — estructura de datos del resultado
# =============================================================================

class ResultadoValidacion:
    """
    Encapsula el resultado de pasar por la cadena completa.
    Permite al frontend mostrar qué eslabón aprobó/rechazó y por qué.
    """

    def __init__(self):
        self.aprobado    = True
        self.pasos       = []   # lista de dict con cada eslabón ejecutado
        self.rechazado_por = None   # nombre del handler que rechazó

    def agregar_paso(self, handler_nombre: str, aprobado: bool, mensaje: str):
        self.pasos.append({
            "handler":  handler_nombre,
            "aprobado": aprobado,
            "mensaje":  mensaje,
        })
        if not aprobado:
            self.aprobado      = False
            self.rechazado_por = handler_nombre

    def to_dict(self) -> dict:
        return {
            "aprobado":      self.aprobado,
            "rechazado_por": self.rechazado_por,
            "pasos":         self.pasos,
            "total_pasos":   len(self.pasos),
        }


# =============================================================================
# HANDLER ABSTRACTO
# =============================================================================

class ValidadorHandler(ABC):
    """
    Handler abstracto del patrón Chain of Responsibility.

    Cada manejador concreto implementa _validar() con su lógica propia.
    El método manejar() orquesta: valida, registra el paso y pasa al siguiente.

    El cliente construye la cadena llamando set_siguiente() y luego
    llama manejar() sobre el primer eslabón — el encadenamiento es automático.
    """

    def __init__(self):
        self._siguiente: ValidadorHandler | None = None

    def set_siguiente(self, handler: "ValidadorHandler") -> "ValidadorHandler":
        """
        Encadena el siguiente handler y lo retorna para poder encadenar
        de forma fluida: A.set_siguiente(B).set_siguiente(C)
        """
        self._siguiente = handler
        return handler

    def manejar(self, solicitud: dict, resultado: ResultadoValidacion) -> ResultadoValidacion:
        """
        Template method del handler:
        1. Ejecuta la validación propia (_validar)
        2. Registra el paso en resultado
        3. Si aprobó Y hay siguiente → pasa la solicitud
        4. Si rechazó → detiene la cadena
        """
        aprobado, mensaje = self._validar(solicitud)

        resultado.agregar_paso(
            handler_nombre = self.get_nombre(),
            aprobado       = aprobado,
            mensaje        = mensaje,
        )

        Logger.get_instancia().log(
            f"[CHAIN] {self.get_nombre()}: {'✅' if aprobado else '❌'} {mensaje}",
            nivel="INFO" if aprobado else "WARNING"
        )

        if aprobado and self._siguiente:
            return self._siguiente.manejar(solicitud, resultado)

        return resultado

    @abstractmethod
    def _validar(self, solicitud: dict) -> tuple[bool, str]:
        """
        Lógica de validación propia del handler.
        Recibe la solicitud completa y retorna (aprobado: bool, mensaje: str).

        Solicitud esperada:
            {
                "cuenta_origen":  Cuenta,
                "monto":          float,
                "tipo":           str,   — deposito / retiro / transferencia
                "canal":          str,   — web / movil / cajero
                "cuenta_destino": Cuenta | None,
            }
        """
        pass

    @abstractmethod
    def get_nombre(self) -> str:
        """Nombre identificador del handler para logs y frontend."""
        pass


# =============================================================================
# CONCRETE HANDLERS
# =============================================================================

class ValidadorEstadoCuenta(ValidadorHandler):
    """
    ConcreteHandler A — Verifica que la cuenta esté en estado operativo.
    Es el primer eslabón: si la cuenta está cerrada o bloqueada,
    no tiene sentido seguir validando nada más.
    """

    def get_nombre(self) -> str:
        return "ValidadorEstadoCuenta"

    def _validar(self, solicitud: dict) -> tuple[bool, str]:
        cuenta = solicitud["cuenta_origen"]
        tipo   = solicitud["tipo"]
        estado = cuenta.get_estado()

        if tipo == "deposito":
            permitido, msg = estado.puede_depositar()
        elif tipo == "retiro":
            permitido, msg = estado.puede_retirar()
        else:
            permitido, msg = estado.puede_transferir()

        if not permitido:
            return False, f"Estado de cuenta no permite la operación: {msg}"

        return True, f"Estado '{estado.get_nombre()}' permite {tipo}"


class ValidadorSaldo(ValidadorHandler):
    """
    ConcreteHandler B — Verifica que haya saldo suficiente.
    Solo aplica a retiros y transferencias.
    """

    def get_nombre(self) -> str:
        return "ValidadorSaldo"

    def _validar(self, solicitud: dict) -> tuple[bool, str]:
        tipo   = solicitud["tipo"]
        cuenta = solicitud["cuenta_origen"]
        monto  = solicitud["monto"]

        if tipo == "deposito":
            return True, "Depósito no requiere validación de saldo"

        if cuenta.saldo < monto:
            return (
                False,
                f"Saldo insuficiente: disponible ${cuenta.saldo:,.2f} | "
                f"requerido ${monto:,.2f}"
            )

        return True, f"Saldo suficiente: ${cuenta.saldo:,.2f} disponible"


class ValidadorLimiteCanal(ValidadorHandler):
    """
    ConcreteHandler C — Verifica que el monto esté dentro de los
    límites del canal (web, movil, cajero).
    Usa la misma lógica de CanalBancarioProducer del Bridge.
    """

    _LIMITES = {
        "web":    {"min": 1_000,  "max": 50_000_000},
        "movil":  {"min": 1_000,  "max": 5_000_000},
        "cajero": {"min": 10_000, "max": 2_000_000},
    }

    def get_nombre(self) -> str:
        return "ValidadorLimiteCanal"

    def _validar(self, solicitud: dict) -> tuple[bool, str]:
        canal  = solicitud["canal"].lower()
        monto  = solicitud["monto"]
        tipo   = solicitud["tipo"]

        limites = self._LIMITES.get(canal)
        if limites is None:
            return False, f"Canal no reconocido: '{canal}'"

        if tipo == "transferencia" and canal == "cajero":
            return False, "El cajero físico no permite transferencias"

        if monto < limites["min"]:
            return (
                False,
                f"Monto ${monto:,.2f} por debajo del mínimo del canal "
                f"{canal.upper()} (${limites['min']:,.0f})"
            )

        if monto > limites["max"]:
            return (
                False,
                f"Monto ${monto:,.2f} supera el límite del canal "
                f"{canal.upper()} (${limites['max']:,.0f})"
            )

        return (
            True,
            f"Monto ${monto:,.2f} dentro de límites del canal "
            f"{canal.upper()} [${limites['min']:,.0f} – ${limites['max']:,.0f}]"
        )


class ValidadorFrecuencia(ValidadorHandler):
    """
    ConcreteHandler D — Verifica que la cuenta no haya superado el
    número máximo de transacciones en la ventana de tiempo configurada.
    Usa ConfigBanco para obtener los umbrales (igual que DetectorFraude).
    """

    def get_nombre(self) -> str:
        return "ValidadorFrecuencia"

    def _validar(self, solicitud: dict) -> tuple[bool, str]:
        from datetime import datetime

        cuenta          = solicitud["cuenta_origen"]
        config          = ConfigBanco.get_instancia()
        max_trans       = config.get_max_transacciones_ventana()
        ventana_minutos = config.get_ventana_tiempo_minutos()

        ahora = datetime.now()
        recientes = [
            t for t in cuenta.transacciones
            if (ahora - datetime.strptime(t["fecha"], "%Y-%m-%d %H:%M:%S")
                ).total_seconds() / 60 <= ventana_minutos
        ]

        if len(recientes) >= max_trans:
            return (
                False,
                f"Límite de frecuencia alcanzado: {len(recientes)} transacciones "
                f"en los últimos {ventana_minutos} min (máx: {max_trans})"
            )

        return (
            True,
            f"Frecuencia normal: {len(recientes)}/{max_trans} transacciones "
            f"en ventana de {ventana_minutos} min"
        )


class ValidadorCuentaDestino(ValidadorHandler):
    """
    ConcreteHandler E — Verifica que la cuenta destino exista y esté
    activa para recibir transferencias.
    Solo aplica a transferencias; el resto pasan automáticamente.
    """

    def get_nombre(self) -> str:
        return "ValidadorCuentaDestino"

    def _validar(self, solicitud: dict) -> tuple[bool, str]:
        tipo    = solicitud["tipo"]
        destino = solicitud.get("cuenta_destino")

        if tipo != "transferencia":
            return True, "No aplica para esta operación"

        if destino is None:
            return False, "Se requiere cuenta destino para transferencia"

        estado_destino = destino.get_estado()
        permitido, msg = estado_destino.puede_depositar()
        if not permitido:
            return (
                False,
                f"Cuenta destino {destino.numero} no puede recibir fondos: {msg}"
            )

        return True, f"Cuenta destino {destino.numero} disponible para recibir"


# =============================================================================
# FACTORY DE LA CADENA — punto de entrada único
# =============================================================================

class CadenaValidacionFactory:
    """
    Construye y retorna la cadena de validación completa lista para usar.

    El orden de la cadena es:
      ValidadorEstadoCuenta → ValidadorSaldo → ValidadorLimiteCanal
      → ValidadorFrecuencia → ValidadorCuentaDestino

    El cliente (api.py, transaccion.py) nunca instancia los handlers:
        resultado = CadenaValidacionFactory.validar(solicitud)
        if not resultado.aprobado:
            return err(resultado.rechazado_por)
    """

    @staticmethod
    def construir() -> ValidadorHandler:
        """Construye y retorna el primer eslabón de la cadena."""
        primero    = ValidadorEstadoCuenta()
        segundo    = ValidadorSaldo()
        tercero    = ValidadorLimiteCanal()
        cuarto     = ValidadorFrecuencia()
        quinto     = ValidadorCuentaDestino()

        primero.set_siguiente(segundo)\
               .set_siguiente(tercero)\
               .set_siguiente(cuarto)\
               .set_siguiente(quinto)

        return primero

    @staticmethod
    def validar(
        cuenta_origen,
        monto: float,
        tipo: str,
        canal: str,
        cuenta_destino=None
    ) -> ResultadoValidacion:
        """
        Punto de entrada único: construye la cadena y la ejecuta.

        Retorna un ResultadoValidacion con todos los pasos ejecutados,
        el resultado global y el handler que rechazó (si aplica).
        """
        solicitud = {
            "cuenta_origen":  cuenta_origen,
            "monto":          monto,
            "tipo":           tipo,
            "canal":          canal,
            "cuenta_destino": cuenta_destino,
        }

        Logger.get_instancia().log(
            f"[CHAIN] Iniciando cadena de validación — "
            f"tipo: {tipo} | canal: {canal} | monto: ${monto:,.2f} | "
            f"cuenta: {cuenta_origen.numero}",
            nivel="INFO"
        )

        cadena    = CadenaValidacionFactory.construir()
        resultado = cadena.manejar(solicitud, ResultadoValidacion())

        Logger.get_instancia().log(
            f"[CHAIN] Cadena finalizada — "
            f"{'✅ APROBADA' if resultado.aprobado else f'❌ RECHAZADA por {resultado.rechazado_por}'} "
            f"| Pasos ejecutados: {len(resultado.pasos)}",
            nivel="SUCCESS" if resultado.aprobado else "WARNING"
        )

        return resultado
