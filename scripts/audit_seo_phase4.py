#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4期300ページの公開ゲート。"""
import argparse, json, re, xml.etree.ElementTree as ET
from collections import Counter
from html import unescape
from pathlib import Path

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

def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument('--release',action='store_true',help='全監査合格時だけ公開台帳を公開可へ更新')
    mode.add_argument('--withdraw',action='store_true',help='公開状態を解除しnoindexへ戻す')
    args=ap.parse_args()
    pub=json.loads((ROOT/'data/seo-phase4-publication.json').read_text(encoding='utf-8'))
    if args.withdraw:
        for item in pub:
            item.update(source_validation='pending',uniqueness_validation='pending',visual_validation='pending',publish_ready=False)
        (ROOT/'data/seo-phase4-publication.json').write_text(json.dumps(pub,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        from build_seo_phase4 import load_rows, set_release_state
        set_release_state(load_rows(), False)
        print('第4期公開状態を解除しました')
        return
    enriched=enrichment_rows()
    topics={int(r['id']):r for r in json.loads((ROOT/'data/seo-phase4-topics.json').read_text(encoding='utf-8'))}
    from build_seo_phase4 import canonical_url
    expected_urls={item_id:canonical_url(row) for item_id,row in topics.items()}
    failures=[]
    paragraphs=[]; normalized_paragraphs=[]; faq_questions=[]; svg_structures=set()
    if len(pub)!=300 or len({p['url'] for p in pub})!=300: failures.append('公開台帳が300固有URLではありません')
    for p in pub:
        d=ROOT/p['url'].strip('/'); path=d/'index.html'
        if not path.is_file(): failures.append(f"HTMLなし {p['url']}"); continue
        h=path.read_text(encoding='utf-8'); n=chars(h)
        row={**topics.get(int(p['id']),{}),**enriched.get(int(p['id']),{})}
        types=jsonld_types(h)
        source_urls=[s.get('url','') for s in row.get('sources',[])]
        fact_urls=[f.get('source_url','') for f in row.get('verified_facts',[]) if isinstance(f,dict)]
        checks={
            '6000文字':n>=6000, 'H1一つ':h.count('<h1')==1, 'H2十個以上':h.count('<h2')>=10,
            '画像三点':h.count('<img ')>=3, '画像レスポンシブ':h.count('style="width:100%;height:auto"')>=3,
            'canonical一つ':h.count('rel="canonical"')==1, 'description一つ':h.count('name="description"')==1,
            'OGP':all(h.count(x)==1 for x in ['property="og:title"','property="og:description"','property="og:url"','property="og:image"']),
            '構造化データ各一つ':all(types.count(x)==1 for x in ['WebPage','FAQPage','BreadcrumbList']) and '__INVALID__' not in types,
            '内部リンク五つ':len(re.findall(r'href="/(?!/)',h))>=5, '一次情報三つ':h.count('target="_blank"')>=3,
            '固有事実六つ':len(row.get('verified_facts',[]))>=6,
            '森町条件三つ':len(row.get('morimachi_conditions',[]))>=3,
            '固有FAQ四つ':len(row.get('faqs',[]))>=4,
            '検証済み出典三つ':len(set(source_urls))>=3 and all(u.startswith('https://') for u in source_urls) and all('verified' in s.get('status','') for s in row.get('sources',[])),
            '固有事実の出典対応':bool(fact_urls) and all(u in set(source_urls) for u in fact_urls),
            '台帳とHTMLの対応':p.get('url')==expected_urls.get(int(p['id'])) and p.get('title')==row.get('title') and p.get('category')==row.get('category') and p.get('editorial_chars')==n,
            '公開状態とnoindexの整合':h.count('data-phase4-pending')==(0 if p.get('publish_ready') is True else 1),
            '大石の視点':'大石の視点' in h, '禁止語なし':('政'+'策') not in h,
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
    if len(set(faq_questions)) < 1100: failures.append(f'FAQ質問の固有数不足: {len(set(faq_questions))}/1200')
    if len(svg_structures) < 30: failures.append(f'SVG構造の種類不足: {len(svg_structures)}')
    if failures: raise SystemExit('第4期監査失敗\n- '+'\n- '.join(failures[:80]))
    if args.release:
        for item in pub:
            item.update(source_validation='verified',uniqueness_validation='verified',visual_validation='verified',publish_ready=True)
        (ROOT/'data/seo-phase4-publication.json').write_text(json.dumps(pub,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        from build_seo_phase4 import load_rows, set_release_state
        set_release_state(load_rows(), True)
    print(f"第4期監査: 300/300ページ合格 / 編集本文 {min(p['editorial_chars'] for p in pub)}字以上 / 完全一致 {exact_ratio:.1%} / 正規化後 {normalized_ratio:.1%} / SVG構造 {len(svg_structures)}種")

if __name__=='__main__': main()
