#!/usr/bin/env python3
"""kg-design refine: graphify 추출 결과를 정제해 클러스터 분리도를 높인다.

graphify 패키지는 건드리지 않는다. graphify-out/.graphify_extract.json 의 edges 를
정책에 따라 필터링한 뒤, graphify 기본 build/cluster/export 를 그대로 재사용해
graph.json / graph.html 을 다시 찍는다. modularity 게이트에 미달하면 정책 강도를
한 단계 올려 자동 재시도한다.

핵심 통찰: graphify 헤어볼의 주범은 'mentioned_in' 류의 약한 구조적(문서-개념 언급)
엣지다. 이런 엣지가 문서 노드를 거대 허브로 만들어 모든 개념을 한 덩어리로 끌어당긴다.
의미 관계(uses/requires/signals/warns_against...)만 남기면 클러스터가 또렷해진다.

사용:
  <graphify-python> refine_graph.py <graphify-out-dir> [--apply] [옵션]
  --apply              실제로 graph.json/graph.html 을 정제본으로 덮어쓴다(미지정 시 측정만).
  --target 0.5         목표 modularity (이 값 도달 시 더 안 자른다).
  --min-retention 0.6  노드 보존율 하한(이 밑으로 떨어지는 레벨은 채택 안 함).
  --max-level 3        최대 정책 강도.
  --strip RELS         추가로 제거할 relation(쉼표구분). 약한 관계 직접 지정.
  --keep RELS          기본 블랙리스트에서 제외할 relation(보존).
  --barnes-hut         생성된 HTML 물리엔진을 barnesHut 으로 치환(허브-스포크에 유리).
"""
import argparse
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import modularity

from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.export import to_json, to_html

# 약한 "구조적 언급" 관계 — 문서-개념 언급은 허브를 망치므로 기본 제거 대상
STRUCTURAL_RELATIONS = {
    "mentioned_in", "appears_in", "found_in", "referenced_in", "cited_in",
    "defined_in", "described_in", "discussed_in", "noted_in", "seen_in",
    "occurs_in", "located_in", "contained_in",
}


def policy_levels(strip_extra, keep, max_level):
    base = (STRUCTURAL_RELATIONS | set(strip_extra)) - set(keep)
    levels = [
        dict(drop_relations=base, drop_conf={"AMBIGUOUS"}, min_weight=0.0, degree_cap=None),
        dict(drop_relations=base, drop_conf={"AMBIGUOUS", "INFERRED"}, min_weight=0.5, degree_cap=None),
        dict(drop_relations=base, drop_conf={"AMBIGUOUS", "INFERRED"}, min_weight=0.6, degree_cap=20),
        dict(drop_relations=base, drop_conf={"AMBIGUOUS", "INFERRED"}, min_weight=0.7, degree_cap=12),
    ]
    return levels[: max_level + 1]


def edge_weight(e):
    for k in ("weight", "confidence_score"):
        if isinstance(e.get(k), (int, float)):
            return float(e[k])
    return 1.0


def filter_edges(edges, pol):
    kept = []
    for e in edges:
        if e.get("relation") in pol["drop_relations"]:
            continue
        if e.get("confidence") in pol["drop_conf"]:
            continue
        if edge_weight(e) < pol["min_weight"]:
            continue
        kept.append(e)
    cap = pol["degree_cap"]
    if cap:
        kept = apply_degree_cap(kept, cap)
    return kept


def apply_degree_cap(edges, cap):
    """degree 가 cap 을 넘는 노드는 인접 엣지 중 약한 것부터 제거한다."""
    edges = list(edges)
    while True:
        inc = defaultdict(list)
        for i, e in enumerate(edges):
            inc[e["source"]].append(i)
            inc[e["target"]].append(i)
        over = [(n, idxs) for n, idxs in inc.items() if len(idxs) > cap]
        if not over:
            break
        drop = set()
        for n, idxs in over:
            ranked = sorted(idxs, key=lambda i: edge_weight(edges[i]))
            for i in ranked[: len(idxs) - cap]:
                drop.add(i)
        edges = [e for i, e in enumerate(edges) if i not in drop]
    return edges


def drop_orphans(nodes, edges):
    used = set()
    for e in edges:
        used.add(e["source"])
        used.add(e["target"])
    return [n for n in nodes if n["id"] in used]


def measure(extraction):
    G = build_from_json(extraction)
    UG = G.to_undirected() if G.is_directed() else G
    comm = cluster(G)
    sets = [set(v) & set(UG.nodes) for v in comm.values()]
    sets = [s for s in sets if s]
    covered = set().union(*sets) if sets else set()
    for n in UG.nodes:
        if n not in covered:
            sets.append({n})
    try:
        m = modularity(UG, sets, weight="weight")
    except Exception:
        m = modularity(UG, sets)
    return G, comm, UG.number_of_nodes(), UG.number_of_edges(), len(comm), m


def patch_barnes_hut(html_path):
    html = Path(html_path).read_text()
    block = (
        "    solver: 'barnesHut',\n"
        "    barnesHut: {\n"
        "      gravitationalConstant: -8000,\n"
        "      centralGravity: 0.15,\n"
        "      springLength: 110,\n"
        "      springConstant: 0.05,\n"
        "      damping: 0.4,\n"
        "      avoidOverlap: 0.6\n"
        "    },"
    )
    new = re.sub(
        r"solver: 'forceAtlas2Based',\s*forceAtlas2Based: \{.*?\},",
        block,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if new != html:
        Path(html_path).write_text(new)
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--target", type=float, default=0.5)
    ap.add_argument("--min-retention", type=float, default=0.6)
    ap.add_argument("--max-level", type=int, default=3)
    ap.add_argument("--strip", default="")
    ap.add_argument("--keep", default="")
    ap.add_argument("--barnes-hut", action="store_true")
    args = ap.parse_args()

    out = Path(args.outdir)
    ex_path = out / ".graphify_extract.json"
    if not ex_path.exists():
        print(f"ERROR: {ex_path} 없음. graphify 를 먼저 돌려라.", file=sys.stderr)
        raise SystemExit(1)

    raw = json.loads(ex_path.read_text())
    nodes0 = raw.get("nodes", [])
    edges0 = raw.get("edges", [])
    n0 = len(nodes0)

    _, _, bn, be, bc, bm = measure(raw)
    print(f"BASELINE: nodes={bn} edges={be} density={be/max(bn,1):.2f} "
          f"communities={bc} modularity={bm:.3f}")

    levels = policy_levels(
        [s.strip() for s in args.strip.split(",") if s.strip()],
        [k.strip() for k in args.keep.split(",") if k.strip()],
        args.max_level,
    )

    best = None  # (modularity, level, extraction, stats)
    for lvl, pol in enumerate(levels):
        edges = filter_edges(edges0, pol)
        nodes = drop_orphans(nodes0, edges)
        ext = dict(raw)
        ext["nodes"] = nodes
        ext["edges"] = edges
        _, _, mn, me, mc, mm = measure(ext)
        retention = mn / max(n0, 1)
        flag = "ok" if retention >= args.min_retention else "LOW-RETENTION"
        print(f"  L{lvl}: edges {len(edges0)}->{me} density={me/max(mn,1):.2f} "
              f"nodes={mn}({retention:.0%}) comm={mc} modularity={mm:.3f} [{flag}]")
        if retention < args.min_retention:
            continue
        if best is None or mm > best[0]:
            best = (mm, lvl, ext, (mn, me, mc))
        if mm >= args.target:
            break

    if best is None:
        print("채택 가능한 레벨 없음(보존율 하한 위반). --min-retention 을 낮추거나 --keep 으로 관계를 보존해라.")
        raise SystemExit(2)

    bm2, lvl, ext, (mn, me, mc) = best
    print(f"\n선택: L{lvl}  modularity {bm:.3f} -> {bm2:.3f}  "
          f"density {be/max(bn,1):.2f} -> {me/max(mn,1):.2f}  nodes {bn} -> {mn}")

    if not args.apply:
        print("(측정만 함. 실제 반영하려면 --apply)")
        return

    raw_bak = out / ".graphify_extract.json.raw"
    if not raw_bak.exists():
        shutil.copy(ex_path, raw_bak)
    ex_path.write_text(json.dumps(ext, ensure_ascii=False))

    G = build_from_json(ext)
    comm = cluster(G)
    labels_path = out / ".graphify_labels.json"
    labels = None
    if labels_path.exists():
        try:
            labels = {int(k): v for k, v in json.loads(labels_path.read_text()).items()}
        except Exception:
            labels = None
    to_json(G, comm, str(out / "graph.json"))
    try:
        to_html(G, comm, str(out / "graph.html"), community_labels=labels)
        if args.barnes_hut:
            print("barnesHut 치환:", "성공" if patch_barnes_hut(out / "graph.html") else "패턴 불일치(스킵)")
    except ValueError as e:
        print(f"HTML 스킵: {e}")
    print(f"적용 완료. 원본 추출 백업: {raw_bak}")


if __name__ == "__main__":
    main()
