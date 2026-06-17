---
name: get-content
description: "Collect external sources (web pages, articles, docs) into KG-ready markdown with provenance front-matter, so they can be fed to /kg-design or graphify. Tries a fast standard fetch first and FALLS BACK TO scrapling when a site blocks it (403/bot-wall/JS-only/empty body). Use when asked to collect/scrape/gather sources, pull an article into the corpus, or add material to the knowledge graph's input folder."
---

# /get-content

Pull external material into the corpus as clean markdown with provenance, ready for `/kg-design` (build) or `graphify --update` (incremental). This is the front of the KG pipeline: collect -> design/build -> query.

## When to use
"Collect this", "scrape these URLs into the corpus", "add this article to the KG input", "gather sources on X". Output lands in `kg-input/sources/` (or `--out <dir>/sources/`) as one markdown file per source.

## The collection rule (scrapling is mandatory fallback)
For each URL, in order:
1. **Fast path** — try the bundled fetcher (standard-library urllib). Good enough for most static pages.
2. **scrapling fallback (required)** — if the site blocks it (403/anti-bot), serves JS-only content, or returns a body shorter than `--min-chars`, the fetcher automatically falls back to **scrapling** (Stealthy/Dynamic/PlayWright fetcher, version-agnostic) to get past bot walls and render JS. This fallback is not optional — it is why this skill exists for hard sites.
3. **Save with provenance** — write front-matter (`source_url`, `captured_at`, `title`, `fetched_via`) + body. The `source_url` becomes the node/edge `source_location` provenance once the graph is built (kg-design A7).

Run the collector (bundled, version-agnostic about scrapling's API):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/get-content/fetch_source.py" "<url>" --out kg-input
# force the stealth path for a known-hard site:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/get-content/fetch_source.py" "<url>" --out kg-input --force-scrapling
```
Options: `--out DIR` (root; saves under `DIR/sources/`), `--title T`, `--min-chars N` (block-detection threshold, default 600), `--force-scrapling`.

If it prints `scrapling 미설치`, install it once: `pip install "scrapling[fetchers]" && scrapling install` (the plugin's SessionStart hook also warns when it's missing).

For multiple URLs, loop over them. For a page you can read cleanly without blocking, you may instead use the WebFetch tool and save the result yourself — but prefer `fetch_source.py` whenever blocking is even possible, so the scrapling fallback is in play.

## After collecting — hand off to the graph
Tell the user the next step based on graph state:
- **No `graphify-out/` yet** (first time): run `/kg-design` to design + build the graph from the freshly collected `kg-input/`.
- **`graphify-out/` already exists**: this is new material on an existing graph -> `graphify <path> --update` then re-run the kg-design refine step (`refine_graph.py --apply`). Not a full redesign.

## Notes
- One file per source keeps provenance clean — each node later traces to a single `source_url`.
- Don't collect into the graph output folder; keep raw sources in `kg-input/` and let `graphify-out/` hold only built artifacts.
- Respect the target site's terms; scrapling is for getting past brittle anti-bot/JS rendering on sources you're allowed to read, not for evading access controls.
