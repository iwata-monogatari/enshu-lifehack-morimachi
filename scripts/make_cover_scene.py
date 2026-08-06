#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ブログ記事の表紙(760x760)を、記事ごとの情景として描く。

make_cover_square.py は文字だけの表紙を作る保険用スクリプト。
本スクリプトは記事固有のモチーフ(畑・柵・獣・地図・杭など)を図形で描き、
下部に見出し帯を載せる。記事が増えたら SCENES に一つ関数を足す。

使い方: python scripts/make_cover_scene.py <slug>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "blog")
S = 760
BAND_TOP = 592

FONT_BOLD = "C:/Windows/Fonts/meiryob.ttc"
FONT_REGULAR = "C:/Windows/Fonts/meiryo.ttc"


def sky(d):
    for y in range(0, 300):
        t = y / 300
        d.line([(0, y), (S, y)], fill=(int(206 + 40 * t), int(228 + 20 * t), int(240 - 4 * t)))
    d.rectangle([0, 300, S, BAND_TOP], fill=(226, 236, 216))


def mountains(d, base=300):
    d.polygon([(0, base - 40), (90, base - 110), (180, base - 50), (270, base - 120),
               (370, base - 55), (470, base - 125), (570, base - 48), (660, base - 115),
               (760, base - 45), (760, base), (0, base)], fill=(150, 180, 198))
    d.polygon([(0, base - 5), (110, base - 60), (230, base - 10), (350, base - 62),
               (480, base - 8), (610, base - 58), (760, base - 12), (760, base), (0, base)],
              fill=(126, 164, 146))


def cedars(d, xs, base, h=54, color=(63, 107, 82)):
    for x in xs:
        d.polygon([(x, base), (x + h // 3, base - h), (x + 2 * h // 3, base)], fill=color)


def band(d, title_lines, sub):
    d.rectangle([0, BAND_TOP, S, S], fill=(31, 62, 82))
    d.rectangle([0, BAND_TOP, S, BAND_TOP + 8], fill=(214, 168, 60))
    f = ImageFont.truetype(FONT_BOLD, 38)
    y = BAND_TOP + 22
    for line in title_lines:
        d.text((36, y), line, font=f, fill="#ffffff")
        y += 48
    d.text((36, S - 38), sub, font=ImageFont.truetype(FONT_REGULAR, 19), fill="#d7e2e8")


def scene_electric_fence(d):
    sky(d)
    mountains(d)
    cedars(d, [30, 78, 120, 640, 690], 300)
    # 手前の地面
    d.polygon([(0, 330), (760, 318), (760, BAND_TOP), (0, BAND_TOP)], fill=(207, 223, 194))
    # 左：草の伸びた畑
    d.polygon([(0, 322), (340, 314), (322, 470), (0, 486)], fill=(150, 170, 82))
    for i in range(14):
        x = 14 + i * 24
        d.line([(x, 484 - i * 2), (x + 6, 420 - i * 2)], fill=(108, 127, 51), width=3)
    # 獣道
    d.polygon([(250, 322), (340, 430), (470, 500), (430, 520), (300, 448), (214, 330)],
              fill=(196, 180, 147))
    # イノシシ（右向き）
    for x in (250, 276, 306, 328):
        d.line([(x, 384), (x - 4, 416)], fill=(74, 61, 49), width=9)
    d.ellipse([232, 338, 344, 392], fill=(107, 90, 73))
    d.polygon([(330, 348), (386, 362), (376, 380), (326, 384)], fill=(91, 75, 60))
    d.ellipse([376, 362, 392, 378], fill=(122, 103, 84))
    d.polygon([(330, 344), (322, 322), (346, 340)], fill=(74, 61, 49))
    d.ellipse([358, 356, 366, 364], fill=(31, 26, 21))
    d.line([(234, 350), (216, 336)], fill=(74, 61, 49), width=5)
    # シカ（左向き）
    for x in (128, 150, 178, 196):
        d.line([(x, 380), (x, 420)], fill=(122, 95, 63), width=7)
    d.ellipse([116, 340, 210, 386], fill=(154, 122, 85))
    d.polygon([(126, 348), (96, 300), (114, 296), (140, 344)], fill=(154, 122, 85))
    d.ellipse([84, 282, 118, 308], fill=(138, 108, 73))
    d.line([(100, 286), (86, 254)], fill=(122, 95, 63), width=5)
    d.line([(88, 268), (70, 262)], fill=(122, 95, 63), width=4)
    d.line([(108, 284), (120, 256)], fill=(122, 95, 63), width=5)
    d.line([(116, 268), (134, 260)], fill=(122, 95, 63), width=4)
    d.ellipse([90, 290, 98, 298], fill=(36, 28, 19))
    d.ellipse([160, 350, 172, 360], fill=(224, 212, 190))
    d.ellipse([182, 356, 194, 366], fill=(224, 212, 190))
    # 右：柵で囲われた畑
    d.polygon([(400, 318), (760, 310), (760, 452), (392, 464)], fill=(118, 166, 84))
    for i in range(4):
        d.line([(396 + i, 348 + i * 30), (760, 340 + i * 30)], fill=(77, 128, 54), width=3)
    for x in (404, 492, 580, 668, 756):
        d.line([(x, 478), (x, 372)], fill=(79, 90, 99), width=6)
    for dy in (0, 30, 60):
        d.line([(404, 392 + dy), (756, 384 + dy)], fill=(216, 99, 44), width=4)
    # 電源装置と危険表示
    d.rectangle([424, 396, 472, 438], fill=(232, 236, 236), outline=(141, 151, 155), width=3)
    d.rectangle([432, 404, 464, 420], fill=(159, 201, 216), outline=(125, 159, 174), width=2)
    d.ellipse([432, 424, 442, 434], fill=(216, 73, 47))
    d.ellipse([452, 424, 462, 434], fill=(63, 145, 82))
    d.line([(448, 372), (448, 396)], fill=(141, 151, 155), width=4)
    d.rectangle([410, 334, 486, 370], fill=(244, 214, 75), outline=(168, 138, 18), width=3)
    d.polygon([(448, 340), (458, 356), (450, 356), (458, 366), (440, 350), (448, 350)],
              fill=(58, 47, 12))
    # 農道と軽トラック
    d.polygon([(70, 616), (250, 486), (700, 478), (760, 570), (760, 616)], fill=(203, 191, 164))
    d.rectangle([470, 512, 610, 558], fill=(238, 241, 238), outline=(152, 161, 166), width=3)
    d.rectangle([470, 512, 526, 558], fill=(222, 229, 229), outline=(152, 161, 166), width=3)
    d.rectangle([480, 520, 516, 542], fill=(188, 211, 221), outline=(143, 165, 174), width=2)
    for cx in (502, 578):
        d.ellipse([cx - 16, 546, cx + 16, 578], fill=(59, 68, 76), outline=(32, 38, 43), width=3)
        d.ellipse([cx - 6, 556, cx + 6, 568], fill=(139, 149, 157))
    band(d, ["使っていない畑ほど、", "獣の通り道になる"], "森町ライフハック／農地・山林・茶畑")


def scene_cadastral(d):
    sky(d)
    mountains(d)
    cedars(d, [660, 704, 34], 300)
    d.polygon([(0, 330), (760, 318), (760, BAND_TOP), (0, BAND_TOP)], fill=(213, 227, 200))
    # 奥：畑と山林の境
    d.polygon([(0, 318), (390, 310), (376, 424), (0, 436)], fill=(126, 172, 92))
    for i in range(4):
        d.line([(0, 340 + i * 24), (384, 332 + i * 24)], fill=(84, 130, 62), width=3)
    d.polygon([(400, 306), (760, 300), (760, 430), (392, 438)], fill=(74, 108, 76))
    for x in range(410, 760, 42):
        d.polygon([(x, 430), (x + 14, 372), (x + 28, 430)], fill=(52, 86, 60))
    # 境界線と杭
    d.line([(392, 300), (368, 470)], fill=(255, 255, 255), width=6)
    d.line([(392, 300), (368, 470)], fill=(216, 99, 44), width=3)
    for y in (330, 380, 434):
        x = 392 - int((y - 300) * 24 / 170)
        d.rectangle([x - 9, y - 26, x + 9, y + 8], fill=(240, 238, 230), outline=(140, 134, 118), width=3)
        d.line([(x - 5, y - 12), (x + 5, y - 12)], fill=(190, 70, 52), width=4)
    # 手前：地籍図を広げた机
    d.polygon([(60, 616), (700, 616), (660, 486), (100, 486)], fill=(160, 140, 108))
    d.polygon([(120, 596), (640, 596), (610, 500), (150, 500)], fill=(250, 246, 234))
    for i in range(1, 5):
        d.line([(150 + i * 8, 500 + i * 24), (612 - i * 6, 500 + i * 24)], fill=(206, 196, 170), width=2)
    for i in range(1, 4):
        d.line([(150 + i * 116, 500), (124 + i * 116, 596)], fill=(206, 196, 170), width=2)
    d.polygon([(300, 512), (452, 510), (462, 566), (292, 570)], fill=(196, 220, 186),
              outline=(120, 150, 112))
    d.line([(292, 570), (300, 512)], fill=(216, 99, 44), width=5)
    d.ellipse([288, 506, 306, 524], fill=(216, 99, 44))
    d.ellipse([446, 504, 464, 522], fill=(216, 99, 44))
    # 虫めがね
    d.ellipse([470, 520, 556, 606], outline=(90, 100, 108), width=9)
    d.ellipse([479, 529, 547, 597], fill=(214, 232, 240))
    d.line([(548, 598), (600, 632)], fill=(90, 100, 108), width=12)
    band(d, ["畑と山の境界は、", "現地に立つ前に確かめる"], "森町ライフハック／農地・山林・茶畑")


SCENES = {
    "20260806-electric-fence-subsidy": scene_electric_fence,
    "20260806-cadastral-survey-boundary": scene_cadastral,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SCENES:
        print("使い方: python scripts/make_cover_scene.py <slug>")
        print("対応する slug: " + " / ".join(sorted(SCENES)))
        return 1
    slug = sys.argv[1]
    img = Image.new("RGB", (S, S), (255, 255, 255))
    SCENES[slug](ImageDraw.Draw(img))
    out = os.path.join(BLOG_DIR, slug, "cover.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "JPEG", quality=88)
    print("生成:", os.path.relpath(out, ROOT).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
