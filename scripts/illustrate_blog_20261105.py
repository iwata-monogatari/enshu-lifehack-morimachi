"""November field notes: four individual landscapes and four illustrated procedures."""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from html import escape

import fitz
from PIL import Image, ImageDraw
from illustrate_blog_20261104_second import rect, path, put, circle, book, ledger, arrow, label

ROOT = Path(__file__).resolve().parents[1]
INK = '#263f3b'
CREAM = '#fff3d3'
TEAL = '#557e74'
GOLD = '#dbad60'
ORANGE = '#e87036'


def ground(key):
    colors = {'hunt':('#d9e8e2','#96b4a6','#4f7465','#c8bc8e'),
              'tea':('#fff1cb','#bdc29b','#809676','#e7d59e'),
              'land':('#e5ece8','#b8c6af','#829981','#eadbb7'),
              'water':('#dcefee','#b1c7b2','#829e89','#dfcf99')}
    sky,far,near,field = colors[key]
    return (rect(-5,-5,1010,570,sky) + circle(849,85,38,'#f3d397') +
            path('M-5 254 Q77 201 153 151 T309 155 Q371 194 444 144 T581 114 Q642 119 711 169 T853 153 Q938 85 1010 132 V565 H-5Z',far,'none') +
            path('M-5 259 Q102 204 192 220 T350 209 Q466 140 566 205 T762 200 Q885 149 1010 207 V570 H-5Z',near,'none') +
            path('M-5 291 Q184 236 332 272 T622 266 Q830 226 1010 251 V570 H-5Z',field,'none'))


def pine(x,y,s):
    shape=path('M-4 0 V-63 H4 V0Z','#705e48')+path('M0 -116 L-24 -74 L-14 -77 L-37 -43 L-22 -45 L-46 -12 Q0 -2 45 -18 L23 -47 L34 -46 L14 -79 L22 -78Z','#476a5b')+path('M0 -93 V-22 M0 -56 L16 -44 M0 -43 L-17 -32',stroke='#8eaa89',width=2)
    return put(shape,x,y,s)


def walker(x,y,s,coat=ORANGE,load=False):
    shape=path('M-13 -54 L-24 -29 L-11 -24 L-4 -42 M10 -53 L23 -37 L34 -46',stroke=INK,width=9)
    shape+=path('M-12 -18 L-17 5 L-27 26 M7 -18 L10 6 L27 17',stroke=INK,width=12)
    shape+=path('M-27 25 L-34 26 M24 17 L30 15',stroke='#5e4938',width=10)
    shape+=path('M-13 -61 Q-1 -69 11 -59 L18 -23 L-17 -19Z',coat)+path('M-12 -47 L14 -50',stroke=CREAM,width=4)
    shape+=circle(0,-76,13,'#ddb797')+path('M-15 -79 Q-15 -98 1 -96 Q15 -97 17 -82 L23 -78Z',coat)
    if load:
        shape+=put(sheaf(),5,-57,.8)
    return put(shape,x,y,s)


def sheaf():
    s=''
    for i in range(11):
        x= -65+i*3
        y= -35+i*5
        s+=path(f'M{x} {y} Q-12 -4 63 19',stroke='#ad7634',width=3)
        s+=path(f'M{x-10} {y-6} Q{x-6} {y-15} {x+9} {y+5} Q{x-3} {y+4} {x-10} {y-6}Z','#e3bf75',stroke='#926e37',width=1)
    return s+path('M3 -9 L-4 10 M10 -8 L3 12',stroke=INK,width=3)


def grass(x,y,s):
    forms=''
    for px,py in [(-29,-67),(-13,-82),(2,-61),(19,-81),(34,-62)]:
        forms+=path(f'M0 0 Q{px//3} {py//2} {px} {py}',stroke='#8e6a38',width=2.5)
        forms+=path(f'M{px} {py} q-7 -3 -8 -15 q15 2 12 17Z',GOLD,'#99763d',1)
    return put(forms,x,y,s)


def hut(x,y,s):
    return put(rect(-34,-39,69,39,'#dfbc8c')+path('M-46 -39 L-5 -69 L46 -40Z','#876d58')+rect(-9,-25,17,25,'#685847'),x,y,s)


def farm_map():
    s=path('M-79 -49 L-25 -67 L21 -48 L72 -66 L82 51 L25 65 L-23 45 L-74 63Z',CREAM)
    s+=path('M-27 -63 L-22 42 M20 -46 L26 61',stroke='#a8ac87',width=2)+path('M-63 30 Q-20 1 1 20 T68 2',stroke='#78aaba',width=7)
    s+=path('M-48 -22 L-23 -31 L10 -17 L-10 7 L-46 1Z','#cea865')+path('M-22 -30 L-25 3',width=2)
    return s


def tea_bag():
    return (path('M-38 -58 L38 -58 L42 53 Q0 64 -42 53Z','#668b74')+
            path('M-37 -46 H37 M-39 46 H39',stroke=CREAM,width=3)+
            rect(-23,-27,46,55,CREAM,3)+path('M-12 9 Q-15 -13 15 -15 Q18 7 -12 9Z','#679368')+
            path('M-12 9 L12 -12',width=2))


def paper():
    return rect(-53,-62,106,124,CREAM,4)+path('M-36 -40 H33 M-36 -22 H29 M-36 -2 H15 M-36 19 H27 M-36 37 H6',width=3)


def phone():
    return rect(-28,-51,56,102,INK,8)+rect(-21,-40,42,74,'#b9d2ba',3)+circle(0,42,3,CREAM)+path('M-12 -16 Q-9 5 11 13 L15 5 L7 0 L2 5 Q-5 0 -5 -8 L-1 -12 L-7 -21Z',TEAL)


def person_on_ditch():
    return walker(604,341,1.37,TEAL)+path('M651 277 L607 383',stroke='#795c3a',width=7)+path('M598 373 L617 382 Q613 409 591 403 Q582 393 598 373Z','#7b9086')


def art(key,mode):
    s=ground(key)
    if mode=='fig2':
        s+=path('M-15 366 Q228 306 467 351 T1015 329 V575 H-15Z','#c7ad7e','none')+path('M-10 398 Q221 349 455 389 T1006 364',stroke='#f4dfb2',width=5)
        if key=='hunt':
            coat=path('M-19 -54 L-47 -42 L-71 6 L-51 16 L-31 -12 L-32 52 H32 L30 -13 L51 15 L69 3 L47 -43 L18 -54 Q0 -34 -19 -54Z',ORANGE)+path('M0 -39 V49 M-32 -4 H31',stroke=CREAM,width=5)
            bell=path('M-39 17 Q-25 4 -24 -20 Q-22 -45 0 -45 Q22 -45 24 -20 Q25 4 39 17Z',GOLD)+circle(0,23,9,'#91643d')+path('M-10 -45 Q-13 -67 0 -69 Q14 -65 10 -46 M44 -29 Q53 -15 47 -4 M56 -35 Q69 -15 59 1',width=4)
            sign=path('M0 53 V-24',stroke='#85674a',width=9)+path('M-48 -56 H41 L53 -42 L39 -26 H-48Z',ORANGE)+path('M-28 -41 H28',stroke=CREAM,width=6)+path('M33 14 Q73 -12 90 10 Q106 38 47 39 M58 29 L45 39 L59 47',stroke='#aa5539',width=5)
            icons=[coat,bell,sign];names=['上着','鈴','標識']
        elif key=='land':
            cal=rect(-52,-49,104,99,CREAM,5)+rect(-52,-49,104,24,'#c66547')+path('M-33 -57 V-39 M30 -57 V-39 M-31 -11 H29 M-31 7 H29 M-31 24 H29 M-10 -16 V35 M10 -16 V35',width=3)+circle(20,16,10,'none')
            icons=[ledger(),farm_map(),cal];names=['二筆を合計','区域を照合','契約日']
        elif key=='tea':
            listing=paper()+path('M-43 -34 l5 5 9 -12 M-43 -13 l5 5 9 -12 M-43 9 l5 5 9 -12',stroke=TEAL,width=3)
            icons=[tea_bag(),book(),listing];names=['茶袋','原料産地','認定地域']
        else:
            letter=rect(-66,-39,132,78,CREAM,3)+path('M-62 -36 L0 7 L62 -36 M-62 35 L-19 -5 M62 35 L20 -5',width=3)+rect(42,-31,15,18,'#b8795b')
            icons=[farm_map(),letter,phone()];names=['田の位置','作業案内','連絡先']
        for i,(icon,name) in enumerate(zip(icons,names)):
            x=186+i*315
            s+=put(icon,x,315,1.55)+label(x,479,name,27)
            if i<2: s+=arrow(x+153,316)
        return s
    if key=='hunt':
        s+=path('M430 243 Q688 250 563 300 Q409 352 631 366 Q876 402 740 561 H340 Q675 404 457 390 Q195 348 459 291 Q562 268 430 243Z','#dbc498','#a39470',3)
        for x,y,z in [(38,346,1.25),(130,314,.9),(205,272,.68),(282,278,.63),(333,279,.57),(897,335,1.04),(972,355,1.49)]:s+=pine(x,y,z)
        if mode=='cover':
            s+=walker(402,397,2.12)+pine(5,568,2.63)+pine(968,492,1.7)
        else:
            s+=walker(331,395,1.55)+walker(405,374,1.17,'#d29438')+path('M698 384 V300',stroke='#745a43',width=11)+path('M641 269 H746 L759 285 L744 300 H641Z',ORANGE)+path('M665 284 H731',stroke=CREAM,width=5)
    elif key=='land':
        s+=hut(562,253,.78)+hut(614,257,.68)
        for x in [15,504]:
            s+=path(f'M{x+15} 408 l144 -125 252 12 54 118 -145 62Z','#bac18b','#b09a69',3)
            s+=path(f'M{x+62} 400 l111 -89 158 12 -80 117Z','#d7a15f',width=4)
            s+=path(f'M{x+112} 382 l94 -64 M{x+147} 392 l98 -67 M{x+183} 405 l101 -74',stroke='#edc593',width=2)
            s+=label(x+212,383,'6,000 m²',29)
        s+=path('M490 249 Q453 325 499 388 Q522 432 476 558',stroke='#7f97a2',width=15)
        if mode=='fig1':s+=label(229,510,'区域内',30)+label(751,510,'区域外',30)
        else:s+=put(farm_map(),837,460,.98)+put(ledger(),168,477,.86)
    elif key=='water':
        s+=path('M509 244 L543 246 L377 560 H129Z','#93bec1','#658e92',5)+path('M453 245 L474 248 L78 560 H-12Z','#b79975','#a58a64',3)
        s+=path('M557 248 L1010 308 V570 H415Z','#b4b37d','#8f986e',3)
        for a in range(8):s+=path(f'M{573+15*a} {260+3*a} L{445+a*88} 555',stroke='#d6cb9a',width=6)
        s+=hut(678,255,1.03)+hut(749,251,.7)
        s+=path('M245 411 L423 424 L409 439 L229 426Z','#a67f55')+path('M278 407 L400 418',stroke='#e3c498',width=4)
        if mode=='cover':s+=hut(837,255,.82)+put(farm_map(),784,429,1.47)+walker(297,369,1.14,ORANGE)+put(phone(),656,452,.99)
        else:s+=walker(187,421,1.85,'#d39453')+person_on_ditch()+path('M572 400 q24 -26 45 -4 q16 -4 23 10Z','#8a7459')
    else:
        s+=path('M0 305 Q180 275 420 311 L548 560 H0Z','#beaa6e','none')+path('M477 277 Q738 234 1010 260 V565 H525Z','#a3ae77','none')
        for i in range(6):s+=path(f'M{479+i*43} {287+i*14} Q{690+i*28} {247+i*30} 1020 {267+i*45}',stroke='#5e8758',width=14+i*3)
        for x,y,z in [(56,380,1.4),(121,354,1.0),(210,344,.82),(308,361,1),(32,503,1.6),(155,493,1.5),(325,486,1.17)]:s+=grass(x,y,z)
        if mode=='cover':s+=walker(481,394,1.72,TEAL,True)+put(sheaf(),772,454,1.35)
        else:s+=walker(267,394,1.33,'#866851')+path('M309 333 Q338 347 345 325 Q352 358 316 350',fill='#abb7a8',width=3)+walker(532,412,1.54,TEAL,True)+put(sheaf(),724,458,1.02)
    return s


def render(svg):
    with fitz.open(stream=svg.encode(),filetype='svg') as doc, fitz.open('pdf',doc.convert_to_pdf()) as pdf:
        pix=pdf[0].get_pixmap(alpha=False)
        return Image.frombytes('RGB',(pix.width,pix.height),pix.samples)


def main():
    out=ROOT/'test-results/dedicated-publish'
    out.mkdir(parents=True,exist_ok=True)
    sheet=Image.new('RGB',(1200,4*253),'#faf8ef')
    draw=ImageDraw.Draw(sheet)
    evidence=[]
    for row,key in enumerate(('hunt','land','water','tea')):
        post=json.loads((ROOT/f'data/blog-20261105-{key}.json').read_text(encoding='utf8'))
        folder=ROOT/'blog'/post['slug']
        folder.mkdir(exist_ok=True)
        for col,mode in enumerate(('cover','fig1','fig2')):
            alt=post['method' if mode=='fig2' else 'scene']
            svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" data-illustration="mori-editorial" role="img"><title>{escape(alt)}</title>'+art(key,mode)+'</svg>')
            img=render(svg)
            if mode=='cover':
                target=folder/'cover.jpg'
                img.save(target,quality=91,optimize=True)
            else:
                target=folder/f'{mode}.svg'
                target.write_text(svg,encoding='utf8')
                root=ET.parse(target).getroot()
                assert root.get('data-illustration')=='mori-editorial' and root.get('viewBox')=='0 0 1000 560'
            sheet.paste(img.resize((390,218),Image.Resampling.LANCZOS),(col*400+5,row*253+8))
            draw.text((col*400+10,row*253+231),f'{key.upper()}    /    {mode.upper()}',fill=INK)
            data=target.read_bytes()
            evidence.append(dict(path=target.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),size=img.size,xml_checked=mode!='cover'))
    assert len({x['sha256'] for x in evidence})==12
    sheet.save(out/'images.jpg',quality=90,optimize=True)
    (out/'images.json').write_text(json.dumps({'articles':4,'assets':evidence},ensure_ascii=False,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    main()
