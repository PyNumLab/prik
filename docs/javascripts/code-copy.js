(function () {
  "use strict";

  const copyIcon = `
    <svg class="x2py-copy-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="8" y="8" width="12" height="13" rx="2"></rect>
      <path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"></path>
    </svg>`;
  const copiedIcon = `
    <svg class="x2py-copied-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="m5 12 4 4L19 6"></path>
    </svg>`;

  function fallbackCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();

    try {
      if (!document.execCommand("copy")) {
        throw new Error("The browser rejected the copy command.");
      }
    } finally {
      textarea.remove();
    }
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    fallbackCopy(text);
  }

  function addCopyButton(code) {
    const pre = code.closest("pre");
    if (!pre) {
      return;
    }

    const parent = pre.parentElement;
    const host =
      parent && (parent.classList.contains("highlight") || parent.classList.contains("codehilite"))
        ? parent
        : pre;
    if (host.classList.contains("x2py-copy-host")) {
      return;
    }

    host.classList.add("x2py-copy-host");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "x2py-code-copy";
    button.setAttribute("aria-label", "Copy code to clipboard");
    button.title = "Copy";
    button.innerHTML = copyIcon + copiedIcon;

    let resetTimer;
    button.addEventListener("click", async function () {
      window.clearTimeout(resetTimer);
      button.disabled = true;
      try {
        await copyText(code.textContent);
        button.classList.add("is-copied");
        button.setAttribute("aria-label", "Copied to clipboard");
        button.title = "Copied";
      } catch (_error) {
        button.classList.add("is-error");
        button.setAttribute("aria-label", "Could not copy to clipboard");
        button.title = "Copy failed";
      } finally {
        button.disabled = false;
        resetTimer = window.setTimeout(function () {
          button.classList.remove("is-copied", "is-error");
          button.setAttribute("aria-label", "Copy code to clipboard");
          button.title = "Copy";
        }, 2000);
      }
    });

    host.appendChild(button);
  }

  function addCopyButtons() {
    document.querySelectorAll("pre code").forEach(addCopyButton);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addCopyButtons);
  } else {
    addCopyButtons();
  }
})();
