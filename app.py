"""
App con dos zonas:
- Pública: pantalla de entrada + formulario de contacto (invitado -> Efraín).
- Privada (login): panel para que Efraín envíe correo desde sus propias
  cuentas hacia cualquier destinatario, con asunto y adjuntos.
"""
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import admin_required, check_credentials, login_admin, logout_admin
from mailer import MailError, get_smtp_accounts, send_contact_email, send_outgoing_email
from validators import (
    validate_attachment,
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
    # El formulario viaja como multipart/form-data cuando hay un archivo adjunto.
    data = request.form if request.form else (request.get_json(silent=True) or {})
    attachment = request.files.get("attachment")

    errors = validate_contact_form(data)
    attachment_error = validate_attachment(attachment)
    if attachment_error:
        errors["attachment"] = attachment_error

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        result_message = send_contact_email(
            name=data.get("name", "").strip(),
            sender_email=data.get("email", "").strip(),
            body=data.get("message", "").strip(),
            attachment=attachment if attachment and attachment.filename else None,
        )
    except MailError as exc:
        return jsonify({"success": False, "errors": {"server": str(exc)}}), 502

    return jsonify({"success": True, "message": result_message}), 200


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if check_credentials(username, password):
        login_admin(username)
        return jsonify({"success": True}), 200

    return jsonify({"success": False, "error": "Usuario o clave incorrectos."}), 401


@app.route("/admin/logout")
def admin_logout():
    logout_admin()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_panel() -> str:
    accounts = get_smtp_accounts()
    return render_template("send.html", accounts=accounts, admin_user=session.get("admin_user", ""))


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

    try:
        result_message = send_outgoing_email(
            account_id=account_id,
            recipients=recipients,
            subject=subject,
            body=message,
            attachments=[f for f in files if f and f.filename],
            sender_name=session.get("admin_user", ""),
        )
    except MailError as exc:
        return jsonify({"success": False, "errors": {"server": str(exc)}}), 502

    return jsonify({"success": True, "message": result_message}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
