# -*- coding: utf-8 -*-
"""重複ページを統合先へ吸収し、301リダイレクトを設定する（抜本改修指示書 5.3 / 5.4）。

処理:
  1. 統合元の「公式出典リンク」と「Q&A」のうち統合先に無いものを統合先へ移す
     （FAQ構造化データも画面表示と一致させて更新する）
  2. 統合元ディレクトリを削除する
  3. サイト内の統合元URLへのリンクを統合先URLへ張り替える（重複リンクは1本に畳む）
  4. _redirects に 301 を追記する

統合の判断は data/topics_master.json の action / merge_target が唯一の根拠。
実行: python scripts/merge_pages.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

TOPICS = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
MERGES = {t["href"]: t["merge_target"]
          for t in TOPICS if t.get("action") == "merge" and t.get("merge_target")}

FAQ_RE = re.compile(r"<details><summary>(.*?)</summary>(.*?)</details>", re.S)
OFFICIAL_LINK_RE = re.compile(
    r'<a class="official-link" href="(https://[^"]+)"[^>]*>(.*?)</a>', re.S)
QA_BLOCK_RE = re.compile(r'(<div class="qa">)(.*?)(</div>)', re.S)
OFFICIAL_BLOCK_RE = re.compile(
    r'(<h2 class="sec">公式窓口・確認先</h2><div class="official">)(.*?)(</div>)', re.S)
FAQ_JSONLD_RE = re.compile(
    r"(<!-- FAQ-JSONLD:START --><script type=\"application/ld\+json\">)(.*?)"
    r"(</script><!-- FAQ-JSONLD:END -->)", re.S)


def page_path(url: str) -> Path:
    return ROOT / url.strip("/") / "index.html"


def strip_tags(s: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", s)).strip()


def harvest(html: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """(公式リンク, Q&A) を取り出す。"""
    officials = []
    m = OFFICIAL_BLOCK_RE.search(html)
    if m:
        for url, label in OFFICIAL_LINK_RE.findall(m.group(2)):
            if "town.morimachi.shizuoka.jp" in url or "pref.shizuoka" in url:
                officials.append((url, label.strip()))
    qas = []
    qm = QA_BLOCK_RE.search(html)
    if qm:
        for q, a in FAQ_RE.findall(qm.group(2)):
            qas.append((q.strip(), a.strip()))
    return officials, qas


def absorb(target_html: str, officials: list, qas: list) -> tuple[str, int, int]:
    added_o = added_q = 0

    # --- 公式出典リンク ---
    m = OFFICIAL_BLOCK_RE.search(target_html)
    if m:
        existing = {u for u, _ in OFFICIAL_LINK_RE.findall(m.group(2))}
        extra = "".join(
            f'<a class="official-link" href="{url}" target="_blank" rel="noopener">{label}</a>'
            for url, label in officials if url not in existing)
        added_o = extra.count("<a class=")
        if extra:
            target_html = (target_html[:m.end(2)] + extra + target_html[m.end(2):])

    # --- Q&A（画面表示） ---
    qm = QA_BLOCK_RE.search(target_html)
    new_qas = []
    if qm:
        existing_q = {strip_tags(q) for q, _ in FAQ_RE.findall(qm.group(2))}
        for q, a in qas:
            if strip_tags(q) not in existing_q:
                new_qas.append((q, a))
                existing_q.add(strip_tags(q))
        if new_qas:
            extra = "".join(f"<details><summary>{q}</summary>{a}</details>"
                            for q, a in new_qas)
            target_html = target_html[:qm.end(2)] + extra + target_html[qm.end(2):]
            added_q = len(new_qas)

    # --- FAQ構造化データ（画面と完全一致させる／指示書 12.2） ---
    if new_qas:
        fm = FAQ_JSONLD_RE.search(target_html)
        if fm:
            data = json.loads(fm.group(2))
            for q, a in new_qas:
                data["mainEntity"].append({
                    "@type": "Question", "name": strip_tags(q),
                    "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)},
                })
            target_html = (target_html[:fm.start(2)]
                           + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                           + target_html[fm.end(2):])
    return target_html, added_o, added_q


def repoint_links(merges: dict[str, str]) -> int:
    """統合元URLへのリンクを統合先へ張り替え、同一先への重複リンクを1本に畳む。"""
    changed = 0
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports"} & set(
                path.relative_to(ROOT).parts):
            continue
        html = original = path.read_text(encoding="utf-8")
        for src, dst in merges.items():
            html = html.replace(f'href="{src}"', f'href="{dst}"')

        # 「あわせて確認したい…のリンク」内の重複を1本に
        def dedupe(m: re.Match) -> str:
            head, body, tail = m.group(1), m.group(2), m.group(3)
            seen, out = set(), []
            for link in re.findall(r'<a class="official-link"[^>]*>.*?</a>', body, re.S):
                href = re.search(r'href="([^"]+)"', link)
                key = href.group(1) if href else link
                if key in seen:
                    continue
                seen.add(key)
                out.append(link)
            return head + "".join(out) + tail

        html = re.sub(r'(<h2 class="sec">あわせて確認したい[^<]*</h2><div class="official">)(.*?)(</div>)',
                      dedupe, html, flags=re.S)
        # 自分自身へのリンクは外す（統合で自己参照になったもの）
        rel = "/" + path.relative_to(ROOT).as_posix()
        self_url = rel[: -len("index.html")]
        html = re.sub(
            r'<a class="official-link" href="' + re.escape(self_url) + r'"[^>]*>.*?</a>',
            "", html, flags=re.S)

        if html != original:
            path.write_text(html, encoding="utf-8")
            changed += 1
    return changed


def write_redirects(merges: dict[str, str]) -> None:
    path = ROOT / "_redirects"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
             if not ln.startswith("# 2026-08 統合")]
    # 既存の統合行を落としてから作り直す（冪等）
    lines = [ln for ln in lines if not any(ln.startswith(src + " ") for src in merges)]
    lines.append("")
    lines.append("# 2026-08 統合（抜本改修指示書 5.3 / 5.4）: 重複していたページを統合先へ301")
    for src, dst in sorted(merges.items()):
        lines.append(f"{src}  {dst}  301")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"統合対象: {len(MERGES)} ページ\n")
    total_o = total_q = 0
    for src, dst in sorted(MERGES.items()):
        src_path, dst_path = page_path(src), page_path(dst)
        if not src_path.exists():
            print(f"  [済] {src}（すでに統合済み）")
            continue
        if not dst_path.exists():
            print(f"  [!!] 統合先が存在しません: {dst}")
            continue
        officials, qas = harvest(src_path.read_text(encoding="utf-8"))
        merged, n_o, n_q = absorb(dst_path.read_text(encoding="utf-8"), officials, qas)
        total_o += n_o
        total_q += n_q
        print(f"  {src}\n    → {dst}（出典+{n_o} / Q&A+{n_q}）")
        if not args.dry_run:
            dst_path.write_text(merged, encoding="utf-8")
            shutil.rmtree(src_path.parent)

    if args.dry_run:
        print("\n--dry-run のため書き込みはしていません")
        return

    changed = repoint_links(MERGES)
    write_redirects(MERGES)
    print(f"\n統合先へ移した出典 {total_o} 件 / Q&A {total_q} 件")
    print(f"内部リンクを張り替えたページ: {changed}")
    print(f"_redirects に 301 を {len(MERGES)} 行追記しました")


if __name__ == "__main__":
    main()
