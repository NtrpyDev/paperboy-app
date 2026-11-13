/* Paperboy explainer kit v1: small helpers every explainer page shares.
   Loaded after d3, Plot, and KaTeX. Exposes one global, PB.
   Pages draw their own visuals with d3, Plot, SVG, or canvas; PB supplies theme colors,
   responsive charts, scroll steps, sliders, toggles, animation loops, glossary terms, and tables. */
(function () {
  "use strict";

  var PB = {};
  var errors = (window.__pbErrors = []);
  window.addEventListener("error", function (e) {
    errors.push(String((e.error && e.error.stack) || e.message || e));
  });
  window.addEventListener("unhandledrejection", function (e) {
    errors.push("unhandled rejection: " + String((e.reason && e.reason.stack) || e.reason));
  });

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
  PB.reducedMotion = function () {
    return reducedMotion.matches || document.documentElement.dataset.motion === "off";
  };

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") node.textContent = attrs[k];
      else if (k === "class") node.className = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }
  PB.el = el;

  function resolve(target) {
    var node = typeof target === "string" ? document.querySelector(target) : target;
    if (!node) throw new Error("PB: target not found: " + target);
    return node;
  }

  /* Theme colors as plain strings, read from the CSS tokens in effect at `scope`
     (pass an element inside a .pb-stage to get the stage's always-dark values). */
  PB.theme = function (scope) {
    var cs = getComputedStyle(scope ? resolve(scope) : document.documentElement);
    function v(name) { return cs.getPropertyValue(name).trim(); }
    var series = [1, 2, 3, 4, 5, 6, 7, 8].map(function (i) { return v("--pb-s" + i); });
    return {
      page: v("--pb-page"), surface: v("--pb-surface"), raised: v("--pb-raised"),
      ink: v("--pb-ink"), ink2: v("--pb-ink-2"), muted: v("--pb-muted"),
      grid: v("--pb-grid"), axis: v("--pb-axis"), accent: v("--pb-accent"),
      deemph: v("--pb-deemph"), series: series,
      seq: [1, 2, 3, 4, 5, 6, 7].map(function (i) { return v("--pb-seq-" + i); }),
      diverging: [v("--pb-div-neg"), v("--pb-div-mid"), v("--pb-div-pos")],
      good: v("--pb-good"), warning: v("--pb-warning"), serious: v("--pb-serious"), critical: v("--pb-critical"),
      font: v("--pb-font")
    };
  };

  /* Re-run `fn` when the theme or the element's width changes. Returns a function that stops it. */
  var themeListeners = [];
  function onThemeChange() { themeListeners.slice().forEach(function (f) { f(); }); }
  darkQuery.addEventListener("change", onThemeChange);
  new MutationObserver(onThemeChange).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  PB.responsive = function (target, fn) {
    var node = resolve(target);
    var lastWidth = -1;
    var queued = false;
    function run() {
      queued = false;
      var width = Math.floor(node.clientWidth);
      if (width <= 0) return;
      lastWidth = width;
      fn(width, PB.theme(node));
    }
    function schedule() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(run);
    }
    var ro = new ResizeObserver(function () {
      if (Math.floor(node.clientWidth) !== lastWidth) schedule();
    });
    ro.observe(node);
    themeListeners.push(schedule);
    run();
    return function () {
      ro.disconnect();
      themeListeners.splice(themeListeners.indexOf(schedule), 1);
    };
  };

  /* A responsive Observable Plot chart.
     build({Plot, d3, theme, width}) returns Plot options (or a finished element).
     Defaults applied: kit font, ink colors, transparent background, hairline grid. */
  PB.plot = function (target, build) {
    var node = resolve(target);
    node.classList.add("pb-plot");
    return PB.responsive(node, function (width, theme) {
      var out = build({ Plot: window.Plot, d3: window.d3, theme: theme, width: width });
      var chart = out instanceof Node ? out : window.Plot.plot(Object.assign({
        width: width,
        marginLeft: 44,
        marginRight: 16,
        marginBottom: 44,
        style: { background: "transparent", color: theme.ink2, fontFamily: theme.font, fontSize: "12px", overflow: "visible" }
      }, out));
      node.replaceChildren(chart);
    });
  };

  /* An SVG that fills its container at a fixed aspect ratio. draw(svgSelection, {width, height, theme})
     is called again on resize and theme change, so it must clear and redraw. */
  PB.svg = function (target, opts, draw) {
    var node = resolve(target);
    var aspect = (opts && opts.aspect) || 4 / 3;
    var svg = window.d3.select(node).append("svg").attr("role", "img");
    if (opts && opts.label) svg.attr("aria-label", opts.label);
    PB.responsive(node, function (width, theme) {
      var height = Math.round(width / aspect);
      svg.attr("viewBox", "0 0 " + width + " " + height).attr("width", width).attr("height", height);
      svg.selectAll("*").remove();
      draw(svg, { width: width, height: height, theme: theme });
    });
    return svg;
  };

  /* A HiDPI canvas that fills its container. Returns {canvas, ctx, width(), height(), theme()}.
     Sizes are in CSS pixels; the context is already scaled for the device pixel ratio. */
  PB.canvas = function (target, opts) {
    var node = resolve(target);
    var aspect = (opts && opts.aspect) || null;
    var canvas = el("canvas", { role: "img" });
    if (opts && opts.label) canvas.setAttribute("aria-label", opts.label);
    node.appendChild(canvas);
    var ctx = canvas.getContext("2d");
    var w = 0, h = 0, theme = PB.theme(node);
    var handle = { canvas: canvas, ctx: ctx, width: function () { return w; }, height: function () { return h; }, theme: function () { return theme; }, onResize: null };
    PB.responsive(node, function (width, t) {
      var ratio = Math.min(window.devicePixelRatio || 1, 3);
      w = width;
      h = aspect ? Math.round(width / aspect) : Math.max(1, Math.floor(node.clientHeight));
      theme = t;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      canvas.width = Math.round(w * ratio);
      canvas.height = Math.round(h * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      if (handle.onResize) handle.onResize();
    });
    return handle;
  };

  /* An animation loop that only runs while `target` is on screen.
     frame(t, dt): t is seconds of running time, dt is seconds since the last frame.
     With reduced motion on, frame is called once with opts.still (default 0) and never loops,
     so every animation must also read correctly as a single still frame. */
  PB.animate = function (target, frame, opts) {
    var node = resolve(target);
    var still = (opts && opts.still) || 0;
    var running = false, visible = false, paused = false, raf = 0, t = 0, last = 0;
    function tick(now) {
      if (!running) return;
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      t += dt;
      frame(t, dt);
      raf = requestAnimationFrame(tick);
    }
    function update() {
      var should = visible && !paused && !PB.reducedMotion();
      if (should && !running) {
        running = true;
        last = performance.now();
        raf = requestAnimationFrame(tick);
      } else if (!should && running) {
        running = false;
        cancelAnimationFrame(raf);
      }
      if (PB.reducedMotion()) frame(still, 0);
    }
    new IntersectionObserver(function (entries) {
      visible = entries[entries.length - 1].isIntersecting;
      update();
    }, { rootMargin: "80px" }).observe(node);
    reducedMotion.addEventListener("change", update);
    document.addEventListener("visibilitychange", function () {
      paused = document.hidden;
      update();
    });
    frame(still, 0);
    return {
      pause: function () { paused = true; update(); },
      play: function () { paused = false; update(); },
      reset: function () { t = 0; frame(0, 0); },
      seek: function (seconds) { t = seconds; frame(t, 0); }
    };
  };

  /* Scroll steps. root holds .pb-step elements; onStep(index, stepEl) fires when a step
     becomes the active one. The first step is active at load. */
  PB.steps = function (root, onStep) {
    var node = resolve(root);
    var steps = Array.prototype.slice.call(node.querySelectorAll(".pb-step"));
    var active = -1;
    function activate(i) {
      if (i === active || i < 0) return;
      active = i;
      steps.forEach(function (s, j) { s.classList.toggle("is-active", j === i); });
      onStep(i, steps[i]);
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) activate(steps.indexOf(entry.target));
      });
    }, { rootMargin: "-45% 0px -45% 0px", threshold: 0 });
    steps.forEach(function (s) { io.observe(s); });
    activate(0);
    return { count: steps.length, go: activate };
  };

  /* A labeled slider. opts: {label, min, max, step, value, format(v), onInput(v)}. */
  PB.slider = function (target, opts) {
    var node = resolve(target);
    var format = opts.format || function (v) { return String(v); };
    var id = "pb-slider-" + Math.random().toString(36).slice(2, 8);
    var output = el("output", { for: id, text: format(opts.value) });
    var input = el("input", {
      type: "range", id: id, min: opts.min, max: opts.max,
      step: opts.step == null ? "any" : opts.step, value: opts.value, "aria-label": opts.label
    });
    var wrap = el("div", { class: "pb-slider" }, [
      el("div", { class: "pb-slider-head" }, [el("label", { for: id, text: opts.label }), output]),
      input
    ]);
    node.appendChild(wrap);
    input.addEventListener("input", function () {
      var v = Number(input.value);
      output.textContent = format(v);
      opts.onInput(v);
    });
    return {
      get value() { return Number(input.value); },
      set: function (v) { input.value = v; output.textContent = format(Number(v)); opts.onInput(Number(v)); }
    };
  };

  /* A segmented toggle. opts: {label, options: [{value, label}], value, onChange(value)}. */
  PB.toggle = function (target, opts) {
    var node = resolve(target);
    var wrap = el("div", { class: "pb-toggle", role: "group", "aria-label": opts.label || "Options" });
    var buttons = opts.options.map(function (o) {
      var b = el("button", { type: "button", text: o.label, "aria-pressed": String(o.value === opts.value) });
      b.addEventListener("click", function () { select(o.value); });
      wrap.appendChild(b);
      return b;
    });
    function select(value) {
      opts.options.forEach(function (o, i) { buttons[i].setAttribute("aria-pressed", String(o.value === value)); });
      opts.onChange(value);
    }
    node.appendChild(wrap);
    return { set: select };
  };

  /* The table twin of a data chart, folded behind "Show the numbers".
     opts: {caption, columns: [{key, label, numeric, format}], rows: [{...}]}. */
  PB.table = function (target, opts) {
    var node = resolve(target);
    var table = el("table", { class: "pb-table" });
    if (opts.caption) table.appendChild(el("caption", { text: opts.caption }));
    var head = el("tr");
    opts.columns.forEach(function (c) { head.appendChild(el("th", { scope: "col", class: c.numeric ? "num" : "", text: c.label })); });
    table.appendChild(el("thead", {}, [head]));
    var body = el("tbody");
    opts.rows.forEach(function (row) {
      var tr = el("tr");
      opts.columns.forEach(function (c) {
        var value = row[c.key];
        tr.appendChild(el("td", { class: c.numeric ? "num" : "", text: c.format ? c.format(value, row) : String(value) }));
      });
      body.appendChild(tr);
    });
    table.appendChild(body);
    var details = el("details", { class: "pb-data" }, [
      el("summary", { text: opts.summary || "Show the numbers" }),
      el("div", { class: "pb-table-wrap" }, [table])
    ]);
    node.appendChild(details);
    return details;
  };

  /* A tooltip that follows the pointer. show(html, event) and hide(). */
  PB.tooltip = function () {
    var tip = el("div", { class: "pb-tip", role: "status" });
    tip.hidden = true;
    document.body.appendChild(tip);
    return {
      show: function (content, event) {
        if (typeof content === "string") tip.textContent = content;
        else tip.replaceChildren(content);
        tip.hidden = false;
        var pad = 12;
        var rect = tip.getBoundingClientRect();
        var x = Math.min(window.innerWidth - rect.width - pad, Math.max(pad, event.clientX - rect.width / 2));
        var y = event.clientY - rect.height - 14;
        if (y < pad) y = event.clientY + 18;
        tip.style.left = x + "px";
        tip.style.top = y + "px";
      },
      hide: function () { tip.hidden = true; }
    };
  };

  function setupTerms() {
    var pop = null;
    function close() {
      if (pop) { pop.remove(); pop = null; }
    }
    document.addEventListener("click", function (event) {
      var term = event.target.closest && event.target.closest(".pb-term");
      close();
      if (!term) return;
      pop = el("div", { class: "pb-term-pop", role: "tooltip" }, [
        el("b", { text: term.dataset.term || term.textContent }),
        term.dataset.def || ""
      ]);
      document.body.appendChild(pop);
      var r = term.getBoundingClientRect();
      var pr = pop.getBoundingClientRect();
      var left = Math.min(window.innerWidth - pr.width - 16, Math.max(16, r.left));
      var top = r.bottom + 8;
      if (top + pr.height > window.innerHeight - 8) top = r.top - pr.height - 8;
      pop.style.left = left + window.scrollX + "px";
      pop.style.top = top + window.scrollY + "px";
    });
    window.addEventListener("scroll", close, { passive: true });
    document.querySelectorAll(".pb-term").forEach(function (t) {
      t.setAttribute("tabindex", "0");
      t.setAttribute("role", "button");
      t.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); t.click(); }
      });
    });
  }

  function setupReveal() {
    var nodes = document.querySelectorAll(".pb-reveal");
    if (!nodes.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add("is-in"); io.unobserve(entry.target); }
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    nodes.forEach(function (n) { io.observe(n); });
  }

  function setupMath() {
    if (!window.renderMathInElement) return;
    window.renderMathInElement(document.body, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false }
      ],
      throwOnError: false
    });
  }

  /* Number formatting helpers so every page prints numbers the same way. */
  PB.fmt = {
    int: function (v) { return Math.round(v).toLocaleString("en-US"); },
    fixed: function (digits) { return function (v) { return Number(v).toFixed(digits); }; },
    pct: function (v, digits) { return (v * 100).toFixed(digits == null ? 0 : digits) + "%"; },
    compact: function (v) { return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(v); },
    sci: function (v, digits) {
      if (v === 0) return "0";
      var exp = Math.floor(Math.log10(Math.abs(v)));
      var mant = v / Math.pow(10, exp);
      return mant.toFixed(digits == null ? 1 : digits) + " × 10" + String(exp).replace(/-/g, "⁻").replace(/\d/g, function (d) { return "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]; });
    }
  };

  var readyFns = [];
  var booted = false;
  /* Page code goes inside PB.ready(fn). It runs after the document, the kit, and math are set up.
     An error thrown inside is recorded for the automated check instead of killing later blocks. */
  PB.ready = function (fn) {
    if (booted) run(fn);
    else readyFns.push(fn);
  };
  function run(fn) {
    try { fn(); } catch (e) { errors.push(String((e && e.stack) || e)); console.error(e); }
  }
  function boot() {
    if (booted) return;
    booted = true;
    run(setupMath);
    run(setupTerms);
    run(setupReveal);
    readyFns.forEach(run);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { document.documentElement.dataset.pbReady = "1"; });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.PB = PB;
})();
