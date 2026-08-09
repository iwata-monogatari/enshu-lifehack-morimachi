#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4期300検索意図を、6,000字以上の独立した実用ページとして生成する。"""
from __future__ import annotations

import json
import random
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://morimachi.enshu-lifehack.com"
TODAY = "2026-08-09"
TOPICS = ROOT / "data" / "seo-phase4-topics.json"
PUBLICATION = ROOT / "data" / "seo-phase4-publication.json"
ENRICHMENT_FILES = tuple(ROOT / "data" / f"seo-phase4-enrichment-{start:03d}-{start+99:03d}.json" for start in (1, 101, 201))
LINK_START = "<!-- SEO-PHASE4-LINKS:START -->"
LINK_END = "<!-- SEO-PHASE4-LINKS:END -->"
ROBOTS_PENDING = '<meta name="robots" content="noindex,nofollow" data-phase4-pending>'

CATEGORY_PATH = {
    "行政手続き": "/life/start-living/", "子育て": "/life/family-grow/", "教育": "/life/education/",
    "健康": "/life/health-medical/", "防災": "/life/emergency/", "交通生活": "/life/play-out/",
}

CATEGORY_CONTEXT = {
    "行政手続き": ("届出・証明・本人確認・期限を別々に整理する", "役場の担当窓口と国の所管情報", "住所、氏名、対象日、本人確認書類"),
    "子育て": ("子どもの年齢と利用開始日から逆算する", "健康こども課と制度所管機関", "年齢、世帯状況、希望日、申請期限"),
    "教育": ("年度・住所・在籍状況をそろえて確認する", "学校教育課と教育機関", "学年、住所、在籍校、希望時期"),
    "健康": ("緊急性と通常相談を分け、対象条件を確認する", "町の保健案内と県・国の医療情報", "年齢、症状、受診歴、保険情報"),
    "防災": ("平時の準備と発災時の行動を混同しない", "森町の防災情報と所管機関", "住所、家族構成、避難経路、連絡先"),
    "交通生活": ("往路・帰路・代替手段を一組で考える", "町の公共交通案内と交通事業者", "出発地、目的地、曜日、帰宅時刻"),
    "住宅": ("建物・敷地・設備・契約資料を分ける", "森町の住まい案内と登記・建築の所管情報", "所在地、地番、名義、設備状況"),
    "空き家": ("所有関係と現在の管理状態を先に確かめる", "森町の空き家窓口と国の不動産情報", "名義、鍵、残置物、管理費"),
    "相続": ("相続人・名義・財産種類・期限を一覧にする", "町の手続き案内と法務・税務の所管情報", "被相続人、相続人、登記、財産資料"),
    "土地": ("登記と現況、接道、利用条件を照合する", "森町の土地利用案内と登記・都市計画情報", "地番、地目、境界、接道"),
    "農地": ("地目・耕作者・権利・水路管理を分ける", "森町農業委員会と農地制度の所管情報", "地番、地目、耕作状況、権利者"),
    "山林": ("境界・進入路・樹木・管理責任を確認する", "森町の林業案内と県・国の森林情報", "地番、所有者、境界、作業道"),
    "事業": ("事業内容・場所・許認可・資金を順に確認する", "森町の産業窓口と事業所管機関", "事業計画、所在地、開始時期、必要手続き"),
    "仕事": ("働き方・通勤・保険・家族時間を同時に見る", "町の就業情報と雇用所管機関", "勤務先、時間帯、交通手段、保険"),
    "文化財": ("指定名称・区分・所在地・管理者を分ける", "森町の文化財資料と国・県の文化資料", "資料名、指定区分、所在地、確認日"),
    "神社": ("神社台帳の事実と祭礼の当年運用を分ける", "神社関係者と森町の文化資料", "社名、所在地、御祭神、当年案内"),
    "寺院": ("法人名簿の事実と拝観・寺務の運用を分ける", "寺院関係者と県・町の公的資料", "寺名、宗派、所在地、拝観条件"),
    "祭り": ("文化的背景と当年の日程・交通を分ける", "主催者の当年案内と森町の文化資料", "行事名、開催年、場所、交通情報"),
    "歴史": ("史料で確認できる事実と伝承を分ける", "森町の歴史資料と文化財所管資料", "史料名、年代、地名、確認箇所"),
    "観光": ("移動・滞在・安全・営業確認を一日でつなぐ", "森町の観光情報と施設・交通の当事者情報", "訪問日、移動手段、同行者、帰路"),
    "食": ("産地・製造・販売・保存条件を表示から確かめる", "森町の産業情報と販売者の一次情報", "商品名、産地、製造者、保存条件"),
    "農業": ("品目・時期・生産者・圃場管理を分ける", "森町の農林業情報と県・国の所管資料", "品目、時期、所在地、管理者"),
}

SECTION_HEADINGS = [
    "この問いで最初に決めること", "一次情報から確定できる範囲", "森町で条件が変わるポイント",
    "資料を集める順番", "現地または窓口で確認すること", "期限と実行日の組み立て方",
    "費用と見えにくい負担", "家族・関係者との共有", "判断を急がないための代案",
    "記録を次の人へ残す", "大石の視点", "まとめと次の一歩",
]

def e(value: object) -> str:
    return escape(str(value), quote=True)

def canonical_url(row: dict) -> str:
    slug = row["slug"].strip()
    if slug.startswith("/"):
        return "/" + slug.strip("/") + "/"
    base = CATEGORY_PATH.get(row["category"], "/guide/")
    return base + slug.strip("/") + "/"

def visible_chars(html: str) -> int:
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", "", html, flags=re.S)
    return len(re.sub(r"\s+", "", text))

def editorial_chars(html: str) -> int:
    match = re.search(r'<article class="post-editorial-body">(.*?)</article>', html, re.S)
    return visible_chars(match.group(1)) if match else 0

def load_rows() -> list[dict]:
    rows = json.loads(TOPICS.read_text(encoding="utf-8"))
    enrichments: dict[int, dict] = {}
    for path in ENRICHMENT_FILES:
        if not path.exists():
            raise RuntimeError(f"公開用固有データがありません: {path.name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("records") or data.get("topics") or data.get("items") or []
        for item in data:
            enrichments[int(item["id"])] = item
    if set(enrichments) != set(range(1, 301)):
        missing = sorted(set(range(1, 301)) - set(enrichments))
        raise RuntimeError(f"固有データが300件そろっていません: missing={missing[:10]}")
    merged = []
    for row in rows:
        item = {**row, **enrichments[int(row["id"])]}
        for key, minimum in {"verified_facts": 6, "morimachi_conditions": 3, "section_headings": 12, "faqs": 4, "sources": 3}.items():
            if len(item.get(key, [])) < minimum:
                raise RuntimeError(f"ID{row['id']} {key} が{minimum}件未満です")
        merged.append(item)
    return merged

def category_context(category: str) -> tuple[str, str, str]:
    return CATEGORY_CONTEXT.get(category, ("対象・時点・担当者・根拠を分ける", "森町と所管機関の一次情報", "対象地、目的、時期、確認資料"))

def paragraph_set(row: dict, section: int) -> list[str]:
    title, intent, category = row["title"], row["search_intent"], row["category"]
    method, authorities, memo = category_context(category)
    risk = str(row.get("risk", "medium")).lower()
    sets = [
        [
            f"{title}で最初に行うのは、検索結果を増やすことではなく、何を決めるための確認かを一文にすることです。このページでは「{intent}」という迷いを扱います。対象、時点、利用者が変われば答えも変わるため、条件を書かずに結論だけを持ち帰らないでください。",
            f"基本の順序は、{method}ことです。森町の案内だけで完結する事項と、県・国・施設・所有者など別の確認先が必要な事項を分けます。一つの窓口で全部決まると思わないことが、手戻りを減らします。",
            f"手元のメモには「今日確定したいこと」「実行直前に再確認すること」「専門判断が必要なこと」の三欄を作ります。{memo}を最初に書けば、問い合わせ時に説明が短くなり、担当者も対象を絞りやすくなります。",
            f"このテーマのリスク区分は{risk}として扱います。これは不安を煽る表示ではなく、古い案内や個別条件を一般化しないための編集上の印です。分からない項目は推測で埋めず、未確認と記録します。",
        ],
        [
            f"一次情報は{authorities}を起点にします。資料が説明している対象者、適用日、場所、担当部署を確認し、ページの更新日だけで新しさを判断しません。制度や行事では、公開日と実施年度が異なる場合があります。",
            "第一の公式資料は、ページ名、確認日、該当する見出しを一緒に残します。PDFならページ番号と注記、表なら単位と対象期間も記録し、数字だけを切り離さないでください。",
            "第二の公式資料は、一件目と対象範囲や管理主体が同じかを確かめます。食い違いがあれば新しい方へ自動的に寄せず、定義と適用範囲を比べます。",
            f"検索結果の要約、個人ブログ、地図の口コミは確認の入口にはなりますが、最終根拠にはしません。{title}について実行日が決まったら、掲載した一次情報をもう一度開き、現在も同じ条件かを確かめます。",
        ],
        [
            f"森町は中心市街地、天浜線沿線、平地の集落、天方・三倉の山間部で、距離と移動の感じ方が異なります。町全体の説明が正しくても、対象地点の道路、標高差、通信、周辺施設まで同じとは限りません。",
            f"住所が分かる場合は地図上の一点だけでなく、入口、接道、最寄りの公共施設、避難経路、帰路を一緒に見ます。住所が未確定なら地区名と目的地を分け、同名施設や旧地名との取り違えを防ぎます。",
            f"曜日と時間帯も条件です。窓口、交通、行事、医療、買物、農作業は平日と休日、朝と夕方で利用状況が変わります。一度の訪問や一枚の写真を、年間を通じた状態として一般化しません。",
            f"山、川、農地、社寺、住宅地では、公開情報だけで見えない管理の都合があります。私有地や作業場所へ入らず、地域の生活と安全を妨げない範囲で確認することを、情報収集の前提にします。",
        ],
        [
            f"資料は、本人・対象を特定するもの、現在の状態を示すもの、期限を示すもの、権利や利用条件を示すものに分けます。全部を一つの封筒へ入れるより、何を証明する資料か付箋を付ける方が不足を見つけやすくなります。",
            f"{memo}を一覧にし、原本が必要か、写しでよいか、発行からの期限があるかを確認します。まだ取得しない資料も「取得先」「必要になる場面」「費用」を書いておくと、家族が代わって動くときに迷いません。",
            f"オンラインで取得した資料はファイル名へ日付と資料名を入れます。紙の資料は該当箇所へ印を付けます。個人番号、医療情報、登記識別情報などを家族共有の一般フォルダへ無防備に置かないでください。",
            f"不足資料があるときは、推定値で話を進めず、どの判断までなら保留のまま進められるかを確認します。{title}の目的は書類を集めきることではなく、次の安全な判断に必要な根拠をそろえることです。",
        ],
        [
            f"窓口や当事者へ問い合わせるときは、{intent}とだけ伝えるのではなく、対象地点、希望時期、すでに見た資料、今日知りたい範囲を伝えます。担当外なら次の窓口名と、引継ぎに必要な説明を聞きます。",
            f"現地では安全、利用条件、周辺動線の三点を優先します。写真には確認日と撮影方向を残し、人物、表札、車両番号、生活状況など個人を特定できる情報を公開しないようにします。",
            f"看板や掲示がウェブ案内と違う場合は、その場で都合よく解釈しません。掲示の対象期間と管理者を確認し、必要なら双方の資料名を示して問い合わせます。現地情報も確認日の記録がなければ再利用できません。",
            f"危険、医療、税、法務、構造、安全性など資格や所管判断が必要な事項は、このページで結論を出しません。事実関係を整理し、専門家や担当機関へ相談するための準備として使います。",
        ],
        [
            f"期限は、申請・予約の締切、資料の有効期間、実施日、支払日、見直し日へ分けます。一つの日付だけをカレンダーへ入れると、前提資料が間に合わないため、準備開始日も設定します。",
            f"{title}を実行する日から逆算し、二週間前、一週間前、前日、当日に確認する事項を置きます。変動しやすい運行、天候、在庫、受付、行事情報は直前確認へ回し、早い段階で断定しません。",
            f"役場、事業者、家族、専門家の返答待ちがある場合は、相手の回答期限ではなく、自分が次の判断をする期限を決めます。返答がなければ保留するのか、別案へ切り替えるのかも先に共有します。",
            f"年度をまたぐ情報は特に注意します。前年の対象者、金額、日程、受付方法を翌年へそのまま当てはめず、当年版の資料が出た時点で差分を確認してください。",
        ],
        [
            f"費用は窓口で支払う金額だけではありません。交通、郵送、証明取得、専門相談、修繕、管理、休業時間、家族の移動などを別々に書き、分からない項目をゼロ円にしないことが大切です。",
            f"見積りが必要な項目は、対象範囲と前提条件をそろえて依頼します。安い・高いという評価より、何を含み何を含まないかを比較します。追加作業が起こる条件も質問してください。",
            f"公的な支援や減免が見つかっても、対象要件、申請時期、着手前申請の有無を確認します。利用できる可能性と、今回実際に利用できることを同じ文章にしません。",
            f"お金をかけない代案にも時間と管理責任があります。先送り、家族対応、自主管理を選ぶなら、誰がいつまで担当し、できなくなったときにどう切り替えるかを決めます。",
        ],
        [
            f"家族や共有者がいる場合、情報を集める人と決定できる人は同じとは限りません。連絡役だけが結論を背負わないよう、選択肢、根拠、費用、未確認事項を一枚で共有します。",
            f"話合いでは賛成・反対を先に聞かず、事実、希望、困りごと、保留条件の順に整理します。{intent}という目的へ戻り、何が分かれば次へ進めるかを各人から確認します。",
            f"遠方の家族には写真だけでなく、住所、地図、資料名、確認日を送ります。写真の印象だけで安全性や管理状態を判断しないよう、撮影していない範囲と未確認事項も添えます。",
            f"本人の意思確認が必要なテーマでは、家族の都合で結論を置き換えません。支援が必要な場合も、本人が理解し選べる情報量と順序を整え、必要に応じて公的相談先へつなぎます。",
        ],
        [
            f"結論を急がないため、実行する案、条件が整えば実行する案、今回は見送る案の三つを残します。二択にすると、未確認事項が多い段階で無理な判断をしやすくなります。",
            f"最小の一歩は、資料一件を確認する、対象地点を地図に記す、担当窓口を確認する、家族一人へ共有する、のいずれかで十分です。大きな契約や申請を最初の行動にしません。",
            f"目的そのものを見直すことも代案です。{title}で本当に解決したいのが時間、費用、安全、家族負担のどれかを確認すれば、別の制度や方法が合う場合があります。",
            f"保留を選ぶ場合も、再確認日と保留理由を残します。何もしない状態と、根拠を持って待つ状態は違います。更新情報が出たときに再開できる形へ整えてください。",
        ],
        [
            f"記録には、対象、確認日、確認者、資料名、分かったこと、未確認事項、次の担当を残します。結論だけでは、前提が変わったときにどこから見直すか分かりません。",
            f"住所と地番、通称と正式名称、年度と暦年など、似ているが役割の違う情報を同じ欄へ入れないでください。元資料の表記を保存し、家族向けの説明を別欄に書きます。",
            f"更新した資料は古い版を黙って上書きせず、確認日の違いが分かるようにします。不要になった個人情報は適切に破棄し、共有範囲も定期的に見直します。",
            f"次の人が同じ問い合わせを繰り返さずに済む記録が理想です。担当者の個人名を必要以上に共有せず、部署名、公式連絡先、回答の要点と確認日を残します。",
        ],
        [
            f"私は小さな不動産業者として、{title}のような相談でも、いきなり売却や契約の話へ進めるべきではないと考えます。対象、道路、境界、名義、農地、維持負担など関係する事実を先に分ける方が、家族の選択肢を守れます。",
            f"森町では地図上の近さだけでなく、道路幅、坂、川、山、鉄道、地域の管理との関係が判断に影響します。私は現地を見ていない事項を体験談のように語らず、確認が必要な条件として明示します。",
            f"まだ決めていない人に必要なのは、結論を迫る言葉より、何が分かれば決められるかを整理する道具です。査定額や制度名だけを先に置かず、家族が引き継げる記録を作ることを勧めます。",
            f"良い選択は一つではありません。実行、管理継続、専門相談、時期を待つという案を同じ表で比べ、地域への配慮と所有者・利用者の現実的な負担を同時に見ます。",
        ],
        [
            f"{title}の結論は、{method}ことから始め、{authorities}で現在の条件を確認することです。一般記事は順序を整える道具であり、個別の可否を保証するものではありません。",
            f"今日できるのは、{memo}を書き出し、二つの一次情報の確認日を残すことです。そのうえで、現地・窓口・家族・専門家のうち、次に確認する相手を一人だけ決めます。",
            f"実行直前には期限、安全、権利・利用条件、費用、帰路または管理方法を再点検します。どれかが未確認なら、結論を急がず代案へ戻れるようにしてください。",
            f"このページを家族へ送る場合は、ページURLだけでなく、自分たちの対象地点、希望時期、保留事項を短く添えます。同じ情報を読んでも前提が違えば判断が変わることを共有して終えます。",
        ],
    ]
    return sets[section]

def svg(row: dict, index: int) -> str:
    seed = int(row["id"]) * 31 + index * 17
    rng = random.Random(seed)
    palettes = [("#173f36", "#dcefe5", "#d49a3a"), ("#283f66", "#e2ebf7", "#b75d43"), ("#5a3827", "#f4e4c8", "#4f7b57")]
    dark, pale, accent = palettes[seed % len(palettes)]
    ridge = " ".join(f"{x},{rng.randint(120,250)}" for x in range(0, 1001, 100))
    motif = row["category"][:4]
    decorations = "".join(
        f'<circle cx="{110+n*67}" cy="{180+(n%3)*42}" r="{12+(n%4)*3}" fill="{accent}" opacity=".55"/>'
        for n in range(1 + (int(row["id"]) + index) % 11)
    )
    scene_kind = (int(row["id"]) + index) % 6
    scenes = [
        f'<g data-scene="document"><rect x="360" y="250" width="260" height="180" rx="18" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M395 305h190M395 345h150M395 385h175" stroke="{dark}" stroke-width="10" opacity=".55"/></g>',
        f'<g data-scene="home"><path d="M350 350 500 225l150 125v140H350Z" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="470" y="405" width="60" height="85" fill="{accent}"/></g>',
        f'<g data-scene="transport"><rect x="330" y="305" width="340" height="130" rx="34" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="410" cy="455" r="32" fill="{accent}"/><circle cx="590" cy="455" r="32" fill="{accent}"/></g>',
        f'<g data-scene="people"><circle cx="430" cy="290" r="42" fill="{accent}"/><circle cx="570" cy="290" r="42" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M355 475q75-155 150 0M495 475q75-155 150 0" fill="none" stroke="{dark}" stroke-width="18"/></g>',
        f'<g data-scene="land"><path d="M285 460 390 270l110 105 105-155 120 240Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M500 375v100" stroke="{accent}" stroke-width="18"/></g>',
        f'<g data-scene="culture"><path d="M350 470V320h300v150M320 320h360L500 205Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M430 470V365h140v105" fill="{accent}"/></g>',
    ]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" role="img" aria-labelledby="title desc" data-illustration="mori-editorial" data-topic-id="{int(row['id'])}" data-scene-index="{index}"><title id="title">{e(row['title'])}の挿絵{index}</title><desc id="desc">森町の山並み、道、{e(row['section_headings'][(index-1)%len(row['section_headings'])])}の確認場面</desc><rect width="1000" height="560" rx="32" fill="{pale}"/><polygon points="{ridge} 1000,350 0,350" fill="{dark}" opacity=".22"/><path d="M0 430 Q250 {rng.randint(330,410)} 500 430 T1000 410 V560 H0Z" fill="{dark}" opacity=".18"/><path d="M60 500 C230 {rng.randint(350,440)} 360 {rng.randint(360,450)} 520 450 S780 {rng.randint(330,430)} 940 390" fill="none" stroke="{accent}" stroke-width="24" stroke-linecap="round"/>{decorations}{scenes[scene_kind]}<text x="500" y="72" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="700" fill="{dark}">{e(motif)}・{e(row['section_headings'][(index+2)%len(row['section_headings'])][:16])}</text></svg>'''

def specific_blocks(row: dict) -> str:
    headings = list(row["section_headings"])
    facts = row["verified_facts"]
    conditions = row["morimachi_conditions"]
    focus = re.sub(r"^(で|の|を|が|に)+", "", row["title"].split("｜", 1)[0].replace("森町", "").strip())
    boundary = row.get("editorial_boundary") or row.get("cannibalization", {}).get("editorial_boundary") or row.get("reason", "")
    guardrail = row.get("legal_tax_guardrail") or row.get("guardrail") or "個別の可否を断定せず、一次情報と当事者確認へつなぎます。"
    blocks = []
    for number, heading in enumerate(headings[:10], 1):
        fact = facts[(number - 1) % len(facts)]
        fact_text = fact.get("statement") if isinstance(fact, dict) else str(fact)
        source_url = fact.get("source_url", "") if isinstance(fact, dict) else ""
        condition = conditions[(number - 1) % len(conditions)]
        variants = [
            f"「{heading}」で根拠にする確認事項は、{fact_text}です。この記載が今回の対象と一致するか、対象者、対象日、場所、例外を資料本文で照合します。確認元は {source_url} として記録し、検索結果の要約だけで判断しません。",
            f"森町で特に分けて考える条件は「{condition}」です。{row['search_intent']}という目的に照らし、住所、利用者、実行時期のどれが違えば結論が変わるかを確認表へ書きます。町全体の一般論を個別地点の答えへ置き換えません。",
            f"{row['title']}について家族や担当窓口へ尋ねるときは、「{heading}」「{fact_text}」「未確認の個別条件」の三点を一組で伝えます。返答は可否だけでなく、根拠資料名、担当部署、再確認が必要な時点まで残します。",
            f"実行前の記録には、第{number}の論点「{heading}」、確認日、対象年度、担当者へ伝えた前提を書きます。{boundary}。このページで断定できない事項は推測で補わず、確認待ちとして次の担当と期限を決めます。",
            f"この論点を後回しにすると、必要資料、移動、家族の役割、費用のいずれかで手戻りが起こります。まず「{condition}」を確かめ、次に「{fact_text}」が自分のケースへ適用されるかを所管情報と窓口で照合してください。",
        ]
        variants = [f"焦点「{focus}」の論点「{heading}」として、{text}" for text in variants]
        shift = (int(row["id"]) * 3 + number) % len(variants)
        variants = variants[shift:] + variants[:shift]
        variants = variants[:2]
        blocks.append(f'''<section class="topic-specific"><h2 class="sec">{e(heading)}</h2>{''.join(f'<p>{e(p)}</p>' for p in variants)}<p><strong>{e(focus)}・第{number}論点の断定防止：</strong>{e(guardrail)}。「{e(fact_text)}」を確認できない場合は結論を保留し、一次情報の所管窓口または必要な専門家へ確認します。</p></section>''')
        if number == 4:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" loading="lazy" alt="森町で{e(row["search_intent"])}ため、資料と現地条件を照合する場面"><figcaption>対象地点と一次資料を同じ確認表へ置きます。</figcaption></figure>')
        if number == 9:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" loading="lazy" alt="{e(row["title"])}について、窓口確認から家族共有へ進む図"><figcaption>未確認事項、次の担当、再確認日を残します。</figcaption></figure>')
    return "".join(blocks)

def render(row: dict, url: str, prev_url: str, next_url: str) -> str:
    title, intent, category = row["title"], row["search_intent"], row["category"]
    focus = re.sub(r"^(で|の|を|が|に)+", "", title.split("｜", 1)[0].replace("森町", "").strip())
    out_dir = ROOT / url.strip("/")
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(("cover.svg", "fig1.svg", "fig2.svg"), 1):
        (out_dir / name).write_text(svg(row, index), encoding="utf-8", newline="\n")
    order = list(range(1, 11))
    random.Random(int(row["id"])).shuffle(order)
    order = [0] + order + [11]
    blocks = []
    for position, idx in enumerate(order):
        blocks.append(f'<section><h2 class="sec">{e(SECTION_HEADINGS[idx])}</h2>')
        variants = paragraph_set(row, idx)
        shift = (int(row["id"]) + idx) % 4
        variants = variants[shift:] + variants[:shift]
        blocks.extend(f"<p>{e(p)}</p>" for p in variants)
        if position == 2:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" loading="lazy" alt="森町の地形と暮らしの中で{e(intent)}ための確認場面"><figcaption>資料だけでなく、森町の場所と暮らしの条件を重ねて確認します。</figcaption></figure>')
        if position == 7:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" loading="lazy" alt="{e(title)}について資料、現地、窓口、家族共有へ進む順序"><figcaption>確定事項と未確認事項を分け、次の担当と期限を決めます。</figcaption></figure>')
        blocks.append("</section>")
    faq = [(item["question"], item["answer"]) for item in row["faqs"][:5]]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
    faq_json = {"@context":"https://schema.org", "@type":"FAQPage", "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}
    desc = f"静岡県{intent}人向けに、一次情報、現地確認、期限、費用、家族共有、大石の視点を順序立てて整理した実用ガイドです。"
    webpage = {"@context":"https://schema.org", "@type":"WebPage", "name":title, "url":SITE+url, "description":desc, "dateModified":TODAY, "author":{"@type":"Person","name":"大石博之"}}
    breadcrumb = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"静岡県森町ライフハック","item":SITE+"/"},{"@type":"ListItem","position":2,"name":category,"item":SITE+CATEGORY_PATH.get(category,"/guide/")},{"@type":"ListItem","position":3,"name":title,"item":SITE+url}]}
    sources = "".join(f'<a class="official-link" href="{e(src["url"])}" target="_blank" rel="noopener">{e(src.get("title") or "一次情報")} <span>{e(src.get("role") or "公式確認")}</span></a>' for src in row["sources"][:5])
    related = "".join([f'<a class="official-link" href="{prev_url}">前の第4期ガイド</a>', f'<a class="official-link" href="{next_url}">次の第4期ガイド</a>', '<a class="official-link" href="/guide/morimachi-complete-guide/">森町総合ガイド</a>', '<a class="official-link" href="/life/living-soon/about-morimachi/">森町を知る</a>', '<a class="official-link" href="/questions/">森町のよくある質問</a>'])
    related += f'<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False, separators=(",", ":"))}</script>'
    common = []
    for heading, offset in (("このページの結論", 0), ("大石の視点", 2), ("まとめと次の一歩", 4)):
        common.append(f'<section><h2 class="sec">{heading}</h2>')
        for pos in range(4):
            fact = row["verified_facts"][(offset + pos) % len(row["verified_facts"])]
            fact_text = fact.get("statement") if isinstance(fact, dict) else str(fact)
            condition = row["morimachi_conditions"][(offset + pos) % len(row["morimachi_conditions"])]
            common.append(f'<p>焦点「{e(focus)}」の{heading}で私が重視する第{pos+1}の判断材料は「{e(fact_text)}」と「{e(condition)}」の照合です。まだ実行を決めていなくても、確認日、対象、根拠、未確認事項を一枚に残せば、家族や担当者が同じ前提から話せます。確認できない事項は結論に混ぜず、次の確認先と期限を記録してください。</p>')
        common.append("</section>")
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | 森町ライフハック</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{url}"><meta property="og:type" content="website"><meta property="og:site_name" content="森町ライフハック"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{SITE}{url}"><meta property="og:image" content="{SITE}{url}cover.svg"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v=20260702"><script type="application/ld+json">{json.dumps(webpage, ensure_ascii=False, separators=(',', ':'))}</script><script type="application/ld+json">{json.dumps(faq_json, ensure_ascii=False, separators=(',', ':'))}</script></head><body><!-- SEO-PHASE4-PAGE --><!-- PART:header:START --><header class="site"><div class="wrap"><a class="logo" href="/">森町ライフハック</a></div></header><!-- PART:header:END --><!-- PART:disclaimer:START --><div class="disclaimer"><div class="wrap">森町ライフハックは森町公式サイトではありません。最新・正確な情報は必ず公式ページで確認してください。</div></div><!-- PART:disclaimer:END --><main><div class="wrap"><p class="breadcrumb"><a href="/">静岡県森町ライフハック</a> ／ {e(category)} ／ {e(title)}</p><section class="hero"><div class="hero-visual"><span aria-hidden="true">🧭</span><h1>{e(title)}</h1></div><div class="hero-body"><p class="lead">{e(intent)}人が、事実と未確認事項を分けて次の一歩を決めるためのガイドです。</p><img style="width:100%;height:auto" src="cover.svg" width="1000" height="560" alt="{e(title)}の確認場面を森町の山並み、家、道、資料で描いた表紙"></div></section><article class="post-editorial-body">{specific_blocks(row)}{''.join(common)}</article><section><h2 class="sec">よくある質問</h2><div class="qa">{faq_html}</div></section><section><h2 class="sec">公式情報源</h2><p>リンク先の対象年度、担当部署、更新日を確認し、実行直前に再確認してください。</p><div class="official">{sources}</div></section><section><h2 class="sec">関連ページ</h2><div class="official">{related}</div></section><p class="verified">生成日：{TODAY} ／ 個別の可否は公式窓口・当事者・必要な専門家へ確認してください。</p></div></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''

def inject_discovery(rows: list[dict]) -> None:
    guide = ROOT / "guide" / "morimachi-complete-guide" / "index.html"
    html = guide.read_text(encoding="utf-8")
    groups = {}
    for row in rows:
        groups.setdefault(row["category"], canonical_url(row))
    links = "".join(f'<a class="official-link" href="{url}">第4期・{e(category)}の確認ガイド</a>' for category, url in sorted(groups.items()))
    block = LINK_START + '<section><h2 class="sec">300の具体的な確認ガイド</h2><p>手続き、住まい、土地、文化、訪問などを、一つの判断ごとに確認できます。</p><div class="official">' + links + "</div></section>" + LINK_END
    html = re.sub(re.escape(LINK_START)+r".*?"+re.escape(LINK_END), block, html, flags=re.S) if LINK_START in html else html.replace("</main>", block+"</main>", 1)
    guide.write_text(html, encoding="utf-8", newline="\n")

def remove_discovery() -> None:
    """未公開ページへの発見導線を総合ガイドから取り除く。"""
    guide = ROOT / "guide" / "morimachi-complete-guide" / "index.html"
    if not guide.is_file():
        return
    html = guide.read_text(encoding="utf-8")
    html = re.sub(re.escape(LINK_START) + r".*?" + re.escape(LINK_END), "", html, flags=re.S)
    guide.write_text(html, encoding="utf-8", newline="\n")

def set_release_state(rows: list[dict], released: bool) -> None:
    """監査済みページだけをindex可能にし、発見導線を同期する。"""
    for row in rows:
        path = ROOT / canonical_url(row).strip("/") / "index.html"
        html = path.read_text(encoding="utf-8")
        html = html.replace(ROBOTS_PENDING, "")
        if not released:
            html = html.replace("<head>", f"<head>{ROBOTS_PENDING}", 1)
        path.write_text(html, encoding="utf-8", newline="\n")
    inject_discovery(rows) if released else remove_discovery()

def main() -> None:
    rows = load_rows()
    if len(rows) != 300 or {int(r["id"]) for r in rows} != set(range(1, 301)):
        raise RuntimeError("第4期台帳はID 1〜300の300件である必要があります")
    if any(r.get("decision") != "CREATE" for r in rows):
        raise RuntimeError("第4期公開台帳にCREATE以外が含まれています")
    urls = [canonical_url(r) for r in rows]
    if len(urls) != len(set(urls)):
        raise RuntimeError("第4期URLが重複しています")
    publication = []
    for index, row in enumerate(rows):
        url = urls[index]
        path = ROOT / url.strip("/") / "index.html"
        if path.is_file() and "SEO-PHASE4-PAGE" not in path.read_text(encoding="utf-8"):
            raise RuntimeError(f"既存ページとのURL衝突: {url}")
        html = render(row, url, urls[index-1], urls[(index+1) % len(urls)])
        html = html.replace("<head>", f"<head>{ROBOTS_PENDING}", 1)
        chars = editorial_chars(html)
        if chars < 6000:
            raise RuntimeError(f"編集本文が6000文字未満: {url} {chars}")
        path.write_text(html, encoding="utf-8", newline="\n")
        publication.append({
            "id": row["id"],
            "url": url,
            "title": row["title"],
            "category": row["category"],
            "editorial_chars": chars,
            "generated_at": TODAY,
            # 第4期は本文生成だけで公開扱いにしない。一次情報の実査、
            # 類似度、表示QAの全ゲートを通した記事だけ publish_ready にする。
            "source_validation": "pending",
            "uniqueness_validation": "pending",
            "visual_validation": "pending",
            "publish_ready": False,
        })
    PUBLICATION.write_text(json.dumps(publication, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    # 公開監査が完了するまでは、総合ガイドから第4期ページへ導線を出さない。
    remove_discovery()
    print(f"第4期300ページ生成: {len(publication)}件 / 最小編集本文 {min(p['editorial_chars'] for p in publication)}字")

if __name__ == "__main__":
    main()
