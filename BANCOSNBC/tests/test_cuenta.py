"""
Tests unitarios — Cuenta (cuenta.py)
Cubre: operaciones básicas, validación de tipo, State, Prototype.
Ejecutar: pytest tests/test_cuenta.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cuenta import Cuenta
from estado_cuenta import EstadoBloqueada, EstadoCerrada, EstadoActiva


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def cuenta():
    return Cuenta(numero="9001", tipo="ahorros", saldo_inicial=1_000_000)


@pytest.fixture
def cuenta_destino():
    return Cuenta(numero="9002", tipo="corriente", saldo_inicial=500_000)


# ── Construcción ──────────────────────────────────────────────────────────

def test_tipo_invalido_lanza_error():
    with pytest.raises(ValueError):
        Cuenta(numero="9999", tipo="invalido")


def test_saldo_inicial_correcto(cuenta):
    assert cuenta.saldo == 1_000_000


# ── Depósito ──────────────────────────────────────────────────────────────

def test_deposito_incrementa_saldo(cuenta):
    cuenta.depositar(200_000, canal="web")
    assert cuenta.saldo == 1_200_000


def test_deposito_monto_negativo_lanza_error(cuenta):
    with pytest.raises(ValueError):
        cuenta.depositar(-100, canal="web")


def test_deposito_monto_cero_lanza_error(cuenta):
    with pytest.raises(ValueError):
        cuenta.depositar(0, canal="web")


# ── Retiro ────────────────────────────────────────────────────────────────

def test_retiro_disminuye_saldo(cuenta):
    cuenta.retirar(300_000, canal="cajero")
    assert cuenta.saldo == 700_000


def test_retiro_saldo_insuficiente_lanza_error(cuenta):
    with pytest.raises(ValueError):
        cuenta.retirar(999_999_999, canal="cajero")


# ── Transferencia ─────────────────────────────────────────────────────────

def test_transferencia_mueve_dinero_entre_cuentas(cuenta, cuenta_destino):
    cuenta.transferir(cuenta_destino, 250_000, canal="web")
    assert cuenta.saldo == 750_000
    assert cuenta_destino.saldo == 750_000


# ── Precisión decimal (crítico en banca) ────────────────────────────────────

def test_precision_decimal_evita_errores_de_flotante():
    c = Cuenta(numero="9003", tipo="ahorros", saldo_inicial=0.1)
    c.depositar(0.2, canal="web")
    assert c.saldo == 0.3  # con float puro esto falla (0.30000000000000004)


# ── State ─────────────────────────────────────────────────────────────────

def test_cuenta_bloqueada_rechaza_deposito(cuenta):
    cuenta.bloquear(motivo="fraude detectado")
    with pytest.raises(ValueError):
        cuenta.depositar(100_000, canal="web")


def test_cuenta_bloqueada_rechaza_retiro(cuenta):
    cuenta.bloquear()
    with pytest.raises(ValueError):
        cuenta.retirar(100_000, canal="cajero")


def test_cuenta_cerrada_es_terminal(cuenta):
    cuenta.cerrar()
    assert isinstance(cuenta.get_estado(), EstadoCerrada)
    cuenta.activar()  # no debe tener efecto: estado terminal
    assert isinstance(cuenta.get_estado(), EstadoCerrada)


def test_activar_reactiva_cuenta_bloqueada(cuenta):
    cuenta.bloquear()
    cuenta.activar()
    assert isinstance(cuenta.get_estado(), EstadoActiva)
    cuenta.depositar(50_000, canal="web")  # ya no debe lanzar error
    assert cuenta.saldo == 1_050_000


# ── Observer ──────────────────────────────────────────────────────────────

def test_desuscribir_observador_detiene_notificaciones(cuenta):
    eventos = []

    class ObservadorDePrueba:
        def get_nombre(self):
            return "ObservadorDePrueba"

        def update(self, evento):
            eventos.append(evento)

    obs = ObservadorDePrueba()
    cuenta.suscribir(obs)
    cuenta.depositar(10_000, canal="web")
    assert len(eventos) == 1

    cuenta.desuscribir(obs)
    cuenta.depositar(10_000, canal="web")
    assert len(eventos) == 1  # no debe crecer tras desuscribir


# ── Prototype ─────────────────────────────────────────────────────────────

def test_clone_genera_cuenta_independiente(cuenta):
    cuenta.depositar(500_000, canal="web")  # da historial de transacciones
    clon = cuenta.clone(nuevo_numero="9099")

    assert clon.numero == "9099"
    assert clon.tipo == cuenta.tipo
    assert clon.saldo == cuenta.saldo
    assert clon.transacciones == []           # historial no se hereda
    assert isinstance(clon.get_estado(), EstadoActiva)  # nace activa

    # Independencia: modificar el clon no debe afectar al original
    clon.depositar(100_000, canal="web")
    assert clon.saldo != cuenta.saldo
