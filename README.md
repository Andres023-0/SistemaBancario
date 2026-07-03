# Patrones - Sistema Bancario Core

**Desarrollado por:**  

- Brayan Andrés Cañas León

- Juan Sebastián Niño Forero

Docente: Eliecer Montero Ojeda

Institución:

- Unidades Tecnológicas de Santander (UTS)

---

## Sistema Bancario UTS: Una Plataforma Financiera Robusta y Extensible
El Sistema Bancario UTS es una plataforma de gestión financiera integral, meticulosamente diseñada para proporcionar una experiencia de usuario completa, confiable y segura en la administración de operaciones bancarias cotidianas. Este sistema permite a los usuarios registrarse, gestionar sus cuentas, y ejecutar transacciones fundamentales como depósitos, retiros y transferencias con agilidad, todo ello en un entorno que prioriza la claridad, trazabilidad y seguridad de cada movimiento financiero.
La arquitectura del Sistema Bancario UTS se distingue por su diseño modular y la aplicación estratégica de 17 patrones de diseño de software (GoF), incluyendo Singleton, Factory Method, Abstract Factory, Builder, Adapter, Prototype, Bridge, Decorator, Facade, Composite, Observer, Strategy, Command, State, Memento, Chain of Responsibility y Template Method. Esta implementación avanzada garantiza que cada operación se ejecute de manera independiente y ordenada, resultando en un servicio estable, consistente y altamente adaptable a las demandas cambiantes del negocio. La modularidad y el desacoplamiento inherentes a estos patrones facilitan la extensibilidad, permitiendo la integración fluida de nuevas funcionalidades y la evolución del sistema sin comprometer su integridad.
Más allá de sus funcionalidades actuales, el Sistema Bancario UTS está cimentado sobre principios de diseño que anticipan futuras expansiones. Su estructura robusta soporta la incorporación de capacidades avanzadas, tales como la integración con diversas plataformas digitales, la generación de reportes financieros sofisticados y una persistencia de datos resiliente. Esta plataforma no solo satisface las necesidades presentes, sino que está preparada para escalar y evolucionar, asegurando su relevancia y eficiencia a largo plazo en el dinámico panorama financiero.

## Objetivos del Proyecto

El objetivo primordial del Sistema Bancario UTS es centralizar y automatizar la gestión financiera de cuentas a gran escala mediante una arquitectura de software avanzada. El sistema garantiza la verificación rigurosa de la identidad de los usuarios, el control preciso de las operaciones y la trazabilidad absoluta de cada movimiento, proporcionando así un entorno bancario académico altamente confiable, seguro y eficiente, sustentado en la implementación coordinada de 17 patrones de diseño GoF y principios SOLID.

## Objetivos Específicos

Para alcanzar la visión del proyecto, se han definido y ejecutado los siguientes siete objetivos específicos que cubren operatividad, seguridad, auditoría y escalabilidad:
| # | Objetivo |
|---|----------|
| 1 | Validar la identidad de cada usuario mediante un módulo de verificación KYC antes de permitir el registro, la apertura de cuentas y la realización de cualquier operación financiera, garantizando el cumplimiento de estándares básicos de seguridad e integridad desde el primer acceso al sistema. |
| 2 | Proveer consultas de saldo en tiempo real a nivel de cuenta individual, sucursal y banco completo, reflejando de forma inmediata cada depósito, retiro o transferencia ejecutada dentro del sistema, de modo que el docente pueda observar el estado financiero actualizado en cualquier nivel de la jerarquía organizacional. |
| 3 | Ofrecer un historial detallado, ordenado cronológicamente y auditable de todos los movimientos realizados por cada cuenta, permitiendo al docente rastrear el origen, destino, monto y estado de cada transacción registrada en el sistema. |
| 4 | Administrar de forma simultánea múltiples cuentas bajo un alto volumen de operaciones concurrentes, asegurando que la ejecución paralela de transacciones no comprometa la consistencia de los saldos ni la integridad de los datos almacenados en el sistema. |
| 5 | Detectar y bloquear automáticamente transacciones sospechosas mediante la evaluación de cinco reglas de riesgo: montos superiores al límite AML de $10,000, frecuencia anómala de operaciones, saldos en estado crítico, uso de canales inusuales e historial negativo del destino, generando alertas en tiempo real ante cualquier anomalía. |
| 6 | Calcular y aplicar sobre los préstamos otorgados tanto tasas de interés fijas como variables, brindando al usuario la posibilidad de seleccionar la modalidad que mejor se ajuste a su perfil financiero y visualizando el impacto de cada estrategia sobre el valor total del crédito. |
| 7 | Someter cada transacción a una secuencia de cinco validaciones previas a su ejecución —estado de la cuenta, disponibilidad de saldo, límites del canal utilizado, frecuencia de operaciones y verificación de la cuenta destino— rechazando automáticamente cualquier movimiento que no supere todos los criterios establecidos. |
| 8 | Registrar automáticamente cada cambio de estado de una cuenta bancaria y permitir su restauración a cualquier punto previo de su historial, brindando al sistema la capacidad de revertir errores operativos sin pérdida de información ni afectación a otros registros. |
| 9 | Generar cuatro tipos de reportes bancarios estructurados —de movimientos, préstamos, sucursal y usuario— bajo un esquema de proceso unificado que garantice coherencia en la presentación de la información y facilite la supervisión y toma de decisiones por parte del docente. |
| 10 | Notificar a los usuarios en tiempo real sobre el resultado de cada operación ejecutada —depósitos, retiros, transferencias y cambios de estado— a través de los canales disponibles (web, móvil y cajero), asegurando que cada acción financiera quede debidamente comunicada y registrada en el sistema. |
## Ingeniería y Arquitectura de Software

Los siguientes objetivos técnicos garantizan que la arquitectura sea robusta, extensible y alineada con principios SOLID:

1. Desacoplamiento Estructural: Implementar el patrón Bridge para separar las operaciones bancarias de los canales de acceso, permitiendo una evolución independiente de ambos componentes. Este patrón es el eje central del sistema, facilitando la adición de nuevos canales o operaciones sin modificar código existente.

2. Precisión Financiera: Asegurar la integridad de todos los cálculos monetarios mediante el uso de tipos de datos Decimal con redondeo ROUND_HALF_UP, eliminando errores de redondeo en transacciones críticas. Esto garantiza exactitud a dos decimales en todas las operaciones financieras.

3. Control de Ciclo de Vida: Administrar las restricciones de las cuentas mediante el patrón State, garantizando que solo se realicen operaciones permitidas según el estado actual (Activa, Bloqueada, Suspendida, Cerrada). Elimina condicionales complejos y asegura que las reglas de negocio se apliquen consistentemente.

4. Seguridad Proactiva: Integrar un motor de detección de fraude basado en el patrón Singleton para evaluar riesgos y comportamientos inusuales en tiempo real. Utiliza Double-Checked Locking para garantizar seguridad en entornos multihilo y una única fuente de verdad para políticas de fraude.

5. Extensibilidad Transversal: Aplicar el patrón Decorator para añadir dinámicamente capacidades de auditoría, medición de tiempo de ejecución y reintentos sin modificar el código base de las operaciones. Cumple con el principio Open/Closed al extender funcionalidad sin modificar clases existentes.

6. Integridad en la Construcción: Estandarizar la creación de cuentas mediante el patrón Builder, asegurando que cumplan con todas las reglas de negocio (KYC, usuario, sucursal) antes de su activación. Centraliza validaciones complejas en una sola clase especializada, fortaleciendo el principio Single Responsibility.

7. Integración Multicanal: Desarrollar un sistema de notificaciones desacoplado utilizando el patrón Adapter para facilitar la conexión con diversos proveedores externos (Email, SMS, Voucher). Permite cambiar proveedores sin alterar la lógica de negocio, cumpliendo con el principio Open/Closed.

8. Resiliencia Operativa: Establecer mecanismos de recuperación y seguimiento histórico mediante el patrón Command, encapsulando transacciones como objetos ejecutables y reversibles. Habilita el historial de movimientos, auditoría completa y la capacidad de deshacer/rehacer operaciones sin pérdida de integridad.

## Módulos Clave y Funcionalidades Financieras
El Sistema Bancario UTS integra funcionalidades críticas que reflejan operaciones reales del sector financiero, con un enfoque riguroso en la precisión, la seguridad y el cumplimiento normativo. A continuación, se detallan las capacidades centrales del sistema:
Aquí el análisis: el texto dice **14 patrones** en "Implementación de Patrones de Diseño" (objetivo 6 de la tabla original) y la tabla de módulos no menciona los 3 patrones nuevos (Memento, Chain of Responsibility, Template Method). Los cambios necesarios son mínimos:

1. En el objetivo 6 de la tabla anterior: "catorce" → "diecisiete"
2. En la tabla de módulos: agregar tres filas nuevas para los patrones faltantes

---

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
| **Reversibilidad de Estados** | Cada cambio de estado de una cuenta genera automáticamente un snapshot previo, permitiendo restaurar cualquier punto del historial sin pérdida de información. | **Patrón Memento:** Preserva instantáneas del estado interno de la cuenta. |
| **Validación Encadenada** | Las transacciones atraviesan cinco validaciones secuenciales y trazables antes de ejecutarse, con reporte detallado del eslabón que rechazó la operación. | **Patrón Chain of Responsibility:** Centraliza y ordena las reglas de validación. |
| **Reportes Estructurados** | Generación de cuatro tipos de reportes bancarios (movimientos, préstamos, sucursal y usuario) bajo un flujo de proceso unificado y coherente. | **Patrón Template Method:** Define un esquema fijo de seis pasos reutilizable por cada tipo de reporte. |

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

La arquitectura del Sistema Bancario UTS se organiza en componentes especializados, cada uno con una responsabilidad clara y fundamentada en patrones de diseño.
## Resumen de Archivos y Responsabilidades

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
| `memento_cuenta.py` | **Memento** | Preservan snapshots del estado de cada cuenta para permitir su restauración histórica. |
| `validacion_chain.py` | **Chain of Responsibility** | Encadenan cinco validaciones secuenciales y trazables antes de ejecutar una transacción. |
| `reporte_template.py` | **Template Method** | Definen el flujo fijo de generación de reportes reutilizable por los cuatro tipos disponibles. |
| `api.py` | **REST API** | Exponen las funcionalidades del core bancario mediante una interfaz HTTP moderna. |
| `seed.py`, `seed_prestamos.py` | **Data Seed** | Precargan el sistema con usuarios y transacciones para demostraciones y pruebas. |

### Organización del Código
El proyecto sigue una estructura donde la **Lógica de Dominio** (`cuenta.py`, `banco.py`) es agnóstica a la interfaz, mientras que las **Fachadas** y los **Producers** actúan como pegamento arquitectónico para mantener el sistema bajo el principio de **Bajo Acoplamiento y Alta Cohesión**.

---

## Conclusiones y Aprendizajes Arquitectónicos

El Sistema Bancario UTS trasciende la implementación técnica para convertirse en una demostración de cómo los patrones de diseño son respuestas precisas a desafíos reales de la ingeniería de software. La aplicación estratégica de los 17 patrones de diseño no fue una elección arbitraria, sino una necesidad arquitectónica para resolver problemas de acoplamiento, extensibilidad y seguridad que emergen en sistemas financieros críticos.
A través de este desarrollo, se han consolidado aprendizajes fundamentales:

Sinergia de Patrones: Se ha demostrado que los patrones no operan de forma aislada. La integración del Builder con el Prototype y el Observer permite que la creación de cuentas sea un proceso atómico, seguro y reactivo desde su origen, garantizando que el sistema sea robusto por diseño.
Respeto a los Principios SOLID: La arquitectura basada en el Bridge y el Decorator permite cumplir rigurosamente con el principio de Abierto/Cerrado (OCP), facilitando la adición de nuevos canales y comportamientos transversales sin alterar la lógica de negocio ya probada.
Precisión y Cumplimiento: La transición hacia tipos de datos de alta precisión (Decimal) y la centralización de políticas de cumplimiento (AML/KYC) mediante Singletons y Fachadas eleva el proyecto de una simulación académica a una plataforma con estándares de nivel profesional.
Trazabilidad y Reversibilidad: La incorporación del Memento y el Chain of Responsibility eleva la confiabilidad operativa del sistema: cada cambio de estado queda preservado y es restaurable, mientras que cada transacción atraviesa una cadena de validaciones ordenada, trazable y ampliable sin modificar código existente.
Estandarización de Procesos: El Template Method demuestra que la coherencia estructural no riñe con la flexibilidad. Definir un flujo fijo de seis pasos para la generación de reportes garantiza que cualquier nuevo tipo de reporte herede automáticamente las garantías del proceso sin duplicar lógica.

En conclusión, este proyecto evidencia que una arquitectura bien cimentada no es un paso previo al desarrollo, sino su columna vertebral. Cuando los patrones se integran con coherencia, el software deja de ser una colección de archivos y se convierte en un ecosistema escalable donde extender la funcionalidad es una consecuencia natural de su estructura, no un riesgo operativo. Los cimientos están puestos; el futuro del sistema es el crecimiento continuo.

---

classDiagram
    direction TB

    class Logger { <<Singleton>> +log() }
    class ConfigBanco { <<Singleton>> +get_instancia() }
    class DetectorFraude { <<Singleton>> +evaluar() }
    class SucursalesManager { <<Singleton>> +get_instancia() }
    class GestorMementos { <<Singleton>> +guardar_estado() +restaurar() }

    class CuentaBuilder { +build() +clone_desde() }
    class CuentaPrototypeRegistry { +registrar() +get() +clonar() }
    class OperacionFactory { <<Abstract>> +crear_operacion() }
    class AbstractCanalFactory { <<Abstract>> +crear_validador() +crear_limite() }

    class OperacionBancaria { <<Abstract>> -_canal: CanalBancario +ejecutar() }
    class CanalBancario { <<Interface>> +validar() +notificar() +get_limite() }
    class NotificadorAdapter { <<Interface>> +notificar() }
    class OperacionDecorator { <<Abstract>> -_operacion: Operacion +ejecutar() }
    class ComponenteBancario { <<Interface>> +get_saldo_total() +listar() }
    class OperacionFacade { +depositar() +retirar() +transferir() +generar_reporte() }
    class UsuarioFacade { +registrar_usuario() +crear_cuenta() }

    class Cuenta { +depositar() +retirar() +transferir() +clone() +set_estado() +crear_snapshot() }
    class Banco { +agregar_usuario() +buscar_cuenta() }
    class Sucursal { +agregar_cuenta() +get_saldo_total() }

    class ObservadorCuenta { <<Interface>> +update() }
    class ObservadorFraude
    class ObservadorSaldoCritico
    class ObservadorLogMovimiento
    class EstadoCuenta { <<Interface>> +puede_depositar() +puede_retirar() }
    class EstadoActiva
    class EstadoBloqueada
    class EstadoSuspendida
    class EstadoCerrada
    class ComandoBancario { <<Interface>> +ejecutar() +deshacer() }
    class ComandoDeposito
    class ComandoRetiro
    class ComandoTransferencia
    class HistorialComandos { <<Invoker>> +ejecutar() +deshacer() +reejecutar() }
    class EstrategiaInteres { <<Interface>> +calcular_cuota() +calcular_total_intereses() }
    class InteresEstrategiaFijo
    class InteresEstrategiaVariable
    class Prestamo { -_estrategia: EstrategiaInteres +registrar_pago() }

    class MementoEstadoCuenta { +get_estado() +get_fecha() +get_motivo() }
    class ValidacionHandler { <<Abstract>> +manejar() +set_siguiente() }
    class ValidadorEstado
    class ValidadorSaldo
    class ValidadorLimiteCanal
    class ValidadorFrecuencia
    class ValidadorDestino
    class CadenaValidacionFactory { +crear_cadena() }
    class GeneradorReporte { <<Abstract>> +generar() +recopilar() +filtrar() +calcular() +formatear() +finalizar() }
    class ReporteMovimientos
    class ReportePrestamos
    class ReporteSucursal
    class ReporteUsuario

    ConfigBanco ..> DetectorFraude : configura
    ConfigBanco ..> SucursalesManager : configura
    Logger <.. Cuenta : usa
    Logger <.. OperacionBancaria : usa

    OperacionBancaria "1" o-- "1" CanalBancario : Bridge
    OperacionBancaria <|-- Deposito
    OperacionBancaria <|-- Retiro
    OperacionBancaria <|-- Transferencia

    AbstractCanalFactory ..> CanalBancario : produce

    OperacionFactory ..> Deposito : crea
    OperacionFactory ..> Retiro : crea
    OperacionFactory ..> Transferencia : crea

    CuentaBuilder ..> Cuenta : construye
    CuentaBuilder ..> CuentaPrototypeRegistry : consulta
    CuentaPrototypeRegistry ..> Cuenta : clona

    NotificadorAdapter <|-- SMSAdapter
    NotificadorAdapter <|-- EmailAdapter
    NotificadorAdapter <|-- VoucherAdapter
    CanalBancario ..> NotificadorAdapter : delega notificacion

    OperacionDecorator o-- OperacionFactory : decora
    OperacionDecorator <|-- LogTiempoDecorator
    OperacionDecorator <|-- AuditoriaDecorator
    OperacionDecorator <|-- ReintentoDecorator

    ComponenteBancario <|-- Banco
    ComponenteBancario <|-- Sucursal
    ComponenteBancario <|-- Cuenta
    Banco o-- Sucursal : contiene
    Sucursal o-- Cuenta : contiene

    OperacionFacade ..> OperacionBancaria : orquesta
    UsuarioFacade ..> CuentaBuilder : usa
    OperacionFacade ..> Cuenta : busca

    Cuenta "1" o-- "0..*" ObservadorCuenta : notifica
    ObservadorCuenta <|-- ObservadorFraude
    ObservadorCuenta <|-- ObservadorSaldoCritico
    ObservadorCuenta <|-- ObservadorLogMovimiento
    ObservadorFraude ..> DetectorFraude : delega

    Cuenta "1" o-- "1" EstadoCuenta : delega
    EstadoCuenta <|-- EstadoActiva
    EstadoCuenta <|-- EstadoBloqueada
    EstadoCuenta <|-- EstadoSuspendida
    EstadoCuenta <|-- EstadoCerrada

    ComandoBancario <|-- ComandoDeposito
    ComandoBancario <|-- ComandoRetiro
    ComandoBancario <|-- ComandoTransferencia
    HistorialComandos o-- ComandoBancario : gestiona pila
    ComandoDeposito ..> Cuenta : receiver
    ComandoRetiro ..> Cuenta : receiver
    ComandoTransferencia ..> Cuenta : receiver

    Prestamo "1" o-- "1" EstrategiaInteres : delega calculo
    EstrategiaInteres <|-- InteresEstrategiaFijo
    EstrategiaInteres <|-- InteresEstrategiaVariable

    Cuenta ..> MementoEstadoCuenta : crea snapshot
    Cuenta ..> GestorMementos : delega snapshot
    GestorMementos o-- MementoEstadoCuenta : almacena pila

    OperacionFacade ..> CadenaValidacionFactory : valida antes de operar
    CadenaValidacionFactory ..> ValidacionHandler : encadena
    ValidacionHandler <|-- ValidadorEstado
    ValidacionHandler <|-- ValidadorSaldo
    ValidacionHandler <|-- ValidadorLimiteCanal
    ValidacionHandler <|-- ValidadorFrecuencia
    ValidacionHandler <|-- ValidadorDestino
    ValidadorEstado ..> Cuenta : consulta estado
    ValidadorSaldo ..> Cuenta : consulta saldo
    ValidadorLimiteCanal ..> CanalBancario : consulta limite
    ValidadorFrecuencia ..> Cuenta : consulta historial

    OperacionFacade ..> GeneradorReporte : genera reporte
    GeneradorReporte ..> Banco : consulta datos
    GeneradorReporte <|-- ReporteMovimientos
    GeneradorReporte <|-- ReportePrestamos
    GeneradorReporte <|-- ReporteSucursal
    GeneradorReporte <|-- ReporteUsuario

    note for OperacionBancaria "Bridge: eje central del sistema"
    note for Cuenta "Observer + State + Composite + Memento"
    note for HistorialComandos "Invoker: pila undo/redo"
    note for GestorMementos "Almacena hasta 10 snapshots por cuenta"
    note for CadenaValidacionFactory "5 eslabones: estado-saldo-canal-frecuencia-destino"
    note for GeneradorReporte "6 pasos: inicializar-recopilar-filtrar-calcular-formatear-finalizar"
    note for OperacionFacade "Punto de entrada: orquesta Chain, Template y Bridge"
    
<img width="8192" height="2250" alt="Diagrama" src="https://github.com/user-attachments/assets/9ca71361-bb5e-4e1b-9b79-a39994e7f6d0" />

---
  -----------------------------
# Documentacion de las implementaciones semana a semana 

https://github.com/Andres023-0/SistemaBancario/blob/main/Documentacion_Implementacion.docx

