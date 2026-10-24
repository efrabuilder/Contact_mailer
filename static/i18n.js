// i18n: cambio de idioma ES/EN para la página de envío (send.html)
// i18n: ES/EN language switching for the send page (send.html)
// Uso / Usage: I18N.init({ es: {...}, en: {...} }, onChange)
const I18N = (function () {
  const STORAGE_KEY = "lang";                 // clave donde se guarda el idioma elegido
  let dictionary = { es: {}, en: {} };        // diccionarios que manda cada página
  let currentLang = "es";                     // idioma actual (español por defecto)
  let onChangeCallback = null;                // función extra que se llama al cambiar idioma

  // Mensajes del servidor (en español) y su traducción al inglés.
  // Server messages (Spanish) and their English translation.
  const SERVER_EN = [
    [/^El mensaje es obligatorio\.$/, function () { return "The message is required."; }],
    [/^El asunto es obligatorio\.$/, function () { return "The subject is required."; }],
    [/^Agregá al menos un destinatario\.$/, function () { return "Add at least one recipient."; }],
    [/^"(.+)" no es un correo válido\.$/, function (m) { return '"' + m[1] + '" is not a valid email.'; }],
    [/^El asunto no puede superar (\d+) caracteres\.$/, function (m) { return "The subject can't exceed " + m[1] + " characters."; }],
    [/^El mensaje no puede superar (\d+) caracteres\.$/, function (m) { return "The message can't exceed " + m[1] + " characters."; }],
    [/^"(.+)" supera los (\d+) MB\.$/, function (m) { return '"' + m[1] + '" exceeds ' + m[2] + " MB."; }],
    [/^El total de adjuntos no puede superar (\d+) MB\.$/, function (m) { return "Total attachments can't exceed " + m[1] + " MB."; }],
    [/^Elegí la cuenta desde la que querés enviar\.$/, function () { return "Choose the account you want to send from."; }]
  ];

  // Reemplaza {variable} por su valor / Replaces {variable} with its value
  function format(text, vars) {
    if (!vars) return text;
    return text.replace(/\{(\w+)\}/g, function (match, name) {
      return vars[name] !== undefined ? vars[name] : match;
    });
  }

  // Devuelve el texto traducido (si no existe en el idioma actual, usa español)
  // Returns the translated text (falls back to Spanish if missing)
  function t(key, vars) {
    const table = dictionary[currentLang] || {};
    const fallback = dictionary.es || {};
    const text = table[key] !== undefined ? table[key] : (fallback[key] !== undefined ? fallback[key] : key);
    return format(text, vars);
  }

  // Traduce un mensaje que viene del servidor / Translates a server-sent message
  function server(message) {
    if (currentLang === "es" || typeof message !== "string") return message;
    for (let i = 0; i < SERVER_EN.length; i++) {
      const match = message.match(SERVER_EN[i][0]);
      if (match) return SERVER_EN[i][1](match);
    }
    return message; // sin traducción conocida: se muestra tal cual
  }

  // Aplica el idioma actual a todos los elementos marcados de la página
  // Applies the current language to every marked element on the page
  function apply() {
    document.documentElement.lang = currentLang;

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      const key = el.getAttribute("data-i18n");
      const vars = el.hasAttribute("data-v-error") ? { error: el.getAttribute("data-v-error") } : null;
      if (dictionary[currentLang] && dictionary[currentLang][key] !== undefined) {
        el.textContent = format(dictionary[currentLang][key], vars);
      }
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")));
    });

    document.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")));
    });

    // Botón de idioma y de tema (textos del aria-label)
    const langBtn = document.getElementById("lang-toggle");
    if (langBtn) langBtn.setAttribute("aria-label", currentLang === "es" ? "Cambiar idioma" : "Change language");
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) themeBtn.setAttribute("aria-label", currentLang === "es" ? "Cambiar tema" : "Toggle theme");

    if (typeof onChangeCallback === "function") onChangeCallback(currentLang);
  }

  // Cambia el idioma y lo guarda en el navegador / Switches language and stores it
  function setLang(lang) {
    currentLang = lang === "en" ? "en" : "es";
    try { localStorage.setItem(STORAGE_KEY, currentLang); } catch (e) { /* sin storage, no pasa nada */ }
    apply();
  }

  // Arranque: recibe los diccionarios y conecta el botón ES / EN
  // Startup: receives the dictionaries and wires up the ES / EN button
  function init(dict, callback) {
    dictionary = dict || dictionary;
    onChangeCallback = callback || null;

    let saved = "es";
    try { saved = localStorage.getItem(STORAGE_KEY) || "es"; } catch (e) { /* ignorar */ }
    currentLang = saved === "en" ? "en" : "es";

    const langBtn = document.getElementById("lang-toggle");
    if (langBtn) {
      langBtn.addEventListener("click", function () {
        setLang(currentLang === "es" ? "en" : "es");
      });
    }

    apply();
  }

  return { init: init, t: t, server: server, setLang: setLang, get lang() { return currentLang; } };
})();
