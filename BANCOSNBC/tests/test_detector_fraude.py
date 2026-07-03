"""
Tests unitarios — DetectorFraude (detector_fraude.py)
Cubre: regla AML (post Fase 2.5 — límite real UIAF $10.000.000),
frecuencia y saldo negativo.
Ejecutar: pytest tests/test_detector_fraude.py -v

IMPORTANTE: DetectorFraude y ConfigBanco son Singleton — leen la config
UNA sola vez en todo el proceso de tests. Por eso estos tests asumen los
valores vigentes definidos en config_banco.py (Fase 2.5).
"""
import sys
import os
from datetime import datetime, timedelta
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cuenta import Cuenta
from detector_fraude import DetectorFraude
from config_banco import ConfigBanco


@pytest.fixture
def cuenta():
    return Cuenta(numero="7001", tipo="ahorros", saldo_inicial=50_000_000)


@pytest.fixture
def detector():
    return DetectorFraude.get_instancia()


# ── Regla AML ─────────────────────────────────────────────────────────────

def test_monto_bajo_limite_aml_no_genera_alerta(cuenta, detector):
    limite = ConfigBanco.get_instancia().get_limite_aml()
    ok, alertas = detector.evaluar(cuenta, monto=limite - 1, canal="web", tipo_operacion="deposito")
    assert not any("AML" in a for a in alertas)


def test_monto_sobre_limite_aml_genera_alerta(cuenta, detector):
    limite = ConfigBanco.get_instancia().get_limite_aml()
    ok, alertas = detector.evaluar(cuenta, monto=limite + 1, canal="web", tipo_operacion="deposito")
    assert any("AML" in a for a in alertas)


def test_limite_aml_es_el_umbral_oficial_uiaf():
    """Regression: bug histórico tenía $10.000 (3 ceros de menos)."""
    assert ConfigBanco.get_instancia().get_limite_aml() == 10_000_000


# ── Regla saldo negativo ─────────────────────────────────────────────────

def test_retiro_que_deja_saldo_negativo_genera_alerta(detector):
    cuenta_pequena = Cuenta(numero="7002", tipo="ahorros", saldo_inicial=1_000)
    ok, alertas = detector.evaluar(
        cuenta_pequena, monto=2_000, canal="web", tipo_operacion="retiro"
    )
    assert any("saldo negativo" in a.lower() for a in alertas)


def test_retiro_normal_no_genera_alerta_de_saldo(cuenta, detector):
    ok, alertas = detector.evaluar(cuenta, monto=100_000, canal="web", tipo_operacion="retiro")
    assert not any("saldo negativo" in a.lower() for a in alertas)


# ── Regla frecuencia ──────────────────────────────────────────────────────

def test_alta_frecuencia_genera_alerta(cuenta, detector):
    config = ConfigBanco.get_instancia()
    max_trans = config.get_max_transacciones_ventana()

    # Simula N transacciones recientes (dentro de la ventana de tiempo)
    ahora = datetime.now()
    for _ in range(max_trans):
        cuenta.transacciones.append({
            "fecha": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": "deposito",
            "monto": 10_000,
            "canal": "web",
            "saldo_final": float(cuenta.saldo),
        })

    ok, alertas = detector.evaluar(cuenta, monto=10_000, canal="web", tipo_operacion="deposito")
    assert any("transacciones en" in a for a in alertas)


def test_transacciones_antiguas_no_cuentan_para_frecuencia(cuenta, detector):
    config = ConfigBanco.get_instancia()
    max_trans = config.get_max_transacciones_ventana()
    ventana = config.get_ventana_tiempo_minutos()

    fecha_vieja = datetime.now() - timedelta(minutes=ventana + 10)
    for _ in range(max_trans):
        cuenta.transacciones.append({
            "fecha": fecha_vieja.strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": "deposito",
            "monto": 10_000,
            "canal": "web",
            "saldo_final": float(cuenta.saldo),
        })

    ok, alertas = detector.evaluar(cuenta, monto=10_000, canal="web", tipo_operacion="deposito")
    assert not any("transacciones en" in a for a in alertas)
