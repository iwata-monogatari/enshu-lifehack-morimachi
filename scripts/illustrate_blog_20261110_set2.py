"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 10 set-2 batch (Tuesday). Writes cover.svg (the vector artwork
itself, which the article pages reference), a local cover.jpg raster (same
artwork, kept for the local quality gates and the contact sheet), and the
two portrait figures per article. Every article gets its own scene; fig1
shows the scene, fig2 shows the method, never a recolor of fig1.
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,mapshape,note,landscape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def card(x,y,s=1,pink=False):return put(rect(-67,-44,134,88,PINK if pink else PAPER,6)+circle(-34,-8,12,TEAL)+line('M-11 -15 H49 M-11 4 H49 M-49 26 H48','#8fa79c',5),x,y,s)
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def boxes(x,y,s=1):return put(rect(-72,6,66,52,'#c9a86a',6)+rect(-4,-16,66,74,'#b8935a',6)+rect(-66,-42,58,46,'#d8ba7d',6)+line('M-72 6 H-6 M-4 -16 H62 M-66 -42 H-8',INK,3),x,y,s)
def panel(x,y,s=1):
 g=rect(-58,-78,116,156,PAPER,8)
 for i in range(3):g+=rect(-40,-58+i*44,32,26,TEAL if i!=1 else RED,3)+line(f'M2 {-45+i*44} H42',INK,4)
 return put(g,x,y,s)
def bolt(x,y,s=1):return put(path('M8 -52 L-26 8 L-2 8 L-12 52 L28 -10 L2 -10Z',GOLD,INK),x,y,s)
def brace_house(x,y,s=1):return put(rect(-70,-58,140,116,PAPER)+path('M-88 -58 L0 -102 L88 -58Z','#816b57')+line('M-70 -58 L70 58 M70 -58 L-70 58',RED,6)+rect(-14,8,28,50,TEAL),x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='koseki':
  sh+=house(700,318,1.7)+rect(250,424,420,19,PAPER)+line('M280 443 V530 M640 443 V530',INK,8)+put(person(TEAL),205,414,1.85)+card(452,462,.85)+card(540,452,.7,True)+house(120,330,.8)
  if method:sh+=card(300,238,.6)+card(430,222,.6,True)+card(560,238,.6)+arrow(690,300,.6)+card(790,262,.75)
 elif key=='rikatsuyo':
  sh+=house(520,318,1.8)+boxes(238,452,1.05)+put(person(RED),770,414,1.8)+circle(852,330,34,GOLD)+line('M852 308 V352 M832 322 H872',INK,5)
  if method:sh+=note(300,240,.6)+arrow(452,262,.55)+rect(560,196,150,96,'#c9a86a',6)+line('M560 244 H710 M635 196 V292',INK,4)
 elif key=='taishin':
  sh+=brace_house(505,330,1.75)+put(person(TEAL),215,414,1.85)+put(person(GOLD),800,410,1.7)+line('M760 330 L742 268',INK,5)+circle(730,238,34,'none')+line('M730 214 V262 M706 238 H754',RED,5)
  if method:sh+=circle(300,232,58,'none')+line('M342 274 L404 336',INK,9)+line('M272 232 H328 M300 204 V260',TEAL,6)+arrow(520,262,.55)+note(700,240,.58)
 else:
  sh+=house(760,326,1.4)+panel(430,360,1.15)+bolt(560,268,.9)+put(person(TEAL),205,414,1.85)+line('M262 372 L352 356',INK,6)
  if method:sh+=panel(268,232,.62)+arrow(420,246,.55)+circle(560,238,40,TEAL)+path('M538 238 L554 254 L586 218',stroke=PAPER,width=7)
 return sh
def svg(key,method=False,portrait=True):
 title={'koseki':'森町役場の窓口で各地の本籍の戸籍をまとめて請求する','rikatsuyo':'相続した空き家の残置物と改修の計画を見比べる家族','taishin':'実家の筋交いを専門家と一緒に確認する家族','kanshin':'実家の分電盤を開けて感震機能の有無を確認する家族'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'koseki':card(183,646,.95)+arrow(300,650,.7)+note(431,657,.8),'rikatsuyo':boxes(170,650,1.0)+arrow(300,650,.7)+house(430,672,.62),'taishin':brace_house(183,657,.62)+arrow(300,650,.7)+note(431,657,.8),'kanshin':panel(178,650,.72)+arrow(300,650,.7)+bolt(428,650,.8)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261110-set2.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261110-set2';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
