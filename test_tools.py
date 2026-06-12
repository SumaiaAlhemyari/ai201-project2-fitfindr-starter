# tests/test_tools.py
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# ── search_listings tests ───────────────────────────────────────────────────────
def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


# ── suggest_outfit tests ───────────────────────────────────────────────────────
# These call the Groq LLM, so they assert on reliable structural properties
# (type, non-empty, branch behavior) rather than exact wording.

# A sample new item reused across the outfit tests.
SAMPLE_ITEM = {
    "title": "Vintage Band Graphic Tee",
    "category": "tops",
    "colors": ["black", "white"],
    "style_tags": ["vintage", "graphic", "streetwear"],
    "price": 24.0,
    "platform": "Depop",
}

def test_suggest_outfit_returns_nonempty_string():
    # With a populated wardrobe, the result must be a non-empty string.
    result = suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())
    assert isinstance(result, str)
    assert result.strip() != ""

def test_suggest_outfit_empty_wardrobe_still_returns_advice():
    # An empty wardrobe must NOT raise or return "" — it falls back to advice.
    result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())
    assert isinstance(result, str)
    assert result.strip() != ""


# ── create_fit_card tests ───────────────────────────────────────────────────────
def test_create_fit_card_returns_caption():
    # A real outfit should produce a non-empty caption string.
    outfit = "Pair the tee with baggy jeans and chunky white sneakers."
    result = create_fit_card(outfit, SAMPLE_ITEM)
    assert isinstance(result, str)
    assert result.strip() != ""

def test_create_fit_card_empty_outfit_returns_error_string():
    # An empty/whitespace outfit must return a descriptive error STRING,
    # not raise an exception and not return "".
    result = create_fit_card("   ", SAMPLE_ITEM)
    assert isinstance(result, str)
    assert result.strip() != ""

    