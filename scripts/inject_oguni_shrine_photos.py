#!/usr/bin/env python3
"""小國神社の第1期ガイドへ提供写真を冪等に反映する。"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "shrine" / "shrines" / "s4410001" / "index.html"
PHOTO_DIR = PAGE.parent
IMAGE_URL = (
    "https://morimachi.enshu-lifehack.com/shrine/shrines/"
    "s4410001/oguni-shrine-main-hall.jpg"
)

PHOTOS = {
    "oguni-shrine-main-hall.jpg",
    "oguni-shrine-approach.jpg",
    "oguni-shrine-pond-bridge.jpg",
    "oguni-shrine-map.jpg",
}

STYLE = """<!-- OGUNI-PHOTOS:STYLE --><style>
.oguni-photo{margin:1.6rem 0 0}
.oguni-photo img{display:block;width:100%;height:auto;border-radius:18px;box-shadow:0 12px 30px rgba(28,46,36,.16)}
.oguni-photo figcaption{margin:.75rem .25rem 0;color:#526058;line-height:1.75}
.oguni-hero-photo{margin:0}
.oguni-hero-photo img{aspect-ratio:16/9;object-fit:cover;object-position:center 44%;border-radius:18px 18px 0 0}
@media(max-width:680px){.oguni-photo img{border-radius:12px}.oguni-hero-photo img{aspect-ratio:4/3;border-radius:12px 12px 0 0}}
</style><!-- OGUNI-PHOTOS:STYLE-END -->"""

HERO = (
    '<figure class="oguni-photo oguni-hero-photo">'
    '<img src="oguni-shrine-main-hall.jpg" '
    'alt="静岡県森町の小國神社拝殿を正面の参道から望む境内写真" '
    'width="2048" height="1536" loading="eager" fetchpriority="high" decoding="async">'
    '<figcaption>小國神社の拝殿と正面参道。催事や整備により境内の通行条件は変わるため、'
    '現地の掲示と誘導を優先してください。</figcaption></figure>'
)

REPLACEMENTS = {
    "approach-and-forest.svg": (
        '<figure class="oguni-photo"><img src="oguni-shrine-approach.jpg" '
        'alt="小國神社の杉木立に囲まれた参道から拝殿方向を望む写真" '
        'width="2048" height="1536" loading="lazy" decoding="async">'
        '<figcaption>杉木立に囲まれた参道。境内は見どころを拾う順路ではなく、鳥居、参道、'
        '手水、拝礼を通じて心を整える場所です。</figcaption></figure>'
    ),
    "shrine-history.svg": (
        '<figure class="oguni-photo"><img src="oguni-shrine-pond-bridge.jpg" '
        'alt="小國神社境内の事待池と朱色の橋を鎮守の森とともに望む写真" '
        'width="2048" height="1536" loading="lazy" decoding="async">'
        '<figcaption>境内の事待池と朱色の橋。池の周囲や橋は参拝者が行き交うため、通路をふさがず、'
        '現地の立入・撮影案内に従って見学します。</figcaption></figure>'
    ),
    "check-before-visit.svg": (
        '<figure class="oguni-photo"><img src="oguni-shrine-map.jpg" '
        'alt="小國神社の境内案内図が描かれた現地案内板の写真" '
        'width="2048" height="1536" loading="lazy" decoding="async">'
        '<figcaption>境内入口付近の案内図は、当日の参拝動線を把握する助けになります。交通や駐車は'
        '「前に行けた方法」ではなく、公式発表、当日運行、現地誘導の順に新しい情報を優先します。'
        '</figcaption></figure>'
    ),
}


def replace_figure(source: str, old_image: str, new_figure: str) -> str:
    pattern = r"<figure><img\b[^>]+src=\"" + re.escape(old_image) + r"\".*?</figure>"
    return re.sub(pattern, new_figure, source, count=1, flags=re.S)


def main() -> None:
    missing = sorted(name for name in PHOTOS if not (PHOTO_DIR / name).exists())
    if missing:
        raise SystemExit("小國神社の写真が不足しています: " + ", ".join(missing))

    source = PAGE.read_text(encoding="utf-8")
    original = source

    if "<!-- OGUNI-PHOTOS:STYLE -->" not in source:
        source = source.replace("</head>", STYLE + "</head>", 1)
    if '<figure class="oguni-photo oguni-hero-photo">' not in source:
        source = source.replace('<div class="hero-body">', HERO + '<div class="hero-body">', 1)

    for old_image, new_figure in REPLACEMENTS.items():
        source = replace_figure(source, old_image, new_figure)

    source = source.replace(
        "公式発表が見つからない可変情報は未確認として残します。",
        "公式発表が見つからない可変情報は掲載を見送り、根拠を確認できた時点で更新します。",
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
    source = source.replace('"dateModified":"2026-08-09"', '"dateModified":"2026-08-10"')
    if '"image":"' not in source.split("</script>", 1)[0]:
        source = source.replace(
            '"url":"https://morimachi.enshu-lifehack.com/shrine/shrines/s4410001/",',
            f'"url":"https://morimachi.enshu-lifehack.com/shrine/shrines/s4410001/",'
            f'"image":"{IMAGE_URL}",',
            1,
        )

    if source == original:
        print("小國神社の写真は反映済みです")
        return
    PAGE.write_text(source, encoding="utf-8", newline="\n")
    print("小國神社の提供写真4点を反映しました")


if __name__ == "__main__":
    main()
