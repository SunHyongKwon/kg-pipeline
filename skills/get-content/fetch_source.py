#!/usr/bin/env python3
"""get-content: 외부 자료를 긁어 KG 입력용 마크다운으로 저장한다.

기본 경로는 표준 라이브러리(urllib)로 빠르게 받아보고, 막히거나(403/봇차단/JS-only/
본문이 너무 짧음) 빈 본문이면 scrapling 으로 폴백한다. scrapling 은 버전마다 fetcher
이름이 달라(StealthyFetcher / DynamicFetcher / PlayWrightFetcher / Fetcher) 방어적으로
순회 호출한다. 결과는 출처 메타(frontmatter: source_url, captured_at, title, fetched_via)
를 붙여 <out>/sources/<slug>.md 로 저장한다 -> 그대로 kg-design / graphify 입력이 된다.

사용:
  python3 fetch_source.py <url> [--out DIR] [--title T] [--min-chars N] [--force-scrapling]
  --out          저장 루트(기본 kg-input). sources/ 하위에 저장.
  --min-chars    본문이 이보다 짧으면 막힌 것으로 보고 scrapling 폴백(기본 600).
  --force-scrapling  urllib 건너뛰고 바로 scrapling.
"""
import argparse
import html
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def slugify(url, title):
    base = title or url
    base = re.sub(r"^https?://", "", base)
    base = re.sub(r"[^0-9A-Za-z가-힣]+", "-", base).strip("-").lower()
    return (base[:60] or "source")


def strip_html(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg|head).*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</(p|div|h[1-6]|li|tr)>", "\n", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_title(raw, fallback):
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    return html.unescape(m.group(1).strip()) if m else fallback


def fetch_urllib(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, errors="replace")


def fetch_scrapling(url):
    """버전 무관 scrapling 폴백. 봇우회 -> JS렌더 -> 기본 순으로 시도."""
    import importlib
    fetchers = importlib.import_module("scrapling.fetchers")
    candidates = [("StealthyFetcher", "fetch"), ("DynamicFetcher", "fetch"),
                  ("PlayWrightFetcher", "fetch"), ("Fetcher", "get")]
    last = None
    for cls_name, meth in candidates:
        cls = getattr(fetchers, cls_name, None)
        if cls is None:
            continue
        fn = getattr(cls, meth, None)
        if fn is None:
            continue
        page = None
        for kw in ({"headless": True}, {}):
            try:
                page = fn(url, **kw)
                break
            except TypeError:
                continue
            except Exception as e:
                last = e
                break
        if page is None:
            continue
        for attr in ("get_all_text", "text"):
            g = getattr(page, attr, None)
            if callable(g):
                try:
                    t = g()
                    if t:
                        return t, cls_name
                except Exception:
                    pass
            elif isinstance(g, str) and g:
                return g, cls_name
        for attr in ("html_content", "body", "html"):
            v = getattr(page, attr, None)
            if isinstance(v, str) and v:
                return strip_html(v), cls_name
    raise RuntimeError(f"scrapling 모든 fetcher 실패: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="kg-input")
    ap.add_argument("--title", default=None)
    ap.add_argument("--min-chars", type=int, default=600)
    ap.add_argument("--force-scrapling", action="store_true")
    args = ap.parse_args()

    raw, title, text, via = None, args.title, None, None

    if not args.force_scrapling:
        try:
            raw = fetch_urllib(args.url)
            title = title or extract_title(raw, args.url)
            text = strip_html(raw)
            via = "urllib"
        except Exception as e:
            print(f"[urllib 실패] {e} -> scrapling 폴백", file=sys.stderr)

    if args.force_scrapling or not text or len(text) < args.min_chars:
        try:
            stext, fetcher = fetch_scrapling(args.url)
            stext = stext if "<" not in stext[:200] else strip_html(stext)
            if not text or len(stext) > len(text):
                text, via = stext, f"scrapling:{fetcher}"
                title = title or args.url
        except ModuleNotFoundError:
            if not text:
                sys.exit("ERROR: 수집 막힘 + scrapling 미설치. `pip install \"scrapling[fetchers]\"; scrapling install` 후 재시도.")
            print("[scrapling 미설치] urllib 결과로 진행", file=sys.stderr)
        except Exception as e:
            if not text:
                sys.exit(f"ERROR: urllib·scrapling 모두 실패: {e}")
            print(f"[scrapling 실패] {e} -> urllib 결과로 진행", file=sys.stderr)

    if not text:
        sys.exit("ERROR: 본문을 가져오지 못함.")

    out = Path(args.out) / "sources"
    out.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.url, title)
    dest = out / f"{slug}.md"
    i = 2
    while dest.exists():
        dest = out / f"{slug}-{i}.md"
        i += 1
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S%z")
    fm = (f"---\nsource_url: {args.url}\ncaptured_at: {stamp}\n"
          f"title: {(title or '').replace(chr(10), ' ')}\nfetched_via: {via}\n---\n\n")
    dest.write_text(fm + text + "\n", encoding="utf-8")
    print(f"저장: {dest}  ({len(text)} chars, via {via})")


if __name__ == "__main__":
    main()
