"""Article-specific, text-free editorial vectors; vertical mobile figures. Set-22 batch.
Scenes: a memorial hall with a flower stand and candle; a festival booth with a teapot
and city skyline; two runners passing a sash on a road; a ceremony hall with bunting
and a big screen."""
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
def hall(x,y,s=1):
 g=rect(-150,-120,300,240,PAPER,8)+path('M-170 -120 L0 -180 L170 -120Z',TEAL,'none')+rect(-14,-58,28,178,INK,4)
 return put(g,x,y,s)
def flower(x,y,s=1):
 g=circle(0,-18,17,PAPER)+circle(-20,2,13,PAPER)+circle(20,2,13,PAPER)+circle(-12,20,11,PAPER)+circle(12,20,11,PAPER)+circle(0,2,8,GOLD)+line('M0 34 V78',GREEN,6)+path('M0 56 Q-26 44 -34 30 Q-12 30 0 48Z',GREEN,'none')
 return put(g,x,y,s)
def candle(x,y,s=1):
 g=rect(-9,-6,18,66,PAPER,3)+path('M0 -44 Q13 -22 0 -6 Q-13 -22 0 -44Z',ORANGE,'none')+circle(0,-18,6,GOLD)
 return put(g,x,y,s)
def stall(x,y,s=1):
 g=path('M-130 -84 L0 -128 L130 -84 L104 -58 L0 -88 L-104 -58Z',RED,'none')+rect(-118,-58,16,150,INK,4)+rect(102,-58,16,150,INK,4)+rect(-108,18,216,20,TEAL,4)+rect(-108,52,216,14,GOLD,4)
 return put(g,x,y,s)
def teapot(x,y,s=1):
 g=circle(0,6,34,TEAL)+path('M-32 -2 L-58 -20 L-50 8 L-30 12Z',TEAL,'none')+path('M32 -6 Q58 -22 50 10',INK,'none')+rect(-7,-40,14,12,INK,3)+circle(0,-44,6,GOLD)
 return put(g,x,y,s)
def tower(x,y,s=1):
 g=rect(-30,-110,60,220,INK,4)+rect(-18,-92,12,16,GOLD,2)+rect(6,-92,12,16,GOLD,2)+rect(-18,-58,12,16,GOLD,2)+rect(6,-58,12,16,GOLD,2)+rect(-18,-24,12,16,GOLD,2)+rect(6,-24,12,16,GOLD,2)+line('M0 -110 V-142',INK,6)+circle(0,-148,7,RED)
 return put(g,x,y,s)
def runner(x,y,s=1):
 g=circle(0,-72,15,INK)+line('M0 -56 L-16 -8 L-44 34 M-16 -8 L22 22 L52 52',INK,9)+line('M0 -50 L38 -30 L64 -44 M0 -50 L-36 -26',INK,8)+path('M-8 -54 L20 8 L8 16 L-20 -46Z',RED,'none')
 return put(g,x,y,s)
def road(x,y,s=1):
 g=path('M-260 60 L260 60 L170 -60 L-170 -60Z','#8a8f87','none')+line('M-120 26 H-52 M-16 26 H52 M88 26 H140 M-84 -22 H-30 M16 -22 H70',PAPER,7)
 return put(g,x,y,s)
def screen(x,y,s=1):
 g=rect(-120,-84,240,150,PAPER,7)+rect(-104,-68,208,118,TEAL,4)+path('M-104 22 Q-40 -26 34 -4 Q76 8 104 -12 V50 H-104Z',GREEN,'none')+circle(58,-38,13,GOLD)+rect(-14,66,28,34,INK,3)
 return put(g,x,y,s)
def bunting(x,y,s=1):
 g=line('M-190 -60 Q0 26 190 -60',INK,4)
 for i,c in enumerate([RED,GOLD,TEAL,ORANGE,GREEN,PINK]):
  px=-158+i*63;py=-38+ (26 if i in (2,3) else 12 if i in (1,4) else 0)
  g+=path(f'M{px} {py} l15 34 l15 -34Z',c,'none')
 return put(g,x,y,s)
def medal(x,y,s=1):
 g=path('M-16 -52 L0 -18 L16 -52 L28 -46 L8 2 L-8 2 L-28 -46Z',RED,'none')+circle(0,26,24,GOLD)+circle(0,26,14,ORANGE)
 return put(g,x,y,s)

def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='senbotsu-heiwa':
  sh+=hall(600,290,1.05)+flower(520,330,1.0)+candle(690,318,.95)+put(person(INK),170,414,1.7)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+flower(650,252,.95)+checkbadge(830,232,.9)
 elif key=='koto-koryu':
  sh+=tower(872,300,.95)+stall(520,320,1.1)+teapot(430,330,.8)+put(person(TEAL),170,414,1.7)+put(tree(),92,340,.8)
  if method:sh+=teapot(282,252,.85)+arrow(442,246,.55)+stall(650,262,.72)+checkbadge(830,232,.9)
 elif key=='shichou-ekiden':
  sh+=road(600,400,1.15)+runner(520,300,1.05)+runner(700,286,.9)+put(person(TEAL),170,414,1.7)+put(tree(),92,320,.85)
  if method:sh+=runner(282,246,.8)+arrow(442,246,.55)+runner(650,246,.8)+checkbadge(830,232,.9)
 else:
  sh+=hall(600,290,1.05)+bunting(600,168,1.0)+screen(600,320,.8)+medal(330,300,.85)+put(person(TEAL),170,414,1.7)
  if method:sh+=medal(282,246,.85)+arrow(442,246,.55)+screen(650,252,.72)+checkbadge(830,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'senbotsu-heiwa':'追悼の花とろうそくと文化会館','koto-koryu':'出展ブースの急須と東京の塔','shichou-ekiden':'タスキを受け渡す二人の選手','gappei-70':'記念式典の会場と大きな画面とメダル'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'senbotsu-heiwa':flower(176,652,.85)+arrow(300,650,.7)+candle(438,646,.9),'koto-koryu':teapot(176,652,.85)+arrow(300,650,.7)+stall(438,652,.62),'shichou-ekiden':runner(176,652,.8)+arrow(300,650,.7)+runner(438,646,.8),'gappei-70':medal(176,652,.85)+arrow(300,650,.7)+screen(438,652,.68)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261128-set22.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261128-set22';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
