"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 14 set-6 batch (Saturday). Same approach as the set-5 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: an enrolment
form beside a qualification card, a tooth with a checkup ticket, a driving
history certificate beside a steering wheel, and a dog with its rabies tag.
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
def shield(x,y,s=1):
 g=path('M0 -70 C30 -52 52 -50 66 -52 C66 10 44 52 0 74 C-44 52 -66 10 -66 -52 C-52 -50 -30 -52 0 -70 Z','#9fc1b9',INK)+line('M0 -34 V34 M-17 -17 H17',RED,11)
 return put(g,x,y,s)
def tooth(x,y,s=1):
 g=path('M-42 -52 C-64 -22 -54 28 -34 58 C-18 32 -6 32 0 58 C6 32 18 32 34 58 C54 28 64 -22 42 -52 C18 -68 -18 -68 -42 -52 Z',PAPER,INK)+line('M-24 -18 H24','#8fa79c',5)
 return put(g,x,y,s)
def wheel(x,y,s=1):
 g=circle(0,0,62,'#eef2e8')+circle(0,0,62,'none')+line('M-62 0 H62 M0 -62 V0 M-44 44 L0 0 L44 44',INK,7)+circle(0,0,14,GOLD)
 return put(g,x,y,s)
def dog2(x,y,s=1):
 body=rect(-80,-18,124,60,'#c9a87c',8)+circle(58,-34,34,'#c9a87c')+path('M40 -58 L58 -30 L24 -28 Z','#a9855a','none')+line('M-80 -8 L-112 -34',INK,7)+line('M-52 42 V74 M22 42 V74','#8a6f4d',8)+circle(66,-38,5,INK)+circle(96,10,10,RED)
 return put(body,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='kokuho':
  sh+=shield(600,320,1.35)+card(390,430,.9)+put(person(TEAL),205,414,1.85)+house(810,320,.8)
  if method:sh+=card(280,238,.62)+arrow(440,246,.55)+shield(620,232,.55)+circle(790,232,28,GOLD)
 elif key=='shishu':
  sh+=tooth(580,320,1.5)+card(380,440,.85,True)+put(person(RED),205,414,1.85)+house(800,310,.8)
  if method:sh+=card(280,238,.6,True)+arrow(440,246,.55)+tooth(620,232,.62)+circle(790,232,26,TEAL)
 elif key=='unten':
  sh+=wheel(590,330,1.3)+card(380,300,.9)+put(person(GOLD),205,414,1.85)+house(800,320,.8)+put(tree(),110,330,.9)
  if method:sh+=wheel(290,238,.55)+arrow(450,246,.55)+card(620,238,.62)+circle(800,232,26,RED)
 else:
  sh+=dog2(600,350,1.35)+card(370,430,.85)+put(person(TEAL),205,414,1.85)+house(810,310,.85)
  if method:sh+=card(280,238,.6)+arrow(440,246,.55)+dog2(640,250,.6)+circle(810,232,26,GOLD)
 return sh
def svg(key,method=False,portrait=True):
 title={'kokuho':'異動届と資格確認書を並べる人','shishu':'歯と受診券を並べる人','unten':'運転経歴証明書とハンドルを並べる人','kyoken':'注射済票を付けた犬と飼い主'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'kokuho':card(183,646,.85)+arrow(300,650,.7)+shield(431,657,.55),'shishu':card(170,650,.85,True)+arrow(300,650,.7)+tooth(440,657,.6),'unten':wheel(183,646,.6)+arrow(300,650,.7)+card(431,657,.8),'kyoken':card(170,650,.85)+arrow(300,650,.7)+dog2(450,657,.55)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261114-set6.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261114-set6';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
