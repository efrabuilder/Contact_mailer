"""
App con dos zonas:
- Pública: pantalla de entrada + formulario de contacto (invitado -> Efraín).
- Privada (login): panel para que Efraín envíe correo desde sus propias
  cuentas hacia cualquier destinatario, con asunto y adjuntos.
"""
import logging
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import (
    admin_required,
    check_credentials,
    is_locked_out,
    login_admin,
    logout_admin,
    register_failed_attempt,
    reset_attempts,
)
from graph_mailer import (
    GraphMailError,
    exchange_code_for_tokens,
    get_authorization_url,
    is_configured as outlook_is_configured,
    is_connected as outlook_is_connected,
    disconnect as outlook_disconnect_account,
    send_via_outlook,
)
import inbox_store
from mailer import MailError, get_smtp_accounts, send_contact_email, send_outgoing_email
from validators import (
    validate_attachments,
    validate_contact_form,
    validate_recipients,
    validate_send_message,
    validate_subject,
)

load_dotenv()  # Carga variables desde .env / Loads variables from .env

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
# Necesaria para firmar la cookie de sesión del login admin.
# Needed to sign the admin login session cookie. Configurala en producción.
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # margen para varios adjuntos


# ---------------------------------------------------------------------------
# Público
# ---------------------------------------------------------------------------

@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/contact")
def contact_page() -> str:
    return render_template("contact.html")


@app.route("/api/contact", methods=["POST"])
def contact() -> tuple:
    # El formulario viaja como multipart/form-data cuando hay archivos adjuntos.
    data = request.form if request.form else (request.get_json(silent=True) or {})
    attachments = request.files.getlist("attachments")

    errors = validate_contact_form(data)
    attachments_error = validate_attachments(attachments)
    if attachments_error:
        errors["attachments"] = attachments_error

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    name = data.get("name", "").strip()
    sender_email = data.get("email", "").strip()
    body = data.get("message", "").strip()
    clean_attachments = [f for f in attachments if f and f.filename]

    try:
        result_message = send_contact_email(
            name=name,
            sender_email=sender_email,
            body=body,
            attachments=clean_attachments,
        )
    except MailError as exc:
        return jsonify({"success": False, "errors": {"server": str(exc)}}), 502

    # El correo de aviso ya salió (lo de arriba); guardar en la bandeja es
    # secundario, así que si Redis falla no le arruinamos el envío al
    # visitante — solo lo dejamos en el log.
    try:
        inbox_store.add_message(
            name=name,
            email=sender_email,
            message=body,
            attachment_names=[f.filename for f in clean_attachments],
        )
    except RuntimeError:
        logging.getLogger("contact_mailer").warning(
            "No se pudo guardar el mensaje en la bandeja (Redis no configurado)."
        )

    return jsonify({"success": True, "message": result_message}), 200


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("login.html")

    locked, seconds_left = is_locked_out()
    if locked:
        minutes_left = max(1, seconds_left // 60)
        return jsonify({
            "success": False,
            "error": f"Demasiados intentos fallidos. Probá de nuevo en {minutes_left} minuto(s).",
        }), 429

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if check_credentials(username, password):
        reset_attempts()
        login_admin(username)
        return jsonify({"success": True}), 200

    register_failed_attempt()
    return jsonify({"success": False, "error": "Usuario o clave incorrectos."}), 401


@app.route("/admin/logout")
def admin_logout():
    logout_admin()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_panel() -> str:
    accounts = get_smtp_accounts()
    return render_template(
        "send.html",
        accounts=accounts,
        admin_user=session.get("admin_user", ""),
        outlook_configured=outlook_is_configured(),
        outlook_connected=outlook_is_connected(),
        outlook_error=request.args.get("outlook_error"),
        unread_count=inbox_store.unread_count(),
    )


@app.route("/admin/inbox")
@admin_required
def admin_inbox() -> str:
    return render_template(
        "inbox.html",
        admin_user=session.get("admin_user", ""),
        messages=inbox_store.list_messages(),
        inbox_configured=inbox_store.is_configured(),
    )


@app.route("/admin/inbox/<msg_id>")
@admin_required
def admin_inbox_detail(msg_id: str) -> str:
    message = inbox_store.get_message(msg_id)
    if not message:
        return redirect(url_for("admin_inbox"))
    inbox_store.mark_read(msg_id)
    return render_template(
        "inbox_detail.html",
        admin_user=session.get("admin_user", ""),
        message=message,
    )


@app.route("/admin/inbox/<msg_id>/delete", methods=["POST"])
@admin_required
def admin_inbox_delete(msg_id: str):
    inbox_store.delete_message(msg_id)
    return redirect(url_for("admin_inbox"))


@app.route("/admin/outlook/connect")
@admin_required
def outlook_connect():
    # "state" evita que alguien mande a la app un callback falso.
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    return redirect(get_authorization_url(state))


@app.route("/admin/outlook/callback")
@admin_required
def outlook_callback():
    error_description = request.args.get("error_description")
    if error_description:
        return redirect(url_for("admin_panel", outlook_error=error_description))

    state = request.args.get("state")
    if not state or state != session.pop("oauth_state", None):
        return redirect(
            url_for("admin_panel", outlook_error="Sesión de autorización inválida, intentá conectar de nuevo.")
        )

    code = request.args.get("code")
    try:
        exchange_code_for_tokens(code)
    except GraphMailError as exc:
        return redirect(url_for("admin_panel", outlook_error=str(exc)))

    return redirect(url_for("admin_panel"))


@app.route("/admin/outlook/disconnect")
@admin_required
def outlook_disconnect():
    outlook_disconnect_account()
    return redirect(url_for("admin_panel"))


@app.route("/api/send", methods=["POST"])
@admin_required
def send_mail() -> tuple:
    data = request.form
    recipients = [r.strip() for r in data.get("recipients", "").split(",") if r.strip()]
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()
    account_id = data.get("account_id", "").strip()
    files = request.files.getlist("attachments")

    errors: dict = {}

    recipients_error = validate_recipients(recipients)
    if recipients_error:
        errors["recipients"] = recipients_error

    subject_error = validate_subject(subject)
    if subject_error:
        errors["subject"] = subject_error

    message_error = validate_send_message(message)
    if message_error:
        errors["message"] = message_error

    attachments_error = validate_attachments(files)
    if attachments_error:
        errors["attachments"] = attachments_error

    if not account_id:
        errors["account_id"] = "Elegí la cuenta desde la que querés enviar."

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    clean_attachments = [f for f in files if f and f.filename]

    try:
        if account_id == "outlook":
            result_message = send_via_outlook(
                recipients=recipients,
                subject=subject,
                body=message,
                attachments=clean_attachments,
            )
        else:
            result_message = send_outgoing_email(
                account_id=account_id,
                recipients=recipients,
                subject=subject,
                body=message,
                attachments=clean_attachments,
                sender_name=session.get("admin_user", ""),
            )
    except (MailError, GraphMailError) as exc:
        return jsonify({"success": False, "errors": {"server": str(exc)}}), 502

    return jsonify({"success": True, "message": result_message}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
