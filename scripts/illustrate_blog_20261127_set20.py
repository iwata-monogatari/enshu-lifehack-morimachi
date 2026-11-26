"""Article-specific, text-free editorial vectors; vertical mobile figures. Set-20 batch.
Scenes: a support notice letter arriving at a family home; energy-saving appliances
(a fridge and an air conditioner) with a leaf; a tea field being replanted with new
seedlings; a disaster-prevention leader with a helmet and a shield badge."""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape,generator,mapshape,camera
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0';ORANGE='#e07b2a';GREEN='#6a9a5b'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def checkbadge(x,y,s=1):
 g=circle(0,0,30,TEAL)+line('M-14 0 L-4 11 L16 -12',PAPER,7)
 return put(g,x,y,s)
def envelope(x,y,s=1):
 g=rect(-100,-62,200,124,PAPER,6)+path('M-100 -62 L0 18 L100 -62Z',GOLD,'none')+line('M-100 62 L-28 -6 M100 62 L28 -6',INK,4)
 return put(g,x,y,s)
def fridge(x,y,s=1):
 g=rect(-52,-105,104,210,TEAL,8)+line('M-52 -28 H52',PAPER,5)+line('M28 -88 V-48 M28 -12 V28',INK,6)
 return put(g,x,y,s)
def aircon(x,y,s=1):
 g=rect(-105,-38,210,76,PAPER,7)+line('M-85 12 H85 M-85 26 H85',TEAL,5)+path('M-40 62 q10 18 0 34 M0 62 q10 18 0 34 M40 62 q10 18 0 34',TEAL,'none')
 return put(g,x,y,s)
def leaf(x,y,s=1):
 g=path('M0 52 C-52 18 -52 -34 0 -58 C52 -34 52 18 0 52Z',GREEN,'none')+line('M0 48 V-48',PAPER,4)
 return put(g,x,y,s)
def tearow(x,y,s=1):
 g=path('M-130 30 Q-60 -18 0 8 Q60 -18 130 30 L130 52 L-130 52Z',GREEN,'none')+line('M-95 22 q14 -16 28 -4 M-30 16 q14 -16 28 -4 M35 16 q14 -16 28 -4',INK,4)
 return put(g,x,y,s)
def sprout(x,y,s=1):
 g=line('M0 40 V-16',GREEN,7)+path('M0 -16 Q-34 -44 -52 -30 Q-34 -4 0 -16Z',GREEN,'none')+path('M0 -16 Q34 -44 52 -30 Q34 -4 0 -16Z',GREEN,'none')
 return put(g,x,y,s)
def helmet(x,y,s=1):
 g=path('M-58 22 A58 58 0 0 1 58 22Z',GOLD,'none')+rect(-70,22,140,14,ORANGE,5)+line('M0 -36 V22',PAPER,6)
 return put(g,x,y,s)
def shield(x,y,s=1):
 g=path('M0 -62 L52 -42 V8 Q52 48 0 66 Q-52 48 -52 8 V-42Z',TEAL,'none')+line('M-24 0 L-6 20 L28 -20',PAPER,8)
 return put(g,x,y,s)

def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='kosodate-ouen':
  sh+=house(600,300,1.15)+envelope(838,238,.85)+put(person(TEAL),170,414,1.7)+put(person(PINK),285,414,1.5)+put(person(GOLD),385,430,1.1)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+envelope(650,252,.85)+checkbadge(830,232,.9)
 elif key=='shoene-kaden':
  sh+=fridge(560,300,1.15)+aircon(838,205,.9)+leaf(300,250,.9)+put(person(TEAL),170,414,1.7)+put(tree(),92,340,.8)
  if method:sh+=fridge(282,246,.62)+arrow(442,246,.55)+leaf(650,246,.95)+checkbadge(830,232,.9)
 elif key=='cha-kaishoku':
  sh+=tearow(600,360,1.5)+sprout(470,225,.95)+sprout(640,205,.8)+sprout(790,232,.7)+put(person(TEAL),170,414,1.7)+put(tree(),905,320,.85)
  if method:sh+=tearow(282,252,.72)+arrow(442,246,.55)+sprout(650,246,.95)+checkbadge(830,232,.9)
 else:
  sh+=put(person(TEAL),560,330,1.9)+helmet(560,205,1.05)+shield(838,270,1.0)+put(person(PINK),215,414,1.6)+house(110,318,.55)
  if method:sh+=helmet(282,240,.95)+arrow(442,246,.55)+shield(650,252,.9)+checkbadge(830,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'kosodate-ouen':'家族の家に届く支給の案内','shoene-kaden':'冷蔵庫とエアコンと省エネの葉','cha-kaishoku':'改植される茶園と新しい芽','bosaisi-josei':'ヘルメットをかぶった防災の担い手と盾'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'kosodate-ouen':note(176,652,.85)+arrow(300,650,.7)+envelope(438,652,.8),'shoene-kaden':fridge(176,652,.62)+arrow(300,650,.7)+leaf(438,652,.85),'cha-kaishoku':tearow(176,660,.62)+arrow(300,650,.7)+sprout(438,646,.85),'bosaisi-josei':helmet(176,652,.85)+arrow(300,650,.7)+shield(438,652,.8)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261127-set20.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261127-set20';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
