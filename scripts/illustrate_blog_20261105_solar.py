"""Illustrate site area and end-of-operation checks for the Mori solar article."""
from illustrate_blog_20261105 import ROOT, ground, walker, render, pine
from illustrate_blog_20261104_second import path, rect, put, circle, arrow, label, ledger, car

FOLDER = ROOT / "blog/20261105-morimachi-solar-site"
def panel(x,y,scale):
    frame = path("M-80 2 V22 M54 2 V22", stroke="#394b51",width=7)
    frame += path("M-88 0 L-67 -52 H91 L68 0Z","#36647b","#283e46",5)
    frame += path("M-80 -21 H76 M-42 -51 L-61 0 M-1 -51 L-22 0 M40 -51 L18 0 M73 -51 L50 0",stroke="#acd3d4",width=2)
    return put(frame,x,y,scale)

def district():
    return ground("land")+put(pine(0,0,1),65,276,.65)+path("M0 428 Q224 369 427 401 T1000 405 L1000 466 Q722 438 499 449 T0 502Z","#d1ae7a","none")

def scene(mode):
    if mode=="cover":
        s=district()+panel(285,335,1.55)+panel(617,324,1.25)+panel(828,317,.88)+walker(904,401,.85)
        s+=path("M89 466 L683 391 L695 410 L99 491Z","#f0c467")
        for n in range(17):
            x=112+n*34;y=465-n*4.25;s+=path(f"M{x} {y} l3 10",width=2)
        return s+rect(58,446,83,57,"#ca713e",19)+circle(100,472,15,"#f0c467")
    if mode=="fig1":
        s=rect(-4,-4,1008,568,"#e2e3c6")
        s+=path("M-20 440 L310 218 L870 -30 L925 -28 L329 248 L-20 489Z","#cebda3")
        for x,y in [(190,105),(300,112),(720,350),(832,333),(600,385)]:s+=pine(x,y,.52)
        for x,y in [(80,201),(466,239)]:
            s+=put(path("M0 0 l205 -95 148 95 -220 113Z","#b3ca9a","#4d6b52",5),x,y)
            s+=panel(x+130,y+1,.55)+panel(x+211,y-26,.55)
        s+=path("M-5 540 Q202 412 325 421 T681 396 T1004 347",stroke="#549da3",width=15)
        return s
    s=rect(-5,-5,1010,570,"#f8f0d8")
    for x in (20,350,680):
        s+=put(path("M0 55 Q75 10 128 55 Q198 -4 296 56 V133 H0Z","#9eb6a1","none")+path("M0 135 Q142 97 296 135 V197 H0Z","#d5be8c","none"),x,180)
    s+=panel(156,300,1.15)+put(car(),511,302,.83)+path("M452 267 L496 189 L535 216 L554 191",stroke="#bf8242",width=13)+panel(605,305,.42)+put(walker(0,0,1),832,316,.7)
    for x in (302,636):s+=arrow(x,382)
    return s+put(ledger(),178,437,.64)+put(ledger(),839,437,.64)

if __name__=="__main__":
    FOLDER.mkdir(exist_ok=True)
    for mode,title in [("cover","敷地を測る巻尺と地上の太陽光設備"),("fig1","進入路と水路に面した二つの発電区画の概念図"),("fig2","稼働、搬出、返還を順に確認する場面")]:
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" data-illustration="mori-editorial" role="img"><title>{title}</title>{scene(mode)}</svg>'
        if mode=="cover":render(svg).save(FOLDER/"cover.jpg",quality=90)
        else:(FOLDER/(mode+".svg")).write_text(svg,encoding="utf8")

