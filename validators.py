"""
Validación del formulario de contacto (server-side).
Server-side validation for the contact form.
"""
import re

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

NAME_MIN, NAME_MAX = 2, 100
MESSAGE_MIN, MESSAGE_MAX = 10, 2000


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
