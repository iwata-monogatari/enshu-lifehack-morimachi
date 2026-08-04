#!/usr/bin/env python3
"""ブログ記事の表紙バナー(正方形760x760)を生成する。

磐田ブログ(fudosan.atawi.link/blog/)と同じく、記事冒頭に正方形の表紙を置く運用。
写真が用意できない日でも記事を出せるように、文字だけの表紙を機械生成できるようにした。
現地写真がある場合はそちらを優先し、本スクリプトは使わずに cover.jpg を直接置く。

使い方:
  python scripts/make_cover_square.py <slug> "表紙に入れる文字" [--axis mon]
  python scripts/make_cover_square.py --all      # 台帳から未生成のものをまとめて作る
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "blog")
LEDGER = os.path.join(ROOT, "data", "blog-posts.json")
SIZE = 760

FONT_BOLD = "C:/Windows/Fonts/meiryob.ttc"
FONT_REGULAR = "C:/Windows/Fonts/meiryo.ttc"

# 曜日テーマ軸ごとの配色(02戦略編4-3)。記事の性格が一覧で見分けられるようにする。
AXIS_COLORS = {
    "mon": ("#0E8F6B", "#0B5C46"),
    "tue": ("#8A5A2B", "#5C3A18"),
    "wed": ("#7A5CC4", "#4E3782"),
    "thu": ("#2FA84F", "#1D6B32"),
    "fri": ("#3E6FD9", "#26468C"),
    "sat": ("#D9564A", "#8C2E26"),
    "sun": ("#2AA8A0", "#1B6E68"),
}
DEFAULT = ("#0074AE", "#15503C")

_MASK = None


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def gradient(c1, c2):
    global _MASK
    if _MASK is None:
        m = Image.new("L", (SIZE, SIZE))
        m.putdata([int(255 * ((x / SIZE) + (y / SIZE)) / 2) for y in range(SIZE) for x in range(SIZE)])
        _MASK = m
    base = Image.new("RGB", (SIZE, SIZE), hex_to_rgb(c1))
    top = Image.new("RGB", (SIZE, SIZE), hex_to_rgb(c2))
    return Image.composite(top, base, _MASK)


def wrap(draw, text, font, max_width):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        if draw.textlength(trial, font=font) > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def render(slug, text, axis, out_path):
    c1, c2 = AXIS_COLORS.get(axis, DEFAULT)
    img = gradient(c1, c2)
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_BOLD, 52)
    lines = wrap(draw, text, font, SIZE - 120)[:7]
    total_h = len(lines) * 68
    y = max(120, (SIZE - total_h) // 2 - 30)
    for line in lines:
        draw.text((60, y), line, font=font, fill="#ffffff")
        y += 68

    draw.text((60, SIZE - 110), "森町ライフハック", font=ImageFont.truetype(FONT_BOLD, 30), fill="#ffffff")
    draw.text((60, SIZE - 70), "morimachi.enshu-lifehack.com", font=ImageFont.truetype(FONT_REGULAR, 22), fill="#e8f0ee")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=88)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("text", nargs="?")
    ap.add_argument("--axis", default=None)
    ap.add_argument("--all", action="store_true", help="台帳から未生成のcover.jpgをまとめて作る")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.all:
        with open(LEDGER, encoding="utf-8-sig") as f:
            posts = json.load(f)["posts"]
        made = 0
        for p in posts:
            out = os.path.join(BLOG_DIR, p["slug"], "cover.jpg")
            if os.path.exists(out) and not args.force:
                continue
            render(p["slug"], p["title"], p.get("axis"), out)
            made += 1
            print("生成:", os.path.relpath(out, ROOT).replace(os.sep, "/"))
        print("表紙 %d 件を生成" % made)
        return 0

    if not args.slug or not args.text:
        ap.error("slug と text を指定するか --all を使ってください")
    out = os.path.join(BLOG_DIR, args.slug, "cover.jpg")
    if os.path.exists(out) and not args.force:
        print("既に存在します(--force で上書き):", out)
        return 0
    print("生成:", render(args.slug, args.text, args.axis, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
