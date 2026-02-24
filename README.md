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
--------------------------------------------
    
    +--------------------+       1     +-------------------+       *     +-------------------+
    |      Banco         |-------------|     Sucursal      |-------------|     Cliente       |
    +--------------------+             +-------------------+             +-------------------+
    | -nombre: String    |             | -nombre: String   |             | -id: String       |
    | -direccion: String |             | -direccion: String|             | -nombre: String   |
    +--------------------+             +-------------------+             | -documento: String|
                                        | +abrirCuenta()   |             | -telefono: String |
                                        +-------------------+             +-------------------+
                                                     ↑                               ↑
                                                     |                               |
                                                     |                               |
                                          +------------------+             +-------------------+
                                          |     Cuenta       |             |    Transaccion    |
                                          +------------------+             +-------------------+
                                          | -numero: String  |1..*         | -id: String       |
                                          | -saldo: double   |-------------| -fecha: Date      |
                                          | -tipo: String    |             | -monto: double    |
                                          +------------------+             | -tipo: String     |
                                          | +depositar()     |             |   (dep/reti/transfer)|
                                          | +retirar()       |             +-------------------+
                                          | +consultarSaldo()|             | +registrar()      |
                                          +------------------+             +-------------------+
                                                     ^
                                                     |
                                   +-----------------+-----------------+
                                   |                                   |
                     +---------------------+             +---------------------+
                     |   CuentaAhorros     |             |  CuentaCorriente    |
                     +---------------------+             +---------------------+
                     | -tasaInteres: double|             | -limiteSobregiro: double|
                     | +calcularInteres()  |             | +permitirSobregiro() |
                     +---------------------+             +---------------------+
-----------------------------------------

    direction TB 
    
      class Banco {
      +nombre : string
      +direccion : string
    }
    
    class Sucursal {
      +nombre : string
      +ubicacion : string
    }
    
    class Cliente {
      +nombre : string
      +documento : string
      +telefono : string
    }
    
    class Cuenta {
      +numero : string
      +saldo : double
      +tipo : string
    }
    
    class CuentaAhorros {
      +tasaInteres : double
    }
    
    class CuentaCorriente {
      +sobregiro : double
    }
    
    class Transaccion {
      +fecha : string
      +monto : double
      +tipo : string
      +descripcion : string
    }
    
    class Tarjeta {
      +numero : string
      +fechaVencimiento : string
      +tipo : string
    }
    
    ' Relaciones (estilo hotel: simple y claro)
    Banco "1" *-- "0..*" Sucursal
    Sucursal "1" o-- "0..*" Cuenta
    Cliente "1" *-- "0..*" Cuenta     ' un cliente puede tener varias cuentas
    Cuenta "1" o-- "0..*" Transaccion
    
    Cuenta <|-- CuentaAhorros
    Cuenta <|-- CuentaCorriente
    
    Cliente "1" o-- "0..*" Tarjeta    ' tarjetas asociadas al cliente
    
    ' Métodos mínimos (como en el hotel)
    Cuenta ..> +depositar()
    Cuenta ..> +retirar()
    Cuenta ..> +consultarSaldo()
------------------------------
