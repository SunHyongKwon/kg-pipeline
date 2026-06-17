---
name: kg-query
description: "Query a knowledge graph (graph.json) to answer a question — find entry nodes by label, traverse the right way (BFS for neighborhoods, DFS for chains, PATH between two nodes, or a structural type filter), pull back only the relevant subgraph with its provenance, then verify precise facts against the source text. Works on both graphify graphs and custom property graphs. Use when asked to query/ask the KG, 'what does the graph say about X', how X and Y connect, or to answer from the knowledge graph instead of re-searching raw files."
---

# /kg-query

Answer a question from a knowledge graph instead of re-reading raw files. The graph is a search index over the corpus: find where to look, pull the relevant subgraph, then drop into the source text for the exact fact.

This is the read side companion to `/kg-design` (which builds the graph). It does **not** depend on the graphify package — it reads `graph.json` directly with the standard library, so it works on any KG: graphify output (`nodes`/`links`, `source`/`target`/`relation`) and custom property graphs (`nodes`/`edges`, `src`/`dst`/`rel`) alike.

## When to use
Use whenever a question can be answered from an existing `graph.json` — "what does the graph say about X", "how do X and Y connect", "which competitions are open", "what failure modes does technique Z warn about". Per the project rule, **query the graph before searching externally or re-deriving** (the graph is accumulated memory).

## Step 1 — locate the graph
The engine auto-searches `graph/graph.json`, `graphify-out/graph.json`, `data/kg/graph.json`, `graph.json` from the cwd. To target a specific one, pass the file or its folder as the first arg. If none is found, tell the user to build one with `/kg-design` first.

Get oriented first if you don't know the schema:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/kg-query/query_graph.py <graph-or-dir> --list-types
```

## Step 2 — pick the traversal mode from the question

YOU choose the mode; `--mode auto` is only a fallback heuristic. Match the question shape:

| Question shape | Mode | Why |
|---|---|---|
| "What is X connected to / related to / around X?" | `--mode bfs` | nearest neighbors, broad context (depth 2) |
| "How does X lead to / cause / flow into Y?" (a chain) | `--mode dfs` | follow one dependency chain deep (depth 6) |
| "How do X and Y connect?" (two named nodes) | `--mode path` | shortest path between the two entry nodes |
| "Which nodes are of type T / list all T" | `--type T` | structural filter, prints props (e.g. `--type Competition`) |
| "Define / explain X" | `--mode bfs --depth 1` | the node and its direct neighbors only |

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/kg-query/query_graph.py <graph-or-dir> "<question>" --mode bfs --budget 2000
```
Options: `--depth N` (override), `--budget N` (output token cap, default 2000), `--type T` (structural list).

## Step 3 — read the returned subgraph
The output is node labels (with `[type]` and a provenance locator), then the edges between them (`A --relation--> B (confidence)` with provenance). Read the relations and confidence tags, not just the nodes.

## Step 4 — verify precise facts against the source (do not stop at the graph)
The graph tells you *where* and *how things relate*; it is not the final evidence for a precise claim. For any exact wording, number, condition, or causal/INFERRED edge that matters:
- follow the node/edge `source_location` (or `source_file` / `source_url` / `prov`) **back into the original document and read the span**, then quote it;
- if `source_location` is only a file (or missing), say the provenance is coarse and flag it — that claim is weakly traceable;
- if the graph lacks the information, say so. **Do not invent nodes or edges.** Only then research the gap externally, and fold new findings back via `/kg-design` so the graph stays the source of truth.

## Step 5 — answer
Answer from the verified subgraph, citing the source span for specific facts. State which entry nodes you used and the mode, so the path to the answer is auditable. If a relationship you relied on turned out wrong or unsupported in the source, note it (and fix it via `/kg-design` Research loop: correct direction, downgrade confidence, or remove).

## Notes
- Traversal is undirected for reachability even on directed graphs, so BFS/PATH find connections regardless of arrow direction; edge labels still show the original direction (`A --rel--> B`).
- Entry-node matching is label-based (term overlap + whole-label match), tuned so short labels don't over-match as substrings. If matching misses, run `--list-types` or rephrase with terms that appear as node labels.
- Large subgraphs are ranked and cut to `--budget`; raise it for more context.
