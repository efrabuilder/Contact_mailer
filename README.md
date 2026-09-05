# contact-mailer

Landing con formulario de contacto que envía correo de verdad — validación
en el servidor, entrega por SMTP y manejo explícito de errores. Sin
servicios de terceros como Resend: usa `smtplib` directo contra Gmail,
Outlook/Office365 o cualquier servidor SMTP.

## Stack

- Python 3.10+
- Flask (servidor y ruta `/api/contact`)
- `smtplib` + `ssl` de la librería estándar (sin dependencias de envío externas)
- Validación propia en `validators.py` (servidor) y JS espejo en el cliente

## Cómo funciona

1. El formulario valida en el navegador para dar feedback inmediato.
2. El servidor **vuelve a validar todo** — nunca confía en el cliente.
3. Si pasa la validación, `mailer.py` arma el correo y se conecta por SMTP
   con STARTTLS.
4. Cualquier falla (credenciales, conexión, TLS) se captura por separado y
   se devuelve como un mensaje entendible, no un stack trace.

## Instalación

```bash
git clone https://github.com/efrabuilder/contact-mailer.git
cd contact-mailer
python -m venv venv
source venv/bin/activate  # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Completá `.env` con tus credenciales (ver abajo) y corré:

```bash
python app.py
```

La landing queda en `http://localhost:5000`.

## Configurar Gmail

1. Activá la verificación en dos pasos en tu cuenta de Google.
2. Generá una **contraseña de aplicación**: Cuenta de Google → Seguridad →
   Verificación en dos pasos → Contraseñas de aplicaciones.
3. En `.env`:
   ```
   SMTP_PROVIDER=gmail
   SMTP_USER=tu_correo@gmail.com
   SMTP_PASSWORD=la_app_password_de_16_caracteres
   ```

## Configurar Outlook / Office365

1. Si tu cuenta tiene 2FA (recomendado), generá una contraseña de aplicación
   desde account.microsoft.com → Seguridad.
2. En `.env`:
   ```
   SMTP_PROVIDER=outlook
   SMTP_USER=tu_correo@outlook.com
   SMTP_PASSWORD=tu_app_password
   ```

## Otro proveedor SMTP

Dejá `SMTP_PROVIDER` vacío y definí `SMTP_HOST` y `SMTP_PORT` manualmente
en `.env`. El resto del flujo (validación, TLS, manejo de errores) es igual.

## Estructura

```
contact-mailer/
├── app.py            # Rutas Flask (landing + /api/contact)
├── mailer.py         # Conexión SMTP, presets de proveedor, errores
├── validators.py     # Reglas de validación del formulario
├── templates/
│   └── index.html    # Landing (hero + diagrama de pipeline + formulario)
├── static/
│   ├── style.css
│   └── script.js      # Validación en vivo, i18n ES/EN, animación del envío
├── .env.example
└── requirements.txt
```

## Despliegue

Cualquier host que corra Python (Render, Railway, Fly.io, un VPS) sirve.
Solo asegurate de setear las variables de entorno del `.env.example` en el
panel del proveedor, y de correr con un servidor WSGI real en producción,
por ejemplo:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```
