/* Runs inside the explainer page after it is ready and has been scrolled through.
   Measures what the render check needs and returns plain data; it never changes the page.
   `structure` holds problems with the document itself and `layout` holds problems that
   depend on the theme or motion setting. Each problem is [rule, detail]. */
(function () {
  "use strict";

  var SECTIONS = ["question", "method", "findings", "confidence", "matters"];
  var KINDS = ["data", "illustration", "paper"];
  var KIT = "/kit/v1/";
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
  var stray = assets.filter(function (a) { return a.indexOf(KIT) !== 0; });
  if (stray.length) s("kit-not-absolute", "scripts and stylesheets must load from " + KIT + ": " + listed(stray));
  ["paperboy.css", "paperboy.js"].forEach(function (name) {
    if (assets.indexOf(KIT + name) < 0) s("kit-not-absolute", "does not load " + KIT + name);
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
      var stages = hero.querySelectorAll(".pb-stage").length;
      if (stages !== 1) s("hero-incomplete", "hero has " + stages + " .pb-stage elements, needs exactly 1");
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

    var source = article.querySelector(".pb-source");
    if (!source) {
      s("missing-source", "no .pb-source footer");
    } else {
      if (!source.querySelector('a[href^="http://"], a[href^="https://"]')) s("missing-source-link", "the .pb-source footer has no link to the paper");
      if (!/machine[\s-]+written/i.test(source.textContent)) s("missing-source-note", 'the .pb-source footer does not say "machine written"');
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

  return {
    ready: doc.dataset.pbReady === "1",
    errors: Array.isArray(window.__pbErrors) ? window.__pbErrors.slice() : null,
    height: Math.ceil(Math.max(doc.scrollHeight, document.body ? document.body.scrollHeight : 0)),
    figures: figures.length,
    dataFigures: figures.filter(function (f) { return f.dataset.kind === "data"; }).length,
    structure: structure,
    layout: layout
  };
})()
