"""
Landing con formulario de contacto que envía correo de verdad.
Landing page with a contact form that actually sends email.
"""
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from mailer import MailError, send_contact_email
from validators import validate_contact_form

load_dotenv()  # Carga variables desde .env / Loads variables from .env

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/contact", methods=["POST"])
def contact() -> tuple:
    data = request.get_json(silent=True) or request.form
    errors = validate_contact_form(data)

    if errors:
        status = 400
        return jsonify({"success": False, "errors": errors}), status

    try:
        result_message = send_contact_email(
            name=data.get("name", "").strip(),
            sender_email=data.get("email", "").strip(),
            body=data.get("message", "").strip(),
        )
    except MailError as exc:
        return jsonify({"success": False, "errors": {"server": str(exc)}}), 502

    return jsonify({"success": True, "message": result_message}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
