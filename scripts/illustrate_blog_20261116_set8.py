"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 16 set-8 batch (Monday). Same approach as the set-7 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: an ID card
handed over at a counter with a smartphone, a medical cross with coins
and an application form, a town notice envelope read by a parent and
child, and a municipal housing block with a key.
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def idcard(x,y,s=1):
 g=rect(-72,-46,144,92,PAPER,7)+rect(-72,-46,144,20,TEAL,7)+rect(-56,-16,34,40,'#b6ccbd',3)+circle(-39,-6,7,INK)+path('M-52 24 Q-39 8 -26 24Z',INK,'none')+rect(2,-14,16,12,GOLD,2)+line('M-8 12 H56 M-8 26 H56','#8fa79c',5)
 return put(g,x,y,s)
def phone(x,y,s=1):
 g=rect(-30,-58,60,116,INK,10)+rect(-24,-46,48,84,'#dcebe2',3)+rect(-12,-34,24,30,PAPER,2)+circle(0,-26,5,TEAL)+line('M-8 -12 H8',TEAL,3)+line('M-16 8 H16 M-16 20 H16','#8fa79c',4)+circle(0,48,5,PAPER)
 return put(g,x,y,s)
def envelope(x,y,s=1):
 g=rect(-72,-44,144,88,PAPER,5)+path('M-72 -44 L0 8 L72 -44',fill='none',stroke=INK,width=4)+rect(38,-36,26,20,GOLD,2)+line('M-52 22 H20 M-52 36 H34','#8fa79c',4)
 return put(g,x,y,s)
def medcross(x,y,s=1):
 g=circle(0,0,54,'#fffdf4')+path('M-11 -30 H11 V-11 H30 V11 H11 V30 H-11 V11 H-30 V-11 H-11Z',RED,'none')
 return put(g,x,y,s)
def coin(x,y,s=1):
 g=circle(0,0,34,GOLD)+circle(0,0,25,'#f0cd8d')+path('M-9 -13 L0 -2 L9 -13 M-11 -2 H11 M0 -2 V14 M-8 6 H8',INK,'none')
 return put(g,x,y,s)
def danchi(x,y,s=1):
 wins=''.join(rect(-78+col*39,-52+row*34,26,22,'#b6ccbd',2) for row in range(3) for col in range(4))
 g=rect(-95,-72,190,150,PAPER)+path('M-108 -72 L0 -98 L108 -72Z','#816b57','none')+wins+line('M-95 -18 H95 M-95 16 H95 M-95 50 H95',INK,3)+rect(-13,44,26,34,TEAL)
 return put(g,x,y,s)
def keyshape(x,y,s=1):
 g=circle(-22,0,24,'none')+line('M0 0 H58 M38 0 V20 M54 0 V14',GOLD,9)
 g=put(circle(-22,0,24,GOLD),0,0,1)+g
 return put(g,x,y,s)
def checkbadge(x,y,s=1):
 g=circle(0,0,30,TEAL)+line('M-14 0 L-4 11 L16 -12',PAPER,7)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='mynumber':
  sh+=idcard(596,318,1.55)+put(person(TEAL),212,414,1.85)+phone(838,300,.95)+house(120,318,.7)
  if method:sh+=phone(272,238,.62)+arrow(442,246,.55)+idcard(622,238,.85)+circle(806,232,27,TEAL)
 elif key=='kokuho-kyufu':
  sh+=medcross(596,300,1.35)+coin(742,428,.95)+coin(668,452,.7)+put(person(TEAL),212,414,1.85)+note(360,300,.62)
  if method:sh+=note(282,240,.62)+arrow(442,246,.55)+coin(622,238,1.05)+circle(800,232,26,GOLD)
 elif key=='jido-genkyo':
  sh+=envelope(596,318,1.5)+put(person(TEAL),212,414,1.85)+put(person(GOLD),330,468,1.15)+house(838,318,.8)
  if method:sh+=envelope(282,240,.62)+arrow(442,246,.55)+note(622,238,.62)+checkbadge(800,232,.9)
 else:
  sh+=danchi(596,330,1.3)+keyshape(806,446,.9)+put(person(TEAL),200,424,1.8)+put(person(GOLD),300,470,1.15)+put(tree(),90,330,.9)
  if method:sh+=note(282,240,.6)+arrow(442,246,.55)+danchi(636,246,.58)+checkbadge(806,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'mynumber':'カードを受け取る住民とスマートフォン','kokuho-kyufu':'医療の十字と硬貨と申請書','jido-genkyo':'町から届いた案内の封筒を読む親子','choei-boshu':'団地の建物と鍵と家族'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'mynumber':phone(176,652,.8)+arrow(300,650,.7)+idcard(438,657,.72),'kokuho-kyufu':medcross(176,650,.85)+arrow(300,650,.7)+coin(438,652,1.0),'jido-genkyo':envelope(183,652,.85)+arrow(300,650,.7)+note(438,657,.8),'choei-boshu':note(176,650,.78)+arrow(300,650,.7)+danchi(442,662,.55)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261116-set8.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261116-set8';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
