# kg-pipeline

지식그래프(KG)의 수집 → 구축 → 질의를 한 묶음으로 처리하는 Claude Code 플러그인.

품질 좋은 KG가 나오도록 두 가지를 자동으로 강제한다: **클러스터 분리도(modularity) 게이트**(헤어볼 방지)와 **span 단위 출처(provenance)**(원문 추적·인용).

## 스킬 3종

| 스킬 | 역할 |
|---|---|
| `kg-pipeline:get-content` | 외부 자료 수집 → KG 입력 마크다운. urllib 우선, 막히면(봇차단/JS-only) **scrapling 폴백**. 출처 frontmatter 부착. |
| `kg-pipeline:kg-design` | 설계(허브/분할/관계정책을 사람과 합의) + 빌드(graphify) + 클러스터 정제(modularity 게이트) + 감사. |
| `kg-pipeline:kg-query` | graph.json 질의. 질문 유형에 따라 BFS(이웃)/DFS(체인)/PATH(두 노드)/타입필터. 출처로 원문 검증. |

## 사전 요구사항 (번들 불가, 직접 설치)

KG 작업 폴더(`kg-input/` 또는 `graphify-out/` 가 있는 폴더)에서 세션을 열면 SessionStart hook이 미설치 항목만 안내한다. KG와 무관한 폴더에서는 조용하다.

- **python3** (kg-query/get-content 엔진, 표준 라이브러리만 사용)
- **graphify** (KG 빌드 엔진, 필수): `pipx install graphify` 또는 `pip install graphify`
- **scrapling** (get-content 봇우회 폴백, 선택): `pip install "scrapling[fetchers]" && scrapling install`
  - 미설치 시 get-content 의 urllib 경로는 동작하지만, 막히는 사이트는 못 뚫는다.

## 설치

```
/plugin marketplace add SunHyongKwon/kg-pipeline
/plugin install kg-pipeline@kg-pipeline
```

업데이트:
```
/plugin marketplace update kg-pipeline
```

로컬에서 바로 테스트:
```
claude --plugin-dir /path/to/kg-pipeline
```

## 워크플로우

1. **수집**: `/kg-pipeline:get-content <url>` → `kg-input/sources/` 에 출처 메타와 함께 저장.
2. **최초 구축(1회)**: `/kg-pipeline:kg-design` → 설계+빌드+정제+감사. 산출물은 `graphify-out/` 에 모인다(graph.json, graph.html, KG-DESIGN.md, KG-AUDIT.md).
3. **새 자료 추가**: `graphify <path> --update` 후 `refine_graph.py --apply` 재실행(풀 재설계 아님).
4. **질의**: `/kg-pipeline:kg-query "<질문>"` → 그래프에서 관련 서브그래프 회수 → 출처로 원문 검증.

프로젝트에 운영 규칙을 박아두려면 `templates/CLAUDE.md` 블록을 그 프로젝트의 `CLAUDE.md` 에 붙여넣는다.

## 설계 메모

- graphify 는 빌드 엔진(pip 패키지)이라 플러그인에 번들하지 않고 외부 의존성으로 둔다.
- 클러스터가 또렷한 KG = 허브-스포크 위상 + 약한 `mentioned_in` 류 엣지 제거. kg-design 의 refine 단계가 이를 강제한다.
- 한글 등 비ASCII 코퍼스: 노드 id 를 자동 transliteration 에 맡기지 말고 개념별 안정 ASCII 슬러그를 고정 재사용(kg-design 추출 규칙에 포함).

## 라이선스

MIT
