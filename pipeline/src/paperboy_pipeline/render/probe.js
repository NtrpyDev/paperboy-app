/* Runs inside the explainer page after it is ready and has been scrolled through.
   Measures what the render check needs and returns plain data; it never changes the page.
   `structure` holds problems with the document itself and `layout` holds problems that
   depend on the theme or motion setting. Each problem is [rule, detail]. */
(function () {
  "use strict";

  var SECTIONS = ["question", "method", "findings", "confidence", "matters"];
  var KINDS = ["data", "illustration", "paper"];
  var HERO_KINDS = ["data", "illustration"];
  var DEPTHS = ["full", "abstract"]; // article.pb data-depth: what the page was built from; no mark is "full"
  /* A page built from the abstract must tell the reader so in its "How sure is this?" section. */
  var DEPTH_NOTE = /built from the paper['\u2019]s abstract,?\s+not its full text/i;
  var KIT = /^\/kit\/v([1-9][0-9]*)\//;
  var MIN_TEXT_PX = 11;
  var MIN_CONTROL_PX = 40;
  var CONTROLS = 'button, input[type="button"], input[type="submit"], input[type="reset"], input[type="range"], .pb-btn';
  var LIMIT = 5; // examples listed per rule

  var doc = document.documentElement;
  var vw = window.innerWidth;
  var article = document.querySelector("article.pb");
  var structure = [];
  var layout = [];
  function s(rule, detail) { structure.push([rule, detail]); }
  function l(rule, detail) { layout.push([rule, detail]); }

  function describe(node) {
    var out = node.tagName.toLowerCase();
    if (node.id) out += "#" + node.id;
    var cls = typeof node.className === "string" ? node.className.trim() : "";
    if (cls) out += "." + cls.split(/\s+/).join(".");
    var text = (typeof node.innerText === "string" ? node.innerText : node.textContent || "").trim().replace(/\s+/g, " ");
    if (text) out += ' "' + (text.length > 40 ? text.slice(0, 40) + "..." : text) + '"';
    return out;
  }

  function rendered(node) {
    if (!node.getClientRects().length) return false;
    var cs = getComputedStyle(node);
    return cs.visibility !== "hidden" && cs.display !== "none";
  }

  function listed(items) {
    var shown = items.slice(0, LIMIT).join("; ");
    return items.length > LIMIT ? shown + "; and " + (items.length - LIMIT) + " more" : shown;
  }

  /* ---- The document: head, kit, page code ---- */

  var colorScheme = document.querySelector('meta[name="color-scheme"]');
  var schemes = colorScheme ? (colorScheme.getAttribute("content") || "").toLowerCase().split(/[\s,]+/) : [];
  if (schemes.indexOf("dark") < 0 || schemes.indexOf("light") < 0) {
    s("missing-color-scheme", colorScheme ? 'meta color-scheme is "' + colorScheme.getAttribute("content") + '", needs "dark light"' : 'no <meta name="color-scheme" content="dark light">');
  }
  if (!document.querySelector('meta[name="viewport"]')) s("missing-viewport", 'no <meta name="viewport">');

  var assets = [];
  document.querySelectorAll("script[src]").forEach(function (n) { assets.push(n.getAttribute("src")); });
  document.querySelectorAll('link[rel~="stylesheet"][href]').forEach(function (n) { assets.push(n.getAttribute("href")); });
  var stray = [], versions = [];
  assets.forEach(function (a) {
    var m = KIT.exec(a);
    if (!m) stray.push(a);
    else if (versions.indexOf(m[1]) < 0) versions.push(m[1]);
  });
  if (stray.length) s("kit-not-absolute", "scripts and stylesheets must load from /kit/v<N>/: " + listed(stray));
  if (versions.length > 1) s("kit-not-absolute", "kit files must all come from one version, found " + versions.map(function (v) { return "/kit/v" + v + "/"; }).join(", "));
  var kitBase = versions.length ? "/kit/v" + versions[0] + "/" : "/kit/v<N>/";
  ["paperboy.css", "paperboy.js"].forEach(function (name) {
    if (assets.indexOf(kitBase + name) < 0) s("kit-not-absolute", "does not load " + kitBase + name);
  });

  var outside = [];
  document.querySelectorAll("script:not([src])").forEach(function (n, i) {
    var type = (n.getAttribute("type") || "").trim().toLowerCase();
    if (type && type !== "text/javascript" && type !== "module" && type !== "application/javascript") return;
    var code = n.textContent.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "").trim();
    if (!code) return;
    if (!/^PB\.ready\(/.test(code) || !/\)\s*;?$/.test(code)) outside.push("inline script " + (i + 1) + ' starts "' + code.slice(0, 40).replace(/\s+/g, " ") + '"');
  });
  if (outside.length) s("code-outside-ready", "page code must be wrapped in PB.ready(...): " + listed(outside));

  /* ---- The article: hero, sections, source, figures ---- */

  var figures = [];
  var depth = null;
  if (!article) {
    s("missing-root", 'no <article class="pb">');
  } else {
    var hero = article.querySelector(".pb-hero");
    if (!hero) {
      s("hero-incomplete", "no .pb-hero");
    } else {
      [".pb-title", ".pb-dek"].forEach(function (sel) {
        if (!hero.querySelector(sel)) s("hero-incomplete", "hero has no " + sel);
      });
      var stages = hero.querySelectorAll(".pb-stage");
      if (stages.length !== 1) s("hero-incomplete", "hero has " + stages.length + " .pb-stage elements, needs exactly 1");
      if (stages.length) {
        var heroKind = stages[0].dataset.kind;
        if (HERO_KINDS.indexOf(heroKind) < 0) s("hero-without-kind", "the hero .pb-stage needs data-kind data or illustration" + (heroKind !== undefined ? ', has data-kind="' + heroKind + '"' : ""));
      }
    }

    var marked = Array.prototype.slice.call(article.querySelectorAll("[data-section]"));
    var names = marked.map(function (n) { return n.dataset.section; });
    var known = names.filter(function (n) { return SECTIONS.indexOf(n) >= 0; });
    SECTIONS.forEach(function (name) {
      var count = names.filter(function (n) { return n === name; }).length;
      if (count === 0) s("missing-section", 'no data-section="' + name + '"');
      if (count > 1) s("duplicate-section", 'data-section="' + name + '" appears ' + count + " times");
    });
    var expected = SECTIONS.filter(function (n) { return known.indexOf(n) >= 0; });
    var seen = known.filter(function (n, i) { return known.indexOf(n) === i; });
    if (seen.join() !== expected.join()) s("section-order", "sections run " + seen.join(", ") + "; the order is " + SECTIONS.join(", "));

    var depthMark = article.getAttribute("data-depth");
    if (depthMark === null) depth = "full";
    else if (DEPTHS.indexOf(depthMark) >= 0) depth = depthMark;
    else s("unknown-depth", 'article.pb has data-depth="' + depthMark + '", needs "full", "abstract", or no data-depth');
    if (depth === "abstract") {
      var ledger = article.querySelector('[data-section="confidence"]');
      var said = ledger && DEPTH_NOTE.test((ledger.innerText || ledger.textContent || "").replace(/\s+/g, " "));
      if (!said) s("missing-depth-note", 'a page with data-depth="abstract" must say "Built from the paper\'s abstract, not its full text." in its data-section="confidence" section');
    }

    var source = article.querySelector(".pb-source");
    if (!source) {
      s("missing-source", "no .pb-source footer");
    } else {
      if (!source.querySelector('a[href^="http://"], a[href^="https://"]')) s("missing-source-link", "the .pb-source footer has no link to the paper");
      if (!/machine[\s-]+written|written\s+by\s+a\s+machine/i.test(source.textContent)) s("missing-source-note", 'the .pb-source footer does not say "machine written" or "written by a machine"');
    }

    var first = marked[0], last = marked[marked.length - 1];
    var FOLLOWS = Node.DOCUMENT_POSITION_FOLLOWING;
    if (hero && first && !(hero.compareDocumentPosition(first) & FOLLOWS)) s("section-order", "the hero must come before the sections");
    if (source && last && !(last.compareDocumentPosition(source) & FOLLOWS)) s("section-order", "the .pb-source footer must come after the sections");

    figures = Array.prototype.slice.call(article.querySelectorAll("figure"));
    var noKind = [], noTable = [], noCredit = [];
    figures.forEach(function (f) {
      var kind = f.dataset.kind;
      if (KINDS.indexOf(kind) < 0) noKind.push(describe(f) + (kind ? ' has data-kind="' + kind + '"' : ""));
      if (kind === "data" && !f.querySelector("table")) noTable.push(describe(f));
      if (kind === "paper" && !f.querySelector(".pb-credit")) noCredit.push(describe(f));
    });
    if (noKind.length) s("figure-without-kind", "every figure needs data-kind data, illustration, or paper: " + listed(noKind));
    if (noTable.length) s("data-figure-without-table", "data figures need a table of their numbers: " + listed(noTable));
    if (noCredit.length) s("paper-figure-without-credit", "paper figures need a .pb-credit line: " + listed(noCredit));
  }

  /* ---- Layout at this theme and motion setting ---- */

  var pageWidth = Math.max(doc.scrollWidth, document.body ? document.body.scrollWidth : 0);
  var wide = [];
  function clipsX(node) {
    for (var n = node.parentElement; n && n !== document.body && n !== doc; n = n.parentElement) {
      var ox = getComputedStyle(n).overflowX;
      if (ox !== "visible") return true;
    }
    return false;
  }
  document.querySelectorAll("body *").forEach(function (node) {
    if (node.closest("script, style, head")) return;
    var r = node.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (r.right <= vw + 0.5 && r.left >= -0.5) return;
    if (!rendered(node) || clipsX(node)) return;
    wide.push(describe(node) + " spans " + Math.round(r.left) + " to " + Math.round(r.right) + " px");
  });
  if (pageWidth > vw + 0.5) l("overflow-x", "page is " + pageWidth + " px wide at a " + vw + " px viewport");
  if (wide.length) l("overflow-x", "content runs past the " + vw + " px viewport: " + listed(wide));

  var small = [];
  function effectiveSize(el, size) {
    if (el instanceof SVGElement && el.getScreenCTM) {
      var m = el.getScreenCTM();
      if (m) size *= Math.sqrt(Math.abs(m.a * m.d - m.b * m.c));
    }
    return size;
  }
  var walker = document.createTreeWalker(document.body || doc, NodeFilter.SHOW_TEXT);
  var checked = new Set();
  for (var t = walker.nextNode(); t; t = walker.nextNode()) {
    var el = t.parentElement;
    if (!el || checked.has(el) || !t.nodeValue.trim() || el.closest("script, style")) continue;
    var range = document.createRange();
    range.selectNodeContents(t);
    var rects = Array.prototype.filter.call(range.getClientRects(), function (r) { return r.width > 0 && r.height > 0; });
    if (!rects.length) continue;
    var cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || parseFloat(cs.opacity) === 0) continue;
    checked.add(el);
    var size = effectiveSize(el, parseFloat(cs.fontSize));
    if (size < MIN_TEXT_PX - 0.005) small.push(describe(el) + " at " + size.toFixed(2) + " px");
  }
  document.querySelectorAll("body *").forEach(function (node) {
    if (!rendered(node)) return;
    ["::before", "::after"].forEach(function (pseudo) {
      var ps = getComputedStyle(node, pseudo);
      if (ps.display === "none") return;
      var m = /^"(.*)"$/.exec(ps.content || "");
      if (!m || !m[1].trim()) return;
      var size = parseFloat(ps.fontSize);
      if (size < MIN_TEXT_PX - 0.005) small.push(describe(node) + pseudo + ' "' + m[1] + '" at ' + size.toFixed(2) + " px");
    });
  });
  if (small.length) l("small-text", "text must be at least " + MIN_TEXT_PX + " px: " + listed(small));

  var tiny = [];
  document.querySelectorAll(CONTROLS).forEach(function (node) {
    if (!rendered(node)) return;
    var r = node.getBoundingClientRect();
    if (Math.min(r.width, r.height) < MIN_CONTROL_PX - 0.5) tiny.push(describe(node) + " is " + Math.round(r.width) + " by " + Math.round(r.height) + " px");
  });
  if (tiny.length) l("small-control", "controls must be at least " + MIN_CONTROL_PX + " px in their smaller dimension: " + listed(tiny));

  /* ---- The page's text, for the numbers check (paperboy_pipeline.numbers) ----
     Every text the page prints, drawn labels included, as [zone, text] runs. A run ends at a
     block element and at each SVG <text>. zone is "scale" inside the kit's ruler and value line
     labels (.pb-tick-label, .pb-value-label), "slug" in the plate slug, "source" in the source
     footer, otherwise "text". <sup> becomes ^{...} and <sub> _{...}; KaTeX math is read from
     its TeX source; the kit's drawn signs (.pb-sign) are read as their character. Text in a
     closed <details> (a figure's table) counts: one tap shows it. */
  var runs = [];
  (function () {
    var BLOCK = /^(block|flex|grid|table|table-row|table-cell|table-caption|table-row-group|table-header-group|table-footer-group|list-item|flow-root)$/;
    var SKIP = /^(script|style|noscript|template|head|title)$/;
    var cur = null;
    function flush() {
      if (cur && cur.text.trim()) runs.push([cur.zone, cur.text.replace(/\s+/g, " ").trim()]);
      cur = null;
    }
    function emit(zone, text) {
      if (cur && cur.zone !== zone) flush();
      if (!cur) cur = { zone: zone, text: "" };
      cur.text += text;
    }
    function walk(node, zone) {
      if (node.nodeType === 3) { emit(zone, node.nodeValue); return; }
      if (node.nodeType !== 1) return;
      var tag = node.tagName.toLowerCase();
      if (SKIP.test(tag) || node.classList.contains("katex-mathml")) return;
      if (node.matches(".pb-tick-label, .pb-value-label")) zone = "scale";
      else if (node.matches(".pb-plate-slug")) zone = "slug";
      else if (node.matches(".pb-source")) zone = "source";
      if (node.classList.contains("katex")) {
        var tex = node.querySelector('annotation[encoding="application/x-tex"]');
        emit(zone, " \\(" + (tex ? tex.textContent : node.textContent) + "\\) ");
        return;
      }
      if (node.classList.contains("pb-sign")) {
        emit(zone, { times: "×", gt: ">" }[node.getAttribute("data-sign")] || " ");
        return;
      }
      var svg = node instanceof SVGElement;
      var block = svg ? (tag === "text" || tag === "svg" && !node.closest("p, span, li, td, th, h1, h2, h3, h4, figcaption, cite, small, b, em, a"))
                      : tag === "br" || BLOCK.test(getComputedStyle(node).display);
      if (block) flush();
      /* Element edges are word edges ("<b>Record</b><span>30+</span>" reads "Record 30+"), so a
         number never fuses with a label beside it into a name like "Record30". */
      emit(zone, tag === "sup" ? " ^{" : tag === "sub" ? " _{" : " ");
      for (var c = node.firstChild; c; c = c.nextSibling) walk(c, zone);
      emit(zone, tag === "sup" || tag === "sub" ? "} " : " ");
      if (block) flush();
    }
    if (document.body) walk(document.body, "text");
    flush();
  })();

  return {
    ready: doc.dataset.pbReady === "1",
    text: runs,
    errors: Array.isArray(window.__pbErrors) ? window.__pbErrors.slice() : null,
    height: Math.ceil(Math.max(doc.scrollHeight, document.body ? document.body.scrollHeight : 0)),
    figures: figures.length,
    dataFigures: figures.filter(function (f) { return f.dataset.kind === "data"; }).length,
    kit: versions.length === 1 ? parseInt(versions[0], 10) : null,
    depth: depth,
    structure: structure,
    layout: layout
  };
})()
