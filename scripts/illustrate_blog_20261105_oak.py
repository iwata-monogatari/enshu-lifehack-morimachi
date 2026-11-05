"""Draw a distant oak, diagnostic details and a family observation map."""
from html import escape
import json
import math
from pathlib import Path
from random import Random

from illustrate_blog_20261105 import render, walker

ROOT = Path(__file__).resolve().parents[1]
INK = '#314339'


def path(d, fill, stroke='none', width=1):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'


def ellipse(x, y, rx, ry, fill):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}"/>'


def tree(x, y, radius, color, seed):
    rng = Random(seed)
    parts = [path(f'M{x-3} {y+radius+11} l2 -35 h3 l2 35Z', '#655644')]
    for step in range(9):
        angle = step * math.pi * 2 / 9
        cx = x + math.cos(angle) * radius * .48
        cy = y + math.sin(angle) * radius * .45
        parts.append(ellipse(round(cx), round(cy), radius*.57, radius*rng.uniform(.51,.66),color))
    parts.append(ellipse(x,y,radius*.7,radius*.67,color))
    return ''.join(parts)


def hillside(detail=False):
    s = path('M0 0H1000V560H0Z', '#f1e7cb')
    s += ellipse(780,93,50,50,'#edc583')
    s += path('M0 210Q115 105 205 147T370 165Q475 210 565 122T760 155Q872 181 1000 98V560H0Z','#b6c6ae')
    s += path('M0 278Q140 114 298 195T555 205Q704 112 785 164T1000 163V560H0Z','#77947b')
    rng = Random(17)
    for row in range(3):
        for j in range(31):
            x = j*36-15
            y = int(237+38*math.cos(x/96)+row*29+rng.randrange(-10,11))
            color = rng.choice(('#51775b','#47735b','#71906b','#69805a','#7b926b'))
            s += tree(x,y,rng.randrange(21,31),color,row*101+j)
    s += tree(482,207,33,'#9f5339',63)+tree(496,201,19,'#bb6f43',57)
    s += path('M0 336Q157 278 315 319T656 343Q846 267 1000 302V560H0Z','#617c5c')
    s += path('M0 357Q128 324 218 361T445 384Q622 347 804 389T1000 379V560H0Z','#9d9f72')
    s += path('M0 476Q162 394 362 414T708 428Q845 418 1000 436V560H0Z','#c2b493')
    s += path('M0 491Q177 414 363 431T717 445Q834 431 1000 448','none','#d5c5a6',8)
    for x,y in ((18,430),(77,411),(182,398),(806,410),(867,402),(908,392),(966,398)):
        s += path(f'M{x} {y}q4 -17 -4 -22q9 5 12 19q7 -20 13 -20q-3 15 -13 25Z','#70805e')
    s += walker(204 if detail else 314,442,1.32,'#486b64')
    if not detail:
        s += walker(391,446,1.13,'#b2784b')
    else:
        s += path('M706 62H963V482H706Q691 482 691 465V79Q691 62 706 62Z','#faf0d5','#566c58',3)
        s += path('M706 417Q831 397 950 419V463H706Z','#b9a17e')
        s += path('M786 82Q805 179 781 320Q773 397 735 437Q785 430 804 406Q824 427 858 434Q842 358 864 265T871 82Z','#8a694c')
        s += path('M809 90Q826 155 805 252T790 390M849 91Q858 174 836 256T820 393','none','#654b39',4)
        for i in range(38):
            y = rng.randrange(238,395)
            x = rng.randrange(794,836)
            s += ellipse(x,y,2.6,3.3,'#322c24')
        for i in range(118):
            x,y = rng.gauss(803,26),rng.gauss(423,8)
            s += ellipse(round(x),round(y),rng.randrange(2,5),1.7,'#e0bf83')
    return s


def mapdesk():
    s = path('M0 0H1000V560H0Z','#ae8260')
    for y in (64,226,390,534):
        s+=path(f'M0 {y}q285 -9 501 2t499 -1','none','#966d50',3)
    s += path('M31 56L643 38L671 467L59 496Z','#efe5c8','#705d47',3)
    s += path('M65 88L609 70L634 433L84 459Z','#d3d9ba')
    for i in range(8):
        s += path(f'M{67+i*44} 90q130 16 83 103t61 140q52 56 25 104','none','#a9b699',2)
    s += path('M68 356Q139 320 197 358T347 368Q411 335 450 346T625 294','none','#81a7aa',15)
    s += path('M81 405Q172 352 243 394T389 389Q485 332 623 353','none','#e8c994',11)
    s += path('M245 393L420 176M385 187L420 176L415 214','none','#a34c37',6)
    s += ellipse(245,393,13,13,'#294b4e')+ellipse(245,393,6,6,'#f8ecd1')
    s += '<ellipse cx="445" cy="146" rx="51" ry="28" fill="none" stroke="#9d523b" stroke-width="3" stroke-dasharray="8 5"/>'
    for x,y,angle,red,num in ((626,72,6,False,'08'),(630,267,-5,True,'11')):
        s += f'<g transform="translate({x} {y}) rotate({angle})">'
        s += path('M0 0H290V174H0Z','#faf0d9','#584c3b',2)+path('M10 11H279V128H10Z','#dce4d2')
        s += path('M10 90Q51 47 79 60T139 62Q177 33 210 49T279 53V128H10Z','#829b7a')
        s += path('M10 102Q63 62 114 83T188 71T279 80V128H10Z','#587558')
        s += tree(150,73,14,'#a65d3e' if red else '#64865c',9)
        s += f'<text x="18" y="160" font-size="23" fill="#43554b">{num}</text>'
        s += path('M57 151H108M138 151H240','none','#8e9a80',3)+'</g>'
    s += path('M417 494L560 330L572 340L427 503L403 514Z','#dcab58',INK,2)+path('M403 514L410 498L421 506Z',INK)
    return s


def main():
    post = json.loads((ROOT/'data/blog-20261105-oak.json').read_text(encoding='utf8'))
    folder = ROOT/'blog'/post['slug']
    folder.mkdir(exist_ok=True)
    for name, description, art in [('cover.jpg',post['cover_description'],hillside()),('fig1.svg',post['scene'],hillside(True)),('fig2.svg',post['method'],mapdesk())]:
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" data-illustration="mori-editorial" role="img"><title>'+escape(description)+'</title>'+art+'</svg>'
        if name.endswith('.jpg'):
            render(svg).save(folder/name,quality=90,optimize=True)
        else:
            (folder/name).write_text(svg,encoding='utf8')


if __name__=='__main__':
    main()
