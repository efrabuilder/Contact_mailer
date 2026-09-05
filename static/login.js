const themeToggle = document.getElementById("theme-toggle");
themeToggle.addEventListener("click", function () {
  const html = document.documentElement;
  const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  themeToggle.querySelector(".theme-icon").textContent = next === "dark" ? "☾" : "☀";
});

const form = document.getElementById("login-form");
const statusEl = document.getElementById("login-status");
const loginBtn = document.getElementById("login-btn");

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  statusEl.textContent = "";
  loginBtn.disabled = true;

  const formData = new FormData(form);
  try {
    const response = await fetch("/admin/login", { method: "POST", body: formData });
    const data = await response.json();
    if (data.success) {
      window.location.href = "/admin";
    } else {
      statusEl.innerHTML = '<div class="err">' + (data.error || "Usuario o clave incorrectos.") + '</div>';
    }
  } catch (err) {
    statusEl.innerHTML = '<div class="err">No se pudo conectar con el servidor.</div>';
  } finally {
    loginBtn.disabled = false;
  }
});
