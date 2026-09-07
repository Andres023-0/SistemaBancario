from logger import Logger
from auth_session import hash_password

class KYCNoVerificadoError(Exception):
    """Se lanza cuando se intenta operar sin KYC verificado"""
    pass

class Usuario:
    def __init__(self, nombre, documento, celular: str = "", correo: str = ""):
        self.nombre = nombre
        self.documento = documento
        self.celular = celular      # ← NUEVO: para notificaciones SMS (Adapter Móvil)
        self.correo = correo        # ← NUEVO: para notificaciones Email (Adapter Web)
        self.verificado_kyc = False
        self.cuentas = []
        self.password_hash = None   # ← FASE 2: antes no existía ningún control de acceso real

    # ── FASE 2: AUTENTICACIÓN ────────────────────────────────────────────────
    # Antes, "la contraseña" de un usuario era una fórmula inventada y
    # comparada solo en el JavaScript del login (nunca en el servidor).
    # Ahora el Usuario guarda un hash real y es el único que puede validarlo.

    def establecer_password(self, password: str):
        """Define (o cambia) la contraseña del usuario. Se guarda hasheada."""
        self.password_hash = hash_password(password)

    def verificar_password(self, password: str) -> bool:
        """Retorna True solo si la contraseña coincide con la registrada."""
        if not self.password_hash:
            return False
        return self.password_hash == hash_password(password)

    def verificar_kyc(self):
        if self.verificado_kyc:
            Logger.get_instancia().log(f"{self.nombre} ya tiene KYC verificado.", nivel="INFO")
            return
        self.verificado_kyc = True
        Logger.get_instancia().log(f"✅ KYC verificado para {self.nombre}", nivel="SUCCESS")

    def agregar_cuenta(self, cuenta):
        if not self.verificado_kyc:
            raise KYCNoVerificadoError("❌ Primero debe verificar KYC")
        self.cuentas.append(cuenta)
        Logger.get_instancia().log(f"Cuenta {cuenta.numero} agregada a {self.nombre}", nivel="INFO")