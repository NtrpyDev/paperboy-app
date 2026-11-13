package io.github.ntrpydev.paperboy.feed

import io.github.ntrpydev.paperboy.rank.item
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class WireFormatTest {
    private val entries = """
        {"v":1,"upgrades":{
          "arxiv-a":{"explainer":"papers/arxiv-a/","hero":{"path":"papers/arxiv-a/hero.webp","width":1200,"height":708},"readout":{"value":"0.96","unit":"angstroms","label":"Median error"},"explained_at":"2026-11-12T16:00:00Z"},
          "arxiv-b":{"explainer":"papers/arxiv-b/","hero":{"path":"papers/arxiv-b/hero.webp","width":1200,"height":708},"readout":null,"explained_at":"2026-11-12T16:00:00Z"},
          "arxiv-c":{"explainer":"papers/arxiv-c/","hero":{"path":"papers/arxiv-c/hero.webp","width":1200,"height":708},"explained_at":"2026-11-12T16:00:00Z"}
        }}
    """.trimIndent()

    private val upgrades = FeedJson.decodeFromString<Upgrades>(entries).upgrades
    private val own = Readout("42", label = "The item's own readout")
    private val short = item("arxiv-x").copy(readout = own)

    @Test fun `an explicit null, a missing key, and an object are three different readout changes`() {
        assertEquals(ReadoutChange.Replace(Readout("0.96", unit = "angstroms", label = "Median error")), upgrades.getValue("arxiv-a").readout)
        assertEquals(ReadoutChange.Remove, upgrades.getValue("arxiv-b").readout)
        assertEquals(ReadoutChange.Keep, upgrades.getValue("arxiv-c").readout)
    }

    @Test fun `a readout object in an upgrade replaces the item's readout`() {
        assertEquals(Readout("0.96", unit = "angstroms", label = "Median error"), short.upgradedWith(upgrades["arxiv-a"]).readout)
    }

    @Test fun `a null readout in an upgrade removes the item's readout`() {
        assertNull(short.upgradedWith(upgrades["arxiv-b"]).readout)
    }

    @Test fun `an upgrade without a readout key leaves the item's readout alone`() {
        assertEquals(own, short.upgradedWith(upgrades["arxiv-c"]).readout)
    }

    @Test fun `every upgrade makes the item an explained card with its plate`() {
        val upgraded = short.upgradedWith(upgrades["arxiv-c"])
        assertEquals(true, upgraded.hasExplainer)
        assertEquals("papers/arxiv-c/", upgraded.explainer)
        assertEquals("papers/arxiv-c/hero.webp", upgraded.hero?.path)
    }

    @Test fun `the plate's night still, kind, and scale are read, and older items without them still parse`() {
        val json = """{"path":"p/hero.webp","width":1200,"height":708,"night":{"path":"p/hero-night.webp","width":1200,"height":708},"kind":"illustration","to_scale":true}"""
        val hero = FeedJson.decodeFromString<Hero>(json)
        assertEquals(Still("p/hero-night.webp", 1200, 708), hero.night)
        assertEquals("illustration", hero.kind)
        assertEquals(true, hero.toScale)

        val old = FeedJson.decodeFromString<Hero>("""{"path":"p/hero.webp","width":1200,"height":675}""")
        assertNull(old.night)
        assertNull(old.kind)
        assertNull(old.toScale)
    }

    @Test fun `the open chunk's items carry the second voice and readouts`() {
        val chunk = FeedJson.decodeFromString<Chunk>(javaClass.classLoader!!.getResource("feed/v1/chunks/000009.json")!!.readText())
        val explained = chunk.items.single { it.id == "arxiv-2611.04821" }
        assertEquals("into a new state of matter", explained.hookTurn)
        assertEquals(Readout("1.2", exponent = -9, unit = "seconds", label = "How long the new state lasts"), explained.readout)
        assertNull(chunk.items.single { it.id == "arxiv-2611.01177" }.readout)
    }
}
