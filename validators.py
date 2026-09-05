"""
Validación de los formularios (server-side).
Server-side validation for both forms (public contact + admin send).
"""
import os
import re

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

NAME_MIN, NAME_MAX = 2, 100
MESSAGE_MIN, MESSAGE_MAX = 10, 2000
MAX_ATTACHMENT_MB = 10
MAX_TOTAL_ATTACHMENTS_MB = 20
SUBJECT_MAX = 200
SEND_MESSAGE_MAX = 5000


# ---------------------------------------------------------------------------
# Formulario público de contacto
# Public contact form
# ---------------------------------------------------------------------------

def validate_contact_form(data: dict) -> dict:
    """
    Revisa los campos del formulario público y regresa un diccionario de
    errores. Un diccionario vacío significa que todo es válido.
    """
    errors: dict = {}

    # Honeypot: campo oculto que un humano nunca llena, los bots sí.
    if data.get("website", "").strip():
        errors["spam"] = "Envío bloqueado por el filtro anti-spam."
        return errors

    name = data.get("name", "").strip()
    if not name:
        errors["name"] = "El nombre es obligatorio."
    elif len(name) < NAME_MIN or len(name) > NAME_MAX:
        errors["name"] = f"El nombre debe tener entre {NAME_MIN} y {NAME_MAX} caracteres."

    email = data.get("email", "").strip()
    if not email:
        errors["email"] = "El correo es obligatorio."
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "El formato del correo no es válido."

    message = data.get("message", "").strip()
    if not message:
        errors["message"] = "El mensaje es obligatorio."
    elif len(message) < MESSAGE_MIN or len(message) > MESSAGE_MAX:
        errors["message"] = f"El mensaje debe tener entre {MESSAGE_MIN} y {MESSAGE_MAX} caracteres."

    return errors


def validate_attachment(file) -> str:
    """
    Revisa un único archivo adjunto (formulario público). Regresa un mensaje
    de error o cadena vacía si es válido / no viene ningún archivo.
    """
    if file is None or file.filename == "":
        return ""

    file.stream.seek(0, os.SEEK_END)
    size_mb = file.stream.tell() / (1024 * 1024)
    file.stream.seek(0)

    if size_mb > MAX_ATTACHMENT_MB:
        return f"El archivo adjunto no puede superar {MAX_ATTACHMENT_MB} MB."

    return ""


# ---------------------------------------------------------------------------
# Panel admin
# Admin panel
# ---------------------------------------------------------------------------

def validate_recipients(recipients: list) -> str:
    """recipients ya viene como lista de strings separada por el caller."""
    if not recipients:
        return "Agregá al menos un destinatario."
    for email in recipients:
        if not EMAIL_PATTERN.match(email.strip()):
            return f'"{email}" no es un correo válido.'
    return ""


def validate_subject(subject: str) -> str:
    subject = subject.strip()
    if not subject:
        return "El asunto es obligatorio."
    if len(subject) > SUBJECT_MAX:
        return f"El asunto no puede superar {SUBJECT_MAX} caracteres."
    return ""


def validate_send_message(message: str) -> str:
    message = message.strip()
    if not message:
        return "El mensaje es obligatorio."
    if len(message) > SEND_MESSAGE_MAX:
        return f"El mensaje no puede superar {SEND_MESSAGE_MAX} caracteres."
    return ""


def validate_attachments(files: list) -> str:
    """Revisa varios archivos adjuntos (panel admin): tamaño individual y total."""
    if not files:
        return ""

    total_mb = 0.0
    for file in files:
        if not file or file.filename == "":
            continue
        file.stream.seek(0, os.SEEK_END)
        size_mb = file.stream.tell() / (1024 * 1024)
        file.stream.seek(0)

        if size_mb > MAX_ATTACHMENT_MB:
            return f'"{file.filename}" supera los {MAX_ATTACHMENT_MB} MB.'
        total_mb += size_mb

    if total_mb > MAX_TOTAL_ATTACHMENTS_MB:
        return f"El total de adjuntos no puede superar {MAX_TOTAL_ATTACHMENTS_MB} MB."

    return ""
