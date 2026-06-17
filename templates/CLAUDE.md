# 지식그래프(KG) 운영 규칙 — kg-pipeline

이 폴더는 kg-pipeline 플러그인으로 KG를 만들고 질의한다. (이 블록을 프로젝트 CLAUDE.md에 붙여넣어 쓴다.)

## 위치
- raw 소스: `kg-input/` — get-content 가 `kg-input/sources/` 에 출처 메타와 함께 저장한다.
- KG 산출물: `graphify-out/` — graph.json, graph.html, KG-DESIGN.md, KG-AUDIT.md 전부 여기. 루트엔 raw 문서만.

## 워크플로우
1. **자료 수집**: `/get-content <url>` — 막히면 scrapling 으로 폴백. `kg-input/` 에 쌓인다.
2. **최초 KG 구축(1회)**: `/kg-design` — 설계(허브/분할/관계정책을 사람과 합의) + 빌드 + 클러스터 정제(modularity 게이트) + 감사.
3. **새 자료 추가**: `graphify <path> --update` 후 `refine_graph.py --apply` 재실행. **풀 재설계가 아니다.** 용어/스키마 변경은 노드 id 를 유지한 채 label 갱신·병합(무조건 삭제 금지).

## 사용자 질의가 들어오면
- `graphify-out/graph.json` 이 있으면 **먼저 `/kg-query` 로 검색**하고, 부족한 부분만 웹검색 등으로 보완한다. (그래프 = 누적 메모리. 외부 검색보다 그래프가 먼저.)
- 질문 유형에 맞춰 모드 선택: 이웃=BFS, 체인=DFS, 두 노드 사이=PATH, 조건 목록=--type.
- 정밀한 사실(수치/조건/인과)은 노드·엣지의 `source_location`/`source_url` 을 따라 **원문을 열어 검증**한 뒤 인용한다.
- 그래프에 없으면 없다고 말하고 지어내지 않는다. 새로 확인한 사실은 그래프에 반영한다.
