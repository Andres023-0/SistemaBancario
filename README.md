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

El diagrama representa la arquitectura del Sistema Bancario Core implementado en Python, mostrando cómo las clases se relacionan entre sí y cómo los patrones de diseño coexisten dentro del mismo sistema.

-----------------------------------------

                SISTEMA BANCARIO CORE — DIAGRAMA UML COMPLETO                        
                       

    ┌─────────────────────┐   1      0..*   ┌─────────────────────┐
    │        Banco        │────────────────▶│      Sucursal        │
    ├─────────────────────┤                 ├─────────────────────┤
    │ -usuarios : List    │                 │ -_nombre : String    │
    │ -sucursales : List  │                 │ -_cuentas : List     │
    ├─────────────────────┤                 ├─────────────────────┤
    │ +agregar_usuario()  │                 │ +agregar_cuenta()    │
    └─────────────────────┘                 └─────────────────────┘
              │ 1
              │ registra
              │ 0..*
              ▼
    ┌─────────────────────┐
    │       Usuario       │
    ├─────────────────────┤
    │ -nombre : String    │
    │ -documento : String │
    │ -verificado_kyc :   │
    │   Boolean           │
    │ -cuentas : List     │
    ├─────────────────────┤
    │ +verificar_kyc()    │
    │ +agregar_cuenta()   │
    └─────────────────────┘
              │ 1
              │ posee
              │ 0..*
               ▼
    ┌─────────────────────┐
    │       Cuenta        │
    ├─────────────────────┤
    │ -numero : String    │
    │ -tipo : String      │
    │   ("corriente" /    │
    │    "ahorros")       │
    │ -_saldo : Decimal   │
    │ -transacciones:List │
    ├─────────────────────┤
    │ +depositar()        │
    │ +retirar()          │
    │ +transferir()       │
    │ -_registrar()       │
    └─────────────────────┘

                  PATRÓN 1: SINGLETON                                                       

    ┌──────────────────────┐     lee      ┌──────────────────────┐
    │   <<Singleton>>      │─────────────▶│   <<Singleton>>      │
    │     ConfigBanco      │              │    DetectorFraude    │
    ├──────────────────────┤              ├──────────────────────┤
    │ -_instancia          │              │ -_instancia          │
    │ -_lock               │              │ -_lock               │
    │ -_limite_aml         │              │ -_limite_aml         │
    │ -_max_transacciones  │              │ -_max_transacciones  │
    │ -_ventana_minutos    │              │ -_ventana_minutos    │
    │ -_saldo_critico      │              │ -_saldo_critico      │
    │ -_sucursales_predet  │              ├──────────────────────┤
    ├──────────────────────┤              │ +get_instancia()     │
    │ +get_instancia()     │              │ +evaluar()           │
    │ +get_limite_aml()    │              └──────────────────────┘
    │ +get_max_transacc()  │                        ▲
    │ +get_ventana_tiemp() │                        │ usa (evalúa fraude)
    │ +get_saldo_critico() │                        │
    │ +get_sucursales()    │              ┌──────────────────────┐
    └──────────────────────┘              │     Transaccion      │
                                          │    (orquestador)     │
    ┌──────────────────────┐              └──────────────────────┘
    │   <<Singleton>>      │                        ▲
    │      Logger          │◀───────────────────────┘
    ├──────────────────────┤         usa (registra logs)
    │ -_instancia          │
    │ -_lock               │
    │ -_logs : List        │
    ├──────────────────────┤
    │ +get_instancia()     │
    │ +log()               │
    │ +get_logs()          │
    └──────────────────────┘

    ┌──────────────────────┐
    │   <<Singleton>>      │
    │  SucursalesManager   │
    ├──────────────────────┤
    │ -_instancia          │
    │ -_lock               │
    │ -_sucursales : List  │
    ├──────────────────────┤
    │ +get_instancia()     │
    │ +agregar_sucursal()  │
    │ +sucursales (prop)   │
    └──────────────────────┘
                PATRÓN 2: FACTORY METHOD                                                  


                 ┌─────────────────────────┐
                 │       <<abstract>>      │
                 │        Operacion        │   ← Producto abstracto
                 ├─────────────────────────┤
                 │ +ejecutar()             │
                 └─────────────────────────┘
                               △
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
    ┌─────────────────┐ ┌───────────────┐ ┌────────────────────┐
    │OperacionDeposito│ │OperacionRetiro│ │OperacionTransfer-  │
    ├─────────────────┤ ├───────────────┤ │   encia            │
    │ +ejecutar()     │ │ +ejecutar()   │ ├────────────────────┤
    └─────────────────┘ └───────────────┘ │ +ejecutar()        │
                                          └────────────────────┘

                   ┌─────────────────────────┐
                   │       <<abstract>>      │
                   │     OperacionFactory    │   ← Creador abstracto
                   ├─────────────────────────┤
                   │ +crear_operacion()      │
                   │   : Operacion           │
                   └─────────────────────────┘
                                △
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
    ┌─────────────────┐ ┌───────────────┐ ┌────────────────────┐
    │ DepositoFactory │ │ RetiroFactory │ │TransferenciaFactory│
    ├─────────────────┤ ├───────────────┤ ├────────────────────┤
    │+crear_operacion │ │+crear_operac- │ │+crear_operacion()  │
    │ ():Operacion-   │ │ ion():Operac- │ │  :OperacionTransf- │
    │  Deposito       │ │  ionRetiro    │ │   erencia          │
    └─────────────────┘ └───────────────┘ └────────────────────┘
              │                 │                  │
              └─────────────────┼──────────────────┘
                                │ instancia y usa
                                ▼
                 ┌─────────────────────────┐
                 │      Transaccion        │
                 │  FACTORIES = {          │
                 │    "deposito":          │
                 │      DepositoFactory(), │
                 │    "retiro":            │
                 │      RetiroFactory(),   │
                 │    "transferencia":     │
                 │      Transf.Factory()   │
                 │  }                      │
                 └─────────────────────────┘

                      PATRÓN 3: ABSTRACT FACTORY                                                

                      ┌──────────────────────────┐
                      │       <<abstract>>       │
                      │   AbstractCanalFactory   │   ← Fábrica abstracta
                      ├──────────────────────────┤
                      │ +crear_validador()       │
                      │ +crear_notificador()     │
                      │ +crear_limite()          │
                      └──────────────────────────┘
                                   △
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │   WebFactory    │  │  MovilFactory   │  │  CajeroFactory  │
    ├─────────────────┤  ├─────────────────┤  ├─────────────────┤
    │+crear_validador │  │+crear_validador │  │+crear_validador │
    │+crear_notific.  │  │+crear_notific.  │  │+crear_notific.  │
    │+crear_limite()  │  │+crear_limite()  │  │+crear_limite()  │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
          │ crea                │ crea               │ crea
          ▼                     ▼                    ▼
    ┌───────────┐         ┌───────────┐        ┌───────────┐
    │Validador  │         │Validador  │        │Validador  │
    │   Web     │         │  Movil    │        │  Cajero   │
    │(máx $50M) │         │(máx  $5M) │        │(máx  $2M) │
    ├───────────┤         ├───────────┤        ├───────────┤
    │Notificador│         │Notificador│        │Notificador│
    │   Web     │         │  Movil    │        │  Cajero   │
    │  (email)  │         │(push+SMS) │        │ (voucher) │
    ├───────────┤         ├───────────┤        ├───────────┤
    │  Limite   │         │  Limite   │        │  Limite   │
    │CanalWeb   │         │CanalMovil │        │CanalCajero│
    └───────────┘         └───────────┘        └───────────┘

                    ┌──────────────────────────┐
                    │   CanalFactoryProducer   │   ← Punto de entrada
                    ├──────────────────────────┤
                    │ _fabricas = {            │
                    │   "web":    WebFactory() │
                    │   "movil":  MovilFactory │
                    │   "cajero": CajeroFact.  │
                    │ }                        │
                    ├──────────────────────────┤
                    │ +get_factory(canal)      │
                    │   : AbstractCanalFactory │
                    └──────────────────────────┘
                                 ▲
                                 │ consulta
                                 │
                    ┌──────────────────────────┐
                    │       Transaccion        │
                    │      (orquestador)       │
                    ├──────────────────────────┤
                    │  Paso 1: AbstractFactory │
                    │    → validador.validar() │
                    │  Paso 2: Singleton       │
                    │    → detector.evaluar()  │
                    │  Paso 3: FactoryMethod   │
                    │    → operacion.ejecutar()│
                    │  Paso 4: AbstractFactory │
                    │    → notificador         │
                    │        .notificar()      │
                    └──────────────────────────┘



            PRODUCTOS ABSTRACTOS (Abstract Factory)


    ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
    │   <<abstract>>   │   │   <<abstract>>   │   │   <<abstract>>   │
    │    Validador     │   │   Notificador    │   │   LimiteCanal    │
    ├──────────────────┤   ├──────────────────┤   ├──────────────────┤
    │ +validar(monto,  │   │ +notificar(tipo, │   │+get_limite_max() │
    │   tipo)          │   │   monto,         │   │+get_limite_min() │
    │   :(bool, str)   │   │   cuenta_numero) │   │+get_nombre_canal │
    └──────────────────┘   └──────────────────┘   └──────────────────┘
            △                      △                      △
            │                      │                      │
      ┌─────┴──────┐         ┌─────┴──────┐        ┌─────┴──────┐
      │ ValidadorW │         │Notificador │        │LimitaCanal │
      │ ValidadorM │         │    Web     │        │    Web     │
      │ ValidadorC │         │Notificador │        │LimiteCanal │
      └────────────┘         │   Movil    │        │   Movil    │
                             │Notificador │        │LimiteCanal │
                             │  Cajero    │        │  Cajero    │
                             └────────────┘        └────────────┘
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
        +gestionarCanales()
    }
    
    class Sucursal {
        -codigo : String
        -direccion : String
        +procesarTransaccion()
        +consultarCajeros()
    }
    
    %% CANALES MÚLTIPLES (NUEVO)
    class CanalAcceso {
        <<abstract>>
        +autenticarUsuario()
        +ejecutarTransaccion()
    }
    
    class AppMovil {
        +pushNotifications()
        +biometria()
    }
    
    class WebBanking {
        +sesionWeb()
        +transferenciasRapidas()
    }
    
    class CajeroAutomatico {
        +leerTarjeta()
        +dispensarEfectivo()
    }
    
    class CallCenter {
        +atencionHumana()
        +verificacionTelefonica()
    }
    
    %% FACTORY METHOD - CORREGIDO
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
    
    %% CLIENTES - CORREGIDO
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
    
    %% CUENTAS - CORREGIDAS
    class Cuenta {
        <<interface>>
        +numeroCuenta : String
        +saldo : BigDecimal
        +depositar(monto : BigDecimal)
        +consultarSaldo()
    }
    
    class CuentaCorriente {
        +sobregiroMaximo : BigDecimal
        +tasaInteres : double
    }
    
    class CuentaAhorros {
        +tasaManejo : BigDecimal
    }
    
    %% TRANSACCIONES
    class Transaccion {
        +id : Long
        +monto : BigDecimal
        +tipo : String
    }
    
    %% RELACIONES COMPLETAS + CANALES
    Banco ||--o{ Sucursal : "gestiona"
    Banco ||--o{ CanalAcceso : "ofrece"
    Banco --> CreadorCuentas : "inyecta"
    
    CanalAcceso <|-- AppMovil
    CanalAcceso <|-- WebBanking
    CanalAcceso <|-- CajeroAutomatico
    CanalAcceso <|-- CallCenter
    
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
    CanalAcceso --> Transaccion : "inicia"
    
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
