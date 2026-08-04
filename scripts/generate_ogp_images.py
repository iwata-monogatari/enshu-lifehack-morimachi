#!/usr/bin/env python3
"""og:image (1200x630) を全ページ分generateする。

磐田版は categories.json を回すが、森町版の categories.json は136件しか持たず
実ページは155件あるため、life/**/index.html を直接走査して全ページを対象にする。

出力先: assets/ogp/<category_id>/<slug>.png
  /life/housing/sell-house/                -> assets/ogp/housing/sell-house.png
  /life/housing/                           -> assets/ogp/housing/index.png
  /life/troubles-consult/farmland/sell-or-rent/
                                           -> assets/ogp/troubles-consult/farmland-sell-or-rent.png

使い方: python scripts/generate_ogp_images.py [--force]
  既定では出力済みのPNGはスキップする(--force で再生成)
"""
import argparse
import glob
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES_PATH = os.path.join(ROOT, "data", "categories.json")
OUT_DIR = os.path.join(ROOT, "assets", "ogp")
W, H = 1200, 630

FONT_BOLD = "C:/Windows/Fonts/meiryob.ttc"
FONT_REGULAR = "C:/Windows/Fonts/meiryo.ttc"
FONT_EMOJI = "C:/Windows/Fonts/seguiemj.ttf"

BRAND = "森町ライフハック"
DOMAIN = "morimachi.enshu-lifehack.com"

# カテゴリごとの背景グラデーション(左上→右下)。磐田版と同じ配色で系列感を揃える。
CATEGORY_COLORS = {
    "living-soon": ("#0074AE", "#15503C"),
    "start-living": ("#0E8F6B", "#0B5C46"),
    "housing": ("#8A5A2B", "#5C3A18"),
    "family-grow": ("#E0708A", "#A8385A"),
    "play-out": ("#2FA84F", "#1D6B32"),
    "education": ("#3E6FD9", "#26468C"),
    "health-medical": ("#2AA8A0", "#1B6E68"),
    "work-life": ("#5A6B8C", "#38425C"),
    "parents-care": ("#B08840", "#7A5C24"),
    "emergency": ("#D9564A", "#8C2E26"),
    "troubles-consult": ("#7A5CC4", "#4E3782"),
    "end-of-life": ("#5C6670", "#3A4149"),
    "moving-out": ("#3E9BD9", "#256B99"),
}

_MASK = None


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def gradient_mask():
    """対角グラデーションのマスクは全画像で共通なので一度だけ作って使い回す。"""
    global _MASK
    if _MASK is None:
        mask = Image.new("L", (W, H))
        mask.putdata([int(255 * ((x / W) + (y / H)) / 2) for y in range(H) for x in range(W)])
        _MASK = mask
    return _MASK


def make_gradient(c1, c2):
    base = Image.new("RGB", (W, H), hex_to_rgb(c1))
    top = Image.new("RGB", (W, H), hex_to_rgb(c2))
    return Image.composite(top, base, gradient_mask())


def wrap_text(draw, text, font, max_width):
    lines, current = [], ""
    for ch in text:
        trial = current + ch
        if draw.textlength(trial, font=font) > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def extract_title(filepath):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"<title>(.*?)\s*\|", html)
    if m:
        return m.group(1).strip()
    m = re.search(r"<title>(.*?)</title>", html)
    return m.group(1).strip() if m else ""


def page_key(relpath):
    """life/housing/sell-house/index.html -> ('housing', 'sell-house')"""
    parts = relpath.replace(os.sep, "/").split("/")[:-1]  # drop index.html
    cat = parts[1]
    slug = "-".join(parts[2:]) if len(parts) > 2 else "index"
    return cat, slug


def render(cat_id, emoji, title, out_path):
    c1, c2 = CATEGORY_COLORS.get(cat_id, ("#0074AE", "#15503C"))
    img = make_gradient(c1, c2)
    draw = ImageDraw.Draw(img)

    if emoji:
        draw.text((70, 55), emoji, font=ImageFont.truetype(FONT_EMOJI, 90), embedded_color=True)

    title_font = ImageFont.truetype(FONT_BOLD, 64)
    y = 210
    for line in wrap_text(draw, title, title_font, W - 140)[:3]:
        draw.text((70, y), line, font=title_font, fill="#ffffff")
        y += 78

    draw.text((70, H - 90), BRAND, font=ImageFont.truetype(FONT_BOLD, 34), fill="#ffffff")
    draw.text((70, H - 50), DOMAIN, font=ImageFont.truetype(FONT_REGULAR, 24), fill="#e8f0ee")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")


# life/ 以外で og:image が必要なページ（サイト既定＋6つの生活場面ハブ）
EXTRA_IMAGES = [
    ("site-default", "living-soon", "🏯", "森町の手続き・相談先を、困りごとから探す"),
    ("hub-procedures", "start-living", "📄", "手続きしたい"),
    ("hub-family", "family-grow", "👶", "子ども・家族"),
    ("hub-care", "parents-care", "👵", "親・介護"),
    ("hub-property", "housing", "🏠", "家・土地"),
    ("hub-trouble", "emergency", "🆘", "困った・緊急"),
    ("hub-enjoy", "play-out", "🌳", "暮らしを楽しむ"),
]


def render_extras(force):
    made = 0
    for name, palette, emoji, title in EXTRA_IMAGES:
        out_path = os.path.join(OUT_DIR, "%s.png" % name)
        if os.path.exists(out_path) and not force:
            continue
        render(palette, emoji, title, out_path)
        made += 1
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="生成済みPNGも作り直す")
    args = ap.parse_args()

    with open(CATEGORIES_PATH, encoding="utf-8-sig") as f:
        cats = json.load(f)["categories"]
    emoji_of = {c["id"]: c.get("emoji", "") for c in cats}

    targets = sorted(glob.glob(os.path.join(ROOT, "life", "**", "index.html"), recursive=True))
    generated = skipped = 0
    unknown_cat = set()

    for filepath in targets:
        rel = os.path.relpath(filepath, ROOT)
        cat, slug = page_key(rel)
        if cat not in emoji_of:
            unknown_cat.add(cat)
        out_path = os.path.join(OUT_DIR, cat, "%s.png" % slug)
        if os.path.exists(out_path) and not args.force:
            skipped += 1
            continue
        title = extract_title(filepath) or slug
        render(cat, emoji_of.get(cat, ""), title, out_path)
        generated += 1

    extras = render_extras(args.force)
    print("生成 %d 件 / スキップ(既存) %d 件 / 対象 %d ページ" % (generated, skipped, len(targets)))
    print("ハブ・サイト既定画像: %d 件" % extras)
    if unknown_cat:
        print("categories.json に無いカテゴリ:", sorted(unknown_cat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
