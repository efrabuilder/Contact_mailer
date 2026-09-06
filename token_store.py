"""
Almacenamiento persistente (Redis) del refresh_token de Outlook.

Las funciones serverless de Vercel no conservan memoria entre ejecuciones,
así que el refresh_token (que además Microsoft rota en cada uso) tiene que
guardarse en algo externo. Usamos el Redis conectado vía REDIS_URL.
"""
import os

import redis

TOKEN_KEY = "contact_mailer:outlook_refresh_token"

_client = None


def _get_client():
    global _client
    if _client is None:
        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url:
            return None
        _client = redis.from_url(redis_url, decode_responses=True)
    return _client


def save_refresh_token(token: str) -> None:
    client = _get_client()
    if client is None:
        raise RuntimeError("REDIS_URL no está configurada.")
    client.set(TOKEN_KEY, token)


def get_refresh_token() -> str:
    client = _get_client()
    if client is None:
        return ""
    return client.get(TOKEN_KEY) or ""


def clear_refresh_token() -> None:
    client = _get_client()
    if client is None:
        return
    client.delete(TOKEN_KEY)
