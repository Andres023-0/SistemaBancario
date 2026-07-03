from logger import Logger

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