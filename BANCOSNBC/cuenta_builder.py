from cuenta import Cuenta
from logger import Logger


class CuentaBuilder:
    """
    Patrón Builder — variante Fluent Builder.
    Permite construir una Cuenta paso a paso, asociarla a un usuario
    y a una sucursal, todo en un proceso legible y encadenado.

    CAMBIO Semana 14 (Observer):
        build() y clone_desde() ahora suscriben automáticamente los
        observadores predeterminados del sistema (ObservadorFraude,
        ObservadorSaldoCritico, ObservadorLogMovimiento) a cada cuenta
        construida o clonada.
        El cliente no necesita conocer ObservadorProducer — el Builder
        se encarga de esa inicialización de forma transparente.

    Uso normal (Builder):
        cuenta = (CuentaBuilder()
            .numero("3001")
            .tipo("ahorros")
            .saldo_inicial(500_000)
            .asociar_usuario(usuario)
            .asociar_sucursal(sucursal)
            .build())

    Uso por clonación (Prototype + Builder):
        cuenta = (CuentaBuilder()
            .numero("3002")
            .asociar_usuario(usuario)
            .asociar_sucursal(sucursal)
            .clone_desde(cuenta_prototipo))
    """

    def __init__(self):
        self._numero        = None
        self._tipo          = "corriente"   # valor por defecto
        self._saldo_inicial = 0.0           # valor por defecto
        self._usuario       = None
        self._sucursal      = None

    # ── Pasos de construcción (cada uno retorna self para encadenar) ──────────

    def numero(self, numero: str):
        self._numero = numero
        return self

    def tipo(self, tipo: str):
        self._tipo = tipo
        return self

    def saldo_inicial(self, monto: float):
        self._saldo_inicial = monto
        return self

    def asociar_usuario(self, usuario):
        self._usuario = usuario
        return self

    def asociar_sucursal(self, sucursal):
        self._sucursal = sucursal
        return self

    # ── build(): valida, construye, asocia y suscribe observadores ────────────

    def build(self) -> Cuenta:
        logger = Logger.get_instancia()

        # Validaciones antes de construir
        if not self._numero:
            raise ValueError("El número de cuenta es obligatorio")
        if not self._usuario:
            raise ValueError("Debe asociar un usuario antes de construir la cuenta")
        if not self._sucursal:
            raise ValueError("Debe asociar una sucursal antes de construir la cuenta")
        if not self._usuario.verificado_kyc:
            raise ValueError("El usuario debe tener KYC verificado")

        # Construir el producto
        cuenta = Cuenta(self._numero, self._tipo, self._saldo_inicial)

        # Guarda referencia al usuario dentro de la cuenta
        cuenta._usuario_ref = self._usuario

        # Asociar al usuario y a la sucursal
        self._usuario.agregar_cuenta(cuenta)
        self._sucursal.agregar_cuenta(cuenta)

        # ── OBSERVER: suscribir observadores predeterminados ──────────────────
        # ObservadorProducer.get_observadores_default() retorna las tres
        # instancias: ObservadorFraude, ObservadorSaldoCritico, ObservadorLogMovimiento.
        # La cuenta queda lista para notificar desde el primer movimiento.
        from observer_cuenta import ObservadorProducer
        for observador in ObservadorProducer.get_observadores_default():
            cuenta.suscribir(observador)
        # ─────────────────────────────────────────────────────────────────────

        logger.log(
            f"[BUILDER] Cuenta {self._numero} ({self._tipo}) construida — "
            f"Usuario: {self._usuario.nombre} | "
            f"Sucursal: {self._sucursal.nombre} | "
            f"Saldo inicial: ${self._saldo_inicial:,.2f}",
            nivel="SUCCESS"
        )

        return cuenta

    # ── clone_desde(): construye por clonación y suscribe observadores ────────

    def clone_desde(self, cuenta_origen: Cuenta) -> Cuenta:
        """
        Patrón Prototype integrado al Builder.
        En lugar de construir la cuenta desde cero, clona una existente
        y solo ajusta número, usuario y sucursal.

        CAMBIO Semana 14 (Observer):
            El clon nace sin observadores (Cuenta.clone() limpia la lista).
            Este método suscribe los observadores default al clon igual que
            build() lo hace para las cuentas nuevas. De este modo, el clon
            queda completamente operativo como Sujeto Observer desde el
            momento en que se entrega al cliente.

        Requiere haber llamado antes: .numero(), .asociar_usuario(),
        .asociar_sucursal()
        No requiere: .tipo() ni .saldo_inicial() — vienen del prototipo.
        """
        logger = Logger.get_instancia()

        # Mismas validaciones de integridad que build()
        if not self._numero:
            raise ValueError("El número de cuenta es obligatorio para el clon")
        if not self._usuario:
            raise ValueError("Debe asociar un usuario antes de clonar la cuenta")
        if not self._sucursal:
            raise ValueError("Debe asociar una sucursal antes de clonar la cuenta")
        if not self._usuario.verificado_kyc:
            raise ValueError("El usuario debe tener KYC verificado")

        # Delega la copia al método clone() de Cuenta (Prototype)
        cuenta_clonada = cuenta_origen.clone(self._numero)

        # Actualiza la referencia de usuario al nuevo dueño
        cuenta_clonada._usuario_ref = self._usuario

        # Asociar al nuevo usuario y sucursal
        self._usuario.agregar_cuenta(cuenta_clonada)
        self._sucursal.agregar_cuenta(cuenta_clonada)

        # ── OBSERVER: suscribir observadores al clon ──────────────────────────
        # El clon nace con _observadores = [] (ver Cuenta.clone()).
        # Se suscriben los mismos observadores default que en build().
        from observer_cuenta import ObservadorProducer
        for observador in ObservadorProducer.get_observadores_default():
            cuenta_clonada.suscribir(observador)
        # ─────────────────────────────────────────────────────────────────────

        logger.log(
            f"[BUILDER+PROTOTYPE] Cuenta {self._numero} ({cuenta_clonada.tipo}) "
            f"clonada desde {cuenta_origen.numero} — "
            f"Usuario: {self._usuario.nombre} | "
            f"Sucursal: {self._sucursal.nombre} | "
            f"Saldo heredado: ${cuenta_clonada.saldo:,.2f}",
            nivel="SUCCESS"
        )

        return cuenta_clonada