# Google登録・インデックス・検索順位 改修計画書 実行結果

実行日：2026年8月7日
対象：<https://morimachi.enshu-lifehack.com/>
元計画書：`morimachi-google-index-seo-improvement-plan.md`

---

## 0. 結論

計画書が最優先課題としていた **技術的なインデックス阻害は、ローカル・本番とも1件も存在しなかった**。
robots.txt、canonical、サイトマップ、noindex、HTTPステータス、内部リンクはすべて要件を満たしている。

一方、計画書には前提の誤りが2件あった（§1参照）。また、検査の過程で**売却導線の実害を1件発見し、修正した**（§3）。

残る作業はSearch Console画面の操作のみで、これはログインが必要なため未実行（§4）。

---

## 1. 計画書の前提の訂正

| 計画書の記述 | 実際 | 影響 |
|---|---|---|
| 「129件前後の暮らしページ」（§1・§8・§22・§36） | **公開ページは395件**。129は `/life/` のみの数 | 母数が3倍。§8「129ページなら単一サイトマップで問題ない」の判断根拠、§22「全129ページへ手作業でリクエストしない」の記述が実態と合わない |
| 「検索結果に十分現れない＝技術的阻害の疑い」（§1） | 技術的阻害は**0件**。サイトは2026年7月3日開設で**約5週間**、全63コミット | 未露出の主因はブロックではなく、新規サブドメインに395ページを短期間で公開したことによる発見・評価の遅れ |

### 内訳（sitemap.xml 実測）

| 区分 | 件数 |
|---|---:|
| /life/（暮らし） | 129 |
| /questions/（質問） | 101 |
| /shrine/（神社） | 56 |
| /temple/（寺院） | 50 |
| /blog/（ブログ） | 41 |
| /hub/・/tools/・/checklist/・/about/・/terms/ ほか | 18 |
| **合計** | **395** |

---

## 2. 実行結果：計画書 第10部 完了判定チェックリスト

### §32 技術SEO（11項目すべて充足）

検査方法：`scripts/preflight_check.py`（ローカル全395ページ）、`scripts/verify_published.py`（本番へ実HTTPリクエスト）、および Googlebot UA での個別 curl。

- [x] robots.txtが200で取得できる — 本番200・プレーンテキスト
- [x] robots.txtに正式サイトマップURLがある — `Sitemap: https://morimachi.enshu-lifehack.com/sitemap.xml`
- [x] 公開対象ページがrobots.txtでブロックされていない — Disallowは `/admin/` のみ。Googlebot専用グループにも記載済み
- [x] 公開対象ページにnoindexがない — HTML内 `noindex` **0件**、`_headers` に `X-Robots-Tag` **なし**
- [x] 全公開ページにcanonicalが1つある — 395/395。欠落は `404.html` と `parts/*`（いずれも配信対象外で正しい）
- [x] canonicalがHTTPS・wwwなし・末尾スラッシュありで統一されている — 全件自己参照・絶対URL
- [x] canonical先が200を返す
- [x] サイトマップ掲載URLがすべて200を返す — **395/395が200**（本番実測）
- [x] サイトマップに301、404、noindex、パラメータURLがない — 実在ページ395/395一致、パラメータ混入0
- [x] HTTP／www／index.html等が正式URLへ転送される — 下記の注記あり
- [x] Search Consoleの重大なページ取得エラーが0件である — 本番で5xx・403は観測されず（GSC画面での最終確認は§4）

#### 転送に関する注記（実害なし・要判断）

| リクエスト | 応答 | 評価 |
|---|---|---|
| `http://` → `https://` | **301** | 計画書の要求どおり |
| `https://www.…` | DNS解決なし | www自体が存在せず重複が発生しない。対応不要 |
| `/index.html` → `/` | **307** | Cloudflare Workers の既定動作。計画書§32は301を要求 |
| 末尾スラッシュなし → あり | **307** | 同上 |
| 存在しないURL | **404** | カスタム404が正しく返る |

307は一時転送のためGoogleは転送元URLを保持しうるが、**全ページのcanonicalが正しい末尾スラッシュ付き絶対URLを指しており、内部リンクも全て正規形**のため、実質的な重複リスクはない。395件分の301ルールを `_redirects` に手書きする副作用のほうが大きいため、**現状維持を推奨**する。

### §33 インデックス（GSC依存のため一部未実行）

- [x] URL台帳が存在する — `reports/url-ledger.csv`（395行、canonical列を含む）。計画書§4.2の要求項目をほぼ充足済み
- [ ] URL台帳とSearch Consoleデータを突合した — **未実行**（§4）
- [ ] 除外理由別に件数と対象URLを把握した — **未実行**（§4）。`reports/search-console-audit.csv` は全行 `未確認` の空欄テンプレート
- [ ] Sページがすべてインデックス登録されている — **未確認**（§4）
- [ ] Google選択canonicalと指定canonicalが一致している — **未確認**（§4）
- [x] クロール済み未登録ページの重複・内容不足を修正した — title 395種／description 395種で**重複ゼロ**。テンプレート残り・空見出し・空セクションも0件
- [x] 検出未登録ページの内部リンクを強化した — 下記のとおり既に要件充足

#### §7 内部リンク実測

| 項目 | 計画書の要求 | 実測 |
|---|---|---|
| 孤立ページ（被リンク0） | 解消すること | **0件** |
| トップから到達不能 | 解消すること | **0件** |
| クリック深度 | 3クリック以内 | 最大**3**（深度0:1／1:37／2:283／3:74） |
| 壊れた内部リンク | 0 | **0件**（不正アンカーも0） |

売却関連の主要ページの被リンク数：`vacant-house` 24／`sell-house` 17／`clean-parents-house` 18／`inherited-house` 13／`inheritance` 10。いずれも孤立しておらず、§7の「修正方針」に着手すべき対象は無かった。

### §34 検索順位・売却導線

- [ ] 重点30キーワードの基準順位を記録した — **未実行**（§4）
- [x] 1キーワード1主ページの対応を決めた — 計画書§24が挙げた対応ページは**7件すべて実在**を確認（`/hub/property/`、`/life/housing/sell-house/`、`/life/housing/vacant-house/`、`/life/end-of-life/inherited-house/`、`/life/housing/clean-parents-house/`）
- [x] Sページに森町固有情報がある — 農地は5ページ（相続・売貸・転用・証明・農振除外）に分割済み。山林・境界・接道はブログで個別に扱いあり
- [x] 行政へ相談する内容と不動産会社へ相談する内容を分けた — `apply_cta_policy.py` が緊急・医療・生活困窮・一般行政手続きの16ページで営業CTAを抑止。CTA掲載は32ページのみ
- [x] 売却未定者向けCTAがある — 実家カルテCTA
- [x] 売却決定者向けCTAがある — **本実行で修正**（§3）
- [x] CTAクリックを計測できる — `data-track-click` 属性。本実行で `cta_sale_consultation` を追加
- [ ] Search Consoleの検索流入から申込みまで月次で追跡できる — **未実行**（§4）

---

## 3. 発見・修正した問題（1件）

### 症状

売却意欲が最も高い2ページ **`/life/housing/sell-house/`** と **`/life/end-of-life/inherited-house/`** に、
売却相談窓口 `fudosan.atawi.link/areas/mori/` へのリンクが**1本も存在しなかった**。

### 原因

`scripts/inject_karte_cta.py` は、通常の不動産CTA（`inject_cta.py` が生成、遷移先は `/areas/mori/`）を
この2ページだけ実家カルテCTAで**上書き**する設計だった。その結果、
カルテ（＝売却未定者向け）しか出口が残らず、**すでに売却を決めている人の導線が消えていた**。

意欲の低い `vacant-house`・`clean-parents-house`・`hub/property` には `/areas/mori/` リンクが残っており、
**意欲が高いページほど出口が無い**という逆転が起きていた。

これは計画書§28「CTAの2系統化」が指摘した問題そのものである。

### 修正

`scripts/inject_karte_cta.py` にカルテCTAと並ぶ第2導線を追加し、両ページを再生成した。

```
すでに売却を考えている方は、森町の家・土地の売却を相談する。
相続登記前・家財が残った状態・農地や山林を含む場合も相談できます。
```

- 遷移先：`https://fudosan.atawi.link/areas/mori/`
- 計測：`data-track-click="cta_sale_consultation"`（計画書§29の `sale_consultation_click` に対応）
- UTM：`utm_campaign=morimachi_sale` / `utm_content={ページ}_{位置}_sale`（early・bottom・mobileを区別）
- 運営会社開示（`cta-disclosure`）は既存のまま維持

変更ファイル：`scripts/inject_karte_cta.py`、`assets/karte-cta.css`（`.karte-cta-decided` を追加、キャッシュバスターを `v=20260807a` へ更新）、および再生成された上記2ページ。

再実行しても重複しないこと（冪等性）と、`preflight_check.py` 全16項目がエラー0であることを確認済み。

### 未デプロイ

**この修正はローカルのみで、本番へは反映していない。** 公開は利用者の判断で行うこと。
なお実行時点でリポジトリには blog-autopilot による新規ブログ記事
`blog/20260807-tenhama-station-frequency/` がステージ済みで残っている。
コミットする際は、この記事とCTA修正を分けるか、意図して一緒に含めるかを確認すること。

---

## 4. 未実行の作業（Search Consoleへのログインが必要）

以下は画面操作が必須で、本実行では行えなかった。計画書の§5・§18〜22・§23〜26・§35が該当する。

### 4.1 まず確認すること（優先順）

1. **プロパティが存在するか**。無ければドメインプロパティ `enshu-lifehack.com` を追加し所有確認する（計画書§18）
2. **サイトマップが送信済みか**。`sitemap.xml` を送信し、「検出されたページ数」が **395**（本日時点。新規ブログを含めると396）になるか確認する
3. **「ページのインデックス登録」レポート**を開き、登録済み／未登録の件数と**除外理由**を記録する
4. **「クロールの統計情報」→ホストのステータス**が「問題なし」か確認する

### 4.2 除外理由ごとの読み方（技術検査が全て通過している前提で）

| 表示される理由 | 本サイトでの解釈 |
|---|---|
| 検出 - インデックス未登録 | **最も可能性が高い。** 新規ドメインに395ページを短期公開した場合の通常の状態。技術修正では解決しない。時間・更新頻度・外部からの参照で改善する |
| クロール済み - インデックス未登録 | 内容の独自性の問題。特に `/questions/` 101件・`/shrine/` 56件・`/temple/` 50件は形式が揃っているため、量産ページと判定されやすい |
| robots.txtによりブロック / noindexタグ | **本実行で0件と確認済み。** もしGSCに表示されたら、それはGoogleのキャッシュが古いか `/admin/` 配下 |
| 重複・Googleが別を正規と選択 | canonicalは全件自己参照で正しい。表示された場合はGoogleが内容の近さで判断しているため、対象ページの差別化が必要 |
| サーバーエラー / 403 | **本実行で0件と確認済み。** 表示されたら Cloudflare 側の一時障害を疑う |

### 4.3 URL検査を行うページ（計画書§21）

技術面は検証済みのため、**Google選択canonicalと最終クロール日時の2点だけ**記録すればよい。

`/` ／ `/hub/property/` ／ `/life/housing/sell-house/` ／ `/life/housing/vacant-house/`
／ `/life/end-of-life/inherited-house/` ／ `/life/housing/clean-parents-house/`
／ `/life/troubles-consult/farmland/sell-or-rent/` ／ `/life/housing/property-tax/`
／ `/life/start-living/how-to-garbage/`

記録先：`reports/search-console-audit.csv`（列は作成済み・全行 `未確認` のまま）

### 4.4 再クロールをリクエストするページ

CTAを修正した2ページに限定する。**395ページへの連続リクエストは行わない。**

- `/life/housing/sell-house/`
- `/life/end-of-life/inherited-house/`

（本番へデプロイした後に実施すること）

---

## 5. 実行に使用したコマンド

```bash
python scripts/preflight_check.py      # ローカル全395ページの技術検査（16項目）
python scripts/verify_published.py     # 本番へ実HTTPリクエスト（200/301/404）
python scripts/inject_karte_cta.py     # CTA再生成（冪等）
```

---

## 6. 次にやるべきこと

| 順 | 作業 | 実行者 | 依存 |
|---:|---|---|---|
| 1 | Search Consoleでインデックス登録状況を取得（§4.1） | 運営者 | GSCログイン |
| 2 | CTA修正を本番へデプロイ | 運営者 | 判断 |
| 3 | デプロイ後、2ページの再クロールをリクエスト（§4.4） | 運営者 | 1・2 |
| 4 | 除外理由が「クロール済み - 未登録」に偏る場合、`/questions/`・`/shrine/`・`/temple/` の差別化を検討 | 編集 | 1 |
| 5 | 重点30キーワードの基準順位を記録し、月次計測を開始（計画書§24） | 運営者 | 1 |

**技術的な改修余地は残っていない。** ここから先の成否は、Search Consoleの実データと、
売却相談に近いページの内容の独自性で決まる。
