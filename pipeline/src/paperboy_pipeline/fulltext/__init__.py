"""Fetches a paper's free, lawful full text and converts it to Markdown.

sources.fetch(candidate, client) picks the route for the candidate's fulltext.kind and
returns a Paper; document.render(paper) writes it out. Converters: latexml (arXiv HTML),
jats (bioRxiv, medRxiv, Europe PMC), mathml (MathML without TeX).
"""
