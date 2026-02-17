# Patrones
Decimo Semestre-Patrones de Software

# Sistema Bancario Core - Módulo KYC/AML

Proyecto académico que simula componentes clave de un **core bancario** moderno, con enfoque especial en procesos de **cumplimiento regulatorio** (KYC y AML) en tiempo real.

**Objetivo principal**  
Demostrar la aplicación práctica de **principios SOLID** y **patrones de diseño** para construir software de calidad en un contexto financiero regulado, eliminando code smells comunes y logrando un diseño modular, mantenible y extensible.

## Contexto del Proyecto

Este trabajo forma parte de la asignatura/taller sobre **Patrones de Diseño y Arquitectura de Software**.  
Se simula un sistema bancario core con módulos representativos del sector financiero:

- Gestión de cuentas múltiples  
- Transacciones por múltiples canales (web, móvil, cajeros, sucursales)  
- Detección de fraude en tiempo real  
- Cumplimiento regulatorio en tiempo real:  
  - **KYC** (Know Your Customer) – Onboarding y validación de clientes  
  - **AML** (Anti-Money Laundering) – Monitoreo y detección de operaciones sospechosas  

## Enfoque de Calidad de Software

### Principios SOLID aplicados

- **S** – Single Responsibility Principle  
  Cada clase tiene una única responsabilidad (validación, creación, persistencia, reglas de negocio, etc.)

- **O** – Open-Closed Principle  
  Extensible mediante estrategias, factories y polimorfismo sin modificar código existente

- **L** – Liskov Substitution Principle  
  Subclases sustituibles sin romper el comportamiento esperado

- **I** – Interface Segregation Principle  
  Interfaces pequeñas y específicas en lugar de interfaces grandes y generales

- **D** – Dependency Inversion Principle  
  Dependencia de abstracciones (interfaces) en lugar de implementaciones concretas

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
