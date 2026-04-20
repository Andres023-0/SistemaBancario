# Patrones - Sistema Bancario Core

**Desarrollado por:**  

- Brayan Andrés Cañas León

- Juan Sebastián Niño Forero

Docente: Eliecer Montero Ojeda

Institución:

- Unidades Tecnológicas de Santander (UTS)

---

## Simulación de un Sistema Bancario

Este proyecto académico, denominado "Sistema Bancario Core", es una simulación avanzada de los componentes fundamentales de un entorno bancario moderno. Su propósito principal es ilustrar la aplicación práctica de principios de diseño de software y patrones arquitectónicos en un contexto financiero regulado, abordando desafíos reales como el cumplimiento normativo (KYC y AML), la detección de fraude en tiempo real y la gestión segura de transacciones a través de múltiples canales.

El objetivo central es demostrar cómo la implementación estratégica de diez patrones de diseño — Singleton, Factory Method, Abstract Factory, Builder, Prototype, Adapter, Bridge, Decorator, Facade y Composite — contribuye a la construcción de un software de alta calidad: modular, mantenible, extensible y robusto. Estos patrones permiten eliminar code smells, promover una arquitectura limpia y lograr un alto nivel de desacoplamiento entre componentes, facilitando la evolución futura del sistema.

---

## Módulos Clave y Funcionalidades Financieras

El sistema bancario simulado integra funcionalidades esenciales que reflejan operaciones reales del sector financiero, con un fuerte enfoque en la precisión, la seguridad y el cumplimiento normativo. Las principales capacidades del sistema son las siguientes:

• Gestión Integral de Cuentas: El sistema soporta cuentas de tipo corriente y de ahorros, asociadas exclusivamente a usuarios previamente verificados. Cada cuenta mantiene un historial completo de transacciones y gestiona su saldo utilizando el tipo de dato Decimal con redondeo ROUND_HALF_UP, garantizando precisión financiera exacta y evitando errores de redondeo acumulativos.

• Procesamiento Multicanal de Transacciones: Las operaciones bancarias (depósitos, retiros y transferencias) pueden ejecutarse a través de tres canales distintos: Web, Móvil y Cajero. Cada canal aplica sus propias reglas de negocio, incluyendo límites transaccionales específicos, restricciones por tipo de operación y mecanismos de notificación diferenciados (email, SMS o voucher físico).

• Detección de Fraude en Tiempo Real: El módulo DetectorFraude, implementado como Singleton, evalúa cada transacción antes de su aprobación aplicando cinco reglas críticas: límite AML por transacción, detección de alta frecuencia de operaciones, monitoreo de saldos críticos después de retiros o transferencias, identificación de canales inusuales y validación de transferencias hacia cuentas sin historial previo.

• Verificación KYC (Know Your Customer): Se exige que cada usuario complete el proceso de verificación KYC (verificado_kyc = True) antes de poder crear cualquier cuenta bancaria. Esta validación es obligatoria y se realiza de forma centralizada durante la construcción de la cuenta.

• Cumplimiento AML (Anti Money Laundering): La configuración global del sistema, gestionada a través del Singleton ConfigBanco, centraliza todos los umbrales y políticas para la prevención del lavado de dinero. Entre ellos se incluyen un límite de $10.000 por transacción, un máximo de 5 operaciones en una ventana de 5 minutos y un saldo crítico mínimo de $1.000.

• Construcción Segura y Consistente de Cuentas: El CuentaBuilder (patrón Builder) permite la creación de cuentas mediante una API fluida y encadenable. Este componente garantiza que cada cuenta se construya de forma atómica, aplicando todas las validaciones necesarias (KYC, número único, asociación a usuario y sucursal) antes de que el objeto sea instanciado.

---

## Patrones de Diseño Implementados

El proyecto **Sistema Bancario Core** es una demostración práctica de cómo los patrones de diseño pueden estructurar una aplicación compleja, promoviendo la modularidad, la extensibilidad y el cumplimiento de principios SOLID. A continuación, se detallan los **diez patrones de diseño** implementados en el sistema:

| Patrón de Diseño          | Descripción y Aplicación en el Proyecto |
|---------------------------|-----------------------------------------|
| **Singleton**             | Asegura una única instancia global para componentes críticos del sistema. Se aplica en `ConfigBanco`, `Logger`, `DetectorFraude` y `SucursalesManager`. Se implementó utilizando la variante *Double-Checked Locking* con `threading.Lock()` para garantizar seguridad en entornos multihilo. |
| **Factory Method**        | Desacopla la creación de objetos de su uso. Permite que `Transaccion` solicite la creación de operaciones bancarias (`Deposito`, `Retiro`, `Transferencia`) a través de fábricas especializadas (`DepositoFactory`, `RetiroFactory`, `TransferenciaFactory`), facilitando la adición de nuevos tipos de operaciones sin modificar el código existente. |
| **Abstract Factory**      | Proporciona una interfaz para crear familias de objetos relacionados sin especificar sus clases concretas. Se utiliza para generar conjuntos coherentes de `Validador`, `Notificador` y `LimiteCanal` específicos para cada canal (Web, Móvil y Cajero), encapsulando las reglas de negocio por canal. |
| **Builder (Fluent Builder)** | Separa la construcción de un objeto complejo de su representación. El `CuentaBuilder` ofrece una API fluida y encadenable para construir objetos `Cuenta` de manera segura, centralizando todas las validaciones (KYC, número único, asociación a usuario y sucursal) antes de crear el objeto final. |
| **Prototype**             | Permite crear nuevos objetos clonando instancias existentes. El `CuentaPrototypeRegistry` junto con el método `clone()` en la clase `Cuenta` facilita la creación de cuentas plantilla y su posterior clonación, ideal para escenarios donde se requieren múltiples cuentas con configuraciones similares. |
| **Adapter**               | Permite que interfaces incompatibles trabajen juntas. Se utiliza para integrar servicios externos de notificación (SMS, Email y Voucher) con la lógica interna del sistema mediante los adaptadores (`SMSAdapter`, `EmailAdapter`, `VoucherAdapter`) y el `NotificadorAdapterProducer`. |
| **Bridge**                | Desacopla una abstracción de su implementación, permitiendo que ambas evolucionen independientemente. Es el patrón central del sistema: une las operaciones bancarias (`OperacionBancaria`) con los canales de atención (`CanalBancario`), permitiendo agregar nuevas operaciones o nuevos canales sin afectar la otra jerarquía. |
| **Decorator**             | Permite añadir funcionalidades adicionales a un objeto de forma dinámica sin alterar su estructura. El `OperacionDecoratorProducer` envuelve las operaciones con comportamientos transversales como registro de tiempo (`LogTiempoDecorator`), auditoría (`AuditoriaDecorator`) y gestión de reintentos (`ReintentoDecorator`). |
| **Facade**                | Proporciona una interfaz simplificada a un subsistema complejo. Se implementa en `OperacionFacade` y `UsuarioFacade`, ocultando la complejidad de clases como `Banco`, `CuentaBuilder`, `Transaccion` y `SucursalesManager`, y haciendo que `main.py` sea mucho más limpio y mantenible. |
| **Composite**             | Permite tratar de forma uniforme objetos individuales y composiciones de objetos. Se aplica en la jerarquía `Banco` → `Sucursal` → `Cuenta` mediante la interfaz `ComponenteBancario`, permitiendo consultar saldos totales y visualizar la estructura completa del banco de manera recursiva y uniforme. |
---

## Resumen de Archivos del Proyecto

La siguiente tabla proporciona una visión general de los archivos clave del proyecto, su rol principal y los patrones de diseño asociados:

| Archivo(s)                          | Patrón(es) Asociado(s)                  | Rol Principal en el Sistema |
|-------------------------------------|-----------------------------------------|-----------------------------|
| `config_banco.py`                   | Singleton                               | Centraliza la configuración global del sistema (umbrales AML, límites de transacciones, etc.). |
| `logger.py`                         | Singleton                               | Proporciona un sistema de registro centralizado y thread-safe para todos los eventos del sistema. |
| `detector_fraude.py`                | Singleton                               | Implementa la detección de fraude en tiempo real mediante cinco reglas críticas. |
| `sucursales_manager.py`             | Singleton                               | Gestiona las sucursales bancarias disponibles en el sistema. |
| `operacion.py`, `operacion_factory.py` | Factory Method                        | Define la interfaz para operaciones bancarias y sus fábricas de creación (`Deposito`, `Retiro`, `Transferencia`). |
| `canal_factory.py`                  | Abstract Factory                        | Crea familias completas de objetos relacionados (`Validador`, `Notificador`, `LimiteCanal`) por canal. |
| `canal_bridge.py`, `operacion_bridge.py` | Bridge                               | Desacopla las operaciones bancarias de los canales de atención, permitiendo que ambas jerarquías evolucionen independientemente. |
| `cuenta_builder.py`                 | Builder + Prototype                     | Facilita la construcción segura y fluida de objetos `Cuenta` mediante una API encadenable. |
| `cuenta.py`, `cuenta_prototype.py`  | Prototype                               | Permite la clonación de cuentas plantilla y gestiona los saldos con precisión usando `Decimal`. |
| `notificador_adapter.py`            | Adapter                                 | Adapta servicios externos de notificación (SMS, Email, Voucher) a la interfaz interna del sistema. |
| `operacion_decorator.py`            | Decorator                               | Añade dinámicamente comportamientos transversales (tiempo, auditoría, reintentos) a las operaciones. |
| `operacion_facade.py`, `usuario_facade.py` | Facade                            | Proporciona una interfaz simplificada para operaciones y gestión de usuarios, ocultando la complejidad interna. |
| `componente_bancario.py`, `banco.py`, `sucursal.py`, `cuenta.py` | Composite | Permite tratar de forma uniforme cuentas individuales, sucursales y el banco completo mediante una interfaz común. |
| `transaccion.py`                    | Bridge + Decorator                      | Orquesta el procesamiento de transacciones, delegando al Bridge y aplicando decoradores cuando corresponde. |
| `main.py`                           | Cliente                                 | Punto de entrada del sistema. Interactúa con el usuario a través de la consola y utiliza las fachadas. |

---

## Diagrama UML — Sistema Bancario Core

El siguiente diagrama representa la arquitectura general del **Sistema Bancario Core**, mostrando cómo las clases se relacionan entre sí y cómo los diez patrones de diseño coexisten y colaboran dentro del mismo sistema.
    
    classDiagram
    direction TB

    %% ==================== SINGLETONS ====================
    class ConfigBanco {
        <<Singleton>>
        + get_instancia() ConfigBanco
        + get_limite_aml() float
    }

    class Logger {
        <<Singleton>>
        + log(mensaje, nivel)
    }

    class DetectorFraude {
        <<Singleton>>
        + evaluar(cuenta, monto, canal, tipo) bool
    }

    class SucursalesManager {
        <<Singleton>>
        + sucursales: List~Sucursal~
    }

    %% ==================== CREACIÓN ====================
    class CuentaBuilder {
        + numero(str) CuentaBuilder
        + tipo(str) CuentaBuilder
        + saldo_inicial(float) CuentaBuilder
        + build() Cuenta
        + clone_desde(Cuenta) Cuenta
    }

    class CuentaPrototypeRegistry {
        + registrar(nombre, cuenta)
        + get(nombre) Cuenta
    }

    class Cuenta {
        + numero: str
        - _saldo: Decimal
        + depositar(monto, canal)
        + retirar(monto, canal)
        + transferir(destino, monto, canal)
        + clone(nuevo_numero) Cuenta
    }

    %% ==================== BRIDGE ====================
    class OperacionBancaria {
        <<Abstract>>
        - _canal: CanalBancario
        + ejecutar(cuenta, monto, destino?) bool
    }

    class CanalBancario {
        <<Interface>>
        + validar(monto, tipo) bool
        + notificar(tipo, monto, cuenta, usuario)
        + get_nombre() str
    }

    class Deposito
    class Retiro
    class Transferencia

    OperacionBancaria <|-- Deposito
    OperacionBancaria <|-- Retiro
    OperacionBancaria <|-- Transferencia

    class CanalWeb
    class CanalMovil
    class CanalCajero

    CanalBancario <|-- CanalWeb
    CanalBancario <|-- CanalMovil
    CanalBancario <|-- CanalCajero

    OperacionBancaria o-- CanalBancario : "Bridge"

    %% ==================== DECORATOR ====================
    class OperacionDecorator {
        <<Abstract>>
        - _operacion: Operacion
        + ejecutar()
    }

    class LogTiempoDecorator
    class AuditoriaDecorator
    class ReintentoDecorator

    OperacionDecorator <|-- LogTiempoDecorator
    OperacionDecorator <|-- AuditoriaDecorator
    OperacionDecorator <|-- ReintentoDecorator

    %% ==================== FACADE + ADAPTER + COMPOSITE ====================
    class OperacionFacade
    class UsuarioFacade

    class NotificadorAdapterProducer {
        + get_adapter(canal, usuario) Notificador
    }

    class ComponenteBancario {
        <<Interface>>
        + get_nombre() str
        + get_saldo_total() float
        + listar(nivel)
    }

    class Banco
    class Sucursal

    ComponenteBancario <|-- Banco
    ComponenteBancario <|-- Sucursal
    ComponenteBancario <|-- Cuenta

    %% ==================== RELACIONES ====================
    Usuario "1" *-- "0..*" Cuenta : "posee"
    Sucursal "1" *-- "0..*" Cuenta : "contiene"
    Banco "1" *-- "0..*" Sucursal : "tiene"

    CuentaBuilder --> Usuario : "asocia"
    CuentaBuilder --> Sucursal : "asocia"
    CuentaBuilder ..> Cuenta : "construye"
    CuentaBuilder ..> CuentaPrototypeRegistry : "usa para clonar"

    OperacionFacade --> OperacionBancaria : "usa"
    UsuarioFacade --> CuentaBuilder : "usa"

<img width="8192" height="2393" alt="Diagrama" src="https://github.com/user-attachments/assets/949892d7-af6d-453b-84cf-bd1496207e01" />

---
  ------------------------------
# Documentacion de las implementaciones semana a semana 

https://github.com/Andres023-0/SistemaBancario/blob/main/Documentacion_Implementacion.docx

