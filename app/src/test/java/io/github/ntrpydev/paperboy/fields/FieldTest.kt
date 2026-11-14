package io.github.ntrpydev.paperboy.fields

import io.github.ntrpydev.paperboy.feed.FeedItem
import io.github.ntrpydev.paperboy.feed.FeedJson
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class FieldTest {
    /** The enum of `field` in schema/feed-item.schema.json, which the unit tests carry as a resource. */
    private fun schemaFields(): List<String> {
        val text = javaClass.classLoader!!.getResource("feed-item.schema.json")!!.readText()
        return Json.parseToJsonElement(text).jsonObject.getValue("properties").jsonObject
            .getValue("field").jsonObject.getValue("enum").jsonArray.map { it.jsonPrimitive.content }
    }

    @Test fun `the app's fields are the schema's, in the same order`() {
        assertEquals(schemaFields(), Field.entries.map { it.wire })
    }

    @Test fun `every field has its label`() {
        assertEquals(
            listOf(
                "Physics", "Space", "Math", "Computer science", "Biology", "Neuroscience",
                "Medicine", "Chemistry", "Earth", "Engineering", "Social science",
            ),
            Field.entries.map { fieldLabel(it.wire) },
        )
    }

    @Test fun `a field this app does not know still parses and gets a label`() {
        val item = FeedJson.decodeFromString<FeedItem>(
            """{"id":"x","title":"T","hook":"H","summary":"S","field":"astronomy","tags":[],"status":"preprint",""" +
                """"venue":"arXiv","published":"2026-11-01","authors_short":"A","url":"https://example.org/x",""" +
                """"has_explainer":false,"significance":5,"added_at":"2026-11-12T00:00:00Z"}""",
        )
        assertEquals("astronomy", item.field)
        assertNull(Field.fromWire(item.field))
        assertEquals("Astronomy", fieldLabel(item.field))
    }
}
