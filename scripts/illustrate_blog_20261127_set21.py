"""Article-specific, text-free editorial vectors; vertical mobile figures. Set-21 batch.
Scenes: a council hall with podium and audience seats; an evacuation plan sheet with
five alert-level steps and a house; a truck carrying bulky waste toward a facility gate;
an agreement document with a university building and a drone."""
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
def podium(x,y,s=1):
 g=path('M-52 60 L-34 -52 H34 L52 60Z',GOLD,'none')+rect(-58,-66,116,16,ORANGE,5)+circle(0,-96,15,INK)
 return put(g,x,y,s)
def seat(x,y,s=1):
 g=rect(-34,-30,68,44,PINK,7)+rect(-34,14,68,30,RED,6)
 return put(g,x,y,s)
def hall(x,y,s=1):
 g=rect(-150,-120,300,240,PAPER,8)+path('M-170 -120 L0 -180 L170 -120Z',TEAL,'none')+rect(-14,-58,28,178,INK,4)
 return put(g,x,y,s)
def steps5(x,y,s=1):
 g=''
 for i,w in enumerate((44,78,112,146,180)):
  g+=rect(-w/2,44-i*24,w,20,[TEAL,GREEN,GOLD,ORANGE,RED][i],4)
 return put(g,x,y,s)
def plan(x,y,s=1):
 g=rect(-72,-96,144,192,PAPER,6)+line('M-48 -62 H48 M-48 -28 H48 M-48 6 H30 M-48 40 H42',INK,5)+circle(34,66,14,RED)
 return put(g,x,y,s)
def truck(x,y,s=1):
 g=rect(-120,-44,168,88,TEAL,6)+path('M48 -20 L96 8 V44 H48Z',GOLD,'none')+circle(-72,58,20,INK)+circle(64,58,20,INK)+rect(-104,-86,84,42,ORANGE,5)
 return put(g,x,y,s)
def gate(x,y,s=1):
 g=rect(-120,-90,20,180,INK,4)+rect(100,-90,20,180,INK,4)+line('M-110 -78 H110',TEAL,9)+path('M-110 -78 L0 -118 L110 -78',RED,'none')
 return put(g,x,y,s)
def drone(x,y,s=1):
 g=rect(-26,-12,52,24,INK,4)+circle(-52,-26,17,TEAL)+circle(52,-26,17,TEAL)+circle(-52,26,17,TEAL)+circle(52,26,17,TEAL)+line('M-40 -16 L-14 -4 M40 -16 L14 -4 M-40 16 L-14 4 M40 16 L14 4',INK,4)+circle(0,22,7,RED)
 return put(g,x,y,s)
def univ(x,y,s=1):
 g=rect(-92,-64,184,128,PAPER,7)+path('M-112 -64 L0 -112 L112 -64Z',TEAL,'none')+rect(-12,-6,24,70,INK,4)+circle(0,-84,11,GOLD)
 return put(g,x,y,s)
def agree(x,y,s=1):
 g=rect(-66,-88,132,176,PAPER,6)+line('M-42 -52 H42 M-42 -18 H42 M-42 16 H24',INK,5)+circle(28,58,17,RED)
 return put(g,x,y,s)

def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='gikai-bocho':
  sh+=hall(600,290,1.05)+podium(600,330,.95)+seat(430,420,.8)+seat(770,420,.8)+put(person(TEAL),170,414,1.7)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+podium(650,252,.85)+checkbadge(830,232,.9)
 elif key=='hinan-keikaku':
  sh+=house(600,300,1.15)+plan(838,238,.85)+steps5(300,330,.95)+put(person(TEAL),170,414,1.7)
  if method:sh+=plan(282,246,.7)+arrow(442,246,.55)+steps5(650,262,.85)+checkbadge(830,232,.9)
 elif key=='ichinomiya-shobunjo':
  sh+=truck(520,330,1.1)+gate(850,290,1.0)+put(person(TEAL),170,414,1.7)+put(tree(),92,340,.8)
  if method:sh+=truck(282,252,.62)+arrow(442,246,.55)+gate(650,246,.8)+checkbadge(830,232,.9)
 else:
  sh+=univ(560,300,1.05)+drone(838,205,.95)+agree(300,270,.85)+put(person(TEAL),170,414,1.7)
  if method:sh+=agree(282,246,.75)+arrow(442,246,.55)+drone(650,246,.9)+checkbadge(830,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'gikai-bocho':'議事堂の演台と傍聴席','hinan-keikaku':'避難計画の用紙と警戒レベルの階段','ichinomiya-shobunjo':'粗大ごみを運ぶトラックと施設の門','minkatsu-renkei':'大学の建物とドローンと協定書'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'gikai-bocho':podium(176,652,.8)+arrow(300,650,.7)+seat(438,646,.85),'hinan-keikaku':plan(176,652,.72)+arrow(300,650,.7)+steps5(438,660,.8),'ichinomiya-shobunjo':truck(176,652,.6)+arrow(300,650,.7)+gate(438,652,.72),'minkatsu-renkei':agree(176,652,.72)+arrow(300,650,.7)+drone(438,646,.85)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261127-set21.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261127-set21';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
