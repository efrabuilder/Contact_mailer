"""
Cliente Redis compartido con reintentos. Las funciones serverless de Vercel
a veces fallan al resolver DNS ('Errno 16 Device or resource busy') o al
conectar; un reintento corto casi siempre lo resuelve.
"""
import logging
import os
import time

import redis

_client = None
_log = logging.getLogger("contact_mailer")


def is_configured() -> bool:
    return bool(os.environ.get("REDIS_URL", ""))


def get_client():
    global _client
    if _client is None:
        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url:
            return None
        _client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _client


def call(fn, default=None, raise_on_fail=False):
    """
    Ejecuta fn() con 3 intentos. Si sigue fallando: lanza RuntimeError
    (raise_on_fail=True, para escrituras) o regresa `default` (lecturas,
    fail-soft para no tumbar la página con un 500).
    """
    for attempt in range(3):
        try:
            return fn()
        except (OSError, redis.exceptions.RedisError) as exc:
            if attempt == 2:
                _log.warning("Redis no disponible: %s", exc)
                if raise_on_fail:
                    raise RuntimeError(f"Redis no disponible: {exc}") from exc
                return default
            time.sleep(0.2 * (attempt + 1))
