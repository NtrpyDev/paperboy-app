package io.github.ntrpydev.paperboy.ui.feed

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.rank.Rating

/**
 * One paper in the feed. An explained card shows its hero image; a short card has none.
 * [heroUrl] is the absolute hero image address, or null for a short card. [rating] is the
 * reader's current rating of this paper; [onRate] is a tap on one of the rating buttons.
 */
@Composable
fun FeedCard(
    item: FeedItem,
    heroUrl: String?,
    rating: Rating?,
    onClick: () -> Unit,
    onRate: (Rating) -> Unit,
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
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                RatingButton("More like this", selected = rating == Rating.More) { onRate(Rating.More) }
                RatingButton("Less like this", selected = rating == Rating.Less) { onRate(Rating.Less) }
            }
        }
    }
}

/** A rating button: filled while selected, outlined otherwise. Tapping the selected one clears it. */
@Composable
private fun RatingButton(label: String, selected: Boolean, onClick: () -> Unit) {
    val modifier = Modifier.semantics {
        contentDescription = label
        this.selected = selected
        stateDescription = if (selected) "Selected" else "Not selected"
    }
    if (selected) {
        Button(onClick = onClick, modifier = modifier) { Text(label) }
    } else {
        OutlinedButton(onClick = onClick, modifier = modifier) { Text(label) }
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
