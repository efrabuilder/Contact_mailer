"""
Autenticación simple del panel admin, basada en sesión de Flask.
Simple session-based auth for the admin panel.
"""
import os
from functools import wraps

from flask import redirect, session, url_for


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
