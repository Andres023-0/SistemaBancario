from datetime import datetime, timedelta
from logger import Logger
from prestamo_strategy import EstrategiaInteresProducer, GestorPrestamos, Prestamo


# =============================================================================
# SEED PRÉSTAMOS — 7 usuarios con préstamos variados
#
# Diseñado para demostrar el patrón Strategy con casos reales:
#   - Mezcla de interés fijo y variable
#   - Montos, plazos y tasas diferentes (Colombia, 2025)
#   - Algunos con pagos ya realizados para ver progreso en la tabla
#   - Fechas de creación distribuidas en los últimos 6 meses
#
# Préstamos:
#   1. Juan Niño        → Fijo   | $8.000.000  | 24 cuotas | 18% EA  (libre inversión)
#   2. Valentina Torres → Fijo   | $15.000.000 | 36 cuotas | 16% EA  (vehículo)
#   3. Andrés Gómez     → Variable| $5.000.000 | 12 cuotas | 16.5% EA (consumo)
#   4. Camila Moreno    → Fijo   | $3.000.000  | 6 cuotas  | 20% EA  (emergencia)
#   5. Mateo Herrera    → Variable| $20.000.000| 48 cuotas | 14% EA  (empresarial)
#   6. Felipe Castillo  → Fijo   | $10.000.000 | 18 cuotas | 17.5% EA (libre inversión)
#   7. Isabella Díaz    → Variable| $6.500.000 | 24 cuotas | 16.5% EA (educación)
# =============================================================================

PRESTAMOS_SEED = [
    {
        "nombre":        "Juan Niño",
        "documento":     "1234567890",
        "numero_cuenta": "1001",
        "monto":         8_000_000.0,
        "num_cuotas":    24,
        "tasa_anual":    18.0,
        "tipo":          "fijo",
        "desc":          "Libre inversión",
        "cuotas_pagar":  5,      # ya pagó 5 cuotas
        "abono_libre":   150_000.0,  # más un abono libre
        "dias_atras":    150,
    },
    {
        "nombre":        "Valentina Torres",
        "documento":     "1010101010",
        "numero_cuenta": "1004",
        "monto":         15_000_000.0,
        "num_cuotas":    36,
        "tasa_anual":    16.0,
        "tipo":          "fijo",
        "desc":          "Crédito vehículo",
        "cuotas_pagar":  8,
        "abono_libre":   0,
        "dias_atras":    240,
    },
    {
        "nombre":        "Andrés Gómez",
        "documento":     "4040404040",
        "numero_cuenta": "1007",
        "monto":         5_000_000.0,
        "num_cuotas":    12,
        "tasa_anual":    16.5,
        "tipo":          "variable",
        "desc":          "Crédito de consumo",
        "cuotas_pagar":  3,
        "abono_libre":   300_000.0,
        "dias_atras":    90,
    },
    {
        "nombre":        "Camila Moreno",
        "documento":     "3030303030",
        "numero_cuenta": "1006",
        "monto":         3_000_000.0,
        "num_cuotas":    6,
        "tasa_anual":    20.0,
        "tipo":          "fijo",
        "desc":          "Crédito emergencia",
        "cuotas_pagar":  2,
        "abono_libre":   200_000.0,
        "dias_atras":    60,
    },
    {
        "nombre":        "Mateo Herrera",
        "documento":     "8080808080",
        "numero_cuenta": "1011",
        "monto":         20_000_000.0,
        "num_cuotas":    48,
        "tasa_anual":    14.0,
        "tipo":          "variable",
        "desc":          "Crédito empresarial",
        "cuotas_pagar":  2,
        "abono_libre":   0,
        "dias_atras":    60,
    },
    {
        "nombre":        "Felipe Castillo",
        "documento":     "1122334455",
        "numero_cuenta": "1013",
        "monto":         10_000_000.0,
        "num_cuotas":    18,
        "tasa_anual":    17.5,
        "tipo":          "fijo",
        "desc":          "Libre inversión",
        "cuotas_pagar":  4,
        "abono_libre":   500_000.0,
        "dias_atras":    120,
    },
    {
        "nombre":        "Isabella Díaz",
        "documento":     "7070707070",
        "numero_cuenta": "1010",
        "monto":         6_500_000.0,
        "num_cuotas":    24,
        "tasa_anual":    16.5,
        "tipo":          "variable",
        "desc":          "Crédito educación",
        "cuotas_pagar":  1,
        "abono_libre":   100_000.0,
        "dias_atras":    30,
    },
]


def _fecha_sim(dias_atras: int, offset_dias: int = 0) -> str:
    """Genera una fecha simulada para parchear registros históricos."""
    dt = datetime.now() - timedelta(days=dias_atras - offset_dias)
    return dt.replace(hour=10, minute=30, second=0).strftime("%Y-%m-%d %H:%M:%S")


def cargar_prestamos_seed(banco):
    """
    Crea y registra los 7 préstamos seed en el sistema.
    """
    logger  = Logger.get_instancia()
    gestor  = GestorPrestamos.get_instancia()

    logger.log("=" * 55, nivel="INFO")
    logger.log("[SEED-PRESTAMOS] Cargando préstamos de prueba...", nivel="INFO")

    # Debug: mostrar usuarios y cuentas disponibles
    logger.log(f"[SEED-PRESTAMOS] Usuarios en banco: {len(banco.usuarios)}", nivel="INFO")
    for u in banco.usuarios:
        nums = [c.numero for c in u.cuentas]
        logger.log(f"  - {u.nombre} | doc: {u.documento} | cuentas: {nums}", nivel="INFO")

    ok_count  = 0
    err_count = 0

    for datos in PRESTAMOS_SEED:
        try:
            # Buscar cuenta del usuario
            cuenta = banco.buscar_cuenta_por_numero(datos["numero_cuenta"])
            if not cuenta:
                logger.log(
                    f"[SEED-PRESTAMOS] ⚠ Cuenta {datos['numero_cuenta']} NO encontrada "
                    f"para {datos['nombre']} — omitido.",
                    nivel="WARNING"
                )
                err_count += 1
                continue

            usuario = banco.buscar_usuario_por_documento(datos["documento"])
            if not usuario:
                logger.log(
                    f"[SEED-PRESTAMOS] ⚠ Usuario doc={datos['documento']} NO encontrado — omitido.",
                    nivel="WARNING"
                )
                err_count += 1
                continue

            logger.log(
                f"[SEED-PRESTAMOS] Creando préstamo: {datos['nombre']} | "
                f"cuenta: {datos['numero_cuenta']} | monto: ${datos['monto']:,.0f}",
                nivel="INFO"
            )

            # Crear préstamo con la estrategia correcta (STRATEGY)
            estrategia = EstrategiaInteresProducer.get(datos["tipo"])
            prestamo   = Prestamo(
                documento_usuario = datos["documento"],
                numero_cuenta     = datos["numero_cuenta"],
                monto             = datos["monto"],
                num_cuotas        = datos["num_cuotas"],
                tasa_anual        = datos["tasa_anual"],
                estrategia        = estrategia,
            )

            # Parchear fecha de creación del préstamo
            prestamo.fecha_creacion = _fecha_sim(datos["dias_atras"])

            # Acreditar monto en la cuenta (simular desembolso)
            cuenta.depositar(datos["monto"], "web")

            # Simular cuotas ya pagadas
            for i in range(datos["cuotas_pagar"]):
                monto_real = prestamo.calcular_monto_real_cuota()
                if monto_real > 0 and cuenta.saldo >= monto_real:
                    cuenta.retirar(monto_real, "web")
                resultado = prestamo.registrar_pago(monto_real)
                if resultado["ok"] and prestamo.pagos:
                    # Parchear fecha del pago: un mes por cuota
                    offset = datos["dias_atras"] - ((i + 1) * 30)
                    prestamo.pagos[-1]["fecha"] = _fecha_sim(max(1, offset))

            # Aplicar abono libre si hay
            if datos["abono_libre"] > 0 and cuenta.saldo >= datos["abono_libre"]:
                cuenta.retirar(datos["abono_libre"], "web")
                prestamo.registrar_abono_manual(datos["abono_libre"])
                if prestamo.pagos:
                    prestamo.pagos[-1]["fecha"] = _fecha_sim(5)  # hace 5 días

            # Registrar en el gestor
            gestor.agregar(prestamo)
            ok_count += 1

            logger.log(
                f"[SEED-PRESTAMOS] ✅ {datos['nombre']} | {datos['desc']} | "
                f"{datos['tipo'].upper()} | ${datos['monto']:,.0f} | "
                f"{datos['num_cuotas']} cuotas | "
                f"Cuota: ${prestamo.cuota_mensual:,.0f} | "
                f"Pagadas: {prestamo.cuotas_pagadas}/{prestamo.num_cuotas}",
                nivel="SUCCESS"
            )

        except Exception as e:
            logger.log(
                f"[SEED-PRESTAMOS] ❌ Error creando préstamo para {datos['nombre']}: {e}",
                nivel="ERROR"
            )
            err_count += 1

    logger.log("=" * 55, nivel="INFO")
    logger.log(f"[SEED-PRESTAMOS] ✅ Préstamos creados : {ok_count}", nivel="INFO")
    logger.log(f"[SEED-PRESTAMOS] ⚠  Errores          : {err_count}", nivel="INFO")
    logger.log("=" * 55, nivel="INFO")
