# 自然検索100PVの本人確認手順

公開用の証明ページは作らない。運営者本人が、Google Search Consoleと独自アクセス解析を
照合して確認する。数値の合算や、SNS・広告・関連サイト流入の上乗せはしない。

## 判定条件

次の両方が100以上のときだけ「達成」とする。

1. Google Search Consoleで対象日を1日に限定し、ページURLに
   `morimachi.enshu-lifehack.com` を含むフィルタを設定した「合計クリック数」
2. 独自アクセス解析の「森町ライフハック」に表示される同日の「人間PV」

Search Consoleのクリック数が自然検索入口の主指標である。人間PVはボット混入や計測漏れを
見つける照合値であり、2つを足して100にはしない。

## 8月30日と9月6日の確認

Search Consoleの確定には通常遅れがあるため、対象日の2日後を目安に確認する。

- 8月30日分: 9月1日〜2日に確認
- 9月6日分: 9月8日〜9日に確認

1. Search Consoleで検索タイプを「ウェブ」、日付を対象日1日だけにする。
2. ページのフィルタを「次を含む: `morimachi.enshu-lifehack.com`」にする。
3. 「エクスポート」からCSVを取得し、「日付」のCSVファイルを保存する。
4. 独自解析画面で森町ライフハックの同日「人間PV」を確認する。
5. 対象日から3日以内なら次のコマンドを実行する。

```powershell
python scripts/report_organic_100pv.py --date 2026-08-30 --gsc-csv "C:\Downloads\日付.csv" --domain-confirmed --output reports\organic-100pv-2026-08-30.md
```

3日より前の確認では、保存しておいた人間PVを `--human-pv` で指定する。

```powershell
python scripts/report_organic_100pv.py --date 2026-08-30 --gsc-csv "C:\Downloads\日付.csv" --domain-confirmed --human-pv 104 --output reports\organic-100pv-2026-08-30.md
```

`--domain-confirmed` は、Search Consoleで森町ホストのフィルタを自分の目で確認した場合だけ付ける。
付けない場合、数値が100以上でもレポートは「判定不能」とする。
