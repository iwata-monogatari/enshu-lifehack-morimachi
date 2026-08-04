#!/usr/bin/env python3
"""data/checklists.json からライフイベント・チェックリストページを生成する。

出力先: checklist/<slug>/index.html
チェック状態は localStorage(キー: enshu-checklist-<slug>)に保持し、進捗バーを表示する。
共通パーツは他ページと同じ <!-- PART:xxx:START/END --> マーカーで埋め込むため、
scripts/inject_parts.py の対象になる。

磐田版からの変更点: 全 href が実在ページを指しているかを生成前に検証する。
チェックリストは「既存155ページに必ず着地させる」導線(01計画書1-B)なので、
リンク切れは仕様違反として扱い、1件でもあれば生成せずに落とす。

使い方: python scripts/build_checklists.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKLISTS_PATH = os.path.join(ROOT, "data", "checklists.json")
PARTS_DIR = os.path.join(ROOT, "parts")
OUT_DIR = os.path.join(ROOT, "checklist")

SITE_NAME = "森町ライフハック"


def load_parts():
    parts = {}
    for name in ("head-css", "header", "disclaimer", "footer"):
        with open(os.path.join(PARTS_DIR, "%s.html" % name), encoding="utf-8") as f:
            parts[name] = f.read().strip()
    return parts


def part_markup(name, content):
    return "<!-- PART:%s:START -->%s<!-- PART:%s:END -->" % (name, content, name)


def validate(data):
    """href が実在するページを指しているか確認する。"""
    broken = []
    for cl in data["checklists"]:
        for t in cl["tasks"]:
            target = os.path.join(ROOT, t["href"].strip("/").replace("/", os.sep), "index.html")
            if not os.path.isfile(target):
                broken.append("%s / %s -> %s" % (cl["slug"], t["id"], t["href"]))
    return broken


def build_page(checklist, parts):
    slug, title, emoji, lead = checklist["slug"], checklist["title"], checklist["emoji"], checklist["lead"]
    tasks = checklist["tasks"]
    storage_key = "enshu-checklist-%s" % slug

    items_html = "".join(
        '<li class="checklist-item" data-task-id="%s">'
        '<label class="checklist-label">'
        '<input type="checkbox" class="checklist-check" data-task-id="%s" data-track-click="checklist_check">'
        '<span class="checklist-text">%s</span>'
        "</label>"
        '<a class="checklist-link" href="%s">くわしく見る</a>'
        "</li>" % (t["id"], t["id"], t["label"], t["href"])
        for t in tasks
    )

    script = (
        "<script>(function(){"
        "var KEY=%s;var ids=%s;"
        "var box=document.getElementById('checklist-box');if(!box){return;}"
        "var bar=document.getElementById('checklist-progress-bar');"
        "var label=document.getElementById('checklist-progress-label');"
        "function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}');}catch(e){return {};}}"
        "function save(state){try{localStorage.setItem(KEY,JSON.stringify(state));}catch(e){}}"
        "function render(){"
        "var state=load();var done=0;"
        "ids.forEach(function(id){"
        "var cb=box.querySelector('.checklist-check[data-task-id=\"'+id+'\"]');"
        "var li=box.querySelector('.checklist-item[data-task-id=\"'+id+'\"]');"
        "var checked=!!state[id];"
        "if(cb){cb.checked=checked;}"
        "if(li){li.classList.toggle('is-done',checked);}"
        "if(checked){done++;}"
        "});"
        "var pct=ids.length?Math.round(done/ids.length*100):0;"
        "if(bar){bar.style.width=pct+'%%';}"
        "if(label){label.textContent=done+' / '+ids.length+' 完了';}"
        "if(done===ids.length&&ids.length){box.classList.add('is-complete');}else{box.classList.remove('is-complete');}"
        "}"
        "box.addEventListener('change',function(e){"
        "var cb=e.target.closest('.checklist-check');if(!cb){return;}"
        "var state=load();state[cb.getAttribute('data-task-id')]=cb.checked;save(state);render();"
        "});"
        "render();"
        "})();</script>"
    ) % (json.dumps(storage_key, ensure_ascii=False), json.dumps([t["id"] for t in tasks], ensure_ascii=False))

    page_url = "https://morimachi.enshu-lifehack.com/checklist/%s/" % slug
    html = (
        '<!doctype html><html lang="ja"><head>\n'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>%s | チェックリスト | %s</title>\n"
        '<meta name="description" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="%s">'
        '<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
        '<meta property="og:url" content="%s"><meta name="twitter:card" content="summary">\n'
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        "%s\n"
        "</head><body>\n"
        "%s\n"
        "%s\n"
        '<main id="main"><div class="wrap">\n'
        '<p class="breadcrumb"><a href="/">%s</a> ／ チェックリスト ／ %s</p>\n'
        '<section class="hero"><div class="hero-visual"><h1><span aria-hidden="true">%s</span> %s</h1></div>'
        '<div class="hero-body"><p class="lead">%s</p></div></section>\n'
        '<div id="checklist-box" class="checklist-box">\n'
        '<div class="checklist-progress"><div class="checklist-progress-track">'
        '<div id="checklist-progress-bar" class="checklist-progress-bar"></div></div>'
        '<p id="checklist-progress-label" class="checklist-progress-label">0 / %d 完了</p></div>\n'
        '<ul class="checklist-list">%s</ul>\n'
        '<p class="checklist-note mini">チェックはこの端末のブラウザに保存されます。他の端末とは共有されません。'
        "手続きの詳細・最新情報は各リンク先ページ、または森町公式サイトで必ず確認してください。</p>\n"
        "</div>\n"
        "%s\n"
        "</div></main>\n"
        "%s\n"
        "</body></html>\n"
    ) % (
        title, SITE_NAME, lead, page_url,
        SITE_NAME, title, lead, page_url,
        part_markup("head-css", parts["head-css"]),
        part_markup("header", parts["header"]),
        part_markup("disclaimer", parts["disclaimer"]),
        SITE_NAME, title,
        emoji, title, lead,
        len(tasks), items_html, script,
        part_markup("footer", parts["footer"]),
    )

    out_path = os.path.join(OUT_DIR, slug, "index.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    return out_path


def main():
    with open(CHECKLISTS_PATH, encoding="utf-8-sig") as f:
        data = json.load(f)

    broken = validate(data)
    if broken:
        print("リンク切れのため生成を中止しました（%d件）:" % len(broken))
        for b in broken:
            print("  " + b)
        return 1

    parts = load_parts()
    generated = [os.path.relpath(build_page(cl, parts), ROOT) for cl in data["checklists"]]
    total = sum(len(cl["tasks"]) for cl in data["checklists"])
    print("生成 %d ページ / タスク %d 件 / リンク切れ 0" % (len(generated), total))
    for p in generated:
        print("  " + p.replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
