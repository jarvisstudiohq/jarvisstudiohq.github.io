/* Shows the support email from config.js wherever a page has a [data-support-email] element. No cookies, no storage, no network. */
(function () {
  var cfg = window.SITE_CONFIG || {};
  var email = String(cfg.supportEmail || "").trim();
  if (!email) return;
  var nodes = document.querySelectorAll("[data-support-email]");
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    el.textContent = email;
    if (el.tagName === "A") {
      var subject = el.getAttribute("data-subject");
      el.setAttribute("href", "mailto:" + email + (subject ? "?subject=" + encodeURIComponent(subject) : ""));
    }
  }
})();
