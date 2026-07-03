from logger import Logger
from transaccion import Transaccion


# =============================================================================
# PATRÓN FACADE — OperacionFacade
#
# Proporciona una interfaz simplificada para todas las operaciones bancarias
# (depósito, retiro, transferencia, consulta de saldo e historial).
#
# CAMBIOS con la incorporación del patrón Composite (Semana 10):
#   - consultar_saldos_usuario() ya no itera manualmente sobre las cuentas.
#     Delega directamente al Composite del usuario buscando sus cuentas como
#     ComponenteBancario y llamando get_saldo_total().
#   - Se agregan dos nuevos métodos que solo el Composite hace posibles:
#       · consultar_saldo_sucursal(nombre_sucursal)
#       · consultar_saldo_banco()
#     Antes eran imposibles sin iterar manualmente. Ahora son una sola llamada.
#
# El cliente (main.py) solo llama:
#   facade.depositar(numero_cuenta, monto, canal)
#   facade.retirar(numero_cuenta, monto, canal)
#   facade.transferir(numero_origen, numero_destino, monto, canal)
#   facade.consultar_cuenta(numero_cuenta)
#   facade.consultar_saldos_usuario(documento)
#   facade.consultar_saldo_sucursal(nombre_sucursal)   ← NUEVO (Composite)
#   facade.consultar_saldo_banco()                     ← NUEVO (Composite)
#   facade.listar_arbol_banco()                        ← NUEVO (Composite)
# =============================================================================


class OperacionFacade:
    """
    Fachada para operaciones bancarias.

    Recibe una referencia al objeto Banco (que contiene usuarios y cuentas)
    y coordina internamente los subsistemas: búsqueda de cuentas, validación
    de existencia y delegación a Transaccion.procesar().

    El cliente nunca instancia Transaccion ni llama a buscar_cuenta_por_numero
    directamente — esa lógica vive aquí.
    """

    def __init__(self, banco):
        self._banco  = banco
        self._logger = Logger.get_instancia()

    # ── Búsqueda interna ─────────────────────────────────────────────────────

    def _obtener_cuenta(self, numero: str):
        """
        Busca una cuenta por número y loguea un error si no existe.
        Retorna la cuenta o None.
        """
        cuenta = self._banco.buscar_cuenta_por_numero(numero)
        if not cuenta:
            self._logger.log(
                f"❌ Cuenta {numero} no encontrada.",
                nivel="ERROR"
            )
        return cuenta

    # ── Operaciones principales (sin cambios) ─────────────────────────────────

    def depositar(self, numero_cuenta: str, monto: float, canal: str) -> bool:
        """
        Realiza un depósito sobre la cuenta indicada.
        Retorna True si fue exitoso, False en caso contrario.
        """
        cuenta = self._obtener_cuenta(numero_cuenta)
        if not cuenta:
            return False

        self._logger.log(
            f"[FACADE] Depósito → cuenta: {numero_cuenta} | "
            f"monto: ${monto:,.2f} | canal: {canal}",
            nivel="INFO"
        )
        exito = Transaccion.procesar(
            cuenta_origen=cuenta,
            monto=monto,
            canal=canal,
            tipo="deposito"
        )
        if exito:
            self._logger.log(
                f"✅ Depósito completado. Saldo actual: ${cuenta.saldo:,.2f}",
                nivel="SUCCESS"
            )
        else:
            self._logger.log(
                "❌ Depósito no realizado (validación o fraude).",
                nivel="ERROR"
            )
        return exito

    def retirar(self, numero_cuenta: str, monto: float, canal: str) -> bool:
        """
        Realiza un retiro sobre la cuenta indicada.
        Retorna True si fue exitoso, False en caso contrario.
        """
        cuenta = self._obtener_cuenta(numero_cuenta)
        if not cuenta:
            return False

        self._logger.log(
            f"[FACADE] Retiro → cuenta: {numero_cuenta} | "
            f"monto: ${monto:,.2f} | canal: {canal}",
            nivel="INFO"
        )
        exito = Transaccion.procesar(
            cuenta_origen=cuenta,
            monto=monto,
            canal=canal,
            tipo="retiro"
        )
        if exito:
            self._logger.log(
                f"✅ Retiro completado. Saldo actual: ${cuenta.saldo:,.2f}",
                nivel="SUCCESS"
            )
        else:
            self._logger.log(
                "❌ Retiro no realizado (saldo insuficiente, validación o fraude).",
                nivel="ERROR"
            )
        return exito

    def transferir(
        self,
        numero_origen: str,
        numero_destino: str,
        monto: float,
        canal: str
    ) -> bool:
        """
        Realiza una transferencia entre dos cuentas.
        Valida que ambas existan antes de procesar.
        Retorna True si fue exitosa, False en caso contrario.
        """
        cuenta_origen  = self._obtener_cuenta(numero_origen)
        cuenta_destino = self._obtener_cuenta(numero_destino)

        if not cuenta_origen or not cuenta_destino:
            return False

        self._logger.log(
            f"[FACADE] Transferencia → origen: {numero_origen} | "
            f"destino: {numero_destino} | monto: ${monto:,.2f} | canal: {canal}",
            nivel="INFO"
        )
        exito = Transaccion.procesar(
            cuenta_origen=cuenta_origen,
            monto=monto,
            canal=canal,
            cuenta_destino=cuenta_destino,
            tipo="transferencia"
        )
        if exito:
            self._logger.log(
                f"✅ Transferencia completada.\n"
                f"   Saldo origen  ({numero_origen}):  ${cuenta_origen.saldo:,.2f}\n"
                f"   Saldo destino ({numero_destino}): ${cuenta_destino.saldo:,.2f}",
                nivel="SUCCESS"
            )
        else:
            self._logger.log(
                "❌ Transferencia no realizada (validación, fraude o canal no permitido).",
                nivel="ERROR"
            )
        return exito

    # ── Consultas ─────────────────────────────────────────────────────────────

    def consultar_cuenta(self, numero_cuenta: str):
        """
        Muestra saldo, tipo y últimos 5 movimientos de una cuenta.
        Retorna la cuenta si existe, None si no.
        """
        cuenta = self._obtener_cuenta(numero_cuenta)
        if not cuenta:
            return None

        self._logger.log(
            f"\n=== INFORMACIÓN CUENTA {cuenta.numero} ({cuenta.tipo}) ===",
            nivel="INFO"
        )
        self._logger.log(f"Saldo actual:      ${cuenta.saldo:,.2f}")
        self._logger.log(f"Total movimientos: {len(cuenta.transacciones)}")

        if cuenta.transacciones:
            self._logger.log("Últimos movimientos:")
            for t in cuenta.transacciones[-5:]:
                self._logger.log(
                    f"  {t['fecha']} | {t['tipo'].upper():15} | "
                    f"${t['monto']:>12,.2f} | Canal: {t['canal']:6} | "
                    f"Saldo final: ${t['saldo_final']:,.2f}"
                )
        else:
            self._logger.log("No hay movimientos aún.")

        return cuenta

    def consultar_saldos_usuario(self, documento: str):
        """
        Muestra todas las cuentas y el saldo total de un usuario.

        ANTES (iteración manual):
            total = 0.0
            for cuenta in usuario.cuentas:
                total += cuenta.saldo

        AHORA (Composite):
            Cada cuenta es un ComponenteBancario. Se llama get_saldo_total()
            sobre cada una y se acumula — la interfaz común hace el trabajo.
            Si en el futuro una "cuenta" fuera en realidad un grupo de
            subcuentas (otro Compuesto), este código no cambiaría en absoluto.

        Retorna el total o None si el usuario no existe.
        """
        usuario = self._banco.buscar_usuario_por_documento(documento)
        if not usuario:
            self._logger.log("❌ Usuario no encontrado.", nivel="ERROR")
            return None

        if not usuario.cuentas:
            self._logger.log(
                f"{usuario.nombre} no tiene cuentas registradas.",
                nivel="INFO"
            )
            return 0.0

        self._logger.log(
            f"\n=== SALDOS TOTALES — {usuario.nombre.upper()} ===",
            nivel="INFO"
        )

        # ── COMPOSITE: cada cuenta expone get_saldo_total() ──────────────────
        total = 0.0
        for cuenta in usuario.cuentas:
            subtotal = cuenta.get_saldo_total()          # ← antes: cuenta.saldo
            self._logger.log(
                f"  - {cuenta.get_nombre()}: ${subtotal:,.2f}"  # ← antes: cuenta.numero/tipo manual
            )
            total += subtotal
        # ─────────────────────────────────────────────────────────────────────

        self._logger.log(f"{'─'*40}")
        self._logger.log(f"  TOTAL: ${total:,.2f}")
        self._logger.log("=" * 40)
        return total

    def consultar_saldo_sucursal(self, nombre_sucursal: str):
        """
        NUEVO — habilitado por el Composite.
        Muestra el saldo total consolidado de una sucursal y lista sus cuentas.
        Antes era imposible sin un for manual sobre todas las cuentas.
        Ahora es una sola llamada a sucursal.get_saldo_total().

        Retorna el total de la sucursal o None si no se encontró.
        """
        sucursal = next(
            (s for s in self._banco.sucursales
             if s.get_nombre().lower() == nombre_sucursal.lower()),
            None
        )
        if not sucursal:
            self._logger.log(
                f"❌ Sucursal '{nombre_sucursal}' no encontrada.",
                nivel="ERROR"
            )
            return None

        self._logger.log(
            f"\n=== SALDO CONSOLIDADO — SUCURSAL {sucursal.get_nombre().upper()} ===",
            nivel="INFO"
        )

        # ── COMPOSITE: listar delega recursivamente a cada Cuenta hija ───────
        sucursal.listar(nivel=1)
        # ─────────────────────────────────────────────────────────────────────

        total = sucursal.get_saldo_total()
        self._logger.log(f"{'─'*40}")
        self._logger.log(f"  TOTAL SUCURSAL: ${total:,.2f}")
        self._logger.log("=" * 40)
        return total

    def consultar_saldo_banco(self):
        """
        NUEVO — habilitado por el Composite.
        Muestra el saldo total consolidado de todo el banco en una sola llamada.
        Antes requería un doble for (sucursales → cuentas) disperso en el código.
        Ahora es banco.get_saldo_total() — la recursión del Composite lo resuelve.

        Retorna el total consolidado del banco.
        """
        self._logger.log(
            "\n=== SALDO CONSOLIDADO — BANCO COMPLETO ===",
            nivel="INFO"
        )
        total = self._banco.get_saldo_total()   # ← Composite raíz
        self._logger.log(f"  TOTAL BANCO: ${total:,.2f}", nivel="INFO")
        self._logger.log("=" * 40)
        return total

    def listar_arbol_banco(self):
        """
        NUEVO — habilitado por el Composite.
        Imprime el árbol completo: Banco → Sucursales → Cuentas,
        con saldos en cada nivel. Una sola llamada genera todo el reporte.

        Retorna None (operación de visualización pura).
        """
        self._logger.log(
            "\n=== ÁRBOL ESTRUCTURAL DEL BANCO [COMPOSITE] ===",
            nivel="INFO"
        )
        self._banco.listar()   # ← delega recursivamente por todo el árbol
        self._logger.log("=" * 50)