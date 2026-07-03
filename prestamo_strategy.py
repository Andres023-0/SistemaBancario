from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from logger import Logger
import threading
import uuid


# =============================================================================
# PATRÓN STRATEGY — Semana 16
# =============================================================================


# =============================================================================
# INTERFAZ STRATEGY
# =============================================================================

class EstrategiaInteres(ABC):

    @abstractmethod
    def calcular_cuota(self, monto: float, tasa_anual: float, num_cuotas: int) -> float:
        pass

    @abstractmethod
    def calcular_total_intereses(self, monto: float, tasa_anual: float, num_cuotas: int) -> float:
        pass

    @abstractmethod
    def get_nombre(self) -> str:
        pass

    @abstractmethod
    def get_descripcion(self) -> str:
        pass

    def get_tipo(self) -> str:
        return self.get_nombre().lower().replace(" ", "_")


# =============================================================================
# CONCRETE STRATEGY A — INTERÉS FIJO
# =============================================================================

class InteresEstrategiaFijo(EstrategiaInteres):

    def calcular_cuota(self, monto: float, tasa_anual: float, num_cuotas: int) -> float:
        if tasa_anual == 0:
            return round(monto / num_cuotas, 2)
        i = (tasa_anual / 100) / 12
        factor = (1 + i) ** num_cuotas
        cuota = monto * (i * factor) / (factor - 1)
        return round(cuota, 2)

    def calcular_total_intereses(self, monto: float, tasa_anual: float, num_cuotas: int) -> float:
        cuota = self.calcular_cuota(monto, tasa_anual, num_cuotas)
        return round((cuota * num_cuotas) - monto, 2)

    def get_nombre(self) -> str:
        return "Interés Fijo"

    def get_descripcion(self) -> str:
        return "Cuota constante durante todo el préstamo. Tasa no cambia. Sistema francés de amortización."

    def get_tipo(self) -> str:
        return "fijo"


# =============================================================================
# CONCRETE STRATEGY B — INTERÉS VARIABLE
# =============================================================================

class InteresEstrategiaVariable(EstrategiaInteres):

    DTF_SIMULADO = 12.5
    SPREAD_BANCO = 4.0

    def _tasa_efectiva(self, tasa_anual: float) -> float:
        return max(tasa_anual, self.DTF_SIMULADO + self.SPREAD_BANCO)

    def calcular_cuota(self, monto: float, tasa_anual: float, num_cuotas: int) -> float:
        tasa = self._tasa_efectiva(tasa_anual)
        if tasa == 0:
            return round(monto / num_cuotas, 2)
        i = (tasa / 100) / 12
        factor = (1 + i) ** num_cuotas
        cuota = monto * (i * factor) / (factor - 1)
        return round(cuota, 2)

    def calcular_total_intereses(self, monto: float, tasa_anual: float, num_cuotas: int) -> float:
        cuota = self.calcular_cuota(monto, tasa_anual, num_cuotas)
        return round((cuota * num_cuotas) - monto, 2)

    def get_nombre(self) -> str:
        return "Interés Variable"

    def get_descripcion(self) -> str:
        return (f"Tasa referenciada al DTF ({self.DTF_SIMULADO}% EA) + spread banco "
                f"({self.SPREAD_BANCO}%). Puede subir o bajar según el mercado.")

    def get_tipo(self) -> str:
        return "variable"

    def get_dtf(self) -> float:
        return self.DTF_SIMULADO

    def get_spread(self) -> float:
        return self.SPREAD_BANCO


# =============================================================================
# PRODUCTOR DE ESTRATEGIAS
# =============================================================================

class EstrategiaInteresProducer:

    @staticmethod
    def get(tipo: str) -> EstrategiaInteres:
        tipo = tipo.lower().strip()
        if tipo == "fijo":
            return InteresEstrategiaFijo()
        elif tipo == "variable":
            return InteresEstrategiaVariable()
        else:
            raise ValueError(
                f"Tipo de interés no soportado: '{tipo}'. Válidos: fijo, variable"
            )

    @staticmethod
    def listar() -> list:
        return ["fijo", "variable"]


# =============================================================================
# CONTEXTO — Prestamo
# =============================================================================

class Prestamo:

    def __init__(
        self,
        documento_usuario: str,
        numero_cuenta: str,
        monto: float,
        num_cuotas: int,
        tasa_anual: float,
        estrategia: EstrategiaInteres,
    ):
        self.id              = str(uuid.uuid4())[:8].upper()
        self.documento       = documento_usuario
        self.numero_cuenta   = numero_cuenta
        self.monto           = monto
        self.num_cuotas      = num_cuotas
        self.tasa_anual      = tasa_anual
        self._estrategia     = estrategia

        self.cuota_mensual   = self._estrategia.calcular_cuota(monto, tasa_anual, num_cuotas)
        self.total_intereses = self._estrategia.calcular_total_intereses(monto, tasa_anual, num_cuotas)
        self.total_a_pagar   = round(monto + self.total_intereses, 2)

        self.cuotas_pagadas  = 0
        self.total_pagado    = 0.0
        self.pagos           = []
        self.estado          = "activo"
        self.fecha_creacion  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        Logger.get_instancia().log(
            f"[STRATEGY] Préstamo {self.id} creado — "
            f"Estrategia: {self._estrategia.get_nombre()} | "
            f"Monto: ${monto:,.2f} | Cuotas: {num_cuotas} | "
            f"Cuota/mes: ${self.cuota_mensual:,.2f} | "
            f"Total intereses: ${self.total_intereses:,.2f}",
            nivel="SUCCESS"
        )

    # ── Strategy ──────────────────────────────────────────────────────────────

    def set_estrategia(self, nueva_estrategia: EstrategiaInteres):
        self._estrategia     = nueva_estrategia
        self.cuota_mensual   = self._estrategia.calcular_cuota(
            self.monto, self.tasa_anual, self.num_cuotas)
        self.total_intereses = self._estrategia.calcular_total_intereses(
            self.monto, self.tasa_anual, self.num_cuotas)
        self.total_a_pagar   = round(self.monto + self.total_intereses, 2)

    def get_estrategia(self) -> EstrategiaInteres:
        return self._estrategia

    # ── MÉTODO FALTANTE — requerido por api.py y seed_prestamos.py ────────────
    def calcular_monto_real_cuota(self) -> float:
        """
        Calcula cuánto hay que cobrar realmente por la siguiente cuota,
        descontando los abonos libres que ya se hicieron y que exceden
        las cuotas formales ya pagadas.

        Lógica:
          - cubierto_formal = cuota_mensual × cuotas_pagadas
            (lo que debería haberse pagado en cuotas formales hasta ahora)
          - excedente = total_pagado - cubierto_formal
            (abonos libres que ya cubrieron parte de la siguiente cuota)
          - monto_real = max(0, cuota_mensual - excedente)

        Si el excedente >= cuota_mensual, la cuota ya está cubierta → retorna 0.0
        y el endpoint la registra sin debitar nada.
        """
        cubierto_formal = round(self.cuota_mensual * self.cuotas_pagadas, 2)
        excedente       = round(max(0.0, self.total_pagado - cubierto_formal), 2)
        monto_real      = round(max(0.0, self.cuota_mensual - excedente), 2)
        return monto_real

    # ── Pagos ─────────────────────────────────────────────────────────────────

    def registrar_pago(self, monto_pago: float) -> dict:
        """
        Registra el pago de una cuota formal.
        monto_pago es el monto real cobrado (puede ser 0 si abonos ya lo cubrieron).
        """
        if self.estado == "pagado":
            return {"ok": False, "mensaje": "El préstamo ya está completamente pagado."}

        if self.cuotas_pagadas >= self.num_cuotas:
            self.estado = "pagado"
            return {"ok": False, "mensaje": "Todas las cuotas ya fueron canceladas."}

        self.cuotas_pagadas += 1
        self.total_pagado    = round(self.total_pagado + monto_pago, 2)

        # Calcular cuánto de esta cuota fue cubierto por abonos previos
        abonos_aplicados = round(self.cuota_mensual - monto_pago, 2) if monto_pago < self.cuota_mensual else 0.0

        pago = {
            "numero_cuota":    self.cuotas_pagadas,
            "tipo":            "cuota",
            "monto":           round(monto_pago, 2),
            "monto_cuota":     self.cuota_mensual,
            "abonos_aplicados": abonos_aplicados,
            "fecha":           datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cuotas_restantes": self.num_cuotas - self.cuotas_pagadas,
            "total_pagado":    self.total_pagado,
        }
        self.pagos.append(pago)

        if self.cuotas_pagadas >= self.num_cuotas:
            self.estado = "pagado"

        Logger.get_instancia().log(
            f"[STRATEGY] Pago cuota {self.cuotas_pagadas}/{self.num_cuotas} "
            f"del préstamo {self.id} — cobrado: ${monto_pago:,.2f} "
            f"| abonos aplicados: ${abonos_aplicados:,.2f} "
            f"| Estado: {self.estado}",
            nivel="SUCCESS"
        )
        return {"ok": True, "pago": pago, "estado": self.estado}

    def registrar_abono_manual(self, monto_abono: float) -> dict:
        """
        Registra un abono libre (cualquier monto) al préstamo.
        No incrementa cuotas_pagadas — solo acumula en total_pagado.
        Si total_pagado >= total_a_pagar, cierra el préstamo automáticamente.
        """
        if self.estado == "pagado":
            return {"ok": False, "mensaje": "El préstamo ya está completamente pagado."}
        if monto_abono <= 0:
            return {"ok": False, "mensaje": "El monto del abono debe ser positivo."}

        self.total_pagado = round(self.total_pagado + monto_abono, 2)
        pago = {
            "numero_cuota": f"Abono #{len(self.pagos) + 1}",
            "tipo":         "manual",
            "monto":        round(monto_abono, 2),
            "fecha":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_pagado": self.total_pagado,
        }
        self.pagos.append(pago)

        if self.total_pagado >= self.total_a_pagar:
            self.estado = "pagado"

        Logger.get_instancia().log(
            f"[STRATEGY] Abono manual ${monto_abono:,.2f} al préstamo {self.id} "
            f"| Acumulado: ${self.total_pagado:,.2f} / ${self.total_a_pagar:,.2f} "
            f"| Estado: {self.estado}",
            nivel="SUCCESS"
        )
        return {
            "ok":           True,
            "pago":         pago,
            "estado":       self.estado,
            "total_pagado": self.total_pagado,
            "total_a_pagar": self.total_a_pagar,
        }

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "documento":        self.documento,
            "numero_cuenta":    self.numero_cuenta,
            "monto":            self.monto,
            "num_cuotas":       self.num_cuotas,
            "tasa_anual":       self.tasa_anual,
            "tipo_interes":     self._estrategia.get_tipo(),
            "nombre_interes":   self._estrategia.get_nombre(),
            "cuota_mensual":    self.cuota_mensual,
            "total_intereses":  self.total_intereses,
            "total_a_pagar":    self.total_a_pagar,
            "cuotas_pagadas":   self.cuotas_pagadas,
            "cuotas_restantes": self.num_cuotas - self.cuotas_pagadas,
            "total_pagado":     round(self.total_pagado, 2),
            "estado":           self.estado,
            "fecha_creacion":   self.fecha_creacion,
            "pagos":            self.pagos,
        }


# =============================================================================
# GESTOR DE PRÉSTAMOS — Singleton
# =============================================================================

class GestorPrestamos:
    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        self._prestamos: list = []

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = GestorPrestamos()
        return cls._instancia

    def agregar(self, prestamo: Prestamo):
        self._prestamos.append(prestamo)

    def get_todos(self) -> list:
        return self._prestamos.copy()

    def get_por_id(self, prestamo_id: str):
        for p in self._prestamos:
            if p.id == prestamo_id:
                return p
        return None

    def get_por_documento(self, documento: str) -> list:
        return [p for p in self._prestamos if p.documento == documento]
