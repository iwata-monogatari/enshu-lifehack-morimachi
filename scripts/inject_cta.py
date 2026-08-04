#!/usr/bin/env python3
"""data/pages.json の格付けと data/cta-rules.json に従ってCTAブロックを注入する。

磐田版の inject_cv_startliving.py は start-living カテゴリ決め打ち＋文言ベタ書きで、
かつ「既に company-strip があるページはスキップ」する作りだった。
森町版は155ページ全てに同一の company-strip が既に入っているため、
そのまま移植すると1ページも更新されない。したがって規則駆動で作り直す。

やること:
  1. 既存の手書き company-strip を検出して撤去する(初回のみ)
  2. 格付けに応じたCTAを <!-- CTA-BLOCK:START/END --> で注入する
  3. cta_type が none のページ(子育て・学校・健康・遊び)にはCTAを描画しない

04修正指示書 A-3 に従い、real_estate / care / both には必ず運営会社の開示文を入れる
(景表法ステルスマーケティング規制)。

使い方: python scripts/inject_cta.py [--check]
"""
import argparse
import html as htmllib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, "data", "pages.json")
RULES = os.path.join(ROOT, "data", "cta-rules.json")

START = "<!-- CTA-BLOCK:START -->"
END = "<!-- CTA-BLOCK:END -->"
MARKER_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)

LEGACY_OPEN = '<div class="company-strip">'
DIV_RE = re.compile(r"<div\b[^>]*>|</div>", re.I)


def find_div_block(src, start_idx):
    """start_idx の <div ...> に対応する </div> の直後位置を返す(入れ子対応)。"""
    depth = 0
    for m in DIV_RE.finditer(src, start_idx):
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return m.end()
        else:
            depth += 1
    return -1


def esc(s):
    return htmllib.escape(s, quote=True)


def render_cta(rule, cta_type):
    """CTAブロックのHTMLを組み立てる。site.css の company-strip 系クラスを再利用する。

    data-track-click はフッターの富士ヶ丘アナリティクスが拾うイベント名。
    UTM(流入元)とクリック(CV手前)を突き合わせられるよう、CTA種別ごとに名前を分ける。
    """
    parts = [
        '<div class="company-strip cta-%s">' % rule["strength"],
        '<h2 class="sec" style="margin-top:0">%s</h2>' % esc(rule["heading"]),
        '<div class="company-grid"><div class="company-card">',
        "<p>%s</p>" % esc(rule["description"]),
        '<a class="official-link" href="%s" target="_blank" rel="noopener" style="margin-top:8px" data-track-click="cta_%s">%s <span>%s</span></a>'
        % (esc(rule["url"]), cta_type, esc(rule["button_text"]), esc(rule["provider"])),
    ]
    if rule.get("secondary_url"):
        parts.append(
            '<a class="official-link" href="%s" target="_blank" rel="noopener" style="margin-top:8px" data-track-click="cta_%s_care">%s <span>%s</span></a>'
            % (esc(rule["secondary_url"]), cta_type, esc(rule["secondary_button_text"]), esc(rule["provider"]))
        )
    parts.append("</div></div>")
    if rule.get("disclosure"):
        parts.append('<p class="cta-disclosure">※%s</p>' % esc(rule["disclosure"]))
    parts.append("</div>")
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    with open(PAGES, encoding="utf-8-sig") as f:
        pages = json.load(f)
    with open(RULES, encoding="utf-8-sig") as f:
        rules = json.load(f)["rules"]

    changed, removed_legacy, no_anchor, missing = [], 0, [], []
    counts = {}

    for page in pages:
        filepath = os.path.join(ROOT, page["url"].strip("/").replace("/", os.sep), "index.html")
        if not os.path.isfile(filepath):
            missing.append(page["url"])
            continue

        with open(filepath, encoding="utf-8") as f:
            src = f.read()

        rule = rules[page["cta_type"]]
        block = "" if page["cta_type"] == "none" else render_cta(rule, page["cta_type"])
        marker_block = START + block + END
        counts[page["cta_type"]] = counts.get(page["cta_type"], 0) + 1

        if MARKER_RE.search(src):
            new = MARKER_RE.sub(lambda m: marker_block, src, count=1)
        else:
            # 初回: 手書きの company-strip を撤去し、その位置に置き換える
            idx = src.find(LEGACY_OPEN)
            if idx != -1:
                endpos = find_div_block(src, idx)
                if endpos == -1:
                    no_anchor.append(page["url"])
                    continue
                new = src[:idx] + marker_block + src[endpos:]
                removed_legacy += 1
            else:
                # company-strip が無ければ feedback-box の直前へ
                anchor = src.find('<section class="feedback-box"')
                if anchor == -1:
                    anchor = src.find("</main>")
                if anchor == -1:
                    no_anchor.append(page["url"])
                    continue
                new = src[:anchor] + marker_block + src[anchor:]

        if new != src:
            changed.append(page["url"])
            if not args.check:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    verb = "要更新" if args.check else "更新"
    print("対象 %d ページ / %s %d ページ / 旧company-strip撤去 %d 件" % (len(pages), verb, len(changed), removed_legacy))
    print("  CTA種別:", dict(sorted(counts.items())))
    if no_anchor:
        print("挿入位置未検出 %d 件: %s" % (len(no_anchor), no_anchor[:10]))
    if missing:
        print("ファイル未検出 %d 件: %s" % (len(missing), missing[:10]))
    return 1 if (no_anchor or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
