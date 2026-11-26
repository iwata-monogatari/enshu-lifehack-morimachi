"""Article-specific, text-free editorial vectors; vertical mobile figures. Set-19 batch.
Scenes: a new community building in a park with three generations; a persimmon tree
and a gift box of Jiro persimmons; a town plan document with a rising chart and
residents; a corn stall with cobs and a map of stands."""
import io,json
from pathlib import Path
import fitz
from PIL import Image
from illustrate_blog_20261107 import rect,path,put,circle,person,tree,line,house,note,landscape,generator,mapshape,camera
ROOT=Path(__file__).resolve().parents[1]
INK='#243f3c';TEAL='#548e87';RED='#b55845';PAPER='#fff4db';GOLD='#dfb66d';PINK='#e5a9a0';ORANGE='#e07b2a';GREEN='#6a9a5b'
def arrow(x,y,s=1):return put(line('M-30 0 H28 M12 -17 L30 0 L12 17',TEAL,7),x,y,s)
def checkbadge(x,y,s=1):
 g=circle(0,0,30,TEAL)+line('M-14 0 L-4 11 L16 -12',PAPER,7)
 return put(g,x,y,s)
def building(x,y,s=1):
 g=rect(-120,-70,240,150,PAPER,6)+path('M-140 -70 L0 -130 L140 -70Z',TEAL,'none')+rect(-30,10,60,70,INK)+rect(-95,-35,44,44,GOLD)+rect(51,-35,44,44,GOLD)+line('M-120 80 H120',INK,6)
 return put(g,x,y,s)
def persimmon(x,y,s=1):
 g=circle(0,6,44,ORANGE)+rect(-16,-46,32,14,'#816b57',5)+line('M0 -32 V-52',GREEN,6)+path('M0 -52 Q26 -66 40 -52 Q26 -40 0 -52Z',GREEN,'none')
 return put(g,x,y,s)
def giftbox(x,y,s=1):
 g=rect(-95,-55,190,110,PAPER,6)+rect(-95,-55,190,26,RED,6)+line('M0 -55 V55',RED,7)
 return put(g,x,y,s)
def chart(x,y,s=1):
 g=rect(-95,-80,190,160,PAPER,6)+line('M-65 55 H70 M-65 55 V-55',INK,5)+path('M-58 30 L-18 -2 L18 12 L62 -38',RED,'none')+circle(62,-38,9,RED)+circle(-18,-2,7,TEAL)+circle(18,12,7,TEAL)
 return put(g,x,y,s)
def corn(x,y,s=1):
 g=path('M0 -78 C30 -40 30 40 0 82 C-30 40 -30 -40 0 -78Z','#f2c230','none')+line('M-16 -52 V52 M16 -52 V52 M-26 -20 H26 M-24 18 H24','#d9a41f',4)+path('M-6 30 Q-52 66 -58 110 Q-20 92 -4 58Z',GREEN,'none')+path('M6 30 Q52 66 58 110 Q20 92 4 58Z',GREEN,'none')
 return put(g,x,y,s)
def stall(x,y,s=1):
 g=rect(-105,-10,210,90,PAPER,5)+path('M-125 -10 L0 -70 L125 -10Z',RED,'none')+line('M-80 -10 V80 M80 -10 V80',INK,6)+line('M-105 80 H105',INK,6)
 return put(g,x,y,s)

def scene(key,method=False):
 sh=landscape()+path('M-5 452 Q370 357 1005 417 V565 H-5Z','#b7a987','none')
 if key=='tasedai-koryu':
  sh+=building(590,300,1.25)+put(tree(),880,330,.9)+put(person(TEAL),170,414,1.7)+put(person(PINK),285,414,1.5)+put(person(GOLD),385,430,1.1)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+building(650,262,.8)+checkbadge(830,232,.9)
 elif key=='jirogaki-kenjo':
  sh+=put(tree(),600,300,1.6)+persimmon(520,215,.8)+persimmon(660,180,.7)+persimmon(610,300,.75)+giftbox(830,330,.95)+put(person(TEAL),190,414,1.7)+house(110,318,.55)
  if method:sh+=persimmon(282,240,.95)+arrow(442,246,.55)+giftbox(650,252,.95)+checkbadge(830,232,.9)
 elif key=='sogokeikaku-10':
  sh+=note(580,280,1.5)+chart(830,215,.75)+put(person(TEAL),170,414,1.7)+put(person(PINK),285,414,1.5)+put(person(INK),390,414,1.6)
  if method:sh+=note(282,240,.8)+arrow(442,246,.55)+chart(650,252,.85)+checkbadge(830,232,.9)
 else:
  sh+=stall(590,320,1.25)+corn(520,215,.8)+corn(660,225,.7)+mapshape(845,215,.75)+put(person(TEAL),190,414,1.7)+put(tree(),90,340,.8)
  if method:sh+=mapshape(282,240,.8)+arrow(442,246,.55)+corn(650,246,.85)+checkbadge(830,232,.9)
 return sh
def svg(key,method=False,portrait=True):
 title={'tasedai-koryu':'公園の中の新しい交流施設と三世代','jirogaki-kenjo':'次郎柿の木と献上の箱','sogokeikaku-10':'総合計画の冊子と住民','corn-map':'とうもろこし直売所とマップ'}[key]
 sh=scene(key,method)
 if portrait:
  lower={'tasedai-koryu':note(176,652,.85)+arrow(300,650,.7)+building(438,665,.75),'jirogaki-kenjo':persimmon(176,652,.85)+arrow(300,650,.7)+giftbox(438,652,.85),'sogokeikaku-10':note(176,652,.85)+arrow(300,650,.7)+chart(438,652,.8),'corn-map':mapshape(176,652,.85)+arrow(300,650,.7)+corn(438,646,.8)}[key]
  sh=rect(0,0,600,800,'#f7eedb')+f'<g transform="translate(0,90) scale(.6)">{sh}</g>'+line('M300 455 V515 M280 495 L300 518 L320 495',TEAL,7)+lower+house(536,729,.5)+put(tree(),62,718,.9)
  box='0 0 600 800';wh='width="600" height="800"'
 else:box='0 0 1000 560';wh='width="1000" height="560"'
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" {wh} data-illustration="mori-editorial" role="img" aria-labelledby="t"><title id="t">{title}</title>{sh}</svg>'
def raster(raw):
 doc=fitz.open(stream=raw.encode(),filetype='svg');return Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')))
def main():
 posts=json.loads((ROOT/'data/blog-batch-20261126-set19.json').read_text(encoding='utf8'));sheet=Image.new('RGB',(900,1600),'white')
 for i,p in enumerate(posts):
  d=ROOT/'blog'/p['slug'];d.mkdir(parents=True,exist_ok=True)
  cover_svg=svg(p['key'],portrait=False);(d/'cover.svg').write_text(cover_svg,encoding='utf8')
  cover=raster(cover_svg);cover.save(d/'cover.jpg',quality=88,optimize=True)
  for n in (1,2):
   raw=svg(p['key'],n==2);(d/f'fig{n}.svg').write_text(raw,encoding='utf8');sheet.paste(raster(raw).resize((300,400)),((n-1)*300,i*400))
  sheet.paste(cover.resize((300,168)),(600,i*400+116))
 out=ROOT/'work-records/browser-proof/20261126-set19';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'illustrations-contact.jpg',quality=92)
 print('PASS: four unique covers and eight portrait figures; visible small text absent')
if __name__=='__main__':main()
