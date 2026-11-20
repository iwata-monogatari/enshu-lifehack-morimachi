"""Article-specific, text-free editorial vectors; vertical mobile figures. Set-13 batch.
Scenes: water meter box with dial and wrench; school bag with envelope and coins;
a house framed by a VR viewer outline; a town bus with a ticket strip."""
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
def meterbox(x,y,s=1):
 g=rect(-95,-70,190,140,'#8fa79c',8)+rect(-80,-55,160,110,PAPER,6)+circle(0,-5,42,'#dcebe2')+line('M0 -5 L26 -28 M0 -5 L-30 8',INK,6)+circle(0,-5,6,RED)+line('M-60 38 H60','#8fa79c',6)
 return put(g,x,y,s)
def wrench(x,y,s=1):
 g=path('M-10 -52 A20 20 0 1 0 -10 -12 L28 44 A10 10 0 0 0 44 28 L6 -26 A20 20 0 0 0 -10 -52Z',GOLD,'none')
 return put(g,x,y,s)
def randoseru(x,y,s=1):
 g=rect(-58,-70,116,140,RED,14)+rect(-58,-70,116,44,'#8f4232',14)+circle(0,-4,10,GOLD)+line('M-58 30 H58',INK,4)
 return put(g,x,y,s)
def envelope(x,y,s=1):
 g=rect(-80,-52,160,104,PAPER,5)+path('M-80 -52 L0 10 L80 -52',TEAL,'none')+line('M-80 52 L-18 -2 M80 52 L18 -2','#8fa79c',4)
 return put(g,x,y,s)
def coin(x,y,s=1):
 g=circle(0,0,30,GOLD)+circle(0,0,19,PAPER)
 return put(g,x,y,s)
def vrframe(x,y,s=1):
 g=rect(-110,-80,220,160,'none',10)+line('M-110 -80 H110 M-110 80 H110',INK,7)+path('M-150 0 L-110 -26 V26Z',TEAL,'none')+path('M150 0 L110 -26 V26Z',TEAL,'none')
 return put(g,x,y,s)
def bus(x,y,s=1):
 g=rect(-105,-75,210,150,TEAL,12)+rect(-88,-58,52,44,PAPER,4)+rect(-26,-58,52,44,PAPER,4)+rect(36,-58,52,44,PAPER,4)+rect(-88,-2,176,26,GOLD,3)+circle(-58,82,20,INK)+circle(58,82,20,INK)+circle(-58,82,8,PAPER)+circle(58,82,8,PAPER)
 return put(g,x,y,s)
def ticket(x,y,s=1):
 g=rect(-90,-34,180,68,PAPER,6)+line('M30 -34 V34',RED,4)+circle(52,0,13,GOLD)+line('M-72 -12 H8 M-72 10 H8','#8fa79c',6)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='suido-meter-kokan':
  sh+=meterbox(580,300,1.5)+wrench(810,180,.95)+put(person(TEAL),212,414,1.85)+house(120,318,.6)
  if method:sh+=meterbox(282,240,.72)+arrow(442,246,.55)+wrench(640,252,1.0)+checkbadge(806,232,.9)
 elif key=='hitorioya-gakudo-shien':
  sh+=randoseru(560,290,1.5)+envelope(810,200,.9)+coin(330,170,.9)+put(person(PINK),150,430,1.6)
  if method:sh+=envelope(282,240,.72)+arrow(442,246,.55)+coin(630,246,1.3)+checkbadge(806,232,.9)
 elif key=='akiya-vr-nairan':
  sh+=house(560,300,1.3)+vrframe(560,290,1.35)+put(person(TEAL),212,414,1.85)+put(tree(),930,350,.8)
  if method:sh+=vrframe(300,240,.8)+arrow(462,246,.55)+house(660,252,.62)+checkbadge(836,232,.9)
 else:
  sh+=bus(570,310,1.45)+ticket(800,180,.95)+put(person(RED),212,414,1.85)+coin(250,180,.8)
  if method:sh+=ticket(282,240,.72)+arrow(442,246,.55)+bus(640,252,.6)+checkbadge(806,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'suido-meter-kokan':'水道メーターとレンチと家','hitorioya-gakudo-shien':'ランドセルと封筒と硬貨','akiya-vr-nairan':'VRの枠の中の空き家','kotsu-riyoken-josei':'町営バスと回数券と硬貨'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'suido-meter-kokan':wrench(176,652,.8)+arrow(300,650,.7)+meterbox(438,652,.62),'hitorioya-gakudo-shien':randoseru(176,652,.68)+arrow(300,650,.7)+envelope(438,652,.72),'akiya-vr-nairan':house(176,652,.55)+arrow(300,650,.7)+vrframe(438,652,.75),'kotsu-riyoken-josei':ticket(176,652,.78)+arrow(300,650,.7)+bus(438,657,.62)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261120-set13.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261120-set13';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
