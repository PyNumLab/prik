(function () {
  "use strict";

  function activateTab(tabs, panels, selected) {
    const panelId = selected.getAttribute("aria-controls");
    tabs.forEach(function (tab) {
      const isSelected = tab === selected;
      tab.setAttribute("aria-selected", String(isSelected));
      tab.tabIndex = isSelected ? 0 : -1;
    });
    panels.forEach(function (panel) {
      panel.hidden = panel.id !== panelId;
    });
  }

  function activateFragmentTab(example, tabs, panels) {
    if (!window.location.hash) {
      return false;
    }

    const target = document.getElementById(window.location.hash.slice(1));
    const panel = target && target.closest(".prik-example-panel");
    if (!panel || !example.contains(panel)) {
      return false;
    }

    const tab = tabs.find(function (candidate) {
      return candidate.getAttribute("aria-controls") === panel.id;
    });
    if (!tab) {
      return false;
    }

    activateTab(tabs, panels, tab);
    return true;
  }

  function initialiseExampleTabs(example) {
    const tabs = Array.from(example.querySelectorAll('[role="tab"]'));
    const panels = tabs
      .map(function (tab) {
        return document.getElementById(tab.getAttribute("aria-controls"));
      })
      .filter(Boolean);
    if (tabs.length < 2 || panels.length !== tabs.length) {
      return;
    }

    const selected = tabs.find(function (tab) {
      return tab.getAttribute("aria-selected") === "true";
    }) || tabs[0];
    if (!activateFragmentTab(example, tabs, panels)) {
      activateTab(tabs, panels, selected);
    }

    tabs.forEach(function (tab, index) {
      tab.addEventListener("click", function () {
        activateTab(tabs, panels, tab);
      });
      tab.addEventListener("keydown", function (event) {
        const offsets = { ArrowLeft: -1, ArrowRight: 1, Home: -index, End: tabs.length - index - 1 };
        if (!(event.key in offsets)) {
          return;
        }
        event.preventDefault();
        const nextIndex = (index + offsets[event.key] + tabs.length) % tabs.length;
        const next = tabs[nextIndex];
        activateTab(tabs, panels, next);
        next.focus();
      });
    });

    window.addEventListener("hashchange", function () {
      activateFragmentTab(example, tabs, panels);
    });
  }

  function initialiseExampleTabSets() {
    document.querySelectorAll("[data-prik-example-tabs]").forEach(initialiseExampleTabs);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialiseExampleTabSets);
  } else {
    initialiseExampleTabSets();
  }
})();
