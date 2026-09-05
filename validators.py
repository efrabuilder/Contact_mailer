"""
Validación del formulario de contacto (server-side).
Server-side validation for the contact form.
"""
import os
import re

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

NAME_MIN, NAME_MAX = 2, 100
MESSAGE_MIN, MESSAGE_MAX = 10, 2000
MAX_ATTACHMENT_MB = 10


def validate_contact_form(data: dict) -> dict:
    """
    Revisa los campos del formulario y regresa un diccionario de errores.
    Checks the form fields and returns a dict of field -> error message.
    Un diccionario vacío significa que todo es válido.
    """
    errors: dict = {}

    # Honeypot: campo oculto que un humano nunca llena, los bots sí.
    # Honeypot: hidden field a human never fills, bots do.
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
    Revisa el archivo adjunto (opcional). Regresa un mensaje de error o
    cadena vacía si es válido / hoy no viene ningún archivo.
    Checks the optional attachment. Returns an error message, or an empty
    string if it's valid / no file was sent at all.
    """
    if file is None or file.filename == "":
        return ""

    file.stream.seek(0, os.SEEK_END)
    size_mb = file.stream.tell() / (1024 * 1024)
    file.stream.seek(0)  # regresa el cursor al inicio / rewind for later use

    if size_mb > MAX_ATTACHMENT_MB:
        return f"El archivo adjunto no puede superar {MAX_ATTACHMENT_MB} MB."

    return ""
