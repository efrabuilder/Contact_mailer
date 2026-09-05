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
    remove.setAttribute("aria-label", "Quitar " + email);
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
    showFieldError("recipients", '"' + email + '" no es un correo válido.');
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

const attachmentsInput = document.getElementById("attachments");
const fileNameEl = document.getElementById("file-name");

attachmentsInput.addEventListener("change", function () {
  const files = Array.from(this.files);
  if (files.length === 0) {
    fileNameEl.textContent = "Ningún archivo seleccionado";
  } else if (files.length === 1) {
    fileNameEl.textContent = files[0].name;
  } else {
    fileNameEl.textContent = files.length + " archivos seleccionados";
  }
});

const form = document.getElementById("send-form");
const submitBtn = document.getElementById("submit-btn");
const statusLog = document.getElementById("status-log");

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  document.querySelectorAll(".field-error").forEach(function (el) { el.textContent = ""; });
  statusLog.innerHTML = "";

  if (recipients.length === 0) {
    showFieldError("recipients", "Agregá al menos un destinatario.");
    return;
  }

  submitBtn.disabled = true;
  statusLog.textContent = "Enviando...";

  const formData = new FormData(form);
  formData.set("recipients", recipients.join(","));

  try {
    const response = await fetch("/api/send", { method: "POST", body: formData });
    const data = await response.json();

    if (data.success) {
      statusLog.innerHTML = '<div class="ok">Correo enviado correctamente.</div>';
      form.reset();
      recipients = [];
      renderChips();
      fileNameEl.textContent = "Ningún archivo seleccionado";
    } else {
      statusLog.innerHTML = '<div class="err">No se pudo enviar el correo.</div>';
      const errors = data.errors || {};
      Object.keys(errors).forEach(function (field) {
        showFieldError(field, errors[field]);
      });
    }
  } catch (err) {
    statusLog.innerHTML = '<div class="err">No se pudo conectar con el servidor.</div>';
  } finally {
    submitBtn.disabled = false;
  }
});
