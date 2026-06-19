#!/usr/bin/env bash
# kg-pipeline SessionStart: KG 작업 폴더에서만 외부 의존성(graphify, scrapling) 점검.
# kg-input/ 또는 graphify-out/ 또는 KG-DESIGN.md 가 없으면 이 폴더는 KG 작업과 무관하므로
# 아무 출력 없이 빠진다(전역으로 설치돼도 관계없는 세션을 시끄럽게 하지 않는다).
if [ ! -d kg-input ] && [ ! -d graphify-out ] && [ ! -f KG-DESIGN.md ] && [ ! -f graphify-out/KG-DESIGN.md ]; then
  exit 0
fi

need=""   # schema-first 기본 경로(Path 1)에 필요
opt=""    # 선택(특정 경로/폴백)

# networkx: schema-first 빌더(build_schema_graph.py)의 modularity 계산 — 기본 경로 필수
python3 -c 'import networkx' >/dev/null 2>&1 || need="$need networkx"

# graphify: bottom-up 빌드 경로(Path 2)/코드 코퍼스용 — 선택. CLI 가 있거나 어떤 python 에서든 import 되면 OK.
gok=0
command -v graphify >/dev/null 2>&1 && gok=1
if [ "$gok" -eq 0 ]; then
  for py in python3 python3.14 python3.13 python3.12 python3.11; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import graphify' >/dev/null 2>&1; then
      gok=1; break
    fi
  done
fi
[ "$gok" -eq 0 ] && opt="$opt graphify"

# scrapling: get-content 봇우회 폴백 — 선택
python3 -c 'import scrapling' >/dev/null 2>&1 || opt="$opt scrapling"

if [ -n "$need" ]; then
  echo "kg-pipeline: 미설치(기본 경로 필요) -$need"
  echo "  networkx  (schema-first 빌더 modularity): pip install networkx"
fi
if [ -n "$opt" ]; then
  echo "kg-pipeline: 미설치(선택) -$opt"
  echo "  graphify  (bottom-up/코드 빌드 경로, 선택): pip install graphifyy  후  graphify install   (※ PyPI 배포명은 graphifyy, y 두 개)"
  echo "  scrapling (get-content 봇우회 폴백):        pip install 'scrapling[fetchers]' && scrapling install"
fi
