(function () {
  "use strict";

  const termDefinitions = {
    ".pyf": {
      id: "pyf",
      label: "What is a .pyf file?",
      text: "An f2py signature file. It describes the Fortran routines and interface used to generate a Python extension.",
    },
    ".pyi": {
      id: "pyi",
      label: "What is a .pyi file?",
      text: "A Python stub file standardized by PEP 484. It contains type hints and API signatures rather than executable runtime code. In PRIK, a semantic .pyi file is also an editable contract for the Python API and its mapping to native procedures.",
    },
  };
  const textTermDefinitions = {
    abi: {
      id: "abi",
      label: "What is an ABI?",
      text: "Application Binary Interface: the low-level rules that let Python and compiled code communicate correctly. They define how functions receive arguments, how values are represented in memory, and how functions return results.",
    },
    "c-order": {
      id: "c-order",
      label: "What is C-order?",
      text: "C-style, row-major array layout: values in the last index are next to each other in memory.",
    },
    "f-order": {
      id: "f-order",
      label: "What is F-order?",
      text: "Fortran-style, column-major array layout: values in the first index are next to each other in memory.",
    },
    gil: {
      id: "gil",
      label: "What is the GIL?",
      text: "Global Interpreter Lock: CPython's lock around interpreter execution. Native code may release it only when it does not need to access Python objects.",
    },
    "semantic ir": {
      id: "semantic-ir",
      label: "What is semantic IR?",
      text: "Semantic intermediate representation: PRIK's shared, language-neutral model of an API. Source and .pyi contracts are converted into this model before PRIK decides how to build the wrapper.",
    },
  };
  const textTermPattern = /\b(?:ABI|semantic IR|Fortran-order|F-order|C-order|GIL)\b/gi;

  function normalisePath(path) {
    return path.replace(/index\.html$/, "").replace(/\/+$/, "/");
  }

  function supportsTermTooltips() {
    const homeLink = document.querySelector(".wy-side-nav-search > a");
    const currentPath = normalisePath(window.location.pathname);
    const homePath = homeLink
      ? normalisePath(new URL(homeLink.getAttribute("href"), window.location.href).pathname)
      : "";

    return currentPath === homePath || /\/user(?:\/|$)/.test(currentPath);
  }

  function setOpen(wrapper, isOpen) {
    const trigger = wrapper.querySelector(".prik-term-trigger");
    wrapper.classList.toggle("is-open", isOpen);
    if (trigger.hasAttribute("aria-expanded")) {
      trigger.setAttribute("aria-expanded", String(isOpen));
    }
    if (isOpen) {
      window.requestAnimationFrame(function () {
        positionTooltip(wrapper);
      });
    }
  }

  function positionTooltip(wrapper) {
    const tooltip = wrapper.querySelector(".prik-term-tooltip");
    const trigger = wrapper.querySelector(".prik-term-trigger");
    const margin = 12;
    const viewportWidth = document.documentElement.clientWidth;
    const viewportHeight = document.documentElement.clientHeight;
    const triggerBounds = trigger.getBoundingClientRect();
    const tooltipWidth = tooltip.offsetWidth;
    const tooltipHeight = tooltip.offsetHeight;
    const preferredLeft = triggerBounds.left + triggerBounds.width / 2;
    const left = Math.min(
      Math.max(preferredLeft, margin + tooltipWidth / 2),
      viewportWidth - margin - tooltipWidth / 2,
    );
    let top = triggerBounds.top - tooltipHeight - margin;
    const opensBelow = top < margin;

    if (opensBelow) {
      top = Math.min(triggerBounds.bottom + margin, viewportHeight - tooltipHeight - margin);
    }
    tooltip.classList.toggle("prik-term-tooltip-below", opensBelow);
    tooltip.style.left = Math.round(left) + "px";
    tooltip.style.top = Math.round(Math.max(margin, top)) + "px";
  }

  function repositionOpenTooltips() {
    document.querySelectorAll(".prik-term-wrap.is-open").forEach(positionTooltip);
  }

  function closeAll(except) {
    document.querySelectorAll(".prik-term-wrap.is-open").forEach(function (wrapper) {
      if (wrapper !== except) {
        setOpen(wrapper, false);
      }
    });
  }

  function createTooltip(visibleTerm, definition, index, link) {
    const wrapper = document.createElement("span");
    const trigger = document.createElement(link ? "span" : "button");
    const tooltip = document.createElement("span");
    const tooltipId = "prik-" + definition.id + "-tooltip-" + index;

    wrapper.className = "prik-term-wrap";
    trigger.className = "prik-term-trigger";
    if (link) {
      const describedBy = link.getAttribute("aria-describedby");
      link.setAttribute("aria-describedby", [describedBy, tooltipId].filter(Boolean).join(" "));
    } else {
      trigger.type = "button";
      trigger.setAttribute("aria-describedby", tooltipId);
      trigger.setAttribute("aria-expanded", "false");
      trigger.setAttribute("aria-label", definition.label);
    }
    tooltip.className = "prik-term-tooltip";
    tooltip.id = tooltipId;
    tooltip.setAttribute("role", "tooltip");
    tooltip.textContent = definition.text;

    trigger.append(visibleTerm);
    wrapper.append(trigger, tooltip);

    const control = link || trigger;
    control.addEventListener("focus", function () {
      closeAll(wrapper);
      setOpen(wrapper, true);
    });
    control.addEventListener("blur", function () {
      setOpen(wrapper, false);
    });
    control.addEventListener("pointerenter", function () {
      closeAll(wrapper);
      setOpen(wrapper, true);
    });
    control.addEventListener("pointerleave", function () {
      if (document.activeElement !== control) {
        setOpen(wrapper, false);
      }
    });
    if (!link) {
      trigger.addEventListener("click", function () {
        closeAll(wrapper);
        setOpen(wrapper, true);
      });
      trigger.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          setOpen(wrapper, false);
          trigger.blur();
        }
      });
    }

    return wrapper;
  }

  function enhanceCodeTerm(term, index) {
    const definition = termDefinitions[term.textContent];
    const wrapper = createTooltip(term.cloneNode(true), definition, index, term.closest("a"));
    term.replaceWith(wrapper);
  }

  function textDefinition(match) {
    const normalized = match.toLowerCase();
    if (normalized === "fortran-order") {
      return textTermDefinitions["f-order"];
    }
    return textTermDefinitions[normalized];
  }

  function isPlainTextTerm(node) {
    const parent = node.parentElement;
    return parent && node.nodeValue.trim() && !parent.closest("button, code, h1, h2, h3, h4, h5, h6, pre, script, style, .prik-term-wrap");
  }

  function sectionFor(element) {
    const headings = document.querySelectorAll(".rst-content h1, .rst-content h2, .rst-content h3, .rst-content h4, .rst-content h5, .rst-content h6");
    let section = 0;

    headings.forEach(function (heading, index) {
      if (heading.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING) {
        section = index + 1;
      }
    });
    return section;
  }

  function enhanceCodeTerms() {
    const seenBySection = new Map();
    let index = 0;
    const documentedTerms = Array.from(document.querySelectorAll(".rst-content code")).filter(function (term) {
      return Object.prototype.hasOwnProperty.call(termDefinitions, term.textContent) && !term.closest("pre, button, h1, h2, h3, h4, h5, h6");
    });

    documentedTerms.forEach(function (term) {
      const section = sectionFor(term);
      const seen = seenBySection.get(section) || new Set();
      const definition = termDefinitions[term.textContent];

      if (!seen.has(definition.id)) {
        enhanceCodeTerm(term, index);
        seen.add(definition.id);
        index += 1;
      }
      seenBySection.set(section, seen);
    });
    return { index: index, seenBySection: seenBySection };
  }

  function enhanceTextTerms(startIndex, seenBySection) {
    const content = document.querySelector(".rst-content");
    let index = startIndex;
    if (!content) {
      return;
    }

    const walker = document.createTreeWalker(content, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    const textNodes = [];
    let section = 0;
    while (walker.nextNode()) {
      if (walker.currentNode.nodeType === Node.ELEMENT_NODE && walker.currentNode.matches("h1, h2, h3, h4, h5, h6")) {
        section += 1;
      } else if (walker.currentNode.nodeType === Node.TEXT_NODE && isPlainTextTerm(walker.currentNode)) {
        textNodes.push({ node: walker.currentNode, section: section });
      }
    }

    textNodes.forEach(function (entry) {
      const node = entry.node;
      const seen = seenBySection.get(entry.section) || new Set();
      const fragment = document.createDocumentFragment();
      const text = node.nodeValue;
      let lastIndex = 0;
      let changed = false;
      let match;

      textTermPattern.lastIndex = 0;
      while ((match = textTermPattern.exec(text))) {
        const definition = textDefinition(match[0]);
        fragment.append(document.createTextNode(text.slice(lastIndex, match.index)));
        if (seen.has(definition.id)) {
          fragment.append(document.createTextNode(match[0]));
        } else {
          const visibleTerm = document.createElement("span");
          visibleTerm.className = "prik-term-label";
          visibleTerm.textContent = match[0];
          fragment.append(createTooltip(visibleTerm, definition, index, node.parentElement.closest("a")));
          seen.add(definition.id);
          index += 1;
        }
        lastIndex = match.index + match[0].length;
        changed = true;
      }

      if (changed) {
        fragment.append(document.createTextNode(text.slice(lastIndex)));
        node.replaceWith(fragment);
      }
      seenBySection.set(entry.section, seen);
    });
  }

  function initialiseTooltips() {
    if (!supportsTermTooltips()) {
      return;
    }

    const enhancedCodeTerms = enhanceCodeTerms();
    enhanceTextTerms(enhancedCodeTerms.index, enhancedCodeTerms.seenBySection);

    document.addEventListener("pointerdown", function (event) {
      if (!event.target.closest(".prik-term-wrap")) {
        closeAll();
      }
    });
    window.addEventListener("resize", repositionOpenTooltips);
    window.addEventListener("scroll", repositionOpenTooltips, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialiseTooltips);
  } else {
    initialiseTooltips();
  }
})();
