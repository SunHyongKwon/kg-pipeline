#!/usr/bin/env bash
# kg-pipeline SessionStart: 번들 불가 외부 의존성(graphify, scrapling) 설치 점검.
# 설치돼 있으면 조용히, 빠진 것만 한 번 안내한다.
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
