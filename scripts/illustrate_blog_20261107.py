"""Original vector scenes: portrait figures and landscape editorial covers."""
import json,io
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261104_second import rect,path,put,circle,person,tree
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';PAPER='#fff4db';TEAL='#548e87';RED='#b55845';GOLD='#dfb66d'
def line(d,c=INK,w=4):return path(d,stroke=c,width=w)
def house(x,y,s=1):return put(rect(-48,-55,96,65,PAPER)+path('M-63 -55 L-2 -94 L63 -55Z','#816b57')+rect(-15,-29,26,39,TEAL)+rect(23,-31,17,19,GOLD),x,y,s)
def mapshape(x,y,s=1):return put(path('M-78 -51 L-26 -65 L25 -51 L78 -65 L77 52 L27 66 L-27 52 L-78 66Z',PAPER)+line('M-26 -62 V49 M26 -48 V63','#b5b79f',3)+line('M-58 30 Q-22 -32 0 -1 T60 -30',TEAL,7)+circle(-57,29,7,RED)+circle(59,-29,7,RED),x,y,s)
def note(x,y,s=1):return put(rect(-80,-66,160,132,PAPER,7)+line('M-53 -40 H58 M-53 -13 H58 M-53 14 H58 M-53 41 H21','#9aaf9e',5)+line('M-68 -47 V47',RED,4)+path('M49 56 L91 -44 L101 -39 L60 61Z',GOLD),x,y,s)
def fire(x,y,s=1):return put(rect(-20,-31,40,77,RED,9)+rect(-13,-43,26,14,INK)+line('M-4 -45 H26 Q43 -42 37 -7',INK,7)+rect(-11,-5,22,24,PAPER,3),x,y,s)
def generator(x,y,s=1):return put(rect(-51,-45,102,78,TEAL,8)+line('M-62 44 V-55 H63 V44 M-61 43 H63',INK,8)+rect(-34,-25,37,39,'#b6ccbd',3)+circle(28,-5,13,INK)+rect(-29,-68,45,13,INK,4)+line('M-29 -19 V8 M-17 -19 V8',INK,4),x,y,s)
def piano(x,y,s=1):
 return put(path('M-99 -46 Q-101 -105 -40 -108 Q32 -116 83 -63 L94 -3 L-94 -3Z',INK)+path('M-90 -45 L77 -67 L77 -52 L-89 -28Z','#4c6560')+path('M-91 -43 L-81 -112 L72 -140 L79 -66Z','#38645e')+rect(-97,-26,155,25,PAPER,2)+line('M-96 -2 H64',INK,5)+line('M-79 0 L-73 57 M47 0 L53 57 M84 -22 L84 36',INK,9)+''.join(line(f'M{x} -24 V-3',INK,2) for x in range(-85,55,12))+rect(-72,-25,8,14,INK)+rect(-47,-25,8,14,INK)+rect(-11,-25,8,14,INK)+rect(13,-25,8,14,INK),x,y,s)
def camera(x,y,s=1):return put(rect(-40,-29,80,57,INK,7)+circle(-2,-2,22,'#9fc1b9')+circle(-2,-2,12,INK)+rect(-24,-43,37,15,TEAL)+line('M0 29 V81 M0 47 L-41 92 M0 47 L43 92',INK,7),x,y,s)
def drum(x,y,s=1):return put(rect(-36,-37,72,77,RED,8)+path('M-37 -28 Q0 -45 37 -28 M-37 27 Q0 44 37 27',stroke=PAPER,width=7)+line('M-27 -31 L-15 32 L0 -32 L15 33 L27 -31',GOLD,4)+line('M-45 48 H47 M-28 48 L-37 77 M29 48 L38 77',INK,7),x,y,s)
def landscape():
 return rect(-2,-2,1004,564,'#e3ebda')+circle(854,81,36,'#edcb87')+path('M-5 234 L136 101 L226 173 L350 76 L474 188 L604 108 L721 192 L865 105 L1005 211 V565 H-5Z','#97b5a3','none')+path('M-5 302 Q180 173 338 252 T636 231 T1005 255 V565 H-5Z','#648e7a','none')+path('M-5 342 Q338 265 1005 321 V565 H-5Z','#d6cc9e','none')+line('M-5 382 Q226 314 382 351 M-5 410 Q211 345 365 380 M-5 438 Q218 374 350 411','#91a16b',8)+house(826,318,.8)+house(915,337,.65)+put(tree(),74,344,1.3)
def scene(key,method=False):
 sh=landscape()+path('M-5 448 Q414 369 1005 424 V565 H-5Z','#b7a987','none')
 if method:
  sh+=path('M202 388 L778 370 L908 550 L136 550Z','#dfc593')+put(person(TEAL),123,467,2.1)+put(person(RED),904,460,1.9)
  if key=='volunteer':sh+=note(330,459,1.0)+mapshape(625,439,.95)+line('M420 437 Q473 399 511 426',TEAL,7)+circle(756,470,37,PAPER)+line('M756 443 V470 L777 481',TEAL,6)
  elif key=='fire':sh+=mapshape(472,448,1.4)+generator(271,445,.6)+fire(703,431,1)+line('M364 488 Q462 538 633 490',TEAL,6)
  elif key=='piano':sh+=note(341,442,1.1)+note(665,442,1.1)+piano(514,351,.34)+circle(515,493,27,PAPER)+line('M515 475 V495 L529 503',TEAL,5)
  else:sh+=note(293,451,.85)+note(511,423,.85)+note(734,451,.85)+line('M369 480 L423 456 M585 456 L647 480',TEAL,6)
 elif key=='volunteer':sh+=house(525,337,1.4)+put(person(TEAL),316,443,2.2)+put(person(RED),681,454,2)+mapshape(500,454,1.3)+line('M245 523 Q491 493 785 539','#7a795f',7)
 elif key=='fire':sh+=rect(249,271,358,24,GOLD)+path('M221 270 L295 202 H565 L638 270Z',PAPER)+rect(275,295,17,152,INK)+rect(570,295,17,152,INK)+rect(291,361,280,19,GOLD)+generator(432,442,1.1)+fire(720,434,1.25)+put(person(TEAL),809,410,1.9)+line('M400 490 Q517 520 598 491',INK,5)
 elif key=='piano':sh+=rect(174,188,666,262,PAPER)+rect(181,196,103,242,RED)+rect(732,196,101,242,RED)+rect(198,445,609,31,INK)+piano(509,390,1.7)+put(person(TEAL),771,415,1.6)+note(853,488,.52)
 else:sh+=rect(191,218,512,214,PAPER)+rect(197,224,58,200,RED)+rect(646,224,50,200,RED)+drum(372,373,.85)+put(person(TEAL),491,366,1.6)+line('M472 294 L549 310',GOLD,6)+rect(204,429,489,22,INK)+camera(758,399,1.0)+rect(768,475,151,82,INK,9)+rect(777,482,133,64,'#a2c3b7',4)+drum(843,527,.4)
 return sh
def svg(key,method=False,portrait=True):
 names={'volunteer':'町を学ぶ案内役','fire':'露店の器具と消防への相談','piano':'舞台のピアノと費用の確認','archive':'祭り囃子の演奏と記録'}
 content=scene(key,method)
 if portrait:
  # Wide scene remains complete; a second lower vignette creates a vertical reading order.
  lower={'volunteer':mapshape(287,648,1.1)+note(446,661,.8),'fire':generator(215,654,.9)+fire(420,643,1.2),'piano':piano(224,665,.75)+note(441,643,.8),'archive':camera(194,609,.75)+note(413,649,.9)}[key]
  content=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{content}</g>'+line('M300 458 V516 M279 496 L300 518 L321 496',TEAL,7)+lower+put(tree(),65,710,1)+house(543,722,.6)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{names[key]}</title>{content}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261107.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(exist_ok=True)
  cover=raster(svg(p['key'],portrait=False));cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');im=raster(raw);sheet.paste(im.resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'test-results/dedicated-publish/20261107';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=90)
 print('PASS: four covers and eight original portrait illustrations; no small text in SVG')
if __name__=='__main__':main()
