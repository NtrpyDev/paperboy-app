package io.github.ntrpydev.paperboy.rank

import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.Hero

/** A feed item for tests, with every field the ranker and taste model read settable. */
internal fun item(
    id: String,
    field: String = "physics",
    tags: List<String> = listOf("optics"),
    status: String = "preprint",
    explained: Boolean = false,
    significance: Double = 5.0,
    addedAt: String = "2026-11-12T00:00:00Z",
) = FeedItem(
    id = id,
    title = "Title of $id",
    hook = "Hook of $id",
    summary = "Summary of $id, long enough to read like a summary.",
    field = field,
    tags = tags,
    status = status,
    venue = "arXiv",
    published = addedAt.take(10),
    authorsShort = "Someone et al.",
    url = "https://example.org/$id",
    hasExplainer = explained,
    explainer = if (explained) "papers/$id/" else null,
    hero = if (explained) Hero("papers/$id/hero.webp", 1200, 675) else null,
    significance = significance,
    addedAt = addedAt,
)
