// i18n: diccionario simple ES/EN aplicado sobre data-i18n
// i18n: simple ES/EN dictionary applied over data-i18n attributes
const translations = {
  es: {
    hero_title: "Un formulario que de verdad<br>llega a tu bandeja de entrada",
    hero_lede: "Nada de \"gracias por tu mensaje\" que se pierde en el vacío. Este formulario valida cada campo en el servidor, se conecta por SMTP a Gmail u Outlook, y te avisa si algo sale mal — con un mensaje que puedas entender.",
    feat_1: "Validación real en el servidor, no solo en el navegador",
    feat_2: "Envío por SMTP a Gmail, Outlook u otro proveedor",
    feat_3: "Errores de conexión y autenticación manejados uno por uno",
    step_1: "Formulario", step_2: "Validación", step_3: "Servidor SMTP", step_4: "Tu inbox",
    form_title: "Probá el envío",
    label_name: "Nombre", label_email: "Correo", label_message: "Mensaje",
    label_attachment: "Adjuntar archivo (opcional)",
    no_file: "Ningún archivo seleccionado",
    btn_send: "Enviar mensaje",
    footer_text: "Hecho con Python + Flask + smtplib.",
    err_name: "El nombre es obligatorio.",
    err_email: "Ingresá un correo válido.",
    err_message: "El mensaje debe tener al menos 10 caracteres.",
    err_attachment: "El archivo no puede superar 10 MB.",
    log_validating: "Validando campos...",
    log_connecting: "Conectando con el servidor SMTP...",
    log_sending: "Enviando el correo...",
    log_success: "Correo enviado. Revisá tu bandeja de entrada.",
    log_fail: "No se pudo enviar el correo."
  },
  en: {
    hero_title: "A form that actually<br>lands in your inbox",
    hero_lede: "No \"thanks for your message\" that vanishes into the void. This form validates every field on the server, connects over SMTP to Gmail or Outlook, and tells you exactly what went wrong when it does.",
    feat_1: "Real server-side validation, not just in the browser",
    feat_2: "SMTP delivery to Gmail, Outlook, or any other provider",
    feat_3: "Connection and authentication errors handled individually",
    step_1: "Form", step_2: "Validation", step_3: "SMTP server", step_4: "Your inbox",
    form_title: "Try sending it",
    label_name: "Name", label_email: "Email", label_message: "Message",
    label_attachment: "Attach a file (optional)",
    no_file: "No file selected",
    btn_send: "Send message",
    footer_text: "Built with Python + Flask + smtplib.",
    err_name: "Name is required.",
    err_email: "Enter a valid email address.",
    err_message: "Message must be at least 10 characters.",
    err_attachment: "The file can't be larger than 10 MB.",
    log_validating: "Validating fields...",
    log_connecting: "Connecting to the SMTP server...",
    log_sending: "Sending the email...",
    log_success: "Email sent. Check your inbox.",
    log_fail: "Could not send the email."
  }
};

let currentLang = "es";

function applyLang(lang) {
  currentLang = lang;
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach(function (el) {
    const key = el.getAttribute("data-i18n");
    if (translations[lang][key]) el.innerHTML = translations[lang][key];
  });
}

document.getElementById("lang-toggle").addEventListener("click", function () {
  applyLang(currentLang === "es" ? "en" : "es");
});

// Tema claro/oscuro / Light-dark theme
const themeToggle = document.getElementById("theme-toggle");
themeToggle.addEventListener("click", function () {
  const html = document.documentElement;
  const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  themeToggle.querySelector(".theme-icon").textContent = next === "dark" ? "☾" : "☀";
});

// Validación en vivo, refleja las reglas del servidor / Live validation mirroring server rules
const rules = {
  name: function (v) { return v.trim().length >= 2; },
  email: function (v) { return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(v.trim()); },
  message: function (v) { return v.trim().length >= 10; }
};

function showFieldError(field, key) {
  const input = document.getElementById(field);
  const errorEl = document.querySelector('.field-error[data-for="' + field + '"]');
  if (key) {
    input.classList.add("invalid");
    errorEl.textContent = translations[currentLang][key];
  } else {
    input.classList.remove("invalid");
    errorEl.textContent = "";
  }
}

["name", "email", "message"].forEach(function (field) {
  document.getElementById(field).addEventListener("blur", function () {
    const value = this.value;
    const valid = rules[field](value);
    showFieldError(field, valid ? null : "err_" + field);
  });
});

// Animación del pipeline: activa cada nodo en secuencia
// Pipeline animation: lights up each node in sequence
function animateStep(stepIndex, done) {
  const node = document.querySelector('.pipeline-node[data-step="' + stepIndex + '"]');
  if (!node) return;
  node.classList.add(done ? "done" : "active");
}

function resetPipeline() {
  document.querySelectorAll(".pipeline-node").forEach(function (n) {
    n.classList.remove("active", "done");
  });
}

function triggerPulse() {
  const dot = document.getElementById("pulse-dot");
  dot.classList.remove("active");
  void dot.offsetWidth; // reinicia la animación / restarts the animation
  dot.classList.add("active");
}

function logStatus(key, cssClass) {
  const log = document.getElementById("status-log");
  const line = document.createElement("div");
  if (cssClass) line.className = cssClass;
  line.textContent = translations[currentLang][key] || key;
  log.appendChild(line);
}

const MAX_ATTACHMENT_MB = 10;
const attachmentInput = document.getElementById("attachment");
const fileNameEl = document.getElementById("file-name");

attachmentInput.addEventListener("change", function () {
  const file = this.files[0];
  if (!file) {
    fileNameEl.textContent = translations[currentLang].no_file;
    showFieldError("attachment", null);
    return;
  }
  fileNameEl.textContent = file.name;
  const tooBig = file.size > MAX_ATTACHMENT_MB * 1024 * 1024;
  showFieldError("attachment", tooBig ? "err_attachment" : null);
});

const form = document.getElementById("contact-form");
const submitBtn = document.getElementById("submit-btn");

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  const values = {
    name: document.getElementById("name").value,
    email: document.getElementById("email").value,
    message: document.getElementById("message").value,
    website: document.getElementById("website").value
  };
  const file = attachmentInput.files[0] || null;

  let hasError = false;
  ["name", "email", "message"].forEach(function (field) {
    const valid = rules[field](values[field]);
    showFieldError(field, valid ? null : "err_" + field);
    if (!valid) hasError = true;
  });
  if (file && file.size > MAX_ATTACHMENT_MB * 1024 * 1024) {
    showFieldError("attachment", "err_attachment");
    hasError = true;
  }
  if (hasError) return;

  document.getElementById("status-log").innerHTML = "";
  resetPipeline();
  submitBtn.disabled = true;

  animateStep(0, false);
  logStatus("log_validating");
  triggerPulse();
  await new Promise(function (r) { setTimeout(r, 500); });
  animateStep(0, true);

  animateStep(1, false);
  await new Promise(function (r) { setTimeout(r, 400); });
  animateStep(1, true);

  animateStep(2, false);
  logStatus("log_connecting");
  triggerPulse();

  try {
    logStatus("log_sending");
    const formData = new FormData();
    formData.append("name", values.name);
    formData.append("email", values.email);
    formData.append("message", values.message);
    formData.append("website", values.website);
    if (file) formData.append("attachment", file);

    // Sin header Content-Type: el navegador arma el boundary del multipart.
    // No Content-Type header: the browser sets the multipart boundary itself.
    const response = await fetch("/api/contact", { method: "POST", body: formData });
    const data = await response.json();

    if (data.success) {
      animateStep(2, true);
      animateStep(3, true);
      logStatus("log_success", "ok");
      form.reset();
      fileNameEl.textContent = translations[currentLang].no_file;
    } else {
      logStatus("log_fail", "err");
      const errors = data.errors || {};
      Object.keys(errors).forEach(function (field) {
        const log = document.getElementById("status-log");
        const line = document.createElement("div");
        line.className = "err";
        line.textContent = errors[field];
        log.appendChild(line);
      });
    }
  } catch (networkError) {
    logStatus("log_fail", "err");
  } finally {
    submitBtn.disabled = false;
  }
});

applyLang("es");
