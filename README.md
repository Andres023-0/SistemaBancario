# Patrones - Sistema Bancario Core

**CREADO POR:**  
BRAYAN ANDRES CAÑAS LEON / JUAN SEBASTIAN NIÑO FORERO

---

## Simulación de un Sistema Bancario

### Objetivo principal

Este proyecto académico simula componentes clave de un entorno bancario moderno, con enfoque especial en procesos de **cumplimiento regulatorio** (KYC y AML) en tiempo real, demostrando la aplicación práctica de **principios SOLID** y **cuatro patrones de diseño creacionales** (Singleton, Factory Method, Abstract Factory y Builder) para construir software de calidad en un contexto financiero regulado, eliminando code smells comunes y logrando un diseño modular, mantenible y extensible.

---

### Módulos representativos del sector financiero

- **Gestión de cuentas múltiples**  
  Cuentas corriente y ahorros asociadas a usuarios verificados, con historial de transacciones y saldo en `Decimal` para precisión financiera.

- **Transacciones por múltiples canales**  
  Web, móvil y cajero procesan operaciones con reglas propias de límites, notificaciones y restricciones por canal mediante Abstract Factory.

- **Detección de fraude en tiempo real**  
  `DetectorFraude` evalúa 5 reglas antes de aprobar cada transacción: límite AML, alta frecuencia, saldo crítico, canal inusual y cuenta sin historial.

- **KYC**  
  `Usuario` requiere `verificado_kyc = True` antes de abrir cualquier cuenta, bloqueando el onboarding de clientes no validados.

- **AML**  
  `ConfigBanco` centraliza los umbrales: $10.000 por transacción, máximo 5 operaciones en 5 minutos y saldo mínimo de $1.000.

- **Construcción de cuentas con Builder**  
  `CuentaBuilder` garantiza que cada cuenta se construya con todos sus datos válidos (número, tipo, saldo, usuario con KYC verificado y sucursal) antes de persistir, mediante una API fluida encadenada.

---

## Enfoque de Calidad de Software con implementación de principios SOLID

### Patrones de diseño implementados

- **Singleton:**  
  Se centralizó la configuración, logs, detección de fraude y sucursales en instancias únicas thread-safe usando Double-Checked Locking, garantizando consistencia global sin duplicar valores en el sistema.

- **Factory Method:**  
  Se delegó la creación de operaciones bancarias a fábricas concretas por tipo, eliminando condicionales en `Transaccion.procesar()` y permitiendo agregar nuevas operaciones sin modificar código existente.

- **Abstract Factory:**  
  Se creó una fábrica por canal que produce familias coherentes de `Validador`, `Notificador` y `LimiteCanal`, garantizando reglas y comportamientos consistentes para Web, Móvil y Cajero.

- **Builder:**  
  Se implementó un Fluent Builder para la creación de cuentas bancarias, desacoplando el proceso de construcción de su representación final. `CuentaBuilder` encadena los pasos de configuración (número, tipo, saldo, usuario, sucursal) y garantiza en `build()` que todos los datos obligatorios estén presentes antes de instanciar la `Cuenta`, asociarla al `Usuario` y registrarla en la `Sucursal`.

---

## Resumen de archivos del proyecto

```
    Archivo                  Patrón                  Rol
─────────────────────────────────────────────────────────────────────────────
config_banco.py        │  Singleton        │  Configuración global del sistema
logger.py              │  Singleton        │  Registro de eventos
detector_fraude.py     │  Singleton        │  Motor antifraude (5 reglas AML)
sucursales_manager.py  │  Singleton        │  Gestión de sucursales
operacion.py           │  Factory Method   │  Producto abstracto/concreto
operacion_factory.py   │  Factory Method   │  Creador abstracto/concreto
canal_factory.py       │  Abstract Factory │  Fábrica + productos por canal
transaccion.py         │  4 patrones       │  Orquestador central
cuenta_builder.py      │  Builder          │  Constructor fluent de cuentas
banco.py               │  Dominio          │  Entidad banco + búsquedas
cuenta.py              │  Dominio          │  Entidad cuenta
usuario.py             │  Dominio          │  Entidad usuario
sucursal.py            │  Dominio          │  Entidad sucursal
main.py                │  Cliente          │  Interfaz de consola
```

---

## Diagrama UML — Sistema Bancario Core

El diagrama representa la arquitectura del Sistema Bancario Core implementado en Python, mostrando cómo las clases se relacionan entre sí y cómo los cuatro patrones de diseño coexisten dentro del mismo sistema.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                 DIAGRAMA DE CLASES — SISTEMA BANCARIO CORE                  ║
╚══════════════════════════════════════════════════════════════════════════════╝


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    CAPA DE DOMINIO — Modelo de negocio
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 ┌───────────────────────────┐                    ┌───────────────────────────┐
 │           Banco           │  1           0..*  │          Sucursal         │
 ├───────────────────────────┤ ─────────────────▶ ├───────────────────────────┤
 │ - usuarios : List         │                    │ - _nombre : String        │
 │ - sucursales : List       │                    │ - _cuentas : List         │
 ├───────────────────────────┤                    ├───────────────────────────┤
 │ + agregar_usuario()       │                    │ + agregar_cuenta()        │
 │ + buscar_usuario_         │                    │ + nombre (property)       │
 │     por_documento()       │                    │ + cuentas (property)      │
 │ + buscar_cuenta_          │                    └───────────────────────────┘
 │     por_numero()          │                                 ▲
 └───────────────────────────┘                                │ asociada a
               │                                              │
               │ 1                                            │
               │ registra                                     │
               │ 0..*                                         │
               ▼                                              │
 ┌───────────────────────────┐                                │
 │          Usuario          │                                │
 ├───────────────────────────┤                                │
 │ + nombre : String         │                                │
 │ + documento : String      │                                │
 │ + verificado_kyc : Boolean│                                │
 │ + cuentas : List          │                                │
 ├───────────────────────────┤                                │
 │ + verificar_kyc()         │                                │
 │ + agregar_cuenta()        │                                │
 └───────────────────────────┘                                │
               │                                              │
               │ 1                                            │
               │ posee                                        │
               │ 0..*                                         │
               ▼                                              │
 ┌───────────────────────────┐                                │
 │          Cuenta           │ ───────────────────────────────┘
 ├───────────────────────────┤
 │ + numero : String         │
 │ - _tipo : String          │
 │ - _saldo : Decimal        │
 │ + transacciones : List    │
 ├───────────────────────────┤
 │ + depositar()             │
 │ + retirar()               │
 │ + transferir()            │
 │ + saldo (property)        │
 │ + tipo (property)         │
 │ - _registrar()            │
 └───────────────────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PATRÓN SINGLETON  ◄─────────────────────────────── [patron_1_singleton]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 ┌──────────────────────────┐        ┌──────────────────────────┐
 │      <<Singleton>>       │  lee   │      <<Singleton>>       │
 │        ConfigBanco       │───────▶│      DetectorFraude      │
 ├──────────────────────────┤        ├──────────────────────────┤
 │ - _instancia             │        │ - _instancia             │
 │ - _lock : Lock           │        │ - _lock : Lock           │
 │ - _limite_aml : float    │        │ - _limite_aml : float    │
 │ - _max_transacciones:int │        │ - _max_transacciones:int │
 │ - _ventana_minutos : int │        │ - _ventana_minutos : int │
 │ - _saldo_critico : float │        │ - _saldo_critico : float │
 │ - _sucursales_predet:List│        ├──────────────────────────┤
 ├──────────────────────────┤        │ + get_instancia()        │
 │ + get_instancia()        │        │ + evaluar()              │
 │ + get_limite_aml()       │        └──────────────────────────┘
 │ + get_max_transacc()     │
 │ + get_ventana_tiemp()    │
 │ + get_saldo_critico()    │
 │ + get_sucursales()       │
 └──────────────────────────┘

 ┌──────────────────────────┐        ┌──────────────────────────┐
 │      <<Singleton>>       │        │      <<Singleton>>       │
 │         Logger           │        │    SucursalesManager     │
 ├──────────────────────────┤        ├──────────────────────────┤
 │ - _instancia             │        │ - _instancia             │
 │ - _lock : Lock           │        │ - _lock : Lock           │
 │ - _logs : List           │        │ - _sucursales : List     │
 ├──────────────────────────┤        ├──────────────────────────┤
 │ + get_instancia()        │        │ + get_instancia()        │
 │ + log()                  │        │ + agregar_sucursal()     │
 │ + get_logs()             │        │ + sucursales (property)  │
 └──────────────────────────┘        └──────────────────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PATRÓN FACTORY METHOD  ◄───────────────────── [patron_2_factory_method]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌──────────────────────────┐
                    │       <<abstract>>       │   archivo: operacion.py
                    │         Operacion        │   (Producto abstracto)
                    ├──────────────────────────┤
                    │ + ejecutar(cuenta_origen,│
                    │   monto, canal,          │
                    │   cuenta_destino)        │
                    └──────────────────────────┘
                                 △
                                 │  hereda
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
 ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐
 │OperacionDeposito │  │ OperacionRetiro  │  │OperacionTransferencia  │
 ├──────────────────┤  ├──────────────────┤  ├────────────────────────┤
 │ + ejecutar()     │  │ + ejecutar()     │  │ + ejecutar()           │
 │ cuenta.depositar │  │ cuenta.retirar() │  │ cuenta.transferir()    │
 └──────────────────┘  └──────────────────┘  └────────────────────────┘

                    ┌──────────────────────────┐
                    │       <<abstract>>       │   archivo: operacion_factory.py
                    │      OperacionFactory    │   (Creador abstracto)
                    ├──────────────────────────┤
                    │ + crear_operacion()      │
                    │     : Operacion          │
                    └──────────────────────────┘
                                 △
                                 │  hereda
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
 ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐
 │  DepositoFactory │  │  RetiroFactory   │  │  TransferenciaFactory  │
 ├──────────────────┤  ├──────────────────┤  ├────────────────────────┤
 │+crear_operacion()│  │+crear_operacion()│  │ + crear_operacion()    │
 │ : Operacion-     │  │ : Operacion-     │  │   : Operacion-         │
 │   Deposito       │  │   Retiro         │  │     Transferencia      │
 └──────────────────┘  └──────────────────┘  └────────────────────────┘
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 │ instanciadas por
                                 ▼
                    ┌──────────────────────────┐
                    │       Transaccion        │
                    ├──────────────────────────┤
                    │ FACTORIES = {            │
                    │  "deposito":             │
                    │     DepositoFactory()    │
                    │  "retiro":               │
                    │     RetiroFactory()      │
                    │  "transferencia":        │
                    │     TransfFactory()      │
                    │ }                        │
                    │ CANALES_VALIDOS : Set    │
                    ├──────────────────────────┤
                    │ + procesar()             │
                    └──────────────────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PATRÓN ABSTRACT FACTORY  ◄────────────────── [patron_3_abstract_factory]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

               ┌────────────────────────────┐
               │         <<abstract>>       │   archivo: canal_factory.py
               │     AbstractCanalFactory   │   (Fábrica abstracta)
               ├────────────────────────────┤
               │ + crear_validador()        │
               │     : Validador            │
               │ + crear_notificador()      │
               │     : Notificador          │
               │ + crear_limite()           │
               │     : LimiteCanal          │
               └────────────────────────────┘
                             △
                             │  hereda
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│    WebFactory    │ │   MovilFactory   │ │  CajeroFactory   │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│+crear_validador()│ │+crear_validador()│ │+crear_validador()│
│+crear_notific.() │ │+crear_notific.() │ │+crear_notific.() │
│+crear_limite()   │ │+crear_limite()   │ │+crear_limite()   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
       │ crea               │ crea               │ crea
       ▼                    ▼                    ▼
┌────────────┐       ┌────────────┐       ┌────────────┐
│ValidadorWeb│       │ValidadorMov│       │ValidadorCaj│
├────────────┤       ├────────────┤       ├────────────┤  Producto A
│+validar()  │       │+validar()  │       │+validar()  │  (hereda Validador)
│ máx: $50M  │       │ máx:  $5M  │       │ máx:  $2M  │
│            │       │            │       │ NO transf. │
└────────────┘       └────────────┘       └────────────┘

┌────────────┐       ┌────────────┐       ┌────────────┐
│Notificador │       │Notificador │       │Notificador │
│    Web     │       │   Movil    │       │  Cajero    │  Producto B
├────────────┤       ├────────────┤       ├────────────┤  (hereda Notificador)
│+notificar()│       │+notificar()│       │+notificar()│
│  (email)   │       │(push + SMS)│       │ (voucher)  │
└────────────┘       └────────────┘       └────────────┘

┌────────────┐       ┌────────────┐       ┌────────────┐
│LimiteCanal │       │LimiteCanal │       │LimiteCanal │
│    Web     │       │   Movil    │       │  Cajero    │  Producto C
├────────────┤       ├────────────┤       ├────────────┤  (hereda LimiteCanal)
│+get_max()  │       │+get_max()  │       │+get_max()  │
│+get_min()  │       │+get_min()  │       │+get_min()  │
│+get_nombre │       │+get_nombre │       │+get_nombre │
└────────────┘       └────────────┘       └────────────┘

          ┌──────────────────────────────┐
          │      CanalFactoryProducer    │   (Punto de entrada)
          ├──────────────────────────────┤
          │ _fabricas = {               │
          │   "web"   : WebFactory()    │
          │   "movil" : MovilFactory()  │
          │   "cajero": CajeroFactory() │
          │ }                           │
          ├──────────────────────────────┤
          │ + get_factory(canal: str)   │
          │     : AbstractCanalFactory  │
          └──────────────────────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PATRÓN BUILDER  ◄──────────────────────────────── [patron_4_builder]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        ┌──────────────────────────────┐
        │         CuentaBuilder        │   archivo: cuenta_builder.py
        ├──────────────────────────────┤
        │ - _numero        : String    │
        │ - _tipo          : String    │
        │ - _saldo_inicial : float     │
        │ - _usuario       : Usuario   │
        │ - _sucursal      : Sucursal  │
        ├──────────────────────────────┤
        │ + numero(n: str)             │──┐
        │ + tipo(t: str)               │  │ retornan self
        │ + saldo_inicial(m: float)    │  │ (Fluent API)
        │ + asociar_usuario(u: Usuario)│──┘
        │ + asociar_sucursal(s: Sucurs)│
        │ + build() : Cuenta           │──► crea y asocia Cuenta
        └──────────────────────────────┘
                      │
                      │ crea
                      ▼
             ┌────────────────┐
             │     Cuenta     │
             └────────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                  PRODUCTOS ABSTRACTOS — Abstract Factory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│     <<abstract>>     │  │     <<abstract>>     │  │     <<abstract>>     │
│       Validador      │  │     Notificador      │  │     LimiteCanal      │
├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
│ + validar(monto,tipo)│  │ + notificar(tipo,    │  │ + get_limite_max()   │
│   : (bool, str)      │  │   monto, cuenta_num) │  │ + get_limite_min()   │
└──────────────────────┘  └──────────────────────┘  │ + get_nombre_canal() │
         △                         △                └──────────────────────┘
         │                         │                         △
  ┌──────┴──────┐           ┌──────┴──────┐          ┌──────┴──────┐
  │ValidadorWeb │           │NotifWeb     │          │LimiteWeb    │
  │ValidadorMov │           │NotifMovil   │          │LimiteMovil  │
  │ValidadorCaj │           │NotifCajero  │          │LimiteCajero │
  └─────────────┘           └─────────────┘          └─────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          CLASE ORQUESTADORA — Transaccion (integra los 4 patrones)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

               ┌─────────────────────────────────────────┐
               │               Transaccion               │
               ├─────────────────────────────────────────┤
               │ FACTORIES : Dict  [Factory Method]      │
               │ CANALES_VALIDOS : Set                   │
               ├─────────────────────────────────────────┤
               │ + procesar(cuenta_origen, monto,        │
               │            canal, cuenta_destino, tipo) │
               │                                         │
               │   Paso 1 ── Abstract Factory ─────────  │
               │            CanalFactoryProducer         │
               │            .get_factory(canal)          │
               │            → validador.validar()        │
               │                                         │
               │   Paso 2 ── Singleton ─────────────────  │
               │            DetectorFraude               │
               │            .get_instancia()             │
               │            → detector.evaluar()         │
               │                                         │
               │   Paso 3 ── Factory Method ────────────  │
               │            FACTORIES[tipo]              │
               │            .crear_operacion()           │
               │            → operacion.ejecutar()       │
               │                                         │
               │   Paso 4 ── Abstract Factory ─────────  │
               │            → notificador.notificar()    │
               └─────────────────────────────────────────┘
                     │            │            │
                     ▼            ▼            ▼
          [Singleton]      [FactoryMethod]  [AbstractFactory]
          DetectorFraude   OperacionFactory  CanalFactoryProducer
          Logger           Operacion         AbstractCanalFactory
```

---

## classDiagram (Mermaid)

```mermaid
classDiagram
direction TB

%% ═══════════════════════════════════════════════════
%%  MÓDULO DOMINIO — Banco, Sucursal, Usuario, Cuenta
%% ═══════════════════════════════════════════════════

class Banco {
  -usuarios : List
  -sucursales : List
  +agregar_usuario(usuario : Usuario)
  +buscar_usuario_por_documento(documento) Usuario
  +buscar_cuenta_por_numero(numero) Cuenta
}

class Sucursal {
  -_nombre : String
  -_cuentas : List
  +agregar_cuenta(cuenta : Cuenta)
  +nombre() String
  +cuentas() List
}

class Usuario {
  +nombre : String
  +documento : String
  +verificado_kyc : Boolean
  +cuentas : List
  +verificar_kyc()
  +agregar_cuenta(cuenta : Cuenta)
}

class Cuenta {
  +numero : String
  -_tipo : String
  -_saldo : Decimal
  +transacciones : List
  +depositar(monto, canal)
  +retirar(monto, canal)
  +transferir(cuenta_destino, monto, canal)
  +saldo() float
  +tipo() String
  -_registrar(tipo, monto, canal)
}

%% ══════════════════════
%%  PATRÓN 1 — SINGLETON
%% ══════════════════════

class ConfigBanco {
  <<Singleton>>
  -_instancia
  -_lock : Lock
  -_limite_aml : float
  -_max_transacciones : int
  -_ventana_minutos : int
  -_saldo_critico : float
  -_sucursales_predeterminadas : List
  +get_instancia() ConfigBanco
  +get_limite_aml() float
  +get_max_transacciones_ventana() int
  +get_ventana_tiempo_minutos() int
  +get_saldo_critico() float
  +get_sucursales() List
}

class Logger {
  <<Singleton>>
  -_instancia
  -_lock : Lock
  -_logs : List
  +get_instancia() Logger
  +log(mensaje, nivel)
  +get_logs() List
}

class DetectorFraude {
  <<Singleton>>
  -_instancia
  -_lock : Lock
  -_limite_aml : float
  -_max_transacciones : int
  -_ventana_minutos : int
  -_saldo_critico : float
  +get_instancia() DetectorFraude
  +evaluar(cuenta, monto, canal, tipo, cuenta_destino) tuple
}

class SucursalesManager {
  <<Singleton>>
  -_instancia
  -_lock : Lock
  -_sucursales : List
  +get_instancia() SucursalesManager
  +agregar_sucursal(nombre)
  +sucursales() List
}

%% ═══════════════════════════
%%  PATRÓN 2 — FACTORY METHOD
%% ═══════════════════════════

class Operacion {
  <<abstract>>
  +ejecutar(cuenta_origen, monto, canal, cuenta_destino)
}

class OperacionDeposito {
  +ejecutar(cuenta_origen, monto, canal, cuenta_destino)
}

class OperacionRetiro {
  +ejecutar(cuenta_origen, monto, canal, cuenta_destino)
}

class OperacionTransferencia {
  +ejecutar(cuenta_origen, monto, canal, cuenta_destino)
}

class OperacionFactory {
  <<abstract>>
  +crear_operacion() Operacion
}

class DepositoFactory {
  +crear_operacion() OperacionDeposito
}

class RetiroFactory {
  +crear_operacion() OperacionRetiro
}

class TransferenciaFactory {
  +crear_operacion() OperacionTransferencia
}

%% ═════════════════════════════
%%  PATRÓN 3 — ABSTRACT FACTORY
%% ═════════════════════════════

class AbstractCanalFactory {
  <<abstract>>
  +crear_validador() Validador
  +crear_notificador() Notificador
  +crear_limite() LimiteCanal
}

class WebFactory {
  +crear_validador() ValidadorWeb
  +crear_notificador() NotificadorWeb
  +crear_limite() LimiteCanalWeb
}

class MovilFactory {
  +crear_validador() ValidadorMovil
  +crear_notificador() NotificadorMovil
  +crear_limite() LimiteCanalMovil
}

class CajeroFactory {
  +crear_validador() ValidadorCajero
  +crear_notificador() NotificadorCajero
  +crear_limite() LimiteCanalCajero
}

class CanalFactoryProducer {
  -_fabricas : Dict
  +get_factory(canal : String) AbstractCanalFactory
}

class Validador {
  <<abstract>>
  +validar(monto, tipo) tuple
}

class Notificador {
  <<abstract>>
  +notificar(tipo, monto, cuenta_numero)
}

class LimiteCanal {
  <<abstract>>
  +get_limite_maximo() float
  +get_limite_minimo() float
  +get_nombre_canal() String
}

class ValidadorWeb {
  +validar(monto, tipo) tuple
}

class NotificadorWeb {
  +notificar(tipo, monto, cuenta_numero)
}

class LimiteCanalWeb {
  +get_limite_maximo() float
  +get_limite_minimo() float
  +get_nombre_canal() String
}

class ValidadorMovil {
  +validar(monto, tipo) tuple
}

class NotificadorMovil {
  +notificar(tipo, monto, cuenta_numero)
}

class LimiteCanalMovil {
  +get_limite_maximo() float
  +get_limite_minimo() float
  +get_nombre_canal() String
}

class ValidadorCajero {
  +validar(monto, tipo) tuple
}

class NotificadorCajero {
  +notificar(tipo, monto, cuenta_numero)
}

class LimiteCanalCajero {
  +get_limite_maximo() float
  +get_limite_minimo() float
  +get_nombre_canal() String
}

%% ══════════════════════
%%  PATRÓN 4 — BUILDER
%% ══════════════════════

class CuentaBuilder {
  -_numero : String
  -_tipo : String
  -_saldo_inicial : float
  -_usuario : Usuario
  -_sucursal : Sucursal
  +numero(n: str) CuentaBuilder
  +tipo(t: str) CuentaBuilder
  +saldo_inicial(m: float) CuentaBuilder
  +asociar_usuario(u: Usuario) CuentaBuilder
  +asociar_sucursal(s: Sucursal) CuentaBuilder
  +build() Cuenta
}

%% ═════════════════════
%%  ORQUESTADOR CENTRAL
%% ═════════════════════

class Transaccion {
  +FACTORIES : Dict
  +CANALES_VALIDOS : Set
  +procesar(cuenta_origen, monto, canal, cuenta_destino, tipo) bool
}

%% ══════════════════════
%%  RELACIONES — DOMINIO
%% ══════════════════════

Banco ||--o{ Sucursal : "gestiona"
Banco ||--o{ Usuario : "registra"
Usuario ||--o{ Cuenta : "posee"
Sucursal ||--o{ Cuenta : "asociada a"

%% ════════════════════════
%%  RELACIONES — SINGLETON
%% ════════════════════════

ConfigBanco --> DetectorFraude : "configura"
SucursalesManager --> Sucursal : "administra"
Transaccion --> Logger : "usa"
Transaccion --> DetectorFraude : "consulta"

%% ═════════════════════════════
%%  RELACIONES — FACTORY METHOD
%% ═════════════════════════════

Operacion <|-- OperacionDeposito
Operacion <|-- OperacionRetiro
Operacion <|-- OperacionTransferencia

OperacionFactory <|-- DepositoFactory
OperacionFactory <|-- RetiroFactory
OperacionFactory <|-- TransferenciaFactory

DepositoFactory ..> OperacionDeposito : "crea"
RetiroFactory ..> OperacionRetiro : "crea"
TransferenciaFactory ..> OperacionTransferencia : "crea"

Transaccion --> OperacionFactory : "usa"
OperacionDeposito --> Cuenta : "depositar()"
OperacionRetiro --> Cuenta : "retirar()"
OperacionTransferencia --> Cuenta : "transferir()"

%% ═══════════════════════════════
%%  RELACIONES — ABSTRACT FACTORY
%% ═══════════════════════════════

AbstractCanalFactory <|-- WebFactory
AbstractCanalFactory <|-- MovilFactory
AbstractCanalFactory <|-- CajeroFactory

Validador <|-- ValidadorWeb
Validador <|-- ValidadorMovil
Validador <|-- ValidadorCajero

Notificador <|-- NotificadorWeb
Notificador <|-- NotificadorMovil
Notificador <|-- NotificadorCajero

LimiteCanal <|-- LimiteCanalWeb
LimiteCanal <|-- LimiteCanalMovil
LimiteCanal <|-- LimiteCanalCajero

WebFactory ..> ValidadorWeb : "crea"
WebFactory ..> NotificadorWeb : "crea"
WebFactory ..> LimiteCanalWeb : "crea"

MovilFactory ..> ValidadorMovil : "crea"
MovilFactory ..> NotificadorMovil : "crea"
MovilFactory ..> LimiteCanalMovil : "crea"

CajeroFactory ..> ValidadorCajero : "crea"
CajeroFactory ..> NotificadorCajero : "crea"
CajeroFactory ..> LimiteCanalCajero : "crea"

CanalFactoryProducer --> AbstractCanalFactory : "retorna"
Transaccion --> CanalFactoryProducer : "consulta"

%% ══════════════════════
%%  RELACIONES — BUILDER
%% ══════════════════════

CuentaBuilder ..> Cuenta : "construye"
CuentaBuilder --> Usuario : "asocia"
CuentaBuilder --> Sucursal : "asocia"
```
  ------------------------------
# Documentacion de las implementaciones semana a semana 

https://github.com/Andres023-0/SistemaBancario/blob/main/Documentacion_Implementacion.docx

