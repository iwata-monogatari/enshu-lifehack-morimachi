#!/usr/bin/env python3
"""社寺の提供写真から表示用WebPを生成し、HTMLをresponsive画像へ更新する。"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIRS = [
    ROOT / "shrine" / "shrines" / "s4410001",
    ROOT / "shrine" / "shrines" / "s4410002",
    ROOT / "shrine" / "shrines" / "s4410003",
    ROOT / "shrine" / "shrines" / "s4410008",
    ROOT / "temple" / "temples" / "t22",
]
PAGES = [
    ROOT / "shrine" / "shrines" / "index.html",
    ROOT / "temple" / "temples" / "index.html",
    ROOT / "scripts" / "generate_shrine_pages.py",
    ROOT / "scripts" / "generate_temple_pages.py",
    *(folder / "index.html" for folder in PHOTO_DIRS),
]
WIDTHS = (480, 800, 1200)


def variant_name(src: str, width: int) -> str:
    return re.sub(r"\.jpg$", f"-{width}.webp", src, flags=re.I)


def generate_variants() -> tuple[int, int]:
    count = 0
    total = 0
    for folder in PHOTO_DIRS:
        for source in sorted(folder.glob("*.jpg")):
            with Image.open(source) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
                for width in WIDTHS:
                    height = round(image.height * width / image.width)
                    output = source.with_name(variant_name(source.name, width))
                    resized = image.resize((width, height), Image.Resampling.LANCZOS)
                    resized.save(output, "WEBP", quality=78, method=6)
                    count += 1
                    total += output.stat().st_size
    return count, total


def responsive_tag(match: re.Match[str], page: Path) -> str:
    tag = match.group(0)
    src = match.group("src")
    if "srcset=" in tag or not any((folder / Path(src).name).with_suffix(".jpg").exists() for folder in PHOTO_DIRS):
        return tag
    if (page.name == "index.html" and page.parent.name in {"shrines", "temples"}) or page.name in {
        "generate_shrine_pages.py",
        "generate_temple_pages.py",
    }:
        sizes = "(max-width:720px) 50vw, 440px"
    elif 'loading="eager"' in tag:
        sizes = "(max-width:720px) 100vw, 876px"
    else:
        sizes = "(max-width:720px) 100vw, 285px"
    srcset = ", ".join(f"{variant_name(src, width)} {width}w" for width in WIDTHS)
    replacement = tag.replace(
        f'src="{src}"',
        f'src="{variant_name(src, 1200)}" srcset="{srcset}" sizes="{sizes}"',
        1,
    )
    replacement = replacement.replace('width="2048" height="1536"', 'width="1200" height="900"')
    return replacement


def update_pages() -> int:
    changed = 0
    pattern = re.compile(r'<img\b(?=[^>]*\bsrc="(?P<src>[^"]+\.jpg)\")[^>]*>', re.I)
    for page in PAGES:
        source = page.read_text(encoding="utf-8")
        updated = pattern.sub(lambda match: responsive_tag(match, page), source)
        if updated != source:
            page.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1
    return changed


def main() -> None:
    variants, total = generate_variants()
    pages = update_pages()
    print(f"WebP variants={variants} total={total / 1024 / 1024:.2f}MB updated_pages={pages}")


if __name__ == "__main__":
    main()
