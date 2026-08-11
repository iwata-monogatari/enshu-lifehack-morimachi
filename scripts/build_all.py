# -*- coding: utf-8 -*-
"""サイト全体を正しい順序で作り直す。

順序に意味がある:
  生成（寺社・ハブ・トップ）→ 注入（ラベル・CTA・見出しid・親ページ）
  → 共通SEO（canonical/OGP/構造化データ）→ 索引（検索・sitemap・台帳）→ 検査

個別スクリプトを単独で走らせると、あとから生成したページに
canonical や見出しid が付かないまま公開されうるため、
公開前は必ずこのスクリプトを通す。

実行: python scripts/build_all.py [--skip-check]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

STEPS: list[tuple[str, list[str]]] = [
    ("200検索意図の第1期公開対象を確定", [sys.executable, "scripts/build_seo_phase1_manifest.py"]),
    ("森町のよくある100の質問を生成", [sys.executable, "scripts/build_questions.py"]),
    ("寺社データベースの生成", [sys.executable, "scripts/generate_shrine_pages.py"]),
    ("寺院データベースの生成", [sys.executable, "scripts/generate_temple_pages.py"]),
    ("6つの生活場面ハブの生成", [sys.executable, "scripts/build_hubs.py"]),
    ("記事台帳の作成（確認状態・リスク区分）", [sys.executable, "scripts/build_article_ledger.py"]),
    ("関連サイト一覧の生成", [sys.executable, "scripts/build_related_sites.py"]),
    ("森町の施設・店舗・農園・史跡台帳を生成", [sys.executable, "scripts/build_mori_directory.py"]),
    ("森町情報台帳の網羅性監査", [sys.executable, "scripts/audit_mori_directory.py"]),
    ("トップページの生成", [sys.executable, "scripts/build_home.py"]),
    ("ブログ一覧の生成・品質確認", [sys.executable, "scripts/build_blog.py"]),
    ("200本の確認済み原稿を公開台帳へ同期", [sys.executable, "scripts/assemble_discover_drafts.py"]),
    ("静岡県森町200ガイドを生成", [sys.executable, "scripts/build_discover.py"]),
    ("静岡県森町200ガイドを公開前監査", [sys.executable, "scripts/audit_discover.py"]),
    ("検索需要を確認した優先ページのタイトル同期", [sys.executable, "scripts/apply_search_demand_titles.py"]),
    ("個別ガイドの検索説明文を本文から同期", [sys.executable, "scripts/sync_content_descriptions.py"]),
    ("検索者がその場で使える5機能を反映", [sys.executable, "scripts/inject_search_tools.py"]),
    ("検索意図台帳で新設する14ガイドと統合項目を反映", [sys.executable, "scripts/build_search_expansion_pages.py"]),
    ("2026-08-09版200検索意図の全期中核ページを反映", [sys.executable, "scripts/build_seo_full_expansion.py"]),
    ("200ページ改修計画の第3期を反映", [sys.executable, "scripts/build_seo_phase3.py"]),
    ("第4期300検索意図を反映", [sys.executable, "scripts/build_seo_phase4.py"]),
    ("第4期12テーマの判断ハブを生成", [sys.executable, "scripts/build_phase4_hubs.py"]),
    ("公開ページ件数を再集計してトップページへ反映", [sys.executable, "scripts/build_home.py"]),
    ("共通部品の反映（ヘッダー・フッター）", [sys.executable, "scripts/inject_parts.py"]),
    ("既存ガイドから質問ページへの入口を追加", [sys.executable, "scripts/inject_question_links.py"]),
    ("重要11ガイドへ関連質問を集約", [sys.executable, "scripts/inject_priority_question_clusters.py"]),
    ("公式窓口ラベルの日本語化", [sys.executable, "scripts/localize_fact_labels.py"]),
    ("表示テキストの不具合修正", [sys.executable, "scripts/fix_text_defects.py"]),
    ("戸籍届書の押印表現", [sys.executable, "scripts/fix_koseki_seal.py"]),
    ("自治体表現（市役所→役場）と空セクション", [sys.executable, "scripts/fix_municipality_wording.py"]),
    ("経過した予定表現", [sys.executable, "scripts/fix_temporal_claims.py"]),
    ("リンクの重複表示", [sys.executable, "scripts/fix_duplicate_labels.py"]),
    ("301経由の内部リンクを統合先へ直結", [sys.executable, "scripts/fix_internal_redirect_links.py"]),
    ("台帳の facts を公式窓口ブロックへ反映", [sys.executable, "scripts/sync_facts_to_html.py"]),
    ("シェア文の再生成", [sys.executable, "scripts/inject_share_box.py"]),
    ("CTAの出し分け", [sys.executable, "scripts/inject_cta.py"]),
    ("見出しidの付与", [sys.executable, "scripts/add_section_ids.py"]),
    ("親ページの分岐カード", [sys.executable, "scripts/apply_parent_pages.py"]),
    ("実家カルテ申込み導線", [sys.executable, "scripts/inject_karte_cta.py"]),
    ("最終確認日の表現をそろえる", [sys.executable, "scripts/fix_verified_dates.py"]),
    ("県名の付与（北海道森町との区別）", [sys.executable, "scripts/add_prefecture_to_seo.py"]),
    ("検索対象ページの説明文を90〜130字へ最終同期", [sys.executable, "scripts/sync_content_descriptions.py"]),
    ("生活ガイドのOGP画像生成", [sys.executable, "scripts/generate_ogp_images.py"]),
    ("OGP・SNS表示をtitleとdescriptionへ同期", [sys.executable, "scripts/inject_ogp_meta.py"]),
    ("第1期ページのcanonical・OGP重複を正規化", [sys.executable, "scripts/normalize_seo_phase1_meta.py"]),
    ("共通SEO（canonical・OGP・構造化データ）", [sys.executable, "scripts/inject_seo_common.py"]),
    ("小國神社の提供写真を反映", [sys.executable, "scripts/inject_oguni_shrine_photos.py"]),
    ("山名神社の提供写真を反映", [sys.executable, "scripts/inject_yamana_shrine_photos.py"]),
    ("神社・寺院74個別ページの人向け本文監査", [sys.executable, "scripts/audit_sacred_place_pages.py"]),
    ("統合元の検索辞書の引き継ぎ", [sys.executable, "scripts/merge_search_dictionary.py"]),
    ("検索インデックスの生成", ["node", "scripts/build-search-index.mjs"]),
    ("検索テスト", ["node", "scripts/test-search.mjs"]),
    ("検索支援機能の計算テスト", ["node", "scripts/test-search-tools.mjs"]),
    # 第4期300ページは品質監査不合格を理由に撤回済み。公開対象として
    # 再監査せず、preflightでnoindex・検索・sitemap隔離だけを検証する。
    ("静岡県森町200ガイドの品質監査", [sys.executable, "scripts/audit_discover.py"]),
    ("sitemap.xml の生成", [sys.executable, "scripts/build_sitemap.py"]),
    ("200ページ計画・第1期の品質監査", [sys.executable, "scripts/audit_seo_phase1.py"]),
    ("200ページ計画・第3期の品質監査", [sys.executable, "scripts/audit_seo_phase3.py"]),
    ("重要11ページと検索発見基盤の監査", [sys.executable, "scripts/audit_search_discovery.py"]),
    ("自然検索向け100問の監査", [sys.executable, "scripts/audit_organic_search.py"]),
    ("llms.txt の生成", [sys.executable, "scripts/build_llms.py"]),
    ("URL台帳の生成", [sys.executable, "scripts/build_url_ledger.py"]),
]

CHECK = ("公開前検査", [sys.executable, "scripts/preflight_check.py"])
RELEASE_STEPS = [
    # 第4期は human_reviewed=true の記事だけを別工程で公開する。
    # 全件を機械監査だけで一括公開する処理は再発防止のため置かない。
    ("公開状態の sitemap.xml を再生成", [sys.executable, "scripts/build_sitemap.py"]),
    ("トップページの公開件数をsitemapへ同期", [sys.executable, "scripts/sync_home_page_count.py"]),
]
WITHDRAW = ("第4期の公開状態を解除", [sys.executable, "scripts/audit_seo_phase4.py", "--withdraw"])


def run(label: str, cmd: list[str]) -> int:
    print(f"\n▼ {label}")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    for line in out.splitlines():
        print("   " + line)
    if proc.returncode != 0:
        print(f"   [失敗] 終了コード {proc.returncode}")
    return proc.returncode


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-check", action="store_true", help="公開前検査を省略する")
    args = ap.parse_args()

    for label, cmd in STEPS:
        if run(label, cmd) != 0:
            print("\n" + "=" * 60)
            print("失敗した工程: " + label)
            sys.exit(1)

    if args.skip_check:
        print("\nビルド完了（公開前検査を省略したため第4期は未公開）")
        return

    code = run(*CHECK)
    if code != 0:
        print("\n" + "=" * 60)
        print("公開前検査に失敗したため第4期は未公開です")
        sys.exit(code)

    for label, cmd in RELEASE_STEPS:
        if run(label, cmd) != 0:
            run(*WITHDRAW)
            print("\n" + "=" * 60)
            print("公開切替に失敗したため第4期を未公開へ戻しました")
            sys.exit(1)

    code = run(*CHECK)
    if code != 0:
        run(*WITHDRAW)
        run("未公開状態の sitemap.xml を再生成", [sys.executable, "scripts/build_sitemap.py"])
    print("\n" + "=" * 60)
    print("ビルド完了・検査合格" if code == 0 else "ビルドは完了しましたが検査で不整合があります")
    sys.exit(code)


if __name__ == "__main__":
    main()
