from abc import ABC, abstractmethod
from canal_factory import Notificador
from logger import Logger


# =============================================================================
# ADAPTEES — Servicios externos simulados
# Representan proveedores reales con interfaces incompatibles.
# NO implementan Notificador. NO conocen el sistema bancario.
# En producción real, estas clases serían SDKs de terceros (Twilio, SendGrid…)
# =============================================================================

class ServicioSMS:
    """
    Adaptee A — Simula un proveedor externo de SMS (ej. Twilio).
    Su interfaz NO es compatible con Notificador.
    Método propio: send_sms(destinatario, mensaje)
    """
    def send_sms(self, destinatario: str, mensaje: str):
        logger = Logger.get_instancia()
        logger.log(
            f"[TWILIO-SMS] → Destinatario: {destinatario} | Mensaje: '{mensaje}'",
            nivel="INFO"
        )


class ServicioEmail:
    """
    Adaptee B — Simula un proveedor externo de email (ej. SendGrid).
    Su interfaz NO es compatible con Notificador.
    Método propio: enviar_correo(asunto, cuerpo, destinatario)
    """
    def enviar_correo(self, asunto: str, cuerpo: str, destinatario: str):
        logger = Logger.get_instancia()
        logger.log(
            f"[SENDGRID-EMAIL] → Asunto: '{asunto}' | Para: {destinatario} | Cuerpo: '{cuerpo}'",
            nivel="INFO"
        )


class ServicioPush:
    """
    Adaptee C — Simula un proveedor externo de notificaciones push (ej. Firebase).
    Su interfaz NO es compatible con Notificador.
    Método propio: push_notification(device_token, titulo, payload)
    """
    def push_notification(self, device_token: str, titulo: str, payload: dict):
        logger = Logger.get_instancia()
        logger.log(
            f"[FIREBASE-PUSH] → Token: {device_token} | Título: '{titulo}' | Payload: {payload}",
            nivel="INFO"
        )


class ServicioVoucherFisico:
    """
    Adaptee D — Simula una impresora de vouchers físicos en cajero.
    Su interfaz NO es compatible con Notificador.
    Método propio: imprimir_voucher(datos_voucher)
    """
    def imprimir_voucher(self, datos_voucher: dict):
        logger = Logger.get_instancia()
        logger.log(
            f"[IMPRESORA-CAJERO] → Imprimiendo voucher: {datos_voucher}",
            nivel="INFO"
        )


# =============================================================================
# ADAPTERS — Traducen la interfaz de cada Adaptee hacia Notificador (Target)
# Implementan Notificador (lo que el sistema espera)
# Internamente delegan al servicio externo con su propia firma
# =============================================================================

class SMSAdapter(Notificador):
    """
    Adapter A — Adapta ServicioSMS a la interfaz Notificador.
    El sistema llama notificar(), el Adapter traduce y llama send_sms().
    """
    def __init__(self, servicio_sms: ServicioSMS, numero_celular: str):
        self._servicio = servicio_sms
        self._numero_celular = numero_celular

    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        mensaje = (
            f"Banco UTS: {tipo.upper()} de ${monto:,.2f} "
            f"en cuenta {cuenta_numero} procesado exitosamente."
        )
        Logger.get_instancia().log(
            f"📲 [SMS-ADAPTER] Traduciendo notificar() → send_sms()",
            nivel="INFO"
        )
        self._servicio.send_sms(self._numero_celular, mensaje)


class EmailAdapter(Notificador):
    """
    Adapter B — Adapta ServicioEmail a la interfaz Notificador.
    El sistema llama notificar(), el Adapter traduce y llama enviar_correo().
    """
    def __init__(self, servicio_email: ServicioEmail, correo_destino: str):
        self._servicio = servicio_email
        self._correo_destino = correo_destino

    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        asunto = f"Confirmación de {tipo.upper()} — Cuenta {cuenta_numero}"
        cuerpo = (
            f"Estimado cliente, le informamos que su {tipo} de ${monto:,.2f} "
            f"en la cuenta {cuenta_numero} fue procesado exitosamente. "
            f"Banco UTS."
        )
        Logger.get_instancia().log(
            f"📧 [EMAIL-ADAPTER] Traduciendo notificar() → enviar_correo()",
            nivel="INFO"
        )
        self._servicio.enviar_correo(asunto, cuerpo, self._correo_destino)


class PushAdapter(Notificador):
    """
    Adapter C — Adapta ServicioPush a la interfaz Notificador.
    El sistema llama notificar(), el Adapter traduce y llama push_notification().
    """
    def __init__(self, servicio_push: ServicioPush, device_token: str):
        self._servicio = servicio_push
        self._device_token = device_token

    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        titulo = f"Movimiento en tu cuenta {cuenta_numero}"
        payload = {
            "tipo": tipo,
            "monto": monto,
            "cuenta": cuenta_numero
        }
        Logger.get_instancia().log(
            f"🔔 [PUSH-ADAPTER] Traduciendo notificar() → push_notification()",
            nivel="INFO"
        )
        self._servicio.push_notification(self._device_token, titulo, payload)


class VoucherAdapter(Notificador):
    """
    Adapter D — Adapta ServicioVoucherFisico a la interfaz Notificador.
    El sistema llama notificar(), el Adapter traduce y llama imprimir_voucher().
    """
    def __init__(self, servicio_voucher: ServicioVoucherFisico):
        self._servicio = servicio_voucher

    def notificar(self, tipo: str, monto: float, cuenta_numero: str):
        datos_voucher = {
            "operacion": tipo.upper(),
            "monto": f"${monto:,.2f}",
            "cuenta": cuenta_numero,
        }
        Logger.get_instancia().log(
            f"🧾 [VOUCHER-ADAPTER] Traduciendo notificar() → imprimir_voucher()",
            nivel="INFO"
        )
        self._servicio.imprimir_voucher(datos_voucher)


# =============================================================================
# ADAPTER PRODUCER — Punto de entrada único
# MODIFICADO: ahora recibe el usuario para usar sus datos reales de contacto
# en lugar de datos hardcodeados
# =============================================================================

class NotificadorAdapterProducer:
    """
    Retorna el Adapter correcto según el canal y los datos reales del usuario
    dueño de la cuenta, para que las notificaciones lleguen a su contacto real.
    """

    @staticmethod
    def get_adapter(canal: str, usuario=None) -> Notificador:  # ← CAMBIO: agrega usuario
        canal = canal.lower()

        # ── Datos reales del usuario con fallback si no existen ──────────────
        celular = usuario.celular if usuario and usuario.celular else "+570000000000"
        correo  = usuario.correo  if usuario and usuario.correo  else "sin-correo@banco.com"

        if canal == "web":
            # Canal Web → Email con correo real del usuario
            return EmailAdapter(
                servicio_email=ServicioEmail(),
                correo_destino=correo          # ← antes: "cliente@email.com" hardcodeado
            )

        elif canal == "movil":
            # Canal Móvil → SMS con celular real del usuario
            return SMSAdapter(
                servicio_sms=ServicioSMS(),
                numero_celular=celular         # ← antes: "+573001234567" hardcodeado
            )

        elif canal == "cajero":
            # Canal Cajero → Voucher físico (no necesita datos de contacto)
            return VoucherAdapter(
                servicio_voucher=ServicioVoucherFisico()
            )

        else:
            raise ValueError(
                f"Canal no soportado: '{canal}'. Canales válidos: web, movil, cajero"
            )