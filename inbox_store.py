"""
Almacenamiento persistente (Redis) de los mensajes del formulario de
contacto, para poder verlos en la bandeja de entrada del panel admin.

Igual que en token_store.py: las funciones serverless de Vercel no
conservan memoria entre ejecuciones, así que esto necesita algo externo.
Usamos el mismo Redis conectado vía REDIS_URL.

Nota: acá NO se guarda el contenido de los adjuntos (solo sus nombres).
Los adjuntos completos siguen viajando en el correo de aviso; guardar
archivos binarios en Redis infla rápido el plan gratuito y no hace
falta para revisar mensajes desde el panel.
"""
import json
import os
import time
import uuid

import redis

INDEX_KEY = "contact_mailer:inbox:index"
MESSAGE_KEY_PREFIX = "contact_mailer:inbox:msg:"

_client = None


def _get_client():
    global _client
    if _client is None:
        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url:
            return None
        _client = redis.from_url(redis_url, decode_responses=True)
    return _client


def is_configured() -> bool:
    return bool(os.environ.get("REDIS_URL", ""))


def add_message(name: str, email: str, message: str, attachment_names: list = None) -> str:
    """
    Guarda un mensaje nuevo y regresa su id. Si Redis no está configurado,
    lanza RuntimeError (el llamador decide si eso debe frenar el request
    o solo quedar en el log, ya que el correo de aviso es lo prioritario).
    """
    client = _get_client()
    if client is None:
        raise RuntimeError("REDIS_URL no está configurada: no se puede guardar en la bandeja.")

    msg_id = uuid.uuid4().hex
    received_at = time.time()
    record = {
        "id": msg_id,
        "name": name,
        "email": email,
        "message": message,
        "attachments": attachment_names or [],
        "received_at": received_at,
        "read": False,
    }
    client.set(MESSAGE_KEY_PREFIX + msg_id, json.dumps(record))
    client.zadd(INDEX_KEY, {msg_id: received_at})
    return msg_id


def list_messages() -> list:
    """Todos los mensajes, del más reciente al más antiguo."""
    client = _get_client()
    if client is None:
        return []

    ids = client.zrevrange(INDEX_KEY, 0, -1)
    if not ids:
        return []

    keys = [MESSAGE_KEY_PREFIX + msg_id for msg_id in ids]
    raw_records = client.mget(keys)

    messages = []
    for msg_id, raw in zip(ids, raw_records):
        if raw is None:
            # El registro se borró pero quedó huérfano en el índice: limpiamos.
            client.zrem(INDEX_KEY, msg_id)
            continue
        messages.append(json.loads(raw))
    return messages


def get_message(msg_id: str) -> dict:
    client = _get_client()
    if client is None:
        return {}
    raw = client.get(MESSAGE_KEY_PREFIX + msg_id)
    return json.loads(raw) if raw else {}


def mark_read(msg_id: str) -> None:
    client = _get_client()
    if client is None:
        return
    key = MESSAGE_KEY_PREFIX + msg_id
    raw = client.get(key)
    if not raw:
        return
    record = json.loads(raw)
    if not record.get("read"):
        record["read"] = True
        client.set(key, json.dumps(record))


def delete_message(msg_id: str) -> None:
    client = _get_client()
    if client is None:
        return
    client.delete(MESSAGE_KEY_PREFIX + msg_id)
    client.zrem(INDEX_KEY, msg_id)


def unread_count() -> int:
    client = _get_client()
    if client is None:
        return 0
    count = 0
    for record in list_messages():
        if not record.get("read"):
            count += 1
    return count
