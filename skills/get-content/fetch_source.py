#!/usr/bin/env python3
"""get-content: 외부 자료를 긁어 KG 입력용 마크다운으로 저장한다.

기본 경로는 표준 라이브러리(urllib)로 빠르게 받아보고, 막히거나(403/봇차단/JS-only/
본문이 너무 짧음) 빈 본문이면 scrapling 으로 폴백한다. scrapling 은 버전마다 fetcher
이름이 달라(StealthyFetcher / DynamicFetcher / PlayWrightFetcher / Fetcher) 방어적으로
순회 호출한다. 결과는 출처 메타(frontmatter: source_url, captured_at, title, fetched_via)
를 붙여 <out>/sources/<slug>.md 로 저장한다 -> 그대로 kg-design / graphify 입력이 된다.

발견(discover) 보조:
  --search "쿼리"   : DuckDuckGo 검색으로 후보 URL 나열(저장 안 함). title<TAB>url<TAB>snippet.
  --emit-links      : 페이지 저장 후 본문 속 '연관/꼬리 기사' 링크를 추려 출력(snowball 용).

사용:
  python3 fetch_source.py <url> [--out DIR] [--title T] [--min-chars N] [--force-scrapling] [--emit-links]
  python3 fetch_source.py --search "쿼리" [--n 15]
  --out          저장 루트(기본 kg-input). sources/ 하위에 저장.
  --min-chars    본문이 이보다 짧으면 막힌 것으로 보고 scrapling 폴백(기본 600).
  --force-scrapling  urllib 건너뛰고 바로 scrapling.
  --search       검색만 하고 후보 URL 출력(수집 X). --n 으로 개수.
  --emit-links   수집 후 추적할 만한 연관/꼬리 링크를 출력(모델이 골라 다시 수집).
"""
import argparse
import html
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# snowball/검색에서 제외할 도메인(공유·SNS·집계) 및 자산 확장자
_SKIP_HOST = ("facebook.", "twitter.", "x.com", "instagram.", "youtube.", "youtu.be",
              "pinterest.", "linkedin.", "t.me", "kakao", "pf.kakao", "play.google",
              "apps.apple", "/intent/", "share")
_SKIP_EXT = (".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
             ".pdf", ".zip", ".mp4", ".mp3", ".woff", ".woff2")


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


def ddg_search(query, n=12):
    """DuckDuckGo HTML 검색 -> [(title, url, snippet)]. uddg redirect 자동 디코드."""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    try:
        raw = fetch_urllib(url)
    except Exception as e:
        print(f"[검색 실패] {e} (쿼리 변형 / 잠시 후 재시도)", file=sys.stderr)
        return []
    titles = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', raw, re.I | re.S)
    snips = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', raw, re.I | re.S)
    out = []
    for i, (href, title) in enumerate(titles):
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        m = re.search(r"uddg=([^&]+)", href)
        real = urllib.parse.unquote(m.group(1)) if m else href
        if real.startswith("//"):
            real = "https:" + real
        snip = ""
        if i < len(snips):
            snip = html.unescape(re.sub(r"<[^>]+>", "", snips[i])).strip()[:160]
        out.append((title, real, snip))
        if len(out) >= n:
            break
    return out


def extract_trail_links(raw, base_url, cap=15):
    """본문 raw HTML에서 추적할 만한 연관/꼬리 링크를 추린다.
    '관련기사·원문·출처' 텍스트 또는 같은 도메인 기사형 경로를 우선순위로."""
    seen, prio, rest = set(), [], []
    base_host = urllib.parse.urlparse(base_url).netloc
    for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', raw, re.I | re.S):
        href = urllib.parse.urljoin(base_url, m.group(1))
        low = href.lower()
        if not low.startswith("http"):
            continue
        if any(low.endswith(e) for e in _SKIP_EXT):
            continue
        host = urllib.parse.urlparse(href).netloc
        if any(s in low for s in _SKIP_HOST):
            continue
        if href in seen:
            continue
        seen.add(href)
        text = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()[:60]
        is_related = bool(re.search(r"관련|기사|뉴스|원문|출처|이전|다음|연관|related|source|story", text, re.I))
        same_article = (host == base_host) and bool(re.search(r"/\d{3,}|news|article|view|read|story|post|/\d{4}/", low))
        (prio if (is_related or same_article) else rest).append((href, text or "(no text)"))
    return (prio + rest)[:cap]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--search", default=None, metavar="QUERY", help="검색만(저장X) 후보 URL 출력")
    ap.add_argument("--n", type=int, default=12, help="검색 결과 개수")
    ap.add_argument("--emit-links", action="store_true", help="수집 후 연관/꼬리 링크 출력")
    ap.add_argument("--out", default="kg-input")
    ap.add_argument("--title", default=None)
    ap.add_argument("--min-chars", type=int, default=600)
    ap.add_argument("--force-scrapling", action="store_true")
    args = ap.parse_args()

    # --- discover 모드: 검색만 ---
    if args.search:
        results = ddg_search(args.search, args.n)
        if not results:
            print("(검색 결과 없음 — 쿼리 변형 또는 `site:<도메인>` 지정 시도)")
        for title, url, snip in results:
            print(f"{title}\t{url}\t{snip}")
        return

    if not args.url:
        ap.error("url 또는 --search 중 하나는 필요하다.")

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

    # --- snowball: 연관/꼬리 링크 출력 ---
    if args.emit_links:
        if raw:
            links = extract_trail_links(raw, args.url)
            if links:
                print("TRAIL LINKS (연관/꼬리 — 가치있는 것만 골라 다시 수집):")
                for href, txt in links:
                    print(f"  {href}\t{txt}")
            else:
                print("TRAIL LINKS: (없음)")
        else:
            print("TRAIL LINKS: (scrapling 경로라 raw HTML 없음 — --search로 후속 검색 권장)", file=sys.stderr)


if __name__ == "__main__":
    main()
