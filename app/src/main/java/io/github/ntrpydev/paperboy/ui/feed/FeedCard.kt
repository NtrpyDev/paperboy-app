package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import io.github.ntrpydev.paperboy.feed.FeedItem

/**
 * One paper in the feed. An explained card shows its hero image; a short card has none.
 * [heroUrl] is the absolute hero image address, or null for a short card.
 */
@Composable
fun FeedCard(
    item: FeedItem,
    heroUrl: String?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(onClick = onClick, modifier = modifier.fillMaxWidth()) {
        val hero = item.hero
        if (heroUrl != null && hero != null && hero.width > 0 && hero.height > 0) {
            AsyncImage(
                model = heroUrl,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(hero.width.toFloat() / hero.height),
            )
        }
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = badgeLabel(item) + "  ·  " + fieldLabel(item.field),
                style = MaterialTheme.typography.labelMedium,
            )
            Text(text = item.hook, style = MaterialTheme.typography.titleMedium)
            Text(text = item.summary, style = MaterialTheme.typography.bodyMedium)
            Text(
                text = "${item.venue}  ·  ${item.published}",
                style = MaterialTheme.typography.labelSmall,
            )
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
