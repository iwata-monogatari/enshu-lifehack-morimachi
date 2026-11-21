"""Article-specific, text-free editorial vectors; vertical mobile figures. Set-14 batch.
Scenes: a maternity booklet with an envelope; a pendant alert device with a phone base;
a collection calendar page with a sorting container; a clinic building with a red cross."""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape,generator,mapshape,camera
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def checkbadge(x,y,s=1):
 g=circle(0,0,30,TEAL)+line('M-14 0 L-4 11 L16 -12',PAPER,7)
 return put(g,x,y,s)
def envelope(x,y,s=1):
 g=rect(-80,-52,160,104,PAPER,5)+path('M-80 -52 L0 10 L80 -52',TEAL,'none')+line('M-80 52 L-18 -2 M80 52 L18 -2','#8fa79c',4)
 return put(g,x,y,s)
def pendant(x,y,s=1):
 g=line('M0 -78 Q34 -30 18 8',INK,5)+rect(-26,4,52,64,TEAL,10)+circle(0,36,15,RED)+circle(0,36,6,PAPER)
 return put(g,x,y,s)
def phonebase(x,y,s=1):
 g=rect(-88,-58,176,116,'#8fa79c',10)+rect(-70,-40,140,80,PAPER,6)+circle(38,0,22,RED)+circle(38,0,9,PAPER)+line('M-52 -18 H8 M-52 8 H8','#8fa79c',6)+line('M-70 58 Q0 84 70 58',INK,5)
 return put(g,x,y,s)
def calpage(x,y,s=1):
 g=rect(-82,-96,164,192,PAPER,6)+rect(-82,-96,164,40,RED,6)+line('M-82 -28 H82 M-82 36 H82 M-28 -56 V96 M28 -56 V96','#8fa79c',4)+circle(28,66,17,GOLD)+line('M20 66 L26 73 L38 58',INK,4)
 return put(g,x,y,s)
def sortbin(x,y,s=1):
 g=rect(-62,-48,124,110,TEAL,7)+rect(-70,-64,140,20,'#8fa79c',5)+line('M-34 -22 V38 M0 -22 V38 M34 -22 V38',PAPER,6)
 return put(g,x,y,s)
def clinic(x,y,s=1):
 g=rect(-100,-72,200,150,PAPER,6)+rect(-100,-72,200,34,'#8fa79c',6)+rect(-16,16,32,62,TEAL,3)+rect(52,-18,34,34,PAPER,3)+line('M69 -32 V-4 M55 -18 H83',RED,6)+path('M0 -104 L16 -72 H-16Z',RED,'none')+line('M0 -96 V-80 M-8 -88 H8',PAPER,5)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='kokuho-sanzen-sango-menjo':
  sh+=note(580,300,1.35)+envelope(815,185,.9)+put(person(PINK),212,414,1.7)+house(120,318,.6)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+envelope(640,252,.85)+checkbadge(806,232,.9)
 elif key=='kinkyu-tsuho-system':
  sh+=phonebase(580,300,1.45)+pendant(815,190,1.05)+put(person(RED),212,414,1.85)+house(120,318,.6)
  if method:sh+=pendant(282,240,.95)+arrow(442,246,.55)+phonebase(640,252,.72)+checkbadge(806,232,.9)
 elif key=='gomi-calendar-r8':
  sh+=calpage(570,295,1.45)+sortbin(815,200,.95)+put(person(TEAL),212,414,1.85)+house(120,318,.6)
  if method:sh+=sortbin(282,240,.85)+arrow(442,246,.55)+calpage(640,252,.78)+checkbadge(806,232,.9)
 else:
  sh+=clinic(570,300,1.4)+note(815,185,.85)+put(person(TEAL),212,414,1.85)+put(tree(),930,350,.8)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+clinic(650,252,.68)+checkbadge(826,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'kokuho-sanzen-sango-menjo':'母子健康手帳と届出書の封筒','kinkyu-tsuho-system':'ペンダント型通報装置と据置型の本体','gomi-calendar-r8':'収集日カレンダーと分別コンテナ','shinryojo-kaigyo-shien':'十字の標識のある診療所と書類'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'kokuho-sanzen-sango-menjo':note(176,652,.85)+arrow(300,650,.7)+envelope(438,652,.78),'kinkyu-tsuho-system':pendant(176,652,.95)+arrow(300,650,.7)+phonebase(438,657,.68),'gomi-calendar-r8':sortbin(176,652,.85)+arrow(300,650,.7)+calpage(438,652,.72),'shinryojo-kaigyo-shien':note(176,652,.85)+arrow(300,650,.7)+clinic(438,657,.6)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261121-set14.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261121-set14';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
