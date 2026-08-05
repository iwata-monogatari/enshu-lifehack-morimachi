# -*- coding: utf-8 -*-
"""全ページ共通のSEO基盤を整える（抜本改修指示書 12.1 / 12.2 / 19 P0）。

  1. 全下層ページに BreadcrumbList 構造化データを付与（既存のパンくずHTMLから生成）
  2. トップに WebSite / Organization / SearchAction を付与
  3. canonical・OGP・Twitter Card の欠落を補う
  4. 二重に読み込まれているアクセス解析タグを1本に戻す

冪等：マーカー（SEO-COMMON:START/END）で管理し、再実行しても増殖しない。
"""
from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

CITY = json.loads((ROOT / "data" / "city.json").read_text(encoding="utf-8"))
SITE = CITY["site_url"].rstrip("/")
SITE_NAME = CITY["site_name"]

START, END = "<!-- SEO-COMMON:START -->", "<!-- SEO-COMMON:END -->"
SKIP = {".git", "_cache", "node_modules", "reports", "parts", "scripts", ".github", ".claude"}

TRACKER_RE = re.compile(
    r'<script defer src="https://fujigaoka-analytics-worker[^"]*"[^>]*></script>')
CRUMB_RE = re.compile(r'<p class="breadcrumb">(.*?)</p>', re.S)
CRUMB_ITEM_RE = re.compile(r'<a href="([^"]+)"[^>]*>(.*?)</a>|(?<=／)([^／<]+)$', re.S)


def strip_tags(s: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", s)).strip()


# 構造化データのnameには装飾絵文字を含めない（画面表示の絵文字はAGENTS.mdどおり残す）
EMOJI_PREFIX_RE = re.compile(
    r"^[\U0001F000-\U0001FAFF☀-➿️‍\s]+")


def plain_name(s: str) -> str:
    return EMOJI_PREFIX_RE.sub("", strip_tags(s)).strip()


def breadcrumb_items(html: str, page_url: str, title: str) -> list[dict] | None:
    m = CRUMB_RE.search(html)
    if not m:
        return None
    inner = m.group(1)
    items = []
    for chunk in inner.split("／"):
        chunk = chunk.strip()
        if not chunk:
            continue
        link = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', chunk, re.S)
        if link:
            items.append({"name": plain_name(link.group(2)), "url": SITE + link.group(1)})
        else:
            name = plain_name(chunk)
            if name:
                items.append({"name": name, "url": SITE + page_url})
    if len(items) < 2:
        return None
    # 末尾（現在地）は必ず自ページURLにそろえる
    items[-1]["url"] = SITE + page_url
    if not items[-1]["name"]:
        items[-1]["name"] = title
    return items


def breadcrumb_jsonld(items: list[dict]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": it["name"], "item": it["url"]}
            for i, it in enumerate(items)
        ],
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            + "</script>")


def top_jsonld() -> str:
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "静岡県森町ライフハック",
        "alternateName": ["森町ライフハック", "遠州森町ライフハック",
                          "森町ライフハック（遠州ライフハック 森町版）"],
        "url": SITE + "/",
        "inLanguage": "ja",
        "description": "静岡県周智郡森町（遠州森町）の手続きと相談先を、暮らしの困りごとから探せる非公式の生活ナビです。北海道茅部郡森町の情報は扱っていません。",
        "about": {"@type": "Place", "name": "静岡県周智郡森町",
                  "address": {"@type": "PostalAddress", "addressRegion": "静岡県",
                              "addressLocality": "周智郡森町", "addressCountry": "JP"}},
        "publisher": {"@id": SITE + "/#organization"},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": SITE + "/?q={search_term_string}",
            },
            "query-input": "required name=search_term_string",
        },
    }
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": SITE + "/#organization",
        "name": "富士ヶ丘サービス株式会社",
        "url": "https://www.fujigaoka-service.co.jp/",
        "description": "森町ライフハックの運営会社。森町公式・行政機関ではありません。",
        "areaServed": "静岡県周智郡森町",
        "founder": {"@type": "Person", "name": "大石浩之", "url": SITE + "/about/author/"},
    }
    return "".join(
        '<script type="application/ld+json">'
        + json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
        for d in (website, org)
    )


# 内部アクセス用パラメータの処理（修正指示書14）。
# canonical は最初からパラメータなしで出力しているので、ここでやるのは
# 「内部アクセスと記録する」「アドレスバーからパラメータを消す」の2つだけ。
# 解析タグ（defer）より先に実行されるよう head に置く。
INTERNAL_FLAG_JS = (
    "<script>(function(){try{var u=new URL(location.href);"
    "if(u.searchParams.get('fga_internal')==='1'){"
    "sessionStorage.setItem('fga_internal','1');"
    "window.__fgaInternal=true;"
    "u.searchParams.delete('fga_internal');"
    "history.replaceState({},'',u.pathname+(u.search||'')+u.hash);}"
    "else if(sessionStorage.getItem('fga_internal')==='1'){window.__fgaInternal=true;}"
    "}catch(e){}})();</script>"
)


def og_block(url: str, title: str, desc: str, image: str) -> str:
    def meta(prop: str, val: str, name: bool = False) -> str:
        attr = "name" if name else "property"
        return f'<meta {attr}="{prop}" content="{val}">'

    return "".join([
        meta("og:type", "website"),
        meta("og:site_name", SITE_NAME),
        meta("og:locale", "ja_JP"),
        meta("og:title", title),
        meta("og:description", desc),
        meta("og:url", url),
        meta("og:image", image),
        meta("og:image:width", "1200"),
        meta("og:image:height", "630"),
        meta("twitter:card", "summary_large_image", name=True),
        meta("twitter:title", title, name=True),
        meta("twitter:description", desc, name=True),
        meta("twitter:image", image, name=True),
        f'<link rel="canonical" href="{url}">',
    ])


def dedupe_tracker(html: str) -> tuple[str, bool]:
    hits = TRACKER_RE.findall(html)
    if len(hits) <= 1:
        return html, False
    # フッターパーツ内の1本だけを残す
    keep = hits[0]
    html = TRACKER_RE.sub("", html)
    html = html.replace("<!-- PART:footer:END -->", keep + "<!-- PART:footer:END -->", 1)
    if keep not in html:  # フッターパーツが無いページは </body> の直前へ
        html = html.replace("</body>", keep + "</body>", 1)
    return html, True


def process(path: Path) -> dict[str, bool]:
    html = path.read_text(encoding="utf-8")
    original = html
    rel = "/" + path.relative_to(ROOT).as_posix()
    url_path = rel[: -len("index.html")] if rel.endswith("index.html") else rel
    page_url = SITE + url_path
    flags = {"breadcrumb": False, "top": False, "canonical": False, "tracker": False}

    html, flags["tracker"] = dedupe_tracker(html)

    # 判定は「自分が入れたブロックを除いた素のHTML」に対して行う。
    # そうしないと再実行時に、自分が入れた canonical を見て「もうある」と判断し、
    # 空のブロックで上書きして canonical を消してしまう。
    bare = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S)

    title = strip_tags(re.search(r"<title>(.*?)</title>", html, re.S).group(1)) \
        if re.search(r"<title>(.*?)</title>", html, re.S) else SITE_NAME
    desc_m = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
    desc = desc_m.group(1) if desc_m else ""

    blocks: list[str] = []
    if url_path == "/":
        blocks.append(top_jsonld())
        flags["top"] = True
    else:
        items = breadcrumb_items(html, url_path, title)
        if items:
            blocks.append(breadcrumb_jsonld(items))
            flags["breadcrumb"] = True

    if 'rel="canonical"' not in bare:
        image = SITE + "/assets/ogp/site-default.png"
        short = title.split("｜")[0].split(" | ")[0]
        blocks.append(og_block(page_url, short, desc, image))
        flags["canonical"] = True

    blocks.append(INTERNAL_FLAG_JS)
    payload = START + "".join(blocks) + END
    if START in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), payload, html, flags=re.S)
    else:
        html = html.replace("</head>", payload + "</head>", 1)

    if html != original:
        path.write_text(html, encoding="utf-8")
    return flags


def main() -> None:
    totals = {"breadcrumb": 0, "top": 0, "canonical": 0, "tracker": 0, "files": 0}
    for path in sorted(ROOT.rglob("*.html")):
        if SKIP & set(path.relative_to(ROOT).parts):
            continue
        if path.name == "404.html":
            continue
        flags = process(path)
        totals["files"] += 1
        for k, v in flags.items():
            totals[k] += 1 if v else 0
    print(f"対象 {totals['files']} ページ")
    print(f"  BreadcrumbList 付与 : {totals['breadcrumb']}")
    print(f"  トップ構造化データ  : {totals['top']}")
    print(f"  canonical/OGP 補完  : {totals['canonical']}")
    print(f"  解析タグ重複を解消  : {totals['tracker']}")


if __name__ == "__main__":
    main()
