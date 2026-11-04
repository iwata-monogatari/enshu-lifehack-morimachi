"""Draw original landscape and research illustrations for the November 4 culture series."""
from pathlib import Path
from html import escape
import fitz

def shrine():
    return '<path fill="#79503d" d="M22 101h128v78H22z"/><path fill="#344d51" d="M0 103Q40 86 73 51q30 35 100 43l-13 15H9z"/><path fill="#cfaa76" d="M37 119h34v60H37zm52 0h41v60H89z"/><path fill="#4c302b" d="M68 117h21v62H68z"/><path fill="#b77747" d="M8 175h150v7H8z"/>'

def bell():
    return '<path d="M64 51Q47 18 36 55m72-2q10-34 23-1" fill="none" stroke="#776244" stroke-width="9"/><ellipse cx="85" cy="108" rx="68" ry="63" fill="#667469" stroke="#3f514c" stroke-width="6"/><ellipse cx="85" cy="106" rx="54" ry="50" fill="none" stroke="#b3aa83" stroke-width="4"/><ellipse cx="85" cy="105" rx="29" ry="27" fill="none" stroke="#c1b28c" stroke-width="3"/><circle cx="85" cy="105" r="11" fill="#b5a67c"/><path d="M31 143q53 28 109-1" fill="none" stroke="#263f3a" stroke-width="6"/><path d="M24 165q5 17 4 39" fill="none" stroke="#bb995e" stroke-width="9"/>'

def books():
    return ''.join(f'<g transform="translate({i*3},{-i*11})"><path fill="{["#526c70","#4c6a58","#89624f","#65768a"][i%4]}" d="M4 144l110-24 50 17-112 27z"/><path fill="#ead8b4" stroke="#725f4b" stroke-width="2" d="M52 164l112-27v7L52 172z"/><path fill="#594e47" d="M4 144l48 20v8L4 152z"/></g>' for i in range(8))

def fabric():
    return '<path fill="#694634" d="M5 57h151v10H5zm9 11h7v109h-7zm129 0h7v109h-7z"/>'+''.join(f'<path fill="{c}" d="M{x} 65h29v{h}l-15 -4-14 4z"/>' for x,h,c in [(25,76,"#bd815f"),(61,87,"#516777"),(98,69,"#6e856e")])+'<path stroke="#e6ca9f" stroke-width="3" d="M29 78l20 16m-20-2 20 16m16-24h20m-20 11h20m18 5h18"/>'

def school():
    return '<path fill="#ebdcb4" stroke="#826e5b" stroke-width="3" d="M9 92h156v86H9z"/><path fill="#454f59" d="M0 95l32-34h111l31 34z"/><path fill="#b16d54" d="M66 91l20-29 23 29z"/>'+''.join(f'<path fill="#70919b" stroke="#fcf0d7" stroke-width="3" d="M{x} {y}h13v18h-13z"/>' for x in [19,44,111,137] for y in [103,138])+'<path fill="#775b49" d="M73 135h26v42H73z"/><path d="M8 131h158M8 178h159" stroke="#9a8e78" stroke-width="5"/>'

def torii():
    return '<path fill="#935f46" d="M25 70h15l-4 108H23zm88 0h15l5 108h-13zM9 90h137v9H9z"/><path fill="#615143" d="M1 49q70 16 151 0l-4 13q-68 11-142 1z"/><path fill="#aa7457" d="M11 65h131v9H11z"/>'

def sheet(mode):
    box='<path fill="#fff5d8" stroke="#846f56" stroke-width="3" d="M3 30l145-6 9 143-145 6z"/>'
    if mode=='map':return box+'<path fill="#bdd3bc" d="M19 55l31-19 28 20 50-14 8 42-24 16-40-18-33 14z"/><path d="M24 154q40-18 49-54t55-45" fill="none" stroke="#77a5b1" stroke-width="9"/><ellipse cx="103" cy="110" rx="24" ry="16" fill="none" stroke="#b86548" stroke-dasharray="5 4" stroke-width="4"/>'
    if mode=='calendar':return box+'<path fill="#426260" d="M4 32l144-6 2 24-144 6z"/>'+''.join(f'<rect x="{x}" y="{y}" width="19" height="14" rx="2" fill="{("#bd6851" if (x,y)==(65,94) else "#b4b99f")}"/>' for x in (32,65,98) for y in (68,94,120))
    if mode=='photo':return box+'<path fill="#acb1a1" d="M16 45h119v103H16z"/><g transform="translate(20,34) scale(.61)">'+school()+'</g>'
    return box+''.join(f'<path d="M23 {y}l98-5" stroke="#9a9f8e" stroke-width="3"/>' for y in (60,78,96,114,132))+'<path d="M90 146l48-68 8 4-50 70-10 5z" fill="#725847"/>'

def place(symbol,x,y,scale):
    return f'<g transform="translate({x} {y}) scale({scale})">{symbol}</g>'

def scene(key,version,title):
    sky=['#f6dfb1','#d5e7dd','#dce8ec'][version]
    base=f'<svg xmlns="http://www.w3.org/2000/svg" data-illustration="mori-editorial" width="1000" height="560" viewBox="0 0 1000 560"><title>{escape(title)}</title><rect width="1000" height="560" fill="{sky}"/><circle cx="815" cy="85" r="39" fill="#fff2ca"/><path fill="#a0b9ae" d="M0 228l128-97 102 60 132-105 140 110 123-72 105 68 118-109 152 98v180H0z"/><path fill="#6d9181" d="M0 272q130-137 292-42t277-7 255-12 176-14v191H0z"/><path fill="#aabb8d" d="M0 317q219-59 479-2t521-34v279H0z"/>'
    if version==2:
        base+='<path fill="#ba8f65" d="M0 323l1000-38v275H0z"/><path d="M0 403l1000-42M0 501l1000-49" stroke="#aa815e" stroke-width="3"/>'
        symbols={'yama':[sheet('calendar'),shrine(),sheet('notes')],'waniguchi':[bell(),sheet('notes'),books()],'toyohei':[books(),sheet('notes'),sheet('map')],'school':[sheet('photo'),school(),sheet('map')]}[key]
        for i,s in enumerate(symbols):base+=place(s,65+i*314,165+(i%2)*18,1.42)
        base+='<path d="M310 410q30 19 65-1m-15-3 17 2-8 13m260-23q29 17 57-2m-14-2 17 1-8 14" stroke="#584c40" fill="none" stroke-width="5"/>'
    else:
        base+='<path fill="#91bcc4" d="M0 339q260 5 418 62t384 30q81-13 198-4v49q-147-20-271 12-180 40-353-45T0 368z"/>'
        trees=''.join(f'<path fill="#456856" d="M{x} {y}l-25 60h13l-20 32h62l-20-32h13z"/>' for x,y in ((75,192),(118,200),(193,189),(888,194),(944,211)))
        base+=trees
        if key=='yama':base+=place(torii(),68 if version else 140,250,1.5)+place(shrine(),550 if version else 432,157,1.9)
        if key=='waniguchi':base+=place(shrine(),470,210,1.4)+'<path fill="#674d3c" d="M50 132h420v27H50z"/><path d="M225 155v74" stroke="#7d7156" stroke-width="6"/>'+place(bell(),85,135,1.65)
        if key=='toyohei':base+=place(fabric(),35,160,1.85)+'<path fill="#a5805c" d="M430 414l352-65 154 87-374 80z"/>'+place(books(),495,209,1.65)
        if key=='school':base+=place(torii(),60,278,1.08)+place(school(),320 if version else 415,164,1.82)
        if version==0:base+='<path fill="#567761" d="M0 530q130-54 280 6t238 22H0zm740 30q160-74 260-43v43z"/>'
    return base+'</svg>'

def draw(p,folder):
    for n in (0,1,2):
        svg=scene(p['key'],n,p['method'] if n==2 else p['scene'])
        if n:
            (folder/f'fig{n}.svg').write_text(svg,encoding='utf8')
        else:
            with fitz.open(stream=svg.encode(),filetype='svg') as doc,fitz.open('pdf',doc.convert_to_pdf()) as pdf:
                pdf[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(str(folder/'cover.jpg'))
