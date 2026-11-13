"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 13 set-5 batch (Friday). Same approach as the set-4 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: a water meter
with a paper form, a small truck carrying furniture to a facility, a seal
stamp with a registration card, and a tax notice beside a calendar.
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
def meter(x,y,s=1):
 g=rect(-95,-60,190,120,'#cfd8cf',6)+circle(0,-6,44,PAPER)+circle(0,-6,30,'#eef2e8')+line('M0 -6 L22 -24',RED,6)+circle(0,-6,6,INK)+line('M-70 38 H70','#8fa79c',5)+path('M-95 60 H95',INK,4)
 return put(g,x,y,s)
def truck(x,y,s=1):
 g=rect(-150,-40,190,80,'#9fc1b9',5)+rect(40,-16,58,56,PAPER,4)+line('M40 -16 H98 V40 H40Z',TEAL,4)+circle(-95,52,24,INK)+circle(72,52,24,INK)+rect(-140,-92,120,52,'#816b57',4)+rect(-132,-84,104,36,PINK,3)
 return put(g,x,y,s)
def stamp(x,y,s=1):
 g=circle(0,26,40,PAPER)+line('M0 -14 V-52',INK,10)+rect(-26,-66,52,16,GOLD,6)+circle(0,26,26,RED)+line('M-14 26 H14 M0 14 V38',RED,5)
 return put(g,x,y,s)
def calendar(x,y,s=1):
 g=rect(-70,-58,140,116,PAPER,6)+rect(-70,-58,140,30,RED,6)+line('M-46 -22 H46 M-46 4 H46 M-46 30 H46','#8fa79c',5)+circle(-24,-44,6,PAPER)+circle(24,-44,6,PAPER)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='todoke':
  sh+=meter(600,330,1.5)+card(390,300,.95)+put(person(TEAL),205,414,1.85)+house(130,320,.65)
  if method:sh+=card(280,238,.62)+arrow(440,246,.55)+meter(620,232,.6)+circle(790,232,28,GOLD)
 elif key=='sodai':
  sh+=truck(600,360,1.35)+put(person(RED),205,414,1.85)+house(800,300,.8)+put(tree(),110,330,.95)
  if method:sh+=card(270,238,.6)+arrow(430,246,.55)+truck(640,250,.62)+circle(810,232,26,TEAL)
 elif key=='inkan':
  sh+=stamp(560,330,1.5)+card(370,430,.85)+put(person(GOLD),205,414,1.85)+house(760,320,.85)
  if method:sh+=stamp(290,238,.62)+arrow(450,246,.55)+card(610,238,.62,True)+circle(790,232,28,RED)
 else:
  sh+=calendar(590,320,1.45)+card(390,440,.85,True)+put(person(TEAL),205,414,1.85)+house(790,320,.8)
  if method:sh+=calendar(280,238,.6)+arrow(440,246,.55)+card(610,238,.6)+circle(790,232,28,GOLD)
 return sh
def svg(key,method=False,portrait=True):
 title={'todoke':'給水届と水道メーターを見比べる人','sodai':'家具を積んだ軽トラックで処理施設へ向かう人','inkan':'印鑑と印鑑登録証を並べる人','entai':'納税通知書とカレンダーを見比べる人'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'todoke':card(183,646,.85)+arrow(300,650,.7)+meter(431,657,.6),'sodai':card(170,650,.85)+arrow(300,650,.7)+truck(440,657,.5),'inkan':stamp(183,646,.7)+arrow(300,650,.7)+card(431,657,.8),'entai':calendar(176,650,.72)+arrow(300,650,.7)+card(431,657,.8,True)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261113-set5.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261113-set5';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
