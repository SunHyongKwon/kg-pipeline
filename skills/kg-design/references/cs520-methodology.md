# 지식그래프(Knowledge Graph) 실무 구축 가이드: Stanford CS520 종합

이 문서는 Stanford CS520 (2021) Knowledge Graphs Seminar 20개 세션을 종합해, "지식그래프를 실제로 어떻게 구축해 나가야 하는가"를 수명주기(lifecycle) 단계별로 정리한 실무 가이드다. 각 주장에는 근거 세션을 (S번호)로 인용했다. 결론은 하나로 수렴한다: 지식그래프 구축은 1인 작업도, 완전 자동화도, 일회성 프로젝트도 아니다. 그것은 다학제 팀(multidisciplinary team)이 use case에서 출발해 점진적으로 키우고 영원히 유지보수하는 소프트웨어 산출물(software artifact)이다 (S2, S15, S16).

---

## 0. 핵심 전제: 지식그래프란 무엇인가

지식그래프는 노드(node)와 엣지(edge)에 잘 정의된 의미(meaning)를 부여한 방향성 레이블 그래프(directed labeled graph)다 (S1). 일반 그래프와의 결정적 차이는 그래프 구조 자체가 아니라 노드/엣지의 의미를 명시적으로 정의한다는 점이다. 트리플 저장(triple store)이나 방향성 레이블 그래프는 새로운 것이 아니다 (semantic networks, description logics, triple store의 긴 역사가 있다). 새로운 것은 세 가지다 (S1, S19):

- **Scale(규모)**: Wikidata는 약 8천만~9천만 객체, 10억+ 트리플 규모 (S1, S6).
- **Bottom-up(상향식) 개발**: top-down 설계가 아니라 가용 데이터에서 ML/NLP로 추출 (S19).
- **Mixed-mode(혼합) 구축**: 수작업 knowledge engineering + 자동 추출 + crowdsourcing을 섞음 (S1, S19).

지식그래프의 부가가치이자 가장 어려운 문제는 "의미 부여"다. 데이터(data)는 추론할 준비가 된 지식(knowledge)이 아니다. Wikidata에 'woman' 클래스가 있어도, 어떤 human이 woman인지 자동 판정하는 recognition conditions가 없으면 instance가 0개로도, 11개로도 나온다 (S6). 즉 클래스/관계/그래프를 갖춰 지식처럼 "보여도" recognition conditions와 inference logic이 없으면 실제로는 data일 뿐이다 (S6, S14).

### 표준화 동향: GQL과 SQL/PGQ (보강)
질의 언어 표준화는 "진행 중"이라는 모호한 표현보다 시점을 명시하는 편이 정확하다. **GQL(Graph Query Language)**은 2019년 ISO/IEC 표준화 투표를 통과했고 2022년 릴리스가 예정되었으며, 1987년 SQL 이후 첫 독립 국제 표준 DB 언어로서 SQL 위에 얹히지 않고 나란히 선다. 동시에 SQL에는 관계형 테이블로부터 가상 그래프(virtual graph)를 매핑하는 **SQL/PGQ** 확장이 추가되며, 둘 다 Cypher의 영향을 강하게 받았고 같은 사람들이 양쪽 그룹에서 작업했다 (S4).

---

## 1단계: 정의(Definition) — Use Case와 Competency Questions

### 무엇을 / 왜
구축에 들어가기 전에 "이 지식그래프가 무엇에 쓰일 것인가"를 먼저 고정한다. 모든 것은 use case에서 시작하며, competency question(애플리케이션이 성공하려면 답해야 하는 질문 집합)으로 범위(scope), 평가 기준, 세분화 수준(granularity), 종료 시점(언제 충분한가)을 정의한다 (S15). use case 없이 추상적으로만 구축하면 KG는 끝없이 비대해진다 (S15). 시맨틱웹(semantic web)이 과거 크게 성공하지 못한 두 이유 중 하나가 바로 "use case 없는 범용 구축"이었다 (S2).

### 어떻게
- Competency question을 먼저 작성하고, 거기서 역으로 노드/엣지의 의미를 설계한다 (S9, S15). 교과서 KG 사례에서는 질문을 diagnostic questions와 educationally useful questions(google-hard, 단순 문자열 조회 이상)로 분류했다 (S9).
- 사용자 페르소나(persona)와 소비 모드를 먼저 파악한다. 같은 KG라도 일반 시민, 전력망 관리자, 과학자에게 필요한 정밀도와 오차 정보 노출 수준이 다르다 (S2). push/pull, known/unknown question의 네 가지 상호작용 모드를 구분한다 (S13).
- **프로토타입을 사용자 중심 설계(user-centered design) 관점에서 반복적으로 보여준다.** 사용자에게 표현 방식을 제시하면 '그건 그렇게 하는 게 아니다'라며 되돌아가 수정해야 할 수 있다. 이 반복(iteration)은 별도의 함정이 아니라 정의 단계의 핵심 활동이다 — 의미 정의가 아직 유동적일 때 사용자 피드백으로 노드/엣지의 의미를 교정한다 (S2).
- NSF Convergence Accelerator는 phase 1에서 모든 팀이 user discovery, human-centered design, prototyping, team science 커리큘럼을 이수하게 했다. 이것이 KG 구축에 본질적으로 중요하다고 평가됐다 (S2).

### 판단 기준 / 트레이드오프
- **수직(vertical) vs 수평(horizontal)**: 도시 홍수, 정밀의학(SPOKE), 법원 기록은 도메인 수직 프로젝트, 지리공간 통합/KG 프로그래밍 시스템은 범용 수평 프로젝트다 (S2). 수직은 sweet spot을 찾기 쉽고, 수평은 일반성 대가로 SOTA 성능이 약해진다 (S2, S10).
- **Sweet spot 식별**: 스키마가 단순(5~10개 타입)하고 레코드가 거대하며 흥미로운 관계로 연결된 도메인이 KG 활용의 sweet spot이다. 이 경우 스키마 매핑 노력은 작고 대부분의 노력이 record linkage, 적재, 그래프 알고리즘에 들어간다 (S7).

### 거버넌스 결정: 프라이버시와 표준 어휘 채택 동력 (보강)
정의 단계에서 두 가지 거버넌스 정책을 함께 결정해야 한다.

- **프라이버시/보호된 접근**: 공개 데이터만 다룰지(OKN처럼), 사적 데이터가 필요하면 보호된 접근(protected access, 예: FSRDC)이나 익명화(anonymization)로 처리할지 먼저 정한다 (S2). 초기 Semantic Web이 빠뜨린 privacy/security 제어를 모델에 포함할지도 이 시점에 결정한다 (S20).
- **표준 어휘 채택의 사회·경제적 동력(adoption incentive)**: 스키마(schema)는 기술만으로 진화하지 않는다. 충분히 많은 동종(homogeneous) 데이터 제공자가 마크업할 동기(예: 검색엔진 노출 이점)가 있고, 커뮤니티 합의가 빠를 때 진화한다 (schema.org의 COVID 확장은 2주 내에 이뤄졌다). 표준 어휘를 채택시키려면 제공자에게 동기를 주고 커뮤니티 합의를 빠르게 이끌 거버넌스를 함께 설계해야 한다 (S2).

---

## 2단계: 데이터 모델링 / 온톨로지 / 스키마 설계

### 무엇을 / 왜
KG 생성은 (1) 스키마(schema) 설계와 (2) 인스턴스(instance) 채우기 두 단계로 나뉜다 (S5). 스키마는 taxonomy 그 이상이어야 한다. "human은 person의 subclass"라는 계층만으로는 부족하고, recognition conditions와 inference를 갖춘 logic이 있어야 진짜 schema다 (S6).

### 핵심 설계 의사결정 1: RDF vs Property Graph

두 모델 모두 directed labeled graph라는 수학적 구조를 공유한다 (S3). 선택은 기술적 우월성보다 응용 요구·팀 배경 같은 사회·문화적 요인에 크게 좌우된다 (S3).

| 항목 | RDF (SPARQL) | Property Graph (Cypher) |
|---|---|---|
| 핵심 동기 | 웹에 데이터 게시·발견·재사용, 다중 소스 질의 (S3, S5) | 폐쇄형 엔터프라이즈, 그래프 순회(traversal) 최적화 (S3, S5) |
| 엣지 속성 | 직접 미지원 → reification 필요 (S3) | 직접 지원 (S3, S4) |
| IRI 식별자 | 필수 (S3) | 불필요, schema-free (S3, S4) |
| 표준화 | W3C 표준 (S3) | GQL: 2019년 ISO/IEC 표준화 통과·2022년 릴리스 예정, SQL/PGQ 동반 (S4) |
| dereferenceability | URI 역참조 가능 → 상호운용성 강함 (S20) | 없음 → 상호운용성 약함 (S20) |

**판단 기준**: 웹에 게시해 타인이 발견·재사용하게 하려면 RDF, 사전 스키마 없이 그래프 순회가 중요하면 Property Graph (S3). Property Graph 채택 동기는 다양한 엔티티/관계, 자기참조(self-referencing), 가변/미지 깊이의 관계 탐색, 경로 발견이 필요할 때다 (S4). 변환은 Property Graph → RDF가 RDF → Property Graph보다 쉽다(역방향은 reification 역공학 필요) (S3). 한 가지 통합 관점도 있다: RelationalAI는 directed/property graph, RDF triple, SQL table을 모두 relation으로 표현해 단일 KGMS로 처리한다 — 데이터 모델이 아니라 질의 언어를 개선하라는 입장이다 (S12).

**그래프 모델의 한계**: 모든 것을 그래프로 강제하지 말 것. 비이진(non-binary, 3항 이상) 관계나 값(숫자)이 대부분인 데이터(예: 시계열 인구통계)는 관계형 테이블이 더 적합하다 (S3). triple만으로는 4항 관계, 양화사 중첩, modal/반사실 추론을 자연스럽게 못 한다 — Cyc는 이 때문에 고차논리/양상논리로 나아갔다 (S20).

### 핵심 설계 의사결정 2: Schema-first vs Data-first (Top-down vs Bottom-up)

- **데이터 통합용 KG**는 pay-as-you-go 상향식이 효과적이다. 먼저 여러 소스의 관계형 데이터를 트리플로 변환해 적재(낮은 진입장벽)하고, 구체적 비즈니스 질문이 생길 때 스키마 매핑을 수행한다 (S1).
- 그러나 **상향식으로 모은 데이터라도 결국 추론을 위해 의미의 경계를 둘러야 하므로**, 하향식 도메인 모델링/클래스·관계 정의가 어느 시점에는 반드시 필요하다 (S1, S19). 학습 가능하다고 해서 top-down semantics 설계의 중요성이 사라지지 않는다 (S19).
- Cypher는 전통적으로 schema-free였고 그것이 장점이었으나, 성숙한 도메인이나 데이터 거버넌스가 필요하면 schema 도입이 유익하다(GQL에 schema 지원 추가 예정) (S4).

### 핵심 설계 의사결정 3: 어휘를 lay user가 이해하게 설계 (보강)
crowdsourcing이든 협업 큐레이션이든 데이터 품질의 핵심은 **작업자의 인지(cognition)에 부합하는 차원/관계 어휘 설계**다. GLUCOSE는 cause와 enable을 별도 차원으로 두었더니 작업자가 혼동해 둘을 합쳤고, 결국 차원 정의를 인지심리학(cognitive psychology) 문헌과 사용자 인터뷰로 도출했다 (S10). 차원/관계 어휘는 형식적 정확성만이 아니라 lay user가 직관적으로 구별할 수 있는지를 기준으로 설계해야 하며, 그렇지 않으면 수집 데이터의 일관성이 무너진다 (S10).

### 온톨로지 설계: 장수(longevity)와 재사용

오래 지속되는 KG/온톨로지의 비결 (S15):
- **기존 vocabulary를 먼저 찾아 재사용하라.** 오늘날 기존 vocabulary를 찾아보지 않고 직접 만들면 거의 항상 실수다. BioPortal, data dictionary, code book, Excel column header 등에서 출발한다 (S15). RDF 설계에서도 org, SKOS, FOAF, schema.org 같은 표준 어휘 재사용이 의미 정의와 상호운용성의 핵심이다 (S5).
- **MIREOT**: 큰 외부 온톨로지(예: ChEBI)는 전체를 import하지 않고 필요한 부분(예: 5%)만 가져온다 (S15).
- **core와 외곽을 구분하라.** core는 제약을 적게 줘 확장이 쉽게, 외곽은 자동화로 현실 변화를 빠르게 반영한다 (S15).
- **restriction은 별도 module로 분리하라.** 제약이 많으면 재사용이 제한된다. 예: has age 상한을 property가 아니라 class에 적용(사람 130, 고양이 더 낮게) (S15).
- **단순함을 우선하고 점진적으로 modularize하라.** 필요 이상 큰 온톨로지를 만들지 말 것. 같은 것을 말하는 방법이 여러 개면 연역적 폐포(deductive closure) 유지를 위해 N제곱 개의 axiom이 필요하다 (S20).
- **모듈형 온톨로지에는 겹치는(overlapping) 전문성을 가진 도메인 전문가 둘 이상, 온톨로지 엔지니어 둘 이상이 필요하다** (S2).
- **모든 process를 documentation하라.** 다른 사람이 동일 절차를 따라야 longevity와 유지보수가 가능하다 (S15). 새 어휘를 만든다면 문서화·자기서술적(self-describing)·버전 관리·다국어·지속적 게시를 지킨다 (S5).

### RDF 설계 원칙: Linked Data 4원칙 (S5)
1. 사물 이름에 IRI 사용, 2. 조회 가능한 HTTP IRI 사용, 3. 조회 시 RDF/SPARQL로 유용한 정보 제공, 4. 다른 데이터셋으로의 링크 포함. IRI는 짧고 기억하기 쉽게(mnemonic), URL처럼 지속적(persistent)으로 짓는다 (S5). 데이터셋 간 링크는 relationship/identity(owl:sameAs)/vocabulary 세 종류를 의식적으로 구분한다 (S5).

### Property Graph 설계: 엔지니어링 판단 (S5)
'무엇을 클래스(label) vs 속성(property) vs 객체+관계로 둘 것인가'는 깊은 철학이 아니라 인덱싱·접근 패턴·시간 가변성 기반의 엔지니어링 판단이다. 대부분의 그래프 엔진은 클래스/관계는 인덱싱하지만 속성은 인덱싱하지 않으므로, 자주 선택·탐색하는 정보는 클래스나 관계로 승격하라 (S5). 시간 가변 정보·출처(provenance)·신뢰도(confidence)는 관계 속성으로 모델링하되, 대량 선택 쿼리가 있으면 reify하라 (S5).

### Reification의 세 가지 목적 (보강)
reification은 단일 기법이 아니라 서로 다른 세 목적으로 쓰인다. 셋을 구분해야 어디에 어떤 형태로 적용할지 판단할 수 있다.

1. **비이진(non-binary) 관계 표현**: 'x is between y and z' 같은 ternary 관계를 between 노드 + 이진 관계들로 분해. conflict-of-interest 같은 n-항 관계도 conflict 노드로 사물화해 표현한다 (S3, S5, S11, S14).
2. **성능을 위한 관계 승격**: 인덱싱되지 않는 관계 속성을 관계(relation)로 재정의해 빠른 선택/탐색을 얻는다 (S5).
3. **Reification of time(시간의 사물화)**: 시제(과거/미래) 대신 시간을 변수 t1, t2로 명시화해 모든 동사를 현재형으로 표현한다. 이렇게 하면 modal logic의 가능세계 의미론(possible world semantics) 같은 복잡성을 피할 수 있다. Logical English의 핵심 모델링 기법 중 하나다 (S14).

RDF의 reification(rdf:subject/predicate/object)과 Property Graph의 관계 승격은 본질적으로 동일한 기법이며 관계 이름 선택만 다르다 (S3, S5).

### 스키마를 진짜 지식으로: logic과 ShEx (S6)
- **MARS/MARPL/EMARPL의 위상 구분(보강)**: Dresden의 Markus Krötzsch 그룹이 만든 MARS/MARPL 계열은 일반 logic에 fact의 qualifier, Wikidata data type·qualifier 처리 rule·constraint를 더한 것이다. David Martin과 Peter Patel-Schneider가 Wikidata에 맞게 확장한 것이 EMARPL이다. 핵심 역할 구분은 다음과 같다 — **MARPL/EMARPL은 inference(새 결론 도출)용이고, ShEx는 integrity/conformance check용이다** (S6). EMARPL은 단순 'logic'이 아니라 **forward chaining rule로 구현 가능하며 inference 복잡도가 나쁘지 않다**는 점이 실용적 핵심이다. transitivity, symmetric property, qualifier 결합, constraint를 forward chaining rule만으로 적용하면 큰 추가 비용 없이 data를 knowledge로 바꿀 수 있다 (S6).
- **OWL vs ShEx 구분**: OWL은 세상(reality)을 top-down 기술(예: 모든 사람은 부모가 둘), ShEx/SHACL은 우리가 가진 데이터(혹은 expectations)를 기술한다 (S6). ShEx는 validation, documentation, pre-submission/pre-ingestion check, form 자동 생성 등에 재사용된다 (S6).

### 시스템 내장 설계: provenance 추적을 쉽게 (보강)
provenance는 단순히 '기록'하는 것을 넘어, **데이터 품질 디버깅을 프로그래밍 환경에 내장(embed)**하면 추적이 쉬워진다는 설계 원칙이 중요하다. 시스템 안에서 작업하면(시스템이 작업의 일부로서 출처를 자동 연결하면) provenance 추적이 외부 후처리보다 훨씬 쉬워진다 (S2). 즉 출처 추적을 별도 단계가 아니라 작업 환경 자체의 속성으로 설계하라.

---

## 3단계: 지식 추출 / 수집(Knowledge Extraction & Ingestion)

KG는 그것이 구축된 데이터의 품질, 수집(ingestion) 방식, 품질 관리 수준만큼만 좋다 (S2).

### A) 구조화 데이터로부터 (S7)
구조화 데이터에서의 KG 구축은 새로운 문제가 아니라 데이터 통합(data integration) 문제이며, 타깃이 triple이라는 점만 다르다 (S7). 두 핵심 하위 문제:

- **스키마 매핑(Schema Mapping)**: Datalog 규칙(head :- body)으로 명세하고 rule engine으로 자동 적재한다. 여러 소스를 합칠 때는 hasSupplier 같은 새 관계와 vendor_1 같은 새 상수로 provenance를 추적한다 (S7). 완전 자동화는 불가능하다 — 스키마 수준 학습 데이터가 매우 희소하기 때문. 언어/형태/제약 기반 휴리스틱(linguistic/instance/constraint mapping)으로 후보를 "제안"만 하고, 최종 검증은 도메인+IT를 모두 아는 knowledge scientist가 한다 (S7).

### B) 비정형 텍스트로부터 (S9)
- **두 building block**: entity extraction(NER, B/I/E/O/S 태그)과 relation extraction (S9).
- **세 갈래 방법**: sequence labeling(CRF+feature engineering), neural/language model(BERT repurpose), rule-based(정규식/사전/Hearst patterns) (S9). 현재 트렌드는 learning 기반이지만, rule/구문 패턴은 학습 데이터 부트스트랩에 핵심이다 (S9).
- **Language model 2단계 적용**: (1) task-independent training으로 대상 도메인 어휘 학습, (2) task-dependent training으로 추출 작업 학습. 특수 마커(CLS/SEP 등)를 삽입해 모델을 repurpose한다 (S9).
- **학습 데이터 부트스트랩**: 교과서 glossary, 기존 KB의 distant supervision, Hearst patterns, weak supervision(Snorkel식 labeling function), open information extraction(단 semantics가 없어 KG 목표에서는 제외) (S9).
- **냉정한 현실**: 자동 추출만으로 정확한 KG는 안 나온다(실측 precision 0.65~0.67, recall 0.51~0.54). 따라서 human-in-the-loop(추출 후 review)가 필수다 (S9). 관계 추출에는 turnkey 솔루션이 없고, 데이터마다 문법이 달라(뉴스 본문 학습기는 헤드라인에서 성능 급락) 반드시 자기 데이터셋으로 직접 학습해야 한다 (S19).

### C) 비정형 이미지/멀티모달로부터 (S10, S15, S17)
- **Scene Graph**: 이미지를 객체(bounding box)+속성+관계로 인코딩하는 조합적 표현 (S10). 객체와 관계를 분리 예측(decomposition)하면 n²·k 대신 n+k 범주만 학습해 novel composition에 일반화된다 (S10).
- **멀티모달**: 동일 엔티티 코드로 텍스트/이미지/영상을 횡단한다. Amazon은 attribute value 추출에서 **multi-modal transformer로 OpenTag(텍스트만) 대비 F-measure 11% 향상**을 달성했고, OCR 기여가 가장 컸다(이미지 정보 대부분이 이미 OCR에 들어있어 image 자체 기여는 적음) (S15). 이 11%(multi-modal vs 텍스트 전용)는 아래 transfer/multi-task의 **F-measure 10%p 향상(category 조건, taxonomy-aware)**과 다른 수치이므로 혼동하지 말 것 (S15).
- GDELT는 Cloud Vision/Video API로 이미지·영상을 그래프화한다 (S17).

### D) Crowdsourcing으로부터: 맥락 기반(contextualized) 규칙 방법론 (보강)
고품질 commonsense/인과 지식은 다단계 crowdsourcing으로 수집 가능하다 (S10).

- **다단계 파이프라인**: GLUCOSE는 Mechanical Turk에 (1) 90%+ 통과 자격 검증(qualification) UI, (2) 본 수집, (3) 0~3점 reviewer 검토 대시보드의 3단계와 약 6라운드 파일럿으로 전문 작업자 풀을 확보했다 (S10).
- **맥락 기반(contextualized) 규칙이 핵심 차별점**: GLUCOSE의 ATOMIC 대비 핵심 개선은 단순한 다단계 crowdsourcing이 아니라 **규칙을 맥락에 grounding하는 방법론** 자체다. ATOMIC식 비맥락 규칙('팔을 두르면 행복하다')은 맥락에 따라 틀릴 수 있다. GLUCOSE는 이를 **특정 스토리에 grounding된 specific rule**과 **더 일반적인 general rule** 두 수준으로 수집해, 같은 추론도 맥락에 따라 다르게 적용되도록 했다 (S10).
- **동적 규칙 생성**: semi-structured inference rule(subject-verb-object 등 단순 구문 템플릿)을 수집해 neural model(fine-tuned T5)을 학습하면, 정적 KB가 아니라 unseen 스토리에서도 규칙을 생성하는 동적 KB가 된다 (S10).

### 핵심 설계 의사결정 4: 자동추출 vs 큐레이션, 수작업 vs 크라우드소싱 vs ML
- **완전 자동은 신화다.** 의미 있는 품질의 KG에는 데이터 라벨링/검증 등 수작업이 항상 일부 포함된다 (S1, S9, S19).
- **라벨 데이터는 제품 생애주기 전반에서 확보한다**: 초기엔 데이터 과학자 자체 라벨링 → 전문가/크라우드소싱 → 출시 후엔 thumbs up/down(explicit), 클릭·랭킹(implicit) (S7).
- **head 지식(고품질 핵심)은 여전히 사람 grader 검증이 표준**이고, 라벨 부족 시 self-supervised/weakly-supervised/masking을 활용한다 (S7).
- **큐레이션된 데이터가 비정형 웹 텍스트 추출보다 유효성이 높다.** 웹 텍스트 추출 시 Barack Obama의 최빈 hypernym이 'terrorist'로 오염되는 사례가 있었다 (S13). 제약 하에서는 완벽한 온톨로지 추론보다 'off-the-shelf good enough'가 실용적이다 (S13).

---

## 4단계: 엔티티 해소(Entity Resolution / Identity)

서로 다른 소스의 레코드/멘션이 동일한 실세계 객체를 가리키는지 식별하는 문제로, record linkage, instance matching, dedup, named entity disambiguation(NED) 등으로 불린다 (S7, S8).

### A) Named Entity Disambiguation (NED) — 텍스트 멘션 (S8)
- 문장의 strings를 지식베이스의 things로 매핑한다(예: "how tall is lincoln" → Abraham Lincoln) (S8).
- **head vs tail/unseen 엔티티 문제**: 산업 질의의 다수가 학습데이터에 거의 없는 꼬리(tail) 엔티티다. 텍스트 암기 기반(BERT)은 head는 잘 처리하지만 tail은 못 한다 (S8).
- **해법(Bootleg)**: 일반화되는 신호인 타입(type)과 KG 관계(relationship) 패턴을 명시적으로 학습한다. 신호 위계는 타입(가장 일반적) > KG 관계 > 엔티티 임베딩(가장 식별적)이다. 같은 관계를 가진 엔티티에 동일 임베딩을 공유시켜 인기 엔티티 신호를 희귀 엔티티로 전이한다 → unseen 엔티티에서 약 40 F1 향상 (S8).
- **inverse-popularity regularization**: 모델이 식별적 엔티티 임베딩에만 의존하지 않고 희귀 엔티티에서는 관계/타입 신호를 쓰게 강제 (S8).
- **자동 라벨링**: Wikipedia 인터링크를 자동 라벨로, Wikidata에서 타입/관계를 자동 스크래핑해 수작업 최소화 (S8).

### B) Web-scale Entity Resolution (ER) — 레코드 (S7, S8)
- **2단계 알고리즘**: blocking(값싼 휴리스틱+인덱싱으로 후보 대폭 축소, O(mn)→O(m+n))과 matching(정밀 비교) (S7, S8).
- **매칭 규칙**: random forest + active learning으로 소수 라벨에서 반복 학습, edit distance/Jaccard/cosine/overlap 유사도를 feature로 사용 (S7).
- **단계적 ER 설계(Kejriwal)**: (1) 타입 정렬 → (2) 술어 정렬(overlap/subset/superset) → (3) blocking → (4) 유사도로 same-as 링크 생성 (S8).
- **DASH 요구사항**: 웹 스케일 ENS(Entity Name System)는 Domain independence, Automation, Scalability, Heterogeneity 4가지를 동시에 충족해야 한다. 문헌에 1~2개 만족은 많지만 4개 동시 만족은 드물다 (S8). MapReduce/Spark로 옮기면 GPU 없이 DBpedia↔Freebase(수백만 노드)를 100달러 미만으로 해소 가능했다 (S8).
- **학습셋 확보 자체가 난제**: m×n 쌍 무작위 샘플링은 대부분 비중복이라 seed set조차 얻기 힘들다 → 자동 노이즈 학습셋 생성기 + self-supervision 사이클로 신호 증폭 (S8).

### 식별자 전략
- 이상적으로 두 소스가 동일 IRI나 owl:sameAs를 쓰면 매핑이 쉽다(RDF 권장) (S5, S7). 동일 식별자(예: Wikidata identifier) 사용으로 서로 다른 기관 데이터를 연결한다 (S1). 폐쇄형 엔터프라이즈도 고유 고객 ID 같은 자체 식별 체계를 갖는데, 이는 사실상 IRI와 같은 유일 식별 문제다 (S5).
- 도메인 의존성 경계: 영어 Wikidata는 타입/관계 품질이 높지만, 의료 텍스트처럼 'finding' 같은 무의미한 광범위 타입만 있는 도메인에서는 효과가 떨어진다 (S8).

---

## 5단계: 통합 / 품질 관리(Integration & Quality)

### 무엇을 / 왜
KG 구축은 본질적으로 noisy하며 100% 정확할 수 없다 (S19). '완전 자동' 광고는 현실과 다르므로 피드백 루프와 수작업 큐레이션을 설계에 포함해야 한다 (S19).

### 데이터 클리닝 (S7)
- **두 문제 클래스 구분**: unification/integration(스키마 매핑·중복제거, 모든 것을 모든 것과 비교하는 조합 문제)과 cleaning(오류/위반 탐지·복구, 데이터 생성 모델만 이해하면 됨) (S7).
- **HoloClean(Noisy Channel Model)**: 데이터가 깨끗하게 생성된 뒤 노이즈 채널(오타·무지·악의)을 거쳐 더러워졌다고 가정하고, 관측 인스턴스로부터 깨끗한 데이터를 최대화한다. 복구·임퓨테이션·지식 구축을 단일 예측 문제로 통합 (S7).
- **도메인 지식 주입이 경쟁우위**: vanilla ML은 구조화 데이터의 희소성 때문에 학습이 안 된다. 그래프 구조·스키마·온톨로지·타입·denial constraint(SHACL 유사)를 feature/soft constraint/prior로 주입해야 한다 (S7).
- **반자동(semi-automatic) 운영**: 자동 임퓨테이션을 곧장 신뢰하지 말 것. (1) attention 가중치로 '왜 틀렸는지' 설명, (2) 확신도/엔트로피로 red/orange/green 분류해 QA 시간을 배분한다 (S7).

### 무결성 제약 (S12)
- 위반을 자동 수정할지, 막고 보고할지 구분하라. integrity constraint(ic)는 위반 변경을 막고 보고한다. 예: 모든 actor는 person(subset), birthdate는 하나(functional dependency), spouse는 symmetric, located-in은 transitive (S12).
- 불완전한 그래프는 symmetric/transitive 같은 성질 선언으로 누락된 엣지를 자동 완성할 수 있다 (S12).

### 논리 기반 vs ML 추측의 혼합: 운영 의미론의 전환 (보강)
신뢰성이 절대적인 금융·과학·법률 도메인에서는 '추측'이 부적절하다(Mike Genesereth의 반론). 휴리스틱 매핑은 약해서 object 대 object 단순 매핑을 넘는 복잡한 join/union을 표현하지 못한다. 또한 데이터를 사후 클리닝하기보다 입력 시점에 올바르게 받는 'correct-on-capture'로 클리닝 문제 자체를 회피하는 접근도 유효하다 (S7).

논의의 핵심 결론은 단순히 "논리와 ML을 혼합하라"가 아니라, **제약(constraint)을 hard 규칙이 아닌 soft constraint/prior로 다루는 운영 의미론(operational semantics)의 전환**으로 받아들이라는 것이다. 즉 제약의 위반을 즉시 거부하는 의미론에서, 제약을 학습 모델에 사전지식으로 주입하는 의미론으로 옮긴다. 동시에 ETL, TGD/EGD, 정보 교환(information exchange) 등 수십 년간 검증된 데이터 통합 문헌을 무시하지 말고 그 위에서 ML 추측을 결합해야 한다 (S7).

### Provenance와 ground truth
- **provenance(출처)를 반드시 기록하라.** 출처 기록 여부가 재사용 성패를 좌우한다 (S15). 고도 큐레이션 DB와 crowdsourcing 관측 데이터가 공존하는 과학 데이터에서 특히 중요하며, provenance 추적을 시스템에 내장하면 비용이 크게 줄어든다 (S2).
- **대규모 클리닝의 ground truth 검증은 전체 단위로는 비현실적**이다. 소규모 gold set을 만들어 모델 학습·평가에만 쓰되, gold set은 운영 파이프라인이 아니라 모델 판정 수단으로만 사용한다 (S7).

---

## 6단계: 저장 / 쿼리(Storage & Query)

### 저장 모델 선택 (S3, S12)
- 지식그래프(triple) 저장에는 전용 트리플 엔진이 관계형보다 빠를 수 있으나, 한 엔티티의 여러 속성을 wide table 한 행에 저장하면 관계형/SQL이 더 빠를 수 있다. 데이터 형태에 맞춰 저장 방식을 고르라 (S3).
- triple 기반 저장은 join 비용이 있으나 스키마 질의 용이성과 확장 유연성(컬럼 추가 대신 관계 추가)이 장점이며, worst-case optimal join 같은 알고리즘이 join 비용을 상당히 완화한다 (S12).

### 질의 언어 (S3, S4)
- **SPARQL**(RDF): graph pattern matching 기반, IRI로 다중 소스 질의 가능, BGP(Basic Graph Pattern, homomorphism 기반 subgraph matching) (S3, S4).
- **Cypher**(Property Graph): ASCII art 패턴, 가변 길이 경로(transitive closure), WITH를 통한 linear composition을 간결히 표현 (S4). 그래프 쿼리 언어는 아직 표준이 없고 Cypher가 선두였으며, 그 뒤를 잇는 GQL은 2019년 ISO/IEC 표준화를 통과(2022년 릴리스 예정), SQL/PGQ가 동반된다 (S4, S19).
- **스키마-데이터 동시 질의(schema-data co-query)(보강)**: 사전에 스키마를 다 모르는 KG 응용에서는 어떤 relation이 존재하는지 탐색할 수 있어야 한다. 따라서 데이터뿐 아니라 스키마도 함께 질의할 수 있게 설계하라. relation을 module(named subgraph)로 묶어 reflect하면, generic PageRank/유사도 같은 알고리즘을 그래프에 일반적으로 적용할 수 있다. 이는 탐색형 KG 응용의 핵심 역량이다 (S12).

### 분산 처리 (S4)
대규모 KG는 단일 머신을 넘어서므로 분산을 전제로 설계한다 (S4). 채택 기준: (1) 데이터 소유권 유지(federated), (2) 단일 머신 초과 또는 동시 질의 병목(scale-out).
- **graph partitioning의 핵심 통찰**: 단순 triple table 해싱은 subject-object join 시 중간 결과가 폭증하므로 피한다. inter-partition join을 줄이려면 edge cut이 아니라 **predicate cut을 최소화**해야 한다 (S4).
- **파티셔닝을 워크로드와 맞춰라**: star 질의는 정점+이웃을 한 파티션에 모아야 유리(edge-disjoint는 불리), cloud/MapReduce는 같은 predicate 엣지를 한 파일에 모으는 edge-disjoint가 유리 (S4).
- **federated 질의의 근본 난제**는 '어떤 소스로 가야 하는가'를 아는 것이며 미해결 문제다. endpoint 신뢰성도 낮다(최대 64% offline) (S4).
- RDF/SPARQL 분산 처리는 분산 관계형 DB만큼 성숙하지 않았다(대부분 BGP만, full SPARQL 1.1은 미흡) (S4).

### 도구 선택 원칙 (S19)
- 단순 traversal만 필요하면 SQL로도 충분하니 그래프를 위한 그래프를 도입하지 마라. 전통적 해법이 실패할 때만 그래프 시스템을 도입하라(incremental adoption) (S19).
- **OLTP**(업데이트/트랜잭션, 빠른 traversal)에는 graph database(Neo4j, Neptune), **읽기 전용 대규모 분석(OLAP)**에는 graph compute engine(NetworkX in-memory, Spark GraphX 분산)을 쓴다 (S19).
- 도구 평가 차원: 분산 여부, ACID, 관리형(managed) 여부, 가격, 지원 생태계 (S19).

### 저지연 서빙 사례 (Neva) (S13)
저지연이 P0 요구이므로 가능한 모든 작업을 **빌드타임(build-time)**으로 옮기고 서브타임 작업을 최소화했다. 서브타임에는 Wikipedia URL을 키로 key-value store(Scylla)에서 조회해 로케일별 렌더링만 한다. 데이터가 정적이므로 1TB를 두 번 처리해도 무방(컴퓨트는 엔지니어링 노력 대비 무료) (S13). 직접 엣지가 없는 사실도 flat JSON을 key-value store에 적재해 edge-path 역추적으로 도출하는 '가난한 자의 그래프 DB'를 만들 수 있다(Dianne Feinstein 사례) (S13).

---

## 7단계: 추론 / 임베딩(Inference & Embeddings)

추론은 명시적으로 저장되지 않은 새 결론을 도출하는 것으로, 단순 조회(SPARQL/Cypher)와 구분된다 (S11).

### A) 그래프 기반 추론 (S11)
추상 그래프에도 적용 가능하다.
- **Pathfinding**: A*(admissible heuristic h(n)이 과대평가 안 하면 최적 보장, h=0이면 Dijkstra/BFS) (S11).
- **Centrality**: degree, betweenness, closeness, PageRank(연결 노드의 영향력까지 반영, damping factor 0.85, 인접행렬 eigenvalue로 해석) (S11).
- **Community detection**: connected components, label propagation, Louvain(modularity) (S11).

### B) 온톨로지 기반 추론 (S11)
**이것이 지식그래프를 일반 그래프와 구별짓는 핵심이다** (S11). 노드에 클래스를 부여하고 관계의 의미·제약을 정의할 때 일반 그래프가 지식그래프가 된다.
- **Taxonomic reasoning**: subclass/instance-of transitivity, disjoint class, necessary/sufficient properties, domain/range/cardinality 제약, inheritance (S11).
- **Rule-based reasoning**: conflict-of-interest 같은 비이진 관계 도출에 적합. 결과를 그래프에 넣으려면 reification(existential rule로 새 객체 생성)이 필요하다 (S11). bottom-up(모든 사실 도출 후 질의, 종료 보장 필요·공간 많음) vs top-down(질의에 필요한 것만, 공간 절약·긴밀 통합 필요) 전략을 선택한다 (S11).
- instance 질의는 반드시 transitive subclass(p31/p279*)까지 포함해야 핵심 통계가 틀리지 않는다 (S6).

### C) 효율적 추론: KGMS, semantic optimizer, 메타프로그래밍 (S12, S20)
사용자가 알고리즘을 직접 짜게 하지 말고 '무엇을' 원하는지만 선언하게 하라. semantic optimizer는 사용자가 선언한 수학적 성질(분배/결합 법칙, functional dependency)을 이용해 고수준 선언에서 효율적 알고리즘(Dijkstra, single-source)을 자동 도출한다 (S12). 그래프 질의 성능의 열쇠는 join 알고리즘이다 — binary join은 triangle query에서 중간 결과가 폭발하므로 worst-case optimal join으로 변수 단위로 좁혀 sparsity를 활용한다 (S12).

**메타프로그래밍(meta-programming)으로 반복 제약을 추상화하라(보강)**: '네덜란드 시민은 Dutch' 같은 규칙을 일일이 쓰지 말고 citizenship-라벨 매핑을 메타 규칙(meta rule)으로 추상화해 대량의 logic을 간결히 생성한다 (S12). Cyc의 **rule macro predicate**도 같은 발상으로, 자주 반복되는 복잡한 schema를 새 술어(예: 3항 술어)로 정의해 if-then 규칙을 ground atomic formula(GAF)로 바꿔 추론 효율을 극적으로 올린다 (S20). 단, 두 가지 트레이드오프를 함께 고려하라 — (1) **표현력(expressivity)은 늘지 않고 작성량만 줄며**, (2) 메타 규칙이 **생성하는 logic의 추론 확장성(scalability)을 별도로 검증**해야 한다. 간결한 메타 규칙이 폭발적으로 많은 ground rule을 생성할 수 있기 때문이다 (S12, S20).

### D) 임베딩과 GNN (S1, S8, S12)
- **Word/graph embedding**: 기호를 ML이 처리할 수치로 변환. word embedding은 동시출현(co-occurrence) 횟수로, graph embedding은 random walk로 그래프를 선형 경로로 바꿔 동일 원리로 node embedding 계산 (S1).
- **KG 임베딩(TransE)**: h + r ≈ t. 한계: 노드 수만큼 파라미터, transductive(미학습 노드 불가), 노드 feature 미활용 (S12).
- **GNN**: 이웃 집계(message passing)로 노드별 계산 그래프를 따라 임베딩 학습, inductive(미학습 노드 가능). node/edge/subgraph/graph 수준 task(분류, link prediction, PinSage 추천, Google Maps 교통 예측, 신약 발견)에 폭넓게 적용 (S12).
- **주의**: 신경망에 graph 주입이 항상 도움 되는 건 아니다. graph/non-graph 경로를 함께 두고 attention/voting으로 유해 신호를 선택하지 않게 설계한다 (S12).

### E) 신경-기호 결합(Neuro-symbolic) (S10, S14, S18)
- **QA-GNN(보강)**: 두 가지 혁신으로 구성된다 — (1) LM으로 각 KG 노드의 질문 조건부 관련성을 점수화(language-conditioned KG node scoring)해 무관한 노드를 pruning하거나 가중치를 주고, (2) QA 문맥 노드 z와 KG를 하나의 joint graph(working graph)로 연결해 GNN message passing으로 텍스트와 KG 두 모달리티의 표현을 함께 갱신한다. 후반 단계에서 표현을 합치는 대신 처음부터 joint graph로 묶는 것이 핵심이다. **ablation 결과 joint graph를 쓰지 않으면 약 2%, 노드 스코어링을 제거하면 약 1% 성능이 하락했다.** QA-GNN은 CommonsenseQA/OpenBookQA에서 기존 LM+KG 모델을 능가했다 (S14).
- **상호보완성(보강)**: KG는 사실·반의어·negation 같은 명시적 추론에 강하고(예: postpone↔hasten), LM은 언어 뉘앙스/상식이 필요한 질문(예: universe vs night sky, soup vs water)에 강하다. oracle 실험에서 둘 중 하나라도 맞히면 성공으로 셀 때 성능이 크게 올라, 어느 소스에 의존할지 학습하는 것이 향후 과제다 (S14).
- **동적 규칙 생성**: 정적 KB 대신 neural model(fine-tuned T5)이 추론 시점에 규칙을 동적 생성, neuro-symbolic reasoner(BRAID)에 plug-in해 설명가능성·디버깅성 확보 (S10).
- **설명가능성 + 통계적 강점의 혼합이 미래**: 신경망만으로는 인과성 설명이 어렵다. 온톨로지/그래프DB를 결합하면 데이터에 의미론을 부여해 설명가능성과 reasoning을 확보한다 (S18).

### F) Small data, large knowledge
데이터 규모(billions of triples)만이 아니라 'small data + large knowledge' 차원도 중요하다. 적은 데이터에서 풍부한 추론을 끌어내고 불일치(inconsistency) 없이 일관된 대규모 지식베이스를 키우는 것이 핵심이다(Sherlock Holmes식 지능) (S11, S19). 실무적으로 더 어려운 것은 데이터 규모보다 계산 복잡도(computational complexity)의 분산/병렬화다 (S11).

---

## 8단계: 활용 / 응용(Application & Consumption)

### 사용자 소비/시각화 설계 (S13)
- **노드-엣지 그래프 그림이 정답이라고 가정하지 마라.** 스키마 수준에서는 그래프가 명확하지만, 수백만 인스턴스에는 지도·필터·표가 더 적합하고, KG가 배경에 숨어 화면에 안 보이는 게 나을 때도 있다 (S13).
- 시각화의 목표는 **사용자의 데이터 이해 증폭(amplify understanding)**이다. overview에서 시작해 details on demand로 드릴다운한다(공간 배치→마커→연결/울타리→망막 속성→애니메이션) (S13).
- **질의 인터페이스**: 구조화 질의(문법 기반)는 작고 잘 정의된 도메인에 강하나 확장성이 약하고, 자연어 질의(semantic parsing: executor/grammar/parser/model/learner)는 변형을 다루나 학습 데이터가 병목이다. 50~60% 정확도는 적은 노력으로 가능하나 그 이상은 막대한 엔지니어링이 든다 (S13). 단일 방법 택일이 아니라 키워드 검색·필터·구조화 질의의 조합이 보통 더 효과적이다 (S13, S14).

### 쓰기(Write) 경로 설계 (보강)
지금까지의 소비 논의는 대부분 읽기(read) 경로다. 그러나 **쓰기(write) 접근은 읽기와 다른 인터랙션 기법이 필요하다** (S13). 사용자 환경의 신뢰 특성에 따라 write-path를 다르게 설계하라.

- **적대적(adversarial)·무보상 환경(예: eBay)**: 사용자가 악의적으로 데이터를 조작할 동기가 있고 품질 기여 보상이 없으므로, 직접 수정을 허용하지 말고 **커뮤니티 검증(community validation)** 같은 강건한 기법을 쓴다 (S13).
- **신뢰·인증된 고가치 환경(예: JPMorgan)**: 사용자가 인증되고 데이터 품질에 이해관계가 일치하므로 **직접 값 수정을 허용**할 수 있다 (S13).
- **혼합형(예: Neva)**: 신뢰 사용자에게 수정 제안 권한을 주고, 그 제안을 업스트림(Wikidata)으로 다시 푸시하는 방향을 모색한다 (S13).

write-path는 read-path보다 무결성·악용 방지·권한 모델을 훨씬 까다롭게 요구하므로, '누가 어떤 환경에서 쓰는가'를 먼저 분류한 뒤 설계해야 한다 (S13).

### 평가셋 편향 점검 (보강)
활용 단계에서 모델/시스템 성능을 측정할 때, **표준 dev/test 평가셋은 인기 엔티티(popular entity) 편향**이라 진짜 성능을 가린다 (S8). 따라서 추론 패턴별 부분모집단 슬라이스 평가(subpopulation sliced evaluation)를 별도로 수행하라 — 타입/KG관계/엔티티 버킷별로 나누고, 특히 tail 슬라이스를 따로 측정해 개선이 어디서 오는지(head 암기인지, tail 일반화인지) 파악한다 (S8).

### 산업 응용 패턴 (S11, S17)
- **검색엔진 지식 패널(Knowledge Panel)**: KG에서 사실을 추출해 요약, 엔티티 disambiguation에도 재사용(예: 'Charleston' → 사용자 위치 기반) (S13).
- **연결된 지식 도메인**: 사용자 여정이 이벤트→인물→영화→장소를 가로지르므로 엔티티 간 연결성을 인코딩해야 한다 (S17). taxonomy 계층화 위에서 collaborative filtering으로 추천을 생성한다 (S17).
- **금융 analytics**: 공급망 pathfinding, betweenness로 핵심 공급사 탐지, PageRank로 영향력 투자자 탐지, community detection으로 공동투자 그룹 탐지, GNN으로 유사 기업 탐지 (S11).
- **재무 계산/보고**: rule-based 세금 계산(TurboTax) + 그래프 인터뷰 자동 생성, FIBO 온톨로지로 보고 표준화 (S11).

---

## 9단계: 유지보수 / 진화(Maintenance & Evolution)

지식그래프는 소프트웨어 산출물이므로 실세계·요구사항 변화에 맞춰 지속적으로 변경해야 한다 (S16). 변경 관리 기법은 세 가지로 분류된다 (S16):

- **Schema evolution**: 시스템 불변식(invariant)을 정의·유지하라. 예: 모든 클래스는 root 하위클래스, 비순환, 고아 클래스 금지. 클래스 제거 시 고아가 되는 하위클래스를 root에 재연결, 속성 제거/이름변경은 전체 triple에 전파, 변경 요약을 사용자에게 제공 (S16). 알고리즘적 이슈뿐 아니라 의존 코드·사용자를 깨뜨리지 않는 사회적(social) 이슈도 고려한다 (S16).
- **View maintenance**: 통합 triple 뷰는 base data 변경에 맞춰 materialized view를 갱신해야 한다. 데이터가 크거나 신선도 요구가 엄격하면 전체 재계산 대신 **incremental view maintenance**를 쓴다 (S16).
- **Truth maintenance**: 추론 규칙으로 유도한 결론의 justification을 추적해, 기반 사실/제약이 바뀌면 연쇄 변경을 파악한다(예: 영화관이 접종센터로 용도 변경) (S16).

### Incremental View Maintenance의 메커니즘: differential dataflow (보강)
재귀(recursion)나 임의 길이 경로 탐색이 있는 그래프 질의(연결 요소, 도달성, transitive closure)의 증분 유지는 약 10년 전까지 **난제**였다. 그냥 "delta에 비례한다"가 아니라, 왜 어려웠고 어떻게 풀렸는지가 핵심이다 (S16).

- **왜 어려웠나**: 반복 계산은 한 라운드의 출력이 다음 라운드의 입력이 되므로, 단순히 변경분을 한 번 흘려보내는 것으로는 반복 전체에 걸친 효과를 추적할 수 없었다 (S16).
- **어떻게 풀렸나(differential dataflow)**: 시간을 직선(total order)이 아니라 **(시간, 반복 라운드)의 부분순서(partial order)**로 두고, 변경을 **2차원 격자에서 인덱싱**한다. '컬렉션 = 해당 시점 이하 모든 변경의 합'이라는 식을 부분순서로 일반화하면(Mobius inversion과 관련) 반복 계산의 증분 갱신이 효율적이 된다. 정확성의 핵심은 **아직 발생하지 않은 변경(green dx)을 계산에서 의도적으로 배제**하는 것이다 (S16).
- 변경은 data-time-diff triple 스트림으로 표현하고, 질의는 join/concat/distinct 같은 elemental operator의 dataflow 그래프로 분해되어 key별로 data-parallel하게 증분 구현된다(distinct가 상태 유지 때문에 가장 복잡) (S16).
- 비용이 변경량(delta)에 비례하므로 연결 요소·도달성 갱신이 수십 마이크로초~밀리초 수준으로 빠르다. 단, 변경이 핵심 위치에서 일어나면 작은 입력 변경이 큰 출력 변화를 낳을 수 있고, **변경이 너무 크면 처음부터 재계산이 더 빠를 수 있다** — 신선도 가치 대비 복잡도 트레이드오프로 판단한다(데이터가 작아도 millisecond 신선도가 중요하면 가치 있다) (S16).

### 외부 소스 동기화와 신선도 추적 (S16, S17)
- 외부 소스(Wikidata 등)와 동기화하려면 소스가 변경분을 **CDC(Change Data Capture)** 형태로 제공해야 한다. 단순 dump만 제공하면 이 기법을 못 쓴다 — old/new 스냅샷으로 직접 diff를 계산해야 한다 (S16). CDC로 변경을 노출하면 대역폭 효율 때문에 제공자에게도 이득이라 점차 그 방향으로 가고 있다 (S16).
- **difference graph로 외부 소스의 신선도/변경을 추적하라(보강)**: GDELT는 뉴스 기사를 24시간 후·1주일 후 재크롤링해 재작성·삭제·검열을 실시간으로 포착한다. 중요한 가정 차이가 있다 — **위키피디아와 달리 라이브 웹(live web)에서는 '악의적 수정이 자동으로 되돌려진다'는 가정이 성립하지 않는다** (S17). 따라서 외부 소스를 신뢰할 때 위키식 자동 복구를 가정하지 말고, 주기적 재수집으로 변경을 직접 추적해야 한다. KG 신선도(freshness)는 제품 신뢰를 좌우한다. Neva는 Wikidata 편집 스트림을 구독해 변경 엔티티만 비동기 재인덱싱한다 (S13, S17).

### 진화를 초기 설계에 포함 (S15)
- schema·data·application(SPARQL query) **세 층 모두에 update 계획**을 세우고, update 요구사항을 초기 use case부터 포함시켜라 (S15).
- **empirically-driven 확장**: 전체 도메인을 미리 다 모델링하지 말고, 새 study가 들어와 모르는 term이 나타날 때만 가져와 매핑한다 (S15).

### 대규모 진화 사례: Amazon Product KG의 "Zero to One Billion" (S15)
'100년 프로젝트'를 단계적으로 쪼갠다. 각 단계의 기술 목표가 다르다:
1. **0→1**: high-precision(최소 90% 정밀도) 모델로 정확한 지식 확보. 정확도라는 '1'이 없으면 아무리 큰 규모(0들)도 전부 0이 된다 (S15).
2. **1→1000**: end-to-end pipeline과 AutoML로 모델링 비용 절감 (S15).
3. **1000→1M**: transfer learning으로 모델 수 축소(one-size-fits-all). 카테고리·attribute·언어별 수백만 모델 유지 비용이 핵심 병목이다. category를 조건으로 입력하고 category 예측을 추가 task로 학습하면 **taxonomy-aware 추출로 F-measure 10%p 향상**(앞의 multi-modal 11% 향상과는 별개 수치) (S15).
4. **1M→1B**: high recall과 multi-modal·웹 추출로 수율 향상 (S15).

산업적 성공 여부는 '없으면 일이 불가능한가'와 '기술이 충분히 성숙했는가'로 갈린다. entity linkage/extraction/cleaning/KBQA는 성공적이나 schema mapping/open IE/knowledge fusion/knowledge inference는 아직 성숙도가 낮다 (S15).

---

## 산업 사례별 실전 교훈

### Wikidata / Gene Wiki (커뮤니티 큐레이션) (S1, S6)
- 대규모 고품질 KG는 단일 인물이 아니라 **커뮤니티 협업**으로 구축된다. Library of Congress 등 외부 기관이 동일 Wikidata 식별자로 데이터를 발행해 연결한다 (S1).
- **기술보다 커뮤니티 설득이 가장 큰 장벽**이다. Wikidata 커뮤니티 일부는 ontology의 필요성조차 인정하지 않고, 지원 조직은 자원이 부족하다 (S6).
- 정렬 protocol: community engagement → schema 합의 → ShEx 변환 → bot 정렬 → CI 동기화. 백신을 직접 발견하진 않았지만 재사용 가능한 protocol을 만든 것이 성과다 (S6).

### Google (검색) (S17)
- KG 코어를 순수 결정론적 사실로 한정하고, collaborative filtering·비구조 연관은 별도 레이어에 둔다(명명의 문제) (S17).
- 질의 이해를 **번역 문제(encoder-decoder)**로 다룬다. surface form을 canonical 엔티티 토큰으로 추상화해 새 엔티티/언어에 일반화 (S17).
- 단일 출처에 의존하지 말고 여러 소스(구매 피드, schema.org, 위키, 추출, 큐레이션)를 reconciliation으로 합성한다 (S17).
- **수억 엔티티 규모에서도 사람의 수작업(라벨링, 평가, 큐레이션, 정규화)이 필수**다. 정책(policy)과 지역별 변형(분쟁 지역 지도), 반달리즘 대비 장치가 필요하다 (S17).

### GDELT (전 세계 뉴스 멀티모달) (S17)
- **단일 마스터 데이터 포맷을 강요하지 마라.** 모달리티가 다양해지면 단일 거대 포맷은 붕괴한다. 데이터를 가장 풍부한 raw 형태(JSON blob)로 저장하고 그래프는 런타임에 구성한다 (S17).
- **스토리지가 병목, 그래프 구성은 병목이 아니다.** 압축 저장 후 BigQuery로 런타임에 brute force로 1조 엣지 co-occurrence 그래프를 구성한다 (S17).
- **difference graph로 라이브 웹의 유동성에 대응한다.** 기사 재작성/삭제/검열을 주기적 재크롤링으로 추적하며, 라이브 웹은 위키처럼 악의적 수정이 자동 복구된다는 가정을 하지 않는다 (S17).
- **언어 장벽 제거**: 영어만 보면 놓친다. 2014 에볼라를 현지어로 일찍 포착했으나 번역 역량 부재로 활용 못한 교훈이 152개 언어 모니터링으로 이어졌다 (S17).
- '진실'뿐 아니라 전 세계의 상충하는 프레이밍(parallel realities)을 함께 인코딩한다 (S17).

### Amazon (Product KG) (S15)
- high-precision 우선, 단계적 확장, 모델 수 축소(transfer learning/MoE/HyperNetwork)가 핵심 (S15).
- seller가 직접 attribute를 입력하도록 유도하지만 seller 목표는 판매이지 catalog 관리가 아니어서 크게 성공하지 못했고, 오류 시 수정 요청·심각하면 overwrite를 병행한다 (S15).

### 금융 (JP Morgan, Causality Link, RelationalAI, FIBO) (S7, S11, S12, S18)
- **신뢰성이 절대적인 도메인에서는 '추측'이 부적절**하다. 휴리스틱 매핑은 약하고, correct-on-capture로 클리닝을 회피하는 접근이 유효하다. 핵심은 제약을 hard 규칙이 아닌 soft constraint/prior로 다루는 운영 의미론으로의 전환이며, ETL/TGD/EGD 같은 검증된 문헌을 무시하지 않는 것이다 (S7).
- 외부 상용 데이터(FactSet 공급망, PitchBook 투자)를 구매해 내부 데이터와 통합한다 (S11).
- 인과 KG는 미래에 대한 명시적·설명가능한 모델을 만들며, 인과 링크는 변동성 큰 신호보다 안정적이다. 소스 품질 필터링이 필수다(Twitter 대신 CEO 분기 발표처럼 법적 진실 의무가 강한 소스) (S18).
- 온톨로지 표준화(FIBO)는 데이터 교환의 핵심이다. 제각각 보고하면 규제기관·거래조직 업무가 악몽이 된다 (S11).

### Cyc (37년 경험, top-down) (S20)
- **온톨로지/taxonomy만 공유하면 핵심을 놓친다.** 명시되지 않은 상식(common sense)과 content, context를 함께 공유해야 진짜 통합이 된다. NYT 기사 한 편의 내용을 triple로 표현하면 99.999%를 버리게 된다 (S20).
- **단순 union은 위험하다.** 잘 작동하던 규칙 집합을 그냥 합치면 (a) 용어가 달라 스쳐 지나가는 누락 오류 또는 (b) 같은 용어를 다른 의미로 써서 충돌이 발생한다. context를 명시하고 시스템에 의미를 설명해야 한다 (S20).
- **표현력-효율 trade-off**: epistemological(무엇을 알 것인가)과 heuristic(어떻게 효율적으로 추론할 것인가)을 분리(EL/HL 이중 표현 + 번역기)하라 (S20).
- **메타지식과 rule macro predicate로 효율을 확보하라.** 자주 반복되는 schema는 새 술어로 만들어 규칙을 GAF로 바꾸고, 무수한 inference parameter 대신 경험적으로 충분한 소수 조합으로 단순화한다 (S20).
- **과도한 표준화를 피하라.** 기존 표준(URI 네이밍, owl:sameAs)의 좋은 부분에서 출발하되 바퀴를 다시 발명하지 마라 (S20).

---

## "처음 구축한다면" 단계별 실행 체크리스트

1. **Use case와 competency questions를 먼저 작성한다.** KG가 답해야 할 구체적 질문 목록을 만들고, 거기서 범위·평가기준·종료 시점을 도출한다 (S15). 사용자 페르소나와 소비 모드(push/pull, known/unknown)를 정의하고, 정의 단계 동안 프로토타입을 user-centered design 관점에서 반복적으로 보여준다 (S2, S13).
2. **도메인 sweet spot인지 판단한다.** 스키마 단순(5~10 타입) + 거대 레코드 + 흥미로운 관계면 적합. 비이진 관계나 값 중심 데이터면 관계형도 고려한다 (S3, S7).
3. **프라이버시/거버넌스 정책을 정한다.** 공개 데이터만 다룰지, 사적 데이터는 보호된 접근(FSRDC)/익명화로 처리할지, privacy/security 제어를 모델에 포함할지 결정한다 (S2, S20).
4. **다학제 팀을 구성한다.** 도메인 전문가(겹치는 전문성 2인+), 온톨로지 엔지니어(2인+), 데이터 과학자(R/Python). 1인 작업이 아니다 (S2).
5. **데이터 모델을 결정한다.** 웹 게시·발견·다중소스면 RDF, 폐쇄형·순회 중심이면 Property Graph. 팀 배경도 고려한다 (S3).
6. **기존 vocabulary/온톨로지를 먼저 찾아 재사용한다.** schema.org, FOAF, SKOS, FIBO, BioPortal. 큰 외부 온톨로지는 MIREOT로 필요한 부분만 import한다. 직접 만들기 전에 반드시 검색한다 (S5, S15).
7. **표준 어휘/스키마 채택 동력을 확보한다.** 동종 데이터 제공자에게 마크업 동기(검색 노출 등)를 주고, 커뮤니티 합의를 빠르게 이끌 거버넌스를 마련한다 (S2).
8. **스키마를 설계하되 core/외곽을 분리한다.** core는 제약 최소(재사용 쉽게), 외곽은 자동 확장. restriction은 별도 module로. 단순함 우선, 점진적 modularize (S15). recognition conditions와 inference logic(EMARPL 같은 forward chaining rule)으로 data를 knowledge로 만든다 (S6). reification의 세 목적(비이진 관계/관계 승격/시간의 사물화)을 구분해 적용한다 (S3, S5, S14).
9. **식별자 전략과 provenance를 확정한다.** IRI(또는 자체 고유 ID), owl:sameAs로 동일 객체 연결, provenance 추적 관계를 설계하고 provenance 추적을 시스템에 내장한다 (S2, S5, S7, S15).
10. **데이터를 수집·적재한다(pay-as-you-go).** 구조화 데이터는 Datalog 규칙으로 매핑·적재, 텍스트는 LM/rule/weak supervision으로 추출, 휴리스틱은 후보 제안에만 쓰고 검증은 사람이 한다 (S1, S7, S9).
11. **크라우드소싱으로 지식을 수집한다면 다단계 파이프라인을 설계한다.** (a) 90%+ 통과 자격 검증 UI, (b) 본 수집, (c) 0~3점 reviewer 검토 대시보드와 파일럿 라운드를 둔다. 어휘/차원은 인지심리 문헌+사용자 인터뷰로 lay user가 이해하게 설계하고, 규칙은 specific+general 두 수준의 맥락 기반(contextualized)으로 수집한다 (S10).
12. **엔티티 해소를 단계적으로 수행한다.** blocking(후보 축소) → matching(random forest + active learning) → same-as 링크. tail 엔티티는 타입/KG 관계 신호로 일반화한다 (S7, S8).
13. **통합·품질 관리 루프를 둔다.** 도메인 지식을 soft constraint로 주입한 클리닝(운영 의미론 전환), 확신도 기반 우선순위, 소규모 gold set으로 모델 평가, integrity constraint로 위반 보고 (S7, S12).
14. **저장·쿼리 도구를 incremental하게 도입한다.** 전통적 해법(SQL/검색)이 실패할 때만 그래프 시스템 도입. OLTP면 graph DB, 분석이면 compute engine. 스키마-데이터 동시 질의가 가능하게 설계하고, 저지연 요구는 빌드타임 전처리로 해결한다 (S12, S13, S19).
15. **추론 레이어를 추가한다.** 그래프 기반(centrality/community/pathfinding) + 온톨로지 기반(taxonomic/rule). 선언적으로 작성하고 시스템이 최적화하게 한다. 메타지식/메타프로그래밍과 rule macro predicate로 반복 schema를 새 술어로 추상화해 작성량과 추론 비용을 줄이되, 생성된 logic의 추론 확장성을 함께 검증한다. 필요하면 GNN/neuro-symbolic(QA-GNN) 결합 (S11, S12, S14, S20).
16. **소비/쓰기 인터페이스를 설계한다.** 노드-엣지 그림을 강요하지 말고 overview → details on demand. 키워드/필터/구조화/자연어 질의의 조합 (S13). 쓰기 경로는 환경 특성에 맞춘다 — 적대적·무보상 환경은 커뮤니티 검증, 신뢰·인증 환경은 직접 수정/제안 후 업스트림 푸시를 허용한다 (S13).
17. **평가셋 편향을 점검한다.** 표준 dev/test는 인기 엔티티 편향이므로 추론 패턴별 부분모집단 슬라이스(타입/KG관계/엔티티 버킷)와 tail 슬라이스를 별도 측정해 개선 출처를 파악한다 (S8).
18. **human-in-the-loop 피드백 루프와 큐레이션을 설계에 내장한다.** explicit(thumbs)/implicit(클릭) feedback으로 오류를 교정한다. '완전 자동'은 신화다 (S9, S19).
19. **유지보수·진화 계획을 초기부터 세운다.** schema/data/application 세 층 모두에 update 계획, CDC 기반 외부 동기화, incremental view maintenance(differential dataflow), difference graph로 외부 소스 신선도 추적 (S15, S16, S17).

---

## 흔한 함정 / 실패 요인

1. **"완전 자동화" 환상.** 자동 추출만으로 고정밀 KG는 안 나온다(precision ~0.65, recall ~0.51). 수작업 라벨링·검증·큐레이션이 항상 일부 포함된다 (S1, S9, S19).
2. **데이터를 모으기만 하고 의미를 정의하지 않음.** recognition conditions와 inference logic이 없으면 클래스/그래프가 있어도 그것은 data일 뿐 knowledge가 아니다(woman instance 0/11 사례) (S6).
3. **use case 없는 범용 구축.** KG가 끝없이 비대해지고, 시맨틱웹 실패의 주요 원인이었다 (S2, S15).
4. **노드-엣지 시각화가 정답이라는 가정.** 수백만 인스턴스에는 지도·필터·표가 낫고, KG가 숨는 게 나을 때도 있다 (S13).
5. **모든 것을 그래프로 강제.** 비이진 관계(reification 미사용 시 표현 불가)나 값 중심 데이터는 관계형이 적합하다 (S3).
6. **transitive subclass/qualifier를 빼고 질의.** p31/p279*를 빼면 핵심 통계(인간 수)가 틀린다 (S6).
7. **단순 union으로 소스 통합.** 용어 불일치로 인한 누락 또는 동음이의로 인한 충돌이 발생한다. context를 명시해야 한다 (S20).
8. **단일 마스터 포맷 강요.** 멀티모달/다양한 데이터셋에서 단일 거대 포맷은 붕괴한다. raw 저장 + 런타임 구성 (S17).
9. **온톨로지를 과도하게 크고 제약 많게 설계.** 제약이 많으면 재사용이 제한되고, deductive closure 유지에 N제곱 axiom이 필요하다. 기존 vocabulary를 안 찾고 직접 만드는 것은 거의 항상 실수 (S15, S20).
10. **provenance를 기록하지 않음.** 출처 기록 여부가 재사용 성패를 좌우한다. 시스템에 내장하지 않으면 추적 비용이 커진다 (S2, S15).
11. **정밀도 없이 규모만 추구.** high-precision '1'이 없으면 규모(0들)는 무의미하다 (S15).
12. **데이터마다 다른 문법을 무시하고 추출기를 재사용.** 뉴스 본문 학습기는 헤드라인에서 성능 급락 — 반드시 자기 데이터로 학습 (S19).
13. **진화 계획 없이 한 번에 완성하려 함.** schema/data/application 세 층의 변경을 초기 use case에 포함시키지 않으면 stale 데이터가 제품 신뢰를 해친다 (S15, S16).
14. **커뮤니티/조직 설득을 과소평가.** 기술보다 ontology 필요성에 대한 합의 도출이 더 큰 장벽일 수 있다 (S6).
15. **계산 복잡도의 분산/병렬화를 간과.** 실무에서는 데이터 규모보다 복잡도 확장이 더 어렵다 (S11).
16. **신경망만으로 설명가능성/인과성 확보 시도.** 온톨로지/그래프DB 결합으로 의미론을 부여해야 reasoning과 설명이 가능하다 (S18).
17. **federated 환경에서 '어떤 소스로 가야 하는가'를 모르는 채 설계.** 미해결 문제이며 endpoint 신뢰성도 낮다(최대 64% offline) (S4).
18. **인기 엔티티 편향 평가셋만 신뢰.** 표준 dev/test는 인기 엔티티 편향이라 tail 성능을 가린다. 부분모집단 슬라이스 평가가 필요하다 (S8).
19. **라이브 웹 소스가 위키처럼 자동 복구된다고 가정.** 라이브 웹에서는 악의적 수정이 되돌려지지 않으므로 difference graph로 직접 변경을 추적해야 한다 (S17).
20. **메타프로그래밍이 표현력을 늘린다고 오해.** 메타 규칙은 작성량만 줄일 뿐 표현력은 안 늘며, 생성된 logic의 추론 확장성을 별도로 검증하지 않으면 폭발할 수 있다 (S12, S20).

---

## 종합 결론

지식그래프 구축은 정의(use case) → 모델링/온톨로지 → 추출 → 엔티티 해소 → 통합/품질 → 저장/쿼리 → 추론/임베딩 → 활용 → 유지보수의 순환 과정이며, 각 단계마다 RDF vs Property Graph, schema-first vs data-first, 자동추출 vs 큐레이션, 논리 vs ML이라는 트레이드오프를 use case와 정확도 요구 수준에 맞춰 의식적으로 선택해야 한다. 일관되게 반복되는 메시지는 다음과 같다 (S1, S6, S9, S15, S19, S20):

- 그래프 자체가 아니라 **의미(meaning) 정의**가 부가가치다.
- **완전 자동은 없다.** 자동화 + 수작업 + 크라우드소싱의 mixed-mode와 human-in-the-loop가 현실이다.
- **정확도(high-precision)가 규모보다 먼저**다.
- 제약은 hard 규칙이 아니라 **soft constraint/prior로 다루는 운영 의미론**으로 전환하되, 수십 년 검증된 데이터 통합 문헌(ETL, TGD/EGD) 위에서 ML을 결합한다 (S7).
- KG는 **다학제 팀이 use case에서 출발해 점진적으로 키우고 영원히 유지보수하는 소프트웨어 산출물**이다.
- bottom-up 연결('a little semantics goes a long way')과 top-down 의미·상식 설계('big semantics')는 대립이 아니라, **큰 것과 작은 것이 함께 움직일 때 가장 큰 힘**이 나온다 (S20).