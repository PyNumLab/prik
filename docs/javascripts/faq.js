(function () {
  "use strict";

  function openLinkedQuestion() {
    if (!window.location.hash) {
      return;
    }

    const id = decodeURIComponent(window.location.hash.slice(1));
    const target = document.getElementById(id);
    if (!target || !target.matches("details.prik-faq-item")) {
      return;
    }

    target.open = true;
    window.requestAnimationFrame(function () {
      target.scrollIntoView({ block: "start" });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", openLinkedQuestion);
  } else {
    openLinkedQuestion();
  }
  window.addEventListener("hashchange", openLinkedQuestion);
})();
