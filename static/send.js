const themeToggle = document.getElementById("theme-toggle");
themeToggle.addEventListener("click", function () {
  const html = document.documentElement;
  const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  themeToggle.querySelector(".theme-icon").textContent = next === "dark" ? "☾" : "☀";
});

const EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

const recipientInput = document.getElementById("recipient-input");
const recipientChips = document.getElementById("recipient-chips");
const recipientsHidden = document.getElementById("recipients");
let recipients = [];

function showFieldError(field, text) {
  const errorEl = document.querySelector('.field-error[data-for="' + field + '"]');
  if (errorEl) {
    errorEl.textContent = text || "";
    return;
  }
  // No hay campo asociado (ej. "server"): mostramos el motivo real en el log.
  if (text) {
    const line = document.createElement("div");
    line.className = "err";
    line.textContent = text;
    statusLog.appendChild(line);
  }
}

function renderChips() {
  recipientChips.innerHTML = "";
  recipients.forEach(function (email, index) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = email;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "chip-remove";
    remove.textContent = "×";
    remove.setAttribute("aria-label", I18N.t("remove", { email: email }));
    remove.addEventListener("click", function () {
      recipients.splice(index, 1);
      renderChips();
    });
    chip.appendChild(remove);
    recipientChips.appendChild(chip);
  });
  recipientsHidden.value = recipients.join(",");
}

function addRecipient(value) {
  const email = value.trim().replace(/,$/, "");
  if (!email) return;
  if (!EMAIL_PATTERN.test(email)) {
    showFieldError("recipients", I18N.t("invalid_email", { email: email }));
    return;
  }
  if (!recipients.includes(email)) {
    recipients.push(email);
    renderChips();
  }
  showFieldError("recipients", "");
}

recipientInput.addEventListener("keydown", function (event) {
  if (event.key === "Enter" || event.key === ",") {
    event.preventDefault();
    addRecipient(recipientInput.value);
    recipientInput.value = "";
  }
});

recipientInput.addEventListener("blur", function () {
  if (recipientInput.value.trim()) {
    addRecipient(recipientInput.value);
    recipientInput.value = "";
  }
});

// Prellenar destinatario/asunto al venir del botón "Responder" de la bandeja.
const prefillParams = new URLSearchParams(window.location.search);
const prefillTo = prefillParams.get("to");
const prefillSubject = prefillParams.get("subject");
if (prefillTo) {
  addRecipient(prefillTo);
}
if (prefillSubject) {
  document.getElementById("subject").value = prefillSubject;
}

const attachmentsInput = document.getElementById("attachments");
const fileNameEl = document.getElementById("file-name");

function updateFileName() {
  const files = Array.from(attachmentsInput.files || []);
  if (files.length === 0) {
    fileNameEl.textContent = I18N.t("no_file");
  } else if (files.length === 1) {
    fileNameEl.textContent = files[0].name;
  } else {
    fileNameEl.textContent = I18N.t("files_selected", { n: files.length });
  }
}

attachmentsInput.addEventListener("change", updateFileName);

const form = document.getElementById("send-form");
const submitBtn = document.getElementById("submit-btn");
const statusLog = document.getElementById("status-log");

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  document.querySelectorAll(".field-error").forEach(function (el) { el.textContent = ""; });
  statusLog.innerHTML = "";

  if (recipients.length === 0) {
    showFieldError("recipients", I18N.t("need_recipient"));
    return;
  }

  submitBtn.disabled = true;
  statusLog.textContent = I18N.t("sending");

  const formData = new FormData(form);
  formData.set("recipients", recipients.join(","));

  try {
    const response = await fetch("/api/send", { method: "POST", body: formData });
    const data = await response.json();

    if (data.success) {
      statusLog.innerHTML = '<div class="ok">' + I18N.t("sent_ok") + '</div>';
      form.reset();
      recipients = [];
      renderChips();
      updateFileName();
    } else {
      statusLog.innerHTML = '<div class="err">' + I18N.t("send_failed") + '</div>';
      const errors = data.errors || {};
      Object.keys(errors).forEach(function (field) {
        showFieldError(field, I18N.server(errors[field]));
      });
    }
  } catch (err) {
    statusLog.innerHTML = '<div class="err">' + I18N.t("server_unreachable") + '</div>';
  } finally {
    submitBtn.disabled = false;
  }
});

I18N.init({
  es: {
    title: "Enviar correo", heading: "Enviar correo", nav_inbox: "Bandeja",
    outlook_error: "No se pudo conectar Outlook: {error}",
    outlook_connected: "Outlook conectado.", outlook_disconnect: "Desconectar",
    outlook_connect: "Conectar cuenta de Outlook",
    label_from: "Enviar desde", no_accounts: "No hay cuentas configuradas",
    label_to: "Destinatarios", ph_to: "correo@ejemplo.com y Enter",
    label_subject: "Asunto", label_message: "Mensaje",
    label_attachments: "Adjuntar archivos (opcional)",
    no_file: "Ningún archivo seleccionado", files_selected: "{n} archivos seleccionados",
    btn_send: "Enviar correo", sending: "Enviando...",
    sent_ok: "Correo enviado correctamente.", send_failed: "No se pudo enviar el correo.",
    remove: "Quitar {email}", invalid_email: '"{email}" no es un correo válido.',
    need_recipient: "Agregá al menos un destinatario."
  },
  en: {
    title: "Send email", heading: "Send email", nav_inbox: "Inbox",
    outlook_error: "Could not connect Outlook: {error}",
    outlook_connected: "Outlook connected.", outlook_disconnect: "Disconnect",
    outlook_connect: "Connect Outlook account",
    label_from: "Send from", no_accounts: "No accounts configured",
    label_to: "Recipients", ph_to: "email@example.com and Enter",
    label_subject: "Subject", label_message: "Message",
    label_attachments: "Attach files (optional)",
    no_file: "No file selected", files_selected: "{n} files selected",
    btn_send: "Send email", sending: "Sending...",
    sent_ok: "Email sent successfully.", send_failed: "Could not send the email.",
    remove: "Remove {email}", invalid_email: '"{email}" is not a valid email.',
    need_recipient: "Add at least one recipient."
  }
}, function () {
  // El texto de "ningún archivo" depende del estado actual del input.
  if (typeof updateFileName === "function") updateFileName();
  if (typeof renderChips === "function") renderChips();
});
