"""
Tests unitarios — Memento (memento_cuenta.py)
Cubre: MementoEstadoCuenta, CaretakerCuenta, GestorMementos (snapshots de estado).
Ejecutar: pytest tests/test_memento_cuenta.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cuenta import Cuenta
from estado_cuenta import EstadoActiva, EstadoBloqueada
from memento_cuenta import GestorMementos, CaretakerCuenta, MementoEstadoCuenta


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def cuenta():
    return Cuenta(numero="8001", tipo="ahorros", saldo_inicial=1_000_000)


@pytest.fixture
def gestor():
    """GestorMementos es Singleton: se limpia el caretaker de la cuenta
    de prueba antes de cada test para evitar fugas de estado entre tests."""
    g = GestorMementos.get_instancia()
    g._caretakers.pop("8001", None)
    return g


# ── CaretakerCuenta (aislado) ─────────────────────────────────────────────

def test_caretaker_guardar_agrega_al_historial():
    caretaker = CaretakerCuenta("9999")
    memento = MementoEstadoCuenta(EstadoActiva(), "activa", "", "9999")
    caretaker.guardar(memento)
    assert caretaker.total_snapshots() == 1
    assert caretaker.tiene_historial() is True


def test_caretaker_deshacer_extrae_el_ultimo_memento():
    caretaker = CaretakerCuenta("9999")
    m1 = MementoEstadoCuenta(EstadoActiva(), "activa", "", "9999")
    m2 = MementoEstadoCuenta(EstadoBloqueada(), "bloqueada", "fraude", "9999")
    caretaker.guardar(m1)
    caretaker.guardar(m2)

    extraido = caretaker.deshacer()
    assert extraido is m2
    assert caretaker.total_snapshots() == 1


def test_caretaker_deshacer_sin_historial_retorna_none():
    caretaker = CaretakerCuenta("9999")
    assert caretaker.deshacer() is None


def test_caretaker_respeta_limite_maximo_fifo():
    caretaker = CaretakerCuenta("9999")
    for i in range(caretaker.MAX_HISTORIAL + 5):
        caretaker.guardar(MementoEstadoCuenta(EstadoActiva(), f"activa-{i}", "", "9999"))
    assert caretaker.total_snapshots() == caretaker.MAX_HISTORIAL


# ── GestorMementos + Cuenta (integración) ────────────────────────────────

def test_guardar_estado_captura_estado_actual_de_la_cuenta(cuenta, gestor):
    memento = gestor.guardar_estado(cuenta)
    assert memento.to_dict()["estado"] == "activa"
    assert gestor.total_snapshots(cuenta.numero) == 1


def test_restaurar_estado_revierte_bloqueo_de_cuenta(cuenta, gestor):
    # 1) Snapshot mientras está activa
    gestor.guardar_estado(cuenta)
    # 2) Se bloquea la cuenta (cambio real de estado, vía State)
    cuenta.bloquear(motivo="fraude detectado")
    assert cuenta.get_estado().get_nombre() == "bloqueada"

    # 3) Restaurar el snapshot debe devolverla a "activa"
    resultado = gestor.restaurar_estado(cuenta)
    assert resultado["ok"] is True
    assert resultado["estado_anterior"] == "bloqueada"
    assert resultado["estado_restaurado"] == "activa"
    assert cuenta.get_estado().get_nombre() == "activa"


def test_restaurar_estado_sin_snapshots_retorna_error(cuenta, gestor):
    resultado = gestor.restaurar_estado(cuenta)
    assert resultado["ok"] is False


def test_restaurar_estado_consume_el_snapshot_usado(cuenta, gestor):
    gestor.guardar_estado(cuenta)
    cuenta.bloquear()
    gestor.restaurar_estado(cuenta)
    assert gestor.total_snapshots(cuenta.numero) == 0


def test_ver_historial_retorna_snapshots_como_diccionarios(cuenta, gestor):
    gestor.guardar_estado(cuenta)
    cuenta.bloquear(motivo="revisión manual")
    gestor.guardar_estado(cuenta)

    historial = gestor.ver_historial(cuenta.numero)
    assert len(historial) == 2
    assert historial[0]["numero_cuenta"] == cuenta.numero
    assert {h["estado"] for h in historial} == {"activa", "bloqueada"}


def test_multiples_snapshots_permiten_deshacer_en_cascada(cuenta, gestor):
    """Guarda 2 estados intermedios y confirma que restaurar_estado
    va sacando el más reciente primero (LIFO), tal como Memento define."""
    gestor.guardar_estado(cuenta)          # snapshot: activa
    cuenta.bloquear(motivo="paso 1")
    gestor.guardar_estado(cuenta)          # snapshot: bloqueada
    cuenta.activar()
    cuenta.bloquear(motivo="paso 2")

    assert gestor.total_snapshots(cuenta.numero) == 2

    r1 = gestor.restaurar_estado(cuenta)   # vuelve a "bloqueada" (último guardado)
    assert r1["ok"] is True
    assert r1["estado_restaurado"] == "bloqueada"

    r2 = gestor.restaurar_estado(cuenta)   # vuelve a "activa" (primer guardado)
    assert r2["ok"] is True
    assert r2["estado_restaurado"] == "activa"
    assert cuenta.get_estado().get_nombre() == "activa"
