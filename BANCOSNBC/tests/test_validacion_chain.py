"""
Tests unitarios — Chain of Responsibility (validacion_chain.py)
Cubre: cada eslabón por separado y la cadena completa integrada.
Ejecutar: pytest tests/test_validacion_chain.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cuenta import Cuenta
from validacion_chain import CadenaValidacionFactory


@pytest.fixture
def cuenta_origen():
    return Cuenta(numero="8001", tipo="ahorros", saldo_inicial=1_000_000)


@pytest.fixture
def cuenta_destino():
    return Cuenta(numero="8002", tipo="ahorros", saldo_inicial=0)


# ── Cadena completa — casos felices ──────────────────────────────────────

def test_deposito_valido_es_aprobado(cuenta_origen):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=100_000, tipo="deposito", canal="web"
    )
    assert resultado.aprobado is True
    assert resultado.rechazado_por is None


def test_retiro_valido_es_aprobado(cuenta_origen):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=100_000, tipo="retiro", canal="cajero"
    )
    assert resultado.aprobado is True


def test_transferencia_valida_es_aprobada(cuenta_origen, cuenta_destino):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=100_000, tipo="transferencia",
        canal="web", cuenta_destino=cuenta_destino
    )
    assert resultado.aprobado is True


# ── ValidadorEstadoCuenta ────────────────────────────────────────────────

def test_cuenta_bloqueada_es_rechazada_por_estado(cuenta_origen):
    cuenta_origen.bloquear()
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=50_000, tipo="deposito", canal="web"
    )
    assert resultado.aprobado is False
    assert resultado.rechazado_por == "ValidadorEstadoCuenta"


# ── ValidadorSaldo ───────────────────────────────────────────────────────

def test_saldo_insuficiente_es_rechazado(cuenta_origen):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=999_999_999, tipo="retiro", canal="web"
    )
    assert resultado.aprobado is False
    assert resultado.rechazado_por == "ValidadorSaldo"


# ── ValidadorLimiteCanal ─────────────────────────────────────────────────

def test_monto_bajo_minimo_de_canal_es_rechazado(cuenta_origen):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=100, tipo="deposito", canal="web"
    )
    assert resultado.aprobado is False
    assert resultado.rechazado_por == "ValidadorLimiteCanal"


def test_monto_sobre_maximo_de_canal_es_rechazado(cuenta_origen):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=3_000_000, tipo="deposito", canal="cajero"
    )
    assert resultado.aprobado is False
    assert resultado.rechazado_por == "ValidadorLimiteCanal"


def test_transferencia_por_cajero_es_rechazada(cuenta_origen, cuenta_destino):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=100_000, tipo="transferencia",
        canal="cajero", cuenta_destino=cuenta_destino
    )
    assert resultado.aprobado is False
    assert resultado.rechazado_por == "ValidadorLimiteCanal"


# ── ValidadorCuentaDestino ───────────────────────────────────────────────

def test_transferencia_sin_cuenta_destino_es_rechazada(cuenta_origen):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=100_000, tipo="transferencia", canal="web"
    )
    assert resultado.aprobado is False
    assert resultado.rechazado_por == "ValidadorCuentaDestino"


# ── Orden de la cadena / trazabilidad ────────────────────────────────────

def test_resultado_incluye_todos_los_pasos_ejecutados(cuenta_origen):
    resultado = CadenaValidacionFactory.validar(
        cuenta_origen=cuenta_origen, monto=100_000, tipo="deposito", canal="web"
    )
    nombres_pasos = [p["handler"] for p in resultado.pasos]
    assert "ValidadorEstadoCuenta" in nombres_pasos
    assert "ValidadorSaldo" in nombres_pasos
    assert "ValidadorLimiteCanal" in nombres_pasos
