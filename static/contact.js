// i18n: diccionario simple ES/EN aplicado sobre data-i18n
const translations = {
  es: {
    hero_title: "Hablemos",
    hero_lede: "Escribime tu mensaje acá abajo y te respondo directo a tu correo. Si necesitás adjuntar un archivo, también podés hacerlo.",
    feat_1: "Tu mensaje llega directo a mi bandeja de entrada",
    feat_2: "Podés adjuntar un archivo si hace falta",
    feat_3: "Te confirmo en pantalla apenas se envía",
    step_1: "Tu mensaje", step_2: "Revisión", step_3: "Envío", step_4: "Mi bandeja",
    form_title: "Escribime",
    label_name: "Nombre", label_email: "Correo", label_message: "Mensaje",
    label_attachment: "Adjuntar archivo (opcional)",
    no_file: "Ningún archivo seleccionado",
    btn_send: "Enviar mensaje",
    err_name: "El nombre es obligatorio.",
    err_email: "Ingresá un correo válido.",
    err_message: "El mensaje debe tener al menos 10 caracteres.",
    err_attachment: "El archivo no puede superar 10 MB.",
    log_validating: "Revisando tu mensaje...",
    log_connecting: "Conectando...",
    log_sending: "Enviando...",
    log_success: "¡Listo! Tu mensaje fue enviado, te responderé pronto.",
    log_fail: "No se pudo enviar tu mensaje."
  },
  en: {
    hero_title: "Let's talk",
    hero_lede: "Write your message below and I'll get it straight to my inbox. You can attach a file if you need to.",
    feat_1: "Your message goes straight to my inbox",
    feat_2: "You can attach a file if needed",
    feat_3: "You'll see a confirmation once it's sent",
    step_1: "Your message", step_2: "Review", step_3: "Sending", step_4: "My inbox",
    form_title: "Write to me",
    label_name: "Name", label_email: "Email", label_message: "Message",
    label_attachment: "Attach a file (optional)",
    no_file: "No file selected",
    btn_send: "Send message",
    err_name: "Name is required.",
    err_email: "Enter a valid email address.",
    err_message: "Message must be at least 10 characters.",
    err_attachment: "The file can't be larger than 10 MB.",
    log_validating: "Checking your message...",
    log_connecting: "Connecting...",
    log_sending: "Sending...",
    log_success: "Done! Your message was sent, I'll get back to you soon.",
    log_fail: "Your message could not be sent."
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

const themeToggle = document.getElementById("theme-toggle");
themeToggle.addEventListener("click", function () {
  const html = document.documentElement;
  const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  themeToggle.querySelector(".theme-icon").textContent = next === "dark" ? "☾" : "☀";
});

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
  void dot.offsetWidth;
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
