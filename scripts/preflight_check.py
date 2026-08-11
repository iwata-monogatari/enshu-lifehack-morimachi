# -*- coding: utf-8 -*-
"""公開前検査（抜本改修指示書 18 フェーズ6 / 20 完了条件）。

検査項目
  1. 内部リンク（存在しないページ・アンカーへのリンク）
  2. 301の対応表と _redirects の整合
  3. canonical / title / description / H1 の有無と重複
  4. 構造化データ（トップ WebSite/Organization/SearchAction、下層 BreadcrumbList）
  5. FAQ構造化データと画面表示の一致
  6. 画面上の内部キー露出（window / tel / note ほか）
  7. リンク文言（助詞終わり・意味が切れる文言）
  8. 緊急・医療・生活困窮ページの営業CTA
  9. 自社CTAの運営会社開示
 10. sitemap.xml の整合（実在・canonical一致・統合先を含まない）
 11. 寺院・神社の件数整合
 12. アクセシビリティの機械チェック（本文16px未満・alt・lang・H1数）
 13. 禁止文言（市役所テンプレート・戸籍届書の押印必須・重複表示）
 14. 空見出し・空セクション
 15. 経過した予定表現
 16. canonical・og:url・サイトマップのパラメータ混入
 17. 未公開台帳の隔離（noindex・sitemap・検索・公開ページからのリンク）
 18. 森町の施設・店舗・農園・史跡台帳

終了コード: 致命的な不整合があれば 1
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

SITE = "https://morimachi.enshu-lifehack.com"
SKIP = {".git", "_cache", "node_modules", "reports", "parts", "scripts",
        "data", ".github", ".claude"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def pages() -> list[Path]:
    out = []
    for p in sorted(ROOT.rglob("*.html")):
        if SKIP & set(p.relative_to(ROOT).parts):
            continue
        if p.name == "404.html":
            continue
        out.append(p)
    return out


def url_of(p: Path) -> str:
    rel = "/" + p.relative_to(ROOT).as_posix()
    return rel[: -len("index.html")] if rel.endswith("index.html") else rel


def strip_tags(s: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", s)).strip()


ALL = {url_of(p): p.read_text(encoding="utf-8") for p in pages()}
REDIRECTS = {}
for line in (ROOT / "_redirects").read_text(encoding="utf-8").splitlines():
    parts = line.split()
    if len(parts) >= 2 and line.startswith("/") and not line.startswith("#"):
        REDIRECTS[parts[0]] = parts[1]


def check_internal_links() -> None:
    print("1. 内部リンク")
    broken = anchors = 0
    for url, html in ALL.items():
        for m in re.finditer(r'href="(/[^"]*)"', html):
            href = m.group(1)
            if href.startswith("//"):
                continue
            path, _, frag = href.partition("#")
            if path.startswith(("/assets/", "/favicon", "/sitemap", "/robots", "/search-index")):
                continue
            if not path:
                continue
            if not path.endswith("/"):
                if (ROOT / path.lstrip("/")).is_file():
                    continue
            if path not in ALL:
                if path in REDIRECTS:
                    warn(f"内部リンクが301経由: {url} → {path}")
                    continue
                err(f"リンク先が存在しない: {url} → {href}")
                broken += 1
                continue
            if frag and f'id="{frag}"' not in ALL[path]:
                err(f"アンカーが存在しない: {url} → {href}")
                anchors += 1
    print(f"   検査 {len(ALL)} ページ / 壊れたリンク {broken} / 不正アンカー {anchors}")


def check_redirects() -> None:
    print("2. 301リダイレクト")
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    merges = {t["href"]: t["merge_target"] for t in topics if t.get("action") == "merge"}
    for src, dst in merges.items():
        if src not in REDIRECTS:
            err(f"_redirects に301が無い: {src}")
        elif REDIRECTS[src] != dst:
            err(f"301の行き先が台帳と違う: {src} → {REDIRECTS[src]}（台帳は {dst}）")
        if src in ALL:
            err(f"統合元のファイルが残っている: {src}")
        if dst not in ALL:
            err(f"統合先が存在しない: {dst}")
    print(f"   統合 {len(merges)} 件を検査")


def check_head() -> None:
    print("3. canonical / title / description / H1")
    titles: dict[str, list[str]] = {}
    descs: dict[str, list[str]] = {}
    for url, html in ALL.items():
        if 'rel="canonical"' not in html:
            err(f"canonical が無い: {url}")
        else:
            c = re.search(r'<link rel="canonical" href="([^"]+)"', html)
            if c and c.group(1) != SITE + url:
                err(f"canonical が自己参照でない: {url} → {c.group(1)}")
        t = re.search(r"<title>(.*?)</title>", html, re.S)
        if not t or not t.group(1).strip():
            err(f"title が無い: {url}")
        else:
            titles.setdefault(strip_tags(t.group(1)), []).append(url)
        d = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
        if not d or not d.group(1).strip():
            err(f"description が無い: {url}")
        else:
            descs.setdefault(d.group(1), []).append(url)
        h1s = re.findall(r"<h1[^>]*>", html)
        if len(h1s) != 1:
            err(f"H1 が {len(h1s)} 個: {url}")
        if 'lang="ja"' not in html:
            err(f"lang=\"ja\" が無い: {url}")
    for value, urls in titles.items():
        if len(urls) > 1:
            err(f"title 重複（{len(urls)}件）: {value} → {urls}")
    for value, urls in descs.items():
        if len(urls) > 1:
            err(f"description 重複（{len(urls)}件）: {value[:40]}… → {urls}")
    print(f"   title {len(titles)} 種 / description {len(descs)} 種")


def check_structured_data() -> None:
    print("4. 構造化データ")
    top = ALL.get("/", "")
    for kind in ("WebSite", "Organization", "SearchAction"):
        if kind not in top:
            err(f"トップに {kind} が無い")
    missing = [u for u, h in ALL.items() if u != "/" and "BreadcrumbList" not in h]
    if missing:
        err(f"BreadcrumbList が無い下層ページ {len(missing)} 件: {missing[:5]}")
    print(f"   下層 {len(ALL) - 1} ページ中 BreadcrumbList 欠落 {len(missing)} 件")


def check_faq_match() -> None:
    print("5. FAQ構造化データと画面表示の一致")
    mismatched = 0
    for url, html in ALL.items():
        m = re.search(r'<!-- FAQ-JSONLD:START --><script type="application/ld\+json">(.*?)</script>',
                      html, re.S)
        if not m:
            continue
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            err(f"FAQ構造化データが壊れている: {url}")
            continue
        jsonld_q = {q["name"].strip() for q in data.get("mainEntity", [])}
        qa = re.search(r'<div class="qa">(.*?)</div>', html, re.S)
        shown_q = {strip_tags(q) for q, _ in
                   re.findall(r"<details><summary>(.*?)</summary>(.*?)</details>",
                              qa.group(1), re.S)} if qa else set()
        if jsonld_q != shown_q:
            err(f"FAQ構造化データが画面と一致しない: {url}"
                f"（JSON-LDのみ {len(jsonld_q - shown_q)} / 画面のみ {len(shown_q - jsonld_q)}）")
            mismatched += 1
    print(f"   不一致 {mismatched} ページ")


def check_raw_keys() -> None:
    print("6. 内部キーの画面露出")
    hits = 0
    for url, html in ALL.items():
        for m in re.finditer(r'<p class="mini"><b>([A-Za-z][A-Za-z0-9_]*)</b>', html):
            err(f"内部キーが画面に出ている: {url} → {m.group(1)}")
            hits += 1
    print(f"   露出 {hits} 箇所")


def check_link_text() -> None:
    print("7. リンク文言")
    bad = 0
    # 明らかに文が途中で切れている助詞。「〜のこと」「〜へ」で終わる名詞句は誤検出になるため除く。
    broken_tail = re.compile(r"(を|に|で|は|が|から|まで|も)$")
    emoji = re.compile(r"[🀀-🫿☀-➿️‍]")
    seen: set[tuple[str, str]] = set()
    for url, html in ALL.items():
        for m in re.finditer(r'<a[^>]+href="(/(?:life|hub|tools|checklist)[^"]*)"[^>]*>([^<]+)</a>',
                             html):
            text = emoji.sub("", strip_tags(m.group(2))).strip()
            if not text or (url, text) in seen:
                continue
            seen.add((url, text))
            if broken_tail.search(text) or len(text) <= 2:
                err(f"意味が途中で切れるリンク文言: {url} → 「{text}」（→ {m.group(1)}）")
                bad += 1
    print(f"   該当 {bad} 箇所")


def check_cta() -> None:
    print("8-9. 営業CTAの配置と開示")
    forbidden_prefixes = (
        "/life/emergency/", "/life/health-medical/",
        "/life/troubles-consult/living-costs-trouble/",
        "/life/troubles-consult/cannot-pay-tax/",
        "/life/troubles-consult/consumer-fraud/",
        "/life/troubles-consult/child-consultation/",
        "/life/housing/public-housing-consultation/",
        "/hub/trouble/",
    )
    banned_words = ["今すぐ売却", "無料査定", "放置すると危険", "すぐお問い合わせ"]
    cta_pages = 0
    for url, html in ALL.items():
        has_cta = any(f'data-track-click="cta_{k}"' in html
                      for k in ("real_estate", "care", "both"))
        if has_cta:
            cta_pages += 1
            if url.startswith(forbidden_prefixes):
                err(f"緊急・医療・困窮ページに営業CTAがある: {url}")
            if "本サイト運営会社" not in html:
                err(f"CTAに運営会社の開示が無い: {url}")
        for word in banned_words:
            if word in html:
                err(f"禁止された煽り表現: {url} → 「{word}」")
    print(f"   CTA掲載 {cta_pages} ページ")


def check_sitemap() -> None:
    print("10. sitemap.xml")
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    paths = [u.replace(SITE, "") for u in locs]
    if len(paths) != len(set(paths)):
        err("sitemap に重複URLがある")
    for p in paths:
        if p not in ALL:
            err(f"sitemap に実在しないURL: {p}")
        if p in REDIRECTS:
            err(f"sitemap にリダイレクト元が入っている: {p}")
    missing = [
        u for u, html in ALL.items()
        if u not in paths
        and not u.startswith("/blog/")
        and not re.search(r'<meta\s+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html, re.I)
    ]
    if missing:
        warn(f"sitemap に載っていない実在ページ {len(missing)} 件: {missing[:8]}")
    print(f"   掲載 {len(paths)} URL / 実在ページ {len(ALL)}")


def check_counts() -> None:
    print("11. 寺院・神社の件数整合")
    for section, data_file, expect_key in (("shrine", "shrines.json", "神社"),
                                           ("temple", "temples.json", "寺院")):
        path = ROOT / "data" / data_file
        if not path.exists():
            warn(f"{data_file} がありません")
            continue
        records = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(records, dict):
            records = records.get("shrines") or records.get("temples") or []
        n = len(records)
        plural = "shrines" if section == "shrine" else "temples"
        detail_pages = [u for u in ALL if u.startswith(f"/{section}/{plural}/")
                        and u != f"/{section}/{plural}/"]
        index_html = ALL.get(f"/{section}/", "")
        stated = re.findall(r"(\d+)\s*(?:社|ヶ寺)", index_html)
        stated_n = int(stated[0]) if stated else None
        if stated_n is not None and stated_n != n:
            err(f"{expect_key}: 一覧本文の件数 {stated_n} と台帳 {n} が不一致")
        print(f"   {expect_key}: 台帳 {n} 件 / 詳細ページ {len(detail_pages)} / 本文表記 {stated_n}")
        if len(detail_pages) != n:
            err(f"{expect_key}: 詳細ページ数 {len(detail_pages)} が台帳 {n} と一致しない")


def check_a11y() -> None:
    print("12. アクセシビリティの機械チェック")
    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    small = [m.group(0) for m in re.finditer(r"font-size:(\d+(?:\.\d+)?)px", css)
             if float(m.group(1)) < 16]
    body_small = [s for s in small if float(s.split(":")[1].rstrip("px")) < 11]
    if body_small:
        warn(f"11px未満の指定が {len(body_small)} 箇所あります（補足テキスト用か確認）")
    noalt = 0
    for url, html in ALL.items():
        for m in re.finditer(r"<img\b[^>]*>", html):
            if "alt=" not in m.group(0):
                err(f"alt が無い画像: {url}")
                noalt += 1
    print(f"   alt欠落 {noalt} 件 / 16px未満のfont-size指定 {len(small)} 箇所（多くは補足文）")


def check_forbidden_terms() -> None:
    """再発しやすい文言を機械的に止める（修正指示書 29 test:content）。"""
    print("13. 禁止文言・テンプレート残り")
    muni = json.loads((ROOT / "data" / "city.json").read_text(encoding="utf-8"))["municipality"]

    # 森町は町。他自治体を正式名称で指す「磐田市役所」等は許可する。
    other_city = re.compile(r"(磐田|袋井|掛川|浜松|菊川|御前崎|湖西|静岡|島田)市役所")
    hits = 0
    for url, html in ALL.items():
        for m in re.finditer(r".{0,12}市役所.{0,12}", html):
            if other_city.search(m.group(0)):
                continue
            err(f"「市役所」が残っている（森町は{muni['office_formal']}）: {url} → …{m.group(0)}…")
            hits += 1

    # 戸籍届書の押印は任意（法務省・2021-09-01〜）
    seal = re.compile(r"(印鑑が必要|印鑑を持参|印鑑を用意|届出人の印鑑)")
    for url, html in ALL.items():
        body = re.sub(r'<!-- SEAL-NOTE -->.*?</p>', "", html, flags=re.S)
        for m in seal.finditer(body):
            around = body[max(0, m.start() - 60):m.end() + 60]
            if any(w in around for w in ("給水届", "印鑑登録", "印鑑証明")):
                continue
            err(f"戸籍届書に押印必須の表現: {url} → …{m.group(0)}…")
            hits += 1

    # 同じ語が隣接して2回出るリンク
    for url, html in ALL.items():
        for m in re.finditer(r"<a [^>]*>(.*?)</a>", html, re.S):
            text = re.sub(r"\s+", " ", strip_tags(m.group(1))).strip()
            words = text.split()
            for i in range(len(words) - 1):
                if words[i] == words[i + 1] and len(words[i]) > 2:
                    err(f"リンク内で同じ語が重複: {url} → 「{text}」")
                    hits += 1
    print(f"   検出 {hits} 件")


def check_empty_sections() -> None:
    """見出しだけあって中身が無いセクションを止める（修正指示書 P0-3）。"""
    print("14. 空見出し・空セクション")
    hits = 0
    for url, html in ALL.items():
        # h2 の区切りで見る。下位見出し(h3)は「中身がある」ことの証拠として扱う。
        for m in re.finditer(r"<h2\b[^>]*>(.*?)</h2>(.*?)(?=<h2\b|</main>)", html, re.S):
            heading, body = strip_tags(m.group(1)), m.group(2)
            visible = strip_tags(re.sub(r"<script.*?</script>", "", body, flags=re.S))
            has_content = re.search(r"<(h3|a|img|input|button|li|p|td)\b", body)
            if heading and not visible and not has_content:
                err(f"見出しの中身が空: {url} → 「{heading}」")
                hits += 1
        for m in re.finditer(r'<span class="label">([^<]*)</span><ul>\s*</ul>', html):
            err(f"中身が空のステップ: {url} → 「{m.group(1)}」")
            hits += 1
    print(f"   検出 {hits} 件")


def check_temporal_claims() -> None:
    """すでに過ぎた日付を「予定」と書いていないか（修正指示書 P0-5）。"""
    print("15. 経過した予定表現")
    today = "2026-08-05"
    era_year = {8: 2026, 9: 2027, 10: 2028}  # 令和
    planned = re.compile(
        r"(令和(\d+)年(\d+)月|(20\d\d)年(\d+)月)[^。<]{0,40}?"
        r"(予定|見込み|改訂作業|準備中|進められている)")
    hits = 0
    for url, html in ALL.items():
        # ブログは日付入りの記録なので対象外（本文に確認日を明記している）
        if url.startswith("/blog/"):
            continue
        for m in planned.finditer(strip_tags(html)):
            if m.group(2):
                year = era_year.get(int(m.group(2)))
                month = int(m.group(3))
            else:
                year, month = int(m.group(4)), int(m.group(5))
            if year is None:
                continue
            if f"{year:04d}-{month:02d}" < today[:7]:
                err(f"すでに過ぎた日付を「予定」と書いている: {url} → 「{m.group(0)[:50]}」")
                hits += 1
    print(f"   検出 {hits} 件")


def check_canonical_params() -> None:
    """canonical・サイトマップ・内部リンクに計測パラメータが混じっていないか（修正指示書14）。"""
    print("16. 正規URLのパラメータ混入")
    hits = 0
    for url, html in ALL.items():
        c = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        if c and "?" in c.group(1):
            err(f"canonical にクエリが入っている: {url} → {c.group(1)}")
            hits += 1
        og = re.search(r'<meta property="og:url" content="([^"]+)"', html)
        if og and "?" in og.group(1):
            err(f"og:url にクエリが入っている: {url} → {og.group(1)}")
            hits += 1
        if c and og and c.group(1) != og.group(1):
            err(f"canonical と og:url が不一致: {url}")
            hits += 1
        for m in re.finditer(r'href="(/[^"]*fga_internal[^"]*)"', html):
            err(f"内部リンクに計測パラメータ: {url} → {m.group(1)}")
            hits += 1
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        if "?" in loc:
            err(f"sitemap にパラメータURL: {loc}")
            hits += 1
    print(f"   検出 {hits} 件")


def check_pending_isolation() -> None:
    """撤回済み・未承認ページが検索発見面へ戻る事故を止める。"""
    print("17. 未公開台帳の隔離")
    phase4_path = ROOT / "data" / "seo-phase4-publication.json"
    phase4 = json.loads(phase4_path.read_text(encoding="utf-8")) if phase4_path.exists() else []
    pending = {
        row["url"] for row in phase4
        if not (
            row.get("publish_ready") is True
            and row.get("human_reviewed") is True
            and row.get("source_validation") == "verified"
            and row.get("uniqueness_validation") == "verified"
            and row.get("visual_validation") == "verified"
        )
    }
    discover_path = ROOT / "data" / "discover-pages.json"
    if discover_path.exists():
        discover = json.loads(discover_path.read_text(encoding="utf-8")).get("pages", [])
        pending |= {
            f'/discover/{row["slug"]}/' for row in discover
            if not (
                row.get("status") == "published"
                and row.get("editor_reviewed") is True
                and row.get("publish_ready") is True
                and row.get("source_validation") == "verified"
                and row.get("uniqueness_validation") == "verified"
                and row.get("visual_validation") == "verified"
            )
        }
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_paths = {u.replace(SITE, "") for u in re.findall(r"<loc>([^<]+)</loc>", sitemap)}
    search_data = json.loads((ROOT / "search-index.json").read_text(encoding="utf-8"))
    search_paths = {row.get("href") for row in search_data}
    public = {url: source for url, source in ALL.items()
              if url not in pending and "noindex" not in source.lower()}
    links_to_pending = []
    for source_url, source in public.items():
        for target in pending:
            if f'href="{target}"' in source:
                links_to_pending.append((source_url, target))
    for target in sorted(pending):
        source = ALL.get(target, "")
        if source and "noindex" not in source.lower():
            err(f"未公開ページにnoindexが無い: {target}")
        if target in sitemap_paths:
            err(f"未公開ページがsitemapに混入: {target}")
        if target in search_paths:
            err(f"未公開ページが検索indexに混入: {target}")
    for source_url, target in links_to_pending[:30]:
        err(f"公開ページから未公開ページへリンク: {source_url} → {target}")
    print(f"   未公開 {len(pending)} URL / 公開面からのリンク {len(links_to_pending)}")


def check_mori_directory() -> None:
    """施設・店舗・農園・史跡台帳のデータと生成HTMLを専用監査へ渡す。"""
    print("18. 森町情報台帳")
    proc = subprocess.run(
        [sys.executable, "scripts/audit_mori_directory.py", str(ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode:
        detail = " / ".join(
            line.strip() for line in (proc.stdout + proc.stderr).splitlines()
            if line.strip().startswith(("ERROR:", "FAIL:"))
        )
        err("森町情報台帳の監査に失敗" + (f": {detail}" if detail else ""))
    else:
        summary = next(
            (line.strip() for line in proc.stdout.splitlines() if line.startswith("PASS:")),
            "PASS",
        )
        print(f"   {summary}")


def main() -> None:
    print(f"公開前検査: {len(ALL)} ページ\n")
    check_internal_links()
    check_redirects()
    check_head()
    check_structured_data()
    check_faq_match()
    check_raw_keys()
    check_link_text()
    check_cta()
    check_sitemap()
    check_counts()
    check_a11y()
    check_forbidden_terms()
    check_empty_sections()
    check_temporal_claims()
    check_canonical_params()
    check_pending_isolation()
    check_mori_directory()

    print("\n" + "=" * 60)
    if warnings:
        print(f"警告 {len(warnings)} 件")
        for w in warnings[:30]:
            print("  ! " + w)
    if errors:
        print(f"\nエラー {len(errors)} 件")
        for e in errors[:60]:
            print("  x " + e)
        if len(errors) > 60:
            print(f"  …ほか {len(errors) - 60} 件")
        sys.exit(1)
    print("エラーなし。公開できます。")


if __name__ == "__main__":
    main()
