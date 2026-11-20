"""
Almacenamiento persistente (Redis) del refresh_token de Outlook.

Las funciones serverless de Vercel no conservan memoria entre ejecuciones,
así que el refresh_token (que además Microsoft rota en cada uso) tiene que
guardarse en algo externo. Usamos el Redis conectado vía REDIS_URL.
"""
from redis_util import call, get_client

TOKEN_KEY = "contact_mailer:outlook_refresh_token"


def save_refresh_token(token: str) -> None:
    client = get_client()
    if client is None:
        raise RuntimeError("REDIS_URL no está configurada.")
    call(lambda: client.set(TOKEN_KEY, token), raise_on_fail=True)


def get_refresh_token() -> str:
    client = get_client()
    if client is None:
        return ""
    return call(lambda: client.get(TOKEN_KEY), "") or ""


def clear_refresh_token() -> None:
    client = get_client()
    if client is None:
        return
    call(lambda: client.delete(TOKEN_KEY))
