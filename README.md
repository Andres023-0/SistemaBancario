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


# Diagrama UML Sistema Bancario

Este diagrama modela específicamente el patrón Singleton aplicado al módulo de detección de fraude, mostrando cómo se garantiza una única configuración regulatoria global (KYC/AML) y logging centralizado en un entorno bancario concurrente. 

### Se utilizo mermaid con direction TB para el grafico en uml
--------------------------------------------
     
    +----------------------+   1      0..*   +----------------------+
    |        Banco         |-----------------|       Sucursal       |
    +----------------------+                 +----------------------+
    | -nombre : String     |                 | -codigo : String     |
    | -nit : String        |                 | -direccion : String  |
    +----------------------+                 +----------------------+
    | +crearSucursal()     |                 | +procesarTransac-    |
    | +registrarCliente()  |                 |   cion()             |
    | +abrirCuenta()       |                 +----------------------+
    +----------------------+
             | 1
             | 0..*
             v
    +----------------------+
    |     <<abstract>>     |
    |        Cliente       |
    +----------------------+
    | -id : Long           |
    | -nombre : String     |
    | -identificacion :    |
    |   String             |
    +----------------------+
             ^
             |
       +-----+-----+
       |           |
    +------------------+  +------------------+
    |  PersonaNatural  |  |  PersonaJuridica |
    +------------------+  +------------------+
    | -tipoDocumento : |  | -nit : String    |
    |   String         |  | -razonSocial :   |
    | -numeroDocumento:|  |   String         |
    |   String         |  +------------------+
    +------------------+
             | 1
             | 0..*
             v
    +----------------------+
    |     <<abstract>>     |
    |        Cuenta        |
    +----------------------+
    | -numeroCuenta :      |
    |   String             |
    | -saldo : BigDecimal  |
    +----------------------+
             ^
             |
       +-----+-----+
       |           |
    +------------------+  +------------------+
    |  CuentaCorriente |  |  CuentaAhorros   |
    +------------------+  +------------------+
    | -sobregiroMaximo:|  | -saldo :         |   
    |   BigDecimal     |  |   BigDecimal     |
    | -tasa de interes:|  | -tasademanejo:   |
    |   BigDecimal     |  |   BigDecimal     |
    +------------------+  +------------------+
    

                            ===== FACTORY METHOD =====
        
                            +----------------------+
                            |   <<abstract>>       |
                            |    CuentaCreator     |
                            +----------------------+
                            | +crearCuenta():Cuenta|
                            | +abrirCuenta()       |
                            +----------------------+
                                      ^
                                      |
                     +----------------+----------------+
                     |                                 |
        +----------------------+          +----------------------+
        |   CreatorAhorros     |          |  CreatorCorriente    |
        +----------------------+          +----------------------+
        | +crearCuenta():      |          | +crearCuenta():      |
        |   CuentaAhorros      |          |   CuentaCorriente    |
        +----------------------+          +----------------------+
-----------------------------------------
      
        classDiagram
        direction TB
        
        %% MÓDULO BANCO Y SUCURSALES
        class Banco {
            -nombre : String
            -nit : String
            +crearSucursal()
            +registrarCliente()
            +abrirCuenta(tipo : String, cliente : Cliente)
        }
        
        class Sucursal {
            -codigo : String
            -direccion : String
            +procesarTransaccion()
            +consultarCajeros()
        }
        
        %% FACTORY METHOD - CREACION CUENTAS
        class CreadorCuentas {
            <<abstract>>
            +crearCuenta(tipo : String) Cuenta
        }
        
        class CreadorCuentasNatural {
            +crearCuenta(tipo : String) Cuenta
        }
        
        class CreadorCuentasJuridica {
            +crearCuenta(tipo : String) Cuenta
        }
        
        %% MÓDULO CLIENTES
        class Cliente {
            <<abstract>>
            +id : Long
            +nombre : String
            +identificacion : String
            +telefono : String
        }
        
        class PersonaNatural {
            +numeroDocumento : String
        }
        
        class PersonaJuridica {
            +nit : String
            +razonSocial : String
        }
        
        %% MÓDULO CUENTAS (PRODUCTOS del Factory)
        class Cuenta {
            <<interface>>
            +numeroCuenta : String
            +saldo : BigDecimal
            +depositar(monto : BigDecimal)
        }
        
        class CuentaCorriente {
            +sobregiroMaximo : BigDecimal
            +tasa de interes: double
        }
        
        class CuentaAhorros {
            +saldo : BigDecimal
            +tasademanejo : BigDecimal
        }
        
        %% TRANSACCIONES
        class Transaccion {
            +id : Long
            +monto : BigDecimal
            +tipo : String
        }
        
        %% RELACIONES COMPLETAS
        Banco ||--o{ Sucursal : "gestiona"
        Banco --> CreadorCuentas : "injeta fábrica"
        
        Cliente <|-- PersonaNatural
        Cliente <|-- PersonaJuridica
        Cliente ||--o{ Cuenta : "posee"
        
        CreadorCuentas <|-- CreadorCuentasNatural
        CreadorCuentas <|-- CreadorCuentasJuridica
        CreadorCuentas ..> Cuenta : "crea"
        
        Cuenta <|-- CuentaCorriente
        Cuenta <|-- CuentaAhorros
        Cuenta ||--o{ Transaccion : "genera"
        
        Sucursal ||--o{ Transaccion : "procesa"
        ---- APLICACION DEL FACTORY METHOD  ----->  crearCuenta() abstracto"
      
      Cuenta ..> +consultarSaldo()
  ------------------------------
# IMPLEMENTACION DE PATRON SINGLETON

### El patrón Singleton nos garantiza que una clase tenga exactamente una instancia y proporciona un punto de acceso global a ella.


[Patron Singleton.docx] 
(https://github.com/Andres023-0/SistemaBancario/blob/45a51572d24fb37dfd65a8c74ac4bad7220f0b98/Patron%20Singleton.docx)

  ------------------------------
  
# IMPLEMENTACION DE PATRON FACTORY METHOD

### En el proyecto "Sistema Bancario Core", el procesamiento de transacciones se realiza en transaccion.py con condicionales para decidir qué hacer según el canal (web, móvil, cajero) y tipo (depósito, retiro, transferencia):

[Patron Factory.docx]
(https://github.com/Andres023-0/SistemaBancario/blob/45a51572d24fb37dfd65a8c74ac4bad7220f0b98/Patron%20Factory.docx)
