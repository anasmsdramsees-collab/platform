/* Component catalogue behaviour (ADR-008).
 *
 * Three jobs, and deliberately no more:
 *   1. switch theme, direction and density on the live page;
 *   2. render the token scales from the computed styles, so the catalogue
 *      cannot drift from the CSS it documents;
 *   3. measure contrast in the browser and show the result.
 *
 * (3) is the interesting one. `libs/design-tokens` verifies the same ratios in
 * CI from tokens.json; this recomputes them from what the browser actually
 * painted. The two agreeing is worth more than either alone, because it catches
 * the case where the CSS and the JSON have parted company.
 *
 * DOM is built with createElement and textContent, never innerHTML — the same
 * rule the console follows.
 */

(function () {
  "use strict";

  var root = document.documentElement;

  // ── token reading ──

  function tokenValue(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  /* Resolve any CSS colour to [r, g, b] by letting the browser do it. Tokens
   * are hex today, but this keeps working if one ever becomes a colour
   * function. */
  var probe = document.createElement("span");
  probe.style.display = "none";
  document.body.appendChild(probe);

  function rgbOf(colour) {
    probe.style.color = "";
    probe.style.color = colour;
    var computed = getComputedStyle(probe).color;
    var parts = computed.match(/-?[\d.]+/g);
    if (!parts || parts.length < 3) {
      return null;
    }
    return [Number(parts[0]), Number(parts[1]), Number(parts[2])];
  }

  // ── WCAG 2.2 contrast ──

  function channelLuminance(value) {
    var scaled = value / 255;
    return scaled <= 0.04045
      ? scaled / 12.92
      : Math.pow((scaled + 0.055) / 1.055, 2.4);
  }

  function relativeLuminance(rgb) {
    return (
      0.2126 * channelLuminance(rgb[0]) +
      0.7152 * channelLuminance(rgb[1]) +
      0.0722 * channelLuminance(rgb[2])
    );
  }

  function contrastRatio(foreground, background) {
    var a = rgbOf(foreground);
    var b = rgbOf(background);
    if (!a || !b) {
      return null;
    }
    var lighter = relativeLuminance(a);
    var darker = relativeLuminance(b);
    if (lighter < darker) {
      var swap = lighter;
      lighter = darker;
      darker = swap;
    }
    return (lighter + 0.05) / (darker + 0.05);
  }

  // ── small DOM helpers ──

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function clear(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  // ── swatches ──

  function renderSwatches() {
    document.querySelectorAll("[data-swatches]").forEach(function (host) {
      clear(host);
      host.dataset.swatches.split(",").forEach(function (name) {
        var token = "--" + name.trim();
        var value = tokenValue(token);
        var swatch = element("div", "swatch");
        var chip = element("div", "swatch__chip");
        chip.style.background = "var(" + token + ")";
        var meta = element("div", "swatch__meta");
        meta.appendChild(element("span", null, name.trim()));
        meta.appendChild(element("span", "swatch__value identifier", value));
        swatch.appendChild(chip);
        swatch.appendChild(meta);
        host.appendChild(swatch);
      });
    });
  }

  // ── contrast readout ──

  /* The pairs a user can actually see. Kept in step with the audit in
   * `libs/design-tokens/src/syltra_design_tokens/tokens.py`. */
  var TEXT_PAIRS = [
    ["text-primary", "background"],
    ["text-secondary", "surface"],
    ["text-tertiary", "surface"],
    ["accent", "surface"],
    ["status-critical", "surface"],
    ["status-warning", "surface"],
    ["status-success", "surface"],
    ["status-info", "surface"],
  ];
  var NON_TEXT_PAIRS = [
    ["border-strong", "surface"],
    ["focus-ring", "background"],
  ];

  function renderContrast() {
    var host = document.querySelector("[data-contrast-summary]");
    if (!host) {
      return;
    }
    clear(host);

    var checked = 0;
    var worstText = Infinity;
    var worstNonText = Infinity;
    var failures = 0;

    function measure(pairs, bar, track) {
      pairs.forEach(function (pair) {
        var ratio = contrastRatio(
          tokenValue("--" + pair[0]),
          tokenValue("--" + pair[1])
        );
        if (ratio === null) {
          return;
        }
        checked += 1;
        if (ratio < bar) {
          failures += 1;
        }
        track(ratio);
      });
    }

    measure(TEXT_PAIRS, 4.5, function (ratio) {
      worstText = Math.min(worstText, ratio);
    });
    measure(NON_TEXT_PAIRS, 3, function (ratio) {
      worstNonText = Math.min(worstNonText, ratio);
    });

    function stat(label, value) {
      var wrap = element("span", null, label + " ");
      wrap.appendChild(element("strong", null, value));
      host.appendChild(wrap);
    }

    stat("Pairs measured:", String(checked));
    stat("Lowest text ratio:", worstText.toFixed(2) + ":1 (needs 4.5)");
    stat("Lowest boundary ratio:", worstNonText.toFixed(2) + ":1 (needs 3.0)");
    stat("Failing:", String(failures));
  }

  // ── scales ──

  var TYPE_STEPS = [
    "display",
    "page-title",
    "section-title",
    "card-title",
    "body-large",
    "body",
    "label",
    "caption",
    "metric-large",
    "metric",
  ];

  var SAMPLE = {
    ltr: "Smart living, seamlessly connected",
    rtl: "حياة ذكية، متصلة بسلاسة",
  };

  function renderTypeRamp() {
    var host = document.querySelector("[data-type-ramp]");
    if (!host) {
      return;
    }
    clear(host);
    var direction = root.getAttribute("dir") === "rtl" ? "rtl" : "ltr";
    TYPE_STEPS.forEach(function (step) {
      var row = element("div", "ramp__row");
      var size = tokenValue("--type-" + step + "-size");
      row.appendChild(element("span", "ramp__key identifier", step + " · " + size));
      var sample = element("span", "type-" + step);
      sample.textContent = step.indexOf("metric") === 0 ? "23.4 °C" : SAMPLE[direction];
      row.appendChild(sample);
      host.appendChild(row);
    });
  }

  var SPACE_STEPS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16];

  function renderSpaceRuler() {
    var host = document.querySelector("[data-space-ruler]");
    if (!host) {
      return;
    }
    clear(host);
    SPACE_STEPS.forEach(function (step) {
      var token = "--space-" + step;
      var row = element("div", "ruler__row");
      row.appendChild(
        element("span", "ruler__key identifier", "space-" + step + " · " + tokenValue(token))
      );
      var bar = element("div", "ruler__bar");
      bar.style.inlineSize = "var(" + token + ")";
      row.appendChild(bar);
      host.appendChild(row);
    });
  }

  var RADII = ["sm", "md", "lg", "xl", "round"];

  function renderRadii() {
    var host = document.querySelector("[data-radius-samples]");
    if (!host) {
      return;
    }
    clear(host);
    RADII.forEach(function (name) {
      var sample = element("div", "radius-sample", name);
      sample.style.borderRadius = "var(--radius-" + name + ")";
      host.appendChild(sample);
    });
  }

  function renderBidiSample() {
    var node = document.querySelector("[data-bidi-sample]");
    if (!node) {
      return;
    }
    var rtl = root.getAttribute("dir") === "rtl";
    clear(node);
    if (rtl) {
      node.appendChild(document.createTextNode("أبلغ مستشعر المطبخ "));
      node.appendChild(element("span", "identifier", "sensor.kitchen_temp_01"));
      node.appendChild(document.createTextNode(" عن "));
      node.appendChild(element("span", "numeric", "23.4"));
      node.appendChild(document.createTextNode(" °م."));
    } else {
      node.appendChild(document.createTextNode("The kitchen sensor "));
      node.appendChild(element("span", "identifier", "sensor.kitchen_temp_01"));
      node.appendChild(document.createTextNode(" last reported "));
      node.appendChild(element("span", "numeric", "23.4"));
      node.appendChild(document.createTextNode(" °C."));
    }
  }

  function renderAll() {
    renderSwatches();
    renderContrast();
    renderTypeRamp();
    renderSpaceRuler();
    renderRadii();
    renderBidiSample();
  }

  // ── controls ──

  function bind(id, apply) {
    var control = document.getElementById(id);
    if (!control) {
      return;
    }
    control.addEventListener("change", function () {
      // The switch is applied first, or the readout would describe the theme
      // the page just left. No rAF: reading a computed style forces the style
      // recalc synchronously, and rAF does not fire in a background tab — a
      // readout that only updates in a foreground tab is a readout that lies.
      apply(control.value);
      renderAll();
    });
  }

  bind("theme", function (value) {
    root.setAttribute("data-theme", value);
  });

  bind("direction", function (value) {
    root.setAttribute("dir", value);
    root.setAttribute("lang", value === "rtl" ? "ar" : "en");
  });

  bind("density", function (value) {
    root.setAttribute("data-density", value);
  });

  // The switch component is a specimen, not a control, but it should still
  // behave — a toggle that never toggles cannot be inspected in both states.
  document.querySelectorAll('[role="switch"]').forEach(function (node) {
    node.addEventListener("click", function () {
      node.setAttribute(
        "aria-checked",
        node.getAttribute("aria-checked") === "true" ? "false" : "true"
      );
    });
  });

  document.querySelectorAll('[role="tab"]').forEach(function (node) {
    node.addEventListener("click", function () {
      node.parentNode.querySelectorAll('[role="tab"]').forEach(function (sibling) {
        sibling.setAttribute("aria-selected", String(sibling === node));
      });
    });
  });

  renderAll();
})();
