"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # ── Part 1: Load every listing from the dataset ────────────────────────────
    # load_listings() reads data/listings.json and returns a list of dicts.
    listings = load_listings()

    # ── Part 2: Break the user's description into lowercase keywords ───────────
    # We lowercase so matching is case-insensitive, and split on spaces so each
    # word ("vintage", "graphic", "tee") can be matched independently.
    keywords = description.lower().split()

    # This list will hold (score, listing) pairs for listings that pass filtering.
    scored = []

    # ── Part 3: Loop over each listing and apply filters + scoring ─────────────
    for listing in listings:

        # ── Part 3a: Price filter ──────────────────────────────────────────────
        # If a max_price was given and this listing costs more, skip it.
        if max_price is not None and listing["price"] > max_price:
            continue

        # ── Part 3b: Size filter (case-insensitive substring match) ────────────
        # "M" should match a listing size like "S/M", so we check that the
        # requested size appears anywhere inside the listing's size string.
        if size is not None and size.lower() not in listing["size"].lower():
            continue

        # ── Part 3c: Score by keyword overlap ──────────────────────────────────
        # Combine the fields worth searching (title, description, style_tags)
        # into one lowercase string, then count how many keywords appear in it.
        searchable_text = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()

        score = 0
        for word in keywords:
            if word in searchable_text:
                score += 1

        # ── Part 3d: Drop listings with no keyword matches ─────────────────────
        # A score of 0 means nothing in the description matched, so it's not
        # relevant — only keep listings that matched at least one keyword.
        if score > 0:
            scored.append((score, listing))

    # ── Part 4: Sort by score, highest (best match) first ──────────────────────
    # reverse=True puts the largest score at the front of the list.
    scored.sort(key=lambda pair: pair[0], reverse=True)

    # ── Part 5: Return just the listing dicts (drop the score) ─────────────────
    # If nothing matched, `scored` is empty and this returns [] — no exception.
    # The `_` discards the score; we only return the listing dicts themselves.
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # ── Part 1: Pull the details of the new item into a readable string ────────
    # We describe the thrifted item the same way in both branches, so the LLM
    # always knows what it's styling. .get() avoids KeyErrors on missing fields.
    item_desc = (
        f"{new_item.get('title', 'this item')} "
        f"(category: {new_item.get('category', 'unknown')}, "
        f"colors: {', '.join(new_item.get('colors', []))}, "
        f"style: {', '.join(new_item.get('style_tags', []))})"
    )

    # ── Part 2: Get the wardrobe items list, defaulting to empty if missing ────
    # wardrobe is a dict like {"items": [...]}. Using .get with [] means a
    # malformed or missing wardrobe is treated the same as an empty one.
    items = wardrobe.get("items", [])

    # ── Part 3: Branch — empty wardrobe vs. populated wardrobe ─────────────────
    if not items:
        # ── Part 3a: EMPTY wardrobe → ask for general styling advice ──────────
        # The user has no closet entered, so we can't reference specific pieces.
        # Instead we ask the LLM for general ideas: what to pair it with and the
        # vibe it suits.
        prompt = (
            f"A shopper is considering this secondhand item: {item_desc}.\n"
            f"They haven't entered their wardrobe yet, so give general styling "
            f"advice: suggest 1-2 outfit directions describing the kinds of "
            f"pieces (tops, bottoms, shoes) that pair well and the overall vibe. "
            f"Keep it short, friendly, and concrete."
        )
    else:
        # ── Part 3b: POPULATED wardrobe → format the closet into the prompt ───
        # Turn each wardrobe item into one readable line so the LLM can refer to
        # specific pieces by name when building outfits.
        wardrobe_lines = []
        for w in items:
            line = f"- {w.get('name', 'item')} ({w.get('category', '')})"
            wardrobe_lines.append(line)
        wardrobe_text = "\n".join(wardrobe_lines)

        # Ask the LLM for specific combinations using the new item + named pieces.
        prompt = (
            f"A shopper is considering this secondhand item: {item_desc}.\n\n"
            f"Here is their existing wardrobe:\n{wardrobe_text}\n\n"
            f"Suggest 1-2 complete outfits that combine the new item with "
            f"specific pieces from their wardrobe (refer to the pieces by name). "
            f"Keep it short, friendly, and concrete."
        )

    # ── Part 4: Call the Groq LLM with the prompt we built ─────────────────────
    # _get_groq_client() reads GROQ_API_KEY from .env and returns a client.
    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",          # capable general chat model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,                            # some variety, still on-topic
    )

    # ── Part 5: Extract and return the text as a non-empty string ──────────────
    # .strip() removes stray whitespace; we never return an empty string because
    # both branches above always send a valid prompt to the LLM.
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # ── Part 1: Guard against an empty or whitespace-only outfit ───────────────
    # If suggest_outfit() failed upstream, `outfit` may be "" or just spaces.
    # We return a descriptive error STRING (not an exception) so the agent and
    # UI can show it gracefully.
    if not outfit or not outfit.strip():
        return "Can't create a fit card without an outfit suggestion to describe."

    # ── Part 2: Pull the item details we want mentioned in the caption ─────────
    # The caption should name the item, its price, and the platform once each,
    # so we extract them up front. .get() keeps it safe if a field is missing.
    title = new_item.get("title", "this piece")
    price = new_item.get("price", "?")
    platform = new_item.get("platform", "secondhand")

    # ── Part 3: Build the prompt with the item details and the outfit ──────────
    # We give the LLM the facts to weave in plus clear style rules so the result
    # reads like a real OOTD post, not a product listing.
    prompt = (
        f"Write a short, casual Instagram/TikTok caption for a thrifted outfit.\n\n"
        f"Item: {title}\n"
        f"Price: ${price}\n"
        f"Found on: {platform}\n"
        f"Outfit: {outfit}\n\n"
        f"Rules:\n"
        f"- 2 to 4 sentences, casual and authentic (a real OOTD post).\n"
        f"- Mention the item name, the price, and the platform naturally, once each.\n"
        f"- Capture the outfit's vibe in specific terms.\n"
        f"- No hashtags-only spam; sound like a person, not an ad."
    )

    # ── Part 4: Call the Groq LLM at a HIGHER temperature for variety ──────────
    # Higher temperature (0.9) makes the caption sound different each time, as the
    # spec asks. _get_groq_client() reads GROQ_API_KEY from .env.
    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )

    # ── Part 5: Return the caption text, trimmed of stray whitespace ───────────
    return response.choices[0].message.content.strip()
