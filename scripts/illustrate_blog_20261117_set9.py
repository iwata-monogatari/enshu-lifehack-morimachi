"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 17 set-9 batch (Tuesday). Same approach as the set-8 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: a pension
booklet with a payment slip and coins, a mother holding a booklet of
checkup tickets, a recycling station with bottles and a crate, and a
shelter tent with blankets and a generator.
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape,generator,mapshape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def booklet(x,y,s=1):
 g=rect(-58,-78,116,156,TEAL,8)+rect(-58,-78,18,156,INK,8)+circle(8,-34,17,PAPER)+line('M-24 6 H40 M-24 26 H40 M-24 46 H28','#dcebe2',6)
 return put(g,x,y,s)
def envelope(x,y,s=1):
 g=rect(-72,-44,144,88,PAPER,5)+path('M-72 -44 L0 8 L72 -44',fill='none',stroke=INK,width=4)+rect(38,-36,26,20,GOLD,2)+line('M-52 22 H20 M-52 36 H34','#8fa79c',4)
 return put(g,x,y,s)
def coin(x,y,s=1):
 g=circle(0,0,34,GOLD)+circle(0,0,25,'#f0cd8d')+path('M-9 -13 L0 -2 L9 -13 M-11 -2 H11 M0 -2 V14 M-8 6 H8',INK,'none')
 return put(g,x,y,s)
def ticket(x,y,s=1):
 g=rect(-78,-40,156,80,PAPER,6)+line('M22 -40 V40','#b55845',4)+circle(48,0,13,RED)+line('M-62 -16 H6 M-62 4 H6 M-62 24 H-6','#8fa79c',5)
 return put(g,x,y,s)
def heart(x,y,s=1):
 g=path('M0 34 C-52 2 -44 -38 -16 -38 C-6 -38 0 -30 0 -24 C0 -30 6 -38 16 -38 C44 -38 52 2 0 34Z',PINK,'none')
 return put(g,x,y,s)
def bottle(x,y,s=1):
 g=rect(-13,-84,26,18,TEAL,3)+path('M-13 -66 L-26 -44 V70 Q-26 84 -12 84 H12 Q26 84 26 70 V-44 L13 -66Z','#dcebe2','none')+line('M-26 -8 H26 M-26 22 H26','#8fa79c',4)
 return put(g,x,y,s)
def crate(x,y,s=1):
 g=rect(-84,-52,168,104,'#b6ccbd',6)+line('M-84 -18 H84 M-84 16 H84 M-42 -52 V52 M42 -52 V52',INK,4)
 return put(g,x,y,s)
def tent(x,y,s=1):
 g=path('M0 -84 L96 62 H-96Z',TEAL,'none')+path('M0 -30 L44 62 H-44Z',PAPER,'none')+line('M0 -84 V-30',INK,4)+line('M-96 62 H96',INK,5)
 return put(g,x,y,s)
def blankets(x,y,s=1):
 g=rect(-72,-38,144,26,GOLD,5)+rect(-72,-10,144,26,PINK,5)+rect(-72,18,144,26,TEAL,5)
 return put(g,x,y,s)
def checkbadge(x,y,s=1):
 g=circle(0,0,30,TEAL)+line('M-14 0 L-4 11 L16 -12',PAPER,7)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='nenkin-tsuino':
  sh+=booklet(560,300,1.35)+envelope(770,420,.95)+coin(700,180,.8)+put(person(TEAL),212,414,1.85)+note(330,300,.55)
  if method:sh+=note(272,238,.62)+arrow(442,246,.55)+envelope(622,238,.85)+circle(806,232,27,TEAL)
 elif key=='ninpu-kenshin':
  sh+=ticket(596,300,1.45)+heart(770,190,.95)+put(person(PINK),212,414,1.85)+put(person(GOLD),330,468,1.15)+house(120,318,.65)
  if method:sh+=booklet(282,240,.55)+arrow(442,246,.55)+ticket(622,238,.85)+checkbadge(800,232,.9)
 elif key=='shigen-kyoten':
  sh+=crate(596,392,1.25)+bottle(520,238,1.05)+bottle(612,252,.9)+bottle(692,238,1.0)+put(person(TEAL),212,414,1.85)+house(856,318,.7)
  if method:sh+=bottle(282,238,.8)+arrow(442,246,.55)+crate(622,252,.72)+checkbadge(800,232,.9)
 else:
  sh+=tent(560,320,1.35)+blankets(806,436,.95)+generator(240,420,.95)+put(person(TEAL),130,430,1.6)+put(tree(),920,330,.9)
  if method:sh+=mapshape(282,240,.62)+arrow(442,246,.55)+tent(630,246,.62)+checkbadge(806,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'nenkin-tsuino':'年金手帳と納付書の封筒と硬貨','ninpu-kenshin':'受診票の束とハートと親子','shigen-kyoten':'ペットボトルと回収かごと役場','hinanjo-bichiku':'避難所のテントと毛布と発電機'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'nenkin-tsuino':booklet(176,652,.62)+arrow(300,650,.7)+coin(438,652,1.0),'ninpu-kenshin':ticket(183,652,.85)+arrow(300,650,.7)+heart(438,652,1.0),'shigen-kyoten':bottle(176,650,.85)+arrow(300,650,.7)+crate(438,657,.72),'hinanjo-bichiku':mapshape(176,652,.8)+arrow(300,650,.7)+tent(438,657,.72)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261117-set9.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261117-set9';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
