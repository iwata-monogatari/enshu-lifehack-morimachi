#!/usr/bin/env python3
"""実家カルテ申込み導線を、関連度の高い2ページへ注入する。

通常のCTAは ``inject_cta.py`` が全ページ共通ルールから生成する。
このスクリプトは、その後段で次の2ページだけを高意欲向けに上書きする。

* 相続した親の家: 選択肢ブロックの直後
* 家を売る前: 「先に結論」の直後

両ページの末尾CTAも同じ訴求にそろえ、スマホだけ固定CTAを表示する。
再実行しても重複しないよう、すべてマーカーで管理する。
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CSS_HREF = "/assets/karte-cta.css?v=20260807a"

EARLY_START = "<!-- KARTE-CTA-EARLY:START -->"
EARLY_END = "<!-- KARTE-CTA-EARLY:END -->"
MOBILE_START = "<!-- KARTE-CTA-MOBILE:START -->"
MOBILE_END = "<!-- KARTE-CTA-MOBILE:END -->"
CSS_START = "<!-- KARTE-CTA-CSS:START -->"
CSS_END = "<!-- KARTE-CTA-CSS:END -->"
CTA_START = "<!-- CTA-BLOCK:START -->"
CTA_END = "<!-- CTA-BLOCK:END -->"

MARKER_PATTERNS = {
    "early": re.compile(re.escape(EARLY_START) + r".*?" + re.escape(EARLY_END), re.S),
    "mobile": re.compile(re.escape(MOBILE_START) + r".*?" + re.escape(MOBILE_END), re.S),
    "css": re.compile(re.escape(CSS_START) + r".*?" + re.escape(CSS_END), re.S),
    "bottom": re.compile(re.escape(CTA_START) + r".*?" + re.escape(CTA_END), re.S),
}

PAGES = {
    "life/end-of-life/inherited-house/index.html": {
        "anchor": "<!-- BRANCH-BLOCK:END -->",
        "utm_content": "inherited_house",
    },
    "life/housing/sell-house/index.html": {
        "anchor": "<!-- INSTANT-HEADER:END -->",
        "utm_content": "sell_house",
    },
}

HEADING = "実家をどうするか、まだ決まっていなくても大丈夫です"
DESCRIPTION = (
    "住所をもとに、道路・境界・農地・登記など、次に確認する順番を宅建士が整理します。"
    "作成料0円、入力約1分。申込みだけで売却依頼にはなりません。"
)
SALE_LINK_LABEL = "森町の家・土地の売却を相談する"
SALE_NOTE = "相続登記前・家財が残った状態・農地や山林を含む場合も相談できます。"
DISCLOSURE = (
    "このご案内は、本サイト運営会社（富士ヶ丘サービス株式会社）の民間サービスです。"
    "ご利用は任意で、森町の制度利用には影響しません。森町役場とは関係ありません。"
)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def form_url(content: str, placement: str) -> str:
    return (
        "https://fudosan.atawi.link/karte/?area=%E6%A3%AE%E7%94%BA"
        "&utm_source=morimachi_lifehack&utm_medium=referral"
        f"&utm_campaign=morimachi_karte&utm_content={content}_{placement}#apply"
    )


def sample_url(content: str, placement: str) -> str:
    return (
        "https://fudosan.atawi.link/karte/sample/"
        "?utm_source=morimachi_lifehack&utm_medium=referral"
        f"&utm_campaign=morimachi_karte&utm_content={content}_{placement}_sample"
    )


def sale_url(content: str, placement: str) -> str:
    """売却をすでに決めている人向けの相談窓口。

    カルテCTAはこの2ページで通常の不動産CTAを上書きするため、
    上書きしたままだと売却意欲が最も高い層の出口が無くなる。
    """
    return (
        "https://fudosan.atawi.link/areas/mori/"
        "?utm_source=morimachi_lifehack&utm_medium=referral"
        f"&utm_campaign=morimachi_sale&utm_content={content}_{placement}_sale"
    )


def render_card(content: str, placement: str) -> str:
    heading_id = f"karte-cta-{content.replace('_', '-')}-{placement}"
    return (
        f'<section class="company-strip cta-strong karte-cta" aria-labelledby="{heading_id}">'
        '<p class="karte-cta-eyebrow">売る前の無料整理</p>'
        f'<h2 id="{heading_id}" class="karte-cta-title">{esc(HEADING)}</h2>'
        f'<p class="karte-cta-copy">{esc(DESCRIPTION)}</p>'
        '<ul class="karte-cta-benefits" aria-label="実家カルテの特徴">'
        '<li>作成料0円</li><li>入力約1分</li><li>売却未定可</li>'
        '</ul>'
        '<div class="karte-cta-actions">'
        f'<a class="karte-cta-primary" href="{esc(form_url(content, placement))}" '
        'target="_blank" rel="noopener" data-track-click="cta_real_estate">'
        '無料で実家カルテを申し込む（約1分）</a>'
        f'<a class="karte-cta-secondary" href="{esc(sample_url(content, placement))}" '
        'target="_blank" rel="noopener" data-track-click="cta_karte_sample">'
        'まずは見本を見る</a>'
        '</div>'
        '<p class="karte-cta-decided">すでに売却を考えている方は、'
        f'<a href="{esc(sale_url(content, placement))}" '
        'target="_blank" rel="noopener" data-track-click="cta_sale_consultation">'
        f'{esc(SALE_LINK_LABEL)}</a>。{esc(SALE_NOTE)}</p>'
        f'<p class="cta-disclosure">※{esc(DISCLOSURE)}</p>'
        '</section>'
    )


def render_mobile(content: str) -> str:
    url = esc(form_url(content, "mobile"))
    return (
        '<div class="mobile-karte-spacer" aria-hidden="true"></div>'
        '<aside class="mobile-karte-cta" aria-label="実家カルテを無料で申し込む">'
        '<div class="mobile-karte-cta-inner">'
        '<span class="mobile-karte-meta">作成料0円・約1分・売却未定可</span>'
        f'<a href="{url}" target="_blank" rel="noopener" '
        'data-track-click="cta_real_estate">無料で申し込む</a>'
        '</div></aside>'
    )


def replace_or_insert(src: str, pattern: re.Pattern[str], block: str, anchor: str, after: bool) -> str:
    if pattern.search(src):
        return pattern.sub(lambda _: block, src, count=1)
    pos = src.find(anchor)
    if pos == -1:
        raise ValueError(f"挿入位置が見つかりません: {anchor}")
    pos = pos + len(anchor) if after else pos
    return src[:pos] + block + src[pos:]


def update_page(path: Path, content: str, anchor: str) -> bool:
    src = path.read_text(encoding="utf-8")
    updated = src

    css_block = CSS_START + f'<link rel="stylesheet" href="{CSS_HREF}">' + CSS_END
    updated = replace_or_insert(updated, MARKER_PATTERNS["css"], css_block, "</head>", after=False)

    early_block = EARLY_START + render_card(content, "early") + EARLY_END
    updated = replace_or_insert(updated, MARKER_PATTERNS["early"], early_block, anchor, after=True)

    bottom_block = CTA_START + render_card(content, "bottom") + CTA_END
    if not MARKER_PATTERNS["bottom"].search(updated):
        raise ValueError(f"末尾CTAが見つかりません: {path.relative_to(ROOT)}")
    updated = MARKER_PATTERNS["bottom"].sub(lambda _: bottom_block, updated, count=1)

    mobile_block = MOBILE_START + render_mobile(content) + MOBILE_END
    updated = replace_or_insert(updated, MARKER_PATTERNS["mobile"], mobile_block, "</body>", after=False)

    if updated == src:
        return False
    path.write_text(updated, encoding="utf-8", newline="")
    return True


def main() -> int:
    changed: list[str] = []
    errors: list[str] = []
    for relative, config in PAGES.items():
        path = ROOT / relative
        try:
            if update_page(path, config["utm_content"], config["anchor"]):
                changed.append("/" + relative.removesuffix("index.html"))
        except (OSError, ValueError) as exc:
            errors.append(str(exc))

    print(f"実家カルテCTA: {len(PAGES)}ページ中 {len(changed)}ページ更新")
    for page in changed:
        print(f"  更新: {page}")
    for error in errors:
        print(f"  エラー: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
