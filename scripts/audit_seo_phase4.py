#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4期300ページの公開ゲート。"""
import argparse, json, re, subprocess, sys, xml.etree.ElementTree as ET
from collections import Counter
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

def jsonld_types(html):
    """文字列の空白形式に依存せずJSON-LDの型を数える。"""
    types=[]
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',html,re.I|re.S):
        try:
            data=json.loads(unescape(raw))
        except (json.JSONDecodeError,TypeError):
            types.append('__INVALID__'); continue
        nodes=data.get('@graph',[]) if isinstance(data,dict) and '@graph' in data else [data]
        for node in nodes:
            if isinstance(node,dict):
                kind=node.get('@type',[])
                types.extend(kind if isinstance(kind,list) else [kind])
    return types

def chars(html):
    m=re.search(r'<article class="post-editorial-body">(.*?)</article>',html,re.S)
    text=re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>','',m.group(1) if m else '',flags=re.S)
    return len(re.sub(r'\s+','',text))

def visible_text(fragment):
    return re.sub(r'\s+', '', unescape(re.sub(r'<[^>]+>', '', fragment)))

def enrichment_rows():
    rows=[]
    for start in (1,101,201):
        path=ROOT/'data'/f'seo-phase4-enrichment-{start:03d}-{start+99:03d}.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        rows.extend(data.get('records', data) if isinstance(data,dict) else data)
    return {int(r['id']):r for r in rows}

def is_verified(row):
    return (row.get('human_reviewed') is True
            and row.get('source_validation') == 'verified'
            and row.get('uniqueness_validation') == 'verified'
            and row.get('visual_validation') == 'verified')

def normalized_identity(value):
    value=visible_text(value).replace('森町ライフハック','').replace('静岡県','')
    return re.sub(r'[^0-9A-Za-zぁ-んァ-ヶ一-龠々ー]+','',value).lower()

def audit_existing_duplicates(selected, publication, failures):
    """選択IDと、すでに公開されているページの衝突を検査する。"""
    selected_ids={int(row['id']) for row in selected}
    selected_urls={row['url'] for row in selected}
    selected_url_paths={urlparse(url).path.rstrip('/')+'/' for url in selected_urls}
    selected_paths={(ROOT/row['url'].strip('/')/'index.html').resolve() for row in selected}
    selected_titles={normalized_identity(row.get('title','')):row['id'] for row in selected}
    selected_paragraphs={}
    for row in selected:
        page=ROOT/row['url'].strip('/')/'index.html'
        html=page.read_text(encoding='utf-8',errors='replace') if page.is_file() else ''
        article=re.search(r'<article class="post-editorial-body">(.*?)</article>',html,re.S)
        selected_paragraphs[int(row['id'])]={
            normalized_identity(fragment) for fragment in re.findall(r'<p[^>]*>(.*?)</p>',article.group(1) if article else '',re.S)
            if len(visible_text(fragment))>=40
        }
    for other in publication:
        if int(other['id']) in selected_ids or other.get('publish_ready') is not True or not is_verified(other):
            continue
        identity=normalized_identity(other.get('title',''))
        if identity and identity in selected_titles:
            failures.append(f"既存公開Phase4とのタイトル重複: {selected_titles[identity]} / {other['id']}")

    sitemap=ROOT/'sitemap.xml'
    if not sitemap.is_file():
        failures.append('既存公開ページ重複監査に必要なsitemap.xmlがありません')
        return
    try:
        tree=ET.parse(sitemap)
        published_urls=[elem.text.strip() for elem in tree.getroot().iter() if elem.tag.rsplit('}',1)[-1]=='loc' and elem.text]
    except ET.ParseError as ex:
        failures.append(f'sitemap.xmlを解析できません: {ex}')
        return
    for published_url in published_urls:
        relative=urlparse(published_url).path.strip('/')
        path=ROOT/relative/'index.html' if relative else ROOT/'index.html'
        if not path.is_file():
            failures.append(f'sitemap掲載HTMLなし: {published_url}')
            continue
        if path.resolve() in selected_paths: continue
        html=path.read_text(encoding='utf-8',errors='replace')
        if re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex',html,re.I): continue
        canonical=re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"',html,re.I)
        canonical_path=(urlparse(canonical.group(1)).path.rstrip('/')+'/') if canonical else ''
        if canonical and (canonical.group(1) in selected_urls or canonical_path in selected_url_paths):
            failures.append(f"既存公開ページとのcanonical重複: {canonical.group(1)} ({path.relative_to(ROOT)})")
            continue
        candidates=re.findall(r'<(?:title|h1)[^>]*>(.*?)</(?:title|h1)>',html,re.I|re.S)
        for candidate in candidates:
            identity=normalized_identity(candidate)
            if identity and identity in selected_titles:
                failures.append(f"既存公開ページとのタイトル/見出し重複: {selected_titles[identity]} ({path.relative_to(ROOT)})")
                break
        body=re.search(r'<article\b[^>]*>(.*?)</article>',html,re.I|re.S)
        if not body:
            body=re.search(r'<main\b[^>]*>(.*?)</main>',html,re.I|re.S)
        existing={
            normalized_identity(fragment) for fragment in re.findall(r'<p[^>]*>(.*?)</p>',body.group(1) if body else '',re.S)
            if len(visible_text(fragment))>=40
        }
        for item_id,fingerprints in selected_paragraphs.items():
            ratio=len(fingerprints & existing)/max(1,len(fingerprints))
            if ratio>0.25:
                failures.append(f"既存公開ページとの段落重複率が25%超: ID {item_id} {ratio:.1%} ({path.relative_to(ROOT)})")

def refresh_public_surfaces():
    commands=[
        ([sys.executable,str(ROOT/'scripts/build_sitemap.py')],'sitemap'),
        (['node',str(ROOT/'scripts/build-search-index.mjs')],'search index'),
        ([sys.executable,str(ROOT/'scripts/preflight_check.py')],'preflight'),
    ]
    for command,label in commands:
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if result.returncode:
            raise SystemExit(f"{label}更新/検証失敗\n"+result.stdout+result.stderr)

def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument('--release',action='store_true',help='選択範囲の全監査合格時だけ公開台帳を公開可へ更新')
    mode.add_argument('--withdraw',action='store_true',help='公開状態を解除しnoindexへ戻す')
    ap.add_argument('--ids',help='監査・公開するID。例: 1,4,10-12（省略時は全300件）')
    args=ap.parse_args()
    pub=json.loads((ROOT/'data/seo-phase4-publication.json').read_text(encoding='utf-8'))
    from build_seo_phase4 import ensure_release_quality, load_rows, parse_ids, set_release_state
    all_rows=load_rows()
    try:
        selected_ids=parse_ids(args.ids,{int(row['id']) for row in all_rows})
    except (TypeError,ValueError) as ex:
        raise SystemExit(f'ID指定が不正です: {ex}') from ex
    selected_pub=[row for row in pub if int(row['id']) in selected_ids]
    selected_rows=[row for row in all_rows if int(row['id']) in selected_ids]
    if len(selected_pub)!=len(selected_ids) or len(selected_rows)!=len(selected_ids):
        raise SystemExit('指定IDが公開台帳または生成台帳にありません')
    if args.withdraw:
        for item in selected_pub:
            item.update(source_validation='pending',uniqueness_validation='pending',visual_validation='pending',human_reviewed=False,publish_ready=False)
        (ROOT/'data/seo-phase4-publication.json').write_text(json.dumps(pub,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        set_release_state(selected_rows, False)
        refresh_public_surfaces()
        print(f'第4期公開状態を解除しました: {len(selected_ids)}件')
        return
    if args.ids is None:
        readability=subprocess.run(
            [sys.executable, str(ROOT/'scripts/audit_phase4_readability.py')],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if readability.returncode != 0:
            raise SystemExit(readability.stdout + readability.stderr)
    else:
        from audit_phase4_readability import audit_page
        readability_failures=[]
        for row in selected_pub:
            result=audit_page(row)
            if result.get('failures'):
                readability_failures.extend(f"ID {row['id']}: {item}" for item in result['failures'])
        if readability_failures:
            raise SystemExit('可読性監査失敗\n- '+'\n- '.join(readability_failures))
    enriched=enrichment_rows()
    topics={int(r['id']):r for r in json.loads((ROOT/'data/seo-phase4-topics.json').read_text(encoding='utf-8'))}
    from build_seo_phase4 import canonical_url
    expected_urls={item_id:canonical_url(row) for item_id,row in topics.items()}
    failures=[]
    paragraphs=[]; normalized_paragraphs=[]; faq_questions=[]; svg_structures=set()
    if len(pub)!=300 or len({int(p['id']) for p in pub})!=300 or len({p['url'] for p in pub})!=300:
        failures.append('公開台帳が300固有ID・URLではありません')
    for p in selected_pub:
        d=ROOT/p['url'].strip('/'); path=d/'index.html'
        if not path.is_file(): failures.append(f"HTMLなし {p['url']}"); continue
        h=path.read_text(encoding='utf-8'); n=chars(h)
        row={**topics.get(int(p['id']),{}),**enriched.get(int(p['id']),{})}
        types=jsonld_types(h)
        source_urls=[s.get('url','') for s in row.get('sources',[])]
        fact_urls=[f.get('source_url','') for f in row.get('verified_facts',[]) if isinstance(f,dict)]
        checks={
            '6000〜8000文字':6000<=n<=8000, 'H1一つ':h.count('<h1')==1, 'H2十個以上':h.count('<h2')>=10,
            '画像三点':h.count('<img ')>=3, '画像レスポンシブ':h.count('style="width:100%;height:auto"')>=3,
            'canonical一つ':h.count('rel="canonical"')==1, 'description一つ':h.count('name="description"')==1,
            'OGP':all(h.count(x)==1 for x in ['property="og:title"','property="og:description"','property="og:url"','property="og:image"']),
            '構造化データ各一つ':all(types.count(x)==1 for x in ['WebPage','FAQPage','BreadcrumbList']) and '__INVALID__' not in types,
            '内部リンク五つ':len(re.findall(r'href="/(?!/)',h))>=5, '一次情報三つ':h.count('target="_blank"')>=3,
            '固有事実六つ':len(row.get('verified_facts',[]))>=6,
            '森町条件三つ':len(row.get('morimachi_conditions',[]))>=3,
            '固有FAQ四つ':len(row.get('faqs',[]))>=4,
            '検証済み出典三つ':len(source_urls)==len(set(source_urls)) and len(source_urls)>=3 and all(u.startswith('https://') for u in source_urls) and all(str(s.get('status','')).lower()=='verified' or str(s.get('status','')).lower().startswith('verified-') for s in row.get('sources',[])),
            '固有事実の出典対応':bool(fact_urls) and all(u in set(source_urls) for u in fact_urls),
            '台帳とHTMLの対応':p.get('url')==expected_urls.get(int(p['id'])) and p.get('title')==row.get('title') and p.get('category')==row.get('category') and p.get('editorial_chars')==n,
            '公開状態とnoindexの整合':h.count('data-phase4-pending')==(0 if p.get('publish_ready') is True else 1),
            '大石の視点':'大石の視点' in h, '禁止語なし':('政'+'策') not in h,
            '編集語なし':not any(term in h for term in ('焦点「','断定防止','第1論点','第2論点','第3論点','テンプレート','カニバリ')),
            '句読点正常':'。。' not in h and '？？' not in h,
        }
        bad=[k for k,v in checks.items() if not v]
        if bad: failures.append(f"{p['url']} {n}字: {','.join(bad)}")
        article=re.search(r'<article class="post-editorial-body">(.*?)</article>',h,re.S)
        for fragment in re.findall(r'<p[^>]*>(.*?)</p>',article.group(1) if article else '',re.S):
            text=visible_text(fragment)
            if not text: continue
            paragraphs.append(text)
            normalized=text.replace(p['title'],'').replace(row.get('search_intent',''),'')
            normalized=re.sub(r'https?://[^\s]+|\d+','',normalized)
            normalized_paragraphs.append(normalized)
        faq_questions.extend(item.get('question','') for item in row.get('faqs',[]))
        for name in ('cover.svg','fig1.svg','fig2.svg'):
            svg=d/name
            try:
                tree=ET.parse(svg)
                svg_structures.add(tuple(elem.tag.rsplit('}',1)[-1] for elem in tree.getroot().iter()))
            except Exception as ex: failures.append(f"SVG不正 {svg}: {ex}")
    exact=Counter(paragraphs); normalized=Counter(normalized_paragraphs)
    exact_ratio=sum(v for v in exact.values() if v>1)/max(1,len(paragraphs))
    normalized_ratio=sum(v for v in normalized.values() if v>1)/max(1,len(normalized_paragraphs))
    if exact_ratio>0.25: failures.append(f'完全一致段落率が25%超: {exact_ratio:.1%}')
    if normalized_ratio>0.25: failures.append(f'正規化後反復率が25%超: {normalized_ratio:.1%}')
    if args.ids is None and len(set(faq_questions)) < 1100: failures.append(f'FAQ質問の固有数不足: {len(set(faq_questions))}/1200')
    if args.ids is not None and len(set(faq_questions)) != len(faq_questions): failures.append('選択コホート内でFAQ質問が重複しています')
    if args.ids is None and len(svg_structures) < 30: failures.append(f'SVG構造の種類不足: {len(svg_structures)}')
    audit_existing_duplicates(selected_pub,pub,failures)
    if failures: raise SystemExit('第4期監査失敗\n- '+'\n- '.join(failures[:80]))
    if args.release:
        unverified=[item.get('url') for item in selected_pub if not is_verified(item)]
        if unverified:
            raise SystemExit(
                '選択コホートに人間確認またはsource/uniqueness/visual検証が未完了のIDがあります。'
                f' 未承認={len(unverified)}件'
            )
        ensure_release_quality(selected_rows)
        for item in selected_pub:
            item['publish_ready']=True
        (ROOT/'data/seo-phase4-publication.json').write_text(json.dumps(pub,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        set_release_state(selected_rows, True)
        refresh_public_surfaces()
    print(f"第4期監査: {len(selected_pub)}ページ合格 / 編集本文 {min(p['editorial_chars'] for p in selected_pub)}字以上 / 完全一致 {exact_ratio:.1%} / 正規化後 {normalized_ratio:.1%} / SVG構造 {len(svg_structures)}種")

if __name__=='__main__': main()
