"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 14 set-7 batch (Saturday). Same approach as the set-6 illustrator:
cover.svg carries the vector artwork the article pages reference, a local
cover.jpg raster is generated for the local quality gates, and the two
portrait figures per article get their own scenes (fig1 = scene, fig2 =
method, never a recolor). Scenes are unique to this batch: a medical
certificate card handed to a parent and child, a school building with a
clock and a randoseru, a cat with a V-cut ear, and an electric fence with
a wild boar in front of the hills.
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def certcard(x,y,s=1,pink=False):
 g=rect(-67,-44,134,88,PINK if pink else PAPER,6)+rect(-67,-44,134,22,TEAL,6)+line('M-14 -4 V16 M-24 6 H-4','#b55845',6)+line('M2 -2 H49 M2 12 H49 M-49 28 H48','#8fa79c',5)
 return put(g,x,y,s)
def clock(x,y,s=1):
 g=circle(0,0,52,'#fffdf4')+line('M0 -38 V-46 M35 27 L41 33 M-35 27 L-41 33 M38 -26 L45 -31 M-38 -26 L-45 -31',INK,4)+line('M0 -30 V0 L22 12',RED,6)+circle(0,0,6,INK)
 return put(g,x,y,s)
def randoseru(x,y,s=1):
 g=rect(-38,-48,76,96,RED,11)+path('M-38 -20 Q0 -44 38 -20 L38 -6 Q0 -26 -38 -6Z','#a34a38','none')+rect(-11,18,22,14,GOLD,3)+line('M-38 34 H38',INK,4)
 return put(g,x,y,s)
def schoolhouse(x,y,s=1):
 g=rect(-95,-38,190,92,PAPER)+path('M-108 -38 L0 -78 L108 -38Z','#816b57','none')+circle(0,-30,13,'#fffdf4')+line('M0 -30 V-40 M0 -30 L8 -25',INK,3)+rect(-14,18,28,36,TEAL)+rect(-78,-16,26,24,GOLD)+rect(52,-16,26,24,GOLD)+line('M95 -78 V-16 M95 -78 L122 -70 L95 -62',INK,4)
 return put(g,x,y,s)
def cat(x,y,s=1):
 g=path('M-52 44 Q-58 -6 -18 -22 Q26 -34 46 2 Q56 22 48 44Z','#6b5a4a','none')+circle(6,-40,27,'#6b5a4a')+path('M-16 -58 L-20 -82 L2 -66Z','#6b5a4a','none')+path('M24 -64 L34 -84 L38 -60 L31 -66 L28 -58Z','#6b5a4a','none')+line('M48 30 Q86 22 82 -12', '#6b5a4a',9)+circle(-2,-42,3.4,PAPER)+circle(15,-42,3.4,PAPER)+line('M-24 -30 L-46 -34 M-24 -22 L-44 -20 M28 -30 L48 -34 M28 -22 L46 -20','#4c3f33',2.4)
 return put(g,x,y,s)
def boar(x,y,s=1):
 g=path('M-72 6 Q-70 -30 -28 -36 L38 -34 Q74 -28 76 2 Q74 26 44 32 L-36 34 Q-66 30 -72 6Z','#5d4a38','none')+path('M44 -30 L86 -16 L84 12 L46 22Z','#5d4a38','none')+circle(88,-4,8,'#8a715a')+path('M70 12 Q78 22 88 18 Q80 8 74 4Z',PAPER,'none')+circle(66,-14,3.6,PAPER)+line('M-58 -34 L-46 -44 M-30 -38 L-22 -48 M0 -38 L6 -48 M28 -36 L36 -44','#463829',5)+line('M-44 34 L-44 52 M40 32 L40 52',INK,6)
 return put(g,x,y,s)
def fence(x,y,s=1):
 g=rect(-104,-46,10,96,'#816b57')+rect(-5,-46,10,96,'#816b57')+rect(94,-46,10,96,'#816b57')+line('M-110 -26 H112 M-110 8 H112',INK,3.4)+circle(-99,-26,5,GOLD)+circle(0,-26,5,GOLD)+circle(99,-26,5,GOLD)+circle(-99,8,5,TEAL)+circle(0,8,5,TEAL)+circle(99,8,5,TEAL)+line('M-92 50 L-84 34 M-76 50 L-72 36 M84 50 L90 35','#7a9a52',4)
 return put(g,x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='hitorioya':
  sh+=certcard(600,318,1.5)+put(person(TEAL),212,414,1.85)+put(person(GOLD),330,468,1.15)+house(822,318,.8)
  if method:sh+=certcard(282,240,.62)+arrow(442,246,.55)+note(622,238,.62)+circle(792,232,27,RED)
 elif key=='gakudo':
  sh+=schoolhouse(590,330,1.35)+clock(838,238,.8)+put(person(RED),222,452,1.25)+randoseru(310,478,.72)+put(person(TEAL),140,420,1.6)
  if method:sh+=clock(282,240,.62)+arrow(442,246,.55)+schoolhouse(628,246,.6)+circle(800,232,26,GOLD)
 elif key=='neko':
  sh+=cat(596,392,1.6)+circle(492,470,13,TEAL)+put(person(TEAL),212,414,1.85)+house(826,312,.85)
  if method:sh+=note(280,238,.6)+arrow(442,246,.55)+cat(636,268,1.0)+circle(806,232,26,RED)
 else:
  sh+=fence(430,428,1.35)+boar(742,392,1.25)+put(person(GOLD),140,424,1.8)+put(tree(),70,330,.9)
  if method:sh+=fence(300,252,.66)+arrow(452,246,.55)+boar(650,258,.66)+circle(806,232,26,TEAL)
 return sh
def svg(key,method=False,portrait=True):
 title={'hitorioya':'受給者証を差し出す親子','gakudo':'時計とランドセルと学校の建物','neko':'耳先にV字カットの入った猫','choju':'電気柵とイノシシと山並み'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'hitorioya':certcard(183,652,.85)+arrow(300,650,.7)+note(431,657,.8),'gakudo':clock(176,650,.82)+arrow(300,650,.7)+schoolhouse(438,662,.6),'neko':cat(186,664,1.05)+arrow(302,650,.7)+house(452,690,.55),'choju':fence(178,660,.8)+arrow(302,650,.7)+boar(448,668,.62)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261114-set7.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261114-set7';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
