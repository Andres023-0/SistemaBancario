# Patrones - Sistema Bancario Core

#CREADO POR:
BRAYAN ANDRES CAÑAS LEON / JUAN SEBASTIAN NIÑO FORERO

Este proyecto académico simula componentes clave de un entorno bancario moderno, con enfoque especial en procesos de **cumplimiento regulatorio** (KYC y AML) en tiempo real.

**Objetivo principal**  
Demostrar la aplicación práctica de **principios SOLID** y **patrones de diseño** para construir software de calidad en un contexto financiero regulado, eliminando code smells comunes y logrando un diseño modular, mantenible y extensible.

## Simulacion de un sistema bancario core con módulos representativos del sector financiero:

- Gestión de cuentas múltiples  
- Transacciones por múltiples canales (web, móvil, cajeros, sucursales)  
- Detección de fraude en tiempo real  
- Cumplimiento regulatorio en tiempo real:  
  - **KYC** (Know Your Customer) – Onboarding y validación de clientes  
  - **AML** (Anti-Money Laundering) – Monitoreo y detección de operaciones sospechosas  

## Enfoque de Calidad de Software con implementacion de principios SOLID aplicados

### Patrones de diseño implementados

- **Patron Singleton** → Apoyados en la recomendacion (Parámetros regulatorios, tasas de interés, límites KYC/AML, URLs de APIs, timeouts)
- **Factory Method / Abstract Factory** → Creación controlada de entidades (Cliente, Cuenta, Transacción)  


### Diagrama UML - Patrón Singleton en Sistema Bancario

#Este diagrama modela específicamente el patrón Singleton aplicado al módulo de detección de fraude, mostrando cómo se garantiza una única configuración regulatoria global (KYC/AML) y logging centralizado en un entorno bancario concurrente. 
# Se utilizo mermaid con direction TB para el grafico en uml

-----------------------
classDiagram
     direction TB

    class ConfiguracionBancaria {
        <<enum>>
        +INSTANCE : ConfiguracionBancaria
        -propiedades : Properties
        -tasasInteres : Map~String, BigDecimal~
        -paisesKYCAltaRiesgo : Set~String~
        -ConfiguracionBancaria()
        +getPropiedad(clave : String) String
        +getTasaInteres(tipoProducto : String) BigDecimal
        +esPaisAltaRiesgo(pais : String) boolean
        +cargarConfiguracion()
        +cargarTasasYReglasRegulatorias()
    }

    class DetectorFraudeService {
        +evaluarTransaccion(tx : Transaccion)
    }

    class Transaccion {
        +id : Long
        +monto : BigDecimal
        +paisOrigen : String
        +tipoProducto : String
        +getPaisOrigen() String
        +getTipoProducto() String
    }

    class LoggerBancario {
        <<enum>>
        +INSTANCE : LoggerBancario
        -log( mensaje : String, nivel : String )
    }

    DetectorFraudeService --> ConfiguracionBancaria : "usa ConfiguracionBancaria.INSTANCE"
    DetectorFraudeService --> Transaccion : "procesa"
    DetectorFraudeService --> LoggerBancario : "usa LoggerBancario.INSTANCE"

------------------------------

