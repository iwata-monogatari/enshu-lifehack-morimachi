"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 19 set-12 batch. Same approach as the set-11 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: a student ID
card with a mortarboard cap and an application form, a declaration
flowchart with a withholding slip and a calendar, an office building with
a job-listing monitor and a registration form, and a house with a damaged
roof beside a camera and a hand-drawn floor plan.
"""
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
def studentcard(x,y,s=1):
 g=rect(-88,-56,176,112,PAPER,7)+rect(-88,-56,176,24,GOLD,7)+circle(-50,14,18,TEAL)+path('M-50 0 Q-64 32 -50 32 Q-36 32 -50 0',INK,'none')+line('M-16 -6 H64 M-16 14 H64 M-16 34 H42','#8fa79c',6)
 return put(g,x,y,s)
def cap(x,y,s=1):
 g=path('M0 -18 L74 8 L0 34 L-74 8Z',INK,'none')+path('M-38 20 V44 Q0 60 38 44 V20 L0 34Z',TEAL,'none')+line('M74 8 V44',GOLD,6)+circle(74,50,7,GOLD)
 return put(g,x,y,s)
def form(x,y,s=1):
 g=rect(-64,-86,128,172,PAPER,6)+rect(-64,-86,128,26,TEAL,6)+line('M-42 -38 H42 M-42 -12 H42 M-42 14 H42 M-42 40 H20','#8fa79c',6)+path('M-40 62 L-28 74 L44 52',RED,'none')
 return put(g,x,y,s)
def diamond(x,y,s=1):
 g=path('M0 -52 L64 0 L0 52 L-64 0Z',PAPER,'none')+line('M0 -52 L64 0 L0 52 L-64 0Z',INK,4)+path('M-18 0 L-6 13 L20 -14',TEAL,'none')
 return put(g,x,y,s)
def slip(x,y,s=1):
 g=rect(-84,-60,168,120,PAPER,6)+rect(-84,-60,168,22,RED,6)+line('M-62 -18 H62 M-62 6 H62 M-62 30 H30','#8fa79c',5)+rect(36,22,34,22,GOLD,3)
 return put(g,x,y,s)
def calendar(x,y,s=1):
 g=rect(-70,-76,140,152,PAPER,6)+rect(-70,-76,140,30,TEAL,6)+circle(-38,-84,8,INK)+circle(38,-84,8,INK)
 for r in range(3):
  for c in range(4):
   g+=rect(-56+c*30,-30+r*32,20,20,'#dcebe2' if (r+c)%2 else GOLD,2)
 return put(g,x,y,s)
def office(x,y,s=1):
 g=rect(-78,-110,156,220,'#dcebe2',5)+line('M-78 -110 H78',INK,5)
 for r in range(4):
  for c in range(3):
   g+=rect(-58+c*42,-88+r*44,26,28,'#9fc1b9',2)
 g+=rect(-16,58,32,52,TEAL,3)
 return put(g,x,y,s)
def monitor(x,y,s=1):
 g=rect(-96,-66,192,132,INK,7)+rect(-84,-54,168,96,PAPER,3)+line('M-68 -34 H20 M-68 -12 H44 M-68 10 H8','#8fa79c',6)+circle(52,-22,16,GOLD)+rect(40,8,52,20,TEAL,3)+line('M0 66 V88 M-30 92 H30',INK,7)
 return put(g,x,y,s)
def damagedhouse(x,y,s=1):
 g=rect(-72,-30,144,96,PAPER)+path('M-88 -30 L0 -84 L34 -52 L58 -70 L88 -30Z','#816b57','none')+line('M34 -52 L48 -30 M48 -30 L40 -8',RED,6)+rect(-14,8,28,58,TEAL)+rect(34,-8,24,24,GOLD)+line('M-88 66 H88',INK,5)
 return put(g,x,y,s)
def plan(x,y,s=1):
 g=rect(-84,-64,168,128,PAPER,6)+line('M-84 -10 H20 M20 -64 V62 M-30 24 H84',INK,4)+path('M-58 -38 L-30 -12 L-52 8 L-24 30',RED,'none')+circle(52,-30,12,RED)+line('M46 -36 L58 -24 M58 -36 L46 -24',RED,5)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='gakusei-nofu-tokurei':
  sh+=studentcard(590,300,1.5)+cap(796,168,.95)+put(person(TEAL),212,414,1.85)+house(120,318,.6)
  if method:sh+=form(282,240,.72)+arrow(442,246,.55)+studentcard(640,252,.68)+checkbadge(806,232,.9)
 elif key=='shinkoku-hantei':
  sh+=diamond(590,250,1.35)+slip(796,420,.95)+calendar(300,180,.8)+put(person(PINK),150,430,1.6)
  if method:sh+=slip(282,240,.72)+arrow(442,246,.55)+diamond(630,246,1.0)+checkbadge(806,232,.9)
 elif key=='iju-hojin-toroku':
  sh+=office(560,300,1.3)+monitor(810,220,.85)+put(person(TEAL),212,414,1.85)+put(tree(),930,350,.8)
  if method:sh+=form(282,240,.72)+arrow(442,246,.55)+office(640,252,.55)+checkbadge(806,232,.9)
 else:
  sh+=damagedhouse(570,320,1.45)+camera(800,190,.95)+put(person(RED),212,414,1.85)+plan(250,180,.75)
  if method:sh+=camera(282,238,.85)+arrow(442,246,.55)+plan(630,240,.85)+checkbadge(806,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'gakusei-nofu-tokurei':'学生証と帽子と申請書','shinkoku-hantei':'申告判定の菱形と源泉徴収票と暦','iju-hojin-toroku':'事業所の建物と求人画面と登録申請書','risai-shomei':'被害を受けた家とカメラと平面図'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'gakusei-nofu-tokurei':form(176,652,.62)+arrow(300,650,.7)+cap(438,652,.95),'shinkoku-hantei':calendar(176,652,.72)+arrow(300,650,.7)+slip(438,652,.78),'iju-hojin-toroku':monitor(176,652,.72)+arrow(300,650,.7)+form(438,652,.62),'risai-shomei':plan(176,652,.78)+arrow(300,650,.7)+damagedhouse(438,657,.68)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261119-set12.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261119-set12';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
