# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Search the mock listings dataset for items matching the description, optional size, and optional price ceiling.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing what the user is looking for (e.g., "vintage graphic tee").
- `size` (str): Size string to filter by, or None to skip size filtering. Matching is case-insensitive (e.g., "M" matches "S/M").
- `max_price` (float): Maximum price (inclusive), or None to skip price filtering.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of matching listing dicts, sorted by relevance (best match first). 
        
**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
Returns an empty list if nothing matches — does NOT raise an exception.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dict (the item the user is considering buying).
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty — handle this gracefully.

**What it returns:**
<!-- Describe the return value -->
A non-empty string with outfit suggestions.
        

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, offer general styling advice for the item rather than raising an exception or returning an empty string.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generate a short, shareable outfit caption for the thrifted find.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string from suggest_outfit().
- `new_item` (dict): The listing dict for the thrifted item.

**What it returns:**
<!-- Describe the return value -->
A 2–4 sentence string usable as an Instagram/TikTok caption.
        
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is empty or missing, return a descriptive error message string — do NOT raise an exception.
        
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The planning loop runs as a fixed sequence inside `run_agent()`, where each step
depends on the output of the previous one and the loop short-circuits on failure:

1. **Parse the query.** Extract `description`, `size`, and `max_price` from the
   natural-language query and store them in `session["parsed"]`.
2. **Call `search_listings()`** with the parsed parameters. This is always first
   because the other two tools need a concrete item to work with.
3. **Branch on the search result.** If `search_listings()` returns an empty list,
   the agent sets `session["error"]` to a helpful message and stops — it does NOT
   call `suggest_outfit()` or `create_fit_card()` with empty input.
4. **Select the top item.** If there are results, take the first
   (highest-relevance) listing as `session["selected_item"]`.
5. **Call `suggest_outfit()`** with the selected item and the wardrobe — a fit
   card needs an outfit to describe, so this comes before the card.
6. **Call `create_fit_card()`** with the outfit string and selected item.
7. **Done.** The loop finishes once `fit_card` is set (or once `error` was set in
   step 3), and it returns the session dict.

The condition that changes behavior is the search result: empty → error path,
non-empty → continue down the tool chain.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent stores and accesses state within a session with _new_session().
The tracked data are:
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
The run_agent function is paassing state between tools via a session dict using function _new_session().

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Returns an empty list if nothing matches — does NOT raise an exception | 
| suggest_outfit | Wardrobe is empty | If the wardrobe is empty, offer general styling advice for the item rather than raising an exception or returning an empty string |
| create_fit_card | Outfit input is missing or incomplete | If outfit is empty or missing, return a descriptive error message string — do NOT raise an exception |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
                         User query  +  wardrobe choice
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │   run_agent()  — PLANNING LOOP      │
                    │                                     │
   _new_session() ──► session dict  (shared STATE)        │
                    │   { query, parsed, search_results,  │
                    │     selected_item, wardrobe,        │
                    │     outfit_suggestion, fit_card,    │
                    │     error }                         │
                    │                                     │
                    │   1. parse query                    │
                    │        │                            │
                    │        ▼                            │
                    │   2. search_listings(desc,size,$)   │
                    │        │                            │
                    │   results empty? ──── yes ──► set session["error"]
                    │        │ no                    └──► return early (STOP)
                    │        ▼                            │
                    │   3. selected_item = results[0]     │
                    │        │                            │
                    │        ▼                            │
                    │   4. suggest_outfit(item, wardrobe) │──► LLM (Groq)
                    │        │                            │
                    │        ▼                            │
                    │   5. create_fit_card(outfit, item)  │──► LLM (Groq)
                    │        │                            │
                    └────────┼────────────────────────────┘
                             ▼
                        return session  ──►  UI panels:
                        (listing) (outfit) (fit card)

  Data: search_listings() reads data/listings.json via load_listings().
  State: every step reads from / writes to the one session dict.
  Error path: only search_listings branches off (empty results → stop).
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

     1/ For search_listings, I'll give Claude the Tool 1 block from planning.md (inputs, return value, failure mode) and ask it to implement the function using load_listings() from the data loader. Before running it, I'll check that the generated code filters by all three parameters (description, size, max_price) and handles the empty-results case by returning []. Then I'll test it with 3 queries: a match, a price-filtered query, and a no-results query.
     2/ For suggest_outfit, I'll give Claude the Tool 2 block from planning.md (inputs, return value, failure mode) and ask it to implement the function using the Groq LLM via _get_groq_client() — NOT load_listings(). Before running it, I'll check that the generated code branches on an empty wardrobe (general styling advice) vs. a populated one (specific combinations using named wardrobe pieces) and always returns a non-empty string. Then I'll test it with an example wardrobe and an empty wardrobe.
     3/ For create_fit_card, I'll give Claude the Tool 3 block from planning.md (inputs, return value, failure mode) and ask it to implement the function using the Groq LLM via _get_groq_client(). Before running it, I'll check that the generated code guards against an empty/whitespace outfit string (returns a descriptive error, no exception) and produces a varied 2–4 sentence caption that mentions the item name, price, and platform. Then I'll test it with a real outfit string and an empty one.

**Milestone 3 — Individual tool implementations:**
I'll implement and test each tool in tools.py in isolation, in order (search_listings, then suggest_outfit, then create_fit_card), using the per-tool prompts above. Each tool is verified on its own (running it directly with sample inputs) before being wired into the agent, so I know any later bug is in the loop, not the tool.

**Milestone 4 — Planning loop and state management:**
I'll give Claude the Planning Loop, State Management, and Architecture sections of this planning.md and ask it to implement run_agent() in agent.py: initialize state with _new_session(), parse the query, call the three tools in sequence, thread results through the session dict, and short-circuit to session["error"] when search_listings() returns []. I'll verify against agent.py's CLI test (the happy path prints a listing/outfit/fit card; the no-results query prints an error message), then connect it to the UI by implementing handle_query() in app.py.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent initializes the session with `_new_session()`, then parses the query.
It extracts `description="vintage graphic tee"`, `size=None`, `max_price=30.0` and
stores them in `session["parsed"]`. (The "baggy jeans and chunky sneakers" detail
isn't a search filter — it's wardrobe/style context used later for styling.)

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
The agent calls `search_listings("vintage graphic tee", size=None, max_price=30.0)`.
It returns a non-empty list of matching listing dicts sorted by relevance, stored
in `session["search_results"]`. The agent picks the top result as
`session["selected_item"]` — e.g. a "Vintage Band Graphic Tee, $24, Depop".

**Step 3:**
<!-- Continue until the full interaction is complete -->
The agent calls `suggest_outfit(selected_item, wardrobe)`. Using the example
wardrobe, the LLM returns 1–2 outfit ideas pairing the tee with the user's pieces
(e.g. baggy jeans + chunky sneakers), stored in `session["outfit_suggestion"]`.

**Step 4:**
The agent calls `create_fit_card(outfit_suggestion, selected_item)`. The LLM
returns a 2–4 sentence shareable caption mentioning the item, its price, and
platform, stored in `session["fit_card"]`. The agent returns the session.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The UI shows three panels: (1) the top listing found (title, price, platform,
condition, etc.), (2) the outfit idea describing how to style the tee with their
wardrobe, and (3) the fit card — a ready-to-post OOTD caption. If the query had
returned no results (e.g. the "designer ballgown size XXS under $5" test), the
user would instead see the error message in the first panel and the other two
panels empty.
