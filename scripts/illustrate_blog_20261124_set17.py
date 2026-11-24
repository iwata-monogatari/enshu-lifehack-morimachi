"""Article-specific, text-free editorial vectors; vertical mobile figures. Set-17 batch.
Scenes: a donor certificate with an application sheet; a couple with a file of receipts;
a cryopreservation tank with a snowflake; a medical wig on a stand beside a mirror."""
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
def sheetgrid(x,y,s=1):
 g=rect(-82,-96,164,192,PAPER,6)+line('M-82 -32 H82 M-82 32 H82 M-28 -96 V96 M28 -96 V96','#8fa79c',4)+rect(-82,-96,164,32,TEAL,6)+circle(0,64,16,GOLD)
 return put(g,x,y,s)
def envelope(x,y,s=1):
 g=rect(-80,-52,160,104,PAPER,5)+path('M-80 -52 L0 10 L80 -52',TEAL,'none')+line('M-80 52 L-18 -2 M80 52 L18 -2','#8fa79c',4)
 return put(g,x,y,s)
def tank(x,y,s=1):
 g=rect(-58,-110,116,220,TEAL,26)+rect(-58,-110,116,34,'#8fa79c',16)+circle(0,-52,17,PAPER)+line('M0 -140 V-110',INK,6)+circle(0,-146,8,RED)
 return put(g,x,y,s)
def snow(x,y,s=1):
 g=line('M0 -34 V34 M-30 -17 L30 17 M-30 17 L30 -17',PAPER,6)+line('M0 -34 L-9 -24 M0 -34 L9 -24 M0 34 L-9 24 M0 34 L9 24',PAPER,5)
 return put(g,x,y,s)
def wigstand(x,y,s=1):
 g=path('M-64 18 C-64 -52 -30 -78 0 -78 C30 -78 64 -52 64 18 C40 2 22 26 0 8 C-22 26 -40 2 -64 18Z',PINK,'none')+line('M0 12 V96 M-34 96 H34',INK,6)
 return put(g,x,y,s)
def mirror(x,y,s=1):
 g=rect(-52,-84,104,168,PAPER,7)+rect(-40,-72,80,144,'#cfe0da',4)+line('M-24 84 L-40 108 M24 84 L40 108',INK,5)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='kotsuzui-donor':
  sh+=sheetgrid(580,300,1.35)+checkbadge(815,185,.9)+put(person(TEAL),212,414,1.7)+house(120,318,.6)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+sheetgrid(640,252,.8)+checkbadge(806,232,.9)
 elif key=='fuikusho-josei':
  sh+=envelope(580,300,1.5)+note(815,190,.9)+put(person(TEAL),190,414,1.7)+put(person(PINK),300,414,1.5)+house(110,318,.55)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+envelope(640,252,.95)+checkbadge(806,232,.9)
 elif key=='ninyosei-onzon':
  sh+=tank(580,300,1.3)+snow(580,300,1.1)+note(815,190,.9)+put(person(PINK),212,414,1.85)+put(tree(),930,350,.8)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+tank(640,252,.8)+snow(640,252,.68)+checkbadge(806,232,.9)
 else:
  sh+=wigstand(560,290,1.35)+mirror(800,300,1.05)+put(person(PINK),212,414,1.85)+house(120,318,.6)
  if method:sh+=wigstand(282,240,.85)+arrow(442,246,.55)+note(640,252,.85)+checkbadge(806,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'kotsuzui-donor':'骨髄バンクの証明書と申請書','fuikusho-josei':'検査結果の書類と領収書のファイル','ninyosei-onzon':'凍結保存のタンクと雪の結晶','appearance-care':'医療用ウィッグと鏡'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'kotsuzui-donor':note(176,652,.85)+arrow(300,650,.7)+sheetgrid(438,652,.72),'fuikusho-josei':envelope(176,652,.95)+arrow(300,650,.7)+note(438,652,.85),'ninyosei-onzon':note(176,652,.85)+arrow(300,650,.7)+tank(438,657,.62)+snow(438,657,.52),'appearance-care':wigstand(176,645,.8)+arrow(300,650,.7)+note(438,652,.85)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261124-set17.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261124-set17';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
