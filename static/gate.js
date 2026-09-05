// Solo el toggle de tema; esta pantalla no tiene formulario.
const themeToggle = document.getElementById("theme-toggle");
themeToggle.addEventListener("click", function () {
  const html = document.documentElement;
  const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  themeToggle.querySelector(".theme-icon").textContent = next === "dark" ? "☾" : "☀";
});
