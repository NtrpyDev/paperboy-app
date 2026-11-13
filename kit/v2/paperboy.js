/* Paperboy explainer kit v2: the helpers every explainer page shares, in the First Light design.
   Loaded after d3, Plot, and KaTeX. Exposes one global, PB.
   v1's surface is kept (PB.ready, PB.theme, PB.responsive, PB.plot, PB.svg, PB.canvas, PB.animate,
   PB.steps, PB.slider, PB.toggle, PB.table, PB.tooltip, PB.fmt, PB.el, PB.reducedMotion), and the
   design is what they produce by default. New: PB.plate, PB.engrave, PB.live, PB.ruler, PB.screen,
   PB.legend, PB.rangeBar, PB.barRows, PB.beam, PB.valueLines, PB.touch, PB.curve, PB.marks. */
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

  /* Inside the Android app the WebView's user agent carries "PaperboyApp/". The app draws its own
     top bar there, so the page leaves its web bar out. */
  PB.inApp = /PaperboyApp\//.test(navigator.userAgent || "");
  if (PB.inApp) document.documentElement.classList.add("pb-in-app");

  var SVGNS = "http://www.w3.org/2000/svg";
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
  PB.reducedMotion = function () {
    return reducedMotion.matches || document.documentElement.dataset.motion === "off";
  };

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (attrs[k] == null) return;
      if (k === "text") node.textContent = attrs[k];
      else if (k === "class") node.className = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      if (c == null) return;
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }
  PB.el = el;

  function resolve(target) {
    var node = typeof target === "string" ? document.querySelector(target) : (target && target.node && !target.nodeType ? target.node() : target);
    if (!node) throw new Error("PB: target not found: " + target);
    return node;
  }

  var uid = 0;
  function nextId(prefix) { uid += 1; return (prefix || "pb") + "-" + uid; }
  function num(v) { return Math.round(v * 100) / 100; }

  /* ---------------------------------------------------------------- theme */

  /* The tokens in effect at `scope`, as plain strings and numbers. series is the documented
     order: the finding (live), ink, plate. An estimate or range is a screen (PB.screen), not a color. */
  PB.theme = function (scope) {
    var cs = getComputedStyle(scope ? resolve(scope) : document.documentElement);
    function v(name) { return cs.getPropertyValue(name).trim(); }
    function n(name) { return parseFloat(v(name)) || 0; }
    var page = v("--pb-page");
    var t = {
      page: page, surface: page, raised: page,
      ink: v("--pb-ink"), ink2: v("--pb-ink-2"), muted: v("--pb-muted"),
      grid: v("--pb-grid"), axis: v("--pb-axis"), rule: v("--pb-rule"),
      accent: v("--pb-accent"), live: v("--pb-accent"),
      slab: v("--pb-slab"), onSlab: v("--pb-on-slab"), stamp: v("--pb-stamp"), onStamp: v("--pb-on-stamp"),
      plate: v("--pb-plate"), contour: v("--pb-contour"), screen: v("--pb-screen"), carriage: v("--pb-carriage"),
      deemph: v("--pb-ink-2"),
      font: v("--pb-font"), display: v("--pb-display"), mono: v("--pb-mono"),
      voice1: n("--pb-w-voice1"), labelSize: n("--pb-fs-label"),
      liveCore: n("--pb-live-core"), liveTrap: n("--pb-live-trap"), pen: n("--pb-pen"), penTrap: n("--pb-pen-trap"),
      ring: n("--pb-ring"), ringOpacity: n("--pb-ring-opacity")
    };
    t.night = n("--pb-halo-b") > 0;
    t.series = [t.live, t.ink, t.plate, t.ink2];
    return t;
  };

  /* ---------------------------------------------------------------- redraw on width and theme */

  var themeListeners = [];
  function onThemeChange() { themeListeners.slice().forEach(function (f) { f(); }); }
  darkQuery.addEventListener("change", onThemeChange);
  new MutationObserver(onThemeChange).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  /* fn(width, theme) runs now and again when the width or the theme changes. A rerun for a new
     width or theme marks the node .pb-done, so its draw-ins do not play a second time.
     Returns a function that stops it; .run() reruns it on purpose, with its draw-ins. */
  PB.responsive = function (target, fn) {
    var node = resolve(target);
    var lastWidth = -1, queued = false, runs = 0;
    function run(intended) {
      queued = false;
      var width = Math.floor(node.clientWidth);
      if (width <= 0) return;
      if (runs > 0 && !intended) node.classList.add("pb-done");
      if (intended) node.classList.remove("pb-done");
      runs += 1;
      lastWidth = width;
      fn(width, PB.theme(node));
    }
    function schedule() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { run(false); });
    }
    var ro = new ResizeObserver(function () {
      if (Math.floor(node.clientWidth) !== lastWidth) schedule();
    });
    ro.observe(node);
    themeListeners.push(schedule);
    run(false);
    var stop = function () {
      ro.disconnect();
      var i = themeListeners.indexOf(schedule);
      if (i >= 0) themeListeners.splice(i, 1);
    };
    stop.run = function () { run(true); };
    return stop;
  };

  /* ---------------------------------------------------------------- SVG helpers */

  function sel(g) { return g && g.node && !g.nodeType ? g : window.d3.select(g); }
  function rootSvg(g) {
    var node = sel(g).node();
    return node.ownerSVGElement || node;
  }
  function defsOf(g) {
    var svg = rootSvg(g);
    var defs = svg.querySelector(":scope > defs");
    if (!defs) {
      defs = document.createElementNS(SVGNS, "defs");
      svg.insertBefore(defs, svg.firstChild);
    }
    return window.d3.select(defs);
  }

  /* A smooth path of cubic curves through points [[x, y], ...] (Catmull-Rom). The live line is
     always one path of curves, never a polyline. closed: true closes it. */
  PB.curve = function (points, closed) {
    var d3 = window.d3;
    return d3.line().curve(closed ? d3.curveCatmullRomClosed.alpha(0.5) : d3.curveCatmullRom.alpha(0.5))(points);
  };

  var TONES = { light: [0.24, 0.24], mid: [0.46, 0.44], heavy: [0.68, 0.66], context: [0.30, 0.30] };
  var COLORS = { screen: "--pb-screen", plate: "--pb-plate", ink: "--pb-ink", "ink-2": "--pb-ink-2", muted: "--pb-ink-2", contour: "--pb-contour" };

  /* A line screen (SYSTEM.md 5.1): parallel lines 3 px apart from an SVG pattern, whose line width
     is the tone. Returns "url(#id)" for a fill. opts: tone "light" | "mid" | "heavy" | "context" or a
     fraction of the pitch; angle 1 (minus 72 degrees, the default) or 2 (minus 12 degrees);
     color "screen" (estimates and ranges, the default), "plate" (context shapes), or "ink".
     Every tone has the same pitch and phase, so tones meet without a break. */
  PB.screen = function (g, opts) {
    opts = opts || {};
    var angle = opts.angle === 2 || opts.angle === -12 ? -12 : -72;
    var tone = typeof opts.tone === "number" ? opts.tone : (TONES[opts.tone || "mid"] || TONES.mid)[angle === -12 ? 1 : 0];
    var pitch = opts.pitch || 3;
    var color = COLORS[opts.color || "screen"] || "--pb-screen";
    var defs = defsOf(g);
    var key = [angle, tone, pitch, color].join("|");
    var found = defs.selectAll("pattern").filter(function () { return this.dataset.key === key; });
    if (!found.empty()) return "url(#" + found.attr("id") + ")";
    var id = nextId("pb-screen");
    var h = pitch * tone;
    defs.append("pattern").attr("id", id).attr("data-key", key)
      .attr("width", 40).attr("height", pitch).attr("patternUnits", "userSpaceOnUse")
      .attr("patternTransform", "rotate(" + angle + ")")
      .append("rect").attr("x", 0).attr("y", num((pitch - h) / 2)).attr("width", 40).attr("height", num(h))
      .style("fill", "var(" + color + ")");
    return "url(#" + id + ")";
  };

  /* A filled shape in a screen with its 0.9 px outline. kind: "screen" (an estimate, mid tone),
     "weave" (two screens overlapping: both angles at the light tone), "band" (a range along a
     line: the estimate screen at tone 0.30), "context" (plate screen, tone 0.30),
     "solid" (ink), "plate" (plate ink), "live" (the finding). Draws into g with the given d3 shape
     maker, e.g. function (s) { return s.append("rect").attr(...) }. */
  function fillShape(g, kind, angle, make) {
    g = sel(g);
    var fills = [];
    if (kind === "weave") fills = [PB.screen(g, { tone: "light", angle: 1 }), PB.screen(g, { tone: "light", angle: 2 })];
    else if (kind === "band") fills = [PB.screen(g, { tone: "context", angle: angle || 1 })];
    else if (kind === "context") fills = [PB.screen(g, { tone: "context", color: "plate", angle: angle || 1 })];
    else if (kind === "solid") fills = ["var(--pb-ink)"];
    else if (kind === "plate") fills = ["var(--pb-plate)"];
    else if (kind === "live") fills = ["var(--pb-accent)"];
    else fills = [PB.screen(g, { tone: "mid", angle: angle || 1 })];
    var nodes = fills.map(function (f) { return make(g).style("fill", f).attr("stroke", "none"); });
    var outline = make(g).attr("class", "pb-outline");
    return { fills: nodes, outline: outline };
  }
  PB.fillShape = fillShape;

  /* The ruler: the one axis (SYSTEM.md 4.2). A 0.9 px line, ticks below it and outside the plot,
     7 px major and 4 px minor, labels with their baseline 20 px under the line, the unit written once.
     opts: x (a d3 scale), y (px), major (array of values, or a step), minor (array or step),
     labels (values to label, default every major), format(v), unit ("s", "Mpc", "solar masses"),
     unitAt "last" (after the last label, the default) or "end" (at x2, set right), x1 and x2 (px; the
     line runs from x1 to x2, default the scale's range; x2 may run past it, off the plate),
     anchor "middle" to center the label at the domain's start too (by default it is set flush left). */
  PB.ruler = function (g, opts) {
    var d3 = window.d3;
    g = sel(g).append("g").attr("class", "pb-ruler");
    var x = opts.x, y = opts.y;
    var dom = x.domain(), rng = x.range();
    function values(spec) {
      if (Array.isArray(spec)) return spec;
      if (typeof spec === "number") return d3.range(dom[0], dom[1] + spec * 1e-6, spec);
      return [];
    }
    var major = values(opts.major != null ? opts.major : x.ticks ? x.ticks(5) : []);
    var minor = values(opts.minor).filter(function (v) { return major.indexOf(v) < 0 && !major.some(function (m) { return Math.abs(m - v) < 1e-9; }); });
    var x1 = opts.x1 != null ? opts.x1 : Math.min(rng[0], rng[1]);
    var x2 = opts.x2 != null ? opts.x2 : Math.max(rng[0], rng[1]);
    var lines = g.append("g").attr("class", "pb-axis-line");
    lines.append("line").attr("x1", num(x1)).attr("x2", num(x2)).attr("y1", y).attr("y2", y);
    major.forEach(function (v) { lines.append("line").attr("x1", num(x(v))).attr("x2", num(x(v))).attr("y1", y).attr("y2", y + 7); });
    minor.forEach(function (v) { lines.append("line").attr("x1", num(x(v))).attr("x2", num(x(v))).attr("y1", y).attr("y2", y + 4); });
    var fmt = opts.format || function (v) { return String(v); };
    var labeled = opts.labels || major;
    var labels = g.append("g").attr("class", "pb-tick-label");
    labeled.forEach(function (v, i) {
      var last = i === labeled.length - 1;
      var text = fmt(v) + (last && opts.unit && opts.unitAt !== "end" ? " " + opts.unit : "");
      var anchor = i === 0 && v === dom[0] && opts.anchor !== "middle" ? "start" : "middle";
      labels.append("text").attr("x", num(x(v))).attr("y", y + 20).attr("text-anchor", anchor).text(text);
    });
    if (opts.unit && opts.unitAt === "end") {
      labels.append("text").attr("x", num(opts.unitX != null ? opts.unitX : x2)).attr("y", y + 20).attr("text-anchor", "end").text(opts.unit);
    }
    return g;
  };

  /* Value lines: how values are read off a chart with a ruler along the bottom. 0.6 px lines across
     the plot, each named at its left end 5 px above the line. opts: y (scale), values, x1, x2,
     format(v), unit (added after the top value). */
  PB.valueLines = function (g, opts) {
    g = sel(g).append("g");
    var fmt = opts.format || String;
    var top = opts.values.length - 1;
    opts.values.forEach(function (v, i) {
      var y = num(opts.y(v));
      g.append("line").attr("class", "pb-grid-line").attr("x1", opts.x1).attr("x2", opts.x2).attr("y1", y).attr("y2", y);
      g.append("text").attr("class", "pb-value-label").attr("x", opts.x1).attr("y", y - 5)
        .text(fmt(v) + (i === top && opts.unit ? " " + opts.unit : ""));
    });
    return g;
  };

  /* A beam: a 1.4 px line with end caps, for a length ("One arm, 4 km"). opts: x1, x2, y, cap (half
     height, 5), live: true makes it the finding's beam. */
  PB.beam = function (g, opts) {
    g = sel(g).append("g").attr("class", opts.live ? "pb-live-beam" : "pb-beam");
    var cap = opts.cap == null ? 5 : opts.cap;
    g.append("line").attr("x1", opts.x1).attr("x2", opts.x2).attr("y1", opts.y).attr("y2", opts.y);
    [opts.x1, opts.x2].forEach(function (x) { g.append("line").attr("x1", x).attr("x2", x).attr("y1", opts.y - cap).attr("y2", opts.y + cap); });
    return g;
  };

  /* The live line (HANDOFF.md 4.5): from one path, in drawing order, the ground trap, the night
     halo (three strokes), the core, the pen point's ground dot, the night halo discs, and the pen
     point, and the carriage on the ruler under the pen when opts.carriage is the ruler's y.
     It never touches plate ink directly. Night differs only through the tokens.
     opts: animate (default true: the line sweeps and the pen travels once, when the figure is in
     view), ms (sweep duration, 1900; 600 to 900 for a short beam), delay (320), pen (default true),
     pulse (the pen breathes after the sweep: the hero's line only), carriage (ruler y),
     cap (half height of the end caps of a beam that rules off a length: one at the start, one riding with the pen),
     upTo (x in px: draw the live part only up to x, the rest as the thin muted line not yet played;
     move it later with handle.set(x)), label (aria-label, makes the group an image).
     Returns {node, set(x), point(x)}. */
  PB.live = function (g, d, opts) {
    opts = opts || {};
    g = sel(g);
    var group = g.append("g").attr("class", "pb-live");
    if (opts.label) group.attr("role", "img").attr("aria-label", opts.label);
    var animate = opts.animate !== false && opts.upTo == null;
    var style = "";
    if (opts.ms) style += "--pb-sweep-ms:" + opts.ms + "ms;";
    if (opts.delay != null) style += "--pb-sweep-delay:" + opts.delay + "ms;";
    if (style) group.attr("style", style);
    var sweep = animate ? " pb-sweep" : "";
    var travel = animate ? " pb-travel" : "";
    var svg = rootSvg(group);
    var probe = document.createElementNS(SVGNS, "path");
    probe.setAttribute("d", d);
    svg.appendChild(probe);
    var total = probe.getTotalLength();
    function lengthAt(x) {
      var lo = 0, hi = total;
      for (var i = 0; i < 40; i++) {
        var mid = (lo + hi) / 2;
        if (probe.getPointAtLength(mid).x < x) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    }
    var clipLive = null, clipRest = null;
    if (opts.upTo != null) {
      var defs = defsOf(group);
      var idL = nextId("pb-clip"), idR = nextId("pb-clip");
      clipLive = defs.append("clipPath").attr("id", idL).append("rect").attr("y", -1e4).attr("height", 2e4).attr("x", -1e4);
      clipRest = defs.append("clipPath").attr("id", idR).append("rect").attr("y", -1e4).attr("height", 2e4).attr("width", 2e4);
      var rest = group.append("g").attr("clip-path", "url(#" + idR + ")");
      rest.append("path").attr("class", "pb-live-rest-trap").attr("d", d);
      rest.append("path").attr("class", "pb-live-rest").attr("d", d);
    }
    var lineG = group.append("g");
    if (clipLive) lineG.attr("clip-path", "url(#" + clipLive.node().parentNode.id + ")");
    ["pb-live-trap", "pb-live-halo-a", "pb-live-halo-b", "pb-live-halo-c", "pb-live-core"].forEach(function (c) {
      if (c === "pb-live-core" && opts.cap) {
        var s0 = probe.getPointAtLength(0);
        lineG.append("line").attr("class", "pb-live-beam").attr("x1", s0.x).attr("x2", s0.x).attr("y1", s0.y - opts.cap).attr("y2", s0.y + opts.cap);
      }
      var p = lineG.append("path").attr("class", c + sweep).attr("d", d);
      if (animate) p.attr("pathLength", 1);
    });
    var offset = "path('" + d + "')";
    var marks = [];
    if (opts.carriage != null) {
      var rid = nextId("pb-rail");
      defsOf(group).append("clipPath").attr("id", rid).append("rect")
        .attr("x", -1e4).attr("width", 2e4).attr("y", opts.carriage - 0.5).attr("height", 8);
      var c = group.append("g").attr("clip-path", "url(#" + rid + ")").append("g").attr("class", travel.trim());
      c.append("line").attr("class", "pb-carriage-mark").attr("x1", 0).attr("x2", 0).attr("y1", -4000).attr("y2", 4000);
      marks.push(c);
    }
    if (opts.cap) {
      var cap = group.append("g").attr("class", travel.trim());
      cap.append("line").attr("class", "pb-live-beam").attr("x1", 0).attr("x2", 0).attr("y1", -opts.cap).attr("y2", opts.cap);
      marks.push(cap);
    }
    if (opts.pen !== false) {
      ["pb-pen-trap", "pb-pen-halo-a", "pb-pen-halo-b", "pb-pen-halo-c", "pb-pen"].forEach(function (cl) {
        var m = group.append("circle").attr("class", cl + travel + (cl === "pb-pen" && opts.pulse && animate ? " pb-pulse" : ""));
        marks.push(m);
      });
    }
    marks.forEach(function (m) { m.style("offset-path", offset).style("offset-rotate", "0deg").style("offset-distance", "100%"); });
    function set(x) {
      var l = lengthAt(x);
      var pct = total ? (l / total) * 100 : 100;
      marks.forEach(function (m) { m.style("offset-distance", pct + "%"); });
      if (clipLive) { clipLive.attr("width", x + 1e4); clipRest.attr("x", x); }
    }
    if (opts.upTo != null) set(opts.upTo);
    var handle = {
      node: group.node(), length: total, set: set,
      point: function (x) { var p = probe.getPointAtLength(lengthAt(x)); return { x: p.x, y: p.y }; }
    };
    // keep the probe for point(): hidden and out of the accessibility tree
    probe.setAttribute("fill", "none");
    probe.setAttribute("stroke", "none");
    probe.setAttribute("aria-hidden", "true");
    group.node().appendChild(probe);
    return handle;
  };

  /* A live marker on a band: the reported value as a vertical beam on a ground trap with a dot on
     top (SYSTEM.md 4.2 rule 6). opts: x, y1 (top, where the dot sits), y2, trap (7, or 6 in a small
     bar), r (3.6, or 3.2), animate ("drop" by default, false for none). */
  PB.marker = function (g, opts) {
    g = sel(g).append("g");
    if (opts.animate !== false) g.attr("class", "pb-" + (opts.animate || "drop"));
    g.append("line").attr("class", "pb-ground").attr("x1", opts.x).attr("x2", opts.x).attr("y1", opts.y1).attr("y2", opts.y2).style("stroke-width", (opts.trap || 7) + "px");
    g.append("line").attr("class", "pb-live-beam").attr("x1", opts.x).attr("x2", opts.x).attr("y1", opts.y1).attr("y2", opts.y2);
    g.append("circle").attr("class", "pb-live-fill").attr("cx", opts.x).attr("cy", opts.y1).attr("r", opts.r || 3.6);
    return g;
  };

  /* A responsive SVG. draw(svg, {width, height, theme}) is called again on resize and theme change,
     so it must clear and redraw (the kit clears it). opts: aspect (width / height, default 4/3) or
     height (px, or a function of width), label (aria-label). Returns the d3 selection; .redraw()
     draws it again with its draw-ins. */
  PB.svg = function (target, opts, draw) {
    var node = resolve(target);
    opts = opts || {};
    var svg = window.d3.select(node).append("svg").attr("role", "img");
    if (opts.label) svg.attr("aria-label", opts.label);
    var stop = PB.responsive(node, function (width, theme) {
      var height = typeof opts.height === "function" ? opts.height(width) : opts.height || Math.round(width / (opts.aspect || 4 / 3));
      svg.attr("viewBox", "0 0 " + width + " " + height).attr("width", width).attr("height", height);
      svg.selectAll("*").remove();
      draw(svg, { width: width, height: height, theme: theme });
    });
    svg.redraw = stop.run;
    return svg;
  };

  /* ---------------------------------------------------------------- the plate */

  /* The hero plate, or any plate (SYSTEM.md 9.4): full bleed, square, in the page's own theme.
     Three layers, back to front: the print (plate ink: line screens and engraved rings), the key
     (the black layer: the subject in contours over a ground knockout), and the live layer (the live
     line, the ruler, the carriage, direct labels). On arrival the print inks in along the screen
     angle and the two layers slide into register; the live line sweeps. At rest, and with motion
     off, everything is in place.
     opts: band (px tall, or a function of width; 196 on a phone), ruler (true: 34 px more under the
     band for the ruler's labels), below (px under the band instead, for a plate with more under it), label (what the plate shows, for screen readers),
     draw(p) with p = {print, key, live (d3 groups), width, band, height, rulerY, left, right, theme}.
     left and right are the text column's edges inside the plate, so a ruler can start at the margin. */
  PB.plate = function (target, opts) {
    var d3 = window.d3;
    var node = resolve(target);
    node.classList.add("pb-plate");
    node.replaceChildren();
    var print = el("div", { class: "pb-plate-print pb-inkwipe" });
    var regA = el("div", { class: "pb-register-a" });
    var regB = el("div", { class: "pb-register-b" });
    print.appendChild(regA);
    print.appendChild(regB);
    node.appendChild(print);
    var svgA = d3.select(regA).append("svg").attr("aria-hidden", "true");
    var svgB = d3.select(regB).append("svg").attr("aria-hidden", "true");
    var svgL = d3.select(node).append("svg").attr("class", "pb-plate-live").attr("role", "img");
    if (opts.label) svgL.attr("aria-label", opts.label);
    var stop = PB.responsive(node, function (width, theme) {
      var band = typeof opts.band === "function" ? opts.band(width) : opts.band || 196;
      var height = band + (opts.below != null ? opts.below : opts.ruler === false ? 0 : 34);
      node.style.height = height + "px";
      node.style.minHeight = "0";
      print.style.height = band + "px";
      print.style.setProperty("--pb-wipe-x", num(band / Math.tan(72 * Math.PI / 180)) + "px");
      [svgA, svgB].forEach(function (s) {
        s.attr("viewBox", "0 0 " + width + " " + band).attr("width", width).attr("height", band).selectAll("*").remove();
      });
      svgL.attr("viewBox", "0 0 " + width + " " + height).attr("width", width).attr("height", height).selectAll("*").remove();
      var article = node.closest(".pb") || document.body;
      var rect = node.getBoundingClientRect(), col = article.getBoundingClientRect();
      var gutter = parseFloat(getComputedStyle(article).paddingLeft) || 20;
      var left = Math.max(0, Math.round(col.left + gutter - rect.left));
      var right = Math.min(width, Math.round(col.right - gutter - rect.left));
      opts.draw({
        print: svgA.append("g"), key: svgB.append("g"), live: svgL.append("g"),
        width: width, band: band, height: height, rulerY: band, left: left, right: right, theme: theme
      });
    });
    return { redraw: stop.run, node: node };
  };

  /* ---------------------------------------------------------------- engraved fields (SYSTEM.md 5.2) */

  PB.engrave = {};

  function crestSpans(r, a, gap, duty) {
    var spans = [];
    [1, -1].forEach(function (arm) {
      for (var k = 0; k < a.length - 1; k++) {
        var g = a[k + 1] - a[k];
        var R = (a[k] + a[k + 1]) / 2;
        var hw = duty * gap(R) / 2;
        if (r < a[k] - hw - g || r > a[k + 1] + hw + g) continue;
        var s = arm * (k % 2 === 0 ? 1 : -1);
        var lo = ((R - hw) * (R - hw) - r * r - g * g / 4) / (r * g);
        var hi = ((R + hw) * (R + hw) - r * r - g * g / 4) / (r * g);
        lo = Math.max(-1, Math.min(1, lo));
        hi = Math.max(-1, Math.min(1, hi));
        if (hi - lo < 1e-9) continue;
        if (s > 0) spans.push([Math.acos(hi), Math.acos(lo)]);
        else {
          var p = 2 * Math.PI - Math.acos(-hi), q = 2 * Math.PI - Math.acos(-lo);
          spans.push([Math.min(p, q), Math.max(p, q)]);
        }
      }
    });
    spans.sort(function (u, v) { return u[0] - v[0]; });
    var merged = [];
    spans.forEach(function (sp) {
      var last = merged[merged.length - 1];
      if (last && sp[0] <= last[1] + 2e-3) last[1] = Math.max(last[1], sp[1]);
      else merged.push([sp[0], sp[1]]);
    });
    if (merged.length > 1 && merged[0][0] < 2e-3 && merged[merged.length - 1][1] > 2 * Math.PI - 2e-3) {
      var first = merged.shift();
      merged[merged.length - 1][1] = first[1] + 2 * Math.PI;
    }
    return merged;
  }

  function lune(cx, cy, r, th0, th1, peak) {
    var al = (th1 - th0) / 2;
    var sag = r * (1 - Math.cos(al));
    var e = Math.min(peak / 2, sag * 0.45);
    if (e < 0.12) return "";
    var co = (2 * r * e + e * e) / (2 * (r + e - r * Math.cos(al)));
    var ci = (-2 * r * e + e * e) / (2 * (r - e - r * Math.cos(al)));
    var ro = r + e - co, ri = r - e - ci;
    var x0 = cx + r * Math.cos(th0), y0 = cy + r * Math.sin(th0);
    var x1 = cx + r * Math.cos(th1), y1 = cy + r * Math.sin(th1);
    return "M" + num(x0) + " " + num(y0) + "A" + num(ro) + " " + num(ro) + " 0 0 1 " + num(x1) + " " + num(y1) +
      "A" + num(ri) + " " + num(ri) + " 0 0 0 " + num(x0) + " " + num(y0) + "Z";
  }

  function arcInView(cx, cy, r, th0, th1, w, h) {
    var n = Math.max(2, Math.floor((th1 - th0) / (3 * Math.PI / 180)) + 1);
    for (var i = 0; i <= n; i++) {
      var th = th0 + (th1 - th0) * i / n;
      var x = cx + r * Math.cos(th), y = cy + r * Math.sin(th);
      if (x >= -3 && x <= w + 3 && y >= -3 && y <= h + 3) return true;
    }
    return false;
  }

  /* An engraved ring field: concentric rings 3.2 px apart around (cx, cy), each swelling into a
     tapered line where it crosses a crest of a two-armed spiral, so the field reads as waves
     leaving a source. Drawn in plate ink; the night form (a dimmer fine pass, only the broad swell)
     comes from the theme. opts: cx, cy, width, height (the area to fill), rot (spiral angle in
     degrees, -25), rmin (14), pitch (3.2), k (scale, 1 at a 390 px plate), gap(r) (crest spacing,
     9 + 0.085 r), near [r0, r1, w] (no ring inside r0; every other ring, w px, from r0 to r1),
     ramp [r0, r1] (swells grow from nothing to full between these radii), avoid [fnBroad, fnNarrow]
     (functions (x, y) that are true where a swell must not be drawn, e.g. from PB.engrave.wells),
     crest [broad, narrow] (peak swell widths; the theme's by default), theme. */
  PB.engrave.rings = function (g, opts) {
    g = sel(g);
    var theme = opts.theme || PB.theme(g.node());
    var k = opts.k || 1;
    var cx = opts.cx, cy = opts.cy, w = opts.width, h = opts.height;
    var pitch = opts.pitch || 3.2, rmin = opts.rmin == null ? 14 : opts.rmin;
    var rot = (opts.rot == null ? -25 : opts.rot) * Math.PI / 180;
    var gap = opts.gap || function (r) { return 9 + 0.085 * r; };
    var duty = opts.duty || [0.52, 0.2];
    var crest = opts.crest || (theme.night ? [1.4, 0] : [1.5, 2.3]);
    var near = opts.near || [0, 0, 0.62];
    var ramp = opts.ramp || [0, 1];
    var avoid = opts.avoid || [];
    var rmax = Math.max(Math.hypot(-cx, -cy), Math.hypot(w - cx, -cy), Math.hypot(-cx, h - cy), Math.hypot(w - cx, h - cy)) + pitch;
    var a = [rmin];
    while (a[a.length - 1] < rmax + 40) a.push(a[a.length - 1] + gap(a[a.length - 1]));

    function runs(r, th0, th1, bad) {
      if (!bad) return [[th0, th1]];
      function out(th) { return !bad(cx + r * Math.cos(th), cy + r * Math.sin(th)); }
      var n = Math.max(8, Math.floor(r * (th1 - th0) / 1.5));
      var ths = [], flags = [];
      for (var i = 0; i <= n; i++) { ths.push(th0 + (th1 - th0) * i / n); flags.push(out(ths[i])); }
      if (flags.every(Boolean)) return [[th0, th1]];
      function edge(tIn, tOut) {
        for (var j = 0; j < 24; j++) { var m = (tIn + tOut) / 2; if (out(m)) tOut = m; else tIn = m; }
        return tOut;
      }
      var res = [], start = flags[0] ? ths[0] : null;
      for (var q = 1; q <= n; q++) {
        if (flags[q] && !flags[q - 1]) start = edge(ths[q - 1], ths[q]);
        else if (!flags[q] && flags[q - 1]) { res.push([start, edge(ths[q], ths[q - 1])]); start = null; }
      }
      if (start != null) res.push([start, ths[n]]);
      return res;
    }

    var all = [], even = [], buckets = [[], []];
    var r = rmin, i = 0;
    function circle(rr) { return "M" + num(cx - rr) + " " + num(cy) + "a" + num(rr) + " " + num(rr) + " 0 1 0 " + num(2 * rr) + " 0a" + num(rr) + " " + num(rr) + " 0 1 0 " + num(-2 * rr) + " 0"; }
    while (r < rmax) {
      var visible = r + 3 > Math.max(0, Math.hypot(Math.max(0, -cx, cx - w), Math.max(0, -cy, cy - h)));
      if (visible) {
        if (r >= near[1] * k) all.push(circle(r));
        else if (r >= near[0] * k && i % 2 === 0) even.push(circle(r));
      }
      for (var c = 0; c < 2; c++) {
        var peak = crest[c];
        if (!(peak > 0) || !visible) continue;
        var spans = crestSpans(r, a, gap, duty[c]);
        for (var s = 0; s < spans.length; s++) {
          var t0 = spans[s][0] + rot, t1 = spans[s][1] + rot;
          if (!arcInView(cx, cy, r, t0, t1, w, h)) continue;
          var mid = (t0 + t1) / 2, al = (t1 - t0) / 2;
          var parts = runs(r, t0, t1, avoid[c]);
          for (var p = 0; p < parts.length; p++) {
            var u0 = parts[p][0], u1 = parts[p][1];
            var off = u0 <= mid && mid <= u1 ? 0 : Math.min(Math.abs(u0 - mid), Math.abs(u1 - mid));
            var pk = peak * (1 - Math.pow(off / al, 2));
            var part = (u1 - u0) / (t1 - t0);
            if (part < 0.4) continue;
            if (part < 1 - 1e-6) pk = Math.min(pk, peak * part);
            pk *= Math.max(0, Math.min(1, (r - ramp[0] * k) / ((ramp[1] - ramp[0]) * k)));
            if (arcInView(cx, cy, r, u0, u1, w, h)) buckets[c].push(lune(cx, cy, r, u0, u1, pk));
          }
        }
      }
      r += pitch;
      i += 1;
    }
    var out = g.append("g").attr("class", "pb-field");
    out.append("path").attr("class", "pb-field-hair").attr("d", all.join(""));
    if (even.length) out.append("path").attr("class", "pb-field-hair").attr("d", even.join("")).style("stroke-width", near[2] + "px");
    buckets.forEach(function (b) { if (b.length) out.append("path").attr("class", "pb-field-swell").attr("d", b.join("")); });
    return out;
  };

  /* Wells: the combined pull of point masses, drawn as contours only (no solid discs), over a
     ground knockout of the outermost contour (SYSTEM.md 5.2). Spacing closes toward each center and
     the centers stay open. opts: bodies [{x, y, m}], reach (px from the heaviest body to the outer
     contour, on the side away from the others; 44), core (3.4), step [2, 0.05], weights [0.55, 0.8],
     k (scale, 1). Returns {node, inside(reach)}: inside(r) is a function (x, y) that is true inside
     the contour r px out, for PB.engrave.rings' avoid option. */
  PB.engrave.wells = function (g, opts) {
    var d3 = window.d3;
    g = sel(g);
    var k = opts.k || 1;
    var bodies = opts.bodies;
    var reach = (opts.reach || 44) * k, core = (opts.core || 3.4) * k;
    var step = opts.step || [2, 0.05], weights = opts.weights || [0.55, 0.8];
    function phi(x, y) {
      var s = 0;
      for (var i = 0; i < bodies.length; i++) s += bodies[i].m / Math.max(1e-6, Math.hypot(x - bodies[i].x, y - bodies[i].y));
      return s;
    }
    var heavy = bodies.reduce(function (p, b) { return b.m > p.m ? b : p; }, bodies[0]);
    var mass = bodies.reduce(function (s, b) { return s + b.m; }, 0);
    var cmx = bodies.reduce(function (s, b) { return s + b.x * b.m; }, 0) / mass;
    var cmy = bodies.reduce(function (s, b) { return s + b.y * b.m; }, 0) / mass;
    var dx = heavy.x - cmx, dy = heavy.y - cmy, dl = Math.hypot(dx, dy) || 1;
    function levelAt(r) { return phi(heavy.x + dx / dl * r, heavy.y + dy / dl * r); }
    var pad = reach * 1.8 + 30;
    var x0 = d3.min(bodies, function (b) { return b.x; }) - pad, x1 = d3.max(bodies, function (b) { return b.x; }) + pad;
    var y0 = d3.min(bodies, function (b) { return b.y; }) - pad, y1 = d3.max(bodies, function (b) { return b.y; }) + pad;
    var res = 0.5;
    var nx = Math.ceil((x1 - x0) / res), ny = Math.ceil((y1 - y0) / res);
    var values = new Float64Array(nx * ny);
    for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) values[j * nx + i] = phi(x0 + (i + 0.5) * res, y0 + (j + 0.5) * res);
    var gen = d3.contours().size([nx, ny]);
    function paths(level) {
      var mp = gen.contour(values, level);
      var out = "";
      mp.coordinates.forEach(function (poly) {
        poly.forEach(function (ring) {
          var pts = ring.slice(0, -1).filter(function (_, n) { return n % 2 === 0; }).map(function (p) { return [x0 + p[0] * res, y0 + p[1] * res]; });
          if (pts.length > 3) out += PB.curve(pts, true);
        });
      });
      return out;
    }
    var radii = [];
    for (var r = reach; r > core; r -= step[0] * k + step[1] * r) radii.push(r);
    var group = g.append("g").attr("class", "pb-wells");
    group.append("path").attr("class", "pb-knockout").attr("d", paths(levelAt(reach)));
    var n = radii.length;
    for (var q = 1; q < n; q++) {
      var wgt = (weights[0] + (weights[1] - weights[0]) * Math.pow(q / Math.max(1, n - 1), 0.8)) * (0.75 + 0.25 * k);
      group.append("path").attr("class", "pb-contour-line").attr("d", paths(levelAt(radii[q]))).style("stroke-width", num(wgt) + "px");
    }
    return {
      node: group.node(),
      inside: function (rr) { var lv = levelAt(rr * k); return function (x, y) { return phi(x, y) >= lv; }; }
    };
  };

  /* ---------------------------------------------------------------- charts drawn by the kit */

  function chartBox(target, height, label, draw) {
    var node = resolve(target);
    node.classList.add("pb-chart");
    return PB.svg(node, { height: height, label: label }, draw);
  }

  /* One value with a range on a ruler (Fig. 2, and the ledger's small bar): a screened band, the
     reported value as the live marker dropping onto it, end labels above the band, the ruler.
     opts: domain [min, max], low, high, value, unit, major (step or values), minor, label (aria),
     mini: true for the 124 by 30 ledger form (band, marker, a baseline with end ticks; no labels). */
  PB.rangeBar = function (target, opts) {
    var d3 = window.d3;
    if (opts.mini) {
      var node = resolve(target);
      node.classList.add("pb-range-mini");
      var svg = d3.select(node).append("svg").attr("viewBox", "0 0 124 30").attr("width", 124).attr("height", 30)
        .attr("role", "img").attr("aria-label", opts.label || "");
      var x = d3.scaleLinear().domain(opts.domain).range([1, 121]);
      fillShape(svg, "screen", 1, function (s) { return s.append("rect").attr("x", num(x(opts.low))).attr("y", 10).attr("width", num(x(opts.high) - x(opts.low))).attr("height", 11); });
      PB.marker(svg, { x: num(x(opts.value)), y1: 5, y2: 26, trap: 6, r: 3.2, animate: false });
      var base = svg.append("g").attr("class", "pb-axis-line");
      base.append("line").attr("x1", 1).attr("x2", 121).attr("y1", 26).attr("y2", 26);
      base.append("line").attr("x1", 1).attr("x2", 1).attr("y1", 22).attr("y2", 26);
      base.append("line").attr("x1", 121).attr("x2", 121).attr("y1", 22).attr("y2", 26);
      return svg;
    }
    return chartBox(target, 70, opts.label, function (svg, s) {
      var unitRoom = opts.unit ? 62 : 8;
      var x = d3.scaleLinear().domain(opts.domain).range([0.5, s.width - unitRoom]);
      fillShape(svg, "screen", 1, function (q) { return q.append("rect").attr("x", num(x(opts.low))).attr("y", 16).attr("width", num(x(opts.high) - x(opts.low))).attr("height", 16); });
      PB.marker(svg, { x: num(x(opts.value)), y1: 9, y2: 44 });
      PB.ruler(svg, { x: x, y: 44, major: opts.major, minor: opts.minor, unit: opts.unit, unitAt: "end", unitX: s.width, format: opts.format });
      var lab = svg.append("g").attr("class", "pb-mark-label");
      lab.append("text").attr("x", num(x(opts.low))).attr("y", 11).attr("text-anchor", "middle").text((opts.format || String)(opts.low));
      lab.append("text").attr("x", num(x(opts.high))).attr("y", 11).attr("text-anchor", "middle").text((opts.format || String)(opts.high));
    });
  };

  /* Rows of segmented bars on one ruler (Fig. 3, "Where the mass went"). Bars are 20 px tall with a
     0.9 px outline; figures sit above their segments in the display face at 25 px.
     opts: domain, unit, major, minor, label (aria), rows: [{label, note, segments: [{from, to,
     kind: "screen" (an estimate, the default) | "weave" | "solid" | "plate" | "live", angle 1 | 2,
     figure (text above), name (a direct label beside a live segment)}]}].
     The live segment floods in when the figure comes into view, with drop lines to the ruler. */
  PB.barRows = function (target, opts) {
    var d3 = window.d3;
    var rowH = 85, bar = 20;
    var height = 48 + rowH * (opts.rows.length - 1) + bar + 26 + 26;
    return chartBox(target, height, opts.label, function (svg, s) {
      var x = d3.scaleLinear().domain(opts.domain).range([0.5, Math.min(s.width * 0.8, 400)]);
      var axis = 48 + rowH * (opts.rows.length - 1) + bar + 26;
      var drops = svg.append("g").attr("class", "pb-grid-line");
      opts.rows.forEach(function (row, i) {
        var top = 48 + rowH * i;
        var head = svg.append("text").attr("x", 0).attr("y", top - 37).attr("class", "pb-mark-label");
        head.append("tspan").attr("data-strong", "").style("font-weight", 600).text(row.label);
        if (row.note) head.append("tspan").attr("dx", 8).style("fill", "var(--pb-ink-2)").text(row.note);
        row.segments.forEach(function (seg) {
          var x0 = num(x(seg.from)), w = num(x(seg.to) - x(seg.from));
          var kind = seg.kind || "screen";
          var shape = fillShape(svg, kind, seg.angle, function (q) { return q.append("rect").attr("x", x0).attr("y", top).attr("width", w).attr("height", bar); });
          if (kind === "live") {
            shape.fills.forEach(function (f) { f.attr("class", "pb-flood"); });
            drops.append("line").attr("x1", x0).attr("x2", x0).attr("y1", top + bar).attr("y2", axis);
            drops.append("line").attr("x1", x0 + w).attr("x2", x0 + w).attr("y1", top + bar).attr("y2", axis);
            if (seg.name) {
              var words = String(seg.name).split(/\n/);
              var t = svg.append("text").attr("class", "pb-mark-label").attr("x", x0 + w + 9).attr("y", top + 8);
              words.forEach(function (wd, n) { t.append("tspan").attr("x", x0 + w + 9).attr("dy", n ? 12 : 0).text(wd); });
            }
          }
          if (seg.figure != null) {
            svg.append("text").attr("class", "pb-mark-figure").attr("x", x0 + w / 2).attr("y", top - 7).attr("text-anchor", "middle").text(seg.figure);
          }
        });
      });
      PB.ruler(svg, { x: x, y: axis, major: opts.major, minor: opts.minor, unit: opts.unit, unitAt: "end", unitX: s.width, format: opts.format });
    });
  };

  /* A legend row (SYSTEM.md 4.2 rule 7): only for two or more kinds of mark, never for a mark with a
     direct label. items: [{kind, label, angle}] with kind "live" (the 7 px dot), "screen" (a 22 by 10
     swatch of the estimate screen), "weave", "band", "context", "line" (a 22 px piece of 1.4 px line),
     "thin" (0.9 px, an estimate drawn as a line), "named" (3.2 px dot), "point" (2.1 px dot),
     "ring" (an open ring, a before value), "solid" (a 4 px solid dot, an after value), "errorbar". */
  PB.legend = function (target, items) {
    var d3 = window.d3;
    var node = resolve(target);
    var row = el("div", { class: "pb-legend" });
    items.forEach(function (it) {
      var key;
      if (it.kind === "live") key = el("i");
      else {
        var svg = d3.create("svg").attr("viewBox", "0 0 22 10").attr("aria-hidden", "true");
        if (it.kind === "screen" || it.kind === "weave" || it.kind === "context" || it.kind === "band") {
          node.appendChild(svg.node()); // patterns need a document for their ids
          fillShape(svg, it.kind, it.angle, function (s) { return s.append("rect").attr("x", 0.45).attr("y", 0.45).attr("width", 21.1).attr("height", 9.1); });
          svg.node().remove();
        } else if (it.kind === "line") svg.append("line").attr("class", "pb-line").attr("x1", 0).attr("x2", 22).attr("y1", 5).attr("y2", 5);
        else if (it.kind === "thin") svg.append("line").attr("class", "pb-line").attr("data-kind", "estimate").attr("x1", 0).attr("x2", 22).attr("y1", 5).attr("y2", 5);
        else if (it.kind === "named") { svg.attr("viewBox", "0 0 10 10").style("width", "10px"); svg.append("circle").attr("class", "pb-dot").attr("data-named", "").attr("cx", 5).attr("cy", 5); }
        else if (it.kind === "point") { svg.attr("viewBox", "0 0 10 10").style("width", "10px"); svg.append("circle").attr("class", "pb-dot").attr("cx", 5).attr("cy", 5); }
        else if (it.kind === "ring") { svg.attr("viewBox", "0 0 10 10").style("width", "10px"); svg.append("circle").attr("class", "pb-ring").attr("cx", 5).attr("cy", 5); }
        else if (it.kind === "solid") { svg.attr("viewBox", "0 0 10 10").style("width", "10px"); svg.append("circle").attr("cx", 5).attr("cy", 5).attr("r", 4).style("fill", "var(--pb-ink)"); }
        else if (it.kind === "errorbar") {
          var w = svg.append("g").attr("class", "pb-whisker");
          w.append("line").attr("x1", 2).attr("x2", 20).attr("y1", 5).attr("y2", 5);
          w.append("line").attr("x1", 2).attr("x2", 2).attr("y1", 1).attr("y2", 9);
          w.append("line").attr("x1", 20).attr("x2", 20).attr("y1", 1).attr("y2", 9);
          svg.append("circle").attr("class", "pb-dot").attr("data-named", "").attr("cx", 11).attr("cy", 5);
        }
        key = svg.node();
      }
      row.appendChild(el("span", {}, [key, it.label]));
    });
    node.appendChild(row);
    return row;
  };

  /* ---------------------------------------------------------------- Observable Plot */

  /* A responsive Observable Plot chart in the design. build({Plot, d3, theme, width, marks}) returns
     Plot options (or a finished element). Plot draws the plain marks; the kit adds, from Plot's own
     scales, what Plot cannot draw: the ruler, the value lines, and the live line.
     Defaults: no Plot axes (the axis is the ruler), the mono label face at 11 px, transparent
     background, visible overflow, margins that leave room for the ruler's labels.
     Kit options beside Plot's: ruler {major, minor, labels, format, unit, unitAt}, values {values,
     format, unit} (value lines), live {data, x, y, label} (the finding as the live line, with its
     pen point at the last point and the carriage on the ruler; one per chart).
     c.marks are Plot marks in the design: line(data, {x, y, series: 2 | 3 | "estimate"}),
     dots(data, {x, y, named}), endLabels(data, {x, y, text, finding}), figure(data, {x, y, text}). */
  PB.plot = function (target, build) {
    var d3 = window.d3;
    var node = resolve(target);
    node.classList.add("pb-plot");
    var stop = PB.responsive(node, function (width, theme) {
      var out = build({ Plot: window.Plot, d3: d3, theme: theme, width: width, marks: plotMarks(theme) });
      if (out instanceof Node) { node.replaceChildren(out); return; }
      var extras = { ruler: out.ruler, values: out.values, live: out.live };
      var opts = Object.assign({
        width: width, marginTop: 20, marginLeft: 0, marginRight: 0, marginBottom: 34
      }, out);
      delete opts.ruler; delete opts.values; delete opts.live;
      opts.x = Object.assign({ axis: null }, out.x || {});
      opts.y = Object.assign({ axis: null }, out.y || {});
      opts.style = Object.assign({ background: "transparent", color: theme.ink, fontFamily: theme.mono, fontSize: theme.labelSize + "px", overflow: "visible" }, out.style || {});
      var chart = window.Plot.plot(opts);
      node.replaceChildren(chart);
      var svg = chart.tagName.toLowerCase() === "svg" ? chart : chart.querySelector("svg");
      var sx = chart.scale("x"), sy = chart.scale("y");
      var x = d3.scaleLinear().domain(sx.domain).range(sx.range);
      var y = sy ? d3.scaleLinear().domain(sy.domain).range(sy.range) : null;
      var rulerY = opts.height - opts.marginBottom;
      var root = d3.select(svg);
      if (extras.values && y) {
        var under = root.insert("g", ":first-child");
        PB.valueLines(under, Object.assign({ y: y, x1: x.range()[0], x2: x.range()[1] }, extras.values));
      }
      if (extras.live && y) {
        var L = extras.live;
        var px = function (d) { return typeof L.x === "function" ? L.x(d) : d[L.x]; };
        var py = function (d) { return typeof L.y === "function" ? L.y(d) : d[L.y]; };
        var d = PB.curve(L.data.map(function (p) { return [x(px(p)), y(py(p))]; }));
        PB.live(root, d, { carriage: extras.ruler ? rulerY : null, label: L.label, ms: L.ms || 1500 });
      }
      if (extras.ruler) PB.ruler(root, Object.assign({ x: x, y: rulerY }, extras.ruler));
    });
    return { redraw: stop.run };
  };

  function plotMarks(theme) {
    var P = window.Plot;
    var color = { 2: theme.ink, 3: theme.plate, estimate: theme.ink2 };
    return {
      /* a 1.4 px line in ink (series 2) or plate ink (series 3), or the thin muted line of an
         estimate (0.9 px), each on a 4.5 px ground trap so lines never touch where they cross */
      line: function (data, o) {
        var s = o.series || 2;
        var base = Object.assign({ curve: "catmull-rom" }, o);
        delete base.series;
        return [
          P.line(data, Object.assign({}, base, { stroke: theme.page, strokeWidth: 4.5, strokeLinecap: "round" })),
          P.line(data, Object.assign({}, base, { stroke: color[s] || theme.ink, strokeWidth: s === "estimate" ? 0.9 : 1.4, strokeLinecap: "round", strokeLinejoin: "round" }))
        ];
      },
      /* points: 2.1 px muted, or 3.2 px ink when named(d) is true */
      dots: function (data, o) {
        var named = o.named || function () { return false; };
        var base = Object.assign({}, o);
        delete base.named;
        return [
          P.dot(data.filter(function (d) { return !named(d); }), Object.assign({}, base, { r: 2.1, fill: theme.ink2, stroke: null })),
          P.dot(data.filter(named), Object.assign({}, base, { r: 3.2, fill: theme.ink, stroke: null }))
        ];
      },
      /* a name at a mark, 12 px to its right, in the label face and the text color.
         finding: true sets it in the heavier slug weight. */
      endLabels: function (data, o) {
        var base = Object.assign({ dx: 12, textAnchor: "start", fill: theme.ink, lineAnchor: "middle" }, o);
        base.className = o.finding ? "pb-plot-finding" : "pb-plot-label";
        delete base.finding;
        return P.text(data, base);
      },
      /* a figure at a mark (the finding's last value) in the display face at 25 px, its baseline at the mark */
      figure: function (data, o) {
        return P.text(data, Object.assign({ dx: 12, dy: 1, textAnchor: "start", lineAnchor: "bottom", fill: theme.ink, className: "pb-plot-figure" }, o));
      }
    };
  }
  PB.marks = plotMarks;

  /* ---------------------------------------------------------------- canvas, animate (as in v1) */

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

  /* ---------------------------------------------------------------- scroll steps */

  /* root holds a .pb-steps-visual (the pinned figure) and .pb-step elements. onStep(index, stepEl)
     fires when a step becomes current. The kit writes the gauge under the pinned figure (one part
     per step, printed up to the current one), makes a step current when it crosses the reading line
     (55 to 65 percent of the screen height), and sets the lead so step 1 is current when the block pins.
     The first step is current at load. */
  PB.steps = function (root, onStep) {
    var node = resolve(root);
    var steps = Array.prototype.slice.call(node.querySelectorAll(".pb-step"));
    var visual = node.querySelector(".pb-steps-visual");
    var gauge = visual && visual.querySelector(".pb-steps-gauge");
    if (visual && !gauge) {
      gauge = el("div", { class: "pb-steps-gauge", role: "img" });
      steps.forEach(function () { gauge.appendChild(el("i")); });
      visual.appendChild(gauge);
    }
    var active = -1;
    function activate(i) {
      if (i === active || i < 0) return;
      active = i;
      steps.forEach(function (s, j) { s.classList.toggle("is-active", j === i); });
      if (gauge) {
        Array.prototype.forEach.call(gauge.children, function (part, j) { part.classList.toggle("is-on", j <= i); });
        gauge.setAttribute("aria-label", "Step " + (i + 1) + " of " + steps.length);
      }
      onStep(i, steps[i]);
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) activate(steps.indexOf(entry.target));
      });
    }, { rootMargin: "-55% 0px -35% 0px", threshold: 0 });
    steps.forEach(function (s) { io.observe(s); });
    function lead() {
      if (!visual || !steps.length) return;
      steps[0].style.setProperty("--pb-steps-lead", Math.max(16, Math.round(0.58 * window.innerHeight - visual.offsetHeight)) + "px");
    }
    lead();
    new ResizeObserver(lead).observe(visual || node);
    window.addEventListener("resize", lead);
    activate(0);
    return { count: steps.length, go: activate };
  };

  /* ---------------------------------------------------------------- controls */

  /* A slider. The handle is the carriage: a 12 by 22 px square in the text color on a ruler.
     opts: {label (what it changes, for the row and the input's name), min, max, step, value,
     format(v) (the current value in words, shown at the right of the row), valueText(v) (for screen
     readers, default format), onInput(v)}.
     Two forms. By default the kit draws its own ruler and puts the row (label left, value right)
     under it. With opts.over = {left, top, width} (px, relative to target, which is positioned) the
     input is laid transparently over a ruler the figure drew itself, its thumb on the ruler at
     top + 24, and the row goes in opts.row (an element) or is left out. */
  PB.slider = function (target, opts) {
    var node = resolve(target);
    var format = opts.format || function (v) { return String(v); };
    var valueText = opts.valueText || format;
    var id = nextId("pb-slider");
    var input = el("input", {
      type: "range", id: id, min: opts.min, max: opts.max,
      step: opts.step == null ? "any" : opts.step, value: opts.value, "aria-label": opts.label
    });
    input.setAttribute("aria-valuetext", valueText(Number(opts.value)));
    var output = el("output", { for: id, text: format(Number(opts.value)) });
    var head = el("div", { class: "pb-slider-head" }, [el("label", { for: id, text: opts.caption || opts.label }), output]);
    var wrap;
    if (opts.over) {
      input.className = "pb-carriage";
      input.style.left = opts.over.left + "px";
      input.style.top = opts.over.top + "px";
      input.style.width = opts.over.width + "px";
      if (getComputedStyle(node).position === "static") node.style.position = "relative";
      node.appendChild(input);
      wrap = input;
      if (opts.row) resolve(opts.row).appendChild(head);
    } else {
      wrap = el("div", { class: "pb-slider" }, [el("div", { class: "pb-slider-rail" }, [input]), head]);
      node.appendChild(wrap);
    }
    function update(v) {
      output.textContent = format(v);
      input.setAttribute("aria-valuetext", valueText(v));
    }
    input.addEventListener("input", function () {
      var v = Number(input.value);
      update(v);
      opts.onInput(v);
    });
    return {
      input: input,
      get value() { return Number(input.value); },
      set: function (v) { input.value = v; update(Number(v)); opts.onInput(Number(v)); }
    };
  };

  /* A segmented toggle: two or three joined segments; the chosen one is stamped with a check.
     opts: {label (shown above it, says what it changes), options: [{value, label}], value, onChange(value)}. */
  PB.toggle = function (target, opts) {
    var node = resolve(target);
    if (opts.label) node.appendChild(el("span", { class: "pb-label pb-toggle-label", text: opts.label }));
    var wrap = el("div", { class: "pb-toggle", role: "group", "aria-label": opts.label || "Options" });
    var current = opts.value;
    var buttons = opts.options.map(function (o) {
      var b = el("button", { type: "button", text: o.label, "aria-pressed": String(o.value === opts.value) });
      b.addEventListener("click", function () { select(o.value); });
      wrap.appendChild(b);
      return b;
    });
    function select(value) {
      if (value === current) return;
      current = value;
      opts.options.forEach(function (o, i) { buttons[i].setAttribute("aria-pressed", String(o.value === value)); });
      opts.onChange(value);
    }
    node.appendChild(wrap);
    return { set: select, get value() { return current; } };
  };

  /* The table twin of a data chart: the last row of a data figure, "The numbers", folded.
     opts: {caption (what the head row does not say, e.g. "All four values are estimates."),
     columns: [{key, label, numeric, format(value, row)}], rows: [{...}], summary, open}.
     format may return a string or a node. */
  PB.table = function (target, opts) {
    var node = resolve(target);
    var table = el("table", { class: "pb-table" });
    if (opts.caption) table.appendChild(el("caption", { text: opts.caption }));
    var head = el("tr");
    opts.columns.forEach(function (c) { head.appendChild(el("th", { scope: "col", class: c.numeric ? "num" : null, text: c.label })); });
    table.appendChild(el("thead", {}, [head]));
    var body = el("tbody");
    opts.rows.forEach(function (row) {
      var tr = el("tr");
      opts.columns.forEach(function (c) {
        var value = row[c.key];
        var out = c.format ? c.format(value, row) : String(value);
        var td = el("td", { class: c.numeric ? "num" : null });
        if (out instanceof Node) td.appendChild(out); else td.textContent = out;
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    table.appendChild(body);
    var details = el("details", { class: "pb-data" }, [
      el("summary", { text: opts.summary || "The numbers" }),
      el("div", { class: "pb-table-wrap" }, [table])
    ]);
    if (opts.open) details.open = true;
    node.appendChild(details);
    return details;
  };

  /* ---------------------------------------------------------------- the touch readout */

  /* A readout that appears while a mark is touched: a small solid slab above the mark.
     show(content, at): content is a string, a node, or {name, rows: [[quantity, value, unit], ...]};
     at is a pointer event or {x, y} in viewport px (the mark's center). hide(). */
  PB.tooltip = function () {
    var tip = el("div", { class: "pb-tip", role: "status" });
    tip.hidden = true;
    document.body.appendChild(tip);
    return {
      node: tip,
      show: function (content, at) {
        if (typeof content === "string") tip.textContent = content;
        else if (content instanceof Node) tip.replaceChildren(content);
        else {
          var dl = el("dl");
          (content.rows || []).forEach(function (r) {
            dl.appendChild(el("dt", { text: r[0] }));
            dl.appendChild(el("dd", {}, [String(r[1])].concat(r[2] ? [" ", el("i", { text: r[2] })] : [])));
          });
          tip.replaceChildren(el("b", { text: content.name || "" }), dl);
        }
        tip.hidden = false;
        var x = at.clientX != null ? at.clientX : at.x, y = at.clientY != null ? at.clientY : at.y;
        var pad = 12;
        var rect = tip.getBoundingClientRect();
        var left = Math.min(window.innerWidth - rect.width - pad, Math.max(pad, x - rect.width / 2));
        var top = y - 14 - rect.height;
        if (top < pad) top = y + 14;
        tip.style.left = left + "px";
        tip.style.top = top + "px";
      },
      hide: function () { tip.hidden = true; }
    };
  };

  /* The marks a chart adds under the readout: a ring on the touched mark over a ground dot, a drop
     line to the ruler, and a tick on the ruler. opts: x, y, rulerY. Returns the group; remove() it
     when the finger lifts. */
  PB.touch = function (g, opts) {
    g = sel(g).append("g").attr("class", "pb-touch").attr("aria-hidden", "true");
    g.append("line").attr("class", "pb-touch-drop").attr("x1", opts.x).attr("x2", opts.x).attr("y1", opts.y + 6.5).attr("y2", opts.rulerY);
    g.append("circle").attr("class", "pb-touch-trap").attr("cx", opts.x).attr("cy", opts.y).attr("r", 8);
    g.append("circle").attr("class", "pb-touch-ring").attr("cx", opts.x).attr("cy", opts.y).attr("r", 6.5);
    g.append("circle").attr("class", "pb-touch-core").attr("cx", opts.x).attr("cy", opts.y).attr("r", 2.6);
    g.append("line").attr("class", "pb-touch-leader").attr("x1", opts.x).attr("x2", opts.x).attr("y1", opts.y - 6.5).attr("y2", opts.y - 14);
    g.append("line").attr("class", "pb-touch-tick").attr("x1", opts.x).attr("x2", opts.x).attr("y1", opts.rulerY).attr("y2", opts.rulerY + 7);
    return g;
  };

  /* ---------------------------------------------------------------- numbers */

  var SIGNS = {
    times: "M1.6 1.6l6.8 6.8M8.4 1.6l-6.8 6.8",
    gt: "M1.8 1.4l6.6 3.6-6.6 3.6"
  };
  /* The multiplication and greater-than signs beside display numerals are drawn, not typed.
     Returns an inline SVG plus the typed character for screen readers. */
  PB.sign = function (which) {
    var frag = document.createDocumentFragment();
    var svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", "pb-sign");
    svg.setAttribute("data-sign", which);
    svg.setAttribute("viewBox", "0 0 10 10");
    svg.setAttribute("aria-hidden", "true");
    var p = document.createElementNS(SVGNS, "path");
    p.setAttribute("d", SIGNS[which]);
    if (which === "gt") p.setAttribute("stroke-linejoin", "miter");
    svg.appendChild(p);
    frag.appendChild(svg);
    frag.appendChild(el("span", { class: "pb-sr", text: which === "gt" ? "greater than " : "×" }));
    return frag;
  };

  /* Number formatting helpers so every page prints numbers the same way. sci returns an element:
     the mantissa, the drawn multiplication sign, 10, and a real superscript with a true minus. */
  PB.fmt = {
    int: function (v) { return Math.round(v).toLocaleString("en-US"); },
    fixed: function (digits) { return function (v) { return Number(v).toFixed(digits).replace(/^-/, "−"); }; },
    pct: function (v, digits) { return (v * 100).toFixed(digits == null ? 0 : digits) + "%"; },
    compact: function (v) { return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(v); },
    minus: function (v) { return String(v).replace(/-/g, "−"); },
    sci: function (v, digits) {
      var span = el("span", { class: "pb-sci" });
      if (v === 0) { span.textContent = "0"; return span; }
      var exp = Math.floor(Math.log10(Math.abs(v)));
      var mant = v / Math.pow(10, exp);
      span.appendChild(document.createTextNode(mant.toFixed(digits == null ? 1 : digits).replace(/^-/, "−")));
      span.appendChild(PB.sign("times"));
      span.appendChild(document.createTextNode("10"));
      span.appendChild(el("sup", { text: String(exp).replace(/-/g, "−") }));
      return span;
    }
  };

  /* ---------------------------------------------------------------- page setup at boot */

  function setupTopbar() {
    if (PB.inApp || document.querySelector(".pb-topbar")) return;
    var article = document.querySelector("article.pb");
    if (!article) return;
    var link = el("a", { class: "pb-wordmark", href: "/", "aria-label": "Paperboy, to the website" }, ["Paper", el("em", { text: "boy" }), el("i")]);
    article.parentNode.insertBefore(el("header", { class: "pb-topbar" }, [link]), article);
  }

  function setupSigns() {
    document.querySelectorAll("span.pb-sign, i.pb-sign").forEach(function (s) {
      var t = s.textContent.trim();
      var which = t === "×" || t === "x" || t === "*" ? "times" : t === ">" ? "gt" : null;
      if (!which) return;
      s.replaceWith(PB.sign(which));
    });
    document.querySelectorAll('.pb-badge[data-status="preprint"]').forEach(function (b) {
      if (!b.firstElementChild) b.replaceChildren(el("span", { text: b.textContent }));
    });
  }

  /* The two voices of a head. When a head runs to more than one line and its second voice fits
     on a line of its own, the second voice takes its own line (the boards' section heads). Otherwise
     it never leaves a single italic word at the end of a line: then too it breaks before the clause. */
  function lineTops(node) {
    var r = document.createRange();
    r.selectNodeContents(node);
    var tops = [];
    Array.prototype.forEach.call(r.getClientRects(), function (rc) {
      if (rc.width < 1) return;
      if (!tops.some(function (t) { return Math.abs(t - rc.top) < 4; })) tops.push(rc.top);
    });
    return tops.length;
  }
  function setupTurns() {
    var heads = document.querySelectorAll(".pb-title em, .pb h2 em, .pb h3 em, .pb-fig-title em");
    function check() {
      heads.forEach(function (em) {
        var head = em.parentElement;
        em.classList.remove("pb-turn");
        if (lineTops(head) <= 1) return;
        em.classList.add("pb-turn");
        if (lineTops(em) === 1) return;
        em.classList.remove("pb-turn");
        var walker = document.createTreeWalker(em, NodeFilter.SHOW_TEXT);
        var tops = [];
        for (var t = walker.nextNode(); t && tops.length < 2; t = walker.nextNode()) {
          var re = /\S+/g, m;
          while ((m = re.exec(t.nodeValue)) && tops.length < 2) {
            var r = document.createRange();
            r.setStart(t, m.index);
            r.setEnd(t, m.index + 1);
            tops.push(r.getBoundingClientRect().top);
          }
        }
        if (tops.length === 2 && Math.abs(tops[0] - tops[1]) > 4) em.classList.add("pb-turn");
      });
    }
    check();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(check);
    var queued = false;
    window.addEventListener("resize", function () {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; check(); });
    });
  }

  /* A figure below the first screen holds its one draw-in until it scrolls into view, once. */
  function setupWait() {
    var nodes = document.querySelectorAll(".pb-fig, .pb-stage, .pb-steps-visual, .pb-wait-here");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.remove("pb-wait"); io.unobserve(entry.target); }
      });
    }, { rootMargin: "0px 0px -15% 0px" });
    nodes.forEach(function (n) {
      if (n.getBoundingClientRect().top > window.innerHeight * 0.85) {
        n.classList.add("pb-wait");
        io.observe(n);
      }
    });
  }

  function setupTerms() {
    var pop = null, open = null;
    function close() {
      if (pop) { pop.remove(); pop = null; }
      if (open) { open.setAttribute("aria-expanded", "false"); open = null; }
    }
    document.addEventListener("click", function (event) {
      var term = event.target.closest && event.target.closest(".pb-term");
      var was = open;
      close();
      if (!term || term === was) return;
      var para = term.closest("p, li, figcaption, .pb-step") || term.parentElement;
      var col = para.getBoundingClientRect();
      var lh = parseFloat(getComputedStyle(para).lineHeight) || 25;
      var r = term.getBoundingClientRect();
      var lineBottom = r.top + r.height / 2 + lh / 2;
      term.setAttribute("aria-expanded", "true");
      open = term;
      pop = el("div", { class: "pb-term-pop", role: "tooltip" }, [
        el("b", { text: term.dataset.term || term.textContent }),
        el("span", { text: term.dataset.def || "" })
      ]);
      document.body.appendChild(pop);
      pop.style.left = col.left + window.scrollX + "px";
      pop.style.width = col.width + "px";
      pop.style.top = lineBottom + window.scrollY + "px";
      pop.style.height = Math.ceil(pop.getBoundingClientRect().height / lh) * lh + "px";
    });
    window.addEventListener("scroll", close, { passive: true });
    document.querySelectorAll(".pb-term").forEach(function (t) {
      t.setAttribute("tabindex", "0");
      t.setAttribute("role", "button");
      t.setAttribute("aria-expanded", "false");
      t.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); t.click(); }
      });
    });
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
    run(setupTopbar);
    run(setupMath);
    run(setupSigns);
    run(setupTerms);
    run(setupWait);
    readyFns.forEach(run);
    run(setupTurns);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { document.documentElement.dataset.pbReady = "1"; });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.PB = PB;
})();
