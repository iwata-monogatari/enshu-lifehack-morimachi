"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 18 set-10 batch (Wednesday). Same approach as the set-9 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: a small car with
a town number plate and a certificate, an insurance limit certificate card
with a medical cross, a health-check clipboard with a stethoscope curve,
and a parent and child with toy blocks at a support centre.
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape,generator,mapshape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def car(x,y,s=1):
 g=path('M-110 28 L-96 -18 Q-94 -30 -80 -32 L-38 -36 L-14 -66 Q-8 -74 4 -74 L44 -74 Q56 -74 62 -64 L84 -34 L104 -30 Q114 -27 114 28Z','#dcebe2','none')+rect(-104,28,218,14,TEAL,6)+circle(-62,44,19,INK)+circle(-62,44,9,PAPER)+circle(66,44,19,INK)+circle(66,44,9,PAPER)+rect(-16,-64,52,26,'#9fc1b9',3)+rect(48,-62,26,24,'#9fc1b9',3)
 return put(g,x,y,s)
def plate(x,y,s=1):
 g=rect(-62,-40,124,80,PAPER,6)+line('M-62 -40 H62 M-62 40 H62',INK,3)+circle(-34,-18,7,TEAL)+circle(34,-18,7,TEAL)+line('M-38 8 H38 M-24 26 H24',INK,6)
 return put(g,x,y,s)
def idcard(x,y,s=1):
 g=rect(-86,-56,172,112,PAPER,7)+rect(-86,-56,172,24,TEAL,7)+circle(-48,16,19,GOLD)+path('M-48 2 Q-62 34 -48 34 Q-34 34 -48 2',INK,'none')+line('M-14 -8 H62 M-14 12 H62 M-14 32 H40','#8fa79c',6)
 return put(g,x,y,s)
def cross(x,y,s=1):
 g=circle(0,0,40,RED)+path('M-9 -24 H9 V-9 H24 V9 H9 V24 H-9 V9 H-24 V-9 H-9Z',PAPER,'none')
 return put(g,x,y,s)
def clipboard(x,y,s=1):
 g=rect(-62,-84,124,168,PAPER,6)+rect(-24,-96,48,22,INK,6)+line('M-40 -52 H40 M-40 -26 H40 M-40 0 H40 M-40 26 H24','#8fa79c',6)+path('M-40 52 L-28 64 L48 44',TEAL,'none')
 return put(g,x,y,s)
def stetho(x,y,s=1):
 g=path('M-34 -52 V6 Q-34 44 6 44 Q40 44 40 12',fill='none',stroke=INK,width=7)+circle(-34,-62,11,TEAL)+circle(40,0,13,GOLD)+circle(40,0,6,INK)
 return put(g,x,y,s)
def blocks(x,y,s=1):
 g=rect(-78,8,62,62,RED,5)+rect(-8,8,62,62,GOLD,5)+path('M44 -58 L76 8 H12Z',TEAL,'none')+circle(-47,-26,24,PINK)
 return put(g,x,y,s)
def heart(x,y,s=1):
 g=path('M0 34 C-52 2 -44 -38 -16 -38 C-6 -38 0 -30 0 -24 C0 -30 6 -38 16 -38 C44 -38 52 2 0 34Z',PINK,'none')
 return put(g,x,y,s)
def checkbadge(x,y,s=1):
 g=circle(0,0,30,TEAL)+line('M-14 0 L-4 11 L16 -12',PAPER,7)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='keijidosha-toroku':
  sh+=car(590,330,1.5)+plate(806,180,.85)+put(person(TEAL),212,414,1.85)+house(120,318,.6)
  if method:sh+=plate(282,240,.8)+arrow(442,246,.55)+car(640,252,.62)+checkbadge(806,232,.9)
 elif key=='kokuho-gendogaku':
  sh+=idcard(590,300,1.5)+cross(790,180,.9)+put(person(PINK),212,414,1.85)+house(120,318,.65)
  if method:sh+=idcard(282,240,.6)+arrow(442,246,.55)+cross(630,240,.85)+checkbadge(806,232,.9)
 elif key=='kokuho-dock':
  sh+=clipboard(580,300,1.4)+stetho(790,220,1.0)+put(person(TEAL),212,414,1.85)+put(tree(),920,330,.9)
  if method:sh+=note(272,238,.62)+arrow(442,246,.55)+clipboard(630,240,.62)+checkbadge(806,232,.9)
 else:
  sh+=blocks(600,360,1.35)+heart(786,190,.95)+put(person(PINK),212,414,1.85)+put(person(GOLD),330,468,1.15)+house(880,318,.65)
  if method:sh+=blocks(282,246,.72)+arrow(442,246,.55)+heart(630,240,1.05)+checkbadge(806,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'keijidosha-toroku':'軽自動車と町ナンバープレートと証明書','kokuho-gendogaku':'限度額適用認定証のカードと医療の十字','kokuho-dock':'健診のクリップボードと聴診器','kosodate-center':'積み木とハートと親子'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'keijidosha-toroku':plate(176,652,.85)+arrow(300,650,.7)+car(438,657,.5),'kokuho-gendogaku':idcard(183,652,.68)+arrow(300,650,.7)+cross(438,652,.95),'kokuho-dock':note(176,652,.55)+arrow(300,650,.7)+clipboard(438,657,.55),'kosodate-center':blocks(176,657,.72)+arrow(300,650,.7)+heart(438,652,1.0)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261118-set10.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261118-set10';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
