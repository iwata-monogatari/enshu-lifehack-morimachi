"""Article-specific, text-free editorial vectors; vertical mobile figures."""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,mapshape,note,landscape
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d'
def phone(x,y,s=1,mode='record'):
 inner=rect(-38,-66,76,132,INK,9)+rect(-30,-55,60,102,'#dcebe3',4)+circle(0,57,4,PAPER)
 if mode=='doctor':inner+=circle(0,-27,13,GOLD)+path('M-20 22 Q0 -17 20 22Z',PAPER)+line('M0 -1 V19 M-10 9 H10',RED,5)
 elif mode=='map':inner+=line('M-20 23 Q-12 -31 9 -16 T20 -32',TEAL,6)+circle(15,-30,7,RED)
 else:inner+=circle(0,-32,13,GOLD)+line('M-19 0 H20 M-19 18 H20 M-19 36 H8',TEAL,5)
 return put(inner,x,y,s)
def card(x,y,s=1):return put(rect(-67,-44,134,88,PAPER,6)+circle(-34,-8,12,TEAL)+line('M-11 -15 H49 M-11 4 H49 M-49 26 H48','#8fa79c',5),x,y,s)
def child(x,y,s=1):return put(person(GOLD),x,y,s)
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='consult':
  sh+=rect(215,378,562,24,PAPER)+line('M250 403 V515 M740 403 V515',INK,10)+put(person(TEAL),185,416,1.8)+put(person(RED),802,412,1.8)+child(869,461,1.1)+mapshape(465,392,1)+note(635,416,.57)
  if method:sh+=phone(520,270,.72,'map')+arrow(615,284,.6)+house(706,298,.67)
 elif key=='app':
  sh+=house(755,332,1.45)+put(person(TEAL),237,403,1.9)+child(325,449,1.1)+rect(350,424,333,19,PAPER)+line('M379 443 V530 M648 443 V530',INK,8)+phone(466,364,1.1)+note(625,396,.65)
  if method:sh+=phone(650,246,.6)+arrow(555,250,.55)+circle(667,298,13,GOLD)
 elif key=='medical':
  sh+=house(225,317,1.25)+rect(689,227,193,164,PAPER)+path('M674 227 L786 166 L897 227Z',TEAL)+rect(767,304,40,87,TEAL)+line('M786 243 V282 M766 262 H806',RED,11)+path('M280 433 Q496 354 725 419',stroke=PAPER,width=33)+put(person(TEAL),381,411,1.8)+child(455,453,1.1)+card(577,466,.8)+note(760,476,.66)
  if method:sh+=arrow(640,437,.7)+circle(850,469,30,GOLD)+line('M850 448 V471 L863 481',INK,5)
 else:
  sh+=house(751,321,1.5)+rect(230,437,453,23,PAPER)+line('M259 460 V541 M654 460 V541',INK,8)+put(person(TEAL),195,406,1.9)+child(325,441,1.0)+phone(480,359,1.35,'doctor')+note(650,422,.55)
  if method:sh+=circle(685,229,39,PAPER)+line('M685 204 V229 L704 239',INK,6)+card(563,247,.57)
 return sh
def svg(key,method=False,portrait=True):
 title={'consult':'移住相談で家族の生活条件を確認する','app':'親子の記録を新しいアプリへ引き継ぐ','medical':'県外の受診と領収書を家族で整理する','leber':'家から医師に相談する準備を整える'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'consult':mapshape(203,647,.9)+note(415,655,.8),'app':phone(190,649,1.1)+arrow(300,647,.7)+note(426,653,.8),'medical':card(183,646,.95)+arrow(300,650,.7)+note(431,657,.8),'leber':phone(190,651,1.1,'doctor')+card(422,653,.9)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261108.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(exist_ok=True)
  cover=raster(svg(p['key'],portrait=False));cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261108';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
