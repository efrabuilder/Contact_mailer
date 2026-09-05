"""
Envío de correo vía SMTP. Soporta Gmail, Outlook/Office365 y cualquier
servidor SMTP genérico configurado por variables de entorno.

Sends email via SMTP. Supports Gmail, Outlook/Office365, and any generic
SMTP server configured through environment variables.

Este módulo maneja dos flujos separados:
- El formulario público de contacto (una sola cuenta emisora fija).
- El panel de admin, que puede enviar desde varias cuentas configuradas
  y a cualquier destinatario, con asunto y adjuntos libres.
"""
import mimetypes
import os
import smtplib
import ssl
import socket
import logging
from email.message import EmailMessage
from email.utils import formataddr

logger = logging.getLogger("contact_mailer")

# Presets conocidos: host y puerto por proveedor.
# Known presets: host and port per provider.
PROVIDER_PRESETS = {
    "gmail": {"host": "smtp.gmail.com", "port": 587},
    "outlook": {"host": "smtp.office365.com", "port": 587},
    "hotmail": {"host": "smtp.office365.com", "port": 587},
}


class MailError(Exception):
    """Error controlado de envío, con mensaje ya listo para mostrar al usuario."""


# ---------------------------------------------------------------------------
# Flujo público: formulario de contacto (visitante -> Efraín)
# Public flow: contact form (visitor -> Efraín)
# ---------------------------------------------------------------------------

def get_smtp_config() -> dict:
    """
    Arma la configuración SMTP del formulario público a partir de variables
    de entorno. Prioridad: SMTP_HOST/SMTP_PORT explícitos > preset de
    SMTP_PROVIDER.
    """
    provider = os.environ.get("SMTP_PROVIDER", "").strip().lower()
    preset = PROVIDER_PRESETS.get(provider, {})

    host = os.environ.get("SMTP_HOST", preset.get("host", ""))
    port = int(os.environ.get("SMTP_PORT", preset.get("port", 587)))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    receiver = os.environ.get("CONTACT_RECEIVER_EMAIL", user)

    if not host or not user or not password:
        raise MailError(
            "Configuración SMTP incompleta. Revisa SMTP_PROVIDER (o SMTP_HOST/SMTP_PORT), "
            "SMTP_USER y SMTP_PASSWORD en tu archivo .env."
        )

    return {"host": host, "port": port, "user": user, "password": password, "receiver": receiver}


def build_message(
    config: dict, name: str, sender_email: str, body: str, attachments=None
) -> EmailMessage:
    """
    Construye el correo del formulario de contacto con remitente/responder-a
    bien configurados. Si vienen archivos adjuntos (lista de werkzeug
    FileStorage), los agrega al mensaje.

    Nota: el "From" siempre es la cuenta autenticada (config["user"]), nunca
    el correo de quien escribe el formulario — los proveedores (Gmail,
    Outlook) rechazan o reescriben un From que no sea la cuenta autenticada
    (protección SPF/DKIM/DMARC contra suplantación). Por eso se usa
    Reply-To: al responder ese correo, la respuesta va directo a quien
    escribió el mensaje.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Nuevo mensaje de contacto — {name}"
    msg["From"] = formataddr((name, config["user"]))
    msg["To"] = config["receiver"]
    msg["Reply-To"] = sender_email
    msg.set_content(
        f"Nombre: {name}\nCorreo: {sender_email}\n\nMensaje:\n{body}"
    )

    for attachment in attachments or []:
        if not attachment or not attachment.filename:
            continue
        content = attachment.read()
        mime_type, _ = mimetypes.guess_type(attachment.filename)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        msg.add_attachment(
            content, maintype=maintype, subtype=subtype, filename=attachment.filename
        )

    return msg


def send_contact_email(name: str, sender_email: str, body: str, attachments=None) -> str:
    """
    Envía el correo del formulario público y regresa un mensaje de éxito.
    Lanza MailError con un mensaje claro si algo falla.
    """
    config = get_smtp_config()
    message = build_message(config, name, sender_email, body, attachments)
    _deliver(config["host"], config["port"], config["user"], config["password"], message)
    return "Tu mensaje fue enviado correctamente."


# ---------------------------------------------------------------------------
# Flujo admin: panel privado (Efraín -> cualquier destinatario)
# Admin flow: private panel (Efraín -> any recipient)
# ---------------------------------------------------------------------------

def get_smtp_accounts() -> list:
    """
    Lee las cuentas emisoras configuradas para el panel admin.
    Busca variables SMTP_ACCOUNT_<n>_USER, _PASSWORD, _LABEL y
    _PROVIDER (o _HOST/_PORT), con <n> = 1, 2, 3... hasta que falte una.
    """
    accounts = []
    i = 1
    while True:
        user = os.environ.get(f"SMTP_ACCOUNT_{i}_USER")
        if not user:
            break
        password = os.environ.get(f"SMTP_ACCOUNT_{i}_PASSWORD", "")
        label = os.environ.get(f"SMTP_ACCOUNT_{i}_LABEL", user)
        provider = os.environ.get(f"SMTP_ACCOUNT_{i}_PROVIDER", "").strip().lower()
        preset = PROVIDER_PRESETS.get(provider, {})
        host = os.environ.get(f"SMTP_ACCOUNT_{i}_HOST", preset.get("host", ""))
        port = int(os.environ.get(f"SMTP_ACCOUNT_{i}_PORT", preset.get("port", 587)))
        accounts.append(
            {
                "id": str(i),
                "label": label,
                "host": host,
                "port": port,
                "user": user,
                "password": password,
            }
        )
        i += 1
    return accounts


def get_account_by_id(account_id: str) -> dict:
    for account in get_smtp_accounts():
        if account["id"] == account_id:
            return account
    return {}


def build_outgoing_message(
    account: dict, sender_name: str, recipients: list, subject: str, body: str, attachments=None
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((sender_name, account["user"])) if sender_name else account["user"]
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    for attachment in attachments or []:
        if not attachment or not attachment.filename:
            continue
        content = attachment.read()
        mime_type, _ = mimetypes.guess_type(attachment.filename)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        msg.add_attachment(
            content, maintype=maintype, subtype=subtype, filename=attachment.filename
        )

    return msg


def send_outgoing_email(
    account_id: str,
    recipients: list,
    subject: str,
    body: str,
    attachments=None,
    sender_name: str = "",
) -> str:
    """
    Envía el correo del panel admin desde la cuenta elegida.
    Lanza MailError con un mensaje claro si algo falla.
    """
    account = get_account_by_id(account_id)
    if not account or not account.get("host") or not account.get("password"):
        raise MailError("La cuenta emisora seleccionada no está configurada correctamente.")

    message = build_outgoing_message(account, sender_name, recipients, subject, body, attachments)
    _deliver(account["host"], account["port"], account["user"], account["password"], message)
    return "Correo enviado correctamente."


# ---------------------------------------------------------------------------
# Entrega compartida por ambos flujos
# Delivery shared by both flows
# ---------------------------------------------------------------------------

def _deliver(host: str, port: int, user: str, password: str, message: EmailMessage) -> None:
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        logger.error("Fallo de autenticación SMTP para %s", user)
        raise MailError(
            "Credenciales SMTP inválidas. Si usas Gmail u Outlook, generá una "
            "contraseña de aplicación (App Password) en lugar de tu contraseña normal."
        )
    except (socket.timeout, ConnectionRefusedError):
        logger.error("Timeout o conexión rechazada por %s:%s", host, port)
        raise MailError("No se pudo conectar al servidor SMTP. Revisá el host, el puerto y tu red.")
    except smtplib.SMTPException as exc:
        logger.error("Error SMTP: %s", exc)
        raise MailError("El servidor de correo rechazó el envío. Intentá de nuevo en unos minutos.")
    except ssl.SSLError:
        logger.error("Error TLS/SSL al conectar con %s", host)
        raise MailError("Falló la conexión segura (TLS) con el servidor SMTP.")
