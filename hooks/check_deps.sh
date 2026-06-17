#!/usr/bin/env bash
# kg-pipeline SessionStart: KG 작업 폴더에서만 외부 의존성(graphify, scrapling) 점검.
# kg-input/ 또는 graphify-out/ 또는 KG-DESIGN.md 가 없으면 이 폴더는 KG 작업과 무관하므로
# 아무 출력 없이 빠진다(전역으로 설치돼도 관계없는 세션을 시끄럽게 하지 않는다).
if [ ! -d kg-input ] && [ ! -d graphify-out ] && [ ! -f KG-DESIGN.md ] && [ ! -f graphify-out/KG-DESIGN.md ]; then
  exit 0
fi

miss=""

# graphify: CLI 가 PATH 에 있거나, 어떤 python 인터프리터든 패키지가 import 되면 OK
# (graphify 는 보통 .graphify_python 이 가리키는 전용 인터프리터에서 -m 으로 호출된다)
gok=0
command -v graphify >/dev/null 2>&1 && gok=1
if [ "$gok" -eq 0 ]; then
  for py in python3 python3.14 python3.13 python3.12 python3.11; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import graphify' >/dev/null 2>&1; then
      gok=1; break
    fi
  done
fi
[ "$gok" -eq 0 ] && miss="$miss graphify"

# scrapling: get-content 가 python3 로 fetch_source.py 를 돌리므로 python3 기준
python3 -c 'import scrapling' >/dev/null 2>&1 || miss="$miss scrapling"

if [ -n "$miss" ]; then
  echo "kg-pipeline: 미설치 의존성 -$miss"
  echo "  graphify  (KG 빌드 엔진, 필수):     pipx install graphify   또는  pip install graphify"
  echo "  scrapling (get-content 봇우회 폴백): pip install 'scrapling[fetchers]' && scrapling install"
fi
