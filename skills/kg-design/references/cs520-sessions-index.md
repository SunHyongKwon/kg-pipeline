# Knowledge Graph 자료 분석 — 인덱스

Stanford CS520 (2021) Knowledge Graphs Seminar 재생목록(20개 세션)을 다운로드/분석한 결과물.

## 산출물
- `01-영상별-요약.md` — 20개 세션 각각의 주제/연사/핵심개념/구축교훈 정리
- `02-지식그래프-구축-가이드.md` — 20개 세션을 종합한 '지식그래프를 어떻게 구축할 것인가' 실무 가이드
- `summaries.json` — 구조화 분석 원본 데이터
- `data/` — 원본 자막(en-orig.srt) + 메타데이터(info.json)
- `transcripts/` — 정제된 평문 자막 (분석 입력)

## 세션 한눈에 보기 (회차 순)

| Session | 재생목록# | 단계 | 주제 |
|---|---|---|---|
| 1 | 01 | 정의/개념 | 지식그래프란 무엇인가 (What is a Knowledge Graph): 정의와 의미(meaning) 부여 방식, 그리고 검색엔진/데이터 통합/AI 세 응용을 통... |
| 2 | 02 | 정의/개념 | 지식그래프란 무엇이며 왜 필요한가 (What is a knowledge graph), 그리고 NSF Convergence Accelerator의 Open Know... |
| 3 | 03 | 정의/개념 | 지식그래프 데이터 모델(Knowledge Graph Data Models): RDF/SPARQL 대 Property Graph/Cypher 비교, 그리고 관계형 ... |
| 4 | 04 | 활용/추론 | 지식그래프 질의 언어와 분산 질의 처리 (Knowledge Graph Query Languages): Property Graph용 Cypher/GQL과 RDF용 ... |
| 5 | 05 | 구축/생성 | 지식그래프 설계 방법론 (How to design a Knowledge Graph) - RDF 그래프와 Property Graph 두 데이터 모델에서 스키마(sc... |
| 6 | 06 | 정의/개념 | 지식그래프 스키마 설계(schema design): 데이터를 진짜 지식(knowledge)으로 만들기 위한 logic/recognition conditions와,... |
| 7 | 07 | 구축/생성 | 구조화된 데이터(structured data)로부터 지식그래프 구축하기 - 스키마 매핑(schema mapping), 레코드 링키지(record linkage),... |
| 8 | 08 | 구축/생성 | 구조화 데이터로부터 지식그래프를 구축할 때의 엔티티 해소(entity disambiguation / entity resolution) - 꼬리(tail) 엔티티 ... |
| 9 | 09 | 구축/생성 | 텍스트로부터 지식그래프 구축 (constructing knowledge graphs from text) - 개체 추출(entity extraction)과 관계 추... |
| 10 | 10 | 구축/생성 | 비정형 입력(텍스트/이미지)에서 지식그래프를 구축하는 방법 - 자연어 이해를 위한 인과 지식그래프(causal knowledge graph)와 컴퓨터 비전을 위한... |
| 11 | 11 | 활용/추론 | 지식그래프 추론 알고리즘 (Knowledge Graph Inference Algorithms): 그래프 기반 추론과 온톨로지 기반 추론, 그리고 금융 분야 응용 ... |
| 12 | 12 | 활용/추론 | 지식그래프 추론(inference) 두 가지 접근: (1) 관계형 시스템(relational system)을 저장 계층으로 쓰는 효율적 추론과 KGMS(Knowl... |
| 13 | 13 | 활용/추론 | 사용자는 지식그래프(Knowledge Graph)를 어떻게 소비/탐색하는가 - 사용자 인터랙션 및 시각화 설계 원칙과, 검색엔진 지식 패널(Knowledge Pa... |
| 14 | 14 | 활용/추론 | 지식그래프 접근(access)을 위한 두 가지 상호보완적 기법: 논리 기반의 Logical English(structured query/프로그래밍 언어)와 사전학... |
| 15 | 20 | 구축/생성 | 대규모 지식그래프를 오래 지속되도록 구축/진화시키는 방법 - Amazon Product Knowledge Graph 구축(0에서 10억으로 확장)과 장수(long... |
| 16 | 15 | 활용/추론 | 지식그래프의 진화/변경 관리(change management)와 증분 뷰 유지(incremental view maintenance) — 스키마 진화(schema ... |
| 17 | 16 | 산업/응용 | 지식그래프의 고가치 활용 사례(high value use cases) - 구글 검색에서의 구조화된 지식 제품화와 GDELT 프로젝트의 전 세계 뉴스 기반 멀티모달... |
| 18 | 17 | 산업/응용 | 금융 산업에서의 지식그래프 활용 - 인과 지식그래프(causal knowledge graphs)를 통한 시장 예측과 온톨로지(ontology)+그래프 DB+머신러... |
| 19 | 18 | 구축/생성 | 지식그래프 구축을 위한 구현 도구 서베이(implementation tools survey) 및 지식그래프와 AI의 관계 종합 정리. 시리즈 마지막 주차로, 데이... |
| 20 | 19 | 활용/추론 | 지식그래프 연구 이슈와 미래 방향 (research issues and future of Knowledge Graphs): 지식그래프 상호운용성(interoper... |