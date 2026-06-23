---
name: get-content
description: "Collect external sources (web pages, articles, docs) into KG-ready markdown with provenance front-matter, so they can be fed to /kg-design or graphify. Given URLs it fetches them (fast urllib, FALLS BACK TO scrapling on 403/bot-wall/JS-only/empty body); given a TOPIC it can also SEARCH, follow related/꼬리 links (snowball), and sweep community/deep-dive sites to build the URL set first. Use when asked to collect/scrape/gather sources, find deep material on X, or add material to the knowledge graph's input folder."
---

# /get-content

Pull external material into the corpus as clean markdown with provenance, ready for `/kg-design` (build) or `graphify --update` (incremental). Front of the KG pipeline: **discover -> collect -> design/build -> query**.

## When to use
"Collect this", "scrape these URLs", "gather sources on X", "find deep material on X". Given URLs it fetches them; given a **topic** it first **searches, sweeps community/deep-dive sites, and follows 연관/꼬리 기사** to build the URL set. Output lands in `kg-input/sources/` (one markdown file per source).

## Discover & snowball (when you have a topic, not URLs)
Don't just fetch the first obvious hits — build a broad seed set, then follow trails:
1. **Search** several query variations (KO/EN, entity+keyword):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/get-content/fetch_source.py" --search "<query>" --n 15
   ```
   (DuckDuckGo HTML; prints `title <TAB> url <TAB> snippet`. No save.)
2. **Sweep BOTH source tiers — don't skip the second one:**
   - **권위(authoritative):** 뉴스·공식사이트·논문·정부/업계 리포트.
   - **딥다이브/커뮤니티(꼭 한 번씩):** Blind(teamblind.com)·브런치·디시·클리앙·뽐뿌·네이버 카페/블로그·퍼블리·폴인·아웃스탠딩·Reddit. 체험형 암묵지·예상질문·실전 흐름 같은 자료는 여기서만 나온다. `--search "site:<도메인> <query>"`로 겨냥.
3. **Fetch seeds, then follow 꼬리/연관 기사:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/get-content/fetch_source.py" "<url>" --out kg-input --emit-links
   ```
   `TRAIL LINKS:`(관련기사·원문·출처 우선)가 출력되면 **가치 있는 것만 골라**(전부 말고) 다시 수집. depth ~2, 총 개수 cap으로 수렴시킨다.
4. **Stop** when new fetches stop adding new material (주제 단위 중복 제거).

> Blind 등은 봇벽으로 댓글이 안 떨어질 수 있다 — 막히면 두드리지 말고 검색 스니펫/캐시나 같은 글을 인용한 블로그로 우회.

## The collection rule (scrapling is mandatory fallback)
For each URL, in order:
1. **Fast path** — bundled urllib fetcher. Good enough for most static pages.
2. **scrapling fallback (required)** — on 403/anti-bot, JS-only, or body shorter than `--min-chars`, auto-falls back to **scrapling** (Stealthy/Dynamic/PlayWright, version-agnostic). Not optional — it's why this skill exists for hard sites.
3. **Save with provenance** — front-matter (`source_url`, `captured_at`, `title`, `fetched_via`) + body. `source_url` becomes the node/edge `source_location` provenance once built (kg-design A7).

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/get-content/fetch_source.py" "<url>" --out kg-input
# force stealth path for a known-hard site:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/get-content/fetch_source.py" "<url>" --out kg-input --force-scrapling
```
Options: `--search "Q" [--n N]` (discover URLs, no save) · `--emit-links` (print 연관/꼬리 links after fetch) · `--out DIR` · `--title T` · `--min-chars N` (block-detection threshold, default 600) · `--force-scrapling`.

If it prints `scrapling 미설치`: `pip install "scrapling[fetchers]" && scrapling install` (the SessionStart hook also warns when missing).

For multiple URLs, loop. For a page you can read cleanly, you may use WebFetch and save yourself — but prefer `fetch_source.py` whenever blocking is even possible.

**Rate limits:** space out searches/fetches; if a community site bot-walls hard, take the search snippet/cache and move on rather than hammering (hammering resets cooldowns and blocks longer).

## After collecting — hand off to the graph
- **No `graphify-out/` yet** (first time): run `/kg-design` to design + build from the fresh `kg-input/`.
- **`graphify-out/` exists**: new material on an existing graph -> `graphify <path> --update`, then kg-design refine step (`refine_graph.py --apply`). Not a full redesign.

## Notes
- One file per source keeps provenance clean — each node traces to a single `source_url`.
- Don't collect into `graphify-out/`; raw sources stay in `kg-input/`.
- Respect the target site's terms; scrapling is for brittle anti-bot/JS on sources you're allowed to read, not for evading access controls.
