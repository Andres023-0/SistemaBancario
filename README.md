# Patrones - Sistema Bancario Core

**Desarrollado por:**  

- Brayan Andrés Cañas León

- Juan Sebastián Niño Forero

Docente: Eliecer Montero Ojeda

Institución:

- Unidades Tecnológicas de Santander (UTS)

---

## Simulación de un Sistema Bancario

Este proyecto académico, denominado "Sistema Bancario Core", es una simulación avanzada de los componentes fundamentales de un entorno bancario moderno. Su propósito principal es ilustrar la aplicación práctica de principios de diseño de software y patrones arquitectónicos en un contexto financiero regulado, abordando desafíos como el cumplimiento normativo (KYC y AML) y la gestión de transacciones en tiempo real.

El objetivo central es demostrar cómo la implementación estratégica de ocho patrones de diseño (Singleton, Factory Method, Abstract Factory, Builder, Prototype, Adapter, Bridge y Decorator) contribuye a la construcción de un software de alta calidad: modular, mantenible, extensible y robusto, eliminando code smells y promoviendo una arquitectura limpia.

---

## Módulos Clave y Funcionalidades Financieras

El sistema bancario simulado integra funcionalidades esenciales que reflejan operaciones del sector financiero, destacando por su enfoque en la precisión y la seguridad:

• Gestión Integral de Cuentas: Soporte para cuentas corrientes y de ahorros, asociadas a usuarios previamente verificados. Cada cuenta mantiene un historial detallado de transacciones y gestiona su saldo utilizando el tipo de dato Decimal para garantizar la precisión financiera y evitar errores de redondeo críticos.

• Procesamiento Multicanal de Transacciones: Las operaciones bancarias (depósitos, retiros, transferencias) pueden ser iniciadas a través de diversos canales (Web, Móvil, Cajero). Cada canal implementa sus propias reglas de negocio, incluyendo límites transaccionales, restricciones específicas y mecanismos de notificación diferenciados.

• Detección de Fraude en Tiempo Real: Un módulo especializado (DetectorFraude) evalúa cada transacción frente a un conjunto de cinco reglas críticas antes de su aprobación. Estas reglas incluyen la verificación de límites AML, la detección de alta frecuencia transaccional, el monitoreo de saldos críticos, la identificación de canales inusuales y la validación de transferencias a cuentas sin historial previo.

• Verificación KYC (Know Your Customer): Se exige que cada Usuario complete un proceso de verificación KYC (verificado_kyc = True) como requisito indispensable antes de poder abrir cualquier tipo de cuenta bancaria, asegurando el cumplimiento normativo.

• Cumplimiento AML (Anti Money Laundering): La configuración global del sistema (ConfigBanco) centraliza los umbrales y políticas para la prevención del lavado de dinero. Esto incluye un límite de $10.000 por transacción, un máximo de 5 operaciones en un período de 5 minutos y un saldo mínimo de $1.000 para ciertas operaciones.

• Construcción Segura y Consistente de Cuentas: El CuentaBuilder facilita la creación de nuevas cuentas bancarias mediante una API fluida y encadenable. Este patrón garantiza que cada cuenta se construya con todos sus atributos válidos y que las validaciones necesarias se realicen de manera centralizada y atómica.

---

## Patrones de Diseño Implementados

El proyecto banco_coreDeco es una demostración práctica de cómo los patrones de diseño pueden estructurar una aplicación compleja, promoviendo la modularidad y la extensibilidad. A continuación, se detallan los ocho patrones implementados:

| Patrón de Diseño | Descripción y Aplicación en el Proyecto |
| :--- | :--- |
| **Singleton** | Asegura una única instancia global para componentes críticos como la configuración (`ConfigBanco`), el sistema de registro (`Logger`), el detector de fraude (`DetectorFraude`) y el gestor de sucursales (`SucursalesManager`). Implementado con *Double-Checked Locking* para garantizar la seguridad en entornos multihilo. |
| **Factory Method** | Desacopla la creación de objetos de su uso. Permite que la clase `Transaccion` solicite la creación de operaciones bancarias (`Deposito`, `Retiro`, `Transferencia`) a fábricas especializadas, facilitando la adición de nuevos tipos de operaciones sin modificar el código existente de `Transaccion`. |
| **Abstract Factory** | Proporciona una interfaz para crear familias de objetos relacionados o dependientes sin especificar sus clases concretas. En este proyecto, se utiliza para generar conjuntos coherentes de `Validador`, `Notificador` y `LimiteCanal` específicos para cada canal (Web, Móvil, Cajero), encapsulando las reglas de negocio por canal. |
| **Builder (Fluent Builder)** | Separa la construcción de un objeto complejo de su representación, permitiendo que el mismo proceso de construcción cree diferentes representaciones. El `CuentaBuilder` ofrece una API fluida para construir objetos `Cuenta` de manera segura y legible, centralizando las validaciones y asegurando la integridad del objeto final. |
| **Prototype** | Permite crear nuevos objetos clonando instancias existentes, evitando la necesidad de recrear objetos complejos desde cero. El `CuentaPrototypeRegistry` y el método `clone()` en `Cuenta` facilitan la creación de cuentas plantilla y su posterior clonación, ideal para escenarios donde se necesitan múltiples cuentas con configuraciones similares. |
| **Adapter** | Permite que interfaces incompatibles trabajen juntas. Se utiliza para integrar servicios externos de notificación (SMS, Email, Voucher) con la lógica interna del sistema. Los adaptadores (`NotificadorAdapterProducer`) permiten que el sistema envíe mensajes a los usuarios a través de diferentes medios sin que la lógica de `Transaccion` necesite conocer los detalles de cada proveedor. |
| **Bridge** | Desacopla una abstracción de su implementación, permitiendo que ambas evolucionen de forma independiente. Es el patrón central que une las operaciones bancarias (`OperacionBancaria`) con los canales de atención (`CanalBancario`), permitiendo añadir nuevas operaciones o nuevos canales sin afectar la otra jerarquía. |
| **Decorator** | Permite añadir nuevas funcionalidades a un objeto dinámicamente sin alterar su estructura. El `OperacionDecoratorProducer` envuelve las operaciones bancarias con comportamientos transversales como el registro de tiempo (`LogTiempoDecorator`), la auditoría (`AuditoriaDecorator`) o la gestión de reintentos (`ReintentoDecorator`), sin modificar las clases de operación originales. |

---

## Resumen de Archivos del Proyecto

La siguiente tabla proporciona una visión general de los archivos clave del proyecto, su rol principal y los patrones de diseño asociados:

| Archivo(s) | Patrón(es) Asociado(s) | Rol Principal en el Sistema |
| :--- | :--- | :--- |
| `config_banco.py` | Singleton | Centraliza la configuración global del sistema y umbrales AML. |
| `logger.py` | Singleton | Proporciona un sistema de registro centralizado para eventos del sistema. |
| `detector_fraude.py` | Singleton | Implementa la lógica para la detección de fraude en transacciones. |
| `sucursales_manager.py` | Singleton | Gestiona las sucursales bancarias disponibles en el sistema. |
| `operacion.py`, `operacion_factory.py` | Factory Method | Define la interfaz para operaciones bancarias y sus fábricas de creación. |
| `canal_factory.py` | Abstract Factory | Crea familias de validadores, notificadores y límites específicos por canal. |
| `canal_bridge.py`, `operacion_bridge.py` | Bridge | Desacopla las operaciones bancarias de sus implementaciones por canal. |
| `cuenta_builder.py` | Builder | Facilita la construcción segura y fluida de objetos `Cuenta`. |
| `cuenta.py`, `cuenta_prototype.py` | Prototype | Permite la clonación de cuentas plantilla y la gestión de saldos con precisión `Decimal`. |
| `notificador_adapter.py` | Adapter | Adapta servicios de notificación externos (SMS, Email, Voucher) al sistema. |
| `operacion_decorator.py` | Decorator | Añade dinámicamente comportamientos transversales a las operaciones. |
| `transaccion.py` | Bridge, Decorator | Orquesta el procesamiento de transacciones, delegando al Bridge y aplicando Decorators. |
| `banco.py` | Dominio | Actúa como el orquestador principal, gestionando usuarios y cuentas. |
| `usuario.py` | Dominio | Representa a los clientes del banco y gestiona su estado KYC. |
| `sucursal.py` | Dominio | Define la entidad sucursal y su asociación con cuentas. |
| `main.py` | Cliente | Punto de entrada del sistema, interactúa con el usuario a través de la consola. |

---

## Diagrama UML — Sistema Bancario Core

El diagrama representa la arquitectura del Sistema Bancario Core implementado en Python, mostrando cómo las clases se relacionan entre sí y cómo los cinco patrones de diseño coexisten dentro del mismo sistema.

    classDiagram
    %% CAPA DE CONFIGURACIÓN Y SERVICIOS (SINGLETON)
    class ConfigBanco {
        <<Singleton>>
        - _instancia: ConfigBanco
        + get_instancia() ConfigBanco
        + get_limite_aml() Decimal
    }

    class DetectorFraude {
        <<Singleton>>
        + evaluar(cuenta, monto, canal, tipo) bool
    }

    class Logger {
        <<Singleton>>
        + log(mensaje, nivel)
    }

    class SucursalesManager {
        <<Singleton>>
        + sucursales: List
    }

    %% CAPA DE CREACIÓN (BUILDER + PROTOTYPE)
    class CuentaBuilder {
        - _numero: str
        - _tipo: str
        - _usuario: Usuario
        + tipo(str) self
        + saldo_inicial(Decimal) self
        + build() Cuenta
        + clone_desde(Cuenta) Cuenta
    }

    class CuentaPrototypeRegistry {
        - _plantillas: dict
        + registrar_plantilla(nombre, cuenta)
        + obtener_plantilla(nombre) Cuenta
    }

    class Cuenta {
        + numero: str
        - _saldo: Decimal
        + clone() Cuenta
        + depositar(monto)
    }

    CuentaBuilder ..> Cuenta : "Construye"
    CuentaBuilder ..> CuentaPrototypeRegistry : "Usa para clone_desde"
    Cuenta ..> Cuenta : "Prototype (clone)"

    %% CAPA DE EJECUCIÓN (BRIDGE)
    class OperacionBancaria {
        <<Abstract>>
        - _canal: CanalBancario
        + ejecutar() bool
        # _operar()*
    }

    class CanalBancario {
        <<Interface>>
        + validar(monto, tipo) bool
        + notificar(tipo, monto)
    }

    OperacionBancaria o-- CanalBancario : "Bridge (Puente)"
    
    class Deposito { + _operar() }
    class Retiro { + _operar() }
    class Transferencia { + _operar() }
    OperacionBancaria <|-- Deposito
    OperacionBancaria <|-- Retiro
    OperacionBancaria <|-- Transferencia

    class CanalWeb { + validar() }
    class CanalMovil { + validar() }
    class CanalCajero { + validar() }
    CanalBancario <|-- CanalWeb
    CanalBancario <|-- CanalMovil
    CanalBancario <|-- CanalCajero

    %% CAPA DE EXTENSIBILIDAD (DECORATOR + ADAPTER + ABSTRACT FACTORY)
    class OperacionDecorator {
        <<Abstract>>
        - _operacion: Operacion
        + ejecutar()
    }
    
    class AuditoriaDecorator { + ejecutar() }
    class LogTiempoDecorator { + ejecutar() }
    class ReintentoDecorator { + ejecutar() }
    OperacionDecorator <|-- AuditoriaDecorator
    OperacionDecorator <|-- LogTiempoDecorator
    OperacionDecorator <|-- ReintentoDecorator

    class AbstractCanalFactory {
        <<Interface>>
        + crear_validador()
        + crear_notificador()
    }
    CanalBancario ..> AbstractCanalFactory : "Usa para componentes"

    class NotificadorAdapter {
        <<Interface>>
        + enviar(mensaje)
    }
    
    class SMSAdapter { - _servicioSMS: ServicioSMS }
    class EmailAdapter { - _servicioEmail: ServicioEmail }
    NotificadorAdapter <|-- SMSAdapter
    NotificadorAdapter <|-- EmailAdapter
    CanalBancario ..> NotificadorAdapter : "Usa para notificar"

    %% RELACIONES DE DOMINIO
    class Usuario {
        + nombre: str
        + verificado_kyc: bool
    }
    
    class Sucursal {
        + nombre: str
        + cuentas: List
    }

    Usuario "1" *-- "0..*" Cuenta : "Posee"
    Sucursal "1" *-- "0..*" Cuenta : "Contiene"
    CuentaBuilder --> Usuario : "Asocia"
    CuentaBuilder --> Sucursal : "Asocia"
<img width="8191" height="2312" alt="Diagrama" src="https://github.com/user-attachments/assets/d19bad59-4b9a-46a9-9f12-2c18cec0eba4" />

---
  ------------------------------
# Documentacion de las implementaciones semana a semana 

https://github.com/Andres023-0/SistemaBancario/blob/main/Documentacion_Implementacion.docx

