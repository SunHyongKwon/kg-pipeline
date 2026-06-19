#!/usr/bin/env python3
"""build_schema_graph — kg-design 의 schema-first 빌드 엔진(번들).

graphify(bottom-up 자동추출)가 큐레이션형/한글/감사필요 KG 에서 만드는 헤어볼을 피하기 위한,
스키마-우선 빌드의 결정론적 후반부. LM 서브에이전트가 KG-DESIGN.md 의 스키마·canonical id
규칙에 맞춰 문서별로 뽑은 추출 JSON 을 받아, 병합·엔티티해소·클러스터링해서
graphify 호환 graph.json(nodes/links) + graph.html + 통계를 만든다. kg-query 가 그대로 읽는다.

역할 분담:
  - 의미(어떤 회사가 무엇을): LM 서브에이전트 추출(스키마·관계정책·canonical id 강제) → extractions
  - 구조(병합·중복정리·modularity·직렬화): 이 스크립트(결정론적·재현가능)

입력(extractions): 추출 객체의 리스트 JSON 파일 1개, 또는 그런 *.json 들이 든 디렉토리.
  추출 객체 = {source_file?, source_url?,
               nodes:[{id,type,label,props?,source_url?,source_location?}],
               edges:[{source,target,relation,confidence?,source_url?,source_location?,evidence?}]}

사용:
  python3 build_schema_graph.py extractions.json --out graphify-out
  python3 build_schema_graph.py extractions_dir/ --out graphify-out --aliases aliases.json --labels labels.json
옵션:
  --aliases F  {중복id: canonical_id}  엔티티해소(동일 실세계 엔티티 병합)
  --labels  F  {node_id: 보정라벨}     공유 노드에 특정 벤더명이 굳는 과잉귀속 방지
  --strip   R  추가로 제거할 약한 관계명(쉼표구분). 기본 blacklist 에 더한다.
  --target  T  목표 modularity(보고용 판정 임계, 기본 0.5)
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities, modularity

# A9 관계 정책: 약한 구조적 mention 은 제거(헤어볼/ god-hub 방지)
DROP_RELATIONS = {
    "mentioned_in", "appears_in", "referenced_in", "related_to",
    "associated_with", "mentions", "cited_in", "linked_to", "see_also", "co_occurs_with",
}
CONF_RANK = {"EXTRACTED": 2, "INFERRED": 1, "AMBIGUOUS": 0, None: 0, "": 0}

PALETTE = {
    "Company": "#e6194B", "AIInitiative": "#4363d8", "Technology": "#3cb44b",
    "Partner": "#f58231", "OrgUnit": "#911eb4", "Person": "#42d4f4",
    "Investment": "#f032e6", "TherapeuticArea": "#bfef45",
}
_EXTRA = ["#469990", "#9A6324", "#800000", "#808000", "#000075", "#a9a9a9"]


def load_extractions(path):
    p = Path(path)
    if p.is_dir():
        docs = []
        for f in sorted(p.glob("*.json")):
            raw = json.loads(f.read_text(encoding="utf-8"))
            docs.extend(raw if isinstance(raw, list) else [raw])
        return docs
    raw = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("extractions") or raw.get("docs") or [raw]
    return raw


def merge(extractions, aliases, labels, drop):
    def rid(i):
        return aliases.get(i, i)
    nodes, node_prov, type_conflicts = {}, defaultdict(list), []
    for doc in extractions:
        surl, sfile = doc.get("source_url", ""), doc.get("source_file", "")
        for n in doc.get("nodes", []):
            nid = rid(n.get("id"))
            if not nid:
                continue
            loc = n.get("source_location") or sfile or surl
            if nid not in nodes:
                nodes[nid] = {
                    "id": nid, "label": labels.get(nid) or n.get("label") or nid,
                    "type": n.get("type") or "Unknown", "props": dict(n.get("props") or {}),
                    "source_url": n.get("source_url") or surl, "source_location": loc,
                }
            else:
                ex = nodes[nid]
                if n.get("type") and ex["type"] not in (n.get("type"), "Unknown"):
                    type_conflicts.append((nid, ex["type"], n.get("type")))
                for k, v in (n.get("props") or {}).items():
                    ex["props"].setdefault(k, v)
            if loc and loc not in node_prov[nid]:
                node_prov[nid].append(loc)

    edges, edge_prov, edge_evid = {}, defaultdict(list), defaultdict(list)
    dropped_weak, dangling = 0, []
    for doc in extractions:
        surl, sfile = doc.get("source_url", ""), doc.get("source_file", "")
        for e in doc.get("edges", []):
            u, v = rid(e.get("source")), rid(e.get("target"))
            rel = (e.get("relation") or "").strip()
            if not u or not v or not rel:
                continue
            if rel in drop:
                dropped_weak += 1
                continue
            if u not in nodes or v not in nodes:
                dangling.append((u, rel, v))
                continue
            key = (u, v, rel)
            conf = e.get("confidence") or "EXTRACTED"
            loc = e.get("source_location") or sfile or surl
            if key not in edges:
                edges[key] = {"source": u, "target": v, "relation": rel, "confidence": conf,
                              "weight": 1, "source_url": e.get("source_url") or surl, "source_location": loc}
            else:
                ex = edges[key]
                ex["weight"] += 1
                if CONF_RANK.get(conf, 0) > CONF_RANK.get(ex["confidence"], 0):
                    ex["confidence"] = conf
            if loc and loc not in edge_prov[key]:
                edge_prov[key].append(loc)
            ev = e.get("evidence")
            if ev and ev not in edge_evid[key]:
                edge_evid[key].append(ev)

    for nid, locs in node_prov.items():
        nodes[nid]["prov"] = locs
    edge_list = []
    for key, ed in edges.items():
        ed["prov"] = edge_prov[key]
        if edge_evid[key]:
            ed["evidence"] = edge_evid[key]
        edge_list.append(ed)
    return nodes, edge_list, {"type_conflicts": type_conflicts, "dropped_weak": dropped_weak, "dangling": dangling}


def cluster(nodes, edges):
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for e in edges:
        if G.has_edge(e["source"], e["target"]):
            G[e["source"]][e["target"]]["weight"] += e.get("weight", 1)
        else:
            G.add_edge(e["source"], e["target"], weight=e.get("weight", 1))
    sub = G.subgraph([n for n in G if G.degree(n) > 0]).copy()
    comms, mod = [], 0.0
    if sub.number_of_edges() > 0:
        comms = list(greedy_modularity_communities(sub, weight="weight"))
        mod = modularity(sub, comms, weight="weight")
    cid, nxt = {}, 0
    for i, c in enumerate(comms):
        for n in c:
            cid[n] = i
        nxt = i + 1
    for n in nodes:
        if n not in cid:
            cid[n] = nxt
            nxt += 1
    for nid, n in nodes.items():
        n["community"] = cid[nid]
    return mod, (len(edges) / len(nodes) if nodes else 0.0), nxt


def color_for(t, seen={}):
    if t in PALETTE:
        return PALETTE[t]
    if t not in seen:
        seen[t] = _EXTRA[len(seen) % len(_EXTRA)]
    return seen[t]


def write_html(nodes, edges, stats, out_html):
    deg = defaultdict(int)
    for e in edges:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    vis_nodes = []
    for nid, n in nodes.items():
        props = " | ".join(f"{k}: {v}" for k, v in (n.get("props") or {}).items())
        prov = "<br>".join(n.get("prov", [])[:4])
        title = f"<b>{n['label']}</b> [{n['type']}]" + (f"<br>{props}" if props else "") + (f"<br><i>{prov}</i>" if prov else "")
        vis_nodes.append({"id": nid, "label": n["label"], "group": n["type"], "title": title,
                          "value": 6 + deg.get(nid, 0) * 3, "color": color_for(n["type"])})
    vis_edges = [{"from": e["source"], "to": e["target"], "label": e["relation"], "arrows": "to",
                  "dashes": e.get("confidence") == "INFERRED",
                  "title": f"{e['relation']} ({e.get('confidence')}) w={e.get('weight')}",
                  "font": {"size": 9, "align": "middle"}} for e in edges]
    types = sorted({n["type"] for n in nodes.values()})
    legend = "".join(f'<span style="display:inline-block;margin:2px 8px;"><span style="display:inline-block;width:12px;'
                     f'height:12px;background:{color_for(t)};border-radius:50%;margin-right:4px;"></span>{t}</span>' for t in types)
    data = json.dumps({"nodes": vis_nodes, "edges": vis_edges}, ensure_ascii=False)
    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><title>Knowledge Graph</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>body{{margin:0;font-family:'Malgun Gothic',sans-serif}}#hdr{{padding:8px 14px;background:#1f2937;color:#fff}}
#hdr small{{color:#9ca3af}}#legend{{padding:6px 14px;background:#f3f4f6;font-size:12px;border-bottom:1px solid #e5e7eb}}
#net{{width:100%;height:calc(100vh - 92px)}}</style></head><body>
<div id="hdr"><b>Knowledge Graph (schema-first)</b> &nbsp;<small>{len(nodes)} nodes · {len(edges)} edges ·
 modularity {stats['modularity']:.3f} · density {stats['density']:.2f} · 점선=INFERRED</small></div>
<div id="legend">{legend}</div><div id="net"></div>
<script>const gd={data};
new vis.Network(document.getElementById('net'),{{nodes:new vis.DataSet(gd.nodes),edges:new vis.DataSet(gd.edges)}},{{
 nodes:{{shape:'dot',scaling:{{min:6,max:40}},font:{{size:13,face:'Malgun Gothic'}}}},
 edges:{{color:{{color:'#cbd5e1',highlight:'#2563eb'}},smooth:{{type:'continuous'}}}},
 physics:{{barnesHut:{{gravitationalConstant:-9000,springLength:140,springConstant:0.03}},stabilization:{{iterations:250}}}},
 interaction:{{hover:true,tooltipDelay:120,navigationButtons:true,keyboard:true}}}});</script></body></html>"""
    Path(out_html).write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="schema-first KG 빌드: 추출 JSON -> graph.json + graph.html + modularity")
    ap.add_argument("extractions", help="추출 JSON 파일 또는 *.json 디렉토리")
    ap.add_argument("--out", default="graphify-out")
    ap.add_argument("--aliases", default=None)
    ap.add_argument("--labels", default=None)
    ap.add_argument("--strip", default=None, help="추가 제거 관계명(쉼표구분)")
    ap.add_argument("--target", type=float, default=0.5)
    args = ap.parse_args()

    aliases = json.loads(Path(args.aliases).read_text(encoding="utf-8")) if args.aliases and Path(args.aliases).exists() else {}
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8")) if args.labels and Path(args.labels).exists() else {}
    drop = set(DROP_RELATIONS) | ({s.strip() for s in args.strip.split(",")} if args.strip else set())

    docs = load_extractions(args.extractions)
    nodes, edges, mstats = merge(docs, aliases, labels, drop)
    mod, density, ncomm = cluster(nodes, edges)

    type_cnt, rel_cnt, conf_cnt = defaultdict(int), defaultdict(int), defaultdict(int)
    for n in nodes.values():
        type_cnt[n["type"]] += 1
    for e in edges:
        rel_cnt[e["relation"]] += 1
        conf_cnt[e.get("confidence")] += 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stats = {"n_nodes": len(nodes), "n_edges": len(edges), "modularity": mod, "density": density,
             "n_communities": ncomm, "types": dict(sorted(type_cnt.items(), key=lambda x: -x[1])),
             "relations": dict(sorted(rel_cnt.items(), key=lambda x: -x[1])), "confidence": dict(conf_cnt),
             "dropped_weak_edges": mstats["dropped_weak"], "n_dangling": len(mstats["dangling"]),
             "dangling_edges": mstats["dangling"][:30], "type_conflicts": mstats["type_conflicts"][:30]}
    (out / "graph.json").write_text(json.dumps({"meta": stats, "nodes": list(nodes.values()), "links": edges},
                                               ensure_ascii=False, indent=2), encoding="utf-8")
    write_html(nodes, edges, stats, out / "graph.html")

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    verdict = "crisp" if mod >= 0.6 else "separated" if mod >= 0.5 else "mushy" if mod >= 0.4 else "hairball/sparse"
    print(f"\n[modularity {mod:.3f} -> {verdict}]  density {density:.2f}  (target {args.target})  "
          f"dangling {len(mstats['dangling'])}  dropped_weak {mstats['dropped_weak']}")
    print(f"wrote {out/'graph.json'}, {out/'graph.html'}")
    if mod < args.target:
        print("힌트: modularity 가 목표 미만. 약한 관계가 남았는지(--strip), 허브 분할축(A9)이 맞는지 점검.")


if __name__ == "__main__":
    main()
