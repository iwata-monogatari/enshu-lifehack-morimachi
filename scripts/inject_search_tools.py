# -*- coding: utf-8 -*-
"""重要ガイド5ページへ、公式データを使う検索支援機能を挿入する。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START = "<!-- SEARCH-TOOL:START -->"
END = "<!-- SEARCH-TOOL:END -->"
ASSET_START = "<!-- SEARCH-TOOL-ASSETS:START -->"
ASSET_END = "<!-- SEARCH-TOOL-ASSETS:END -->"
ASSETS = (
    f'{ASSET_START}<link rel="stylesheet" href="/assets/search-tools.css?v=20260806a">'
    '<script type="module" src="/assets/search-tools.mjs?v=20260806a"></script>'
    f'{ASSET_END}'
)

TOOLS = {
    "/life/start-living/how-to-garbage/": """
<section class="search-tool" id="next-garbage-day" aria-labelledby="garbage-tool-title">
<h2 id="garbage-tool-title">町内会名から次のごみ収集日を確認</h2>
<p class="search-tool-intro">令和8年度の森町公式ごみ収集カレンダーから、燃やせるごみ、資源・埋立ごみ、容器包装プラスチックの次回予定を表示します。</p>
<form class="search-tool-form" data-garbage-tool>
<div class="search-tool-field"><label for="garbage-area">町内会名</label><select id="garbage-area" name="area" required><option value="">選んでください</option></select></div>
<button type="submit">次の収集日を表示</button>
</form><div class="search-tool-result" data-tool-result aria-live="polite"></div>
<p class="search-tool-note">最終確認：2026年8月6日。町内会名が分からない場合や臨時変更は、<a href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/seikatsukankyokakari/1/1/692.html" target="_blank" rel="noopener">森町公式の分別・収集日案内</a>で確認してください。</p>
</section>""",
    "/life/family-grow/nursery-school/": """
<section class="search-tool" id="nursery-vacancy" aria-labelledby="nursery-tool-title">
<h2 id="nursery-tool-title">年齢から保育園の受入れ見込みを確認</h2>
<p class="search-tool-intro">森町が公表した令和8年度入所可能数見込みを、子どもの年齢ごとに並べます。</p>
<form class="search-tool-form" data-nursery-tool>
<div class="search-tool-field"><label for="nursery-age">入所年度の4月1日時点の年齢</label><select id="nursery-age" name="age" required><option value="0">0歳</option><option value="1">1歳</option><option value="2">2歳</option><option value="3">3歳</option><option value="4">4歳</option><option value="5">5歳</option></select></div>
<button type="submit">施設別の見込みを表示</button>
</form><div class="search-tool-result" data-tool-result aria-live="polite"></div>
<p class="search-tool-note">最終確認：2026年8月6日。受入れ数は随時変わり、申込み後の選考があります。<a href="https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/hoikuen_yochiento/hoikuen/4624.html" target="_blank" rel="noopener">森町公式の保育園案内</a>で最新状況を確認してください。</p>
</section>""",
    "/life/start-living/water-sewer/": """
<section class="search-tool" id="water-fee-estimate" aria-labelledby="water-tool-title">
<h2 id="water-tool-title">水道・下水道料金を概算</h2>
<p class="search-tool-intro">2か月分の使用水量とメーター口径から、消費税込みの概算を計算します。</p>
<form class="search-tool-form" data-water-tool>
<div class="search-tool-field"><label for="water-usage">2か月分の使用水量（m³）</label><input id="water-usage" name="usage" type="number" min="0" step="1" value="40" required></div>
<div class="search-tool-field"><label for="water-diameter">メーター口径</label><select id="water-diameter" name="diameter"><option value="13">13mm</option><option value="20">20mm</option><option value="25">25mm</option><option value="30">30mm</option><option value="40">40mm</option><option value="50">50mm</option><option value="75">75mm</option><option value="100">100mm</option></select></div>
<fieldset><legend>公共下水道</legend><div class="search-tool-radio"><label><input type="radio" name="sewer" value="yes" checked>接続している</label><label><input type="radio" name="sewer" value="no">接続していない</label></div></fieldset>
<button type="submit">料金を計算</button>
</form><div class="search-tool-result" data-tool-result aria-live="polite"></div>
<p class="search-tool-note">最終確認：2026年8月6日。<a href="https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/jogesuido/josuido/1402.html" target="_blank" rel="noopener">水道料金</a>と<a href="https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/jogesuido/gesuido/1208.html" target="_blank" rel="noopener">下水道使用料</a>の森町公式計算式を使用しています。実際の請求額は検針票で確認してください。</p>
</section>""",
    "/life/education/school-zones/": """
<section class="search-tool" id="school-zone-check" aria-labelledby="school-tool-title">
<h2 id="school-tool-title">住所・地区から学区を確認する準備</h2>
<p class="search-tool-intro">住所または地区名を入力すると、学校教育課へそのまま伝えられる確認文を作ります。入力内容は送信・保存されません。</p>
<form class="search-tool-form" data-school-tool>
<div class="search-tool-field"><label for="school-address">森町内の住所・地区名</label><input id="school-address" name="address" type="text" autocomplete="street-address" placeholder="例：森125、谷中" required></div>
<button type="submit">確認内容と窓口を表示</button>
</form><div class="search-tool-result" data-tool-result aria-live="polite"></div>
<p class="search-tool-note">最終確認：2026年8月6日。住所別通学区域の公式な公開一覧を確認できないため、自動で学校名を断定しません。<a href="https://www.town.morimachi.shizuoka.jp/morikko/sodachi/4787.html" target="_blank" rel="noopener">森町公式の小中学校一覧</a>も参照できます。</p>
</section>""",
    "/life/work-life/subsidies/": """
<section class="search-tool" id="migration-support-check" aria-labelledby="migration-tool-title">
<h2 id="migration-tool-title">移住就業支援金の対象候補を確認</h2>
<p class="search-tool-intro">主な条件だけを確認する簡易チェックです。最終判定や申請受付ではありません。</p>
<form class="search-tool-form" data-migration-tool>
<div class="search-tool-field"><label for="migration-move">森町へ転入した・転入予定</label><select id="migration-move" name="move"><option value="yes">はい</option><option value="no">いいえ・未定</option></select></div>
<div class="search-tool-field"><label for="migration-tokyo">東京23区に在住、または東京圏から23区へ通勤した期間の条件を満たす</label><select id="migration-tokyo" name="tokyo"><option value="yes">はい</option><option value="unsure">分からない</option><option value="no">いいえ</option></select></div>
<div class="search-tool-field"><label for="migration-year">転入後1年以内に申請する</label><select id="migration-year" name="withinYear"><option value="yes">はい</option><option value="unsure">分からない</option><option value="no">いいえ</option></select></div>
<div class="search-tool-field"><label for="migration-five">森町に5年以上住む意思がある</label><select id="migration-five" name="fiveYears"><option value="yes">はい</option><option value="no">いいえ・未定</option></select></div>
<div class="search-tool-field"><label for="migration-route">移住後の仕事など</label><select id="migration-route" name="route"><option value="job">対象求人への就業</option><option value="telework">以前の仕事をテレワークで継続</option><option value="professional">専門人材制度を利用</option><option value="relationship">森町の関係人口要件に該当</option><option value="startup">起業支援を利用</option><option value="unknown">未定・分からない</option></select></div>
<button type="submit">対象候補を確認</button>
</form><div class="search-tool-result" data-tool-result aria-live="polite"></div>
<p class="search-tool-note">最終確認：2026年8月6日。世帯100万円・単身60万円を基本とする制度ですが、時期・世帯・就業等の要件があります。<a href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/izyusankouzyohou/2128.html" target="_blank" rel="noopener">森町公式の移住就業支援金案内</a>で必ず確認してください。</p>
</section>""",
}


def page_path(href: str) -> Path:
    return ROOT / href.strip("/") / "index.html"


def inject(href: str, tool: str) -> None:
    path = page_path(href)
    html = path.read_text(encoding="utf-8")
    html = re.sub(
        re.escape(ASSET_START) + r".*?" + re.escape(ASSET_END),
        "", html, flags=re.S)
    html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S)
    html = html.replace("</head>", ASSETS + "</head>", 1)
    block = START + tool.strip() + END
    if "<!-- BRANCH-BLOCK:END -->" in html:
        html = html.replace("<!-- BRANCH-BLOCK:END -->", "<!-- BRANCH-BLOCK:END -->" + block, 1)
    else:
        hero = re.search(r'<section class="hero".*?</section>', html, flags=re.S)
        if not hero:
            raise RuntimeError(f"heroが見つかりません: {href}")
        html = html[:hero.end()] + block + html[hero.end():]
    path.write_text(html, encoding="utf-8")


def main() -> None:
    for href, tool in TOOLS.items():
        inject(href, tool)
        print(f"検索支援機能を反映: {href}")


if __name__ == "__main__":
    main()
