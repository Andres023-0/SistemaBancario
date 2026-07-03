import threading

class ConfigBanco:
    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        # ── AML — Umbrales oficiales UIAF Colombia (Guía de Normatividad UIAF) ──
        # Transacción individual en efectivo reportable: $10.000.000 COP
        # (antes: 10000 → error de 3 ceros, disparaba alerta en el 100% de operaciones)
        self._limite_aml_por_transaccion = 10_000_000

        # Transacciones múltiples del mismo cliente en un mes: $50.000.000 COP
        self._limite_aml_transacciones_multiples_mes = 50_000_000

        self._max_transacciones_por_ventana = 5
        self._ventana_tiempo_minutos = 5

        # ── Saldo crítico — regla de negocio propia (no normativa UIAF) ─────────
        # Ajustado a una magnitud coherente con saldos reales del banco (antes: 1000)
        self._saldo_critico_minimo = 100_000

        self._sucursales_predeterminadas = [
            "Bucaramanga Centro",
            "Bucaramanga Norte",
            "Floridablanca"
        ]

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = ConfigBanco()
        return cls._instancia

    def get_limite_aml(self):
        return self._limite_aml_por_transaccion

    def get_limite_aml_multiples_mes(self):
        return self._limite_aml_transacciones_multiples_mes

    def get_max_transacciones_ventana(self):
        return self._max_transacciones_por_ventana

    def get_ventana_tiempo_minutos(self):
        return self._ventana_tiempo_minutos

    def get_saldo_critico(self):
        return self._saldo_critico_minimo

    def get_sucursales(self):
        return self._sucursales_predeterminadas.copy()  # copia para seguridad