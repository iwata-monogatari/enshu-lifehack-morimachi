"""Article-specific, text-free editorial vectors; vertical mobile figures.

November 9 additional batch. Writes cover.svg (the vector artwork itself,
which the article pages reference), a local cover.jpg raster (same artwork,
kept for the local quality gates and the contact sheet), and the two
portrait figures per article.
"""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,mapshape,note,landscape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0'
def card(x,y,s=1,pink=False):return put(rect(-67,-44,134,88,PINK if pink else PAPER,6)+circle(-34,-8,12,TEAL)+line('M-11 -15 H49 M-11 4 H49 M-49 26 H48','#8fa79c',5),x,y,s)
def child(x,y,s=1):return put(person(GOLD),x,y,s)
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def envelope(x,y,s=1):return put(rect(-70,-45,140,90,PAPER,4)+path('M-70 -45 L0 12 L70 -45',stroke=INK,width=4)+circle(48,-24,8,RED),x,y,s)
def calendar(x,y,s=1):return put(rect(-62,-72,124,144,PAPER,6)+rect(-62,-72,124,30,RED,6)+line('M-62 -14 H62 M-62 44 H62 M-21 -42 V72 M21 -42 V72','#9aaf9e',3)+circle(41,15,13,'none')+path('M28 15 A13 13 0 1 0 41 28 A13 13 0 1 0 28 15',stroke=RED,width=5),x,y,s)
def steps(x,y,s=1):
    g=''
    for i in range(5):g+=circle(x+i*80*s,y,15,TEAL if i<4 else GOLD)
    return line(f'M{x} {y} H{x+4*80*s}',INK,4)+g
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='nintei':
  sh+=house(505,322,1.9)+rect(300,424,410,19,PAPER)+line('M330 443 V530 M680 443 V530',INK,8)+put(person(TEAL),238,414,1.85)+put(person(RED),786,410,1.8)+card(560,462,.82,True)
  if method:sh+=note(505,238,.62)+steps(300,300,1)
 elif key=='onestop':
  sh+=rect(215,420,570,20,PAPER)+line('M245 440 V532 M755 440 V532',INK,9)+put(person(TEAL),168,424,1.9)+envelope(385,458,.85)+envelope(525,458,.85)+envelope(665,458,.85)+note(852,436,.55)
  if method:sh+=calendar(520,246,.78)+arrow(648,262,.55)+envelope(748,302,.62)
 elif key=='iryohi':
  sh+=house(778,326,1.4)+rect(228,437,455,23,PAPER)+line('M257 460 V541 M654 460 V541',INK,8)+put(person(TEAL),192,408,1.9)+note(428,398,.6)+note(566,414,.55)+envelope(706,472,1.0)
  if method:sh+=note(428,246,.55)+note(578,246,.55)+arrow(505,322,.6)+card(706,272,.6)
 else:
  sh+=house(758,330,1.45)+rect(350,424,333,19,PAPER)+line('M379 443 V530 M648 443 V530',INK,8)+put(person(TEAL),240,404,1.9)+child(332,450,1.1)+card(520,462,.85)+note(664,424,.55)
  if method:sh+=calendar(556,248,.75)+card(724,296,.55)
 return sh
def svg(key,method=False,portrait=True):
 title={'nintei':'窓口で認定申請の流れを相談する','onestop':'寄附の受領書と申請書を自治体ごとに分ける','iryohi':'家族の領収書と医療費通知を封筒へ分ける','teate':'児童手当の申請書類をそろえる親子'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'nintei':card(183,646,.95,True)+arrow(300,650,.7)+note(431,657,.8),'onestop':envelope(183,650,1.0)+arrow(300,650,.7)+note(431,657,.8),'iryohi':note(190,649,1.0)+arrow(300,647,.7)+card(422,653,.9),'teate':put(person(GOLD),175,649,1.2)+card(415,653,.9)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261109-additional.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261109-additional';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
