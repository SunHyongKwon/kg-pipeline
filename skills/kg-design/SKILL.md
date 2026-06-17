---
name: kg-design
description: "Design and build a HIGH-QUALITY knowledge graph using the Stanford CS520 methodology: define use case + competency questions first, choose RDF vs property graph, design a schema with recognition conditions, plan entity resolution / quality / provenance, then hand off to graphify to build, and audit the result against the design. Use when asked to design or properly build a knowledge graph, model an ontology/schema, decide how to structure graph data, or judge whether a graph is any good."
trigger: /kg-design
---

# /kg-design

Design a knowledge graph the right way before you build it, build it (via graphify), then prove it is actually good.

This skill is the top-down, quality-first companion to `/graphify`. graphify mechanically extracts a concept graph from a folder (EXTRACTED/INFERRED/AMBIGUOUS edges + community detection). It does not decide *what* graph you need, *whether the nodes/edges carry defined meaning*, or *whether the result answers your questions*. That is what this skill adds.

The methodology is distilled from the Stanford CS520 (2021) Knowledge Graphs Seminar (20 sessions). Full reference with per-claim session citations (Sn):
`${CLAUDE_PLUGIN_ROOT}/skills/kg-design/references/cs520-methodology.md`
Session index: `${CLAUDE_PLUGIN_ROOT}/skills/kg-design/references/cs520-sessions-index.md`

## The one idea that matters

The value of a knowledge graph is **meaning, not graph structure**. A pile of nodes and edges with no recognition conditions and no inference logic is *data, not knowledge* (S6). So this skill never just "extracts a graph." It forces three phases in order, and the design + audit phases are non-negotiable:

```
A. DESIGN   (top-down)  - decide what graph, why, and how meaning is defined   -> KG-DESIGN.md
B. BUILD    (bottom-up) - extract/populate, hand off to graphify where it fits  -> graphify-out/
C. AUDIT    (judge)     - does it answer the competency questions? is it knowledge? -> KG-AUDIT.md
```

If the user only wants a quick exploratory graph of a folder, tell them `/graphify` alone is enough. Use `/kg-design` when the graph must reliably answer specific questions, carry a real schema, be maintained over time, or feed downstream reasoning.

## Usage

```
/kg-design                      # design a KG for the current folder, then build (graphify) + audit
/kg-design <path>               # same, on a specific path
/kg-design --design-only        # produce KG-DESIGN.md only; do not build
/kg-design --build              # design already exists; build + audit
/kg-design --audit              # audit an existing graphify-out/graph.json against KG-DESIGN.md
/kg-design "<domain/question>"  # no corpus yet: design from a described use case
/kg-design --research "<topic>" # continuous loop: query graph first, verify relations, fold findings, re-audit
```

If no path is given, use `.`. Do not block on a path.

---

## Phase A - DESIGN (always first; this is the part graphify skips)

Produce `KG-DESIGN.md` with the sections below. Interview the user briefly only for what you cannot infer from the corpus; default to proposing answers and asking for correction, not interrogating.

### A1. Use case & competency questions (S2, S9, S15)
Everything starts from the use case. Write the **competency questions (CQs)** the graph must answer to be a success - these define scope, granularity, evaluation, and the stopping point ("when is it enough").
- List 5-15 concrete CQs. Prefer "google-hard" questions (need joined/inferred facts), not single string lookups (S9).
- Identify the user persona(s) and interaction mode: push vs pull, known vs unknown question (S13). Precision and error-disclosure needs differ per persona (S2).
- A KG with no use case grows without bound and fails - this was a top reason the Semantic Web underdelivered (S2, S15).

### A2. Scope & sweet-spot check (S3, S7)
KGs pay off in a **sweet spot**: a simple schema (5-10 core types), huge record volume, connected by interesting relationships - then most effort goes to record linkage / loading / graph algorithms, not schema mapping (S7).
- If the data is mostly non-binary (ternary+) relations or value-heavy (e.g. time-series), a relational table may be the better home. Do not force everything into a graph (S3).

### A3. Data model decision - RDF vs Property Graph (S3, S4, S5)
Both are directed labeled graphs; the choice is driven by application + team, not raw superiority (S3).

| Factor | RDF (SPARQL) | Property Graph (Cypher/GQL) |
|---|---|---|
| Best when | publish to web, multi-source discovery/reuse | closed enterprise, fast traversal |
| Edge properties | needs reification | native |
| Global identifiers (IRI) | required | optional, schema-free |
| Interoperability | strong (dereferenceable URIs) | weak |
| Standard | W3C | GQL (ISO/IEC, 2019 vote) + SQL/PGQ |

Rule of thumb: web-publish/reuse/multi-source -> RDF; pre-schema-free traversal -> Property Graph. Property Graph -> RDF conversion is easier than the reverse (S3). graphify produces a property-graph-style concept graph (and can emit Neo4j Cypher); for RDF/triples plan a separate mapping.

### A4. Schema / ontology design (S5, S6, S15)
A taxonomy alone is not a schema. You need **recognition conditions** (how to decide an instance belongs to a class) and **inference logic** or it is data, not knowledge (S6).
- **Reuse existing vocabularies first** - schema.org, FOAF, SKOS, FIBO, BioPortal, existing data dictionaries. Hand-rolling vocabulary without searching is almost always a mistake (S5, S15). Import only what you need from large ontologies (MIREOT) (S15).
- **Core vs periphery**: keep the core small with few constraints (easy reuse/extension); push volatile detail to an auto-extended periphery (S15).
- Keep it simple; modularize incrementally. Over-constrained, oversized ontologies kill reuse and blow up deductive closure (S15, S20).
- Know the three uses of **reification** and apply the right one: (1) represent non-binary relations, (2) promote a relation for indexing/performance, (3) reify time (use t1,t2 variables instead of tense) (S3, S5, S14).
- Distinguish OWL (describe reality, top-down) from ShEx/SHACL (validate the data you have) (S6).

### A5. Extraction & ingestion plan (S7, S9, S10)
The graph is only as good as the data, ingestion, and QC behind it (S2). Pick per input type:
- **Structured data**: it is a data-integration problem with triples as the target. Specify schema mapping as Datalog rules; full automation is impossible (schema-level training data is scarce) - heuristics propose, a human who knows domain+IT verifies (S7).
- **Text**: entity extraction (NER) + relation extraction via LM / sequence labeling / rules; bootstrap labels with distant supervision, Hearst patterns, weak supervision (S9). Auto-extraction alone is not accurate (precision ~0.65, recall ~0.51) - human-in-the-loop review is mandatory (S9). Train on YOUR data; extractors do not transfer across genres (S19).
- **Images/multimodal**: scene graphs (objects+attributes+relations), shared entity codes across modalities (S10, S15).
- **Crowdsourcing**: multi-stage pipeline (qualification UI -> collection -> reviewer dashboard); design the dimension/relation vocabulary so a lay worker can tell categories apart (S10).
- Decide the automation mix explicitly: **fully automatic is a myth** - automation + manual + crowdsourcing + human-in-the-loop is reality (S1, S9, S19).

### A6. Entity resolution strategy (S7, S8)
Plan how records/mentions that denote the same real-world entity get merged (record linkage / NED).
- Two stages: **blocking** (cheap heuristics + indexing to cut candidates O(mn)->O(m+n)) then **matching** (precise compare; random forest + active learning) (S7, S8).
- Tail/unseen entities: rely on generalizable signals (type > KG-relation > entity embedding), not memorized embeddings (S8).
- Identifier strategy: prefer shared IRI / owl:sameAs / a unique key so sources link cleanly (S5, S7).

### A7. Quality, provenance, constraints (S2, S7, S12, S15)
- **Record provenance** for every fact - reuse succeeds or fails on this; embed provenance tracking into the system, not as an afterthought (S2, S15).
- Inject domain knowledge as **soft constraints/priors**, not only hard rules - shift the operational semantics, but stand on proven data-integration literature (ETL, TGD/EGD) (S7).
- Integrity constraints (subset, functional, symmetric, transitive) catch violations and can auto-complete missing edges (S12).
- High-precision first: in "0 -> 1 -> 1B", without the "1" (accuracy) all the scale "0"s are worthless (S15).

### A8. Maintenance / evolution plan (S15, S16, S17)
A KG is a software artifact, maintained forever (S16). Plan updates across **schema, data, and application (queries)** from the first use case (S15).
- Schema evolution: define invariants (no orphan classes, acyclic, etc.) and how changes propagate (S16).
- Sync external sources via Change Data Capture; use incremental view maintenance for large/fresh data; track external freshness with a difference graph - and do not assume the live web self-heals like a wiki (S16, S17).

### A9. Clustering axis - agree the hubs with the human BEFORE extraction

A pretty, well-separated graph is not luck - it comes from a **hub-and-spoke topology** (a few hub entity types, everything else hangs off them as typed satellites) and the **absence of weak "mention" edges** that glue everything into one hairball. graphify's raw extraction does neither by default, so decide the clustering axis up front, *with the human*:

- **Name the hub type(s)**: what is the natural center each cluster forms around? (e.g. `Competition`, `Paper`, `Session`, `Strategy`). Every other type should mostly attach to a hub, not cross-link freely. If no natural hub exists, the domain is an inherently dense mesh - say so; clustering will improve but never reach star-shaped.
- **Set the community axis**: along which dimension should clusters split? (by hub instance / by topic / by source / by time). This is the human's call - they usually have an intent ("I want it split this way").
- **Decide the relation policy**: which relations are *meaningful* (keep: `uses`, `requires`, `signals`, `warns_against`...) vs *weak structural mentions* (drop: `mentioned_in`, `appears_in`, `referenced_in`...). Weak mention edges are the #1 cause of hairballs - they turn document nodes into god-hubs.

**Ask the human these three** (hub type, split axis, relation keep/drop) with a short multiple-choice question rather than guessing - this is the human-in-the-loop the whole methodology insists on (S1, S9, S19). Record the answers in `KG-DESIGN.md`; Phase B feeds them to extraction and Phase B.5 enforces them.

**Output A**: write `graphify-out/KG-DESIGN.md` capturing A1-A9 (CQs verbatim - the audit needs them). Keep ALL graph artifacts in `graphify-out/`, not the repo root - `mkdir -p graphify-out` first if it doesn't exist yet. The repo root holds only raw source documents.

---

## Phase B - BUILD (hand off to graphify where it fits)

Decide the build path from the design:

- **Concept/corpus KG from unstructured files** (notes, papers, code, docs): graphify is ideal. Invoke it.
- **Curated/structured property graph or strict schema-first KG**: graphify's auto-extraction will not respect your schema. Build schema-first (apply the A4 schema, map structured sources with Datalog-style rules, do A6 entity resolution), then optionally `--neo4j` export. Say so explicitly rather than forcing graphify.

To invoke graphify, call the **Skill tool** with `skill: graphify` and args mapped from the design:

| Design decision | graphify args |
|---|---|
| Relationships are directional (most KGs) | `<path> --directed` |
| Need rich inferred edges / thorough | `--mode deep` |
| Property-graph / Neo4j target (A3) | `--neo4j` (or `--neo4j-push bolt://...`) |
| Gephi / yEd analysis | `--graphml` |
| Corpus will grow incrementally (A8) | `--update` |
| Agent-crawlable output | `--wiki` |

graphify writes, by default (no extra flags), into `graphify-out/`:
- `graph.html` - interactive visualization, opens in any browser, no server (the headline output; skipped only with `--no-viz`, or auto-skipped + warned above ~5,000 nodes -> use `--obsidian`/`--wiki` instead)
- `graph.json` - GraphRAG-ready graph, persists across sessions
- `GRAPH_REPORT.md` - plain-language audit trail

After build, note graphify's EXTRACTED vs INFERRED vs AMBIGUOUS edge counts from `GRAPH_REPORT.md` - the audit uses them.

When invoking graphify on unstructured files, **steer its extraction toward the A9 schema**: pass the agreed hub type(s) and the relation keep/drop policy into the extraction prompt (graphify Step 3 Part B runs semantic subagents - tell them which entity types are hubs and to prefer the meaningful relations, not blanket `mentioned_in`). This narrows the raw graph before any pruning.

**Fill provenance at extraction time (A7) - span level, not just file.** Also instruct the semantic subagents to populate `source_location` on every node and edge, not only `source_file`: record the *exact span* the fact came from - file + a locator such as the section heading, a line/char range, or a chunk id (e.g. `article_06.md#스캘핑-진입조건` or `02-guide.md:L210-238`). If one fact is supported by several places, record them all. This is the link that lets a query drop **from the graph back into the original text** to verify and quote a specific fact - with only `source_file`, provenance points vaguely at "somewhere in this document" and the answer loses the exact wording/number/nuance. A node whose claim cannot be traced to a span is data, not knowledge (S6); the **Provenance & freshness** audit step checks this. Note: graphify reliably fills `source_location` for code (AST positions) but tends to leave it null for prose unless explicitly told to - so this instruction matters most for document/article corpora (danta-king, knowledge_graph).

**Stable ASCII ids for non-ASCII (Korean etc.) corpora.** Do NOT let graphify auto-transliterate node ids for non-Latin text. Instruct the semantic subagents to assign each concept an explicit, stable, human-readable ASCII slug (단타 -> `concept_danta`, 스캘핑 -> `tech_scalping`, 손절 -> `risk_stoploss`) and to **reuse the exact same id for the same concept across every file**. If ids collapse to `_` or empty strings, one concept fragments into a different node per file, no hub forms, and clustering fails outright - a Korean build looks like dust without this. It is the single most important extraction rule for Korean corpora. The audit's cluster-separation step will surface the failure (low modularity, many singleton nodes) if it was skipped.

graphify limitation to flag: it is bottom-up concept extraction. It does not enforce recognition conditions, RDF triples, or your A4 schema. The audit (Phase C) is where you catch the gap.

---

## Phase B.5 - REFINE (clustering gate; the part that makes it *look* like a real KG)

graphify's raw output is usually a hairball: weak `mentioned_in` edges make document nodes into god-hubs and pull every concept into one blob. This phase enforces the A9 decisions on the built graph and **gates on cluster separation (modularity)** before you call the build done. It does NOT touch the graphify package - it filters `graphify-out/.graphify_extract.json` (backing up the raw to `.graphify_extract.json.raw`) and re-runs graphify's own build/cluster/export.

Run the refiner (use the same interpreter graphify used - `graphify-out/.graphify_python`):

```bash
PY=$(cat graphify-out/.graphify_python)
# 1) measure first (dry-run): see baseline modularity + what each prune level would do
$PY ${CLAUDE_PLUGIN_ROOT}/skills/kg-design/refine_graph.py graphify-out --target 0.5
# 2) apply the auto-selected level (re-writes graph.json + graph.html from the pruned extraction)
$PY ${CLAUDE_PLUGIN_ROOT}/skills/kg-design/refine_graph.py graphify-out --apply --target 0.5 --barnes-hut
```

What it does, in order, escalating prune strength only as needed to hit `--target` modularity while keeping node retention above `--min-retention` (default 0.6):
- drops the weak structural relations from A9 (default blacklist: `mentioned_in`, `appears_in`, `referenced_in`, ...; extend with `--strip`, protect a relation with `--keep`),
- drops `AMBIGUOUS` then `INFERRED` edges and low-weight edges,
- caps node degree (removes a god-hub's weakest edges first),
- removes orphaned nodes, re-clusters, and re-measures modularity,
- picks the lowest prune level that reaches the target (or the best one that respects retention), then re-renders.

Interpreting the result: **modularity ~0.4 = mushy, ~0.5 = clearly separated, ~0.6+ = crisp**. Density (edges/node) dropping toward ~1.5-2 is the hairball clearing. If the best achievable modularity is still low at acceptable retention, the domain is a genuine dense mesh (A9) - report that honestly rather than over-pruning into disconnected dust. The pruned edges are not deleted from source; the raw extraction is preserved in `.graphify_extract.json.raw` and the relation policy is recorded in KG-DESIGN.md, so this is reversible and auditable.

---

## Phase C - AUDIT (the part that makes it "good")

Write `graphify-out/KG-AUDIT.md` (keep it with the other artifacts, not in the repo root). A graph that builds is not a graph that is good.

1. **Competency-question coverage**: for each CQ in KG-DESIGN.md, attempt to answer it from the built graph (use `/graphify query "<CQ>"` for corpus graphs). Mark PASS / PARTIAL / FAIL. FAILs are the next iteration's work.
2. **Data-vs-knowledge test (S6)**: sample nodes/edges - do they have defined meaning / recognition conditions? If classes exist but nothing decides membership, it is data, not knowledge. Flag it.
3. **Edge honesty**: report EXTRACTED vs INFERRED ratio. A graph that is mostly INFERRED/AMBIGUOUS is a hypothesis, not knowledge.
4. **Cluster separation (from B.5)**: record final modularity and density. ~0.5+ modularity / ~1.5-2 density = the clusters are real and the A9 hub decision held. If still mushy at acceptable retention, note it as an inherent-mesh finding, not a failure to hide.
5. **Pitfall sweep**: walk the list below; flag every hit with the offending node/edge/section.
6. **Provenance & freshness**: is provenance recorded (A7)? Sample nodes/edges - is `source_location` filled at span level (file + section/line/chunk), or only `source_file`? Span-traceable claims are knowledge; "somewhere in this doc" claims are weak. Is there an update path (A8)?

Output the gaps as a prioritized next-iteration list. KG construction is iterative.

### Common pitfalls (sweep every one)
1. "Fully automatic" fantasy - no human-in-the-loop (S1, S9, S19).
2. Collected data but never defined meaning / recognition conditions (S6).
3. No use case -> unbounded, purposeless graph (S2, S15).
4. Assuming a node-edge picture is the right UI for millions of instances (S13).
5. Forcing non-binary / value-heavy data into a graph (S3).
6. Querying without transitive subclass/qualifier (p31/p279*) - wrong counts (S6).
7. Naive union of sources -> term-mismatch misses or homonym clashes; make context explicit (S20).
8. Single master format for multimodal data -> collapses; store raw, build graph at runtime (S17).
9. Oversized, over-constrained ontology; not reusing existing vocabulary (S15, S20).
10. No provenance recorded (S2, S15).
11. Scale without precision (S15).
12. Reusing an extractor across genres without retraining (S19).
13. No evolution plan across schema/data/application (S15, S16).
14. Underestimating community/organizational buy-in for the ontology (S6).
15. Ignoring distribution/parallelization of computational complexity (S11).
16. Expecting a neural net alone to give explainability/causality (S18).
17. Federated design without knowing which source to route to (S4).
18. Trusting only popularity-biased eval sets - slice by tail (S8).
19. Assuming a live-web source self-heals like a wiki - track changes with a difference graph (S17).
20. Believing meta-programming adds expressivity (it only cuts authoring; verify the generated logic scales) (S12, S20).

---

## Research loop (continuous mode — graph as living memory)

Use this whenever you research or work in a folder that already has `graphify-out/graph.json`. The graph IS the accumulated memory; consult and correct it on every pass instead of treating it as a one-shot snapshot (S16 maintenance/evolution).

1. **Query first, before searching externally or re-deriving.** Hit the existing graph: `graphify query "<topic>"`, `graphify path "A" "B"` (how two things connect), `graphify explain "X"`. Do not re-research what the graph already answers.
2. **Verify the relationships it returns** — especially causal / dependency / INFERRED edges. For each relationship that matters to the task, **follow its `source_location` back into the original document and read the span** - do not answer from the graph alone for any precise fact (exact wording, number, condition). The graph is the index; the source text is the evidence. Causality is directional: confirm `source -> target` is the actual cause/prerequisite, not mere correlation or a reversed arrow. Wrong or unsupported edges get fixed, not left: correct the direction, downgrade confidence (EXTRACTED -> INFERRED/AMBIGUOUS), or remove. If `source_location` is missing so the claim can't be traced, that itself is a defect to flag. This is the data-vs-knowledge discipline (S6) applied continuously.
3. **Research only the gap** — what the graph lacks, or what step 2 flagged as wrong/uncertain.
4. **Fold new content back**: add new material to the corpus and run `graphify <path> --update` (incremental re-extract). It re-extracts only changed files, merges them into the existing `graph.json`, and **auto-prunes nodes whose source file was deleted** (ghost nodes). Keep the backbone anchor ids stable so the schema does not drift. Record useful Q&A with `graphify save-result`.
4b. **Re-run REFINE after every `--update`** (this is the easy-to-forget step): `--update` merges raw new extraction onto your already-pruned graph, so the *new* slice arrives with weak `mentioned_in`-style edges re-attached even though the old slice stays clean. Re-run `refine_graph.py graphify-out --apply` to re-enforce the A9 policy on the new edges and re-check the modularity gate. The refine is idempotent on already-clean edges, so the old clusters are preserved and only the new noise is removed. (Note: `.graphify_extract.json.raw` holds the *first* pre-refine snapshot, not a per-update history — it is a reset point, not a full undo log.)
4c. **Handle term / schema changes deliberately — do NOT blanket-delete old nodes.** When a method or term is renamed or merged, choose per case: (a) *same concept, new name* -> keep the anchor id, update the `label` only (edges survive); (b) *two concepts collapse into one* -> entity-resolution merge onto one stable id, repoint edges, drop the duplicate; (c) *concept genuinely retired* -> remove it, or mark deprecated if history matters. `--update` only auto-removes nodes from *deleted files*; rename/merge of still-present content is a human-in-the-loop edit here, governed by the A8 schema-evolution invariants (no orphan classes, stable backbone ids).
5. **Re-audit the changed region** (Phase C): CQ coverage, edge honesty, final modularity/density (did the new content keep the clusters crisp?), and the relationship/node corrections from steps 2 and 4c. Append to `KG-AUDIT.md` with a dated note so the graph gets measurably more correct each pass.

The point: search starts at the graph, every traversed relationship is checked for correctness, new content is folded in *and re-refined*, and renames/merges are done as deliberate id-stable edits — so the graph converges toward a verified causal/relational map rather than drifting or re-growing the hairball.

## When you finish

Report, in order: the design decisions made (data model, schema approach, automation mix), what was built and how, the competency-question pass/fail table, and the prioritized gaps. Point the user at the three deliverables, all inside `graphify-out/` - `graphify-out/KG-DESIGN.md`, `graphify-out/graph.html` (open in a browser to see the graph), and `graphify-out/KG-AUDIT.md`. To answer questions from the built graph afterward, use `/kg-query`. For depth on any decision, cite the relevant session and reference `references/cs520-methodology.md`.
