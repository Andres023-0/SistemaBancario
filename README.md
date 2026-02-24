# Patrones - Sistema Bancario Core

# CREADO POR:
BRAYAN ANDRES CAÑAS LEON / JUAN SEBASTIAN NIÑO FORERO


-------------------------------
# Simulacion de un Sistema Bancario:


# **Objetivo principal**  
Este proyecto académico simula componentes clave de un entorno bancario moderno, con enfoque especial en procesos de **cumplimiento regulatorio** (KYC y AML) en tiempo real, demostrando la aplicación práctica de **principios SOLID** y **patrones de diseño** para construir software de calidad en un contexto financiero regulado, eliminando code smells comunes y logrando un diseño modular, mantenible y extensible.

### módulos representativos del sector financiero:

- Gestión de cuentas múltiples  
- Transacciones por múltiples canales (web, móvil, cajeros, sucursales)  
- Detección de fraude en tiempo real  
- Cumplimiento regulatorio en tiempo real:  
  - **KYC** (Know Your Customer) – Onboarding y validación de clientes  
  - **AML** (Anti-Money Laundering) – Monitoreo y detección de operaciones sospechosas  

# Enfoque de Calidad de Software con implementacion de principios SOLID aplicados

## Patrones de diseño implementados

- **Patron Singleton** → Apoyados en la recomendacion (Parámetros regulatorios, tasas de interés, límites KYC/AML, URLs de APIs, timeouts)
- **Factory Method / Abstract Factory** → Creación controlada de entidades (Cliente, Cuenta, Transacción)  


# Diagrama UML - Patrón Singleton en Sistema Bancario

Este diagrama modela específicamente el patrón Singleton aplicado al módulo de detección de fraude, mostrando cómo se garantiza una única configuración regulatoria global (KYC/AML) y logging centralizado en un entorno bancario concurrente. 

### Se utilizo mermaid con direction TB para el grafico en uml

-----------------------
classDiagram
    direction TB
    
    %% ENTIDADES PRINCIPALES DEL BANCO
    class Banco {
        +nombre : String
        +nit : String
        +cuentas : List~Cuenta~
        +clientes : List~Cliente~
    }
    
    class Cliente {
        <<abstract>>
        +id : Long
        +nombre : String
        +identificacion : String
        +direccion : String
    }
    
    class PersonaNatural {
        +tipoDocumento : String
        +numeroDocumento : String
    }
    
    class PersonaJuridica {
        +nit : String
        +representanteLegal : String
    }
    
    class Cuenta {
        <<abstract>>
        +numeroCuenta : String
        +saldo : BigDecimal
        +cliente : Cliente
        +transacciones : List~Transaccion~
    }
    
    class CuentaCorriente {
        +sobregiroPermitido : BigDecimal
    }
    
    class CuentaAhorro {
        +tasaInteres : BigDecimal
    }
    
    %% MÓDULO FRAUDE (tu diagrama Singleton integrado)
    class DetectorFraudeService {
        +evaluarTransaccion(tx : Transaccion) : Riesgo
    }
    
    class ConfiguracionBancaria {
        <<enum>>
        +INSTANCE : ConfiguracionBancaria
        -tasasInteres : Map~String, BigDecimal~
        -paisesKYCAltaRiesgo : Set~String~
        +esPaisAltaRiesgo(pais : String) boolean
        +getTasaInteres(tipo : String) BigDecimal
    }
    
    class LoggerBancario {
        <<enum>>
        +INSTANCE : LoggerBancario
    }
    
    class Transaccion {
        +id : Long
        +monto : BigDecimal
        +paisOrigen : String
        +tipo : TipoTransaccion
        +cuentaOrigen : Cuenta
        +cuentaDestino : Cuenta
    }
    
    %% RELACIONES GLOBALES
    Banco ||--o{ Cliente : "gestiona"
    Banco ||--o{ Cuenta : "ofrece"
    Cliente ||--o{ Cuenta : "posee"
    Cuenta ||--o{ Transaccion : "genera"
    
    Cliente <|-- PersonaNatural
    Cliente <|-- PersonaJuridica
    Cuenta <|-- CuentaCorriente
    Cuenta <|-- CuentaAhorro
    
    %% INTEGRACIÓN MÓDULO FRAUDE
    DetectorFraudeService --> ConfiguracionBancaria : "usa INSTANCE"
    DetectorFraudeService --> Transaccion : "evalua"
    DetectorFraudeService --> LoggerBancario : "audita"


------------------------------

