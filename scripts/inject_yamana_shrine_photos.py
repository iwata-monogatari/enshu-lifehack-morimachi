#!/usr/bin/env python3
"""山名神社の第1期ガイドへ提供写真を冪等に反映する。"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "shrine" / "shrines" / "s4410003" / "index.html"
PHOTO_DIR = PAGE.parent
IMAGE_URL = (
    "https://morimachi.enshu-lifehack.com/shrine/shrines/"
    "s4410003/yamana-shrine-main-hall.jpg"
)

PHOTOS = {
    "yamana-shrine-main-hall.jpg",
    "yamana-shrine-torii.jpg",
    "yamana-shrine-dance-stage.jpg",
    "yamana-shrine-cultural-property-sign.jpg",
}

STYLE = """<!-- YAMANA-PHOTOS:STYLE --><style>
.yamana-photo{margin:1.6rem 0 0}
.yamana-photo img{display:block;width:100%;height:auto;border-radius:18px;box-shadow:0 12px 30px rgba(28,46,36,.16)}
.yamana-photo figcaption{margin:.75rem .25rem 0;color:#526058;line-height:1.75}
.yamana-hero-photo{margin:0}
.yamana-hero-photo img{aspect-ratio:16/9;object-fit:cover;object-position:center 48%;border-radius:18px 18px 0 0}
@media(max-width:680px){.yamana-photo img{border-radius:12px}.yamana-hero-photo img{aspect-ratio:4/3;border-radius:12px 12px 0 0}}
</style><!-- YAMANA-PHOTOS:STYLE-END -->"""

HERO = (
    '<figure class="yamana-photo yamana-hero-photo">'
    '<img src="yamana-shrine-main-hall.jpg" '
    'alt="静岡県森町飯田の山名神社拝殿を正面から望む境内写真" '
    'width="2048" height="1536" loading="eager" fetchpriority="high" decoding="async">'
    '<figcaption>森町飯田に鎮座する山名神社の拝殿。参拝や見学では、境内の掲示と'
    '当日の案内を優先してください。</figcaption></figure>'
)

FACT_PHOTO = (
    '<figure class="yamana-photo"><img src="yamana-shrine-cultural-property-sign.jpg" '
    'alt="山名神社天王祭舞楽の由来と国指定重要無形民俗文化財について記した現地説明板" '
    'width="2048" height="1536" loading="lazy" decoding="async">'
    '<figcaption>境内の文化財説明板。由来や指定内容を読む手掛かりになりますが、'
    '当年の祭礼日程や観覧方法は主催者と森町の最新案内を別に確認します。</figcaption></figure>'
)

REPLACEMENTS = {
    "figure-1.svg": (
        '<figure class="yamana-photo"><img src="yamana-shrine-torii.jpg" '
        'alt="山名神社の石鳥居と社号標の先に拝殿を望む入口の写真" '
        'width="2048" height="1536" loading="lazy" decoding="async">'
        '<figcaption>道路側から見た石鳥居と境内入口。参拝時は道路上で立ち止まらず、'
        '車や地域の通行を妨げない位置から境内へ進みます。</figcaption></figure>'
    ),
    "figure-2.svg": (
        '<figure class="yamana-photo"><img src="yamana-shrine-dance-stage.jpg" '
        'alt="山名神社境内に建つ木造の舞殿を斜め前方から望む写真" '
        'width="2048" height="1536" loading="lazy" decoding="async">'
        '<figcaption>境内の舞殿。祭礼当日の使用範囲、観覧場所、撮影の可否は、'
        '保存関係者と現地係員の案内に従ってください。</figcaption></figure>'
    ),
}


def replace_figure(source: str, old_image: str, new_figure: str) -> str:
    pattern = r'<figure><img\b[^>]+src="' + re.escape(old_image) + r'".*?</figure>'
    return re.sub(pattern, new_figure, source, count=1, flags=re.S)


def main() -> None:
    missing = sorted(name for name in PHOTOS if not (PHOTO_DIR / name).exists())
    if missing:
        raise SystemExit("山名神社の写真が不足しています: " + ", ".join(missing))

    source = PAGE.read_text(encoding="utf-8")
    original = source

    if "<!-- YAMANA-PHOTOS:STYLE -->" not in source:
        source = source.replace("</head>", STYLE + "</head>", 1)
    if '<figure class="yamana-photo yamana-hero-photo">' not in source:
        source = source.replace('<div class="hero-body">', HERO + '<div class="hero-body">', 1)
    if "yamana-shrine-cultural-property-sign.jpg" not in source:
        source = source.replace(
            '<section><h2 class="sec">このページの使い方',
            FACT_PHOTO + '<section><h2 class="sec">このページの使い方',
            1,
        )

    for old_image, new_figure in REPLACEMENTS.items():
        source = replace_figure(source, old_image, new_figure)

    source = re.sub(
        r'<img (?!style="width:100%;height:auto")(?=[^>]*src="yamana-shrine-[^"]+\.jpg")',
        '<img style="width:100%;height:auto" ',
        source,
    )

    source = re.sub(
        r'(<meta property="og:image" content=")[^"]+("[^>]*>)',
        rf"\g<1>{IMAGE_URL}\g<2>",
        source,
        count=1,
    )
    source = re.sub(
        r'(<meta name="twitter:image" content=")[^"]+("[^>]*>)',
        rf"\g<1>{IMAGE_URL}\g<2>",
        source,
        count=1,
    )
    source = re.sub(
        r'("dateModified"\s*:\s*")2026-08-09(")',
        r'\g<1>2026-08-10\g<2>',
        source,
    )
    page_url = "https://morimachi.enshu-lifehack.com/shrine/shrines/s4410003/"
    if f'"image":"{IMAGE_URL}"' not in source and f'"image": "{IMAGE_URL}"' not in source:
        source = re.sub(
            r'("url"\s*:\s*"' + re.escape(page_url) + r'",)',
            rf'\g<1> "image":"{IMAGE_URL}",',
            source,
            count=1,
        )

    if source == original:
        print("山名神社の写真は反映済みです")
        return
    PAGE.write_text(source, encoding="utf-8", newline="\n")
    print("山名神社の提供写真4点を反映しました")


if __name__ == "__main__":
    main()
