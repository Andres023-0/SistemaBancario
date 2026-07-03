from logger import Logger
from usuario_facade import UsuarioFacade
from datetime import datetime, timedelta
import random


# =============================================================================
# SEED — Datos de prueba precargados
#
# 13 usuarios con KYC verificado, una cuenta cada uno,
# distribuidos en las 3 sucursales.
#
# Los movimientos se distribuyen en los últimos 30 días
# para que los gráficos de actividad diaria muestren curvas reales.
#
# Sucursal 1 → Bucaramanga Centro  (índice 1)
# Sucursal 2 → Bucaramanga Norte   (índice 2)
# Sucursal 3 → Floridablanca       (índice 3)
# =============================================================================

USUARIOS_PRUEBA = [
    {"nombre": "Juan Niño",       "documento": "1234567890", "celular": "+573001111111", "correo": "Juan@bancouts.com",
     "cuenta": {"numero": "1001", "tipo": "corriente", "saldo_inicial": 5_000_000.0, "indice_sucursal": 1}},
    {"nombre": "Brayan Cañas",    "documento": "9876543210", "celular": "+573002222222", "correo": "Brayan@bancouts.com",
     "cuenta": {"numero": "1002", "tipo": "ahorros",   "saldo_inicial": 4_000_000.0, "indice_sucursal": 2}},
    {"nombre": "Pedro Ochoa",     "documento": "7548162548", "celular": "+573015247859", "correo": "Pedro@bancouts.com",
     "cuenta": {"numero": "1003", "tipo": "ahorros",   "saldo_inicial": 3_000_000.0, "indice_sucursal": 3}},
    {"nombre": "Valentina Torres","documento": "1010101010", "celular": "+573003333333", "correo": "valentina@bancouts.com",
     "cuenta": {"numero": "1004", "tipo": "ahorros",   "saldo_inicial": 6_000_000.0, "indice_sucursal": 1}},
    {"nombre": "Sebastián Ruiz",  "documento": "2020202020", "celular": "+573004444444", "correo": "sebastian@bancouts.com",
     "cuenta": {"numero": "1005", "tipo": "corriente", "saldo_inicial": 4_500_000.0, "indice_sucursal": 2}},
    {"nombre": "Camila Moreno",   "documento": "3030303030", "celular": "+573005555555", "correo": "camila@bancouts.com",
     "cuenta": {"numero": "1006", "tipo": "ahorros",   "saldo_inicial": 5_500_000.0, "indice_sucursal": 3}},
    {"nombre": "Andrés Gómez",    "documento": "4040404040", "celular": "+573006666666", "correo": "andres@bancouts.com",
     "cuenta": {"numero": "1007", "tipo": "corriente", "saldo_inicial": 7_000_000.0, "indice_sucursal": 1}},
    {"nombre": "Luisa Fernández", "documento": "5050505050", "celular": "+573007777777", "correo": "luisa@bancouts.com",
     "cuenta": {"numero": "1008", "tipo": "ahorros",   "saldo_inicial": 3_800_000.0, "indice_sucursal": 2}},
    {"nombre": "Carlos Vargas",   "documento": "6060606060", "celular": "+573008888888", "correo": "carlos@bancouts.com",
     "cuenta": {"numero": "1009", "tipo": "corriente", "saldo_inicial": 5_200_000.0, "indice_sucursal": 3}},
    {"nombre": "Isabella Díaz",   "documento": "7070707070", "celular": "+573009999999", "correo": "isabella@bancouts.com",
     "cuenta": {"numero": "1010", "tipo": "ahorros",   "saldo_inicial": 4_100_000.0, "indice_sucursal": 1}},
    {"nombre": "Mateo Herrera",   "documento": "8080808080", "celular": "+573010101010", "correo": "mateo@bancouts.com",
     "cuenta": {"numero": "1011", "tipo": "corriente", "saldo_inicial": 6_500_000.0, "indice_sucursal": 2}},
    {"nombre": "Sara Ospina",     "documento": "9090909090", "celular": "+573011111111", "correo": "sara@bancouts.com",
     "cuenta": {"numero": "1012", "tipo": "ahorros",   "saldo_inicial": 3_500_000.0, "indice_sucursal": 3}},
    {"nombre": "Felipe Castillo", "documento": "1122334455", "celular": "+573012121212", "correo": "felipe@bancouts.com",
     "cuenta": {"numero": "1013", "tipo": "corriente", "saldo_inicial": 8_000_000.0, "indice_sucursal": 1}},
]


# =============================================================================
# MOVIMIENTOS DE PRUEBA
# Tupla: (origen, destino_o_None, monto, canal, tipo, dias_atras)
# dias_atras: 0 = hoy, 29 = hace 29 días
# =============================================================================

MOVIMIENTOS_PRUEBA = [
    # ── Semana 1 (hace 29-22 días) ─────────────────────────
    ("1001", None,    500_000, "web",    "deposito",       29),
    ("1002", None,    300_000, "movil",  "deposito",       29),
    ("1003", None,    200_000, "web",    "deposito",       28),
    ("1004", None,    800_000, "web",    "deposito",       28),
    ("1007", None,    600_000, "movil",  "deposito",       27),
    ("1013", None,  1_000_000, "web",    "deposito",       27),
    ("1005", None,    250_000, "cajero", "deposito",       26),
    ("1008", None,    180_000, "cajero", "deposito",       26),
    ("1001", None,    100_000, "cajero", "retiro",         25),
    ("1004", None,    200_000, "cajero", "retiro",         25),
    ("1001", "1002",  200_000, "web",    "transferencia",  24),
    ("1007", "1005",  400_000, "web",    "transferencia",  24),
    ("1013", "1008",  500_000, "web",    "transferencia",  23),
    ("1011", "1001",  300_000, "movil",  "transferencia",  23),
    ("1006", None,    400_000, "web",    "deposito",       22),
    ("1009", None,    350_000, "movil",  "deposito",       22),

    # ── Semana 2 (hace 21-15 días) ─────────────────────────
    ("1010", None,    250_000, "web",    "deposito",       21),
    ("1012", None,    180_000, "cajero", "deposito",       21),
    ("1002", None,    200_000, "cajero", "deposito",       20),
    ("1003", None,    150_000, "web",    "deposito",       20),
    ("1005", None,     80_000, "cajero", "retiro",         19),
    ("1006", None,    150_000, "cajero", "retiro",         19),
    ("1004", "1006",  300_000, "web",    "transferencia",  18),
    ("1009", "1007",  220_000, "movil",  "transferencia",  18),
    ("1001", None,    300_000, "web",    "deposito",       17),
    ("1007", None,    500_000, "web",    "deposito",       17),
    ("1011", None,    700_000, "web",    "deposito",       16),
    ("1013", None,    750_000, "movil",  "deposito",       16),
    ("1002", None,     50_000, "cajero", "retiro",         15),
    ("1009", None,    250_000, "cajero", "retiro",         15),

    # ── Semana 3 (hace 14-8 días) ──────────────────────────
    ("1004", None,    400_000, "movil",  "deposito",       14),
    ("1005", None,    150_000, "web",    "deposito",       14),
    ("1008", None,    120_000, "movil",  "deposito",       13),
    ("1010", None,    250_000, "web",    "deposito",       13),
    ("1007", None,    300_000, "cajero", "retiro",         12),
    ("1011", None,    400_000, "cajero", "retiro",         12),
    ("1004", "1009",  250_000, "movil",  "transferencia",  11),
    ("1013", "1012",  300_000, "movil",  "transferencia",  11),
    ("1006", "1001",  180_000, "web",    "transferencia",  10),
    ("1012", "1011",  100_000, "web",    "transferencia",  10),
    ("1001", None,    200_000, "movil",  "deposito",        9),
    ("1003", None,    100_000, "web",    "deposito",        9),
    ("1006", None,    600_000, "web",    "deposito",        8),
    ("1009", None,    700_000, "web",    "deposito",        8),

    # ── Semana 4 (hace 7-1 días) ───────────────────────────
    ("1002", None,    200_000, "movil",  "deposito",        7),
    ("1005", None,    150_000, "web",    "deposito",        7),
    ("1010", None,    350_000, "movil",  "deposito",        6),
    ("1012", None,     80_000, "cajero", "deposito",        6),
    ("1003", None,     30_000, "cajero", "retiro",          5),
    ("1008", None,     40_000, "cajero", "retiro",          5),
    ("1007", "1008",  400_000, "web",    "transferencia",   4),
    ("1005", "1006",  120_000, "web",    "transferencia",   4),
    ("1008", "1009",  150_000, "movil",  "transferencia",   3),
    ("1011", "1013",  350_000, "web",    "transferencia",   3),
    ("1013", None,    400_000, "cajero", "retiro",          2),
    ("1001", None,    300_000, "web",    "deposito",        2),
    ("1004", "1005",  300_000, "web",    "transferencia",   1),
    ("1013", "1002",  400_000, "web",    "transferencia",   1),

    # ── Hoy (dia 0) ────────────────────────────────────────
    ("1001", None,    150_000, "web",    "deposito",        0),
    ("1007", None,    400_000, "web",    "deposito",        0),
    ("1004", None,    200_000, "movil",  "deposito",        0),
    ("1011", None,    300_000, "web",    "deposito",        0),
    ("1002", None,    100_000, "cajero", "retiro",          0),
    ("1006", None,    100_000, "cajero", "retiro",          0),
    ("1013", "1003",  200_000, "web",    "transferencia",   0),
    ("1009", "1010",  180_000, "movil",  "transferencia",   0),
]


def _fecha_simulada(dias_atras: int) -> str:
    """Genera timestamp con día correcto y hora aleatoria."""
    hora    = random.randint(7, 19)
    minuto  = random.randint(0, 59)
    segundo = random.randint(0, 59)
    dt = datetime.now() - timedelta(days=dias_atras)
    dt = dt.replace(hour=hora, minute=minuto, second=segundo, microsecond=0)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _ejecutar_movimiento(banco, origen_num, destino_num, monto, canal, tipo, dias_atras):
    """
    Ejecuta el movimiento directamente sobre la cuenta (sin DetectorFraude)
    y luego parchea la fecha del registro para distribuirlo en el tiempo.
    """
    cuenta_origen = banco.buscar_cuenta_por_numero(origen_num)
    if not cuenta_origen:
        return False, f"Cuenta origen {origen_num} no encontrada"

    idx_antes = len(cuenta_origen.transacciones)

    try:
        if tipo == "deposito":
            cuenta_origen.depositar(monto, canal)

        elif tipo == "retiro":
            cuenta_origen.retirar(monto, canal)

        elif tipo == "transferencia":
            cuenta_destino = banco.buscar_cuenta_por_numero(destino_num)
            if not cuenta_destino:
                return False, f"Cuenta destino {destino_num} no encontrada"
            cuenta_origen.transferir(cuenta_destino, monto, canal)

    except Exception as e:
        return False, str(e)

    # Parchear fecha en los nuevos registros del origen
    fecha_sim = _fecha_simulada(dias_atras)
    for i in range(idx_antes, len(cuenta_origen.transacciones)):
        cuenta_origen.transacciones[i]["fecha"] = fecha_sim

    # Parchear también el depósito en cuenta destino (transferencias)
    if tipo == "transferencia" and destino_num:
        cuenta_destino = banco.buscar_cuenta_por_numero(destino_num)
        if cuenta_destino and cuenta_destino.transacciones:
            cuenta_destino.transacciones[-1]["fecha"] = fecha_sim

    return True, "ok"


def cargar_datos_prueba(banco):
    """
    Registra usuarios, crea cuentas y ejecuta movimientos
    distribuidos en los últimos 30 días.
    """
    logger   = Logger.get_instancia()
    u_facade = UsuarioFacade(banco)

    logger.log("=" * 55, nivel="INFO")
    logger.log("[SEED] Cargando usuarios y cuentas...", nivel="INFO")

    for datos in USUARIOS_PRUEBA:
        doc = datos["documento"]
        u_facade.registrar_usuario(
            nombre    = datos["nombre"],
            documento = doc,
            celular   = datos["celular"],
            correo    = datos["correo"],
        )
        u_facade.verificar_kyc(doc)
        c = datos["cuenta"]
        u_facade.crear_cuenta(
            documento        = doc,
            numero_cuenta    = c["numero"],
            tipo             = c["tipo"],
            saldo_inicial    = c["saldo_inicial"],
            indice_sucursal  = c["indice_sucursal"],
        )

    logger.log("[SEED] Usuarios listos. Ejecutando movimientos históricos...", nivel="INFO")

    ok_count  = 0
    err_count = 0

    for mov in MOVIMIENTOS_PRUEBA:
        origen, destino_num, monto, canal, tipo, dias_atras = mov
        exito, msg = _ejecutar_movimiento(
            banco, origen, destino_num, monto, canal, tipo, dias_atras
        )
        if exito:
            ok_count += 1
        else:
            logger.log(f"[SEED] ⚠ {tipo} {origen}: {msg}", nivel="WARNING")
            err_count += 1

    logger.log("=" * 55, nivel="INFO")
    logger.log("[SEED] ✅ Carga completa:", nivel="INFO")
    logger.log(f"  👥 Usuarios registrados  : {len(USUARIOS_PRUEBA)}", nivel="INFO")
    logger.log(f"  💳 Movimientos exitosos  : {ok_count}", nivel="INFO")
    logger.log(f"  ⚠️  Movimientos fallidos  : {err_count}", nivel="INFO")
    logger.log("", nivel="INFO")
    logger.log("  Cuentas disponibles:", nivel="INFO")
    for u in USUARIOS_PRUEBA:
        c = u["cuenta"]
        suc = ["", "Bga Centro", "Bga Norte", "Floridablanca"][c["indice_sucursal"]]
        logger.log(
            f"  👤 {u['nombre']:<20} | doc: {u['documento']} "
            f"| cuenta: {c['numero']} | sucursal: {suc}",
            nivel="INFO"
        )
    logger.log("=" * 55, nivel="INFO")