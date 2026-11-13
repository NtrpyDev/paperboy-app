package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.Layout
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.rank.Rating
import io.github.ntrpydev.paperboy.ui.design.DoubleRule
import io.github.ntrpydev.paperboy.ui.design.HatchedTag
import io.github.ntrpydev.paperboy.ui.design.Headline
import io.github.ntrpydev.paperboy.ui.design.Icons
import io.github.ntrpydev.paperboy.ui.design.Margin
import io.github.ntrpydev.paperboy.ui.design.OutlineButton
import io.github.ntrpydev.paperboy.ui.design.OutlineTag
import io.github.ntrpydev.paperboy.ui.design.RatingButton
import io.github.ntrpydev.paperboy.ui.design.SlabButton
import io.github.ntrpydev.paperboy.ui.design.SolidTag
import io.github.ntrpydev.paperboy.ui.design.TextLink
import io.github.ntrpydev.paperboy.ui.design.voices
import io.github.ntrpydev.paperboy.ui.theme.Paperboy
import kotlin.math.max

/**
 * One paper in the feed, and the divider under it (SYSTEM.md 9.3 and 9.8).
 *
 * An explained card: tag row, headline at 44, the plate full bleed, the readout row,
 * summary, "See it explained", the rating row. A short card: tag row, headline at 30, the
 * stat when the paper has a readout (otherwise the summary), "Read the paper", the rating row.
 *
 * [plateUrl] is the plate still for the current theme, or null. [press] plays the headline's
 * Press, once, when the card first appears.
 */
@Composable
fun FeedCard(
    item: FeedItem,
    plateUrl: String?,
    rating: Rating?,
    onOpen: () -> Unit,
    onOpenPaper: () -> Unit,
    onRate: (Rating) -> Unit,
    modifier: Modifier = Modifier,
    press: Boolean = false,
) {
    val type = Paperboy.type
    val c = Paperboy.colors
    val explained = item.hasExplainer
    val voices = voices(item.hook, item.hookTurn)
    Column(
        modifier
            .fillMaxWidth()
            .clickable(interactionSource = null, indication = null, onClick = onOpen),
    ) {
        TagRow(item, onOpenPaper)
        val headlineModifier = Modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 10.dp)
        if (explained) {
            Headline(voices, type.headline, headlineModifier, press = press)
            val hero = item.hero
            if (plateUrl != null && hero != null) {
                val still = if (c.dark) hero.night else null
                val w = still?.width ?: hero.width
                val h = still?.height ?: hero.height
                if (w > 0 && h > 0) {
                    AsyncImage(
                        model = plateUrl,
                        contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier
                            .padding(top = 12.dp)
                            .fillMaxWidth()
                            .aspectRatio(w.toFloat() / h),
                    )
                }
            }
            ReadoutRow(item.readout, hero)
            Text(
                item.summary,
                style = type.bodyFeed,
                color = c.text,
                modifier = Modifier.padding(start = Margin, end = Margin, top = 10.dp),
            )
        } else {
            Headline(voices, type.head2, headlineModifier, press = press)
            val readout = item.readout
            if (readout != null) {
                Stat(readout)
            } else {
                Text(
                    item.summary,
                    style = type.bodyFeed,
                    color = c.text,
                    modifier = Modifier.padding(start = Margin, end = Margin, top = 8.dp),
                )
            }
        }
        Column(
            Modifier.padding(start = Margin, end = Margin, top = 14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            if (explained) SlabButton("See it explained", onOpen) else OutlineButton("Read the paper", onOpen)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                RatingButton("More like this", Icons.Plus, rating == Rating.More, { onRate(Rating.More) }, Modifier.weight(1f))
                RatingButton("Less like this", Icons.Minus, rating == Rating.Less, { onRate(Rating.Less) }, Modifier.weight(1f))
            }
        }
        Spacer(Modifier.height(18.dp))
        DoubleRule(heavyOnTop = false, modifier = Modifier.padding(horizontal = Margin))
    }
}

/**
 * The tag row: the field tag, the badge, and the journal link at the right end. When the
 * link does not fit beside the tags it takes its own line, right aligned (SYSTEM.md 9.5).
 * The journal name is never shortened.
 */
@Composable
private fun TagRow(item: FeedItem, onOpenPaper: () -> Unit) {
    Layout(
        modifier = Modifier.fillMaxWidth().padding(start = Margin, end = Margin, top = 13.dp),
        content = {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                OutlineTag(fieldLabel(item.field))
                if (item.isPeerReviewed) SolidTag(badgeLabel(item)) else HatchedTag(badgeLabel(item))
            }
            Box { TextLink(item.venue, Icons.OutArrow, onOpenPaper, overhang = true) }
        },
    ) { measurables, constraints ->
        val width = constraints.maxWidth
        val tags = measurables[0].measure(constraints.copy(minWidth = 0))
        val gap = 6.dp.roundToPx()
        val linkWidth = measurables[1].maxIntrinsicWidth(Constraints.Infinity)
        val oneLine = tags.width + gap + linkWidth <= width
        val link = measurables[1].measure(Constraints(maxWidth = if (oneLine) width - tags.width - gap else width))
        if (oneLine) {
            val height = max(tags.height, link.height)
            layout(width, height) {
                tags.place(0, (height - tags.height) / 2)
                link.place(width - link.width, (height - link.height) / 2)
            }
        } else {
            layout(width, tags.height + gap + link.height) {
                tags.place(0, 0)
                link.place(width - link.width, tags.height + gap)
            }
        }
    }
}

/** The badge text from the glossary: PREPRINT or PEER-REVIEWED. */
fun badgeLabel(item: FeedItem): String = if (item.isPeerReviewed) "PEER-REVIEWED" else "PREPRINT"

/** Display names for the schema's field values. */
fun fieldLabel(field: String): String = when (field) {
    "cs" -> "Computer science"
    "social" -> "Social science"
    else -> field.replaceFirstChar { it.uppercase() }
}
