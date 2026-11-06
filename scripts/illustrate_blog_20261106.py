"""Native editorial SVG scenes for the four Friday transport features."""
import json,io
from pathlib import Path
from html import escape
import fitz
from PIL import Image,ImageDraw,ImageFont
from illustrate_blog_20261104_second import rect,path,put,circle,person,tree
ROOT=Path(__file__).resolve().parents[1]
INK='#263f3b';PAPER='#fff5db';TEAL='#548884';GOLD='#dbad60';RED='#ae493d'
def line(d,c=INK,w=4):return path(d,stroke=c,width=w)
def background(key):
 sky={'ticket':'#d7e9e6','wheel':'#e2e9ed','schoolroute':'#f3e5cc','cycle':'#e5e8cc'}[key]
 return rect(-5,-5,1010,570,sky)+circle(856,87,36,'#edcc8a')+path('M-5 250 Q85 205 171 120 Q250 185 302 158 Q420 81 491 193 Q589 116 651 168 Q730 95 813 179 Q910 98 1010 161 V565 H-5Z','#92b0a0','none')+path('M-5 284 Q122 204 219 232 T401 217 Q493 183 568 222 T780 217 Q885 199 1010 243 V570 H-5Z','#5c8474','none')+path('M-5 320 Q174 267 380 302 T709 289 Q869 263 1010 281 V570 H-5Z','#d3c593','none')+line('M-5 354 Q171 296 354 342 M-5 377 Q179 319 344 365 M-5 400 Q166 351 324 391','#7d9364',8)
def house(x,y,s=1):return put(rect(-35,-37,70,45,PAPER)+path('M-48 -38 L-3 -70 L49 -38Z','#876d58')+rect(-9,-20,18,28,TEAL)+rect(15,-22,12,12,GOLD),x,y,s)
def train(x,y,s=1):
 sh=rect(-112,-76,224,80,PAPER,12)+rect(-108,-26,216,17,TEAL)+rect(-91,-59,29,25,'#adc7c8',4)+rect(-49,-59,29,25,'#adc7c8',4)+rect(-7,-59,29,25,'#adc7c8',4)+rect(38,-64,34,66,'#dbcda5',3)+rect(44,-57,22,22,'#adc7c8')+rect(85,-59,18,25,'#adc7c8')+circle(-70,10,12,INK)+circle(70,10,12,INK)+line('M-125 27 H126','#685b4d',5)+line('M-125 36 H126','#a09276',4)
 return put(sh,x,y,s)
def station(x,y,s=1):return put(rect(-104,-95,207,105,'#d7b88d')+path('M-125 -95 L-76 -140 H65 L123 -95Z','#776b5c')+rect(-77,-56,44,66,INK)+rect(1,-63,65,45,'#d5e2da')+line('M33 -63 V-19 M2 -41 H64','#8a8c72',3)+rect(-24,-93,54,20,PAPER),x,y,s)
def mapshape():return path('M-69 -53 L-23 -68 L20 -52 L64 -68 L75 41 L25 58 L-20 43 L-64 59Z',PAPER)+line('M-23 -65 L-20 43 M21 -49 L25 55','#b6ba9b',2)+line('M-48 33 Q-24 -33 3 -2 T51 -34',TEAL,6)+circle(-46,29,6,RED)+circle(50,-34,6,RED)
def ticket(x,y,s=1,color=PAPER):return put(rect(-64,-37,128,74,color,7)+line('M18 -34 V33','#9c9a7e',2)+line('M-48 -17 H2 M-48 0 H2 M-48 17 H-10',TEAL,6)+circle(43,0,11,GOLD),x,y,s)
def phone(x,y,s=1):return put(rect(-26,-45,52,90,INK,8)+rect(-21,-37,42,66,'#c4ddd0',5)+circle(0,36,3,GOLD)+line('M-9 -16 Q0 -25 9 -16 M-12 -10 Q0 -21 12 -10',TEAL,3),x,y,s)
def bike(x,y,s=1,front=True):
 sh=circle(47,0,25,'none')+path('M-43 0 L-12 -47 L13 0 L-43 0 L-3 -26 L47 0 L30 -53 H45',stroke=INK,width=4)+line('M-22 -48 H-3 M26 -55 H39',RED,7)+circle(13,0,6,GOLD)
 if front:sh=circle(-43,0,25,'none')+sh
 return put(sh,x,y,s)
def wheelchair(x,y,s=1):
 sh=circle(0,0,30,'none')+circle(0,0,22,'none')+circle(0,-65,13,'#ddb797')+path('M-5 -46 L2 -17 H36 L47 8',stroke=INK,width=10)+path('M-7 -48 Q8 -54 18 -30 H-6Z',RED)+line('M-16 -38 V-9 H29 M46 9 H60',TEAL,6)+circle(47,10,7,INK)
 return put(sh,x,y,s)
def notebook(x,y,s=1):return put(rect(-87,-64,174,128,PAPER,6)+line('M-58 -44 H63 M-58 -18 H63 M-58 8 H30 M-58 34 H52','#a5b1a1',4)+line('M-74 -48 V48',RED,3)+path('M67 48 L100 -39 L108 -35 L76 51Z',GOLD),x,y,s)
def scene(key,method=False):
 sh=background(key)
 sh+=put(tree(),94,328,1.5)+put(tree(),919,297,1.3)+house(810,299,.9)+house(870,320,.65)
 if not method:
  sh+=path('M-5 463 Q410 377 1010 428 V570 H-5Z','#b6b7a1','none')+line('M-10 418 Q520 338 1010 389','#6f695a',7)+line('M-10 432 Q520 353 1010 404','#6f695a',5)
  sh+=station(315,343,.78)+train(650,369,.78)
  if key=='ticket':sh+=put(person(TEAL),204,449,2)+put(person(RED),323,459,1.8)+put(mapshape(),459,458,.8)+ticket(678,465,1.1)+ticket(821,493,.8,'#e3c680')
  elif key=='wheel':sh+=path('M361 515 L615 430 L615 456 L361 540Z',PAPER)+line('M355 478 L606 395 M358 480 V519 M441 453 V490 M521 425 V466 M605 396 V438',TEAL,6)+wheelchair(376,454,1.4)+put(person(TEAL),266,446,1.8)+put(mapshape(),791,490,.85)
  elif key=='schoolroute':
   sh=background(key)+house(169,290,1.3)+house(842,302,1)+path('M379 250 L534 250 L770 570 H128Z','#c1b9a2','none')+path('M-5 405 L1010 343 V403 L-5 477Z','#c1b9a2','none')
   for x,y in [(368,437),(408,434),(448,432),(488,430)]:sh+=path(f'M{x} {y} l19 0 l18 23 l-23 1Z',PAPER,'none')
   sh+=put(person(TEAL),220,404,1.8)+put(person(GOLD),349,327,1)+put(person(RED),390,337,.85)+notebook(779,470,1.0)+put(tree(),95,380,1.5)
  else:sh+=bike(510,461,1.65,False)+put(person(TEAL),313,459,1.9)+circle(369,495,40,'none')+path('M511 348 Q552 334 582 373 L610 427 L487 425Z','#a5b8a3')+phone(812,477,1.1)
 else:
  sh+=path('M-5 369 Q440 305 1010 370 V570 H-5Z','#b8a07d','none')+path('M121 388 L788 350 L910 526 L195 560Z','#ead7ae')+put(person(TEAL),95,468,2.3)+put(person(RED),916,468,2.1)
  if key=='ticket':sh+=put(mapshape(),475,439,1.35)+ticket(265,445,.95)+ticket(742,431,.95,'#e3c680')+line('M340 468 Q390 508 436 500 M566 398 Q620 373 653 400',TEAL,5)
  elif key=='wheel':sh+=notebook(319,452,1.0)+phone(713,419,1.2)+wheelchair(507,472,1.1)+line('M406 402 Q470 378 528 407 M574 472 Q627 497 683 462',TEAL,5)
  elif key=='schoolroute':sh+=notebook(337,438,1.2)+phone(704,433,1.3)+path('M477 370 L558 356 L568 484 L486 498Z','#ccd4b3')+line('M494 394 L546 384 M498 421 L548 412',TEAL,5)+line('M426 488 Q515 534 652 472',TEAL,5)
  else:sh+=bike(328,432,.9,False)+circle(222,476,27,'none')+phone(512,448,1)+circle(736,432,47,PAPER)+line('M736 398 V432 L761 432',TEAL,6)+line('M589 476 Q640 503 675 471',TEAL,5)
 return sh
def svg(key,method):
 title={'ticket':'区間を選ぶ乗車券','wheel':'往復のホームと介助','schoolroute':'守る道と相談の記録','cycle':'輪行と返却の段取り'}[key]
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" data-illustration="mori-editorial" role="img" aria-labelledby="title"><title id="title">{escape(title)}</title>{scene(key,method)}</svg>'
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261106.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(1000,1120),'white')
 for i,p in enumerate(posts):
  folder=ROOT/'blog'/p['slug'];folder.mkdir(exist_ok=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(folder/f'fig{n}.svg').write_text(raw,encoding='utf8')
   doc=fitz.open(stream=raw.encode(),filetype='svg');png=doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png');im=Image.open(io.BytesIO(png))
   if n==1:im.save(folder/'cover.jpg',quality=88,optimize=True)
   thumb=im.resize((500,280));sheet.paste(thumb,((n-1)*500,i*280))
 out=ROOT/'test-results/dedicated-publish';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=88)
 print('4 covers / 8 article-specific SVG figures written')
if __name__=='__main__':main()
