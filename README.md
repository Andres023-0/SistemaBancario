# Sistema Bancario Core — BANCOSNBC

Sistema bancario educativo que implementa 16 patrones de diseño GoF sobre un dominio real: usuarios, cuentas, transacciones, préstamos, fraude y reportes. Expone dos interfaces: CLI (`main.py`) y API REST (`api.py`) consumida por un frontend HTML/CSS/JS vanilla.

## Requisitos

- Python 3.11+
- pip

## Instalación

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

### CLI

```bash
python main.py
```

### API REST

```bash
python api.py
```

Por defecto levanta en `http://localhost:5000` con datos de prueba precargados (`seed.py`, `seed_prestamos.py`).

## Variables de entorno (producción)

| Variable | Default | Descripción |
|---|---|---|
| `FLASK_DEBUG` | `0` | `1` activa el debugger de Werkzeug. **Nunca en producción.** |
| `CORS_ORIGINS` | `*` | Lista separada por comas de orígenes permitidos. |
| `API_KEY` | *(vacío)* | Si se define, exige header `X-API-Key` en 16 endpoints sensibles (dinero, undo/redo, eliminación, préstamos). |
| `PORT` | `5000` | Puerto del servidor Flask. |

Ejemplo producción:

```bash
export FLASK_DEBUG=0
export CORS_ORIGINS=https://tu-frontend.com
export API_KEY=$(openssl rand -hex 32)
python api.py
```

## Arquitectura

```
main.py (CLI)  ─┐
                 ├──> Facades (operacion_facade, usuario_facade) ──> Banco (Composite root)
api.py (Flask)  ─┘                                                        │
                                                                    Sucursal → Cuenta
frontend (*.html) ──fetch──> api.py (37 endpoints REST)
```

**Persistencia:** en memoria (RAM). Los datos se pierden al reiniciar el proceso. Ver roadmap.

## Patrones de diseño implementados

| Patrón | Archivo | Rol |
|---|---|---|
| Singleton | `logger.py`, `config_banco.py`, `sucursales_manager.py` | Instancias únicas compartidas |
| Composite | `componente_bancario.py`, `banco.py`, `sucursal.py`, `cuenta.py` | Árbol Banco → Sucursal → Cuenta |
| Builder | `cuenta_builder.py` | Construcción fluida de cuentas |
| Prototype | `cuenta_prototype.py` | Clonación de cuentas plantilla |
| Factory Method | `operacion_factory.py`, `canal_factory.py` | Creación de operaciones/canales |
| Facade | `operacion_facade.py`, `usuario_facade.py` | Interfaz simplificada para CLI/API |
| Decorator | `operacion_decorator.py` | Tiempo, auditoría, reintento apilables |
| Bridge | `operacion_bridge.py`, `canal_bridge.py` | Desacople operación ↔ canal |
| Adapter | `notificador_adapter.py` | Normalización de notificaciones |
| Observer | `observer_cuenta.py` | Fraude, saldo crítico, log de movimientos |
| State | `estado_cuenta.py` | Activa / Bloqueada / Suspendida / Cerrada |
| Memento | `memento_cuenta.py` | Snapshots y restauración de estado |
| Command | `command_transaccion.py` | Undo/redo de transacciones |
| Chain of Responsibility | `validacion_chain.py` | Validaciones encadenadas (AML, límites, KYC) |
| Strategy | `prestamo_strategy.py` | Cálculo de interés de préstamos |
| Template Method | `reporte_template.py` | Generación de reportes |

## Roadmap de mejoras

- [x] **Fase 1** — Seguridad: debug controlado, CORS restringible, API key opcional en endpoints sensibles.
- [x] **Fase 2** — Higiene: `requirements.txt`, `.gitignore`, `README.md`.
- [ ] **Fase 3** — Tests automatizados (`Cuenta`, `validacion_chain`, `detector_fraude`).
- [ ] **Fase 4** — Persistencia real (SQLite/Postgres vía capa de repositorio).
