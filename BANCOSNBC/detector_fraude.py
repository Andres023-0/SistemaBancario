import threading
from datetime import datetime
from decimal import Decimal
from config_banco import ConfigBanco

class DetectorFraude:
    """
    Singleton para detección de fraude en tiempo real.
    Garantiza una única instancia en toda la aplicación.
    """
    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        config = ConfigBanco.get_instancia()
        self._limite_aml = config.get_limite_aml()
        self._limite_aml_mensual = config.get_limite_aml_multiples_mes()
        self._max_transacciones = config.get_max_transacciones_ventana()
        self._ventana_minutos = config.get_ventana_tiempo_minutos()
        self._saldo_critico = config.get_saldo_critico()

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = DetectorFraude()
        return cls._instancia

    def evaluar(self, cuenta, monto, canal, tipo_operacion="deposito", cuenta_destino=None):
        alertas = []

        # Regla 1: Monto alto (AML) — transacción individual
        if monto > self._limite_aml:
            alertas.append(f"Monto excede límite AML (${self._limite_aml:,.0f})")

        # Regla 1.5: Monto alto (AML) — acumulado del cliente en el mes calendario actual
        # (normativa UIAF: transacciones múltiples del mismo cliente en un mes)
        ahora = datetime.now()
        mes_actual = ahora.strftime("%Y-%m")
        acumulado_mes = sum(
            Decimal(str(t["monto"]))
            for t in cuenta.transacciones
            if t["fecha"].startswith(mes_actual)
        ) + Decimal(str(monto))
        if acumulado_mes > self._limite_aml_mensual:
            alertas.append(
                f"Acumulado mensual del cliente excede límite AML "
                f"(${self._limite_aml_mensual:,.0f}) — total del mes: ${acumulado_mes:,.0f}"
            )

        # Regla 2: Alta frecuencia
        trans_recientes = [
            t for t in cuenta.transacciones
            if (ahora - datetime.strptime(t['fecha'], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60 <= self._ventana_minutos
        ]
        if len(trans_recientes) >= self._max_transacciones:
            alertas.append(
                f"Más de {self._max_transacciones} transacciones en {self._ventana_minutos} minutos"
            )

        # Regla 3: Saldo crítico — solo bloquea si el saldo resultante es negativo
        # (saldo insuficiente real). Quedar con saldo bajo es válido.
        if tipo_operacion in ["retiro", "transferencia"]:
            saldo_proyectado = Decimal(str(cuenta.saldo)) - Decimal(str(monto))
            if saldo_proyectado < Decimal("0"):
                alertas.append(f"{tipo_operacion.capitalize()} genera saldo negativo — operación no permitida")

        # Regla 4: Canal inusual
        if len(cuenta.transacciones) >= 5:
            canales_recientes = [t['canal'] for t in cuenta.transacciones[-5:]]
            if canal not in set(canales_recientes):
                alertas.append(f"Canal inusual para esta cuenta: {canal}")

        # Regla 5: Transferencia a cuenta nueva
        # Solo se registra en log informativo; no bloquea la operación.
        # Es normal que cuentas nuevas reciban su primera transferencia.
        if tipo_operacion == "transferencia" and cuenta_destino:
            if not cuenta_destino.transacciones:
                from logger import Logger
                Logger.get_instancia().log(
                    "[FRAUDE] Info: cuenta destino sin historial previo (operación permitida)",
                    nivel="INFO"
                )

        return len(alertas) == 0, alertas