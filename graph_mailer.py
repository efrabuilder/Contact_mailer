"""
Envío de correo desde Outlook/Microsoft usando OAuth2 y Microsoft Graph.

Microsoft retiró el envío SMTP con usuario/contraseña (incluidas las App
Passwords) para estas cuentas en abril de 2026, así que el único camino
que queda es autenticación moderna: el usuario autoriza una vez en el
navegador (flujo de código de autorización), guardamos el refresh_token,
y con eso pedimos tokens de acceso nuevos cada vez que hace falta enviar
un correo.
"""
import base64
import os
import urllib.parse

import requests

from token_store import clear_refresh_token, get_refresh_token, save_refresh_token

SCOPES = "offline_access Mail.Send User.Read"
MAX_ATTACHMENTS_BYTES = 3 * 1024 * 1024  # límite de Graph para adjuntos directos


class GraphMailError(Exception):
    """Error controlado del envío por Microsoft Graph, listo para mostrar al usuario."""


def _get_config() -> dict:
    return {
        "client_id": os.environ.get("MS_CLIENT_ID", ""),
        "client_secret": os.environ.get("MS_CLIENT_SECRET", ""),
        "tenant": os.environ.get("MS_TENANT", "common"),
        "redirect_uri": os.environ.get("MS_REDIRECT_URI", ""),
    }


def _authority(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}"


def is_configured() -> bool:
    config = _get_config()
    return bool(config["client_id"] and config["client_secret"] and config["redirect_uri"])


def is_connected() -> bool:
    """True si ya hay una cuenta de Outlook conectada (hay un refresh_token guardado)."""
    return bool(get_refresh_token())


def disconnect() -> None:
    clear_refresh_token()


def get_authorization_url(state: str) -> str:
    """Arma la URL a la que hay que mandar al usuario para que autorice la app."""
    config = _get_config()
    params = {
        "client_id": config["client_id"],
        "response_type": "code",
        "redirect_uri": config["redirect_uri"],
        "response_mode": "query",
        "scope": SCOPES,
        "state": state,
    }
    url = _authority(config["tenant"]) + "/oauth2/v2.0/authorize"
    return url + "?" + urllib.parse.urlencode(params)


def exchange_code_for_tokens(code: str) -> None:
    """
    Intercambia el código de autorización (que llega en el callback) por
    tokens, y guarda el refresh_token para poder enviar correo más adelante
    sin que el usuario tenga que volver a loguearse.
    """
    config = _get_config()
    url = _authority(config["tenant"]) + "/oauth2/v2.0/token"
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config["redirect_uri"],
        "scope": SCOPES,
    }
    response = requests.post(url, data=data, timeout=10)
    if response.status_code != 200:
        raise GraphMailError(
            "Microsoft rechazó la autorización. Revisá que la URI de redirección "
            "configurada en Azure coincida exactamente con la de la app."
        )

    tokens = response.json()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise GraphMailError(
            "Microsoft no devolvió un token de actualización. Confirmá que el "
            "permiso 'offline_access' esté agregado en Azure."
        )
    save_refresh_token(refresh_token)


def _get_access_token() -> str:
    """Usa el refresh_token guardado para conseguir un access_token nuevo."""
    config = _get_config()
    refresh_token = get_refresh_token()
    if not refresh_token:
        raise GraphMailError("No hay ninguna cuenta de Outlook conectada. Conectala primero.")

    url = _authority(config["tenant"]) + "/oauth2/v2.0/token"
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": SCOPES,
    }
    response = requests.post(url, data=data, timeout=10)
    if response.status_code != 200:
        raise GraphMailError(
            "La conexión con Outlook expiró o fue revocada. Volvé a conectar la cuenta."
        )

    tokens = response.json()
    # Microsoft rota el refresh_token en cada uso: hay que guardar el nuevo
    # o la próxima renovación va a fallar.
    new_refresh_token = tokens.get("refresh_token")
    if new_refresh_token:
        save_refresh_token(new_refresh_token)

    return tokens["access_token"]


def send_via_outlook(recipients: list, subject: str, body: str, attachments=None) -> str:
    """Envía un correo desde la cuenta de Outlook conectada, vía Microsoft Graph."""
    access_token = _get_access_token()

    message = {
        "subject": subject,
        "body": {"contentType": "Text", "content": body},
        "toRecipients": [{"emailAddress": {"address": addr}} for addr in recipients],
    }

    graph_attachments = []
    total_bytes = 0
    for attachment in attachments or []:
        if not attachment or not attachment.filename:
            continue
        content = attachment.read()
        total_bytes += len(content)
        if total_bytes > MAX_ATTACHMENTS_BYTES:
            raise GraphMailError(
                "Los adjuntos por Outlook no pueden superar 3 MB en total (límite de "
                "Microsoft Graph para envío directo). Probá con archivos más chicos, o "
                "enviá este correo desde una cuenta de Gmail."
            )
        graph_attachments.append(
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": attachment.filename,
                "contentBytes": base64.b64encode(content).decode("utf-8"),
            }
        )

    if graph_attachments:
        message["attachments"] = graph_attachments

    response = requests.post(
        "https://graph.microsoft.com/v1.0/me/sendMail",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"message": message, "saveToSentItems": "true"},
        timeout=15,
    )

    if response.status_code != 202:
        raise GraphMailError("Microsoft Graph rechazó el envío. Intentá de nuevo en unos minutos.")

    return "Correo enviado correctamente desde Outlook."
