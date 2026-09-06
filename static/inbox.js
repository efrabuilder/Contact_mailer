const themeToggle = document.getElementById("theme-toggle");
themeToggle.addEventListener("click", function () {
  const html = document.documentElement;
  const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  themeToggle.querySelector(".theme-icon").textContent = next === "dark" ? "☾" : "☀";
});

// Las fechas vienen como timestamp Unix (segundos) en data-timestamp; se
// formatean en el navegador para respetar la zona horaria de quien mira.
document.querySelectorAll("[data-timestamp]").forEach(function (el) {
  const seconds = parseFloat(el.getAttribute("data-timestamp"));
  if (!seconds) return;
  const date = new Date(seconds * 1000);
  el.textContent = date.toLocaleString("es-CR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
});

const deleteForm = document.getElementById("delete-form");
if (deleteForm) {
  deleteForm.addEventListener("submit", function (event) {
    if (!window.confirm("¿Eliminar este mensaje de la bandeja? Esta acción no se puede deshacer.")) {
      event.preventDefault();
    }
  });
}
