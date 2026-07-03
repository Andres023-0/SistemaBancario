from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from logger import Logger


# =============================================================================
# PATRÓN TEMPLATE METHOD — Generación de reportes bancarios
#
# Define el esqueleto del algoritmo de generación de reporte en la clase
# base. Las subclases concretas sobreescriben solo los pasos que cambian,
# sin alterar la estructura general del proceso.
#
# Participantes:
#   - GeneradorReporte          → AbstractClass (define el template)
#   - ReporteMovimientos        → ConcreteClass A
#   - ReportePrestamos          → ConcreteClass B
#   - ReporteSucursal           → ConcreteClass C
#   - ReporteUsuario            → ConcreteClass D
#
# Esqueleto del algoritmo (template):
#   1. inicializar()      — configura parámetros base (hook opcional)
#   2. recopilar_datos()  — obtiene los datos crudos (abstracto)
#   3. filtrar_datos()    — aplica filtros de período/tipo (hook opcional)
#   4. calcular_totales() — agrega y resume (abstracto)
#   5. formatear()        — estructura el dict de respuesta (abstracto)
#   6. finalizar()        — log de cierre (hook fijo)
#
# Qué resuelve:
#   SIN TEMPLATE: cada tipo de reporte en api.py tiene su propio bloque
#                 de código con lógica duplicada de fechas, logging y
#                 formateo. Agregar un nuevo reporte requiere copiar toda
#                 esa estructura.
#   CON TEMPLATE: el flujo está definido una sola vez. Agregar un nuevo
#                 reporte = crear una subclase e implementar los métodos
#                 abstractos. El resto es heredado automáticamente.
# =============================================================================


# =============================================================================
# ABSTRACT CLASS — Template
# =============================================================================

class GeneradorReporte(ABC):
    """
    Clase abstracta que define el esqueleto del algoritmo de generación
    de reportes bancarios.

    El método generar() es el Template Method: no debe sobreescribirse.
    Las subclases implementan recopilar_datos(), calcular_totales() y
    formatear(). Pueden sobreescribir inicializar() y filtrar_datos()
    si necesitan comportamiento adicional (hooks).
    """

    def __init__(self, banco, periodo_dias: int = 30):
        self._banco        = banco
        self._periodo_dias = periodo_dias
        self._fecha_inicio = (datetime.now() - timedelta(days=periodo_dias - 1)).date()
        self._fecha_fin    = datetime.now().date()
        self._datos_crudos = []
        self._datos_filtrados = []
        self._totales      = {}
        self._logger       = Logger.get_instancia()

    # =========================================================================
    # TEMPLATE METHOD — No sobreescribir
    # =========================================================================

    def generar(self) -> dict:
        """
        Esqueleto del algoritmo. Define el orden fijo de los pasos.
        Este método NO debe sobreescribirse en las subclases.
        """
        self._logger.log(
            f"[TEMPLATE] Iniciando reporte '{self.get_nombre()}' "
            f"| Período: últimos {self._periodo_dias} días "
            f"({self._fecha_inicio} → {self._fecha_fin})",
            nivel="INFO"
        )

        self.inicializar()                          # Hook A (opcional)
        self._datos_crudos    = self.recopilar_datos()   # Paso 2 (abstracto)
        self._datos_filtrados = self.filtrar_datos()     # Hook B (opcional)
        self._totales         = self.calcular_totales()  # Paso 4 (abstracto)
        resultado             = self.formatear()         # Paso 5 (abstracto)
        self.finalizar(resultado)                   # Hook C (fijo)

        return resultado

    # =========================================================================
    # HOOKS — Pueden sobreescribirse, tienen implementación por defecto
    # =========================================================================

    def inicializar(self):
        """
        Hook A: configuración previa al reporte.
        Por defecto no hace nada. Las subclases pueden sobreescribir.
        """
        pass

    def filtrar_datos(self) -> list:
        """
        Hook B: filtra self._datos_crudos por período u otros criterios.
        Por defecto filtra por período usando el campo 'fecha' de cada registro.
        """
        filtrados = []
        for item in self._datos_crudos:
            fecha_str = item.get("fecha", "")
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S").date()
                if self._fecha_inicio <= fecha <= self._fecha_fin:
                    filtrados.append(item)
            except Exception:
                # Si no tiene fecha o tiene formato distinto, se incluye igual
                filtrados.append(item)
        return filtrados

    def finalizar(self, resultado: dict):
        """
        Hook C: log de cierre. Siempre se ejecuta al final.
        Las subclases pueden sobreescribir para agregar lógica adicional.
        """
        total_items = resultado.get("total_registros", 0)
        self._logger.log(
            f"[TEMPLATE] Reporte '{self.get_nombre()}' completado "
            f"| Registros: {total_items}",
            nivel="SUCCESS"
        )

    # =========================================================================
    # MÉTODOS ABSTRACTOS — Deben implementarse en cada subclase
    # =========================================================================

    @abstractmethod
    def recopilar_datos(self) -> list:
        """Paso 2: obtiene los datos crudos de la fuente correspondiente."""
        pass

    @abstractmethod
    def calcular_totales(self) -> dict:
        """Paso 4: calcula agregados, sumas y métricas sobre datos filtrados."""
        pass

    @abstractmethod
    def formatear(self) -> dict:
        """Paso 5: estructura el dict final que retornará la API."""
        pass

    @abstractmethod
    def get_nombre(self) -> str:
        """Nombre identificador del tipo de reporte."""
        pass


# =============================================================================
# CONCRETE CLASS A — Reporte de movimientos de una cuenta
# =============================================================================

class ReporteMovimientos(GeneradorReporte):
    """
    ConcreteClass A: reporte de movimientos de una cuenta específica.
    Muestra historial, volumen por tipo, por canal y saldo actual.
    """

    def __init__(self, banco, numero_cuenta: str, periodo_dias: int = 30):
        super().__init__(banco, periodo_dias)
        self._numero_cuenta = numero_cuenta
        self._cuenta        = None

    def get_nombre(self) -> str:
        return "ReporteMovimientos"

    def inicializar(self):
        """Hook A: busca la cuenta antes de recopilar datos."""
        self._cuenta = self._banco.buscar_cuenta_por_numero(self._numero_cuenta)
        if not self._cuenta:
            raise ValueError(f"Cuenta {self._numero_cuenta} no encontrada")

    def recopilar_datos(self) -> list:
        return list(self._cuenta.transacciones)

    def calcular_totales(self) -> dict:
        por_tipo   = {"deposito": 0, "retiro": 0, "transferencia": 0}
        vol_tipo   = {"deposito": 0.0, "retiro": 0.0, "transferencia": 0.0}
        por_canal  = {"web": 0, "movil": 0, "cajero": 0}

        for t in self._datos_filtrados:
            tipo  = t.get("tipo",  "deposito")
            canal = t.get("canal", "web")
            monto = t.get("monto", 0.0)
            if tipo  in por_tipo:  por_tipo[tipo]  += 1
            if tipo  in vol_tipo:  vol_tipo[tipo]  += monto
            if canal in por_canal: por_canal[canal] += 1

        return {
            "total":    len(self._datos_filtrados),
            "por_tipo": por_tipo,
            "vol_tipo": vol_tipo,
            "por_canal": por_canal,
        }

    def formatear(self) -> dict:
        return {
            "tipo_reporte":    self.get_nombre(),
            "numero_cuenta":   self._numero_cuenta,
            "tipo_cuenta":     self._cuenta.tipo,
            "saldo_actual":    self._cuenta.saldo,
            "estado_cuenta":   self._cuenta.get_estado().get_nombre(),
            "periodo_dias":    self._periodo_dias,
            "fecha_inicio":    str(self._fecha_inicio),
            "fecha_fin":       str(self._fecha_fin),
            "total_registros": self._totales["total"],
            "por_tipo":        self._totales["por_tipo"],
            "volumen_por_tipo": self._totales["vol_tipo"],
            "por_canal":       self._totales["por_canal"],
            "movimientos":     self._datos_filtrados[-50:],  # últimos 50
        }


# =============================================================================
# CONCRETE CLASS B — Reporte de préstamos de un usuario
# =============================================================================

class ReportePrestamos(GeneradorReporte):
    """
    ConcreteClass B: reporte de préstamos asociados a un usuario.
    Muestra estado, progreso de pago y totales de intereses.
    """

    def __init__(self, banco, documento: str, periodo_dias: int = 365):
        super().__init__(banco, periodo_dias)
        self._documento = documento
        self._usuario   = None

    def get_nombre(self) -> str:
        return "ReportePrestamos"

    def inicializar(self):
        """Hook A: valida que el usuario exista."""
        self._usuario = self._banco.buscar_usuario_por_documento(self._documento)
        if not self._usuario:
            raise ValueError(f"Usuario con documento {self._documento} no encontrado")

    def recopilar_datos(self) -> list:
        from prestamo_strategy import GestorPrestamos
        todos = GestorPrestamos.get_instancia().get_por_documento(self._documento)
        return [p.to_dict() for p in todos]

    def filtrar_datos(self) -> list:
        """
        Hook B sobreescrito: filtra por fecha_creacion del préstamo
        en lugar del campo genérico 'fecha'.
        """
        filtrados = []
        for item in self._datos_crudos:
            fecha_str = item.get("fecha_creacion", "")
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S").date()
                if self._fecha_inicio <= fecha <= self._fecha_fin:
                    filtrados.append(item)
            except Exception:
                filtrados.append(item)
        return filtrados

    def calcular_totales(self) -> dict:
        total_deuda    = sum(p["total_a_pagar"]   for p in self._datos_filtrados)
        total_pagado   = sum(p["total_pagado"]     for p in self._datos_filtrados)
        total_pendiente= sum(
            p["total_a_pagar"] - p["total_pagado"] for p in self._datos_filtrados
        )
        activos = [p for p in self._datos_filtrados if p["estado"] == "activo"]
        pagados = [p for p in self._datos_filtrados if p["estado"] == "pagado"]

        return {
            "total":           len(self._datos_filtrados),
            "activos":         len(activos),
            "pagados":         len(pagados),
            "total_deuda":     round(total_deuda, 2),
            "total_pagado":    round(total_pagado, 2),
            "total_pendiente": round(total_pendiente, 2),
        }

    def formatear(self) -> dict:
        return {
            "tipo_reporte":    self.get_nombre(),
            "documento":       self._documento,
            "nombre_usuario":  self._usuario.nombre,
            "periodo_dias":    self._periodo_dias,
            "fecha_inicio":    str(self._fecha_inicio),
            "fecha_fin":       str(self._fecha_fin),
            "total_registros": self._totales["total"],
            "prestamos_activos":  self._totales["activos"],
            "prestamos_pagados":  self._totales["pagados"],
            "total_deuda":        self._totales["total_deuda"],
            "total_pagado":       self._totales["total_pagado"],
            "total_pendiente":    self._totales["total_pendiente"],
            "prestamos":          self._datos_filtrados,
        }


# =============================================================================
# CONCRETE CLASS C — Reporte consolidado de una sucursal
# =============================================================================

class ReporteSucursal(GeneradorReporte):
    """
    ConcreteClass C: reporte consolidado de actividad de una sucursal.
    Muestra saldo total, movimientos por día, por tipo y por canal.
    """

    def __init__(self, banco, nombre_sucursal: str, periodo_dias: int = 30):
        super().__init__(banco, periodo_dias)
        self._nombre_sucursal = nombre_sucursal
        self._sucursal        = None

    def get_nombre(self) -> str:
        return "ReporteSucursal"

    def inicializar(self):
        """Hook A: busca la sucursal antes de recopilar datos."""
        from sucursales_manager import SucursalesManager
        manager = SucursalesManager.get_instancia()
        self._sucursal = next(
            (s for s in manager.sucursales
             if s.nombre.lower() == self._nombre_sucursal.lower()),
            None
        )
        if not self._sucursal:
            raise ValueError(f"Sucursal '{self._nombre_sucursal}' no encontrada")

    def recopilar_datos(self) -> list:
        """Reúne todas las transacciones de todas las cuentas de la sucursal."""
        todas = []
        for cuenta in self._sucursal.cuentas:
            for t in cuenta.transacciones:
                todas.append({**t, "numero_cuenta": cuenta.numero})
        return todas

    def calcular_totales(self) -> dict:
        por_tipo  = {"deposito": 0, "retiro": 0, "transferencia": 0}
        por_canal = {"web": 0, "movil": 0, "cajero": 0}
        vol_tipo  = {"deposito": 0.0, "retiro": 0.0, "transferencia": 0.0}

        dias: dict[str, int] = {}
        fecha_actual = self._fecha_inicio
        while fecha_actual <= self._fecha_fin:
            dias[str(fecha_actual)] = 0
            fecha_actual += timedelta(days=1)

        for t in self._datos_filtrados:
            tipo  = t.get("tipo",  "deposito")
            canal = t.get("canal", "web")
            monto = t.get("monto", 0.0)
            try:
                fecha_d = str(datetime.strptime(
                    t["fecha"], "%Y-%m-%d %H:%M:%S").date())
                if fecha_d in dias:
                    dias[fecha_d] += 1
            except Exception:
                pass
            if tipo  in por_tipo:  por_tipo[tipo]  += 1
            if tipo  in vol_tipo:  vol_tipo[tipo]  += monto
            if canal in por_canal: por_canal[canal] += 1

        return {
            "total":    len(self._datos_filtrados),
            "por_tipo": por_tipo,
            "vol_tipo": vol_tipo,
            "por_canal": por_canal,
            "por_dia":  [{"fecha": k, "cantidad": v} for k, v in sorted(dias.items())],
        }

    def formatear(self) -> dict:
        return {
            "tipo_reporte":    self.get_nombre(),
            "sucursal":        self._nombre_sucursal,
            "saldo_total":     self._sucursal.get_saldo_total(),
            "total_cuentas":   len(self._sucursal.cuentas),
            "periodo_dias":    self._periodo_dias,
            "fecha_inicio":    str(self._fecha_inicio),
            "fecha_fin":       str(self._fecha_fin),
            "total_registros": self._totales["total"],
            "por_tipo":        self._totales["por_tipo"],
            "volumen_por_tipo": self._totales["vol_tipo"],
            "por_canal":       self._totales["por_canal"],
            "actividad_diaria": self._totales["por_dia"],
        }


# =============================================================================
# CONCRETE CLASS D — Reporte resumen de un usuario
# =============================================================================

class ReporteUsuario(GeneradorReporte):
    """
    ConcreteClass D: reporte completo de un usuario (cuentas + movimientos).
    Útil para la vista de perfil del usuario en el frontend.
    """

    def __init__(self, banco, documento: str, periodo_dias: int = 30):
        super().__init__(banco, periodo_dias)
        self._documento = documento
        self._usuario   = None

    def get_nombre(self) -> str:
        return "ReporteUsuario"

    def inicializar(self):
        self._usuario = self._banco.buscar_usuario_por_documento(self._documento)
        if not self._usuario:
            raise ValueError(f"Usuario {self._documento} no encontrado")

    def recopilar_datos(self) -> list:
        todos = []
        for cuenta in self._usuario.cuentas:
            for t in cuenta.transacciones:
                todos.append({**t, "numero_cuenta": cuenta.numero})
        return todos

    def calcular_totales(self) -> dict:
        saldo_total = sum(c.saldo for c in self._usuario.cuentas)
        por_tipo    = {"deposito": 0, "retiro": 0, "transferencia": 0}
        vol_total   = 0.0

        for t in self._datos_filtrados:
            tipo  = t.get("tipo", "deposito")
            monto = t.get("monto", 0.0)
            if tipo in por_tipo:
                por_tipo[tipo] += 1
            vol_total += monto

        return {
            "total":       len(self._datos_filtrados),
            "saldo_total": saldo_total,
            "por_tipo":    por_tipo,
            "vol_total":   round(vol_total, 2),
        }

    def formatear(self) -> dict:
        cuentas_info = [
            {
                "numero":  c.numero,
                "tipo":    c.tipo,
                "saldo":   c.saldo,
                "estado":  c.get_estado().get_nombre(),
                "movimientos_periodo": len([
                    t for t in c.transacciones
                    if self._en_periodo(t.get("fecha", ""))
                ])
            }
            for c in self._usuario.cuentas
        ]
        return {
            "tipo_reporte":    self.get_nombre(),
            "documento":       self._documento,
            "nombre":          self._usuario.nombre,
            "kyc":             self._usuario.verificado_kyc,
            "total_cuentas":   len(self._usuario.cuentas),
            "saldo_total":     self._totales["saldo_total"],
            "periodo_dias":    self._periodo_dias,
            "fecha_inicio":    str(self._fecha_inicio),
            "fecha_fin":       str(self._fecha_fin),
            "total_registros": self._totales["total"],
            "volumen_total":   self._totales["vol_total"],
            "por_tipo":        self._totales["por_tipo"],
            "cuentas":         cuentas_info,
        }

    def _en_periodo(self, fecha_str: str) -> bool:
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S").date()
            return self._fecha_inicio <= fecha <= self._fecha_fin
        except Exception:
            return False


# =============================================================================
# PRODUCTOR DE REPORTES — punto de entrada único
# =============================================================================

class ReporteProducer:
    """
    Retorna el generador de reporte correcto por nombre.
    El cliente (api.py) nunca instancia directamente las subclases.

    Uso:
        generador = ReporteProducer.get("movimientos", banco,
                        numero_cuenta="1001", periodo_dias=30)
        resultado = generador.generar()
    """

    @staticmethod
    def get(tipo: str, banco, **kwargs) -> GeneradorReporte:
        tipo = tipo.lower().strip()
        periodo = kwargs.get("periodo_dias", 30)

        if tipo == "movimientos":
            numero_cuenta = kwargs.get("numero_cuenta")
            if not numero_cuenta:
                raise ValueError("Se requiere 'numero_cuenta' para ReporteMovimientos")
            return ReporteMovimientos(banco, numero_cuenta, periodo)

        elif tipo == "prestamos":
            documento = kwargs.get("documento")
            if not documento:
                raise ValueError("Se requiere 'documento' para ReportePrestamos")
            return ReportePrestamos(banco, documento, kwargs.get("periodo_dias", 365))

        elif tipo == "sucursal":
            nombre_sucursal = kwargs.get("nombre_sucursal")
            if not nombre_sucursal:
                raise ValueError("Se requiere 'nombre_sucursal' para ReporteSucursal")
            return ReporteSucursal(banco, nombre_sucursal, periodo)

        elif tipo == "usuario":
            documento = kwargs.get("documento")
            if not documento:
                raise ValueError("Se requiere 'documento' para ReporteUsuario")
            return ReporteUsuario(banco, documento, periodo)

        else:
            raise ValueError(
                f"Tipo de reporte no soportado: '{tipo}'. "
                f"Válidos: movimientos, prestamos, sucursal, usuario"
            )

    @staticmethod
    def listar() -> list:
        return ["movimientos", "prestamos", "sucursal", "usuario"]
