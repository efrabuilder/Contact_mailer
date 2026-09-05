"""
Envío de correo vía SMTP. Soporta Gmail, Outlook/Office365 y cualquier
servidor SMTP genérico configurado por variables de entorno.

Sends email via SMTP. Supports Gmail, Outlook/Office365, and any generic
SMTP server configured through environment variables.
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


def get_smtp_config() -> dict:
    """
    Arma la configuración SMTP a partir de variables de entorno.
    Builds the SMTP config from environment variables.
    Prioridad: SMTP_HOST/SMTP_PORT explícitos > preset de SMTP_PROVIDER.
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
    config: dict, name: str, sender_email: str, body: str, attachment=None
) -> EmailMessage:
    """
    Construye el correo con remitente/responder-a bien configurados.
    Si viene un archivo adjunto (werkzeug FileStorage), lo agrega al mensaje.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Nuevo mensaje de contacto — {name}"
    msg["From"] = formataddr((name, config["user"]))
    msg["To"] = config["receiver"]
    # Reply-To apunta al correo de quien llenó el formulario, no al buzón emisor.
    # Reply-To points to the form sender, not the sending mailbox.
    msg["Reply-To"] = sender_email
    msg.set_content(
        f"Nombre: {name}\nCorreo: {sender_email}\n\nMensaje:\n{body}"
    )

    if attachment is not None and attachment.filename:
        content = attachment.read()
        mime_type, _ = mimetypes.guess_type(attachment.filename)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        msg.add_attachment(
            content, maintype=maintype, subtype=subtype, filename=attachment.filename
        )

    return msg


def send_contact_email(name: str, sender_email: str, body: str, attachment=None) -> str:
    """
    Envía el correo y regresa un mensaje de éxito.
    Sends the email and returns a success message.
    Lanza MailError con un mensaje claro si algo falla.
    """
    config = get_smtp_config()
    message = build_message(config, name, sender_email, body, attachment)
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
            server.starttls(context=context)
            server.login(config["user"], config["password"])
            server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        logger.error("Fallo de autenticación SMTP para %s", config["user"])
        raise MailError(
            "Credenciales SMTP inválidas. Si usas Gmail u Outlook, generá una "
            "contraseña de aplicación (App Password) en lugar de tu contraseña normal."
        )
    except (socket.timeout, ConnectionRefusedError):
        logger.error("Timeout o conexión rechazada por %s:%s", config["host"], config["port"])
        raise MailError("No se pudo conectar al servidor SMTP. Revisá el host, el puerto y tu red.")
    except smtplib.SMTPException as exc:
        logger.error("Error SMTP: %s", exc)
        raise MailError("El servidor de correo rechazó el envío. Intentá de nuevo en unos minutos.")
    except ssl.SSLError:
        logger.error("Error TLS/SSL al conectar con %s", config["host"])
        raise MailError("Falló la conexión segura (TLS) con el servidor SMTP.")

    return "Tu mensaje fue enviado correctamente."
