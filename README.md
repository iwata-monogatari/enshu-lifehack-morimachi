# enshu-lifehack-morimachi

森町ライフハック（遠州ライフハック 森町版）の **静的サイト** リポジトリ。
公開先：`https://morimachi.enshu-lifehack.com/`（Cloudflare Pages）

磐田版から手動クローン・履歴を切って新設。横展開の設計原則は袋井版の指示書（`enshu-lifehack-fukuroi` リポジトリ `docs/fukuroi-lifehack-design-spec.md`）に準拠する。

## 構成

静的HTMLのみ。Cloudflare Pages の **Build output directory = `/`**（ビルド不要）で配信する。

```
index.html              トップ（くらしの場面・目的から選ぶ）
data/city.json          市町プロファイル（市名・公式窓口・CVフラグ等の差分を集約）
data/topics_master.json 中項目マスター台帳（磐田155項目が起点）
life/<大項目>/           くらしの大項目ページ
life/<大項目>/<中項目>/   個別ページ
sitemap.xml             サイトマップ
robots.txt
_redirects              旧 /iwata/ 配下 → 直下への 301
404.html                カスタム404
favicon.svg
```

## 生成方法

本サイトは公式サイトのクロール・静的化ではなく、`data/topics_master.json` の中項目台帳をもとに、公式情報を1件ずつ調査した上でAIが執筆する「台帳駆動」の生成物である（掛川版と同じ方式）。

## 免責

本サイトは森町公式サイトではありません。最新・正確な情報は森町公式サイトをご確認ください。
運営：富士ヶ丘サービス ／ 代表：大石浩之
