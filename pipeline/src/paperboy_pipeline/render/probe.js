/* Runs inside the explainer page after it is ready. Measures what the render check needs
   and returns plain data; it never changes the page. */
(function () {
  "use strict";

  var doc = document.documentElement;
  var article = document.querySelector("article.pb");
  var figures = article ? Array.prototype.slice.call(article.querySelectorAll("figure")) : [];

  return {
    ready: doc.dataset.pbReady === "1",
    errors: Array.isArray(window.__pbErrors) ? window.__pbErrors.slice() : null,
    height: Math.ceil(Math.max(doc.scrollHeight, document.body ? document.body.scrollHeight : 0)),
    figures: figures.length,
    dataFigures: figures.filter(function (f) { return f.dataset.kind === "data"; }).length
  };
})()
