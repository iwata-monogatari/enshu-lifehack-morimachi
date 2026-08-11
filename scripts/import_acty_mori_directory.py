#!/usr/bin/env python3
"""Re-fetch and build a factual directory from the official Acty Mori site.

The importer intentionally stores only discrete facts. It does not ingest page
introductions, promotional prose, image captions, or social-media text. A run
fails when evidence markers change so that source changes receive human review.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


BASE_URL = "https://actymori.co.jp/"
USER_AGENT = "MorimachiInfoCatalog/1.0 (+https://morimachi.enshu-lifehack.com/)"
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

SOURCE_SPECS = [
    ("acty-home", "トップページ", BASE_URL, "全体案内", 0),
    ("acty-sitemap", "サイトマップ", BASE_URL + "sitemap", "恒常ページ一覧", 0),
    ("acty-company", "施設概要・周辺案内", BASE_URL + "company", "施設種別、周辺宿泊・キャンプ", 1),
    ("acty-enjoy", "楽しみ方", BASE_URL + "company/enjoy", "モデル所要時間", 0),
    ("acty-guide", "ご利用ガイド", BASE_URL + "company/guide", "受付、予約方法、服装、ペット制限", 1),
    ("acty-profile", "営業案内", BASE_URL + "profile", "営業時間、休業日、入場料、駐車場", 1),
    ("acty-access", "アクセス", BASE_URL + "access", "所在地、電話、車・鉄道、駐車台数", 1),
    ("acty-guidemap", "園内マップ・設備一覧", BASE_URL + "guidemap", "園内設備、支払い、受付場所", 1),
    ("acty-make", "創作体験", BASE_URL + "make", "陶芸、和紙、草木染め、樹脂粘土", 6),
    ("acty-play", "アウトドア体験", BASE_URL + "play", "自転車、テニス、カヌー、グラウンド・ゴルフ", 4),
    ("acty-eat", "食事・BBQ", BASE_URL + "eat", "レストラン、軽食、BBQ", 3),
    ("acty-shopping", "特産品販売", BASE_URL + "shopping", "売店営業時間、取扱品", 1),
    ("acty-pet", "ペット・ドッグラン", BASE_URL + "pet", "利用時間、料金、入場条件", 1),
    ("acty-booking", "予約一覧", BASE_URL + "booking", "予約対象、予約経路", 1),
    ("acty-booking-ayu", "鮎のつかみ取り予約", BASE_URL + "booking/booking-post/ayu", "予約掲載状態", 1),
    ("acty-booking-sup", "SUP予約", BASE_URL + "booking/booking-post/booking-sup", "予約掲載状態", 1),
    ("acty-faq", "よくある質問", BASE_URL + "faq", "年少者、予約、交通の補足条件", 1),
    ("acty-group", "団体利用", BASE_URL + "group", "団体人数、予約期限、定員、取消条件", 1),
]


def fact(label: str, value: Any) -> dict[str, Any]:
    return {"label": label, "value": value}


RECORDS: list[dict[str, Any]] = [
    {
        "id": "acty-facility",
        "name": "森町体験の里 アクティ森",
        "categories": ["施設", "体験"],
        "facts": [
            fact("営業時間", "9:00～17:30"),
            fact("冬季営業時間", "12月～2月は17:00まで"),
            fact("定休日", "水曜日、年末年始"),
            fact("祝日", "水曜日が祝日の場合は営業し、原則木曜日を休館"),
            fact("入場料", "無料"),
            fact("駐車場", "無料"),
        ],
        "source_url": BASE_URL + "profile",
        "evidence": ["9:00～17:30", "12月～2月は17:00まで", "入場料・駐車場", "無料"],
    },
    {
        "id": "acty-access",
        "name": "アクティ森へのアクセス",
        "categories": ["アクセス", "施設"],
        "facts": [
            fact("所在地", "〒437-0204 静岡県周智郡森町問詰1115-1"),
            fact("電話", "0538-85-0115"),
            fact("遠州森町スマートIC", "車で15分"),
            fact("森掛川IC", "車で15分"),
            fact("袋井IC", "車で30分"),
            fact("掛川IC", "車で40分"),
            fact("普通車", "200台"),
            fact("大型バス", "5台"),
            fact("遠州森駅", "タクシーで15分"),
        ],
        "source_url": BASE_URL + "access",
        "evidence": ["静岡県周智郡森町問詰1115-1", "0538-85-0115", "普通車", "200台", "大型バス", "5台"],
    },
    {
        "id": "acty-reception-guide",
        "name": "アクティ森の受付・予約方法",
        "categories": ["利用案内", "予約"],
        "facts": [
            fact("体験センター受付", ["陶芸", "吉川和紙", "草木染め", "ポリマークレイ", "ドッグラン", "バーベキュー", "テニス", "SUP", "カヌー", "グラウンド・ゴルフ"]),
            fact("専用受付", ["マウンテンバイクパーク", "レンタサイクル"]),
            fact("ネット予約", ["陶芸", "吉川和紙", "草木染め", "ポリマークレイ", "バーベキュー", "テニス"]),
            fact("問い合わせ予約", ["グラウンド・ゴルフ", "SUP", "カヌー", "ドッグラン貸切", "手ぶらBBQ注文内容"]),
            fact("ペット制限", ["体験センター", "よんな市", "レストラン", "グラウンド・ゴルフ場", "テニスコート", "BBQ場パーゴラ席付近"]),
        ],
        "source_url": BASE_URL + "company/guide",
        "evidence": ["各体験の受付場所", "ネット予約", "お問い合わせフォーム", "ペットの立ち入り制限エリア"],
    },
    {
        "id": "acty-facilities",
        "name": "アクティ森の園内設備",
        "categories": ["施設", "設備"],
        "facts": [
            fact("トイレ", ["体験センター内", "レストラン内", "体験センター前駐車場東側", "テニスコート東側"]),
            fact("車いす", "体験センター受付で無料貸出"),
            fact("おむつ交換台", ["体験センター内", "体験センター駐車場東側トイレ"]),
            fact("授乳室", "スポーツ体験受付棟"),
            fact("キャッシュレス", ["クレジットカード", "PayPay"]),
            fact("キャッシュレス対応場所", ["体験センター", "森のよんな市", "レストラン"]),
            fact("こども広場", ["砂場", "お絵描き黒板", "幼児用滑り台", "輪投げ"]),
            fact("テニスコート", "2面"),
            fact("グラウンド・ゴルフ場", "18ホール"),
        ],
        "source_url": BASE_URL + "guidemap",
        "evidence": ["車いす", "無料レンタル", "オムツ交換台", "授乳室", "キャッシュレス支払い"],
    },
    {
        "id": "acty-nearby-stays-camps",
        "name": "アクティ森周辺の宿泊・キャンプ",
        "categories": ["周辺施設", "宿泊", "キャンプ"],
        "facts": [
            fact("コテージ・アクティ", "アクティ森から車で2分"),
            fact("リバ・ウッド・リゾート", "グランピング、アクティ森から車で5分"),
            fact("吉川キャンプ場カワセミの里", "キャンプ場、アクティ森から車で9分"),
            fact("位置付け", "アクティ森周辺の別施設"),
        ],
        "source_url": BASE_URL + "company#spot",
        "evidence": ["コテージ・アクティ", "リバ・ウッド・リゾート", "吉川キャンプ場カワセミの里"],
    },
    {
        "id": "acty-pottery-handbuilding",
        "name": "陶芸 手ひねりコース",
        "categories": ["創作体験", "陶芸"],
        "facts": [
            fact("料金", "1個・粘土1kg以内 2,200円"),
            fact("団体料金", "20名以上 2,000円"),
            fact("所要時間", "1時間30分"),
            fact("予約期限", "Webは24時間前、メールは前日15:59、電話は当日可"),
            fact("定員", "20名"),
            fact("受付枠", ["9:45～11:15", "10:45～12:15", "11:30～13:00", "12:30～14:00", "13:15～14:45", "14:15～15:45", "15:00～16:30", "16:00～17:30"]),
            fact("作品受取", "約1か月半～2か月後、再来場または着払い宅配"),
        ],
        "source_url": BASE_URL + "make#tehineri_ryoukin",
        "evidence": ["陶芸 手ひねりコース", "2,200円", "体験所要時間", "1時間30分", "定員", "20名"],
    },
    {
        "id": "acty-pottery-painting",
        "name": "陶芸 絵付けコース",
        "categories": ["創作体験", "陶芸"],
        "facts": [
            fact("料金", ["湯のみ 1,430円", "茶碗 1,650円", "マグカップ 1,980円", "皿 1,980円"]),
            fact("団体料金", "20名以上の湯のみ 1,230円"),
            fact("所要時間", "1時間30分"),
            fact("予約期限", "Webは24時間前、メールは前日15:59、電話は当日可"),
            fact("定員", "10名"),
            fact("作品受取", "約1か月半～2か月後、再来場または着払い宅配"),
        ],
        "source_url": BASE_URL + "make#etuke_ryoukin",
        "evidence": ["陶芸　絵付けコース", "湯のみ", "1,430円", "定員", "10名"],
    },
    {
        "id": "acty-pottery-wheel",
        "name": "陶芸 電動ろくろコース",
        "categories": ["創作体験", "陶芸"],
        "facts": [
            fact("料金", "1個・粘土2kg以内 3,410円"),
            fact("所要時間", "1時間30分"),
            fact("受付枠", ["9:30～11:00", "10:30～12:00", "13:30～15:00", "14:30～16:00"]),
            fact("予約期限", "Webは24時間前、メールは前日15:59、電話は当日可"),
            fact("定員", "午前5名、午後5名"),
            fact("作品受取", "約1か月半～2か月後、再来場または着払い宅配"),
        ],
        "source_url": BASE_URL + "make#rokuro_ryoukin",
        "evidence": ["陶芸　電動ろくろコース", "3,410円", "午前：5名", "午後：5名"],
    },
    {
        "id": "acty-washi",
        "name": "和紙体験",
        "categories": ["創作体験", "和紙"],
        "facts": [
            fact("料金", ["葉すき小 1,100円", "葉すき大 1,320円", "はがき8枚 1,540円", "うちわ 1,540円", "カレンダー 1,870円", "ランプ 3,740円"]),
            fact("所要時間", "45分"),
            fact("受付枠", ["9:30～10:15", "11:00～11:45", "12:45～13:30", "14:00～14:45", "15:15～16:00"]),
            fact("予約期限", "Webは24時間前、メールは前日15:59、電話は当日可"),
            fact("定員", "6名"),
            fact("作品受取", "約1時間乾燥後、当日持ち帰り"),
        ],
        "source_url": BASE_URL + "make#washi",
        "evidence": ["和紙体験", "葉すき小", "1,100円", "定員", "6名"],
    },
    {
        "id": "acty-natural-dyeing",
        "name": "草木染め",
        "categories": ["創作体験", "染色"],
        "facts": [
            fact("料金", ["ハンカチ 1,540円", "巾着 1,650円", "A4エコバッグ 1,650円", "A3エコバッグ 1,980円", "バンダナ 1,980円", "手ぬぐい 1,980円", "ストール 2,530円"]),
            fact("所要時間", "45分"),
            fact("受付枠", ["10:00～10:45", "11:15～12:00", "13:00～13:45", "14:30～15:15", "15:45～16:30"]),
            fact("予約期限", "Webは24時間前、メールは前日15:59、電話は当日可"),
            fact("定員", "9名"),
            fact("作品受取", "当日持ち帰り"),
        ],
        "source_url": BASE_URL + "make#kusakizome",
        "evidence": ["草木染め", "ハンカチ", "1,540円", "定員", "9名"],
    },
    {
        "id": "acty-polymer-clay",
        "name": "ポリマークレイ",
        "categories": ["創作体験", "樹脂粘土"],
        "facts": [
            fact("料金", ["自由創作 1,210円", "スプーン小 1,540円", "フォーク小 1,540円", "スプーン大 1,870円"]),
            fact("所要時間", "45分"),
            fact("予約期限", "Webは24時間前、メールは前日15:59、電話は当日可"),
            fact("定員", "18名"),
            fact("作品受取", "約30分焼成後、当日持ち帰り"),
        ],
        "source_url": BASE_URL + "make#porimakurei",
        "evidence": ["ポリマークレイ", "自由創作", "1,210円", "定員", "18名"],
    },
    {
        "id": "acty-mtb-cycle",
        "name": "マウンテンバイクパーク・レンタサイクル",
        "categories": ["アウトドア体験", "自転車"],
        "facts": [
            fact("コース", "初級から上級まで5コース"),
            fact("未就学児", "超初級コースを利用可"),
            fact("案内先", "Mountain Ride Hub"),
        ],
        "related_url": "https://mountain-ride-hub.jp/park/forecha",
        "source_url": BASE_URL + "play#rentasaikuru",
        "evidence": ["マウンテンバイクパーク", "未就学児", "5コース", "レンタサイクル"],
    },
    {
        "id": "acty-tennis",
        "name": "レンタルテニスコート",
        "categories": ["アウトドア体験", "テニス"],
        "facts": [
            fact("コート", "砂入り人工芝2面"),
            fact("料金", ["平日1時間 1,430円", "土日祝1時間 1,980円", "森町在住・平日1時間 1,100円", "森町在住・土日祝1時間 1,650円"]),
            fact("貸出", "ラケット1本110円、ボール2個無料"),
            fact("受付時間", "9:00～16:30、12月～2月は16:00まで"),
            fact("服装", "運動靴、貸靴なし"),
            fact("予約", "インターネットまたは電話を推奨"),
        ],
        "source_url": BASE_URL + "play#tenisu",
        "evidence": ["レンタルテニスコート", "1,430円", "1,980円", "貸出ラケット", "110円"],
    },
    {
        "id": "acty-canoe",
        "name": "カヌー体験",
        "categories": ["アウトドア体験", "水上体験"],
        "facts": [
            fact("開催期間", "4月中旬～9月中旬の土日祝日"),
            fact("料金", "1人2,200円"),
            fact("小学3年生以下", "保護者と2人乗り、追加330円"),
            fact("小学4年生以上の単独乗艇", "保護者同伴が必要"),
            fact("所要時間", "約60分"),
            fact("予約期限", "5営業日前、完全予約制"),
            fact("定員", "6名"),
            fact("持ち物", ["濡れてもよい服装", "着替え", "タオル"]),
        ],
        "source_url": BASE_URL + "play#kanu",
        "evidence": ["カヌー", "2,200円", "小学三年生以下", "+330円", "完全予約制"],
    },
    {
        "id": "acty-ground-golf",
        "name": "グラウンド・ゴルフ",
        "categories": ["アウトドア体験", "ゴルフ"],
        "facts": [
            fact("料金", ["4時間 440円", "8時間 550円", "貸しクラブ・ボール付 220円"]),
            fact("コース", "1ラウンド16ホール"),
            fact("受付時間", "9:00～16:30、12月～2月は16:00まで"),
            fact("予約", "個人は不要、団体は必要"),
        ],
        "source_url": BASE_URL + "play#guraund_gorufu",
        "evidence": ["グラウンド・ゴルフ", "4時間", "440円", "8時間", "550円"],
    },
    {
        "id": "acty-restaurant-kawasemi",
        "name": "森のレストラン かわせみ",
        "categories": ["食事", "レストラン"],
        "facts": [
            fact("席数", "70席"),
            fact("営業時間", "10:00～16:00、ラストオーダー15:00"),
            fact("定休日", "火曜日・水曜日、祝日は営業して別日に休業"),
            fact("団体", "旅行、宴会、法事は予算に応じた食事を相談可"),
        ],
        "source_url": BASE_URL + "eat#kawasemi",
        "evidence": ["森のレストラン かわせみ", "席数70", "10:00～16:00", "15:00"],
    },
    {
        "id": "acty-hakkakuan",
        "name": "八角庵",
        "categories": ["食事", "軽食"],
        "facts": [
            fact("営業日", "土日祝日"),
            fact("営業時間", "10:00～15:00"),
            fact("商品", "あまごの塩焼き"),
            fact("価格", "700円"),
        ],
        "source_url": BASE_URL + "eat#hakkakuan",
        "evidence": ["八角庵", "土日祝日", "10:00～15:00"],
    },
    {
        "id": "acty-bbq",
        "name": "アクティ森 バーベキュー",
        "categories": ["食事", "バーベキュー"],
        "facts": [
            fact("利用時間", "10:00～15:00"),
            fact("手ぶら料金", ["Aコース 2,750円", "Bコース 3,300円", "食事なし・中学生以上 550円"]),
            fact("手ぶら予約", "5営業日前まで、完全予約制、1区画最低4食"),
            fact("手ぶら取消料", "前日50%、当日100%"),
            fact("場所貸し料金", "8名まで1区画4,400円、4名まで追加可・1人550円"),
            fact("場所貸し器材", "1セット2,200円"),
            fact("場所貸し予約", "利用日前日まで、完全予約制"),
            fact("屋根", "全席あり"),
            fact("ペット", "同伴不可"),
        ],
        "source_url": BASE_URL + "eat#bbq",
        "evidence": ["手ぶらでバーベキュー", "2,750円", "場所貸しバーベキュー", "4,400円", "完全予約制"],
    },
    {
        "id": "acty-yonnaichi",
        "name": "森のよんな市",
        "categories": ["売店", "特産品"],
        "facts": [
            fact("営業時間", "9:30～16:00"),
            fact("取扱例", ["梅衣", "みそまんじゅう", "麦こがしまんじゅう アクティ森", "次郎柿ワイン"]),
        ],
        "source_url": BASE_URL + "shopping#yonnaichi",
        "evidence": ["森のよんな市", "9:30～16:00", "梅衣", "みそまんじゅう", "次郎柿ワイン"],
    },
    {
        "id": "acty-dog-run",
        "name": "アクティ森 ドッグラン",
        "categories": ["ペット", "ドッグラン"],
        "facts": [
            fact("小・中型犬", "12kg未満"),
            fact("大型犬", "12kg以上"),
            fact("利用枠", "小・中型犬と大型犬を1時間交代"),
            fact("通常料金", "施設利用者は無料"),
            fact("貸切", "1団体33,000円"),
            fact("年少者", "中学生以下は保護者同伴"),
            fact("対象動物", "犬のみ"),
            fact("入場不可", ["1年以内に狂犬病・各種ワクチンを受けていない犬", "発情期の犬", "伝染性の病気の犬"]),
            fact("受付", "体験センターで同意書記入とメンバーカード発行"),
        ],
        "source_url": BASE_URL + "pet#dogrun",
        "evidence": ["12㎏未満", "12㎏以上", "33,000円", "中学生以下", "保護者の同伴"],
    },
    {
        "id": "acty-ayu-booking",
        "name": "夏季限定 鮎のつかみ取り",
        "categories": ["アウトドア体験", "季節体験"],
        "facts": [fact("掲載状態", "予約一覧に掲載"), fact("予約経路", "公式予約ページ")],
        "source_url": BASE_URL + "booking/booking-post/ayu",
        "evidence": ["予約する・予約を確認する一覧に戻る"],
    },
    {
        "id": "acty-sup-booking",
        "name": "SUP",
        "categories": ["アウトドア体験", "水上体験"],
        "facts": [fact("予約掲載", "公式予約一覧に掲載"), fact("現在の予約カレンダー", "利用不可表示")],
        "source_url": BASE_URL + "booking/booking-post/booking-sup",
        "evidence": ["この予約カレンダーは現在利用することができません"],
    },
    {
        "id": "acty-pattern-golf-booking",
        "name": "パターゴルフ",
        "categories": ["アウトドア体験", "ゴルフ"],
        "facts": [fact("掲載状態", "予約一覧に掲載"), fact("案内先", "問い合わせ")],
        "source_url": BASE_URL + "booking",
        "evidence": ["パターゴルフ", "お問い合わせ"],
    },
    {
        "id": "acty-faq-conditions",
        "name": "アクティ森 FAQ利用条件",
        "categories": ["利用案内", "予約"],
        "facts": [
            fact("見学", "自由"),
            fact("年少者", "保護者が補助すれば電動ろくろ以外を体験可"),
            fact("予約なし", "電動ろくろ以外は空きがあれば可能"),
            fact("要予約", ["カヌー", "レンタルマウンテンバイク"]),
            fact("公共交通", "遠州森駅から町営バス、便数が少ない"),
        ],
        "source_url": BASE_URL + "faq",
        "evidence": ["見学はできますか", "小さい子ども", "電動ろくろ以外", "町営バス"],
    },
    {
        "id": "acty-group-use",
        "name": "アクティ森 団体利用",
        "categories": ["団体", "予約"],
        "facts": [
            fact("団体料金の基準", "20名以上"),
            fact("基本予約期限", "2週間前"),
            fact("連絡先", "0538-85-0115"),
            fact("陶芸手ひねり定員", "120名"),
            fact("陶芸絵付け定員", "150名"),
            fact("ポリマークレイ定員", "120名"),
            fact("草木染め定員", "20名、ハンカチのみ40名"),
            fact("レストラン最終人数", "3営業日前17時"),
            fact("団体BBQ席数", "144席"),
            fact("取消料発生日", ["体験はなし", "レストランは2日前", "BBQは5日前"]),
        ],
        "source_url": BASE_URL + "group",
        "evidence": ["20名様以上", "2週間前", "120名", "150名", "144席"],
    },
]


def canonical_page_url(url: str) -> str:
    split = urlsplit(url)
    return urlunsplit((split.scheme.lower(), split.netloc.lower(), split.path or "/", split.query, ""))


def fetch(url: str, retries: int = 3) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ja,en;q=0.5",
        },
    )
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=30) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt + 1 == retries:
                raise RuntimeError(f"fetch failed: {url}: {exc}") from exc
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")


def page_text(page: str) -> str:
    page = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", page, flags=re.I | re.S)
    page = re.sub(r"<br\s*/?>|</(?:p|li|tr|td|th|dt|dd|h[1-6]|section|article|div)>", "\n", page, flags=re.I)
    text = html.unescape(TAG_RE.sub(" ", page)).replace("\u3000", " ").replace("\xa0", " ")
    return "\n".join(SPACE_RE.sub(" ", line).strip() for line in text.splitlines() if line.strip())


def evidence_text(value: str) -> str:
    return SPACE_RE.sub(" ", value.replace("\u3000", " ").replace("\xa0", " ")).strip()


def validate_blueprints() -> None:
    ids: set[str] = set()
    urls: set[str] = set()
    source_urls = {canonical_page_url(item[2]) for item in SOURCE_SPECS}
    forbidden_keys = {"description", "catch", "copy", "source_text"}
    forbidden_term = chr(25919) + chr(31574)
    for record in RECORDS:
        record_id = record["id"]
        source_url = record["source_url"]
        if record_id in ids:
            raise ValueError(f"duplicate id: {record_id}")
        if source_url in urls:
            raise ValueError(f"duplicate source_url: {source_url}")
        ids.add(record_id)
        urls.add(source_url)
        if canonical_page_url(source_url) not in source_urls:
            raise ValueError(f"record source page is absent from registry: {source_url}")
        if urlsplit(source_url).scheme != "https":
            raise ValueError(f"non-HTTPS source_url: {source_url}")
        if forbidden_keys.intersection(record):
            raise ValueError(f"forbidden key in {record_id}")
        if forbidden_term in json.dumps(record, ensure_ascii=False):
            raise ValueError(f"forbidden term in {record_id}")


def build_directory(checked_at: str, *, offline: bool = False) -> dict[str, Any]:
    validate_blueprints()
    pages: dict[str, str] = {}
    if not offline:
        for _, name, url, _, _ in SOURCE_SPECS:
            print(f"fetch: {name}: {url}", file=sys.stderr)
            pages[canonical_page_url(url)] = page_text(fetch(url))

        for record in RECORDS:
            source_page = pages[canonical_page_url(record["source_url"])]
            missing = [
                marker for marker in record["evidence"] if evidence_text(marker) not in source_page
            ]
            if missing:
                raise RuntimeError(f"source changed for {record['id']}; missing evidence: {missing}")

    records = []
    for blueprint in RECORDS:
        record = deepcopy(blueprint)
        record.pop("evidence")
        record["checked_at"] = checked_at
        record["as_of"] = checked_at
        records.append(record)

    indexed_by_url: dict[str, int] = {}
    for record in records:
        key = canonical_page_url(record["source_url"])
        indexed_by_url[key] = indexed_by_url.get(key, 0) + 1

    sources = []
    for source_id, name, url, scope, expected in SOURCE_SPECS:
        indexed = indexed_by_url.get(canonical_page_url(url), 0)
        if indexed != expected:
            raise ValueError(f"coverage mismatch for {source_id}: expected {expected}, indexed {indexed}")
        sources.append(
            {
                "id": source_id,
                "name": name,
                "url": url,
                "scope": scope,
                "expected_records": expected,
                "indexed_records": indexed,
                "status": "verified" if not offline else "offline-snapshot",
                "checked_at": checked_at,
                "as_of": checked_at,
            }
        )
    return {"checked_at": checked_at, "as_of": checked_at, "sources": sources, "records": records}


def main() -> int:
    default_output = Path(__file__).resolve().parents[1] / "data" / "acty-mori-directory.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--checked-at", default=date.today().isoformat())
    parser.add_argument("--offline", action="store_true", help="write the reviewed snapshot without network checks")
    args = parser.parse_args()
    payload = build_directory(args.checked_at, offline=args.offline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['records'])} records to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
