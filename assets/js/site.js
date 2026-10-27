/* Jarvis Studios website. No cookies, no storage, no network.
 * 1. Shows the support email from config.js wherever a page has a [data-support-email] element.
 * 2. The mobile menu button and the Games dropdown (real buttons with aria-expanded; Escape closes them).
 * 3. The screenshot lightbox: a link with [data-lightbox] opens its image in a <dialog>. Without JavaScript the link opens the image.
 */
(function () {
  var cfg = window.SITE_CONFIG || {};
  var email = String(cfg.supportEmail || "").trim();
  if (email) {
    var nodes = document.querySelectorAll("[data-support-email]");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      el.textContent = email;
      if (el.tagName === "A") {
        var subject = el.getAttribute("data-subject");
        el.setAttribute("href", "mailto:" + email + (subject ? "?subject=" + encodeURIComponent(subject) : ""));
      }
    }
  }

  function setOpen(btn, open) {
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  }

  // ---- mobile menu
  var menuBtn = document.querySelector(".menu-toggle");
  var nav = document.getElementById("site-nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = menuBtn.getAttribute("aria-expanded") !== "true";
      setOpen(menuBtn, open);
      document.body.classList.toggle("menu-open", open);
    });
  }

  // ---- Games dropdown
  var subBtns = document.querySelectorAll(".sub-toggle");
  function closeSubs(except) {
    for (var j = 0; j < subBtns.length; j++) if (subBtns[j] !== except) setOpen(subBtns[j], false);
  }
  for (var k = 0; k < subBtns.length; k++) {
    subBtns[k].addEventListener("click", function (e) {
      var b = e.currentTarget;
      var open = b.getAttribute("aria-expanded") !== "true";
      closeSubs(b);
      setOpen(b, open);
    });
  }
  document.addEventListener("click", function (e) {
    if (!e.target.closest || !e.target.closest(".has-sub")) closeSubs(null);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    for (var j = 0; j < subBtns.length; j++) {
      if (subBtns[j].getAttribute("aria-expanded") === "true") {
        setOpen(subBtns[j], false);
        subBtns[j].focus();
        return;
      }
    }
    if (menuBtn && menuBtn.getAttribute("aria-expanded") === "true") {
      setOpen(menuBtn, false);
      document.body.classList.remove("menu-open");
      menuBtn.focus();
    }
  });
  // Leaving the dropdown with Tab closes it.
  var subs = document.querySelectorAll(".has-sub");
  for (var s = 0; s < subs.length; s++) {
    subs[s].addEventListener("focusout", function (e) {
      var li = e.currentTarget;
      if (e.relatedTarget && !li.contains(e.relatedTarget)) closeSubs(null);
    });
  }

  // ---- screenshot lightbox
  var links = document.querySelectorAll("a[data-lightbox]");
  if (links.length && typeof HTMLDialogElement === "function") {
    var dlg = document.createElement("dialog");
    dlg.className = "lightbox";
    dlg.setAttribute("aria-label", "Screenshot");
    dlg.innerHTML = '<figure><img alt=""><figcaption></figcaption></figure>' +
      '<button class="lightbox-close" type="button">Close</button>';
    document.body.appendChild(dlg);
    var img = dlg.querySelector("img");
    var cap = dlg.querySelector("figcaption");
    var opener = null;
    dlg.querySelector(".lightbox-close").addEventListener("click", function () { dlg.close(); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener("close", function () { if (opener) opener.focus(); });
    for (var n = 0; n < links.length; n++) {
      links[n].addEventListener("click", function (e) {
        var a = e.currentTarget;
        var thumb = a.querySelector("img");
        e.preventDefault();
        opener = a;
        img.src = a.getAttribute("href");
        img.alt = thumb ? thumb.alt : "";
        cap.textContent = a.getAttribute("data-caption") || "";
        dlg.showModal();
      });
    }
  }
})();
