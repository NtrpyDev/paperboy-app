package io.github.ntrpydev.paperboy.feed

/**
 * Reads the feed from the content base: the head first, then chunks from the
 * newest backward.
 */
interface FeedSource {
    /** The newest chunk, as named by the head. */
    suspend fun loadNewest(): FeedPage

    /** The chunk before [page], or null when [page] is the oldest chunk. */
    suspend fun loadOlder(page: FeedPage): FeedPage?
}

/** The items of one chunk. */
data class FeedPage(
    val chunkNumber: Int,
    val items: List<FeedItem>,
)

/** Thrown by [FeedSource] when the feed cannot be read. */
class FeedUnavailableException(
    val reason: Reason,
    message: String,
    cause: Throwable? = null,
) : java.io.IOException(message, cause) {
    enum class Reason {
        /** The content base could not be reached. */
        Offline,

        /** The content base answered with an error status. */
        Server,

        /** A feed file arrived but did not match the wire format. */
        BadData,
    }
}
