#!/usr/bin/env python3
"""kg-query: 지식그래프(graph.json)를 질문으로 질의한다.

진입 노드를 라벨 매칭으로 찾고, 질문 유형에 맞는 순회(BFS/DFS/PATH)로 관련
서브그래프만 떼어내 출처와 함께 출력한다. 전체 문서를 읽지 않고 관련 부분만
회수하는 GraphRAG 방식.

graphify 그래프(nodes/links, source/target/relation)와 커스텀 property 그래프
(nodes/edges, src/dst/rel)를 모두 지원한다. graphify 패키지에 의존하지 않고
표준 라이브러리만 쓴다 -> 어떤 python3 로도 실행 가능.

사용:
  python3 query_graph.py [그래프경로|폴더] "질문" [--mode auto|bfs|dfs|path] [옵션]
  --mode   auto(기본): 질문에서 추정. bfs: 이웃 넓게. dfs: 체인 깊게. path: 두 노드 사이.
  --depth  순회 깊이(기본 bfs=2, dfs=6).
  --budget 출력 토큰 예산(기본 2000).
  --type   해당 타입 노드만 나열(구조적 필터; 예: --type Competition).
  --list-types  노드 타입 분포만 출력하고 종료.
경로 생략 시 graph/graph.json, graphify-out/graph.json, data/kg/graph.json 순으로 자동 탐색.
"""
import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

CANDIDATES = ["graph/graph.json", "graphify-out/graph.json", "data/kg/graph.json", "graph.json"]


def find_graph(path_arg):
    if path_arg:
        p = Path(path_arg)
        if p.is_dir():
            for c in ["graph.json", "graphify-out/graph.json", "graph/graph.json", "data/kg/graph.json"]:
                if (p / c).exists():
                    return p / c
            sys.exit(f"ERROR: {path_arg} 안에서 graph.json 못 찾음.")
        if p.exists():
            return p
        sys.exit(f"ERROR: 경로 없음: {path_arg}")
    for c in CANDIDATES:
        if Path(c).exists():
            return Path(c)
    sys.exit("ERROR: graph.json 없음. 경로를 인자로 주거나 KG 폴더에서 실행해라.")


def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes = {}
    for n in d.get("nodes", []):
        nid = n.get("id")
        if nid is None:
            continue
        nodes[nid] = {
            "id": nid,
            "label": n.get("label") or n.get("norm_label") or str(nid),
            "type": n.get("type") or n.get("kind") or n.get("file_type"),
            "source_file": n.get("source_file"),
            "source_location": n.get("source_location"),
            "source_url": n.get("source_url"),
            "props": n.get("props") or {},
            "prov": n.get("prov"),
        }
    edges = []
    for e in d.get("links") or d.get("edges") or []:
        u = e.get("source", e.get("src"))
        v = e.get("target", e.get("dst"))
        if u is None or v is None or u not in nodes or v not in nodes:
            continue
        edges.append({
            "u": u, "v": v,
            "rel": e.get("relation") or e.get("rel") or "",
            "conf": e.get("confidence") or e.get("kind"),
            "weight": e.get("weight", 1.0),
            "source_file": e.get("source_file"),
            "source_location": e.get("source_location"),
        })
    adj = defaultdict(list)
    for i, e in enumerate(edges):
        adj[e["u"]].append((e["v"], i))
        adj[e["v"]].append((e["u"], i))
    return nodes, edges, adj


def terms_of(q):
    cleaned = q.lower()
    for ch in "?!,.\"'()[]":
        cleaned = cleaned.replace(ch, " ")
    return [t for t in cleaned.split() if len(t) >= 2]


def find_starts(nodes, question, k=3):
    q = question.lower()
    terms = terms_of(question)
    scored = []
    for nid, n in nodes.items():
        lab = (n["label"] or "").lower()
        if not lab:
            continue
        score = 0
        for t in terms:
            if t in lab:
                score += 2
        if len(lab) >= 3 and lab in q:
            score += 4
        if score:
            scored.append((score, len(lab), nid))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [nid for _, _, nid in scored[:k]]


def bfs(adj, starts, depth, max_nodes=80):
    seen = set(starts)
    order = list(starts)
    used = set()
    frontier = list(starts)
    for _ in range(depth):
        nxt = []
        for u in frontier:
            for v, ei in adj[u]:
                used.add(ei)
                if v not in seen:
                    seen.add(v)
                    order.append(v)
                    nxt.append(v)
                    if len(seen) >= max_nodes:
                        return seen, order, used
        frontier = nxt
    return seen, order, used


def dfs(adj, starts, depth, max_nodes=80):
    seen = set()
    order = []
    used = set()
    stack = [(s, 0) for s in reversed(starts)]
    while stack:
        u, d = stack.pop()
        if u in seen or d > depth:
            continue
        seen.add(u)
        order.append(u)
        if len(seen) >= max_nodes:
            break
        for v, ei in adj[u]:
            used.add(ei)
            if v not in seen:
                stack.append((v, d + 1))
    return seen, order, used


def shortest_path(adj, src, dst):
    prev = {src: None}
    q = deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            break
        for v, ei in adj[u]:
            if v not in prev:
                prev[v] = (u, ei)
                q.append(v)
    if dst not in prev:
        return None, None
    nodes_path = []
    used = set()
    cur = dst
    while cur is not None and cur != src:
        nodes_path.append(cur)
        u, ei = prev[cur]
        used.add(ei)
        cur = u
    nodes_path.append(src)
    nodes_path.reverse()
    return nodes_path, used


def auto_mode(q):
    ql = q.lower()
    path_kw = ["사이", "between", " vs "]
    dfs_kw = ["어떻게", "왜", "과정", "흐름", "단계", "이어", "통해", "경로", "why", "how does", "leads to"]
    if any(k in ql for k in path_kw):
        return "path"
    if any(k in ql for k in dfs_kw):
        return "dfs"
    return "bfs"


def loc_of(n):
    return n.get("source_location") or n.get("source_file") or n.get("source_url") or (
        ",".join(n["prov"]) if isinstance(n.get("prov"), list) else "")


def emit(nodes, edges, seen, order, used, question, mode, budget):
    L = [f"Q: {question}", f"mode={mode}  서브그래프 {len(seen)} 노드", "", "노드:"]
    for nid in order:
        n = nodes[nid]
        t = f" [{n['type']}]" if n["type"] else ""
        loc = loc_of(n)
        loc = f"  <- {loc}" if loc else ""
        L.append(f"  - {n['label']}{t}{loc}")
    L.append("")
    L.append("관계:")
    for ei in used:
        e = edges[ei]
        if e["u"] in seen and e["v"] in seen:
            c = f" ({e['conf']})" if e["conf"] else ""
            eloc = e["source_location"] or e["source_file"] or ""
            eloc = f"  <- {eloc}" if eloc else ""
            L.append(f"  - {nodes[e['u']]['label']} --{e['rel']}--> {nodes[e['v']]['label']}{c}{eloc}")
    out = "\n".join(L)
    cap = budget * 4
    if len(out) > cap:
        out = out[:cap] + "\n...(잘림; --budget 늘려라)"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", nargs="?", default=None)
    ap.add_argument("question", nargs="?", default=None)
    ap.add_argument("--mode", default="auto", choices=["auto", "bfs", "dfs", "path"])
    ap.add_argument("--depth", type=int, default=None)
    ap.add_argument("--budget", type=int, default=2000)
    ap.add_argument("--type", default=None)
    ap.add_argument("--list-types", action="store_true")
    args = ap.parse_args()

    gpath = find_graph(args.graph)
    nodes, edges, adj = load(gpath)
    print(f"# graph: {gpath}  ({len(nodes)} 노드, {len(edges)} 엣지)")

    if args.list_types:
        cnt = defaultdict(int)
        for n in nodes.values():
            cnt[n["type"]] += 1
        for t, c in sorted(cnt.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
        return

    if args.type:
        hits = [n for n in nodes.values() if (n["type"] or "").lower() == args.type.lower()]
        print(f"# type={args.type}: {len(hits)} 노드")
        for n in sorted(hits, key=lambda x: x["label"]):
            extra = " ".join(f"{k}={v}" for k, v in (n["props"] or {}).items())
            loc = loc_of(n)
            print(f"  - {n['label']}  {extra}  {('<- ' + loc) if loc else ''}")
        return

    if not args.question:
        sys.exit("ERROR: 질문을 줘라. 예: query_graph.py . \"스캘핑이 경고하는 위험은?\"")

    mode = auto_mode(args.question) if args.mode == "auto" else args.mode
    starts = find_starts(nodes, args.question)
    if not starts:
        print("진입 노드 없음. 질문 용어가 노드 라벨과 안 맞음. --list-types 로 구조를 보거나 용어를 바꿔라.")
        return

    if mode == "path":
        if len(starts) < 2:
            print(f"path 모드인데 진입 노드가 1개({nodes[starts[0]]['label']})뿐. bfs 로 대체.")
            mode = "bfs"
        else:
            np_, used = shortest_path(adj, starts[0], starts[1])
            if np_ is None:
                print(f"'{nodes[starts[0]]['label']}' 와 '{nodes[starts[1]]['label']}' 사이 경로 없음(서로 다른 군집).")
                return
            print(emit(nodes, edges, set(np_), np_, used, args.question, "path", args.budget))
            return

    depth = args.depth if args.depth is not None else (6 if mode == "dfs" else 2)
    seen, order, used = (dfs if mode == "dfs" else bfs)(adj, starts, depth)
    print(emit(nodes, edges, seen, order, used, args.question, mode, args.budget))


if __name__ == "__main__":
    main()
