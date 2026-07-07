"""
Tests unitarios — Command (command_transaccion.py)
Cubre: ComandoDeposito, ComandoRetiro, ComandoTransferencia, HistorialComandos (undo/redo).
Ejecutar: pytest tests/test_command_transaccion.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cuenta import Cuenta
from command_transaccion import (
    ComandoDeposito,
    ComandoRetiro,
    ComandoTransferencia,
    HistorialComandos,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def cuenta():
    return Cuenta(numero="7001", tipo="ahorros", saldo_inicial=1_000_000)


@pytest.fixture
def cuenta_destino():
    return Cuenta(numero="7002", tipo="corriente", saldo_inicial=500_000)


@pytest.fixture
def historial():
    """Invoker limpio para cada test (evita fugas de estado entre tests,
    ya que HistorialComandos es Singleton)."""
    h = HistorialComandos.get_instancia()
    h.limpiar()
    return h


# ── ComandoDeposito ───────────────────────────────────────────────────────

def test_deposito_ejecutar_incrementa_saldo(cuenta):
    cmd = ComandoDeposito(cuenta, 200_000)
    resultado = cmd.ejecutar()
    assert resultado["ok"] is True
    assert cuenta.saldo == 1_200_000


def test_deposito_deshacer_revierte_saldo_exacto(cuenta):
    saldo_original = cuenta.saldo
    cmd = ComandoDeposito(cuenta, 200_000)
    cmd.ejecutar()
    resultado = cmd.deshacer()
    assert resultado["ok"] is True
    assert cuenta.saldo == saldo_original


def test_deposito_no_se_puede_ejecutar_dos_veces(cuenta):
    cmd = ComandoDeposito(cuenta, 100_000)
    cmd.ejecutar()
    resultado = cmd.ejecutar()
    assert resultado["ok"] is False


def test_deposito_no_se_puede_deshacer_sin_ejecutar(cuenta):
    cmd = ComandoDeposito(cuenta, 100_000)
    resultado = cmd.deshacer()
    assert resultado["ok"] is False


# ── ComandoRetiro ─────────────────────────────────────────────────────────

def test_retiro_ejecutar_disminuye_saldo(cuenta):
    cmd = ComandoRetiro(cuenta, 300_000)
    resultado = cmd.ejecutar()
    assert resultado["ok"] is True
    assert cuenta.saldo == 700_000


def test_retiro_deshacer_revierte_saldo_exacto(cuenta):
    saldo_original = cuenta.saldo
    cmd = ComandoRetiro(cuenta, 300_000)
    cmd.ejecutar()
    resultado = cmd.deshacer()
    assert resultado["ok"] is True
    assert cuenta.saldo == saldo_original


# ── ComandoTransferencia ──────────────────────────────────────────────────

def test_transferencia_ejecutar_mueve_dinero(cuenta, cuenta_destino):
    cmd = ComandoTransferencia(cuenta, cuenta_destino, 150_000)
    resultado = cmd.ejecutar()
    assert resultado["ok"] is True
    assert cuenta.saldo == 850_000
    assert cuenta_destino.saldo == 650_000


def test_transferencia_deshacer_revierte_ambas_cuentas(cuenta, cuenta_destino):
    saldo_origen_original = cuenta.saldo
    saldo_destino_original = cuenta_destino.saldo
    cmd = ComandoTransferencia(cuenta, cuenta_destino, 150_000)
    cmd.ejecutar()
    resultado = cmd.deshacer()
    assert resultado["ok"] is True
    assert cuenta.saldo == saldo_origen_original
    assert cuenta_destino.saldo == saldo_destino_original


# ── HistorialComandos (Invoker) — undo/redo ──────────────────────────────

def test_ejecutar_registra_en_stack_undo(cuenta, historial):
    cmd = ComandoDeposito(cuenta, 100_000)
    historial.ejecutar(cmd)
    assert historial.puede_deshacer() is True
    assert historial.puede_reejecutar() is False


def test_deshacer_mueve_command_a_stack_redo(cuenta, historial):
    cmd = ComandoDeposito(cuenta, 100_000)
    historial.ejecutar(cmd)
    resultado = historial.deshacer()
    assert resultado["ok"] is True
    assert historial.puede_deshacer() is False
    assert historial.puede_reejecutar() is True
    assert cuenta.saldo == 1_000_000  # vuelve al saldo original


def test_reejecutar_aplica_de_nuevo_la_operacion(cuenta, historial):
    cmd = ComandoDeposito(cuenta, 100_000)
    historial.ejecutar(cmd)
    historial.deshacer()
    resultado = historial.reejecutar()
    assert resultado["ok"] is True
    assert cuenta.saldo == 1_100_000
    assert historial.puede_deshacer() is True
    assert historial.puede_reejecutar() is False


def test_deshacer_sin_operaciones_retorna_error(historial):
    resultado = historial.deshacer()
    assert resultado["ok"] is False


def test_reejecutar_sin_operaciones_retorna_error(historial):
    resultado = historial.reejecutar()
    assert resultado["ok"] is False


def test_nuevo_comando_limpia_stack_redo(cuenta, historial):
    """Comportamiento estándar de undo/redo: ejecutar un comando nuevo
    después de un undo descarta la rama de redo (igual que en un editor)."""
    cmd1 = ComandoDeposito(cuenta, 100_000)
    historial.ejecutar(cmd1)
    historial.deshacer()
    assert historial.puede_reejecutar() is True

    cmd2 = ComandoDeposito(cuenta, 50_000)
    historial.ejecutar(cmd2)
    assert historial.puede_reejecutar() is False


def test_get_historial_incluye_comandos_ejecutados_y_deshechos(cuenta, historial):
    cmd1 = ComandoDeposito(cuenta, 100_000)
    cmd2 = ComandoRetiro(cuenta, 50_000)
    historial.ejecutar(cmd1)
    historial.ejecutar(cmd2)
    historial.deshacer()  # cmd2 pasa a redo

    tabla = historial.get_historial()
    tipos_en_stack = {(h["tipo"], h["en_stack"]) for h in tabla}
    assert ("deposito", "undo") in tipos_en_stack
    assert ("retiro", "redo") in tipos_en_stack


def test_limpiar_vacia_ambos_stacks(cuenta, historial):
    cmd = ComandoDeposito(cuenta, 100_000)
    historial.ejecutar(cmd)
    historial.deshacer()
    historial.limpiar()
    assert historial.puede_deshacer() is False
    assert historial.puede_reejecutar() is False
    assert historial.get_historial() == []
