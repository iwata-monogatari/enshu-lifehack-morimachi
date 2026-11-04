"""Article-specific line drawings, rendered as JPEG covers and accessible SVG figures."""
from pathlib import Path
from html import escape

import fitz

INK = '#263f3b'
GOLD = '#d49247'
PAPER = '#fff6dc'
TEAL = '#548884'
RED = '#ae493d'

def path(d, fill='none', stroke=INK, width=4):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'

def put(shape, x, y, scale=1):
    return f'<g transform="translate({x} {y}) scale({scale})">{shape}</g>'

def rect(x,y,w,h,fill,rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="4"/>'

def circle(x,y,r,fill):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="4"/>'

def label(x,y,value,size=28):
    return f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" font-weight="700" fill="{INK}" text-anchor="middle">{escape(value)}</text>'

def tree():
    return path('M0 2 L8 -55 M5 -21 Q-20 -14 -21 -40 Q-1 -43 5 -21 M6 -34 Q27 -28 28 -58 Q12 -56 6 -34 M8 -49 Q-3 -52 3 -75 Q17 -63 8 -49',TEAL)

def person(coat=RED):
    return circle(0,-42,9,PAPER)+path('M-11 -24 Q-3 -34 8 -25 L15 2 L-16 2 Z',coat)+path('M-8 2 L-10 21 M7 2 L12 21')

def roof():
    return path('M-68 -51 L-42 -88 Q-4 -81 43 -87 L70 -50 Q6 -42 -68 -51Z',INK)+path('M-61 -54 Q0 -47 62 -54',stroke=GOLD,width=3)

def hall():
    return rect(-51,-51,102,53,'#d7ac74')+roof()+rect(-18,-46,36,47,'#684b39')+path('M-61 3 H62 M-42 -44 V0 M42 -44 V0',stroke=INK)

def lantern():
    return path('M-26 0 H26 L20 -7 L10 -11 V-35 H-10 V-11 L-21 -7Z','#acafa2')+rect(-18,-62,36,25,GOLD)+path('M-29 -62 Q-20 -69 0 -79 Q15 -70 28 -62 Z','#748078')+circle(0,-82,4,GOLD)+path('M-10 -58 V-42 M0 -58 V-42 M10 -58 V-42',width=2)

def shelter():
    return roof()+path('M-54 -48 V7 M54 -48 V7 M-65 9 H65',width=8)+put(lantern(),0,4,.58)

def torii():
    return path('M-59 -66 Q-1 -59 58 -66 M-47 -46 H47 M-34 -63 L-38 0 M34 -63 L38 0',stroke=RED,width=11)

def book():
    return path('M-56 -33 Q-25 -42 0 -25 Q28 -42 55 -33 V30 Q26 21 0 37 Q-24 22 -56 30 Z',PAPER)+path('M0 -25 V36 M-47 -18 Q-25 -23 -9 -14 M9 -14 Q28 -23 47 -18 M-47 -3 Q-24 -11 -9 -1 M9 -1 Q27 -13 47 -4',width=3)

def car():
    return path('M-57 -9 L-49 -26 L-24 -30 L-10 -46 L18 -46 L34 -29 L51 -24 L57 -7 V4 H-57 Z',TEAL)+path('M-15 -30 L-7 -40 H15 L25 -30 Z',PAPER)+circle(-34,2,10,INK)+circle(33,2,10,INK)

def inn():
    return hall()+path('M-26 -42 H25 V-23 L12 -20 L0 -23 L-12 -20 L-26 -23 Z',TEAL)+path('M-12 -40 V-21 M0 -40 V-22 M12 -40 V-21',stroke=PAPER,width=2)+path('M57 -32 H79 M75 -32 V-27',width=3)+rect(67,-27,17,21,GOLD,4)

def ledger():
    return rect(-55,-45,110,87,PAPER,3)+path('M-52 -29 H53 M-15 -28 V40 M18 -28 V40 M-52 -8 H53 M-52 10 H53 M-52 26 H53',width=2)+path('M22 2 l6 5 13 -15',stroke=RED)

def arrow(x,y):
    return put(path('M-31 0 H27 M15 -12 L29 0 L15 12',stroke=RED,width=5),x,y)

def river():
    return path('M-30 457 Q180 410 330 464 T620 454 T1030 458 L1030 585 H-30Z','#a2c9c0',stroke='none')+path('M0 475 Q170 432 321 482 T625 475 T1010 477',stroke=PAPER,width=3)

def illustration(key,mode,alt):
    method = mode == 'fig2'
    skies={'ekijin':'#edd4b4','lamp':'#e5eed8','inn':'#fae7c6','parking':'#dae9e5'}
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" data-illustration="mori-editorial" role="img"><title>{escape(alt)}</title>'
    svg+=rect(-5,-5,1010,570,skies[key])+circle(815,105,43,'#f1bc76')
    svg+=path('M-20 275 Q96 252 189 155 Q245 102 321 190 Q395 248 481 188 Q579 95 653 163 Q758 253 845 175 Q923 104 1020 191 V570 H-20Z','#b6c9ad','none')+path('M-10 305 Q132 228 253 289 T497 274 T745 268 T1010 273 V570 H-10Z','#8ba894','none')+path('M-10 336 Q261 274 530 324 T1010 308 V570 H-10Z','#f3e3bb','none')
    for x,y,s in [(60,322,.9),(96,324,.65),(701,295,.6),(950,327,1.1)]:
        svg+=put(tree(),x,y,s)
    if method:
        svg+=river()+path('M62 373 Q224 334 399 366 T652 374 T956 360',stroke='#c2a379',width=26)
        steps={'ekijin':[(book(),'11/19'),(rect(-49,-36,98,72,PAPER)+label(0,5,'70',31),'社報'),(put(hall(),0,26,.85),'家族の暦')],
               'lamp':[(shelter(),'覆う堂'),(lantern(),'内側の灯籠'),(rect(-52,-32,104,64,PAPER)+label(0,11,'1813',27),'年号の所在')],
               'inn':[(ledger(),'内訳を足す'),(rect(-55,-35,110,70,PAPER)+label(0,8,'24 / 358',22),'分母で割る'),(book(),'別章と照合')],
               'parking':[(car(),'駐車区画'),(torii(),'門前'),(car(),'車へ戻る')]}[key]
        for i,(sym,cap) in enumerate(steps):
            x=190+i*310
            svg+=put(sym,x,340,1.45)+label(x,424,cap,26)
            if i<2:svg+=arrow(x+154,314)
    else:
        svg+=path('M-20 550 Q215 365 470 351 T1030 340',stroke='#c3a57a',width=44)
        if key=='ekijin':
            svg+=put(hall(),590,318,2.1)+put(torii(),340,362,1.55)+put(tree(),516,360,1.4)+put(person(),650,385,1.2)+put(person(TEAL),711,389,1)+rect(670,352,12,26,PAPER)+rect(91,372,132,96,PAPER,6)+label(157,406,'11月',22)+label(157,452,'19',40)
        elif key=='lamp':
            svg+=river()+put(shelter(),283,369,2.17)+put(lantern(),711,373,1.85)+label(283,422,'大門・堂入')+label(711,422,'北戸綿・灯籠')
        elif key=='inn':
            for x,y,s in [(210,323,1.1),(375,330,1.35),(602,352,1.7)]:svg+=put(inn(),x,y,s)
            svg+=put(person(),427,385,1.23)+put(person(TEAL),490,396,1.35)+put(ledger(),800,426,1.54)
        else:
            svg+=put(torii(),725,315,1.6)+put(car(),211,394,1.6)+put(person(),426,383,1.3)+put(person(TEAL),470,389,1.18)+path('M482 382 L493 408',width=4)+path('M516 377 Q567 355 648 350',stroke=RED,width=4)+label(570,417,'門前まで',24)
        if mode=='cover':
            svg+=path('M0 498 Q235 490 481 506 T1000 490 V560 H0Z',INK,'none')+label(502,95,{'ekijin':'十一月の祈り','lamp':'街道の灯り','inn':'文政十三年の宿場','parking':'親と歩く参道'}[key],38)
    return svg+'</svg>'

def draw(p,folder:Path):
    for mode,name in [('fig1','scene'),('fig2','method'),('cover','scene')]:
        svg=illustration(p['key'],mode,p[name])
        if mode=='cover':
            with fitz.open(stream=svg.encode(),filetype='svg') as source,fitz.open('pdf',source.convert_to_pdf()) as doc:
                doc[0].get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(str(folder/'cover.jpg'),jpg_quality=90)
        else:
            (folder/(mode+'.svg')).write_text(svg,encoding='utf8')
