# Patrones - Sistema Bancario Core

**Desarrollado por:**  

- Brayan Andrés Cañas León

- Juan Sebastián Niño Forero

Docente: Eliecer Montero Ojeda

Institución:

- Unidades Tecnológicas de Santander (UTS)

---

## Sistema Bancario UTS: Una Plataforma Financiera Robusta y Extensible

El **Sistema Bancario UTS** es una plataforma de gestión financiera integral, meticulosamente diseñada para proporcionar una experiencia de usuario completa, confiable y segura en la administración de operaciones bancarias cotidianas. Este sistema permite a los usuarios registrarse, gestionar sus cuentas, y ejecutar transacciones fundamentales como depósitos, retiros y transferencias con agilidad, todo ello en un entorno que prioriza la **claridad, trazabilidad y seguridad** de cada movimiento financiero.

La arquitectura del Sistema Bancario UTS se distingue por su **diseño modular y la aplicación estratégica de 14 patrones de diseño de software** (GoF), incluyendo Singleton, Factory Method, Abstract Factory, Builder, Adapter, Prototype, Bridge, Decorator, Facade, Composite, Observer, Strategy, Command y State. Esta implementación avanzada garantiza que cada operación se ejecute de manera independiente y ordenada, resultando en un servicio estable, consistente y altamente adaptable a las demandas cambiantes del negocio. La modularidad y el desacoplamiento inherentes a estos patrones facilitan la extensibilidad, permitiendo la integración fluida de nuevas funcionalidades y la evolución del sistema sin comprometer su integridad.

Más allá de sus funcionalidades actuales, el Sistema Bancario UTS está cimentado sobre principios de diseño que anticipan futuras expansiones. Su estructura robusta soporta la incorporación de capacidades avanzadas, tales como la integración con diversas plataformas digitales, la generación de reportes financieros sofisticados y una persistencia de datos resiliente. Esta plataforma no solo satisface las necesidades presentes, sino que está preparada para escalar y evolucionar, asegurando su relevancia y eficiencia a largo plazo en el dinámico panorama financiero.

## Objetivos del Proyecto

El objetivo primordial del **Sistema Bancario UTS** es centralizar y automatizar la gestión financiera de cuentas a gran escala mediante una arquitectura de software avanzada. El sistema garantiza la verificación rigurosa de la identidad de los usuarios, el control preciso de las operaciones y la trazabilidad absoluta de cada movimiento, proporcionando así un entorno bancario altamente confiable, seguro y eficiente.

### Objetivos Específicos

Para alcanzar la visión del proyecto, se han definido y ejecutado los siguientes objetivos técnicos y funcionales:

#### Gestión y Operación Bancaria
| Objetivo | Implementación Técnica y Valor Agregado |
| :--- | :--- |
| **Verificación KYC** | Validar la identidad del usuario mediante un módulo **Know Your Customer** obligatorio antes de habilitar su operatividad, asegurando el cumplimiento normativo. |
| **Consulta en Tiempo Real** | Suministrar información financiera precisa mediante el patrón **Composite**, permitiendo decisiones informadas basadas en el estado real de los activos. |
| **Historial y Trazabilidad** | Habilitar consultas detalladas de transacciones reforzadas con el patrón **Observer**, registrando cada evento de forma independiente y segura. |
| **Auditoría y Reconstrucción** | Garantizar la integridad mediante el patrón **Command**, permitiendo auditar el origen de los fondos y reconstruir estados históricos con mecanismos de *Undo/Redo*. |
| **Gestión a Volumen** | Optimizar el rendimiento para múltiples cuentas con alto flujo transaccional mediante una arquitectura basada en los patrones **Bridge** y **Facade**. |

#### Ingeniería y Arquitectura de Software
1. **Desacoplamiento Estructural:** Implementar el patrón *Bridge* para separar las operaciones bancarias de los canales de acceso, permitiendo una evolución independiente de ambos componentes.
2. **Precisión Financiera:** Asegurar la integridad de todos los cálculos monetarios mediante el uso de tipos de datos *Decimal*, eliminando errores de redondeo en transacciones críticas.
3. **Control de Ciclo de Vida:** Administrar las restricciones de las cuentas mediante el patrón *State*, garantizando que solo se realicen operaciones permitidas según el estado actual.
4. **Seguridad Proactiva:** Integrar un motor de detección de fraude basado en el patrón *Singleton* para evaluar riesgos y comportamientos inusuales en tiempo real.
5. **Extensibilidad Transversal:** Aplicar el patrón *Decorator* para añadir capacidades de auditoría y medición de rendimiento sin modificar el código base de las operaciones.
6. **Integridad en la Construcción:** Estandarizar la creación de cuentas mediante el patrón *Builder*, asegurando que cumplan con todas las reglas de negocio antes de su activación.
7. **Integración Multicanal:** Desarrollar un sistema de notificaciones desacoplado utilizando el patrón *Adapter* para facilitar la conexión con diversos proveedores externos.
8. **Resiliencia Operativa:** Establecer mecanismos de recuperación y seguimiento histórico mediante comandos ejecutables y reversibles.

## Módulos Clave y Funcionalidades Financieras

El **Sistema Bancario UTS** integra funcionalidades críticas que reflejan operaciones reales del sector financiero, con un enfoque riguroso en la precisión, la seguridad y el cumplimiento normativo. A continuación, se detallan las capacidades centrales del sistema:

| Módulo | Funcionalidad y Valor Agregado | Fundamento Técnico |
| :--- | :--- | :--- |
| **Gestión de Cuentas** | Soporte para cuentas corrientes y de ahorros con precisión financiera exacta mediante el tipo de dato **Decimal** (ROUND_HALF_UP). | **Patrón State:** Controla el ciclo de vida y restricciones de la cuenta. |
| **Procesamiento Multicanal** | Ejecución de depósitos, retiros y transferencias vía **Web, Móvil y Cajero**, cada uno con límites y reglas de negocio propias. | **Patrón Bridge:** Desacopla la operación del canal de acceso. |
| **Seguridad y Fraude** | Evaluación en tiempo real de 5 reglas críticas: límites AML, alta frecuencia, saldos críticos, canales inusuales e historial de destino. | **Patrón Singleton:** Garantiza un motor de fraude centralizado y consistente. |
| **Verificación KYC** | Validación obligatoria de identidad (**Know Your Customer**) como requisito previo e ineludible para la apertura de productos financieros. | **Arquitectura de Facade:** Centraliza la lógica de cumplimiento en el registro. |
| **Cumplimiento AML** | Centralización de umbrales y políticas para la prevención del lavado de dinero (límites de $10,000 y ventanas de tiempo). | **Configuración Centralizada:** Gestión global de políticas de cumplimiento. |
| **Construcción Atómica** | Creación segura de cuentas mediante una API fluida que garantiza la integridad de todos los datos antes de la instanciación. | **Patrón Builder:** Asegura objetos válidos y consistentes desde su origen. |

### Capacidades Destacadas

*   **Notificaciones Inteligentes:** El sistema adapta el mensaje y el medio (Email, SMS o Voucher) según el canal utilizado y los datos reales del usuario, gracias a la implementación del patrón **Adapter**.
*   **Gestión de Préstamos:** Módulo especializado que permite el cálculo de cuotas e intereses mediante estrategias fijas o variables, utilizando el patrón **Strategy** para adaptarse a diferentes políticas crediticias.
*   **Auditoría y Monitoreo:** Cada transacción es supervisada por observadores independientes (**Patrón Observer**) que generan logs de auditoría, alertas de saldo y registros de riesgo de forma automática.

---

## Arquitectura y Patrones de Diseño Implementados

El **Sistema Bancario UTS** es una demostración práctica de ingeniería de software avanzada. Se han implementado **14 patrones de diseño GoF** (Gang of Four) para estructurar una aplicación modular, extensible y alineada con los principios **SOLID**.

### Patrones Creacionales
| Patrón | Aplicación en el Proyecto | Beneficio Técnico |
| :--- | :--- | :--- |
| **Singleton** | Implementado en `ConfigBanco`, `Logger` y `DetectorFraude` usando *Double-Checked Locking*. | Garantiza una única fuente de verdad y seguridad en entornos multihilo. |
| **Factory Method** | Utilizado para la creación de operaciones bancarias (`Deposito`, `Retiro`, `Transferencia`). | Desacopla la lógica de creación, permitiendo añadir nuevas operaciones sin modificar el núcleo. |
| **Abstract Factory** | Genera familias coherentes de validadores, notificadores y límites específicos por canal. | Asegura que los componentes de cada canal (Web, Móvil, Cajero) sean compatibles entre sí. |
| **Builder** | `CuentaBuilder` ofrece una API fluida para la construcción atómica de cuentas bancarias. | Centraliza validaciones complejas (KYC, asociaciones) antes de la instanciación del objeto. |
| **Prototype** | `CuentaPrototypeRegistry` permite clonar cuentas existentes con configuraciones predefinidas. | Optimiza la creación masiva de productos financieros basados en plantillas o modelos base. |

### Patrones Estructurales
| Patrón | Aplicación en el Proyecto | Beneficio Técnico |
| :--- | :--- | :--- |
| **Bridge** | Separa la jerarquía de `OperacionBancaria` de la jerarquía de `CanalBancario`. | Es el eje del sistema; permite que operaciones y canales evolucionen de forma independiente. |
| **Adapter** | Integra servicios externos (Twilio, SendGrid, Firebase) mediante una interfaz común. | Permite cambiar proveedores de notificación sin alterar el código de la lógica de negocio. |
| **Decorator** | Añade dinámicamente capas de auditoría, registro de tiempo y políticas de reintento. | Cumple con el principio Open/Closed al extender funcionalidad sin modificar clases existentes. |
| **Facade** | `UsuarioFacade` y `OperacionFacade` simplifican el acceso a subsistemas complejos. | Reduce el acoplamiento entre la interfaz de usuario (Main/API) y la lógica interna del banco. |
| **Composite** | Trata de forma uniforme la jerarquía Banco → Sucursal → Cuenta. | Facilita cálculos recursivos de saldos y la visualización de la estructura organizacional. |

### Patrones de Comportamiento
| Patrón | Aplicación en el Proyecto | Beneficio Técnico |
| :--- | :--- | :--- |
| **Observer** | Las cuentas notifican automáticamente a observadores de fraude, saldo y auditoría. | Desacopla las reacciones post-transacción de la lógica de ejecución de la operación. |
| **Strategy** | Define diferentes algoritmos para el cálculo de intereses en préstamos (Fijo vs. Variable). | Permite cambiar la política financiera en tiempo de ejecución según el producto crediticio. |
| **Command** | Encapsula transacciones como objetos ejecutables y reversibles. | Habilita el historial de movimientos y la capacidad de deshacer/rehacer (*Undo/Redo*). |
| **State** | Gestiona el comportamiento de la cuenta según su estado (Activa, Bloqueada, Suspendida). | Elimina condicionales complejos y garantiza que las reglas de negocio se apliquen por estado. |


---

## Análisis de Patrones No Implementados

Aunque el sistema es altamente robusto, se optó por no implementar formalmente ciertos patrones cuya funcionalidad ya es satisfecha por la arquitectura actual o cuya complejidad no se justifica para el alcance del proyecto:

| Patrón | Justificación de Omisión | Alternativa Implementada |
| :--- | :--- | :--- |
| **Flyweight** | El sistema ya aplica la esencia de este patrón mediante los **Producers** (`CanalBancarioProducer`, `CanalFactoryProducer`), que gestionan y reutilizan instancias compartidas de forma eficiente. | **Producers (Flyweight por intención):** Reutilización de objetos compartidos para optimizar el uso de memoria. |
| **Proxy** | Las responsabilidades de un Proxy (control de acceso, validación y auditoría) se encuentran distribuidas estratégicamente entre otros componentes más potentes. | **Bridge + Decorator:** El Bridge valida el acceso por canal y el Decorator gestiona la auditoría y seguridad. |
| **Chain of Responsibility** | El flujo de validación y aprobación es directo y centralizado en el Bridge, por lo que una cadena de responsabilidad añadiría una complejidad innecesaria al flujo de transacciones. | **Validación Centralizada:** El motor de fraude y los validadores de canal procesan las reglas de forma secuencial y atómica. |
| **Memento** | La capacidad de restaurar estados previos se ha delegado al patrón **Command**, el cual es más adecuado para sistemas transaccionales que requieren un historial de acciones reversibles. | **Command (Undo/Redo):** Mantiene el historial de operaciones permitiendo revertir cambios sin necesidad de guardar capturas de estado completas. |


---

## Resumen de Archivos y Responsabilidades

La arquitectura del **Sistema Bancario UTS** se organiza en componentes especializados, cada uno con una responsabilidad clara y fundamentada en patrones de diseño.

| Archivo(s) | Patrón(es) Asociado(s) | Rol Principal en el Sistema |
| :--- | :--- | :--- |
| `config_banco.py`, `logger.py` | **Singleton** | Centralizan la configuración global y el registro de eventos con seguridad multihilo. |
| `operacion.py`, `operacion_factory.py` | **Factory Method** | Definen y fabrican las operaciones base (`Deposito`, `Retiro`, `Transferencia`). |
| `canal_bridge.py`, `operacion_bridge.py` | **Bridge** | Orquestan el flujo principal desacoplando la operación del canal (Web, Móvil, Cajero). |
| `cuenta_builder.py` | **Builder + Prototype** | Construyen cuentas de forma atómica y gestionan la clonación de plantillas. |
| `notificador_adapter.py` | **Adapter** | Conectan el sistema con servicios externos de SMS, Email y Voucher. |
| `operacion_decorator.py` | **Decorator** | Inyectan comportamientos de auditoría y reintentos en tiempo de ejecución. |
| `usuario_facade.py`, `operacion_facade.py` | **Facade** | Simplifican la interacción con el sistema, ocultando la complejidad del núcleo. |
| `componente_bancario.py`, `banco.py` | **Composite** | Gestionan la estructura jerárquica para cálculos de saldo y reportes uniformes. |
| `observer_cuenta.py` | **Observer** | Reaccionan a movimientos para detectar fraude y alertar sobre saldos críticos. |
| `prestamo_strategy.py` | **Strategy** | Calculan intereses de préstamos mediante algoritmos fijos o variables. |
| `command_transaccion.py` | **Command** | Encapsulan acciones reversibles para permitir el historial y el Undo/Redo. |
| `estado_cuenta.py` | **State** | Gobiernan las reglas de negocio según la condición (Activa, Bloqueada) de la cuenta. |
| `api.py` | **REST API** | Exponen las funcionalidades del core bancario mediante una interfaz HTTP moderna. |
| `seed.py`, `seed_prestamos.py` | **Data Seed** | Precargan el sistema con usuarios y transacciones para demostraciones y pruebas. |

### Organización del Código
El proyecto sigue una estructura donde la **Lógica de Dominio** (`cuenta.py`, `banco.py`) es agnóstica a la interfaz, mientras que las **Fachadas** y los **Producers** actúan como pegamento arquitectónico para mantener el sistema bajo el principio de **Bajo Acoplamiento y Alta Cohesión**.


---

## Conclusiones y Aprendizajes Arquitectónicos

El **Sistema Bancario UTS** trasciende la implementación técnica para convertirse en una demostración de cómo los patrones de diseño son respuestas precisas a desafíos reales de la ingeniería de software. La aplicación estratégica de los **14 patrones de diseño** no fue una elección arbitraria, sino una necesidad arquitectónica para resolver problemas de acoplamiento, extensibilidad y seguridad que emergen en sistemas financieros críticos.

A través de este desarrollo, se han consolidado aprendizajes fundamentales:

*   **Sinergia de Patrones:** Se ha demostrado que los patrones no operan de forma aislada. La integración del **Builder** con el **Prototype** y el **Observer** permite que la creación de cuentas sea un proceso atómico, seguro y reactivo desde su origen, garantizando que el sistema sea robusto por diseño.
*   **Respeto a los Principios SOLID:** La arquitectura basada en el **Bridge** y el **Decorator** permite cumplir rigurosamente con el principio de *Abierto/Cerrado* (OCP), facilitando la adición de nuevos canales y comportamientos transversales sin alterar la lógica de negocio ya probada.
*   **Precisión y Cumplimiento:** La transición hacia tipos de datos de alta precisión (**Decimal**) y la centralización de políticas de cumplimiento (**AML/KYC**) mediante **Singletons** y **Fachadas** eleva el proyecto de una simulación académica a una plataforma con estándares de nivel profesional.

En conclusión, este proyecto evidencia que una arquitectura bien cimentada no es un paso previo al desarrollo, sino su columna vertebral. Cuando los patrones se integran con coherencia, el software deja de ser una colección de archivos y se convierte en un ecosistema escalable donde **extender la funcionalidad es una consecuencia natural de su estructura, no un riesgo operativo**. Los cimientos están puestos; el futuro del sistema es el crecimiento continuo.


---

classDiagram
    direction TB

    %% ==================== SINGLETONS ====================
    class ConfigBanco { <<Singleton>> +get_instancia() }
    class Logger { <<Singleton>> +log() }
    class DetectorFraude { <<Singleton>> +evaluar() }

    %% ==================== CREACIONALES ====================
    class CuentaBuilder { +build() +clone_desde() }
    class Cuenta { +depositar() +retirar() +clone() }
    class OperacionFactory { <<Abstract>> +crear_operacion() }

    %% ==================== ESTRUCTURALES ====================
    class OperacionBancaria { <<Abstract>> -_canal: CanalBancario +ejecutar() }
    class CanalBancario { <<Interface>> +validar() +notificar() }
    class OperacionDecorator { <<Abstract>> -_operacion: Operacion }
    class ComponenteBancario { <<Interface>> +get_saldo_total() }
    class NotificadorAdapterProducer { +get_adapter() }

    %% ==================== COMPORTAMIENTO (NUEVOS) ====================
    class ObservadorCuenta { <<Interface>> +update() }
    class ObservadorFraude
    class ObservadorSaldoCritico
    class EstrategiaInteres { <<Interface>> +calcular() }
    class Prestamo { -_estrategia: EstrategiaInteres }
    class ComandoBancario { <<Interface>> +ejecutar() +deshacer() }
    class EstadoCuenta { <<Interface>> +depositar() +retirar() }

    %% ==================== RELACIONES Y PATRONES ====================
    
    %% Bridge
    OperacionBancaria "1" o-- "1" CanalBancario : "Bridge"
    
    %% Observer
    Cuenta "1" o-- "0..*" ObservadorCuenta : "Sujeto Observer"
    ObservadorCuenta <|-- ObservadorFraude
    ObservadorCuenta <|-- ObservadorSaldoCritico
    
    %% Strategy
    Prestamo "1" o-- "1" EstrategiaInteres : "Strategy"
    
    %% State
    Cuenta "1" o-- "1" EstadoCuenta : "State"
    
    %% Composite
    ComponenteBancario <|-- Banco
    ComponenteBancario <|-- Sucursal
    ComponenteBancario <|-- Cuenta
    
    %% Decorator
    OperacionDecorator o-- "decora" OperacionBancaria : "Decorator"
    
    %% Builder & Prototype
    CuentaBuilder ..> Cuenta : "construye / clona"
    
    %% Command
    ComandoBancario <.. HistorialComandos : "invoker"

    %% Notas de Arquitectura
    note for OperacionBancaria "Bridge: Eje central del sistema"
    note for Cuenta "Sujeto de Observer y Contexto de State"
    note for ComandoBancario "Permite Undo/Redo de transacciones"


---

<img width="8192" height="1964" alt="Diagrama" src="https://github.com/user-attachments/assets/f34071e5-3c97-4c88-8572-1effe11c0001" />


---
  -----------------------------
# Documentacion de las implementaciones semana a semana 

https://github.com/Andres023-0/SistemaBancario/blob/main/Documentacion_Implementacion.docx

