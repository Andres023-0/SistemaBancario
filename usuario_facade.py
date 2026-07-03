from logger import Logger
from usuario import Usuario
from cuenta_builder import CuentaBuilder
from sucursales_manager import SucursalesManager


# =============================================================================
# PATRÓN FACADE — UsuarioFacade
#
# Proporciona una interfaz simplificada para el ciclo de vida de usuarios:
# registro, verificación KYC, creación de cuentas y eliminación.
#
# El cliente (main.py) ya no necesita conocer:
#   - Usuario, CuentaBuilder, SucursalesManager directamente
#   - El orden correcto de pasos (crear → agregar al banco → KYC → cuenta)
#   - La lógica de limpieza en sucursales al eliminar un usuario
#
# main.py solo llama:
#   facade.registrar_usuario(nombre, documento, celular, correo)
#   facade.verificar_kyc(documento)
#   facade.crear_cuenta(documento, numero, tipo, saldo_inicial, indice_sucursal)
#   facade.eliminar_usuario(documento)
#   facade.listar_usuarios()
# =============================================================================


class UsuarioFacade:
    """
    Fachada para la gestión del ciclo de vida de usuarios.

    Recibe una referencia al objeto Banco y coordina internamente:
    Usuario, CuentaBuilder, SucursalesManager y la lógica de validación.
    El cliente no necesita conocer ninguno de esos subsistemas.
    """

    def __init__(self, banco):
        self._banco  = banco
        self._logger = Logger.get_instancia()

    # ── Búsqueda interna ─────────────────────────────────────────────────────

    def _obtener_usuario(self, documento: str):
        """
        Busca un usuario por documento y loguea error si no existe.
        Retorna el usuario o None.
        """
        usuario = self._banco.buscar_usuario_por_documento(documento)
        if not usuario:
            self._logger.log(
                f"❌ No se encontró ningún usuario con documento {documento}.",
                nivel="ERROR"
            )
        return usuario

    # ── Gestión de usuarios ───────────────────────────────────────────────────

    def registrar_usuario(
        self,
        nombre: str,
        documento: str,
        celular: str = "",
        correo: str  = ""
    ):
        """
        Crea un nuevo Usuario y lo registra en el Banco.
        Valida que el documento no esté duplicado antes de proceder.
        Retorna el usuario creado o None si ya existía.
        """
        if self._banco.buscar_usuario_por_documento(documento):
            self._logger.log(
                f"❌ Ya existe un usuario con documento {documento}.",
                nivel="WARNING"
            )
            return None

        self._logger.log(
            f"[FACADE] Registrando usuario: {nombre} | doc: {documento}",
            nivel="INFO"
        )
        nuevo_usuario = Usuario(nombre, documento, celular, correo)
        self._banco.agregar_usuario(nuevo_usuario)
        return nuevo_usuario

    def verificar_kyc(self, documento: str) -> bool:
        """
        Verifica el KYC del usuario identificado por documento.
        Retorna True si se verificó (o ya estaba verificado), False si no existe.
        """
        usuario = self._obtener_usuario(documento)
        if not usuario:
            return False

        self._logger.log(
            f"[FACADE] Verificando KYC → {usuario.nombre}",
            nivel="INFO"
        )
        usuario.verificar_kyc()
        return True

    def crear_cuenta(
        self,
        documento: str,
        numero_cuenta: str,
        tipo: str,
        saldo_inicial: float,
        indice_sucursal: int
    ):
        """
        Crea una cuenta bancaria y la asocia al usuario y sucursal indicados.

        Parámetros:
            documento       — documento del usuario dueño de la cuenta
            numero_cuenta   — número único de la nueva cuenta
            tipo            — 'corriente' o 'ahorros'
            saldo_inicial   — monto inicial en la cuenta
            indice_sucursal — índice base-1 de la sucursal en SucursalesManager

        Retorna la Cuenta creada o None si alguna validación falla.
        """
        # Validar usuario
        usuario = self._obtener_usuario(documento)
        if not usuario:
            return None

        if not usuario.verificado_kyc:
            self._logger.log(
                f"❌ El usuario {usuario.nombre} debe tener KYC verificado primero.",
                nivel="ERROR"
            )
            return None

        # Validar número de cuenta único
        if self._banco.buscar_cuenta_por_numero(numero_cuenta):
            self._logger.log(
                f"❌ El número de cuenta {numero_cuenta} ya existe en el sistema.",
                nivel="ERROR"
            )
            return None

        # Obtener sucursal
        sucursales = SucursalesManager.get_instancia().sucursales
        if not (1 <= indice_sucursal <= len(sucursales)):
            self._logger.log(
                f"❌ Índice de sucursal inválido: {indice_sucursal}. "
                f"Rango válido: 1-{len(sucursales)}.",
                nivel="ERROR"
            )
            return None

        sucursal = sucursales[indice_sucursal - 1]

        self._logger.log(
            f"[FACADE] Creando cuenta {numero_cuenta} ({tipo}) → "
            f"usuario: {usuario.nombre} | sucursal: {sucursal.nombre}",
            nivel="INFO"
        )

        try:
            cuenta = (
                CuentaBuilder()
                .numero(numero_cuenta)
                .tipo(tipo)
                .saldo_inicial(saldo_inicial)
                .asociar_usuario(usuario)
                .asociar_sucursal(sucursal)
                .build()
            )
            self._logger.log(
                f"✅ Cuenta {numero_cuenta} creada. Saldo inicial: ${cuenta.saldo:,.2f}",
                nivel="SUCCESS"
            )
            return cuenta

        except ValueError as e:
            self._logger.log(f"❌ Error al crear cuenta: {e}", nivel="ERROR")
            return None

    def eliminar_usuario(self, documento: str) -> bool:
        """
        Elimina un usuario del sistema con toda la limpieza necesaria:
        1. Desvincula sus cuentas de las sucursales (usando _cuentas interno,
            no la propiedad .cuentas que devuelve copia — BUG corregido).
        2. Elimina al usuario de la lista del banco.

        Retorna True si se eliminó correctamente, False si no se encontró.
        """
        usuario = self._obtener_usuario(documento)
        if not usuario:
            return False

        self._logger.log(
            f"[FACADE] Eliminando usuario: {usuario.nombre} | "
            f"doc: {documento} | cuentas: {len(usuario.cuentas)}",
            nivel="INFO"
        )

        try:
            # ── CORRECCIÓN DEL BUG ────────────────────────────────────────────
            # sucursal.cuentas es una @property que retorna una COPIA de _cuentas.
            # Llamar .remove() sobre esa copia no modifica el estado real.
            # La solución correcta es acceder a sucursal._cuentas directamente,
            # que es la lista interna mutable de la sucursal.
            # ─────────────────────────────────────────────────────────────────
            manager = SucursalesManager.get_instancia()
            for sucursal in manager.sucursales:
                for cuenta in usuario.cuentas:
                    if cuenta in sucursal._cuentas:
                        sucursal._cuentas.remove(cuenta)

            self._banco.usuarios.remove(usuario)

            self._logger.log(
                f"✅ Usuario '{usuario.nombre}' eliminado correctamente. "
                f"Se desvincularon {len(usuario.cuentas)} cuenta(s).",
                nivel="SUCCESS"
            )
            return True

        except Exception as e:
            self._logger.log(
                f"❌ Error inesperado durante la eliminación: {e}",
                nivel="ERROR"
            )
            return False

    # ── Consultas ─────────────────────────────────────────────────────────────

    def listar_usuarios(self):
        """
        Muestra todos los usuarios registrados con sus cuentas y datos de contacto.
        """
        if not self._banco.usuarios:
            self._logger.log(
                "Aún no hay usuarios registrados en el sistema.",
                nivel="INFO"
            )
            return

        self._logger.log(
            f"\n=== LISTADO COMPLETO DE USUARIOS ({len(self._banco.usuarios)}) ===",
            nivel="INFO"
        )
        for idx, usuario in enumerate(self._banco.usuarios, 1):
            kyc_str = "✅ Verificado" if usuario.verificado_kyc else "❌ Pendiente"
            self._logger.log(
                f"\n{idx}. 👤 {usuario.nombre} | Documento: {usuario.documento}"
            )
            self._logger.log(f"   KYC:     {kyc_str}")
            self._logger.log(f"   Celular: {usuario.celular or 'No registrado'}")
            self._logger.log(f"   Correo:  {usuario.correo  or 'No registrado'}")

            if usuario.cuentas:
                self._logger.log(f"   Cuentas ({len(usuario.cuentas)}):")
                for cuenta in usuario.cuentas:
                    self._logger.log(
                        f"     → {cuenta.numero} ({cuenta.tipo}) "
                        f"| Saldo: ${cuenta.saldo:,.2f}"
                    )
            else:
                self._logger.log("   Sin cuentas asociadas aún.")

        self._logger.log("=" * 50)

    def get_sucursales(self) -> list:
        """
        Retorna la lista de sucursales disponibles.
        Útil para que main.py muestre las opciones sin importar SucursalesManager.
        """
        return SucursalesManager.get_instancia().sucursales