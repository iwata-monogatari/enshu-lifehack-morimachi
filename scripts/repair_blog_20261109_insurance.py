"""Preserve this article's content while repairing narrow tables and figure spacing."""
from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parents[1]
SLUG='20261109-taishoku-kenkohoken-hikaku'
FOLDER=ROOT/'blog'/SLUG
CSS='@media(max-width:600px){.insurance-table{overflow:visible;border:0}.insurance-table table{min-width:0;width:100%;display:block}.insurance-table caption{display:block;padding:12px 0;white-space:normal}.insurance-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.insurance-table tbody{display:block}.insurance-table tr{display:block;margin:0 0 18px;border:1px solid #8eaaa0;border-radius:6px;overflow:hidden}.insurance-table th[scope="row"]{display:block;border:0;padding:12px;background:#e9efe9}.insurance-table td{display:block;width:auto;border:0;border-top:1px solid #b6c2b9;padding:12px;white-space:normal;overflow-wrap:anywhere}.insurance-table td:before{content:attr(data-label);display:block;font-weight:700;color:#205f68;margin-bottom:6px}}'
raw=(FOLDER/'fig2.svg').read_text('utf8')
fixed=raw.replace('translate(199 293)','translate(199 245)').replace('M300 365 V421','M300 385 V421').replace('y="342"','y="355"').replace('M180 653 Q300 710 423 653','M180 686 Q300 704 423 686')
digest=hashlib.sha256(fixed.encode('utf8')).hexdigest();name='fig2-repaired-'+digest[:12]+'.svg'
target=FOLDER/name
if target.exists():assert target.read_text('utf8')==fixed
else:target.write_text(fixed,'utf8')
labels=['協会けんぽの任意継続','森町の国民健康保険','家族の健康保険の被扶養者']
for p in [ROOT/'data/content/blog-20261109-taishoku-hoken.html',FOLDER/'index.html']:
 text=p.read_text('utf8');n=[0]
 def label(match):
  val='<td data-label="'+labels[n[0]%3]+'">';n[0]+=1;return val
 text=re.sub(r'<td>',label,text)
 text=re.sub(r'/blog/'+SLUG+r'/fig2(?:-repaired-[0-9a-f]{12})?\.svg','/blog/'+SLUG+'/'+name,text)
 text=text.replace('スマートフォンでは表の中を左右に動かせます。各方式の詳しい説明は、この下に続きます。','スマートフォンでは比較項目ごとに3方式を縦に並べています。各方式の詳しい説明は、この下に続きます。')
 if p.name=='index.html' and CSS not in text:text=text.replace('</style>',CSS+'</style>',1)
 p.write_text(text,'utf8')
print(target.relative_to(ROOT).as_posix())
