"""
Autenticación simple del panel admin, basada en sesión de Flask, con
límite de intentos de login (protección básica contra fuerza bruta).
Simple session-based auth for the admin panel, with login rate limiting.
"""
import os
from functools import wraps

from flask import redirect, request, session, url_for

try:
    import redis
except ImportError:  # pragma: no cover - redis es dependencia obligatoria del proyecto
    redis = None

# ---------------------------------------------------------------------------
# Límite de intentos de login
# Login rate limiting
#
# Guardado en Redis (igual que token_store.py / inbox_store.py) porque las
# funciones serverless de Vercel no comparten memoria entre invocaciones:
# un contador en una variable de Python no serviría de nada ahí. Si no hay
# REDIS_URL configurada (típico en desarrollo local), el límite queda
# desactivado en vez de bloquear a todo el mundo.
# ---------------------------------------------------------------------------

MAX_FAILED_ATTEMPTS = 5
ATTEMPTS_WINDOW_SECONDS = 15 * 60  # ventana en la que se cuentan los intentos
LOCKOUT_SECONDS = 15 * 60  # cuánto dura el bloqueo una vez superado el límite

ATTEMPTS_KEY_PREFIX = "contact_mailer:login_attempts:"
LOCKOUT_KEY_PREFIX = "contact_mailer:login_lockout:"

_client = None


def _get_client():
    global _client
    if redis is None:
        return None
    if _client is None:
        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url:
            return None
        _client = redis.from_url(redis_url, decode_responses=True)
    return _client


def _client_identifier() -> str:
    # X-Forwarded-For: Vercel corre detrás de un proxy, la IP real del
    # visitante viene ahí (la primera de la lista).
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "desconocido"


def is_locked_out() -> tuple:
    """
    Regresa (bloqueado: bool, segundos_restantes: int) para el cliente
    actual. Si Redis no está configurado, nunca bloquea.
    """
    client = _get_client()
    if client is None:
        return False, 0

    lockout_key = LOCKOUT_KEY_PREFIX + _client_identifier()
    ttl = client.ttl(lockout_key)
    if ttl and ttl > 0:
        return True, ttl
    return False, 0


def register_failed_attempt() -> None:
    client = _get_client()
    if client is None:
        return

    identifier = _client_identifier()
    attempts_key = ATTEMPTS_KEY_PREFIX + identifier
    attempts = client.incr(attempts_key)
    if attempts == 1:
        client.expire(attempts_key, ATTEMPTS_WINDOW_SECONDS)

    if attempts >= MAX_FAILED_ATTEMPTS:
        lockout_key = LOCKOUT_KEY_PREFIX + identifier
        client.set(lockout_key, "1", ex=LOCKOUT_SECONDS)
        client.delete(attempts_key)


def reset_attempts() -> None:
    client = _get_client()
    if client is None:
        return
    client.delete(ATTEMPTS_KEY_PREFIX + _client_identifier())


def check_credentials(username: str, password: str) -> bool:
    """
    Compara usuario/clave contra las variables de entorno
    ADMIN_USERNAME / ADMIN_PASSWORD.
    """
    expected_user = os.environ.get("ADMIN_USERNAME", "")
    expected_pass = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_user or not expected_pass:
        return False
    return username.strip() == expected_user and password == expected_pass


def login_admin(username: str) -> None:
    session["is_admin"] = True
    session["admin_user"] = username.strip()


def logout_admin() -> None:
    session.clear()


def is_admin() -> bool:
    return bool(session.get("is_admin"))


def admin_required(view_func):
    """Decorador: redirige a /admin/login si no hay sesión admin activa."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not is_admin():
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapped
