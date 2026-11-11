"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 11 set-3 batch (Wednesday). Same approach as the set-2 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor).
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def card(x,y,s=1,pink=False):return put(rect(-67,-44,134,88,PINK if pink else PAPER,6)+circle(-34,-8,12,TEAL)+line('M-11 -15 H49 M-11 4 H49 M-49 26 H48','#8fa79c',5),x,y,s)
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def clinic(x,y,s=1):
 g=rect(-90,-70,180,140,PAPER,4)+path('M-105 -70 L0 -118 L105 -70Z','#816b57')+rect(-16,6,32,64,TEAL)+circle(0,-38,17,RED)+line('M0 -52 V-24 M-14 -38 H14',PAPER,6)
 return put(g,x,y,s)
def fence(x,y,s=1):
 g=''
 for i in range(5):g+=line(f'M{-120+i*60} -70 V70',INK,7)
 g+=line('M-135 -38 H135 M-135 6 H135 M-135 48 H135',GOLD,5)
 g+=path('M-30 -70 L-8 -92 L14 -70 L36 -92 L58 -70',RED,INK)
 return put(g,x,y,s)
def shield(x,y,s=1):return put(path('M0 -62 L48 -44 V6 Q48 48 0 66 Q-48 48 -48 6 V-44Z',TEAL,INK)+line('M-24 0 L-6 20 L28 -22',PAPER,8),x,y,s)
def syringe(x,y,s=1):return put(line('M-46 46 L18 -18',INK,7)+rect(6,-44,34,34,RED,4)+line('M40 -30 L56 -46 M24 -50 L34 -60',INK,6),x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='kenshin':
  sh+=clinic(560,318,1.5)+put(person(TEAL),215,414,1.85)+card(330,452,.8)+house(120,330,.75)
  if method:sh+=note(300,238,.6)+arrow(452,262,.55)+card(620,232,.7)+circle(770,238,30,GOLD)
 elif key=='kouki':
  sh+=house(700,318,1.6)+put(person(GOLD),215,414,1.85)+card(452,462,.85)+card(560,452,.7,True)
  if method:sh+=card(280,238,.62)+arrow(430,246,.55)+card(590,238,.62,True)+circle(770,232,30,TEAL)
 elif key=='denkisaku':
  sh+=fence(520,360,1.35)+put(tree(),150,330,1.1)+put(tree(),880,320,1.0)+put(person(RED),205,430,1.7)
  if method:sh+=fence(330,238,.62)+arrow(520,262,.55)+circle(700,238,42,GOLD)+line('M700 210 V266 M672 238 H728',INK,6)
 else:
  sh+=clinic(700,326,1.35)+shield(430,330,.95)+syringe(520,250,.8)+put(person(TEAL),205,414,1.85)
  if method:sh+=card(280,238,.6)+arrow(430,246,.55)+shield(600,238,.62)+circle(760,232,28,RED)
 return sh
def svg(key,method=False,portrait=True):
 title={'kenshin':'森町の総合検診の会場へ向かう人と検診の案内','kouki':'75歳の節目に新しい資格確認書を受け取る人','denkisaku':'畑を囲う電気柵と見回る農家','flu':'高齢者の予防接種と盾のイメージ'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'kenshin':note(183,646,.9)+arrow(300,650,.7)+card(431,657,.8),'kouki':card(170,650,.9)+arrow(300,650,.7)+card(431,657,.8,True),'denkisaku':fence(178,650,.55)+arrow(300,650,.7)+circle(428,650,34,GOLD),'flu':shield(178,650,.75)+arrow(300,650,.7)+card(431,657,.8)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261111-set3.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261111-set3';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
