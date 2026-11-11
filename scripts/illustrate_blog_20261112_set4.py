"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 12 set-4 batch (Thursday). Same approach as the set-3 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: water meter and
pilot, tax notice with three levy cards, convenience-store payment, and a
septic tank cross-section by a river.
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
def wrench(x,y,s=1):return put(path('M-38 38 L14 -14 A20 20 0 1 1 38 -38 L16 -16 L30 -2 A20 20 0 0 1 -14 14 L-38 38Z',GOLD,INK),x,y,s)
def store(x,y,s=1):
 g=rect(-110,-70,220,140,PAPER,4)+path('M-125 -70 H125 L105 -34 H-105Z',RED)+rect(-70,-6,52,76,TEAL)+rect(28,-6,52,76,'#9fc1b9')+line('M-110 70 H110',INK,5)
 return put(g,x,y,s)
def phone(x,y,s=1):
 g=rect(-34,-58,68,116,INK,10)+rect(-26,-44,52,76,'#dfe9dc',3)+circle(0,-24,13,TEAL)+line('M-16 2 H16 M-16 18 H8',TEAL,5)+circle(0,44,5,PAPER)
 return put(g,x,y,s)
def tank(x,y,s=1):
 g=rect(-120,-46,240,92,'#b6ccbd',8)+line('M-40 -46 V46 M40 -46 V46','#7d9a89',5)+circle(-80,-72,16,'#816b57')+rect(-92,-64,24,20,PAPER,3)+path('M120 0 Q170 -14 210 6',TEAL,7)
 return put(g,x,y,s)
def river(x,y,s=1):return put(path('M-140 0 Q-70 -26 0 0 T140 0',TEAL,8,)+path('M-140 30 Q-70 4 0 30 T140 30','#9fc1b9',7),x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='rosui':
  sh+=meter(560,318,1.45)+wrench(760,392,.9)+put(person(TEAL),215,414,1.85)+house(120,330,.7)
  if method:sh+=meter(300,238,.62)+arrow(452,262,.55)+wrench(620,232,.8)+circle(770,238,30,GOLD)
 elif key=='kokuhozei':
  sh+=house(720,318,1.5)+put(person(GOLD),215,414,1.85)+card(430,452,.85)+card(545,442,.7,True)+card(640,458,.62)
  if method:sh+=card(270,238,.6)+arrow(420,246,.55)+card(575,238,.6,True)+arrow(700,246,.5)+circle(790,232,28,TEAL)
 elif key=='shiharai':
  sh+=store(620,330,1.5)+phone(400,300,.95)+put(person(TEAL),205,414,1.85)
  if method:sh+=card(280,238,.6)+arrow(430,246,.55)+phone(600,238,.62)+circle(760,232,28,RED)
 else:
  sh+=tank(540,392,1.35)+river(540,486,1.1)+house(770,300,1.05)+put(person(RED),205,414,1.8)+put(tree(),120,320,1.0)
  if method:sh+=tank(330,246,.62)+arrow(520,262,.55)+circle(700,238,42,GOLD)+line('M700 210 V266 M672 238 H728',INK,6)
 return sh
def svg(key,method=False,portrait=True):
 title={'rosui':'水道メーターのパイロットを確認する人','kokuhozei':'国保税の通知書と三つの区分のカードを見比べる人','shiharai':'コンビニで水道料金を納める人とスマートフォン決済','jokaso':'河川のそばに据えられる合併処理浄化槽'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'rosui':meter(183,646,.72)+arrow(300,650,.7)+wrench(431,657,.62),'kokuhozei':card(170,650,.9)+arrow(300,650,.7)+card(431,657,.8,True),'shiharai':phone(178,650,.78)+arrow(300,650,.7)+card(431,657,.8),'jokaso':tank(212,650,.55)+arrow(330,650,.6)+river(440,672,.5)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261112-set4.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261112-set4';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
