# Patrones - Sistema Bancario Core

#CREADO POR:
#BRAYAN ANDRES CAÑAS LEON / JUAN SEBASTIAN NIÑO FORERO

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

- **Factory Method / Abstract Factory** → Creación controlada de entidades (Cliente, Cuenta, Transacción)  
- **Strategy** → Diferentes algoritmos de detección AML según tipo de transacción o perfil de riesgo  
- **Repository** → Abstracción de acceso a datos (in-memory para simulación)  
- **Specification / Validator** → Reglas de validación KYC reutilizables y componibles  
- **DTO** → Transferencia limpia de datos entre capas  
- **Facade** (opcional) → Interfaz simplificada para procesos complejos de onboarding  

### Code Smells eliminados / refactorizados

- Long Parameter List  
- Duplicate Code  
- Primitive Obsession  
- Data Clumps  
- Large Method / God Method  
- Feature Envy  
- Acoplamiento alto entre capas  

## Estructura del Código (Clean Architecture)
