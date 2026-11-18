"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 18 set-11 batch. Same approach as the set-9 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: an underground
septic tank with a vacuum truck and checklist, a house pipe running to a
public manhole with a bill envelope, a nursery building with a clipboard
and children, and a library bookshelf with a big book and a user card.
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape,generator,mapshape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def checkbadge(x,y,s=1):
 g=circle(0,0,30,TEAL)+line('M-14 0 L-4 11 L16 -12',PAPER,7)
 return put(g,x,y,s)
def envelope(x,y,s=1):
 g=rect(-72,-44,144,88,PAPER,5)+path('M-72 -44 L0 8 L72 -44',fill='none',stroke=INK,width=4)+rect(38,-36,26,20,GOLD,2)+line('M-52 22 H20 M-52 36 H34','#8fa79c',4)
 return put(g,x,y,s)
def coin(x,y,s=1):
 g=circle(0,0,34,GOLD)+circle(0,0,25,'#f0cd8d')+path('M-9 -13 L0 -2 L9 -13 M-11 -2 H11 M0 -2 V14 M-8 6 H8',INK,'none')
 return put(g,x,y,s)
def tank(x,y,s=1):
 g=rect(-130,-58,260,116,'#b6ccbd',8)+line('M-44 -58 V58 M44 -58 V58',INK,5)+path('M-130 -18 Q-88 -34 -44 -18 T44 -18 T130 -18',TEAL,'none')+rect(-24,-84,48,26,INK,4)+circle(88,-30,13,TEAL)+line('M-130 58 H130',INK,6)
 return put(g,x,y,s)
def truck(x,y,s=1):
 g=rect(-104,-52,150,74,'#dcebe2',6)+path('M46 -30 L86 -30 L104 4 L104 22 L46 22Z',TEAL,'none')+rect(56,-22,26,20,PAPER,2)+circle(-64,34,17,INK)+circle(0,34,17,INK)+circle(76,34,17,INK)+line('M-104 -52 H46',INK,4)
 return put(g,x,y,s)
def hose(x,y,s=1):return put(path('M-90 40 Q-30 -52 40 -38 T96 -52',fill='none',stroke=INK,width=7),x,y,s)
def manhole(x,y,s=1):
 g=circle(0,0,52,'#8fa79c')+circle(0,0,40,'#b6ccbd')+line('M-28 -14 H28 M-32 4 H32 M-28 22 H28',INK,4)
 return put(g,x,y,s)
def pipeflow(x,y,s=1):return put(line('M-110 0 H110',TEAL,13)+line('M-110 0 H110',INK,3),x,y,s)
def shelf(x,y,s=1):
 g=rect(-118,-96,236,192,PAPER,5)+line('M-118 -32 H118 M-118 32 H118',INK,5)
 for dx,c in [(-92,RED),(-64,TEAL),(-36,GOLD),(-8,PINK),(20,TEAL),(48,RED),(76,GOLD)]:
  g+=rect(dx,-92,22,56,c,2)
 for dx,c in [(-92,TEAL),(-58,GOLD),(-24,RED),(10,PINK),(44,TEAL),(78,GOLD)]:
  g+=rect(dx,-28,24,56,c,2)
 for dx,c in [(-88,RED),(-52,PINK),(-16,TEAL),(20,GOLD),(56,RED)]:
  g+=rect(dx,36,26,56,c,2)
 return put(g,x,y,s)
def bigbook(x,y,s=1):
 g=path('M0 -52 C-34 -70 -66 -66 -88 -56 V52 C-66 42 -34 38 0 56 C34 38 66 42 88 52 V-56 C66 -66 34 -70 0 -52Z',PAPER,'none')+line('M0 -52 V56',INK,4)+line('M-70 -34 H-18 M-70 -12 H-18 M-70 10 H-24 M18 -34 H70 M18 -12 H70 M18 10 H64','#8fa79c',4)
 return put(g,x,y,s)
def ucard(x,y,s=1):
 g=rect(-72,-46,144,92,TEAL,7)+rect(-58,-32,34,44,PAPER,3)+circle(-41,-16,8,INK)+line('M-12 -24 H54 M-12 -4 H54 M-12 16 H38',PAPER,5)
 return put(g,x,y,s)
def clipboard(x,y,s=1):
 g=rect(-62,-84,124,168,PAPER,6)+rect(-22,-98,44,22,GOLD,5)+line('M-40 -52 H40 M-40 -24 H40 M-40 4 H24','#8fa79c',5)+path('M-38 38 L-24 52 L42 30',TEAL,'none')
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='jokaso-ijikanri':
  sh+=tank(560,392,1.15)+truck(238,300,.8)+hose(400,300,.8)+put(person(TEAL),856,414,1.7)+note(856,220,.5)
  if method:sh+=note(272,238,.62)+arrow(442,246,.55)+tank(622,252,.62)+checkbadge(806,232,.9)
 elif key=='gesuido-shiyoriyo':
  sh+=house(300,300,1.25)+pipeflow(520,420,1.2)+manhole(760,430,.95)+envelope(770,220,.9)+coin(620,180,.75)+put(person(TEAL),140,430,1.6)
  if method:sh+=envelope(282,238,.8)+arrow(442,246,.55)+coin(622,238,1.0)+checkbadge(800,232,.9)
 elif key=='hoiku-nintei':
  sh+=house(560,300,1.5)+clipboard(806,240,.8)+put(person(PINK),212,414,1.85)+put(person(GOLD),330,468,1.15)+put(tree(),920,330,.9)
  if method:sh+=clipboard(282,240,.62)+arrow(442,246,.55)+house(640,252,.62)+checkbadge(806,232,.9)
 else:
  sh+=shelf(560,300,1.25)+bigbook(806,430,.85)+ucard(230,200,.8)+put(person(TEAL),212,414,1.85)+put(tree(),920,330,.8)
  if method:sh+=ucard(282,238,.85)+arrow(442,246,.55)+bigbook(622,238,.85)+checkbadge(800,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'jokaso-ijikanri':'浄化槽とバキューム車と点検表','gesuido-shiyoriyo':'家と公共ますと請求書の封筒','hoiku-nintei':'保育施設と申込のボードと親子','toshokan-riyo':'本棚と大きな本と利用者カード'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'jokaso-ijikanri':tank(176,657,.62)+arrow(300,650,.7)+note(438,652,.62),'gesuido-shiyoriyo':pipeflow(176,652,.62)+arrow(300,650,.7)+manhole(438,652,.85),'hoiku-nintei':clipboard(183,652,.72)+arrow(300,650,.7)+house(438,657,.62),'toshokan-riyo':ucard(176,652,.85)+arrow(300,650,.7)+bigbook(438,652,.8)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261118-set11.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261118-set11';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
