#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ブログ記事の表紙(760x760)を、記事ごとの情景として描く。

make_cover_square.py は文字だけの表紙を作る保険用スクリプト。
本スクリプトは記事固有のモチーフ(畑・柵・獣・地図・杭など)を図形で描き、
下部に見出し帯を載せる。記事が増えたら SCENES に一つ関数を足す。

使い方: python scripts/make_cover_scene.py <slug>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "blog")
S = 760
BAND_TOP = 592

FONT_BOLD = "C:/Windows/Fonts/meiryob.ttc"
FONT_REGULAR = "C:/Windows/Fonts/meiryo.ttc"


def sky(d):
    for y in range(0, 300):
        t = y / 300
        d.line([(0, y), (S, y)], fill=(int(206 + 40 * t), int(228 + 20 * t), int(240 - 4 * t)))
    d.rectangle([0, 300, S, BAND_TOP], fill=(226, 236, 216))


def mountains(d, base=300):
    d.polygon([(0, base - 40), (90, base - 110), (180, base - 50), (270, base - 120),
               (370, base - 55), (470, base - 125), (570, base - 48), (660, base - 115),
               (760, base - 45), (760, base), (0, base)], fill=(150, 180, 198))
    d.polygon([(0, base - 5), (110, base - 60), (230, base - 10), (350, base - 62),
               (480, base - 8), (610, base - 58), (760, base - 12), (760, base), (0, base)],
              fill=(126, 164, 146))


def cedars(d, xs, base, h=54, color=(63, 107, 82)):
    for x in xs:
        d.polygon([(x, base), (x + h // 3, base - h), (x + 2 * h // 3, base)], fill=color)


def band(d, title_lines, sub):
    d.rectangle([0, BAND_TOP, S, S], fill=(31, 62, 82))
    d.rectangle([0, BAND_TOP, S, BAND_TOP + 8], fill=(214, 168, 60))
    f = ImageFont.truetype(FONT_BOLD, 38)
    y = BAND_TOP + 22
    for line in title_lines:
        d.text((36, y), line, font=f, fill="#ffffff")
        y += 48
    d.text((36, S - 38), sub, font=ImageFont.truetype(FONT_REGULAR, 19), fill="#d7e2e8")


def scene_electric_fence(d):
    sky(d)
    mountains(d)
    cedars(d, [30, 78, 120, 640, 690], 300)
    # 手前の地面
    d.polygon([(0, 330), (760, 318), (760, BAND_TOP), (0, BAND_TOP)], fill=(207, 223, 194))
    # 左：草の伸びた畑
    d.polygon([(0, 322), (340, 314), (322, 470), (0, 486)], fill=(150, 170, 82))
    for i in range(14):
        x = 14 + i * 24
        d.line([(x, 484 - i * 2), (x + 6, 420 - i * 2)], fill=(108, 127, 51), width=3)
    # 獣道
    d.polygon([(250, 322), (340, 430), (470, 500), (430, 520), (300, 448), (214, 330)],
              fill=(196, 180, 147))
    # イノシシ（右向き）
    for x in (250, 276, 306, 328):
        d.line([(x, 384), (x - 4, 416)], fill=(74, 61, 49), width=9)
    d.ellipse([232, 338, 344, 392], fill=(107, 90, 73))
    d.polygon([(330, 348), (386, 362), (376, 380), (326, 384)], fill=(91, 75, 60))
    d.ellipse([376, 362, 392, 378], fill=(122, 103, 84))
    d.polygon([(330, 344), (322, 322), (346, 340)], fill=(74, 61, 49))
    d.ellipse([358, 356, 366, 364], fill=(31, 26, 21))
    d.line([(234, 350), (216, 336)], fill=(74, 61, 49), width=5)
    # シカ（左向き）
    for x in (128, 150, 178, 196):
        d.line([(x, 380), (x, 420)], fill=(122, 95, 63), width=7)
    d.ellipse([116, 340, 210, 386], fill=(154, 122, 85))
    d.polygon([(126, 348), (96, 300), (114, 296), (140, 344)], fill=(154, 122, 85))
    d.ellipse([84, 282, 118, 308], fill=(138, 108, 73))
    d.line([(100, 286), (86, 254)], fill=(122, 95, 63), width=5)
    d.line([(88, 268), (70, 262)], fill=(122, 95, 63), width=4)
    d.line([(108, 284), (120, 256)], fill=(122, 95, 63), width=5)
    d.line([(116, 268), (134, 260)], fill=(122, 95, 63), width=4)
    d.ellipse([90, 290, 98, 298], fill=(36, 28, 19))
    d.ellipse([160, 350, 172, 360], fill=(224, 212, 190))
    d.ellipse([182, 356, 194, 366], fill=(224, 212, 190))
    # 右：柵で囲われた畑
    d.polygon([(400, 318), (760, 310), (760, 452), (392, 464)], fill=(118, 166, 84))
    for i in range(4):
        d.line([(396 + i, 348 + i * 30), (760, 340 + i * 30)], fill=(77, 128, 54), width=3)
    for x in (404, 492, 580, 668, 756):
        d.line([(x, 478), (x, 372)], fill=(79, 90, 99), width=6)
    for dy in (0, 30, 60):
        d.line([(404, 392 + dy), (756, 384 + dy)], fill=(216, 99, 44), width=4)
    # 電源装置と危険表示
    d.rectangle([424, 396, 472, 438], fill=(232, 236, 236), outline=(141, 151, 155), width=3)
    d.rectangle([432, 404, 464, 420], fill=(159, 201, 216), outline=(125, 159, 174), width=2)
    d.ellipse([432, 424, 442, 434], fill=(216, 73, 47))
    d.ellipse([452, 424, 462, 434], fill=(63, 145, 82))
    d.line([(448, 372), (448, 396)], fill=(141, 151, 155), width=4)
    d.rectangle([410, 334, 486, 370], fill=(244, 214, 75), outline=(168, 138, 18), width=3)
    d.polygon([(448, 340), (458, 356), (450, 356), (458, 366), (440, 350), (448, 350)],
              fill=(58, 47, 12))
    # 農道と軽トラック
    d.polygon([(70, 616), (250, 486), (700, 478), (760, 570), (760, 616)], fill=(203, 191, 164))
    d.rectangle([470, 512, 610, 558], fill=(238, 241, 238), outline=(152, 161, 166), width=3)
    d.rectangle([470, 512, 526, 558], fill=(222, 229, 229), outline=(152, 161, 166), width=3)
    d.rectangle([480, 520, 516, 542], fill=(188, 211, 221), outline=(143, 165, 174), width=2)
    for cx in (502, 578):
        d.ellipse([cx - 16, 546, cx + 16, 578], fill=(59, 68, 76), outline=(32, 38, 43), width=3)
        d.ellipse([cx - 6, 556, cx + 6, 568], fill=(139, 149, 157))
    band(d, ["使っていない畑ほど、", "獣の通り道になる"], "森町ライフハック／農地・山林・茶畑")


def scene_cadastral(d):
    sky(d)
    mountains(d)
    cedars(d, [660, 704, 34], 300)
    d.polygon([(0, 330), (760, 318), (760, BAND_TOP), (0, BAND_TOP)], fill=(213, 227, 200))
    # 奥：畑と山林の境
    d.polygon([(0, 318), (390, 310), (376, 424), (0, 436)], fill=(126, 172, 92))
    for i in range(4):
        d.line([(0, 340 + i * 24), (384, 332 + i * 24)], fill=(84, 130, 62), width=3)
    d.polygon([(400, 306), (760, 300), (760, 430), (392, 438)], fill=(74, 108, 76))
    for x in range(410, 760, 42):
        d.polygon([(x, 430), (x + 14, 372), (x + 28, 430)], fill=(52, 86, 60))
    # 境界線と杭
    d.line([(392, 300), (368, 470)], fill=(255, 255, 255), width=6)
    d.line([(392, 300), (368, 470)], fill=(216, 99, 44), width=3)
    for y in (330, 380, 434):
        x = 392 - int((y - 300) * 24 / 170)
        d.rectangle([x - 9, y - 26, x + 9, y + 8], fill=(240, 238, 230), outline=(140, 134, 118), width=3)
        d.line([(x - 5, y - 12), (x + 5, y - 12)], fill=(190, 70, 52), width=4)
    # 手前：地籍図を広げた机
    d.polygon([(40, 592), (720, 592), (670, 466), (90, 466)], fill=(160, 140, 108))
    d.polygon([(112, 574), (648, 574), (612, 480), (148, 480)], fill=(250, 246, 234))
    for i in range(1, 4):
        d.line([(148 + i * 6, 480 + i * 24), (614 - i * 5, 480 + i * 24)], fill=(206, 196, 170), width=2)
    for i in range(1, 4):
        d.line([(148 + i * 116, 480), (124 + i * 116, 574)], fill=(206, 196, 170), width=2)
    d.polygon([(268, 492), (420, 490), (430, 546), (260, 550)], fill=(196, 220, 186),
              outline=(120, 150, 112))
    d.line([(260, 550), (268, 492)], fill=(216, 99, 44), width=5)
    d.ellipse([256, 486, 274, 504], fill=(216, 99, 44))
    d.ellipse([414, 484, 432, 502], fill=(216, 99, 44))
    # 虫めがね
    d.line([(556, 552), (600, 582)], fill=(90, 100, 108), width=13)
    d.ellipse([468, 470, 566, 568], outline=(90, 100, 108), width=9)
    d.ellipse([477, 479, 557, 559], fill=(214, 232, 240))
    band(d, ["畑と山の境界は、", "現地に立つ前に確かめる"], "森町ライフハック／農地・山林・茶畑")


def scene_smart_ic(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 62, 700, 742], 300)
    # 中景：茶畑
    d.polygon([(0, 296), (760, 288), (760, 352), (0, 362)], fill=(139, 183, 95))
    for i in range(4):
        d.line([(0, 306 + i * 14), (760, 298 + i * 14)], fill=(93, 138, 62), width=3)
    # 新東名の高架橋
    d.rectangle([0, 352, 760, 378], fill=(216, 221, 221))
    d.rectangle([0, 346, 760, 354], fill=(242, 245, 245))
    d.rectangle([0, 376, 760, 383], fill=(154, 164, 167))
    for x in (74, 300, 552):
        d.rectangle([x, 383, x + 28, 448], fill=(201, 208, 209))
        d.rectangle([x - 6, 442, x + 34, 454], fill=(174, 183, 185))
    # 高架上の車
    d.rectangle([160, 330, 218, 350], fill=(233, 237, 236), outline=(154, 164, 167), width=2)
    d.rectangle([160, 330, 182, 350], fill=(207, 216, 217))
    d.rectangle([430, 328, 502, 350], fill=(127, 168, 196), outline=(95, 130, 153), width=2)
    d.rectangle([482, 332, 500, 350], fill=(222, 231, 234))
    # ETC専用ゲート
    d.rectangle([232, 398, 246, 470], fill=(141, 149, 154))
    d.rectangle([404, 396, 418, 468], fill=(141, 149, 154))
    d.rectangle([226, 366, 424, 398], fill=(47, 95, 69), outline=(32, 69, 50), width=3)
    f = ImageFont.truetype(FONT_BOLD, 24)
    d.text((260, 372), "ETC専用", font=f, fill="#ffffff")
    d.rectangle([248, 414, 402, 423], fill=(216, 132, 44))
    for x in (258, 300, 342):
        d.rectangle([x, 414, x + 16, 423], fill=(255, 255, 255))
    # ゲート前で一旦停止する車
    d.rectangle([310, 440, 386, 470], fill=(240, 243, 241), outline=(152, 161, 166), width=3)
    d.rectangle([310, 440, 340, 470], fill=(217, 225, 226), outline=(152, 161, 166), width=3)
    for cx in (330, 372):
        d.ellipse([cx - 10, 464, cx + 10, 484], fill=(59, 68, 76))
    # 手前：集落側の町道
    d.polygon([(0, 486), (760, 466), (760, BAND_TOP), (0, BAND_TOP)], fill=(207, 200, 184))
    d.polygon([(0, 470), (760, 452), (760, 486), (0, 504)], fill=(147, 184, 105))
    for i in range(3):
        d.line([(0, 528 + i * 22), (760, 510 + i * 22)], fill=(255, 255, 255), width=4)
    # 木造駅舎
    d.rectangle([28, 462, 158, 546], fill=(244, 236, 220), outline=(169, 143, 104), width=3)
    d.polygon([(16, 462), (93, 424), (170, 462)], fill=(111, 90, 69))
    d.rectangle([44, 484, 76, 526], fill=(201, 221, 229), outline=(150, 176, 187), width=2)
    d.rectangle([92, 484, 124, 526], fill=(201, 221, 229), outline=(150, 176, 187), width=2)
    d.rectangle([28, 540, 158, 550], fill=(176, 151, 119))
    # 町営バスの停留所（要予約）
    d.rectangle([596, 456, 604, 552], fill=(141, 149, 154))
    d.rectangle([540, 436, 664, 480], fill=(255, 255, 255), outline=(44, 74, 82), width=3)
    fs = ImageFont.truetype(FONT_BOLD, 19)
    d.text((556, 442), "町営バス", font=fs, fill="#2c4a52")
    d.text((548, 460), "要予約の便", font=ImageFont.truetype(FONT_REGULAR, 16), fill="#a8551a")
    band(d, ["「ICが近い」は、", "暮らしやすさとは別"], "森町ライフハック／地区めぐり")


def scene_water_routes(d):
    sky(d)
    mountains(d)
    cedars(d, [26, 70, 116, 700, 740], 300)
    d.polygon([(0, 320), (760, 306), (760, BAND_TOP), (0, BAND_TOP)], fill=(210, 226, 196))
    # 丘の上の配水池
    d.polygon([(392, 330), (470, 274), (600, 268), (676, 330)], fill=(146, 176, 118))
    d.ellipse([472, 288, 596, 320], fill=(190, 200, 202))
    d.rectangle([472, 266, 596, 304], fill=(226, 232, 232), outline=(150, 161, 164), width=3)
    d.ellipse([472, 250, 596, 282], fill=(240, 244, 244), outline=(150, 161, 164), width=3)
    d.rectangle([520, 232, 548, 254], fill=(207, 214, 216), outline=(150, 161, 164), width=3)
    # 配水管（本管）と三方向の分岐
    d.line([(534, 318), (534, 400)], fill=(90, 140, 168), width=14)
    d.line([(140, 400), (534, 400)], fill=(90, 140, 168), width=14)
    for x in (172, 320, 466):
        d.line([(x, 400), (x, 452)], fill=(90, 140, 168), width=9)
    # 左：上水道の一戸建て
    d.rectangle([112, 452, 232, 546], fill=(246, 241, 226), outline=(181, 166, 135), width=3)
    d.polygon([(98, 452), (172, 410), (246, 452)], fill=(141, 106, 76))
    d.rectangle([130, 476, 162, 512], fill=(198, 219, 228), outline=(154, 180, 192), width=2)
    d.rectangle([182, 476, 214, 512], fill=(198, 219, 228), outline=(154, 180, 192), width=2)
    # 中央：受水槽のある集合住宅
    d.rectangle([268, 434, 374, 552], fill=(238, 240, 236), outline=(154, 164, 167), width=3)
    for row in range(3):
        for col in range(3):
            d.rectangle([280 + col * 32, 448 + row * 34, 302 + col * 32, 470 + row * 34],
                        fill=(190, 214, 224), outline=(148, 174, 186), width=2)
    d.rectangle([288, 400, 356, 434], fill=(226, 232, 232), outline=(150, 161, 164), width=3)
    d.rectangle([294, 408, 350, 420], fill=(143, 188, 214))
    # 右：簡易水道の山あいの家
    d.rectangle([416, 466, 516, 546], fill=(244, 238, 224), outline=(181, 166, 135), width=3)
    d.polygon([(404, 466), (466, 430), (528, 466)], fill=(122, 96, 70))
    d.rectangle([434, 486, 462, 516], fill=(198, 219, 228), outline=(154, 180, 192), width=2)
    d.rectangle([474, 486, 500, 516], fill=(198, 219, 228), outline=(154, 180, 192), width=2)
    # 右端：本管とつながっていない井戸（あいだを空ける）
    d.ellipse([612, 500, 728, 540], fill=(126, 160, 112))
    d.rectangle([626, 470, 714, 514], fill=(168, 152, 126), outline=(122, 108, 86), width=3)
    d.ellipse([626, 454, 714, 486], fill=(200, 224, 234), outline=(122, 108, 86), width=3)
    d.ellipse([642, 460, 698, 480], fill=(143, 188, 214))
    d.line([(638, 454), (638, 408)], fill=(122, 108, 86), width=7)
    d.line([(702, 454), (702, 408)], fill=(122, 108, 86), width=7)
    d.line([(630, 408), (710, 408)], fill=(122, 108, 86), width=7)
    d.line([(670, 408), (670, 442)], fill=(90, 100, 108), width=4)
    d.rectangle([654, 442, 686, 462], fill=(160, 140, 108), outline=(112, 96, 72), width=3)
    band(d, ["同じ森町でも、", "水の来る経路は一つでない"], "森町ライフハック／地区めぐり")


def scene_tenhama_station(d):
    sky(d)
    mountains(d)
    cedars(d, [20, 66, 112, 692, 736], 300)
    # 中景：茶畑
    d.polygon([(0, 296), (760, 288), (760, 356), (0, 366)], fill=(139, 183, 95))
    for i in range(4):
        d.line([(0, 306 + i * 15), (760, 298 + i * 15)], fill=(93, 138, 62), width=3)
    d.polygon([(0, 360), (760, 350), (760, BAND_TOP), (0, BAND_TOP)], fill=(203, 221, 178))
    # 単線の線路（枕木とレール）
    d.polygon([(0, 372), (760, 362), (760, 424), (0, 434)], fill=(205, 197, 174))
    for x in range(8, 760, 46):
        d.line([(x, 428), (x, 378)], fill=(156, 143, 116), width=7)
    d.line([(0, 386), (760, 376)], fill=(92, 98, 102), width=6)
    d.line([(0, 418), (760, 408)], fill=(92, 98, 102), width=6)
    # 左：木造駅舎と屋根付きホーム
    d.rectangle([36, 274, 198, 366], fill=(245, 238, 221), outline=(176, 151, 122), width=3)
    d.polygon([(20, 276), (117, 226), (214, 276)], fill=(125, 107, 87))
    d.rectangle([20, 276, 214, 286], fill=(100, 85, 68))
    d.rectangle([58, 296, 96, 336], fill=(198, 219, 228), outline=(148, 174, 186), width=2)
    d.rectangle([110, 296, 148, 336], fill=(198, 219, 228), outline=(148, 174, 186), width=2)
    d.rectangle([160, 300, 190, 366], fill=(168, 132, 94), outline=(132, 102, 63), width=2)
    d.rectangle([14, 366, 224, 378], fill=(222, 215, 198), outline=(179, 171, 152), width=2)
    d.line([(26, 366), (26, 322)], fill=(141, 149, 154), width=5)
    d.line([(212, 366), (212, 322)], fill=(141, 149, 154), width=5)
    d.rectangle([8, 310, 230, 324], fill=(95, 138, 156))
    # 一両の気動車
    d.rounded_rectangle([252, 296, 452, 386], radius=10, fill=(238, 242, 241),
                        outline=(147, 160, 162), width=3)
    d.rectangle([252, 320, 452, 331], fill=(63, 125, 95))
    for x in (266, 314, 362, 410):
        d.rectangle([x, 338, x + 34, 368], fill=(188, 215, 226), outline=(139, 167, 180), width=2)
    d.rectangle([278, 302, 338, 314], fill=(44, 74, 82))
    d.ellipse([272, 374, 296, 398], fill=(74, 82, 87))
    d.ellipse([414, 374, 438, 398], fill=(74, 82, 87))
    # 右：待合小屋だけの駅
    d.rectangle([578, 366, 748, 378], fill=(222, 215, 198), outline=(179, 171, 152), width=2)
    d.rectangle([614, 318, 704, 366], fill=(236, 238, 233), outline=(154, 163, 166), width=3)
    d.polygon([(600, 318), (659, 290), (718, 318)], fill=(141, 149, 154))
    d.rectangle([632, 332, 686, 350], fill=(198, 219, 228), outline=(148, 174, 186), width=2)
    # 手前：町道と町営バスの停留所
    d.polygon([(0, 470), (760, 452), (760, BAND_TOP), (0, BAND_TOP)], fill=(205, 197, 176))
    for i in range(3):
        d.line([(0, 502 + i * 26), (760, 484 + i * 26)], fill=(255, 255, 255), width=4)
    d.rectangle([196, 452, 205, 560], fill=(141, 149, 154))
    d.rectangle([138, 428, 264, 476], fill=(255, 255, 255), outline=(44, 74, 82), width=3)
    d.text((152, 434), "町営バス", font=ImageFont.truetype(FONT_BOLD, 19), fill="#2c4a52")
    d.text((146, 454), "要予約の便あり", font=ImageFont.truetype(FONT_REGULAR, 16), fill="#a8551a")
    # 手前：駅へ向かう自転車
    for cx in (520, 606):
        d.ellipse([cx - 26, 500, cx + 26, 552], outline=(58, 66, 74), width=6)
    d.line([(520, 526), (562, 490)], fill=(58, 66, 74), width=6)
    d.line([(562, 490), (606, 526)], fill=(58, 66, 74), width=6)
    d.line([(562, 490), (582, 526)], fill=(58, 66, 74), width=6)
    d.line([(560, 490), (550, 470)], fill=(58, 66, 74), width=6)
    band(d, ["「駅が近い」は、", "本数と接続を見てから"], "森町ライフハック／地区めぐり")


def scene_obon_walk(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 106, 686, 730], 300)
    # 段になった茶畑
    d.polygon([(0, 292), (760, 282), (760, 366), (0, 378)], fill=(139, 183, 95))
    for i in range(4):
        d.line([(0, 300 + i * 20), (760, 290 + i * 20)], fill=(93, 138, 62), width=4)
    d.polygon([(0, 370), (760, 358), (760, BAND_TOP), (0, BAND_TOP)], fill=(207, 224, 176))
    # 手前へ下る坂道
    d.polygon([(388, 370), (486, 370), (642, BAND_TOP), (196, BAND_TOP)], fill=(208, 201, 184))
    for i in range(4):
        y = 400 + i * 48
        d.line([(432 + i * 4, y), (440 + i * 4, y + 26)], fill=(255, 255, 255), width=5)
    # 右手の蓋のない水路
    d.polygon([(486, 370), (516, 370), (700, BAND_TOP), (642, BAND_TOP)], fill=(168, 160, 138))
    d.polygon([(494, 376), (510, 376), (684, 584), (660, 584)], fill=(143, 188, 214))
    # 左：石段を上がった先の家
    d.rectangle([48, 318, 250, 420], fill=(245, 238, 221), outline=(176, 151, 122), width=3)
    d.polygon([(32, 320), (149, 262), (266, 320)], fill=(125, 107, 87))
    d.rectangle([32, 320, 266, 330], fill=(100, 85, 68))
    d.rectangle([76, 344, 122, 386], fill=(198, 219, 228), outline=(148, 174, 186), width=2)
    d.rectangle([140, 344, 186, 386], fill=(198, 219, 228), outline=(148, 174, 186), width=2)
    d.rectangle([204, 348, 236, 420], fill=(168, 132, 94), outline=(132, 102, 63), width=2)
    d.rectangle([48, 414, 250, 424], fill=(169, 143, 112))
    for i in range(5):
        d.rectangle([150 + i * 8, 428 + i * 16, 254 + i * 8, 442 + i * 16],
                    fill=(201, 195, 177), outline=(164, 157, 137), width=2)
    # 電柱と防災無線のスピーカー
    d.rectangle([322, 232, 332, 340], fill=(163, 163, 150))
    d.rectangle([304, 244, 350, 251], fill=(141, 141, 128))
    d.polygon([(328, 238), (356, 228), (356, 254), (328, 246)], fill=(207, 214, 216),
              outline=(150, 161, 164))
    # バス停の標識
    d.rectangle([352, 372, 359, 432], fill=(154, 163, 166))
    d.rectangle([314, 348, 396, 378], fill=(255, 255, 255), outline=(44, 74, 82), width=3)
    d.text((324, 354), "バス停", font=ImageFont.truetype(FONT_BOLD, 19), fill="#2c4a52")
    # 集会所（水路の向こう）
    d.rectangle([578, 300, 694, 356], fill=(238, 241, 238), outline=(152, 161, 166), width=3)
    d.polygon([(566, 302), (636, 272), (706, 302)], fill=(141, 149, 154))
    d.rectangle([596, 316, 628, 342], fill=(198, 219, 228), outline=(148, 174, 186), width=2)
    d.rectangle([644, 316, 676, 342], fill=(198, 219, 228), outline=(148, 174, 186), width=2)
    # 並んで歩く親と子
    d.ellipse([386, 428, 426, 468], fill=(227, 195, 157), outline=(185, 146, 107), width=3)
    d.chord([386, 422, 426, 458], 180, 360, fill=(206, 210, 212))
    d.line([(406, 468), (406, 524)], fill=(138, 111, 156), width=24)
    d.line([(396, 524), (386, 572)], fill=(67, 80, 90), width=12)
    d.line([(416, 524), (426, 572)], fill=(67, 80, 90), width=12)
    d.line([(396, 482), (374, 514)], fill=(138, 111, 156), width=12)
    d.ellipse([464, 406, 504, 446], fill=(227, 195, 157), outline=(185, 146, 107), width=3)
    d.chord([464, 398, 504, 434], 180, 360, fill=(74, 64, 56))
    d.line([(484, 446), (484, 508)], fill=(63, 111, 134), width=24)
    d.line([(474, 508), (462, 562)], fill=(67, 80, 90), width=12)
    d.line([(494, 508), (506, 562)], fill=(67, 80, 90), width=12)
    d.line([(476, 462), (450, 494)], fill=(63, 111, 134), width=12)
    band(d, ["お盆の三日間で、", "親の生活圏を歩く"], "森町ライフハック／地区めぐり")


def firework(d, cx, cy, r, color, tip):
    for dx, dy in ((0, -1), (0.7, -0.7), (1, 0), (0.7, 0.7), (0, 1), (-0.7, 0.7), (-1, 0), (-0.7, -0.7)):
        x2, y2 = cx + dx * r, cy + dy * r
        d.line([(cx, cy), (x2, y2)], fill=color, width=4)
        d.ellipse([x2 - 4, y2 - 4, x2 + 4, y2 + 4], fill=tip)


def scene_hanabi_river(d):
    # 夕暮れの空
    for y in range(0, 262):
        t = y / 262
        d.line([(0, y), (S, y)], fill=(int(58 + 190 * t), int(84 + 138 * t), int(118 + 66 * t)))
    d.rectangle([0, 262, S, BAND_TOP], fill=(226, 236, 216))
    firework(d, 148, 92, 56, (244, 208, 106), (249, 236, 192))
    firework(d, 402, 64, 44, (232, 139, 106), (246, 203, 180))
    firework(d, 626, 118, 40, (168, 216, 200), (222, 240, 234))
    mountains(d, 300)
    cedars(d, [22, 66, 690, 734], 300)
    # 段になった茶畑
    d.polygon([(0, 292), (760, 284), (760, 340), (0, 350)], fill=(112, 148, 88))
    for i in range(3):
        d.line([(0, 300 + i * 15), (760, 292 + i * 15)], fill=(88, 122, 68), width=3)
    # 橋（右手）
    d.rectangle([470, 306, 760, 320], fill=(200, 204, 198))
    d.rectangle([470, 298, 760, 306], fill=(226, 229, 223))
    for x in (520, 620, 720):
        d.rectangle([x, 320, x + 14, 356], fill=(176, 181, 174))
    # 堤防と葉桜の並木
    d.polygon([(0, 348), (760, 338), (760, 386), (0, 400)], fill=(147, 168, 120))
    for cx in (56, 152, 248, 344, 440):
        d.ellipse([cx - 40, 300, cx + 40, 350], fill=(79, 122, 67))
        d.line([(cx, 352), (cx, 322)], fill=(107, 82, 56), width=7)
    for cx in (104, 200, 296, 392):
        d.line([(cx, 356), (cx, 314)], fill=(141, 143, 136), width=4)
        d.rectangle([cx - 11, 292, cx + 11, 316], fill=(240, 201, 106), outline=(195, 154, 60), width=2)
    # 河川敷（芝生）
    d.polygon([(0, 396), (760, 382), (760, 486), (0, 504)], fill=(156, 184, 119))
    # ローラースケート場のトラック
    d.ellipse([26, 414, 250, 480], fill=(185, 176, 160), outline=(154, 146, 133), width=4)
    d.ellipse([62, 428, 214, 466], fill=(168, 189, 133))
    # グラウンドのバックネットと内野
    d.polygon([(292, 434), (292, 368), (386, 362), (386, 432)], fill=(201, 212, 194),
              outline=(141, 154, 136))
    for x in (316, 340, 364):
        d.line([(x, 366), (x, 434)], fill=(141, 154, 136), width=2)
    for y in (388, 410):
        d.line([(292, y), (386, y - 4)], fill=(141, 154, 136), width=2)
    d.polygon([(296, 452), (420, 444), (446, 458), (304, 468)], fill=(203, 184, 148))
    # 並んだ車
    for row, col_fill in ((392, (232, 236, 231)), (418, (207, 214, 208))):
        for i in range(4):
            x = 466 + i * 60
            d.rounded_rectangle([x, row - i, x + 48, row + 18 - i], radius=5,
                                fill=col_fill, outline=(154, 162, 156), width=3)
    # 屋台のテント
    d.polygon([(568, 452), (634, 430), (700, 452), (700, 458), (568, 458)], fill=(192, 68, 44))
    d.rectangle([576, 458, 692, 486], fill=(240, 236, 224), outline=(195, 189, 169), width=3)
    d.line([(578, 486), (578, 498)], fill=(168, 160, 148), width=4)
    d.line([(690, 486), (690, 498)], fill=(168, 160, 148), width=4)
    # 河原を歩く人
    for cx, cy in ((236, 420), (274, 428), (440, 424)):
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(227, 195, 157), outline=(185, 146, 107), width=2)
        d.rounded_rectangle([cx - 8, cy + 9, cx + 8, cy + 36], radius=7, fill=(63, 111, 134))
        d.line([(cx - 4, cy + 36), (cx - 7, cy + 56)], fill=(67, 80, 90), width=6)
        d.line([(cx + 4, cy + 36), (cx + 7, cy + 56)], fill=(67, 80, 90), width=6)
    # 玉石の河原
    d.polygon([(0, 498), (760, 480), (760, 518), (0, 538)], fill=(205, 201, 187))
    for cx, cy in ((84, 522), (176, 514), (292, 510), (420, 504), (548, 500), (676, 494)):
        d.ellipse([cx - 15, cy - 7, cx + 15, cy + 7], fill=(180, 176, 162))
    # 川の流れ
    d.polygon([(0, 534), (760, 514), (760, BAND_TOP), (0, BAND_TOP)], fill=(111, 155, 178))
    d.line([(40, 566), (400, 552)], fill=(185, 219, 230), width=5)
    d.line([(470, 578), (740, 564)], fill=(185, 219, 230), width=5)
    d.polygon([(198, 576), (330, 564), (392, 576), (300, 586), (206, 582)], fill=(198, 194, 178))
    # 量水標
    d.rectangle([446, 486, 462, 588], fill=(242, 242, 236), outline=(91, 106, 114), width=3)
    for y in (506, 526, 546, 566):
        d.line([(446, y), (462, y)], fill=(91, 106, 114), width=3)
    d.line([(438, 516), (470, 516)], fill=(192, 68, 44), width=5)
    band(d, ["花火の会場は、", "一年の大半が川の中"], "森町ライフハック／祭礼・イベント")


def scene_yatai_storage(d):
    sky(d)
    mountains(d, 300)
    cedars(d, [18, 62, 700, 742], 300)
    # 段になった茶畑
    d.polygon([(0, 292), (760, 284), (760, 336), (0, 346)], fill=(126, 168, 92))
    for i in range(3):
        d.line([(0, 300 + i * 14), (760, 292 + i * 14)], fill=(94, 132, 70), width=3)
    d.polygon([(0, 340), (760, 330), (760, BAND_TOP), (0, BAND_TOP)], fill=(213, 227, 200))
    # 右奥：神社の境内
    d.polygon([(452, 340), (760, 330), (760, 380), (452, 390)], fill=(184, 200, 164))
    for i in range(3):
        d.rectangle([470 + i * 5, 356 - i * 12, 556 + i * 5, 366 - i * 12],
                    fill=(203, 198, 182), outline=(169, 164, 147), width=2)
    d.rectangle([566, 250, 578, 340], fill=(184, 80, 58))
    d.rectangle([640, 248, 652, 338], fill=(184, 80, 58))
    d.rectangle([552, 234, 666, 248], fill=(184, 80, 58))
    d.rectangle([560, 266, 658, 276], fill=(184, 80, 58))
    d.polygon([(660, 300), (704, 272), (748, 300)], fill=(125, 106, 83))
    d.rectangle([668, 300, 742, 344], fill=(239, 231, 213), outline=(181, 164, 135), width=3)
    d.rectangle([692, 314, 718, 344], fill=(194, 160, 116), outline=(157, 127, 87), width=2)
    cedars(d, [452, 740], 344, h=44, color=(79, 122, 82))
    # 中央奥：集会所と掲示板
    d.polygon([(292, 302), (356, 270), (420, 302)], fill=(141, 148, 154))
    d.rectangle([302, 302, 410, 352], fill=(239, 241, 236), outline=(174, 180, 174), width=3)
    d.rectangle([316, 316, 344, 340], fill=(195, 217, 227), outline=(150, 177, 189), width=2)
    d.rectangle([356, 316, 384, 340], fill=(195, 217, 227), outline=(150, 177, 189), width=2)
    d.rectangle([392, 322, 406, 352], fill=(194, 160, 116), outline=(157, 127, 87), width=2)
    d.rectangle([236, 308, 288, 314], fill=(140, 133, 120))
    d.rectangle([240, 314, 248, 358], fill=(140, 133, 120))
    d.rectangle([276, 314, 284, 358], fill=(140, 133, 120))
    d.rectangle([236, 316, 288, 350], fill=(246, 244, 234), outline=(179, 172, 154), width=3)
    for i in range(3):
        d.line([(244, 326 + i * 8), (280 - i * 8, 326 + i * 8)], fill=(168, 85, 26), width=3)
    # 左：屋台蔵（主役）
    d.polygon([(10, 356), (146, 288), (282, 356)], fill=(111, 91, 69))
    d.rectangle([10, 352, 282, 364], fill=(84, 69, 47))
    d.rectangle([28, 362, 266, 506], fill=(239, 233, 218), outline=(176, 166, 142), width=4)
    d.rectangle([58, 386, 238, 506], fill=(201, 171, 119), outline=(150, 117, 75), width=4)
    d.line([(148, 386), (148, 506)], fill=(150, 117, 75), width=5)
    # 開いたすきまから見える屋台
    d.rectangle([130, 394, 174, 506], fill=(61, 52, 40))
    d.ellipse([122, 428, 182, 488], outline=(211, 180, 111), width=7)
    d.ellipse([148, 454, 156, 462], fill=(211, 180, 111))
    d.line([(152, 430), (152, 486)], fill=(211, 180, 111), width=3)
    d.line([(124, 458), (180, 458)], fill=(211, 180, 111), width=3)
    d.line([(132, 438), (172, 478)], fill=(211, 180, 111), width=3)
    d.line([(172, 438), (132, 478)], fill=(211, 180, 111), width=3)
    d.rounded_rectangle([138, 400, 166, 424], radius=11, fill=(240, 214, 142),
                        outline=(195, 154, 60), width=3)
    d.line([(140, 412), (164, 412)], fill=(184, 80, 58), width=3)
    # 蔵の札
    d.rectangle([190, 398, 246, 432], fill=(255, 255, 255), outline=(141, 154, 160), width=3)
    d.line([(198, 410), (238, 410)], fill=(141, 154, 160), width=3)
    d.line([(198, 420), (228, 420)], fill=(141, 154, 160), width=3)
    # 太鼓蔵
    d.polygon([(288, 408), (340, 378), (392, 408)], fill=(125, 106, 83))
    d.rectangle([298, 408, 382, 492], fill=(239, 233, 218), outline=(176, 166, 142), width=4)
    d.rectangle([316, 428, 364, 492], fill=(201, 171, 119), outline=(150, 117, 75), width=3)
    d.line([(400, 470), (386, 500)], fill=(140, 116, 84), width=8)
    d.line([(444, 470), (458, 500)], fill=(140, 116, 84), width=8)
    d.ellipse([392, 424, 452, 476], fill=(184, 80, 58), outline=(140, 58, 41), width=3)
    d.ellipse([404, 434, 440, 466], fill=(240, 224, 194), outline=(201, 181, 142), width=3)
    d.line([(398, 418), (450, 438)], fill=(214, 186, 140), width=7)
    d.line([(450, 418), (398, 438)], fill=(214, 186, 140), width=7)
    # 境界杭と敷地の線
    for x, y in ((478, 486), (700, 462)):
        d.rectangle([x, y, x + 16, y + 38], fill=(244, 242, 234), outline=(154, 148, 132), width=3)
        d.line([(x + 2, y + 14), (x + 14, y + 14)], fill=(192, 68, 44), width=4)
    for i in range(9):
        x0 = 494 + i * 24
        d.line([(x0, 486 - i * 3), (x0 + 14, 484 - i * 3)], fill=(168, 85, 26), width=5)
    # 手前の道
    d.polygon([(0, 520), (760, 502), (760, BAND_TOP), (0, BAND_TOP)], fill=(205, 197, 176))
    for i in range(2):
        d.line([(0, 548 + i * 26), (760, 530 + i * 26)], fill=(255, 255, 255), width=4)
    # 図面を広げて確かめる二人
    d.rectangle([516, 522, 664, 566], fill=(253, 251, 243), outline=(124, 138, 144), width=3)
    for i in range(1, 4):
        d.line([(516 + i * 37, 522), (516 + i * 37, 566)], fill=(199, 192, 172), width=2)
    d.line([(516, 544), (664, 544)], fill=(199, 192, 172), width=2)
    d.polygon([(552, 530), (620, 528), (624, 558), (556, 560)], fill=(226, 236, 214),
              outline=(143, 174, 125), width=3)
    for cx, body in ((492, (92, 127, 87)), (688, (63, 111, 134))):
        d.ellipse([cx - 17, 496, cx + 17, 530], fill=(227, 195, 157), outline=(185, 146, 107), width=3)
        d.rounded_rectangle([cx - 15, 530, cx + 15, 572], radius=13, fill=body)
        d.line([(cx - 7, 572), (cx - 12, BAND_TOP)], fill=(67, 80, 90), width=10)
        d.line([(cx + 7, 572), (cx + 12, BAND_TOP)], fill=(67, 80, 90), width=10)
    band(d, ["屋台をしまう建物は、", "誰の名義で建っているか"], "森町ライフハック／祭礼・イベント")


def scene_tencomori(d):
    sky(d)
    mountains(d, 300)
    cedars(d, [22, 66, 690, 734], 300)
    # 段になった茶畑
    d.polygon([(0, 292), (760, 284), (760, 340), (0, 350)], fill=(126, 168, 92))
    for i in range(3):
        d.line([(0, 300 + i * 15), (760, 292 + i * 15)], fill=(94, 132, 70), width=3)
    d.polygon([(0, 344), (760, 334), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 228, 201))
    # 奥：集落の家並みと鳥居
    for x, w in ((44, 96), (168, 78), (600, 92)):
        d.rectangle([x, 352, x + w, 392], fill=(233, 227, 214))
        d.polygon([(x - 8, 354), (x + w // 2, 326), (x + w + 8, 354)], fill=(139, 154, 162))
    d.rectangle([300, 336, 308, 388], fill=(184, 80, 58))
    d.rectangle([352, 336, 360, 388], fill=(184, 80, 58))
    d.rectangle([288, 326, 372, 336], fill=(184, 80, 58))
    d.rectangle([294, 346, 366, 353], fill=(184, 80, 58))
    # 太田川と橋
    d.polygon([(0, 400), (760, 388), (760, 428), (0, 442)], fill=(158, 198, 221))
    d.line([(60, 418), (330, 410)], fill=(226, 240, 246), width=5)
    d.line([(420, 416), (700, 404)], fill=(226, 240, 246), width=5)
    d.rectangle([448, 386, 700, 396], fill=(216, 211, 196))
    for x in (472, 552, 632):
        d.rectangle([x, 396, x + 9, 428], fill=(183, 178, 163))
    # 手前：田と道
    d.polygon([(0, 436), (760, 422), (760, 486), (0, 502)], fill=(206, 224, 178))
    for i in range(2):
        d.line([(0, 456 + i * 22), (760, 442 + i * 22)], fill=(168, 196, 137), width=4)
    d.polygon([(0, 496), (760, 480), (760, 520), (0, 538)], fill=(205, 197, 176))
    d.line([(0, 518), (760, 500)], fill=(255, 255, 255), width=4)
    # 縁側の板張り
    d.rectangle([0, 530, 760, BAND_TOP], fill=(201, 168, 119))
    for y in (544, 560, 576):
        d.line([(0, y), (760, y)], fill=(177, 144, 95), width=3)
    # 縁側に座る三人（卓の向こう側）
    for cx, body, rh in ((110, (92, 139, 109), 24), (378, (74, 120, 150), 24), (652, (220, 154, 99), 20)):
        d.ellipse([cx - rh, 424 - rh, cx + rh, 424 + rh], fill=(230, 196, 157),
                  outline=(189, 154, 114), width=3)
        d.chord([cx - rh, 424 - rh - 6, cx + rh, 424 + rh - 6], 180, 360, fill=(70, 61, 51))
        d.polygon([(cx - rh - 6, 452), (cx + rh + 6, 452), (cx + rh + 14, 522), (cx - rh - 14, 522)],
                  fill=body)
        d.line([(cx + rh + 4, 470), (cx + rh + 26, 500)], fill=(230, 196, 157), width=13)
    # 低い卓（手前）と開いたパンフレット
    d.rectangle([132, 520, 512, 542], fill=(185, 143, 93))
    d.rectangle([132, 542, 512, 550], fill=(160, 120, 74))
    d.polygon([(160, 520), (320, 486), (322, 520)], fill=(255, 255, 255),
              outline=(150, 162, 168), width=4)
    d.polygon([(484, 520), (324, 486), (322, 520)], fill=(243, 246, 244),
              outline=(150, 162, 168), width=4)
    d.line([(322, 486), (322, 520)], fill=(150, 162, 168), width=4)
    for i in range(4):
        d.line([(196 + i * 8, 508 - i * 6), (310, 496 - i * 6)], fill=(190, 199, 204), width=4)
        d.line([(334, 496 - i * 6), (448 - i * 8, 508 - i * 6)], fill=(190, 199, 204), width=4)
    # 三枚の付せん（卓の手前・右）
    for x, fill, edge in ((536, (244, 215, 116), (207, 174, 63)),
                          (610, (168, 216, 176), (111, 168, 124)),
                          (684, (169, 207, 232), (111, 155, 184))):
        d.rectangle([x, 522, x + 62, 570], fill=fill, outline=edge, width=3)
        d.line([(x + 10, 538), (x + 50, 538)], fill=(125, 124, 102), width=4)
        d.line([(x + 10, 552), (x + 42, 552)], fill=(125, 124, 102), width=4)
    # 鉛筆
    d.rectangle([176, 562, 254, 572], fill=(224, 176, 74))
    d.polygon([(254, 560), (276, 567), (254, 574)], fill=(138, 107, 58))
    band(d, ["パンフレットを開く前に、", "条件を三つ決めておく"], "森町ライフハック／移住・暮らし・データ")


def scene_akiya_august(d):
    # 夏の強い空
    for y in range(0, 300):
        t = y / 300
        d.line([(0, y), (S, y)], fill=(int(140 + 96 * t), int(190 + 44 * t), int(224 - 8 * t)))
    d.rectangle([0, 300, S, BAND_TOP], fill=(226, 236, 216))
    # 太陽
    d.ellipse([44, 30, 148, 134], fill=(255, 224, 138))
    d.ellipse([58, 44, 134, 120], fill=(255, 210, 94))
    for dx, dy in ((0, -78), (0, 78), (-78, 0), (78, 0), (-56, -56), (56, 56), (-56, 56), (56, -56)):
        d.line([(96 + dx // 2, 82 + dy // 2), (96 + dx, 82 + dy)], fill=(255, 210, 94), width=8)
    # 入道雲
    for cx, cy, r in ((470, 108, 52), (532, 78, 64), (604, 110, 50), (660, 94, 42),
                      (528, 136, 50), (606, 140, 42)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
    d.rounded_rectangle([432, 128, 700, 164], radius=18, fill=(255, 255, 255))
    mountains(d, 300)
    cedars(d, [16, 58, 700, 742], 300)
    # 段になった茶畑
    d.polygon([(0, 294), (760, 286), (760, 336), (0, 346)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 302 + i * 14), (760, 294 + i * 14)], fill=(105, 147, 74), width=3)
    d.polygon([(0, 340), (760, 330), (760, BAND_TOP), (0, BAND_TOP)], fill=(219, 230, 193))
    # 空き家（瓦屋根の平屋）
    d.polygon([(96, 396), (352, 306), (608, 396)], fill=(127, 143, 151))
    d.polygon([(122, 396), (352, 316), (582, 396)], fill=(147, 161, 168))
    d.line([(176, 372), (416, 372)], fill=(119, 133, 140), width=4)
    d.rectangle([140, 396, 566, 520], fill=(239, 233, 219))
    d.rectangle([140, 396, 566, 408], fill=(207, 199, 181))
    # 開いた雨戸
    d.rectangle([144, 414, 176, 500], fill=(169, 144, 106), outline=(139, 115, 80), width=3)
    d.rectangle([530, 414, 562, 500], fill=(169, 144, 106), outline=(139, 115, 80), width=3)
    # 開け放った窓（奥が暗い）
    d.rectangle([188, 418, 336, 498], fill=(95, 111, 116), outline=(139, 148, 154), width=4)
    d.rectangle([368, 418, 516, 498], fill=(95, 111, 116), outline=(139, 148, 154), width=4)
    d.rectangle([344, 414, 362, 502], fill=(216, 207, 186))
    # 縁側
    d.rectangle([132, 502, 574, 524], fill=(201, 168, 119))
    d.rectangle([132, 524, 574, 534], fill=(169, 138, 92))
    # 風の通り道
    d.line([(72, 458), (188, 448)], fill=(63, 126, 164), width=7)
    d.polygon([(188, 436), (216, 448), (188, 460)], fill=(63, 126, 164))
    d.line([(516, 452), (620, 442)], fill=(63, 126, 164), width=7)
    d.polygon([(620, 430), (650, 442), (620, 454)], fill=(63, 126, 164))
    # 傾いた物置
    d.polygon([(628, 424), (740, 414), (748, 500), (636, 508)], fill=(207, 212, 208))
    d.polygon([(620, 426), (684, 392), (750, 416)], fill=(143, 153, 149))
    d.rectangle([664, 448, 706, 500], fill=(180, 187, 183), outline=(152, 160, 156), width=3)
    # 伸びた草（縁側より手前だけ）
    for x in range(8, 760, 30):
        d.line([(x, 588), (x + 8, 544)], fill=(111, 155, 70), width=5)
        d.line([(x + 14, 590), (x + 20, 554)], fill=(127, 170, 82), width=4)
    # 温度計・懐中電灯・水筒（手前の草の中）
    d.rectangle([88, 528, 114, 588], fill=(244, 246, 242), outline=(125, 135, 140), width=3)
    d.rectangle([95, 546, 107, 580], fill=(192, 86, 60))
    d.rounded_rectangle([164, 556, 236, 582], radius=8, fill=(61, 70, 78))
    d.polygon([(236, 550), (276, 569), (236, 588)], fill=(255, 233, 168))
    d.rounded_rectangle([628, 540, 668, 588], radius=9, fill=(74, 120, 150),
                        outline=(55, 98, 124), width=3)
    d.rectangle([638, 530, 658, 542], fill=(55, 98, 124))
    band(d, ["空き家の下見は、", "八月の午後に一度入る"], "森町ライフハック／移住・暮らし・データ")


def scene_quiet_sunday(d):
    sky(d)
    mountains(d, 300)
    cedars(d, [14, 56, 704, 746], 300)
    # 段になった茶畑
    d.polygon([(0, 292), (760, 284), (760, 332), (0, 342)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 300 + i * 13), (760, 292 + i * 13)], fill=(105, 147, 74), width=3)
    # 太田川と橋
    d.polygon([(0, 340), (760, 330), (760, 366), (0, 378)], fill=(158, 198, 221))
    d.line([(40, 356), (300, 348)], fill=(226, 240, 246), width=4)
    d.line([(430, 354), (700, 344)], fill=(226, 240, 246), width=4)
    d.rectangle([460, 328, 700, 337], fill=(216, 211, 196))
    for x in (492, 566, 640):
        d.rectangle([x, 337, x + 8, 366], fill=(183, 178, 163))
    d.polygon([(0, 372), (760, 360), (760, BAND_TOP), (0, BAND_TOP)], fill=(219, 231, 195))
    # 図書館
    d.rectangle([28, 394, 200, 480], fill=(240, 236, 224), outline=(201, 192, 171), width=3)
    d.polygon([(16, 396), (114, 358), (212, 396)], fill=(139, 154, 162))
    d.rectangle([48, 412, 180, 424], fill=(31, 62, 82))
    d.rectangle([46, 434, 84, 468], fill=(207, 224, 234), outline=(169, 191, 203), width=3)
    d.rectangle([96, 434, 134, 468], fill=(207, 224, 234), outline=(169, 191, 203), width=3)
    d.rectangle([148, 434, 180, 480], fill=(185, 163, 124), outline=(154, 133, 96), width=3)
    # 資料館（瓦屋根の古い建物）
    d.rectangle([248, 400, 404, 480], fill=(234, 227, 211), outline=(196, 186, 162), width=3)
    d.polygon([(234, 402), (326, 364), (418, 402)], fill=(127, 143, 151))
    d.polygon([(250, 396), (326, 370), (402, 396)], fill=(147, 161, 168))
    for x in (266, 310, 354):
        d.rectangle([x, 420, x + 32, 458], fill=(217, 210, 192), outline=(186, 177, 155), width=2)
    d.rectangle([304, 458, 348, 480], fill=(185, 163, 124), outline=(154, 133, 96), width=3)
    # 体育館（丸い屋根）
    d.rectangle([456, 414, 626, 480], fill=(238, 240, 236), outline=(195, 200, 193), width=3)
    d.pieslice([450, 358, 632, 470], 180, 360, fill=(147, 167, 173))
    for x in (476, 526, 576):
        d.rectangle([x, 430, x + 32, 456], fill=(207, 224, 234), outline=(169, 191, 203), width=2)
    d.rectangle([524, 456, 570, 480], fill=(185, 163, 124), outline=(154, 133, 96), width=3)
    # バス停の標柱
    d.rectangle([690, 414, 700, 500], fill=(125, 135, 140))
    d.rectangle([662, 386, 728, 422], fill=(246, 244, 234), outline=(125, 135, 140), width=3)
    for y in (396, 405, 414):
        d.line([(670, y), (720, y)], fill=(152, 162, 166), width=3)
    d.ellipse([683, 366, 707, 390], fill=(74, 120, 150))
    # 集落の道
    d.polygon([(0, 492), (760, 476), (760, 540), (0, 560)], fill=(205, 197, 176))
    d.line([(0, 528), (760, 510)], fill=(255, 255, 255), width=4)
    # 歩く三人家族
    for cx, body, r, base in ((176, (92, 139, 109), 24, 500), (264, (220, 154, 99), 19, 512),
                              (352, (74, 120, 150), 24, 504)):
        d.ellipse([cx - r, base - r * 2 - 8, cx + r, base - 8], fill=(230, 196, 157),
                  outline=(189, 154, 114), width=3)
        d.chord([cx - r, base - r * 2 - 14, cx + r, base - 14], 180, 360, fill=(70, 61, 51))
        d.polygon([(cx - r - 6, base + 2), (cx + r + 6, base + 2),
                   (cx + r + 12, BAND_TOP), (cx - r - 12, BAND_TOP)], fill=body)
    band(d, ["何もない日曜日を、", "家族で一日過ごす"], "森町ライフハック／移住・暮らし・データ")


def scene_obon_window(d):
    # 夕暮れの空
    for y in range(0, 250):
        t = y / 250
        d.line([(0, y), (S, y)], fill=(int(95 + 148 * t), int(126 + 76 * t), int(166 - 6 * t)))
    d.rectangle([0, 250, S, BAND_TOP], fill=(226, 236, 216))
    d.ellipse([608, 148, 692, 232], fill=(255, 209, 140))
    mountains(d, 250)
    cedars(d, [12, 50, 700, 742], 250)
    # 段になった茶畑
    d.polygon([(0, 244), (760, 236), (760, 288), (0, 298)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 252 + i * 14), (760, 244 + i * 14)], fill=(105, 147, 74), width=3)
    d.polygon([(0, 292), (760, 282), (760, BAND_TOP), (0, BAND_TOP)], fill=(219, 231, 195))
    # 役場の庁舎
    d.polygon([(28, 320), (210, 254), (392, 320)], fill=(139, 154, 162))
    d.polygon([(48, 314), (210, 268), (372, 314)], fill=(162, 176, 182))
    d.rectangle([50, 320, 390, 430], fill=(238, 241, 236), outline=(195, 200, 193), width=3)
    d.rounded_rectangle([76, 330, 364, 362], radius=6, fill=(31, 62, 82))
    d.text((220, 346), "森町役場", font=ImageFont.truetype(FONT_BOLD, 24),
           fill=(255, 255, 255), anchor="mm")
    for x in (68, 140, 212):
        d.rectangle([x, 376, x + 58, 416], fill=(255, 233, 168), outline=(201, 171, 106), width=3)
    d.rectangle([288, 376, 336, 430], fill=(207, 224, 234), outline=(169, 191, 203), width=3)
    d.rectangle([344, 384, 384, 430], fill=(185, 143, 93), outline=(148, 112, 63), width=3)
    # コンビニとマルチコピー機
    d.rectangle([430, 344, 730, 430], fill=(244, 242, 232), outline=(201, 192, 171), width=3)
    d.rectangle([430, 344, 730, 370], fill=(47, 125, 90))
    d.text((580, 357), "コンビニ", font=ImageFont.truetype(FONT_BOLD, 18),
           fill=(255, 255, 255), anchor="mm")
    d.rectangle([446, 380, 570, 424], fill=(207, 224, 234), outline=(169, 191, 203), width=3)
    d.rectangle([600, 376, 700, 428], fill=(232, 235, 232), outline=(152, 162, 166), width=3)
    d.rectangle([610, 384, 690, 400], fill=(255, 233, 168), outline=(201, 171, 106), width=2)
    d.rectangle([622, 408, 678, 424], fill=(195, 200, 193))
    # 七枚の日めくり札
    d.line([(16, 436), (744, 432)], fill=(139, 133, 119), width=3)
    labels = ("月", "火", "水", "木", "金", "土", "日")
    subs = ("17:15", "閉庁", "19時まで", "17:15", "17:15", "閉庁", "閉庁")
    closed = (1, 5, 6)
    f_day = ImageFont.truetype(FONT_BOLD, 30)
    f_sub = ImageFont.truetype(FONT_REGULAR, 15)
    f_sub_b = ImageFont.truetype(FONT_BOLD, 15)
    for i, name in enumerate(labels):
        x = 22 + 106 * i
        d.line([(x + 47, 434), (x + 47, 446)], fill=(139, 133, 119), width=2)
        if i == 2:
            d.rounded_rectangle([x, 444, x + 94, 548], radius=8,
                                fill=(31, 62, 82), outline=(18, 41, 58), width=3)
            d.text((x + 47, 484), name, font=f_day, fill=(255, 255, 255), anchor="mm")
            d.text((x + 47, 524), subs[i], font=f_sub_b, fill=(255, 217, 138), anchor="mm")
            continue
        if i in closed:
            fill, line, day_c, sub_c = (221, 216, 205), (164, 156, 141), (107, 95, 82), (122, 59, 48)
        else:
            fill, line, day_c, sub_c = (244, 246, 238), (154, 167, 155), (31, 62, 82), (62, 107, 85)
        d.rounded_rectangle([x, 444, x + 94, 516], radius=8, fill=fill, outline=line, width=3)
        d.text((x + 47, 476), name, font=f_day, fill=day_c, anchor="mm")
        d.text((x + 47, 502), subs[i], font=f_sub, fill=sub_c, anchor="mm")
    # 手前の道と、庁舎へ向かう人・コンビニへ向かう親子
    d.polygon([(0, 552), (760, 542), (760, BAND_TOP), (0, BAND_TOP)], fill=(205, 197, 176))
    d.ellipse([97, 533, 123, 559], fill=(230, 196, 157), outline=(189, 154, 114), width=3)
    d.chord([97, 527, 123, 553], 180, 360, fill=(70, 61, 51))
    d.polygon([(95, 562), (125, 562), (131, BAND_TOP), (89, BAND_TOP)], fill=(55, 83, 107))
    d.ellipse([628, 536, 652, 560], fill=(230, 196, 157), outline=(189, 154, 114), width=3)
    d.chord([628, 530, 652, 554], 180, 360, fill=(91, 74, 54))
    d.polygon([(626, 563), (654, 563), (660, BAND_TOP), (620, BAND_TOP)], fill=(92, 139, 109))
    d.ellipse([668, 548, 688, 568], fill=(240, 211, 173), outline=(196, 160, 119), width=3)
    d.polygon([(667, 570), (689, 570), (693, BAND_TOP), (663, BAND_TOP)], fill=(220, 154, 99))
    band(d, ["19時まで開くのは水曜だけ", "お盆週の窓口の使い方"], "森町ライフハック／手続き・制度")


def scene_consult_split(d):
    sky(d)
    mountains(d, 250)
    cedars(d, [14, 52, 700, 742], 250)
    # 段になった茶畑
    d.polygon([(0, 244), (760, 236), (760, 286), (0, 296)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 252 + i * 14), (760, 244 + i * 14)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 290), (760, 280), (760, BAND_TOP), (0, BAND_TOP)], fill=(224, 233, 210))
    # 相談する建物
    d.polygon([(226, 306), (380, 254), (534, 306)], fill=(139, 154, 162))
    d.polygon([(246, 300), (380, 268), (514, 300)], fill=(162, 176, 182))
    d.rectangle([246, 306, 514, 392], fill=(241, 243, 238), outline=(195, 200, 193), width=3)
    d.rounded_rectangle([266, 314, 494, 340], radius=5, fill=(31, 62, 82))
    d.text((380, 327), "相談窓口", font=ImageFont.truetype(FONT_BOLD, 20),
           fill=(255, 255, 255), anchor="mm")
    for x in (266, 328, 390, 452):
        d.rectangle([x, 352, x + 44, 384], fill=(207, 224, 234), outline=(169, 191, 203), width=3)
    # 左右を分ける破線
    for y in range(404, BAND_TOP, 26):
        d.line([(380, y), (380, min(y + 14, BAND_TOP))], fill=(150, 146, 132), width=4)
    # 左：予約が要る（カレンダーと電話する人）
    d.rounded_rectangle([56, 404, 320, 442], radius=10, fill=(31, 62, 82))
    d.text((188, 423), "予約が要る", font=ImageFont.truetype(FONT_BOLD, 22),
           fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([36, 460, 186, 576], radius=7, fill=(255, 255, 255),
                        outline=(179, 173, 160), width=3)
    d.rounded_rectangle([36, 460, 186, 486], radius=7, fill=(192, 86, 60))
    marked = {(1, 1), (2, 2), (3, 0)}
    for row in range(3):
        for col in range(4):
            cx, cy = 62 + col * 34, 506 + row * 26
            if (col, row) in marked:
                d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(192, 86, 60))
                d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=(192, 86, 60), width=3)
            else:
                d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(138, 132, 119))
    d.ellipse([238, 466, 302, 530], fill=(230, 196, 157), outline=(189, 154, 114), width=3)
    d.chord([238, 458, 302, 522], 180, 360, fill=(70, 61, 51))
    d.polygon([(228, 540), (312, 540), (322, BAND_TOP), (218, BAND_TOP)], fill=(55, 83, 107))
    d.rounded_rectangle([300, 452, 326, 502], radius=11, fill=(74, 79, 86))
    for r in (18, 32):
        d.arc([326 - r, 477 - r, 326 + r, 477 + r], -60, 60, fill=(74, 120, 150), width=5)
    # 右：予約は要らない（掲示板と開いた扉）
    d.rounded_rectangle([432, 404, 728, 442], radius=10, fill=(62, 107, 85))
    d.text((580, 423), "予約は要らない", font=ImageFont.truetype(FONT_BOLD, 22),
           fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([416, 460, 546, 562], radius=6, fill=(248, 246, 238),
                        outline=(164, 156, 141), width=3)
    d.rectangle([430, 474, 532, 490], fill=(62, 107, 85))
    for i in range(3):
        d.line([(430, 508 + i * 16), (532 - i * 18, 508 + i * 16)], fill=(195, 189, 174), width=4)
    d.rectangle([476, 562, 486, BAND_TOP], fill=(138, 132, 119))
    d.rectangle([588, 440, 728, BAND_TOP], fill=(231, 226, 212), outline=(179, 173, 160), width=3)
    d.rectangle([606, 458, 710, BAND_TOP], fill=(255, 233, 168))
    d.polygon([(606, 458), (652, 476), (652, BAND_TOP), (606, BAND_TOP)], fill=(201, 168, 106))
    d.ellipse([638, 524, 648, 534], fill=(138, 111, 63))
    d.ellipse([664, 486, 716, 538], fill=(230, 196, 157), outline=(189, 154, 114), width=3)
    d.chord([664, 478, 716, 530], 180, 360, fill=(91, 74, 54))
    d.polygon([(656, 546), (724, 546), (730, BAND_TOP), (650, BAND_TOP)], fill=(92, 139, 109))
    band(d, ["予約が要る相談と、", "要らない相談"], "森町ライフハック／手続き・制度")


def scene_proxy_certificates(d):
    # 座敷の壁と鴨居
    d.rectangle([0, 0, S, 368], fill=(234, 227, 211))
    d.rectangle([0, 66, S, 76], fill=(168, 135, 94))
    # 畳
    d.rectangle([0, 368, S, BAND_TOP], fill=(222, 215, 184))
    for y in (420, 480, 540):
        d.line([(0, y), (S, y)], fill=(201, 194, 162), width=3)
    for x in (190, 400, 610):
        d.line([(x, 368), (x, BAND_TOP)], fill=(201, 194, 162), width=3)
    # 掛け軸
    d.rounded_rectangle([52, 88, 188, 98], radius=4, fill=(107, 85, 57))
    d.rectangle([60, 98, 180, 288], fill=(245, 240, 226), outline=(216, 207, 180), width=3)
    d.rounded_rectangle([52, 288, 188, 300], radius=4, fill=(107, 85, 57))
    d.line([(76, 232), (100, 186)], fill=(143, 165, 176), width=5)
    d.line([(100, 186), (124, 228)], fill=(143, 165, 176), width=5)
    d.line([(124, 228), (148, 180)], fill=(143, 165, 176), width=5)
    d.line([(148, 180), (170, 230)], fill=(143, 165, 176), width=5)
    d.ellipse([132, 122, 160, 150], fill=(216, 164, 138))
    # 障子の外（茶畑と蔵）
    for y in range(88, 190):
        t = (y - 88) / 102
        d.line([(420, y), (724, y)], fill=(int(188 + 45 * t), int(216 + 26 * t), int(234 - 8 * t)))
    d.polygon([(420, 186), (462, 158), (504, 188), (552, 154), (600, 186), (648, 154),
               (696, 188), (724, 166), (724, 210), (420, 210)], fill=(157, 182, 196))
    d.polygon([(424, 210), (434, 182), (444, 210)], fill=(79, 127, 102))
    d.polygon([(704, 210), (714, 180), (724, 210)], fill=(79, 127, 102))
    d.polygon([(420, 204), (724, 198), (724, 232), (420, 238)], fill=(123, 169, 84))
    for i in range(2):
        d.line([(420, 212 + i * 12), (724, 206 + i * 12)], fill=(95, 138, 66), width=3)
    d.polygon([(420, 234), (724, 228), (724, 286), (420, 286)], fill=(217, 227, 198))
    d.polygon([(448, 244), (504, 216), (560, 244)], fill=(125, 139, 147))
    d.polygon([(458, 239), (504, 221), (550, 239)], fill=(152, 165, 171))
    d.rectangle([458, 244, 550, 286], fill=(242, 240, 230), outline=(207, 201, 182), width=3)
    d.rectangle([488, 262, 520, 286], fill=(138, 122, 99), outline=(109, 96, 76), width=3)
    d.rectangle([648, 258, 656, 286], fill=(138, 111, 79))
    d.ellipse([626, 226, 678, 278], fill=(92, 139, 109))
    # 縁側と障子の枠
    d.rectangle([420, 286, 724, 306], fill=(201, 168, 106))
    d.rectangle([420, 300, 724, 308], fill=(169, 138, 82))
    d.rectangle([412, 80, 732, 312], outline=(138, 111, 79), width=10)
    d.rectangle([412, 80, 476, 312], fill=(246, 243, 230), outline=(138, 111, 79), width=6)
    d.line([(444, 86), (444, 306)], fill=(201, 189, 160), width=3)
    for y in (140, 196, 252):
        d.line([(416, y), (472, y)], fill=(201, 189, 160), width=3)
    # 親（左・筆を持つ）
    d.ellipse([202, 292, 278, 368], fill=(230, 196, 157), outline=(189, 154, 114), width=3)
    d.chord([202, 284, 278, 360], 180, 360, fill=(216, 211, 203))
    d.polygon([(196, 372), (284, 372), (298, 470), (182, 470)], fill=(107, 127, 140))
    d.line([(288, 400), (344, 430)], fill=(230, 196, 157), width=17)
    d.line([(340, 424), (368, 462)], fill=(59, 54, 48), width=11)
    # 子（右・用紙を押さえる）
    d.ellipse([420, 300, 488, 368], fill=(240, 211, 173), outline=(196, 160, 119), width=3)
    d.chord([420, 292, 488, 360], 180, 360, fill=(70, 61, 51))
    d.polygon([(416, 374), (492, 374), (504, 470), (404, 470)], fill=(74, 120, 150))
    d.line([(414, 404), (368, 434)], fill=(240, 211, 173), width=16)
    # 卓袱台
    d.ellipse([80, 448, 680, 560], fill=(185, 143, 93))
    d.ellipse([80, 434, 680, 546], fill=(211, 165, 107))
    d.rectangle([196, 540, 216, BAND_TOP], fill=(162, 121, 63))
    d.rectangle([548, 536, 568, BAND_TOP], fill=(162, 121, 63))
    # 机の上：委任状・朱肉と印鑑・免許証・封筒
    d.polygon([(158, 456), (322, 448), (338, 508), (172, 518)], fill=(255, 255, 255),
              outline=(198, 203, 199), width=3)
    for i in range(3):
        d.line([(178 + i * 2, 470 + i * 14), (306 - i * 18, 464 + i * 14)],
               fill=(185, 194, 198), width=3)
    d.ellipse([358, 470, 402, 496], fill=(224, 219, 208), outline=(182, 176, 162), width=3)
    d.ellipse([368, 474, 392, 488], fill=(192, 86, 60))
    d.rounded_rectangle([414, 448, 434, 490], radius=5, fill=(138, 111, 79),
                        outline=(109, 85, 57), width=2)
    d.rectangle([414, 482, 434, 492], fill=(192, 86, 60))
    d.polygon([(456, 462), (532, 456), (536, 490), (460, 496)], fill=(238, 243, 247),
              outline=(182, 194, 202), width=3)
    d.ellipse([468, 470, 484, 486], fill=(200, 207, 212))
    d.line([(496, 472), (526, 470)], fill=(200, 207, 212), width=3)
    d.line([(497, 482), (520, 480)], fill=(200, 207, 212), width=3)
    d.polygon([(120, 512), (212, 504), (218, 548), (126, 556)], fill=(246, 241, 226),
              outline=(202, 191, 159), width=3)
    d.line([(120, 512), (168, 534)], fill=(202, 191, 159), width=3)
    d.line([(168, 534), (212, 504)], fill=(202, 191, 159), width=3)
    band(d, ["実家の証明書を、", "子が代わりに取る"], "森町ライフハック／手続き・制度")


def scene_akiya_plan(d):
    sky(d)
    mountains(d)
    cedars(d, [20, 62, 104, 660, 704, 744], 300)
    # 段になった茶畑
    d.polygon([(0, 292), (760, 284), (760, 340), (0, 350)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 300 + i * 15), (760, 292 + i * 15)], fill=(105, 147, 74), width=3)
    d.polygon([(0, 344), (760, 334), (760, BAND_TOP), (0, BAND_TOP)], fill=(219, 230, 193))
    # 川と橋（奥）
    d.polygon([(0, 356), (760, 346), (760, 372), (0, 382)], fill=(143, 185, 207))
    d.rectangle([300, 344, 470, 352], fill=(216, 210, 194))
    d.rectangle([310, 352, 320, 378], fill=(189, 183, 166))
    d.rectangle([450, 352, 460, 378], fill=(189, 183, 166))
    # 奥の集落
    for x in (60, 152, 596, 676):
        d.polygon([(x, 392), (x + 34, 368), (x + 68, 392)], fill=(127, 143, 151))
        d.rectangle([x + 8, 392, x + 60, 424], fill=(239, 233, 219), outline=(198, 191, 174), width=2)
        d.rectangle([x + 24, 402, x + 40, 424], fill=(184, 196, 200))
    # 手前左：雨戸を閉めた空き家
    d.polygon([(28, 468), (196, 384), (364, 468)], fill=(111, 124, 130))
    d.polygon([(52, 468), (196, 396), (340, 468)], fill=(139, 151, 155))
    d.line([(84, 452), (308, 452)], fill=(102, 115, 122), width=4)
    d.polygon([(252, 414), (288, 434), (262, 440), (232, 424)], fill=(77, 88, 94))
    d.rectangle([56, 468, 336, 566], fill=(239, 233, 219), outline=(194, 186, 167), width=3)
    d.rectangle([84, 488, 190, 552], fill=(179, 154, 118), outline=(143, 122, 91), width=3)
    for x in (110, 136, 162):
        d.line([(x, 488), (x, 552)], fill=(143, 122, 91), width=3)
    d.rectangle([214, 488, 300, 538], fill=(195, 214, 221), outline=(147, 167, 174), width=3)
    d.line([(218, 494), (262, 522)], fill=(93, 111, 119), width=3)
    d.line([(262, 522), (296, 502)], fill=(93, 111, 119), width=3)
    d.line([(254, 488), (246, 536)], fill=(93, 111, 119), width=3)
    # 外れかけた樋
    d.line([(336, 472), (352, 480)], fill=(154, 165, 169), width=7)
    d.line([(352, 480), (348, 534)], fill=(154, 165, 169), width=7)
    d.line([(348, 534), (368, 560)], fill=(154, 165, 169), width=7)
    # 傾いたブロック塀
    for x in (16, 56, 96):
        d.rectangle([x, 524, x + 38, 548], fill=(207, 202, 189), outline=(169, 162, 146), width=3)
    d.polygon([(138, 522), (178, 528), (174, 552), (134, 546)], fill=(196, 191, 175),
              outline=(169, 162, 146), width=3)
    # 伸びた草（塀の手前だけ）
    for x in range(12, 392, 26):
        d.line([(x, 588), (x + 7, 556)], fill=(121, 149, 63), width=5)
    # 手前右：地図を広げて確かめる二人
    d.polygon([(396, 524), (752, 500), (760, 588), (410, 588)], fill=(246, 241, 226))
    d.polygon([(396, 524), (752, 500), (754, 514), (398, 538)], fill=(226, 219, 197))
    for i in range(4):
        d.line([(432 + i * 80, 588), (450 + i * 80, 518)], fill=(206, 197, 173), width=3)
    for i in range(2):
        d.line([(400, 552 + i * 22), (758, 530 + i * 22)], fill=(206, 197, 173), width=3)
    d.line([(430, 578), (520, 540), (612, 566), (700, 528)], fill=(150, 186, 208), width=6)
    d.ellipse([494, 522, 546, 560], outline=(192, 86, 60), width=6)
    # 左の人（地図の丸印を指さす）
    d.ellipse([420, 388, 476, 444], fill=(230, 196, 157), outline=(189, 154, 114), width=3)
    d.pieslice([420, 380, 476, 436], 180, 360, fill=(70, 61, 51))
    d.polygon([(412, 456), (484, 456), (498, 528), (398, 528)], fill=(74, 120, 150))
    d.line([(482, 474), (516, 528)], fill=(230, 196, 157), width=15)
    d.ellipse([504, 518, 530, 542], fill=(230, 196, 157))
    # 右の人（手帳に書き取る）
    d.ellipse([624, 400, 676, 452], fill=(230, 196, 157), outline=(189, 154, 114), width=3)
    d.pieslice([624, 392, 676, 444], 180, 360, fill=(58, 50, 42))
    d.polygon([(616, 464), (684, 464), (700, 532), (604, 532)], fill=(63, 107, 82))
    d.rectangle([616, 508, 692, 560], fill=(255, 255, 255), outline=(186, 194, 198), width=3)
    for i in range(3):
        d.line([(626, 522 + i * 12), (682, 522 + i * 12)], fill=(196, 206, 211), width=3)
    d.line([(614, 484), (626, 514)], fill=(230, 196, 157), width=14)
    d.line([(700, 500), (668, 528)], fill=(192, 86, 60), width=7)
    band(d, ["町は10年計画で", "空き家を見ている"], "森町ライフハック／空き家・実家・相続")


def scene_water_shutoff(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 58, 100, 686, 728], 300)
    # 丘の上の配水池
    d.polygon([(556, 300), (620, 250), (720, 244), (760, 262), (760, 300)], fill=(159, 185, 143))
    d.rectangle([636, 208, 716, 250], fill=(223, 228, 226), outline=(169, 178, 176), width=3)
    d.polygon([(628, 208), (676, 186), (724, 208)], fill=(148, 163, 166))
    d.rectangle([654, 250, 664, 268], fill=(169, 178, 176))
    d.rectangle([690, 250, 700, 268], fill=(169, 178, 176))
    # 段になった茶畑
    d.polygon([(0, 292), (760, 284), (760, 336), (0, 344)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 300 + i * 14), (760, 292 + i * 14)], fill=(105, 147, 74), width=3)
    d.polygon([(0, 340), (760, 330), (760, BAND_TOP), (0, BAND_TOP)], fill=(219, 230, 193))
    # 左：雨戸を閉めた空き家
    d.polygon([(6, 424), (166, 340), (326, 424)], fill=(111, 124, 130))
    d.polygon([(30, 424), (166, 352), (302, 424)], fill=(139, 151, 155))
    d.line([(62, 408), (270, 408)], fill=(102, 115, 122), width=4)
    d.rectangle([34, 424, 298, 526], fill=(239, 233, 219), outline=(194, 186, 167), width=3)
    d.rectangle([60, 446, 158, 508], fill=(179, 154, 118), outline=(143, 122, 91), width=3)
    for x in (84, 110, 134):
        d.line([(x, 446), (x, 508)], fill=(143, 122, 91), width=3)
    d.rectangle([186, 446, 268, 496], fill=(195, 214, 221), outline=(147, 167, 174), width=3)
    # 伸びた草
    for x in range(10, 320, 26):
        d.line([(x, 570), (x + 7, 536)], fill=(121, 149, 63), width=5)
    # 手前：開いたメーターボックス
    d.ellipse([88, 528, 300, 588], fill=(207, 202, 189))
    d.ellipse([98, 524, 290, 580], fill=(142, 154, 160), outline=(111, 122, 128), width=3)
    d.ellipse([116, 528, 272, 572], fill=(60, 74, 82))
    d.rectangle([136, 534, 200, 562], fill=(201, 204, 196), outline=(141, 147, 140), width=3)
    d.ellipse([158, 540, 180, 558], fill=(238, 242, 243), outline=(141, 147, 140), width=3)
    d.line([(169, 549), (169, 542)], fill=(192, 86, 60), width=3)
    d.rectangle([220, 538, 246, 558], fill=(169, 178, 176), outline=(125, 135, 133), width=3)
    d.line([(233, 538), (233, 524)], fill=(125, 135, 133), width=4)
    d.line([(216, 524), (250, 524)], fill=(192, 86, 60), width=7)
    # 開けた蓋
    d.polygon([(300, 522), (372, 500), (384, 532), (312, 554)], fill=(180, 188, 187),
              outline=(141, 150, 148), width=3)
    # 右：二つの札
    d.rounded_rectangle([404, 372, 736, 432], radius=12, fill=(31, 62, 82))
    f = ImageFont.truetype(FONT_BOLD, 25)
    d.text((422, 390), "廃止 → 再開は新規扱い", font=f, fill="#ffffff")
    d.rounded_rectangle([404, 444, 736, 504], radius=12, fill=(255, 255, 255),
                        outline=(143, 183, 156), width=4)
    d.text((422, 462), "継続 → 毎月の基本料金", font=f, fill="#1f3e52")
    # 加入金の札束
    d.rounded_rectangle([432, 300, 604, 350], radius=8, fill=(232, 223, 194),
                        outline=(185, 169, 112), width=3)
    d.rounded_rectangle([444, 286, 616, 336], radius=8, fill=(242, 234, 208),
                        outline=(185, 169, 112), width=3)
    d.ellipse([514, 296, 546, 326], fill=(216, 178, 94), outline=(168, 132, 47), width=3)
    # 硬貨
    for cx in (654, 690, 726):
        d.ellipse([cx - 20, 306, cx + 20, 346], fill=(201, 194, 176), outline=(154, 147, 132), width=3)
    fs = ImageFont.truetype(FONT_REGULAR, 19)
    d.text((408, 518), "加入金 38,500円（口径13ミリ）", font=fs, fill=(63, 73, 80))
    d.text((408, 546), "基本料金 1,100円（1か月）", font=fs, fill=(63, 73, 80))
    band(d, ["止めると再開に", "加入金がかかる"], "森町ライフハック／空き家・実家・相続")


def scene_nayosecho(d):
    """親名義の筆が実家のまわりに散らばり、明細書には一部しか載らない場面。"""
    sky(d)
    mountains(d)
    cedars(d, [24, 66, 108, 660, 706], 300)
    # 茶畑の帯
    d.polygon([(0, 296), (760, 288), (760, 340), (0, 350)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 306 + i * 14), (760, 298 + i * 14)], fill=(95, 138, 66), width=3)
    # 手前の地面
    d.polygon([(0, 344), (760, 334), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    # 川
    d.polygon([(0, 366), (240, 356), (470, 380), (760, 366), (760, 396), (470, 410),
               (240, 386), (0, 398)], fill=(169, 206, 222))
    # 道
    d.polygon([(0, 470), (300, 448), (760, 470), (760, 492), (300, 472), (0, 496)],
              fill=(232, 226, 210))
    # 山林の筆（右上）
    d.polygon([(560, 300), (700, 268), (748, 312), (606, 346)], fill=(93, 127, 92))
    for x in (592, 630, 668):
        d.polygon([(x, 322), (x + 12, 292), (x + 24, 322)], fill=(51, 96, 74))
    # 畑の筆（左）
    d.polygon([(24, 404), (256, 392), (270, 462), (36, 476)], fill=(185, 168, 132))
    for i in range(3):
        d.line([(30, 418 + i * 18), (264, 408 + i * 18)], fill=(149, 133, 106), width=4)
    # 実家（中央）
    d.polygon([(276, 400), (386, 340), (496, 400)], fill=(111, 124, 130))
    d.polygon([(296, 400), (386, 350), (476, 400)], fill=(139, 151, 155))
    d.rectangle([300, 400, 472, 486], fill=(243, 239, 227), outline=(194, 186, 167), width=4)
    d.rectangle([322, 424, 372, 466], fill=(227, 233, 234), outline=(181, 191, 194), width=3)
    d.line([(347, 424), (347, 466)], fill=(181, 191, 194), width=3)
    d.rectangle([404, 428, 446, 486], fill=(200, 207, 203), outline=(163, 172, 168), width=3)
    # 雑種地の筆（右下）
    d.polygon([(516, 452), (712, 442), (722, 500), (526, 512)], fill=(207, 201, 172))
    # 境界杭（赤頭）
    for x, y in ((24, 404), (270, 462), (276, 400), (496, 400), (560, 300), (748, 312),
                 (516, 452), (722, 500)):
        d.rectangle([x - 4, y - 26, x + 4, y], fill=(138, 122, 94))
        d.rectangle([x - 8, y - 34, x + 8, y - 24], fill=(192, 86, 60))
    # 左手前：課税明細書（三行だけ実線、残りは点線）
    d.polygon([(30, 496), (250, 486), (262, 578), (42, BAND_TOP)], fill=(255, 255, 255),
              outline=(185, 194, 198), width=3)
    for i in range(3):
        d.line([(52, 514 + i * 16), (238, 506 + i * 16)], fill=(143, 183, 156), width=6)
    for i in range(2):
        for seg in range(6):
            x0 = 56 + seg * 31
            d.line([(x0, 564 + i * 16), (x0 + 18, 563 + i * 16)], fill=(213, 218, 220), width=4)
    # 右手前：名寄帳の一覧（行が多い）
    d.polygon([(496, 486), (734, 496), (722, BAND_TOP), (484, 578)], fill=(255, 255, 255),
              outline=(185, 194, 198), width=3)
    for i in range(6):
        d.line([(510, 508 + i * 13), (712, 514 + i * 13)], fill=(143, 183, 156), width=5)
    f = ImageFont.truetype(FONT_BOLD, 22)
    d.rounded_rectangle([300, 500, 464, 540], radius=10, fill=(31, 62, 82))
    d.text((318, 510), "名寄帳", font=f, fill="#ffffff")
    band(d, ["親の土地は課税明細", "だけでは数え切れない"], "森町ライフハック／空き家・実家・相続")


def scene_souzoku_houki(d):
    """継がないと決める3か月と、放棄しても残る保存義務を並べた場面。"""
    sky(d)
    mountains(d)
    cedars(d, [24, 68, 690, 730], 300)
    d.polygon([(0, 296), (760, 288), (760, 336), (0, 346)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 304 + i * 13), (760, 296 + i * 13)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 340), (760, 330), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    # 左：雨戸を閉めた実家
    d.polygon([(16, 384), (146, 310), (276, 384)], fill=(111, 124, 130))
    d.polygon([(34, 384), (146, 320), (258, 384)], fill=(139, 151, 155))
    d.rectangle([34, 384, 258, 500], fill=(233, 227, 211), outline=(189, 180, 159), width=4)
    for x0 in (54, 156):
        d.rectangle([x0, 408, x0 + 84, 484], fill=(185, 172, 145), outline=(148, 138, 114), width=3)
        for i in range(3):
            d.line([(x0 + 21 * (i + 1), 408), (x0 + 21 * (i + 1), 484)], fill=(148, 138, 114), width=3)
    # 外れかけた樋
    d.line([(30, 390), (150, 390)], fill=(163, 172, 168), width=7)
    d.line([(150, 390), (176, 414)], fill=(163, 172, 168), width=7)
    # 伸びた草
    for x in (24, 46, 68, 246, 268, 290):
        d.line([(x, 528), (x + 6, 486)], fill=(121, 149, 63), width=4)
    # 右：三か月のカレンダー
    for i, x0 in enumerate((408, 528, 648)):
        last = i == 2
        head_fill = (192, 86, 60) if last else (95, 125, 140)
        d.rounded_rectangle([x0, 328, x0 + 100, 452], radius=8, fill=(255, 255, 255),
                            outline=head_fill, width=4)
        d.rounded_rectangle([x0, 328, x0 + 100, 356], radius=8, fill=head_fill)
        for row in range(4):
            for col in range(5):
                d.rounded_rectangle([x0 + 10 + col * 17, 368 + row * 20,
                                     x0 + 22 + col * 17, 378 + row * 20],
                                    radius=2, fill=(207, 215, 218))
        if last:
            d.ellipse([x0 + 60, 402, x0 + 92, 434], outline=(192, 86, 60), width=6)
    f = ImageFont.truetype(FONT_BOLD, 21)
    d.text((418, 334), "1か月", font=f, fill="#ffffff")
    d.text((538, 334), "2か月", font=f, fill="#ffffff")
    d.text((658, 334), "3か月", font=f, fill="#ffffff")
    # 手前：申述書と印紙と鍵
    d.polygon([(292, 470), (462, 462), (470, 560), (300, 568)], fill=(255, 255, 255),
              outline=(185, 194, 198), width=3)
    d.rounded_rectangle([302, 478, 456, 508], radius=7, fill=(62, 107, 85))
    d.text((312, 484), "相続放棄申述書", font=ImageFont.truetype(FONT_BOLD, 19), fill="#ffffff")
    for i in range(3):
        d.line([(310, 524 + i * 14), (452, 520 + i * 14)], fill=(169, 191, 203), width=4)
    d.rounded_rectangle([474, 476, 528, 544], radius=4, fill=(220, 201, 168),
                        outline=(179, 159, 124), width=3)
    d.ellipse([485, 495, 517, 527], fill=(176, 101, 90))
    d.ellipse([566, 496, 598, 528], outline=(138, 122, 94), width=6)
    d.line([(596, 508), (662, 480)], fill=(138, 122, 94), width=7)
    d.line([(646, 486), (652, 470)], fill=(138, 122, 94), width=6)
    d.line([(624, 496), (630, 480)], fill=(138, 122, 94), width=6)
    band(d, ["継がないと決めるなら", "3か月"], "森町ライフハック／空き家・実家・相続")


def scene_obon_clean_center(d):
    """お盆週に家財を軽トラックへ積み、受入日を見比べる場面。"""
    sky(d)
    mountains(d)
    cedars(d, [22, 66, 700, 738], 300)
    d.polygon([(0, 296), (760, 288), (760, 334), (0, 344)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 304 + i * 13), (760, 296 + i * 13)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 338), (760, 328), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    d.polygon([(0, 490), (760, 478), (760, 534), (0, 546)], fill=(232, 226, 210))
    # 左：実家
    d.polygon([(6, 388), (104, 332), (202, 388)], fill=(111, 124, 130))
    d.rectangle([22, 388, 186, 470], fill=(243, 239, 227), outline=(194, 186, 167), width=4)
    d.rectangle([40, 408, 84, 444], fill=(227, 233, 234), outline=(181, 191, 194), width=3)
    d.rectangle([116, 412, 152, 470], fill=(200, 207, 203), outline=(163, 172, 168), width=3)
    # 軽トラック
    d.rectangle([250, 372, 512, 460], fill=(230, 233, 230), outline=(169, 178, 176), width=4)
    d.polygon([(512, 460), (512, 366), (596, 366), (626, 412), (626, 460)],
              fill=(230, 233, 230), outline=(169, 178, 176), width=4)
    d.polygon([(536, 378), (588, 378), (610, 410), (536, 410)], fill=(207, 224, 230),
              outline=(169, 188, 194), width=3)
    # 荷物
    d.rectangle([264, 316, 336, 370], fill=(214, 191, 148), outline=(172, 151, 112), width=3)
    d.line([(300, 316), (300, 370)], fill=(172, 151, 112), width=3)
    d.rectangle([346, 330, 424, 370], fill=(238, 241, 234), outline=(184, 192, 182), width=3)
    d.rectangle([434, 308, 504, 370], fill=(214, 191, 148), outline=(172, 151, 112), width=3)
    d.line([(434, 340), (504, 340)], fill=(172, 151, 112), width=3)
    d.ellipse([300, 288, 420, 318], fill=(185, 143, 93), outline=(143, 108, 67), width=3)
    d.rectangle([242, 452, 630, 470], fill=(139, 151, 155))
    for cx in (312, 566):
        d.ellipse([cx - 30, 462, cx + 30, 522], fill=(60, 74, 82))
        d.ellipse([cx - 13, 479, cx + 13, 505], fill=(169, 178, 176))
    # 右：受入日の三枚札
    f = ImageFont.truetype(FONT_BOLD, 22)
    fs = ImageFont.truetype(FONT_REGULAR, 18)
    rows = (("火 8/11", "休み", (192, 86, 60)),
            ("水〜金", "9時〜17時", (62, 107, 85)),
            ("土", "午前だけ", (184, 134, 15)))
    for i, (day, note, col) in enumerate(rows):
        y0 = 336 + i * 76
        d.rounded_rectangle([624, y0, 744, y0 + 62], radius=10, fill=(255, 255, 255),
                            outline=col, width=4)
        d.rounded_rectangle([624, y0, 744, y0 + 28], radius=10, fill=col)
        d.text((636, y0 + 3), day, font=f, fill="#ffffff")
        d.text((636, y0 + 34), note, font=fs, fill=(66, 83, 92))
    band(d, ["家財を運び出す前に、", "受入日を見る"], "森町ライフハック／空き家・実家・相続")


def scene_tomodake(d):
    """茅葺きに戻された民家と、隣で建築年を数えている実家を並べた場面。"""
    sky(d)
    mountains(d)
    cedars(d, [20, 64, 108, 700, 740], 300)
    d.polygon([(0, 296), (760, 288), (760, 336), (0, 346)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 304 + i * 13), (760, 296 + i * 13)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 340), (760, 330), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    # 左：茅葺きの寄棟屋根
    d.polygon([(8, 424), (86, 314), (250, 314), (328, 424)], fill=(150, 128, 82))
    d.line([(82, 314), (254, 314)], fill=(93, 77, 43), width=9)
    for x0, x1 in ((40, 100), (74, 122), (108, 144), (232, 190), (266, 212), (300, 234)):
        d.line([(x0, 424), (x1, 324)], fill=(174, 152, 100), width=3)
    d.line([(8, 426), (328, 426)], fill=(111, 92, 52), width=8)
    d.rectangle([28, 428, 308, 528], fill=(231, 222, 208), outline=(184, 171, 151), width=4)
    d.rectangle([44, 452, 110, 528], fill=(90, 75, 61), outline=(63, 53, 41), width=3)
    d.rectangle([128, 452, 210, 512], fill=(239, 231, 214), outline=(168, 152, 126), width=3)
    for x in (144, 160, 176, 192):
        d.line([(x, 452), (x, 512)], fill=(125, 107, 79), width=5)
    d.rectangle([228, 452, 292, 512], fill=(239, 231, 214), outline=(168, 152, 126), width=3)
    d.line([(260, 452), (260, 512)], fill=(168, 152, 126), width=3)
    # 足場と茅の束
    for x in (238, 292, 340):
        d.line([(x, 322), (x, 452)], fill=(169, 127, 75), width=6)
    for y in (368, 414):
        d.line([(232, y), (346, y)], fill=(169, 127, 75), width=6)
    d.polygon([(236, 340), (300, 364), (294, 384), (230, 360)], fill=(201, 172, 109),
              outline=(156, 132, 82))
    # 標識
    d.line([(66, 570), (66, 528)], fill=(138, 122, 94), width=6)
    d.rounded_rectangle([12, 536, 148, 570], radius=7, fill=(255, 255, 255),
                        outline=(62, 107, 85), width=3)
    d.text((26, 543), "重要文化財", font=ImageFont.truetype(FONT_BOLD, 21), fill=(31, 62, 82))
    # 右：瓦屋根の実家
    d.polygon([(410, 428), (536, 348), (662, 428)], fill=(111, 124, 130))
    d.polygon([(428, 428), (536, 358), (644, 428)], fill=(139, 151, 155))
    d.rectangle([428, 428, 644, 524], fill=(233, 227, 211), outline=(189, 180, 159), width=4)
    for x0 in (446, 550):
        d.rectangle([x0, 450, x0 + 78, 512], fill=(185, 172, 145), outline=(148, 138, 114), width=3)
        for i in range(3):
            d.line([(x0 + 19 * (i + 1), 450), (x0 + 19 * (i + 1), 512)], fill=(148, 138, 114), width=3)
    # 手前：書類と巻尺と電卓
    d.polygon([(392, 536), (752, 528), (760, 584), (400, 592)], fill=(196, 169, 127),
              outline=(164, 141, 104))
    d.polygon([(406, 540), (546, 536), (552, 580), (412, 584)], fill=(255, 255, 255),
              outline=(185, 194, 198))
    d.text((416, 544), "建築年", font=ImageFont.truetype(FONT_BOLD, 19), fill=(62, 107, 85))
    for i in range(2):
        d.line([(416, 566 + i * 10), (540, 563 + i * 10)], fill=(169, 191, 203), width=3)
    d.ellipse([576, 538, 634, 584], fill=(216, 137, 47), outline=(168, 104, 30), width=4)
    d.ellipse([598, 553, 614, 569], fill=(244, 231, 205))
    d.line([(630, 546), (686, 534)], fill=(244, 231, 205), width=8)
    d.rounded_rectangle([664, 546, 744, 588], radius=6, fill=(74, 90, 99),
                        outline=(51, 67, 75), width=3)
    d.rectangle([674, 552, 734, 566], fill=(207, 224, 216))
    for r in range(2):
        for c in range(3):
            d.rounded_rectangle([674 + c * 21, 572 + r * 9, 686 + c * 21, 578 + r * 9],
                                radius=2, fill=(143, 162, 172))
    band(d, ["茅葺きは戻された。", "古さを二つに分ける"], "森町ライフハック／寺社・歴史")


def scene_ishimatsu(d):
    """門前の削られた墓石と、訪ねる人のいない斜面の墓地を並べた場面。"""
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 104, 296, 340], 300)
    d.polygon([(0, 296), (760, 288), (760, 332), (0, 342)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 304 + i * 12), (760, 296 + i * 12)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 336), (760, 326), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    # 左：山門
    d.polygon([(24, 366), (168, 300), (312, 366)], fill=(92, 74, 58))
    d.polygon([(48, 366), (168, 310), (288, 366)], fill=(122, 100, 80))
    d.rectangle([18, 368, 318, 380], fill=(74, 60, 47))
    d.rectangle([60, 380, 82, 470], fill=(107, 86, 67))
    d.rectangle([254, 380, 276, 470], fill=(107, 86, 67))
    d.rectangle([82, 392, 254, 470], fill=(60, 51, 42))
    d.rectangle([120, 408, 216, 470], fill=(44, 38, 31))
    # 削られた墓石
    d.rectangle([116, 528, 220, 548], fill=(185, 189, 180), outline=(147, 152, 142), width=3)
    d.rectangle([128, 508, 208, 530], fill=(200, 204, 195), outline=(147, 152, 142), width=3)
    d.rounded_rectangle([142, 436, 194, 510], radius=22, fill=(213, 216, 207),
                        outline=(147, 152, 142), width=3)
    d.arc([132, 452, 160, 486], 300, 60, fill=(169, 173, 163), width=6)
    d.arc([176, 452, 204, 486], 120, 240, fill=(169, 173, 163), width=6)
    # 線香の煙
    for x in (232, 250):
        d.line([(x, 528), (x + 10, 500)], fill=(183, 195, 200), width=4)
        d.line([(x + 10, 500), (x - 2, 474)], fill=(183, 195, 200), width=4)
    d.rectangle([222, 528, 262, 540], fill=(138, 122, 94))
    # 三代目の札
    d.line([(74, 560), (74, 512)], fill=(138, 122, 94), width=5)
    d.rounded_rectangle([26, 480, 124, 514], radius=7, fill=(255, 255, 255),
                        outline=(192, 86, 60), width=3)
    d.text((38, 486), "三代目", font=ImageFont.truetype(FONT_BOLD, 22), fill=(192, 86, 60))
    # 右：草の伸びた斜面の墓地
    d.polygon([(392, 356), (760, 336), (760, BAND_TOP), (392, BAND_TOP)], fill=(213, 224, 201))
    d.line([(396, 434), (760, 418)], fill=(189, 180, 159), width=6)
    d.line([(400, 512), (760, 494)], fill=(189, 180, 159), width=6)
    graves = ((424, 396, -8), (528, 386, 6), (648, 378, -10), (452, 486, 7), (584, 478, -6),
              (700, 470, 8))
    for x, y, tilt in graves:
        d.rectangle([x, y, x + 62, y + 14], fill=(185, 189, 180), outline=(150, 154, 144), width=3)
        off = tilt // 2
        d.polygon([(x + 12 + off, y), (x + 10, y - 52), (x + 52, y - 52), (x + 50 - off, y)],
                  fill=(205, 208, 199), outline=(150, 154, 144))
    # 倒れた花立てと枯れ花
    d.rounded_rectangle([600, 522, 646, 540], radius=6, fill=(169, 173, 163),
                        outline=(131, 135, 126), width=3)
    for dx, dy in ((0, -14), (6, -4), (10, 6)):
        d.line([(646 + dx, 528 + dy), (692 + dx, 512 + dy)], fill=(160, 138, 82), width=4)
    # 伸びた草
    for x in (404, 470, 556, 622, 712, 740):
        d.line([(x, 576), (x + 8, 534)], fill=(138, 165, 82), width=4)
    for x in (436, 512, 668):
        d.line([(x, 470), (x + 6, 436)], fill=(138, 165, 82), width=4)
    band(d, ["削られた墓は建て直され、", "誰も来ない墓は残る"], "森町ライフハック／寺社・歴史")


def scene_nagi(d):
    """標柱の立つ神木と、誰も測っていない庭の大木を並べた場面。"""
    sky(d)
    mountains(d)
    d.polygon([(0, 292), (760, 284), (760, 328), (0, 338)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 300 + i * 12), (760, 292 + i * 12)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 332), (760, 322), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    cedars(d, [8, 46, 712, 744], 332, h=48)
    # 左：社殿
    d.polygon([(14, 396), (100, 348), (186, 396)], fill=(107, 86, 67))
    d.polygon([(32, 396), (100, 356), (168, 396)], fill=(138, 113, 84))
    d.rectangle([8, 396, 192, 406], fill=(89, 72, 58))
    d.rectangle([32, 406, 168, 476], fill=(239, 231, 214), outline=(189, 180, 159), width=4)
    d.rectangle([44, 420, 60, 476], fill=(176, 60, 48))
    d.rectangle([140, 420, 156, 476], fill=(176, 60, 48))
    d.rectangle([68, 420, 132, 476], fill=(200, 189, 168), outline=(162, 151, 127), width=3)
    # ナギの大木
    d.polygon([(206, 520), (214, 384), (256, 384), (264, 520)], fill=(122, 98, 71))
    d.ellipse([132, 216, 340, 400], fill=(44, 92, 56))
    d.ellipse([112, 288, 236, 380], fill=(36, 76, 46))
    d.ellipse([238, 284, 356, 376], fill=(36, 76, 46))
    d.ellipse([148, 508, 324, 542], fill=(185, 199, 174))
    for x in (140, 190, 288, 336):
        d.line([(x, 540), (x, 500)], fill=(138, 122, 94), width=6)
    d.line([(136, 512), (340, 508)], fill=(138, 122, 94), width=6)
    d.rounded_rectangle([120, 546, 292, 580], radius=7, fill=(255, 255, 255),
                        outline=(62, 107, 85), width=3)
    d.text((132, 552), "県指定天然記念物", font=ImageFont.truetype(FONT_BOLD, 22), fill=(31, 62, 82))
    # 右：実家
    d.polygon([(396, 424), (486, 366), (576, 424)], fill=(111, 124, 130))
    d.polygon([(412, 424), (486, 376), (560, 424)], fill=(139, 151, 155))
    d.rectangle([412, 424, 560, 500], fill=(233, 227, 211), outline=(189, 180, 159), width=4)
    for x0 in (426, 500):
        d.rectangle([x0, 442, x0 + 48, 488], fill=(185, 172, 145), outline=(148, 138, 114), width=3)
        d.line([(x0 + 24, 442), (x0 + 24, 488)], fill=(148, 138, 114), width=3)
    # 電柱と電線
    d.line([(724, 520), (724, 320)], fill=(154, 163, 159), width=9)
    d.line([(696, 344), (752, 344)], fill=(154, 163, 159), width=6)
    d.line([(696, 348), (560, 366)], fill=(107, 117, 112), width=4)
    # 庭の大木
    d.polygon([(620, 528), (628, 404), (664, 404), (672, 528)], fill=(122, 98, 71))
    d.line([(630, 410), (556, 386)], fill=(122, 98, 71), width=8)
    d.line([(662, 408), (740, 380)], fill=(122, 98, 71), width=8)
    d.ellipse([516, 336, 660, 424], fill=(79, 124, 70))
    d.ellipse([648, 328, 760, 412], fill=(79, 124, 70))
    d.ellipse([572, 288, 716, 384], fill=(93, 139, 78))
    # 枯れ枝
    d.line([(668, 438), (740, 410)], fill=(156, 138, 106), width=5)
    d.line([(716, 420), (734, 400)], fill=(156, 138, 106), width=4)
    # 巻尺
    d.arc([604, 452, 690, 496], 0, 180, fill=(240, 216, 120), width=8)
    d.ellipse([692, 448, 730, 486], fill=(216, 137, 47), outline=(168, 104, 30), width=4)
    d.ellipse([704, 460, 718, 474], fill=(244, 231, 205))
    d.rounded_rectangle([440, 540, 728, 578], radius=8, fill=(255, 255, 255),
                        outline=(192, 86, 60), width=3)
    d.text((454, 548), "測った人は、まだいない", font=ImageFont.truetype(FONT_BOLD, 22),
           fill=(192, 86, 60))
    band(d, ["守られる木と、", "誰も測っていない木"], "森町ライフハック／寺社・歴史")


def scene_tanbo_lease(d):
    """他人が作っている実家の田と、空欄のままの契約書を並べた場面。"""
    sky(d)
    mountains(d)
    cedars(d, [12, 56, 100, 700, 744], 300)
    d.polygon([(0, 292), (760, 284), (760, 330), (0, 340)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 300 + i * 12), (760, 292 + i * 12)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 334), (760, 324), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    # 稲の育った田（奥）
    d.polygon([(0, 336), (760, 326), (760, 404), (0, 416)], fill=(156, 203, 105))
    for i in range(4):
        d.line([(0, 348 + i * 18), (760, 338 + i * 18)], fill=(101, 146, 69), width=5)
    # 畦
    d.polygon([(0, 416), (760, 404), (760, 428), (0, 440)], fill=(201, 192, 164))
    # 二枚目の田
    d.polygon([(0, 440), (760, 428), (760, 486), (0, 500)], fill=(140, 190, 92))
    for i in range(3):
        d.line([(0, 452 + i * 18), (760, 440 + i * 18)], fill=(94, 136, 64), width=5)
    # 他人の耕うん機
    d.polygon([(150, 350), (256, 344), (260, 388), (146, 394)], fill=(200, 80, 58))
    d.polygon([(252, 352), (300, 350), (306, 382), (256, 384)], fill=(226, 230, 226))
    d.rectangle([264, 358, 294, 376], fill=(182, 211, 224), outline=(138, 168, 182), width=3)
    d.line([(160, 346), (160, 316)], fill=(107, 115, 112), width=6)
    d.line([(160, 316), (198, 316)], fill=(107, 115, 112), width=6)
    d.ellipse([154, 372, 202, 420], fill=(75, 84, 80), outline=(47, 55, 51), width=5)
    d.ellipse([170, 388, 186, 404], fill=(168, 176, 172))
    d.ellipse([262, 380, 298, 416], fill=(75, 84, 80), outline=(47, 55, 51), width=5)
    d.ellipse([274, 392, 286, 404], fill=(168, 176, 172))
    d.ellipse([196, 306, 230, 340], fill=(227, 195, 157), outline=(185, 146, 107), width=3)
    d.polygon([(190, 310), (236, 310), (232, 300), (194, 300)], fill=(111, 124, 130))
    d.polygon([(200, 324), (226, 324), (232, 350), (194, 350)], fill=(63, 111, 134))
    # 字の消えた古い杭
    d.line([(600, 500), (600, 420)], fill=(155, 138, 108), width=13)
    d.rectangle([540, 424, 664, 456], fill=(243, 241, 230), outline=(168, 154, 124), width=3)
    for y in (436, 446):
        d.line([(554, y), (650 - (y - 436) * 3, y)], fill=(195, 184, 156), width=5)
    # 手前：縁側の卓と書類一式
    d.rectangle([0, 500, 760, BAND_TOP], fill=(201, 168, 119))
    for y in (516, 536, 556, 576):
        d.line([(0, y), (760, y)], fill=(177, 144, 95), width=3)
    d.rounded_rectangle([36, 486, 300, 588], radius=6, fill=(255, 255, 255),
                        outline=(138, 148, 154), width=4)
    d.rectangle([58, 504, 278, 522], fill=(223, 230, 233))
    for i in range(3):
        d.line([(58, 542 + i * 16), (278 - i * 26, 542 + i * 16)], fill=(198, 206, 210), width=5)
    d.rectangle([214, 552, 278, 580], fill=(253, 246, 230), outline=(192, 86, 60), width=3)
    d.polygon([(340, 588), (340, 512), (352, 496), (416, 496), (428, 512), (428, 588)],
              fill=(230, 221, 198), outline=(179, 166, 133))
    d.rectangle([358, 526, 410, 558], fill=(200, 162, 90))
    d.rounded_rectangle([460, 512, 578, 578], radius=5, fill=(63, 111, 134),
                        outline=(44, 84, 104), width=4)
    d.rectangle([474, 526, 546, 540], fill=(207, 224, 232))
    d.rectangle([474, 550, 528, 562], fill=(143, 178, 196))
    d.rounded_rectangle([612, 496, 728, 582], radius=5, fill=(246, 242, 228),
                        outline=(168, 154, 124), width=4)
    for y in (514, 532, 550):
        d.line([(626, y), (714, y)], fill=(195, 184, 156), width=3)
    d.line([(670, 496), (670, 582)], fill=(195, 184, 156), width=3)
    band(d, ["作っているのは親ではない。", "紙は、どこにもない"], "森町ライフハック／農地・山林・茶畑")


def scene_kokko_forest(d):
    """境界杭の立つ杉林と、崖と倒木で境界の分からない斜面を並べた場面。"""
    sky(d)
    mountains(d)
    d.polygon([(0, 288), (760, 280), (760, 322), (0, 332)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 296 + i * 12), (760, 288 + i * 12)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 326), (760, 316), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    # 左：手入れされた杉の人工林
    d.polygon([(0, 322), (368, 314), (356, 470), (0, 486)], fill=(126, 166, 96))
    for x, top in ((22, 250), (76, 262), (130, 246), (186, 264), (242, 250), (298, 266)):
        d.polygon([(x, 400), (x + 24, top), (x + 48, 400)], fill=(63, 107, 82))
        d.rectangle([x + 20, 398, x + 28, 424], fill=(107, 82, 56))
        d.rectangle([x + 17, 404, x + 31, 412], fill=(200, 80, 58))
    for x, top in ((48, 210), (160, 214), (272, 208)):
        d.polygon([(x, 300), (x + 20, top), (x + 40, 300)], fill=(52, 92, 70))
    # 境界杭
    for x, y in ((116, 452), (272, 442)):
        d.rectangle([x, y, x + 18, y + 46], fill=(246, 244, 236), outline=(168, 154, 124), width=4)
        d.line([(x + 3, y + 16), (x + 15, y + 16)], fill=(192, 86, 60), width=6)
    # 右：放置された斜面
    d.polygon([(388, 314), (760, 308), (760, 456), (396, 466)], fill=(125, 145, 105))
    for x, top in ((408, 268), (472, 282), (540, 262)):
        d.polygon([(x, 386), (x + 20, top), (x + 40, 386)], fill=(75, 107, 72))
    # 倒木
    d.line([(404, 412), (528, 388)], fill=(122, 98, 71), width=11)
    d.line([(452, 434), (566, 424)], fill=(122, 98, 71), width=11)
    d.line([(478, 392), (462, 370)], fill=(107, 82, 56), width=5)
    d.line([(508, 388), (524, 366)], fill=(107, 82, 56), width=5)
    # 笹
    for x in (398, 418, 438, 556, 578, 600, 622):
        d.line([(x, 462), (x + 7, 428)], fill=(95, 138, 66), width=5)
    # 崖
    d.polygon([(650, 320), (760, 312), (760, 462), (660, 456)], fill=(168, 154, 128))
    for y in (352, 390, 428):
        d.line([(664, y), (760, y - 6)], fill=(138, 125, 100), width=5)
    d.line([(650, 320), (660, 456)], fill=(192, 86, 60), width=6)
    # 林道と行き止まりの標識
    d.polygon([(0, 512), (760, 480), (760, 522), (0, 556)], fill=(201, 192, 164))
    for i in range(6):
        x = 40 + i * 130
        d.line([(x, 528 - i * 5), (x + 46, 526 - i * 5)], fill=(224, 217, 194), width=6)
    d.line([(560, 560), (560, 500)], fill=(154, 163, 159), width=8)
    d.rectangle([466, 464, 668, 500], fill=(255, 255, 255), outline=(192, 86, 60), width=3)
    d.text((480, 472), "この先 行き止まり", font=ImageFont.truetype(FONT_BOLD, 19), fill=(192, 86, 60))
    d.rectangle([20, 452, 242, 488], fill=(255, 255, 255), outline=(62, 107, 85), width=3)
    d.text((34, 460), "ここまで、と言える", font=ImageFont.truetype(FONT_BOLD, 19), fill=(31, 62, 82))
    band(d, ["国が見ているのは", "木の値段ではなく境界"], "森町ライフハック／農地・山林・茶畑")


def scene_august_grass(d):
    """草の伸びた畑と、刈り終えた空き地を並べた場面。"""
    # 夏の強い空
    for y in range(0, 300):
        t = y / 300
        d.line([(0, y), (S, y)], fill=(int(150 + 86 * t), int(196 + 38 * t), int(226 - 10 * t)))
    d.rectangle([0, 300, S, BAND_TOP], fill=(226, 236, 216))
    d.ellipse([46, 32, 142, 128], fill=(255, 214, 100))
    for cx, cy, r in ((520, 96, 44), (572, 70, 54), (628, 98, 42), (574, 122, 42)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
    mountains(d, 300)
    cedars(d, [14, 58, 706, 748], 300)
    d.polygon([(0, 292), (760, 284), (760, 326), (0, 336)], fill=(123, 169, 84))
    for i in range(3):
        d.line([(0, 300 + i * 12), (760, 292 + i * 12)], fill=(95, 138, 66), width=3)
    d.polygon([(0, 330), (760, 320), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 227, 200))
    # 左：草の伸びた畑
    d.polygon([(0, 326), (352, 318), (344, 540), (0, 560)], fill=(138, 165, 82))
    for i in range(11):
        x = 12 + i * 32
        d.line([(x, 546 - i), (x + 10, 424 - i)], fill=(109, 138, 60), width=7)
        d.line([(x + 16, 550), (x + 24, 452)], fill=(156, 184, 98), width=5)
    # 傾いた物置
    d.polygon([(196, 372), (268, 340), (340, 376), (336, 442), (200, 444)], fill=(207, 214, 210))
    d.polygon([(190, 374), (268, 336), (346, 376)], fill=(143, 154, 150))
    d.rectangle([236, 392, 288, 442], fill=(174, 183, 178), outline=(143, 154, 150), width=3)
    # 右：刈り終えた空き地
    d.polygon([(408, 318), (760, 312), (760, BAND_TOP), (400, BAND_TOP)], fill=(197, 207, 154))
    for i in range(4):
        d.line([(404, 366 + i * 46), (760, 358 + i * 46)], fill=(173, 184, 132), width=4)
    # 刈った草の山
    d.polygon([(430, 500), (452, 444), (494, 428), (536, 448), (556, 500)], fill=(168, 160, 78))
    d.line([(462, 492), (492, 448)], fill=(135, 127, 54), width=4)
    d.line([(516, 494), (536, 456)], fill=(135, 127, 54), width=4)
    # 軽トラック
    d.rectangle([588, 434, 692, 500], fill=(230, 234, 230), outline=(154, 163, 159), width=4)
    d.rectangle([692, 448, 752, 500], fill=(240, 243, 240), outline=(154, 163, 159), width=4)
    d.rectangle([702, 458, 742, 480], fill=(182, 211, 224), outline=(138, 168, 182), width=3)
    d.rounded_rectangle([600, 400, 640, 436], radius=6, fill=(200, 191, 126), outline=(162, 154, 95), width=3)
    d.rounded_rectangle([646, 406, 686, 436], radius=6, fill=(200, 191, 126), outline=(162, 154, 95), width=3)
    for cx in (624, 722):
        d.ellipse([cx - 20, 484, cx + 20, 524], fill=(75, 84, 80), outline=(47, 55, 51), width=5)
        d.ellipse([cx - 6, 498, cx + 6, 510], fill=(168, 176, 172))
    # 境の畦と刈払機
    d.polygon([(354, 320), (404, 318), (396, BAND_TOP), (338, BAND_TOP)], fill=(201, 192, 164))
    d.line([(370, 552), (382, 388)], fill=(107, 115, 112), width=9)
    d.ellipse([362, 366, 402, 406], fill=(200, 80, 58), outline=(150, 51, 31), width=4)
    d.line([(358, 456), (398, 448)], fill=(107, 115, 112), width=7)
    # 札
    d.rectangle([20, 336, 250, 372], fill=(255, 255, 255), outline=(192, 86, 60), width=3)
    d.text((36, 344), "八月のはじめ", font=ImageFont.truetype(FONT_BOLD, 21), fill=(192, 86, 60))
    d.rectangle([448, 336, 744, 372], fill=(255, 255, 255), outline=(62, 107, 85), width=3)
    d.text((462, 344), "刈り終えた同じ土地", font=ImageFont.truetype(FONT_BOLD, 21), fill=(31, 62, 82))
    band(d, ["刈っても月内に戻る。", "回数で決まる費用"], "森町ライフハック／農地・山林・茶畑")


def scene_license_return(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 104, 700, 742], 300)
    # 中景：段になった茶畑
    d.polygon([(0, 296), (760, 288), (760, 348), (0, 358)], fill=(139, 183, 95))
    for i in range(3):
        d.line([(0, 306 + i * 16), (760, 298 + i * 16)], fill=(93, 138, 62), width=3)
    d.polygon([(0, 352), (760, 342), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 226, 200))
    # 左：山あいの斜面と細い道
    d.polygon([(0, 352), (250, 344), (300, 404), (140, 436), (0, 420)], fill=(147, 176, 117))
    cedars(d, [24, 66, 108], 404, h=46, color=(66, 112, 90))
    d.polygon([(0, 470), (330, 440), (330, 486), (0, 520)], fill=(200, 195, 180))
    for x in range(10, 320, 56):
        d.line([(x, 500 - x // 12), (x + 30, 497 - x // 12)], fill=(255, 255, 255), width=5)
    # 左：小型の町営バス
    d.rounded_rectangle([120, 386, 300, 452], radius=9, fill=(244, 247, 243),
                        outline=(92, 111, 102), width=5)
    for x in (134, 186, 234):
        d.rectangle([x, 400, x + 42, 428], fill=(188, 220, 234), outline=(127, 165, 182), width=3)
    d.rectangle([128, 366, 236, 388], fill=(47, 107, 83))
    d.text((142, 369), "町営バス", font=ImageFont.truetype(FONT_BOLD, 17), fill="#ffffff")
    for cx in (158, 264):
        d.ellipse([cx - 19, 440, cx + 19, 478], fill=(75, 84, 80), outline=(47, 55, 51), width=5)
    # 左：バス停で待つ人
    d.rectangle([56, 400, 64, 520], fill=(143, 154, 150))
    d.ellipse([38, 372, 82, 416], fill=(255, 255, 255), outline=(47, 107, 83), width=5)
    d.ellipse([80, 462, 108, 490], fill=(232, 201, 168), outline=(185, 154, 124), width=3)
    d.polygon([(80, 470), (94, 452), (108, 470)], fill=(141, 143, 148))
    d.polygon([(78, 494), (110, 494), (114, 560), (74, 560)], fill=(179, 87, 123))
    # 右：瓦屋根の家と地域タクシー
    d.polygon([(596, 396), (664, 356), (732, 396), (732, 470), (596, 470)],
              fill=(239, 233, 220), outline=(167, 159, 140), width=4)
    d.polygon([(584, 400), (664, 350), (744, 400)], fill=(109, 122, 128))
    d.rectangle([632, 420, 692, 470], fill=(201, 180, 140), outline=(156, 135, 99), width=3)
    d.polygon([(392, 470), (420, 428), (536, 428), (564, 470), (564, 508), (392, 508)],
              fill=(63, 143, 106), outline=(44, 107, 78), width=5)
    d.rectangle([428, 436, 474, 464], fill=(207, 230, 240), outline=(127, 165, 182), width=3)
    d.rectangle([482, 436, 528, 464], fill=(207, 230, 240), outline=(127, 165, 182), width=3)
    d.rectangle([444, 404, 512, 430], fill=(255, 255, 255), outline=(44, 107, 78), width=3)
    d.text((456, 407), "TAXI", font=ImageFont.truetype(FONT_BOLD, 17), fill="#1f5d44")
    for cx in (434, 522):
        d.ellipse([cx - 20, 500, cx + 20, 540], fill=(75, 84, 80), outline=(47, 55, 51), width=5)
    # 中央：返した免許証を載せた小さな机
    d.rectangle([310, 526, 386, 534], fill=(156, 135, 99))
    d.rectangle([316, 534, 322, 560], fill=(156, 135, 99))
    d.rectangle([374, 534, 380, 560], fill=(156, 135, 99))
    d.rectangle([316, 496, 384, 526], fill=(243, 244, 239), outline=(143, 154, 150), width=3)
    d.rectangle([322, 502, 338, 518], fill=(198, 207, 201))
    d.line([(344, 506), (378, 506)], fill=(177, 187, 181), width=4)
    d.line([(344, 516), (366, 516)], fill=(177, 187, 181), width=4)
    # 札
    d.rectangle([20, 314, 262, 350], fill=(255, 255, 255), outline=(62, 107, 85), width=3)
    d.text((34, 322), "平日だけ来る路線", font=ImageFont.truetype(FONT_BOLD, 21), fill=(31, 62, 82))
    d.rectangle([424, 314, 744, 350], fill=(255, 255, 255), outline=(192, 86, 60), width=3)
    d.text((438, 322), "一宮・園田は1台500円", font=ImageFont.truetype(FONT_BOLD, 21), fill=(192, 86, 60))
    band(d, ["車を返した日に、", "その地区に残る足"], "森町ライフハック／地区めぐり")


def scene_bridge_plans(d):
    sky(d)
    mountains(d)
    cedars(d, [14, 58, 100, 704, 744], 300)
    # 中景：段になった茶畑
    d.polygon([(0, 296), (760, 288), (760, 344), (0, 354)], fill=(139, 183, 95))
    for i in range(3):
        d.line([(0, 304 + i * 15), (760, 296 + i * 15)], fill=(93, 138, 62), width=3)
    d.polygon([(0, 348), (760, 338), (760, BAND_TOP), (0, BAND_TOP)], fill=(214, 226, 200))
    # 右：山肌とトンネル坑口
    d.polygon([(520, 348), (640, 342), (760, 396), (760, 540), (556, 528)], fill=(157, 180, 135))
    d.polygon([(596, 470), (596, 424), (600, 412), (620, 402), (640, 412), (644, 424), (644, 470)],
              fill=(59, 69, 80))
    d.polygon([(588, 428), (592, 410), (608, 396), (632, 396), (648, 410), (652, 428)],
              fill=(198, 206, 197), outline=(152, 163, 150), width=4)
    # 対岸の家と蔵、ひび割れた細い道
    d.polygon([(392, 396), (444, 364), (496, 396), (496, 452), (392, 452)],
              fill=(239, 233, 220), outline=(167, 159, 140), width=4)
    d.polygon([(382, 400), (444, 358), (506, 400)], fill=(109, 122, 128))
    d.rectangle([420, 416, 466, 452], fill=(201, 180, 140), outline=(156, 135, 99), width=3)
    d.polygon([(330, 490), (596, 424), (612, 444), (352, 516)], fill=(200, 195, 180))
    for x0, y0 in ((376, 496), (426, 486), (476, 472), (526, 458)):
        d.line([(x0, y0 + 12), (x0 + 16, y0 - 6)], fill=(143, 138, 124), width=3)
        d.line([(x0 + 16, y0 - 6), (x0 + 30, y0 + 4)], fill=(143, 138, 124), width=3)
    # 川
    d.polygon([(0, 470), (140, 452), (300, 466), (420, 502), (420, BAND_TOP), (0, BAND_TOP)],
              fill=(140, 186, 212))
    d.line([(40, 512), (240, 500)], fill=(226, 238, 244), width=4)
    d.line([(80, 546), (280, 534)], fill=(226, 238, 244), width=4)
    # 一本だけの橋
    d.rectangle([94, 428, 372, 450], fill=(211, 215, 210), outline=(152, 161, 150), width=4)
    d.rectangle([94, 450, 372, 462], fill=(183, 189, 182))
    d.line([(120, 462), (120, 522)], fill=(152, 161, 150), width=8)
    d.line([(346, 462), (346, 508)], fill=(152, 161, 150), width=8)
    for x in (100, 168, 236, 304, 366):
        d.line([(x, 428), (x, 398)], fill=(143, 154, 150), width=5)
    d.line([(98, 401), (368, 401)], fill=(143, 154, 150), width=5)
    # 手前の河原
    d.polygon([(0, 502), (146, 510), (312, BAND_TOP), (0, BAND_TOP)], fill=(207, 201, 182))
    for cx, cy in ((48, 540), (104, 556), (156, 572)):
        d.ellipse([cx - 8, cy - 6, cx + 8, cy + 6], fill=(179, 172, 151))
    # 桁下を見上げる点検作業員
    d.ellipse([176, 496, 206, 526], fill=(232, 201, 168), outline=(185, 154, 124), width=3)
    d.polygon([(174, 504), (191, 486), (208, 504)], fill=(232, 163, 60))
    d.polygon([(174, 530), (208, 530), (212, BAND_TOP), (170, BAND_TOP)], fill=(77, 111, 140))
    # 札
    d.rectangle([18, 320, 268, 356], fill=(255, 255, 255), outline=(192, 86, 60), width=3)
    d.text((32, 328), "迂回路のない橋", font=ImageFont.truetype(FONT_BOLD, 21), fill=(192, 86, 60))
    d.rectangle([540, 320, 744, 356], fill=(255, 255, 255), outline=(31, 62, 82), width=3)
    d.text((554, 328), "トンネルは1本", font=ImageFont.truetype(FONT_BOLD, 21), fill=(31, 62, 82))
    band(d, ["実家へ渡る橋は、", "いつ誰が直すのか"], "森町ライフハック／地区めぐり")


def scene_kasanboko(d):
    # 夕暮れの空
    for y in range(0, 300):
        t = y / 300
        d.line([(0, y), (S, y)], fill=(int(238 - 6 * t), int(184 + 34 * t), int(126 + 76 * t)))
    d.rectangle([0, 300, S, BAND_TOP], fill=(226, 232, 210))
    d.ellipse([646, 46, 706, 106], fill=(244, 162, 89))
    mountains(d)
    cedars(d, [16, 60, 104, 700, 740], 300)
    # 中景：段になった茶畑
    d.polygon([(0, 296), (760, 288), (760, 340), (0, 350)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 302 + i * 14), (760, 294 + i * 14)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 344), (760, 334), (760, BAND_TOP), (0, BAND_TOP)], fill=(216, 220, 196))
    # 右：新盆の家
    d.polygon([(468, 396), (468, 520), (720, 520), (720, 396)],
              fill=(242, 236, 224), outline=(163, 153, 127), width=4)
    d.polygon([(452, 400), (594, 336), (736, 400)], fill=(106, 122, 128))
    d.rectangle([492, 424, 606, 502], fill=(231, 220, 196), outline=(176, 164, 136), width=3)
    d.rectangle([516, 442, 542, 490], fill=(138, 107, 70), outline=(107, 81, 51), width=3)
    d.rectangle([650, 434, 700, 520], fill=(201, 180, 140), outline=(156, 135, 99), width=3)
    # 軒の白提灯
    d.line([(676, 400), (676, 414)], fill=(123, 112, 90), width=3)
    d.ellipse([658, 414, 694, 456], fill=(253, 248, 234), outline=(201, 189, 160), width=3)
    # 門口のたいまつ
    d.polygon([(424, 552), (452, 552), (446, 512), (430, 512)], fill=(141, 122, 92))
    d.polygon([(438, 456), (420, 490), (428, 512), (448, 512), (456, 486)], fill=(240, 161, 60))
    d.polygon([(438, 476), (430, 496), (436, 508), (446, 506), (450, 490)], fill=(255, 224, 138))
    # 道
    d.polygon([(0, 560), (200, 528), (430, 508), (444, 546), (210, 566), (0, BAND_TOP)],
              fill=(205, 195, 168))
    # 盆車（提灯と太鼓）
    d.rectangle([206, 452, 348, 500], fill=(233, 220, 192), outline=(163, 145, 95), width=4)
    d.rectangle([206, 440, 348, 454], fill=(201, 176, 114))
    d.line([(220, 440), (220, 396)], fill=(141, 122, 76), width=5)
    d.line([(334, 440), (334, 396)], fill=(141, 122, 76), width=5)
    d.line([(220, 400), (334, 400)], fill=(141, 122, 76), width=5)
    for cx in (242, 278, 314):
        d.ellipse([cx - 12, 404, cx + 12, 436], fill=(253, 243, 216), outline=(201, 162, 74), width=3)
    d.ellipse([248, 452, 306, 500], fill=(184, 86, 58), outline=(138, 59, 38), width=4)
    d.ellipse([262, 462, 292, 490], fill=(240, 228, 203), outline=(201, 180, 140), width=3)
    d.ellipse([204, 496, 240, 532], fill=(106, 91, 69), outline=(70, 60, 45), width=4)
    d.ellipse([314, 496, 350, 532], fill=(106, 91, 69), outline=(70, 60, 45), width=4)
    # 盆車を曳く子ども
    d.ellipse([146, 470, 178, 502], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(144, 506), (180, 506), (184, BAND_TOP), (140, BAND_TOP)], fill=(216, 120, 94))
    d.line([(178, 516), (206, 506)], fill=(240, 210, 176), width=7)
    # 先頭の唐傘（笠鉾）と子ども
    d.line([(74, 500), (74, 336)], fill=(141, 122, 92), width=8)
    d.polygon([(10, 336), (24, 292), (124, 292), (138, 336)], fill=(192, 86, 60),
              outline=(143, 59, 38), width=4)
    for x0 in (20, 48, 76, 104):
        d.rectangle([x0, 336, x0 + 14, 336 + 42 + (x0 % 3) * 6], fill=(192, 86, 60))
    d.ellipse([64, 274, 84, 294], fill=(216, 161, 60), outline=(168, 118, 31), width=3)
    d.ellipse([58, 486, 90, 518], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(56, 522), (92, 522), (96, BAND_TOP), (52, BAND_TOP)], fill=(224, 192, 94))
    # 札
    d.rectangle([148, 306, 372, 344], fill=(255, 255, 255), outline=(192, 86, 60), width=3)
    d.text((162, 314), "笠鉾が先頭に立つ", font=ImageFont.truetype(FONT_BOLD, 21), fill=(192, 86, 60))
    d.rectangle([472, 306, 744, 344], fill=(255, 255, 255), outline=(31, 62, 82), width=3)
    d.text((486, 314), "新盆を迎える家へ", font=ImageFont.truetype(FONT_BOLD, 21), fill=(31, 62, 82))
    band(d, ["カサンボコは", "新盆の家で唱えられる"], "森町ライフハック／祭礼・イベント")


def scene_mori_matsuri_choice(d):
    # 夜空
    for y in range(0, 300):
        t = y / 300
        d.line([(0, y), (S, y)], fill=(int(29 + 32 * t), int(43 + 40 * t), int(69 + 48 * t)))
    d.rectangle([0, 300, S, BAND_TOP], fill=(74, 74, 68))
    d.ellipse([646, 40, 694, 88], fill=(246, 239, 208))
    for x, y in ((92, 48), (168, 30), (250, 62), (338, 38), (430, 70), (520, 34), (596, 116)):
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(244, 240, 220))
    # 遠景の山と茶畑
    d.polygon([(0, 216), (96, 160), (196, 214), (300, 156), (410, 214), (520, 158),
               (630, 214), (740, 162), (760, 190), (760, 240), (0, 240)], fill=(46, 64, 92))
    d.polygon([(0, 236), (760, 226), (760, 268), (0, 278)], fill=(58, 84, 80))
    d.line([(0, 250), (760, 240)], fill=(45, 67, 64), width=3)
    d.polygon([(0, 272), (760, 262), (760, BAND_TOP), (0, BAND_TOP)], fill=(74, 74, 68))
    # 道
    d.polygon([(0, 500), (760, 440), (760, BAND_TOP), (0, BAND_TOP)], fill=(93, 91, 80))
    # 左：町家と土蔵
    d.rectangle([10, 300, 108, 424], fill=(63, 74, 82), outline=(42, 51, 58), width=4)
    d.polygon([(0, 304), (59, 268), (118, 304)], fill=(51, 60, 68))
    for x0 in (24, 54, 84):
        d.rectangle([x0, 330, x0 + 18, 380], fill=(200, 163, 90))
    # 屋台（御所車型・提灯つき）
    d.polygon([(196, 292), (306, 244), (416, 292)], fill=(122, 59, 44), outline=(92, 42, 30), width=4)
    d.rectangle([214, 292, 398, 302], fill=(92, 42, 30))
    d.rectangle([220, 302, 392, 400], fill=(139, 74, 52), outline=(92, 42, 30), width=4)
    d.rectangle([234, 318, 378, 372], fill=(201, 162, 74), outline=(160, 127, 44), width=3)
    d.line([(192, 276), (420, 276)], fill=(107, 90, 58), width=4)
    for cx, cy in ((206, 292), (250, 274), (306, 266), (362, 274), (406, 292)):
        d.ellipse([cx - 12, cy - 15, cx + 12, cy + 15], fill=(255, 233, 174), outline=(201, 162, 74), width=3)
    # 囃子の奏者
    d.ellipse([250, 326, 274, 350], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(248, 356), (276, 356), (278, 372), (246, 372)], fill=(47, 95, 122))
    d.ellipse([288, 330, 324, 366], fill=(184, 86, 58), outline=(138, 59, 38), width=3)
    d.ellipse([298, 340, 314, 356], fill=(240, 228, 203))
    d.ellipse([340, 326, 364, 350], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(338, 356), (366, 356), (368, 372), (336, 372)], fill=(47, 95, 122))
    # 二輪
    for cx in (256, 356):
        d.ellipse([cx - 30, 396, cx + 30, 456], fill=(90, 75, 56), outline=(51, 42, 30), width=5)
        d.ellipse([cx - 10, 416, cx + 10, 436], fill=(141, 122, 85))
    # 綱を引く人
    d.line([(220, 384), (150, 414)], fill=(216, 203, 168), width=6)
    d.ellipse([128, 400, 156, 428], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(126, 434), (158, 434), (162, 500), (122, 500)], fill=(43, 74, 107))
    # 肩車された舞児
    d.ellipse([438, 372, 468, 402], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(434, 408), (472, 408), (476, 486), (430, 486)], fill=(60, 95, 67))
    d.ellipse([440, 330, 466, 356], fill=(246, 220, 188), outline=(194, 161, 129), width=3)
    d.polygon([(438, 336), (453, 318), (468, 336)], fill=(184, 86, 58))
    d.polygon([(440, 360), (466, 360), (468, 396), (438, 396)], fill=(216, 165, 184))
    # 右：雨戸を閉めた空き家
    d.rectangle([560, 322, 720, 460], fill=(74, 81, 88), outline=(47, 53, 59), width=4)
    d.polygon([(546, 326), (640, 274), (734, 326)], fill=(51, 60, 68))
    d.rectangle([586, 354, 694, 424], fill=(92, 97, 105), outline=(61, 67, 74), width=3)
    for x0 in (612, 640, 668):
        d.line([(x0, 354), (x0, 424)], fill=(61, 67, 74), width=3)
    for x0, y0 in ((548, 500), (566, 502), (726, 498), (744, 502)):
        d.line([(x0, y0), (x0 - 3, y0 - 36)], fill=(95, 123, 61), width=4)
    # 掲示板
    d.rectangle([470, 300, 546, 358], fill=(233, 228, 210), outline=(141, 131, 104), width=4)
    d.line([(482, 372), (482, 300)], fill=(107, 95, 74), width=6)
    d.line([(534, 372), (534, 300)], fill=(107, 95, 74), width=6)
    for y0 in (312, 320, 336, 344):
        d.line([(480, y0), (536, y0)], fill=(164, 154, 128), width=2)
    band(d, ["十一月の祭りは、", "八月から動き出す"], "森町ライフハック／祭礼・イベント")


def scene_children_roles(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 104, 656, 700, 744], 300)
    # 中景：段になった茶畑
    d.polygon([(0, 296), (760, 288), (760, 336), (0, 346)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 302 + i * 13), (760, 294 + i * 13)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 340), (760, 330), (760, BAND_TOP), (0, BAND_TOP)], fill=(221, 227, 210))
    # 社殿
    d.rectangle([236, 320, 524, 366], fill=(232, 224, 204), outline=(169, 154, 120), width=4)
    d.polygon([(212, 324), (380, 268), (548, 324)], fill=(106, 122, 128))
    d.rectangle([212, 324, 548, 336], fill=(85, 101, 107))
    # 舟形の舞台
    d.polygon([(148, 546), (612, 546), (612, 406), (148, 406)],
              fill=(229, 217, 189), outline=(163, 145, 95), width=5)
    d.rectangle([148, 406, 612, 422], fill=(201, 176, 114))
    d.line([(148, 452), (612, 452)], fill=(163, 145, 95), width=6)
    d.rectangle([288, 462, 472, 504], fill=(244, 238, 218), outline=(200, 186, 144), width=3)
    # 三本の柱
    for x in (206, 380, 554):
        d.line([(x, 406), (x, 300)], fill=(141, 122, 76), width=12)
    # 神紋幕
    d.rectangle([392, 300, 578, 352], fill=(63, 86, 116))
    for cx in (428, 478, 528):
        d.ellipse([cx - 8, 318, cx + 8, 334], fill=(230, 236, 242))
    # 蟷螂を舞う子ども
    d.polygon([(330, 432), (300, 420), (292, 444), (318, 452)], fill=(127, 168, 90))
    d.polygon([(430, 432), (460, 420), (468, 444), (442, 452)], fill=(127, 168, 90))
    d.ellipse([352, 380, 408, 436], fill=(143, 180, 95), outline=(92, 127, 60), width=4)
    d.ellipse([364, 396, 376, 408], fill=(51, 66, 31))
    d.ellipse([384, 396, 396, 408], fill=(51, 66, 31))
    d.line([(364, 380), (352, 356)], fill=(92, 127, 60), width=4)
    d.line([(396, 380), (408, 356)], fill=(92, 127, 60), width=4)
    d.polygon([(354, 436), (406, 436), (410, 516), (350, 516)], fill=(216, 165, 184))
    d.line([(348, 452), (312, 468)], fill=(240, 210, 176), width=8)
    d.line([(412, 452), (448, 468)], fill=(240, 210, 176), width=8)
    # 鼓の奏者（左右）
    for cx, flip in ((196, 1), (566, -1)):
        d.ellipse([cx - 14, 462, cx + 14, 490], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
        d.polygon([(cx - 16, 496), (cx + 16, 496), (cx + 18, 546), (cx - 18, 546)], fill=(122, 91, 140))
        d.polygon([(cx + flip * 26, 486), (cx + flip * 44, 494), (cx + flip * 44, 514), (cx + flip * 26, 522)],
                  fill=(184, 86, 58), outline=(138, 59, 38), width=3)
    # 教える大人
    d.ellipse([56, 424, 92, 460], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(52, 466), (96, 466), (102, BAND_TOP), (46, BAND_TOP)], fill=(184, 132, 94))
    d.line([(98, 482), (142, 462)], fill=(240, 210, 176), width=9)
    # 空いた座布団
    for x0 in (626, 686):
        d.rectangle([x0, 500, x0 + 52, 532], fill=(201, 205, 189), outline=(167, 171, 153), width=3)
    band(d, ["囃子とお舞の役は、", "子どもに回る"], "森町ライフハック／祭礼・イベント")


def scene_marriage_subsidy(d):
    sky(d)
    mountains(d)
    cedars(d, [18, 62, 106, 650, 694, 738], 300)
    # 中景：段になった茶畑と集落
    d.polygon([(0, 294), (760, 286), (760, 334), (0, 344)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 300 + i * 13), (760, 292 + i * 13)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 338), (760, 328), (760, BAND_TOP), (0, BAND_TOP)], fill=(224, 230, 213))
    # 窓の外の家並みと生け垣
    for x, w in ((30, 96), (150, 78)):
        d.rectangle([x, 346, x + w, 386], fill=(238, 232, 218))
        d.polygon([(x - 8, 348), (x + w // 2, 320), (x + w + 8, 348)], fill=(133, 148, 156))
    d.polygon([(20, 388), (250, 380), (250, 402), (20, 410)], fill=(111, 154, 88))
    # 窓の外の小型トラック（荷物を積む）
    d.rectangle([272, 348, 366, 400], fill=(241, 244, 242), outline=(147, 160, 166), width=4)
    d.polygon([(272, 348), (272, 400), (238, 400), (238, 366), (254, 348)],
              fill=(226, 232, 232), outline=(147, 160, 166), width=4)
    d.rectangle([244, 362, 268, 380], fill=(184, 214, 228), outline=(138, 169, 184), width=3)
    for cx in (268, 348):
        d.ellipse([cx - 14, 390, cx + 14, 418], fill=(64, 74, 82), outline=(35, 43, 49), width=3)
    # 窓枠
    d.rectangle([12, 306, 384, 424], fill=None, outline=(160, 152, 130), width=8)
    d.line([(198, 306), (198, 424)], fill=(160, 152, 130), width=6)
    # 壁と暦
    d.rectangle([404, 300, 748, 430], fill=(240, 236, 222), outline=(174, 165, 141), width=5)
    d.rectangle([404, 300, 748, 330], fill=(31, 62, 82))
    f = ImageFont.truetype(FONT_BOLD, 24)
    d.text((432, 305), "7月1日 → 2月26日", font=f, fill="#ffffff")
    for i in range(3):
        d.line([(404, 356 + i * 26), (748, 356 + i * 26)], fill=(203, 196, 174), width=3)
    for i in range(5):
        d.line([(404 + (i + 1) * 57, 330), (404 + (i + 1) * 57, 430)], fill=(203, 196, 174), width=3)
    d.ellipse([424, 336, 456, 368], outline=(192, 86, 60), width=6)
    d.ellipse([692, 388, 724, 420], outline=(192, 86, 60), width=6)
    # 窓口のカウンター
    d.rectangle([0, 486, 760, 520], fill=(185, 143, 93))
    d.rectangle([0, 520, 760, 534], fill=(158, 118, 72))
    # カウンター越しの職員（暦を指す）
    d.ellipse([586, 396, 630, 440], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([586, 388, 630, 432], 180, 360, fill=(72, 62, 52))
    d.polygon([(578, 446), (638, 446), (648, 486), (568, 486)], fill=(96, 134, 168))
    d.line([(582, 456), (536, 424)], fill=(240, 210, 176), width=10)
    # 手前の夫婦（後ろ姿・紙ばさみを抱える）
    for cx, body in ((172, (196, 127, 146)), (300, (135, 164, 95))):
        d.ellipse([cx - 24, 396, cx + 24, 444], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
        d.chord([cx - 24, 388, cx + 24, 436], 180, 360, fill=(64, 54, 44))
        d.polygon([(cx - 32, 450), (cx + 32, 450), (cx + 42, 486), (cx - 42, 486)], fill=body)
    d.rectangle([206, 442, 268, 490], fill=(253, 251, 242), outline=(178, 170, 150), width=4)
    for y0 in (456, 468, 480):
        d.line([(216, y0), (258, y0)], fill=(196, 189, 166), width=3)
    # カウンター上の書類・印鑑・通帳
    d.rectangle([372, 446, 470, 486], fill=(255, 255, 255), outline=(152, 162, 168), width=3)
    d.rectangle([382, 436, 480, 476], fill=(246, 248, 247), outline=(152, 162, 168), width=3)
    for y0 in (450, 462):
        d.line([(394, y0), (466, y0)], fill=(184, 193, 198), width=3)
    d.rectangle([496, 452, 560, 486], fill=(253, 243, 216), outline=(196, 173, 106), width=3)
    d.line([(508, 468), (548, 468)], fill=(196, 173, 106), width=3)
    d.rectangle([664, 452, 700, 486], fill=(141, 95, 67), outline=(107, 70, 48), width=3)
    d.ellipse([666, 434, 698, 462], fill=(192, 86, 60), outline=(143, 59, 40), width=3)
    d.rectangle([708, 462, 756, 486], fill=(95, 134, 168), outline=(63, 102, 132), width=3)
    band(d, ["新生活の補助は、", "七月から二月で閉じる"], "森町ライフハック／移住・暮らし・データ")


def scene_moving_in_timing(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 104, 650, 694, 738], 300)
    # 中景：段になった茶畑
    d.polygon([(0, 292), (760, 284), (760, 332), (0, 342)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 298 + i * 13), (760, 290 + i * 13)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 336), (760, 326), (760, BAND_TOP), (0, BAND_TOP)], fill=(224, 230, 213))
    # 校庭
    d.polygon([(0, 372), (760, 360), (760, 470), (0, 484)], fill=(216, 206, 172))
    # 校舎（奥）
    d.rectangle([28, 344, 402, 452], fill=(242, 239, 228), outline=(164, 154, 128), width=4)
    d.rectangle([16, 330, 414, 348], fill=(124, 138, 144))
    for x in (48, 112, 176, 240, 304):
        d.rectangle([x, 362, x + 46, 392], fill=(188, 220, 234), outline=(127, 165, 182), width=3)
    for x in (48, 112, 176):
        d.rectangle([x, 408, x + 46, 444], fill=(188, 220, 234), outline=(127, 165, 182), width=3)
    d.rectangle([248, 404, 396, 452], fill=(253, 247, 230), outline=(193, 168, 106), width=4)
    # ランドセルの児童（校庭）
    for cx, body, sack in ((452, (95, 134, 168), (192, 86, 60)), (528, (135, 164, 95), (63, 102, 132))):
        d.ellipse([cx - 17, 384, cx + 17, 418], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
        d.polygon([(cx - 22, 424), (cx + 22, 424), (cx + 28, 486), (cx - 28, 486)], fill=body)
        d.rectangle([cx - 44, 430, cx - 22, 466], fill=sack)
    # 保育園（右奥）
    d.rectangle([590, 404, 750, 470], fill=(246, 239, 224), outline=(184, 166, 124), width=4)
    d.polygon([(576, 408), (670, 376), (764, 408)], fill=(192, 122, 94))
    for x in (606, 668):
        d.rectangle([x, 420, x + 40, 450], fill=(188, 220, 234), outline=(127, 165, 182), width=3)
    d.ellipse([716, 464, 742, 490], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.polygon([(714, 496), (744, 496), (748, 528), (710, 528)], fill=(226, 160, 180))
    # 手前：窓口のカウンター
    d.rectangle([0, 500, 760, 534], fill=(185, 143, 93))
    d.rectangle([0, 534, 760, 548], fill=(158, 118, 72))
    # 掲示（九月と四月の二枚）
    f = ImageFont.truetype(FONT_BOLD, 26)
    d.rectangle([406, 306, 596, 372], fill=(255, 255, 255), outline=(31, 62, 82), width=5)
    d.text((424, 322), "9月14日", font=f, fill="#c0563c")
    d.rectangle([604, 306, 748, 372], fill=(255, 255, 255), outline=(31, 62, 82), width=5)
    d.text((626, 322), "4月", font=f, fill="#3f6684")
    d.line([(596, 338), (604, 338)], fill=(31, 62, 82), width=5)
    # 掲示を指す職員
    d.ellipse([610, 400, 654, 444], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([610, 392, 654, 436], 180, 360, fill=(72, 62, 52))
    d.polygon([(602, 450), (662, 450), (672, 500), (592, 500)], fill=(96, 134, 168))
    d.line([(606, 460), (566, 386)], fill=(240, 210, 176), width=10)
    # 手前の家族（後ろ姿・親二人と子ども一人）
    for cx, body, r in ((110, (196, 127, 146), 24), (240, (135, 164, 95), 24), (346, (95, 134, 168), 17)):
        d.ellipse([cx - r, 424 - r + 12, cx + r, 424 + r + 12], fill=(240, 210, 176),
                  outline=(194, 161, 129), width=3)
        d.chord([cx - r, 428 - r, cx + r, 428 + r], 180, 360, fill=(64, 54, 44))
        d.polygon([(cx - r - 10, 466), (cx + r + 10, 466), (cx + r + 18, 500), (cx - r - 18, 500)],
                  fill=body)
    # カウンター上の申込書
    d.rectangle([146, 456, 260, 500], fill=(253, 251, 242), outline=(178, 170, 150), width=4)
    for y0 in (470, 482, 494):
        d.line([(158, y0), (248, y0)], fill=(196, 189, 166), width=3)
    d.rectangle([282, 462, 384, 500], fill=(253, 243, 216), outline=(196, 173, 106), width=4)
    d.line([(294, 480), (368, 480)], fill=(196, 173, 106), width=3)
    band(d, ["四月の入園と入学は、", "九月の申込みで決まる"], "森町ライフハック／移住・暮らし・データ")


def scene_heir_representative(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 104, 646, 692, 736], 300)
    # 中景：段になった茶畑と家並み
    d.polygon([(0, 292), (760, 284), (760, 330), (0, 340)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 298 + i * 13), (760, 290 + i * 13)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 334), (760, 324), (760, BAND_TOP), (0, BAND_TOP)], fill=(224, 230, 213))
    for x, w in ((26, 92), (140, 74), (620, 96)):
        d.rectangle([x, 342, x + w, 380], fill=(238, 232, 218))
        d.polygon([(x - 8, 344), (x + w // 2, 316), (x + w + 8, 344)], fill=(133, 148, 156))
    d.polygon([(0, 384), (760, 374), (760, 398), (0, 408)], fill=(111, 154, 88))
    # 庭の柿の木
    d.rectangle([672, 356, 686, 424], fill=(138, 106, 72))
    d.ellipse([626, 296, 732, 384], fill=(95, 140, 76))
    for cx, cy in ((650, 330), (700, 316), (712, 356)):
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(224, 138, 60), outline=(181, 106, 38), width=2)
    # 左：門柱と郵便受け（封筒が差さったまま）
    d.rectangle([14, 356, 44, 496], fill=(185, 178, 161), outline=(141, 136, 120), width=4)
    d.rectangle([46, 386, 122, 434], fill=(95, 123, 140), outline=(63, 87, 104), width=4)
    d.rectangle([54, 404, 114, 412], fill=(47, 68, 83))
    for i, y0 in enumerate((360, 350, 340)):
        d.rectangle([58 + i * 10, y0, 110 + i * 10, y0 + 26], fill=(253, 251, 242),
                    outline=(168, 155, 124), width=3)
    # 座敷の床と縁側
    d.rectangle([0, 468, 760, 486], fill=(201, 168, 119))
    d.rectangle([0, 486, 760, BAND_TOP], fill=(221, 201, 164))
    for y0 in (512, 550):
        d.line([(0, y0), (760, y0)], fill=(196, 171, 132), width=3)
    # 座卓と書類
    d.rectangle([206, 494, 546, 520], fill=(185, 143, 93))
    d.rectangle([206, 520, 546, 532], fill=(156, 118, 72))
    d.rectangle([234, 460, 348, 498], fill=(255, 255, 255), outline=(152, 162, 168), width=3)
    d.rectangle([242, 448, 356, 486], fill=(246, 248, 247), outline=(152, 162, 168), width=3)
    d.rectangle([242, 448, 356, 462], fill=(31, 62, 82))
    for y0 in (470, 480):
        d.line([(254, y0), (344, y0)], fill=(184, 193, 198), width=3)
    d.rectangle([378, 446, 476, 498], fill=(253, 251, 242), outline=(168, 155, 124), width=3)
    for y0 in (460, 472, 484):
        d.line([(388, y0), (466, y0)], fill=(207, 197, 168), width=3)
    d.line([(424, 446), (424, 498)], fill=(207, 197, 168), width=3)
    d.rectangle([494, 452, 540, 498], fill=(233, 226, 205), outline=(168, 155, 124), width=3)
    d.rectangle([494, 452, 506, 498], fill=(141, 95, 67))
    d.rectangle([486, 502, 504, 534], fill=(141, 95, 67), outline=(107, 70, 48), width=3)
    d.ellipse([518, 500, 542, 524], fill=(192, 86, 60), outline=(143, 59, 40), width=3)
    # 通知書を指す人・封筒の束を抱える人
    d.ellipse([146, 424, 194, 472], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([146, 416, 194, 464], 180, 360, fill=(75, 66, 56))
    d.polygon([(138, 478), (202, 478), (212, BAND_TOP), (128, BAND_TOP)], fill=(92, 134, 160))
    d.line([(200, 490), (240, 476)], fill=(240, 210, 176), width=10)
    d.ellipse([566, 418, 614, 466], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([566, 410, 614, 458], 180, 360, fill=(87, 73, 60))
    d.polygon([(558, 472), (622, 472), (632, BAND_TOP), (548, BAND_TOP)], fill=(160, 106, 124))
    d.rectangle([540, 486, 606, 522], fill=(253, 251, 242), outline=(168, 155, 124), width=3)
    d.line([(540, 486), (573, 506)], fill=(168, 155, 124), width=3)
    d.line([(573, 506), (606, 486)], fill=(168, 155, 124), width=3)
    # 壁の暦（八月と十一月二日）
    f = ImageFont.truetype(FONT_BOLD, 22)
    d.rectangle([222, 336, 358, 424], fill=(253, 251, 242), outline=(141, 131, 104), width=4)
    d.rectangle([222, 336, 358, 364], fill=(31, 62, 82))
    d.text((272, 340), "8月", font=f, fill="#ffffff")
    for i in range(2):
        d.line([(222, 386 + i * 20), (358, 386 + i * 20)], fill=(195, 189, 166), width=3)
    d.rectangle([378, 336, 514, 424], fill=(253, 251, 242), outline=(141, 131, 104), width=4)
    d.rectangle([378, 336, 514, 364], fill=(125, 63, 44))
    d.text((394, 340), "11月2日", font=f, fill="#ffffff")
    for i in range(2):
        d.line([(378, 386 + i * 20), (514, 386 + i * 20)], fill=(195, 189, 166), width=3)
    d.ellipse([396, 382, 424, 410], outline=(192, 86, 60), width=6)
    band(d, ["通知書は、", "誰の家に届くのか"], "森町ライフハック／手続き・制度")


def scene_insurance_care_papers(d):
    sky(d)
    mountains(d)
    cedars(d, [14, 58, 102, 652, 698, 742], 300)
    # 中景：茶畑と家並み
    d.polygon([(0, 292), (760, 284), (760, 328), (0, 338)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 298 + i * 12), (760, 290 + i * 12)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 332), (760, 322), (760, BAND_TOP), (0, BAND_TOP)], fill=(224, 230, 213))
    for x, w in ((22, 88), (132, 70), (600, 92)):
        d.rectangle([x, 340, x + w, 376], fill=(238, 232, 218))
        d.polygon([(x - 8, 342), (x + w // 2, 316), (x + w + 8, 342)], fill=(133, 148, 156))
    d.polygon([(0, 380), (760, 370), (760, 394), (0, 404)], fill=(111, 154, 88))
    # 庭の木
    d.rectangle([676, 352, 690, 420], fill=(138, 106, 72))
    d.ellipse([636, 300, 730, 380], fill=(95, 140, 76))
    # 畳と座卓
    d.rectangle([0, 452, S, 470], fill=(201, 168, 119))
    d.rectangle([0, 470, S, BAND_TOP], fill=(221, 201, 164))
    d.line([(0, 528), (S, 528)], fill=(196, 171, 132), width=3)
    d.rectangle([116, 470, 656, 500], fill=(185, 143, 93))
    d.rectangle([116, 500, 656, 512], fill=(156, 118, 72))
    # 卓上：橙色（期限切れ）と藤色（新しい）の資格確認書
    d.rounded_rectangle([148, 396, 268, 468], radius=8, fill=(224, 138, 60),
                        outline=(181, 106, 38), width=4)
    d.rectangle([160, 408, 256, 420], fill=(244, 196, 143))
    d.line([(148, 396), (268, 468)], fill=(143, 74, 28), width=4)
    d.rounded_rectangle([292, 396, 412, 468], radius=8, fill=(176, 163, 212),
                        outline=(127, 112, 171), width=4)
    d.rectangle([304, 408, 400, 420], fill=(215, 207, 233))
    # 卓上：ピンクの介護保険被保険者証と割合の紙
    d.rectangle([438, 408, 528, 468], fill=(242, 195, 208), outline=(201, 141, 160), width=4)
    for y0 in (426, 442):
        d.line([(450, y0), (516, y0)], fill=(215, 159, 176), width=3)
    d.rectangle([550, 414, 620, 468], fill=(253, 251, 242), outline=(168, 155, 124), width=3)
    for y0 in (430, 444):
        d.line([(560, y0), (610, y0)], fill=(207, 197, 168), width=3)
    # 卓上：眼鏡と診察券
    d.ellipse([636, 428, 668, 460], outline=(75, 66, 56), width=4)
    d.ellipse([672, 428, 704, 460], outline=(75, 66, 56), width=4)
    d.line([(668, 444), (672, 444)], fill=(75, 66, 56), width=4)
    d.rectangle([44, 424, 106, 456], fill=(255, 255, 255), outline=(152, 162, 168), width=3)
    d.rectangle([54, 414, 116, 446], fill=(246, 248, 247), outline=(152, 162, 168), width=3)
    # 壁の暦（八月一日に丸）
    f = ImageFont.truetype(FONT_BOLD, 24)
    d.rectangle([176, 300, 352, 392], fill=(253, 251, 242), outline=(141, 131, 104), width=4)
    d.rectangle([176, 300, 352, 332], fill=(31, 62, 82))
    d.text((240, 304), "8月", font=f, fill="#ffffff")
    for i in range(2):
        d.line([(176, 354 + i * 20), (352, 354 + i * 20)], fill=(195, 189, 166), width=3)
    d.ellipse([190, 336, 220, 366], outline=(192, 86, 60), width=6)
    d.rectangle([382, 300, 610, 340], fill=(255, 255, 255), outline=(125, 63, 44), width=4)
    d.text((398, 306), "橙 → 藤いろ", font=ImageFont.truetype(FONT_BOLD, 26), fill=(125, 63, 44))
    # 紙を見比べる子
    d.ellipse([50, 336, 106, 392], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([50, 326, 106, 382], 180, 360, fill=(75, 66, 56))
    d.polygon([(38, 400), (118, 400), (130, 470), (26, 470)], fill=(92, 134, 160))
    # 封筒の束を出す親
    d.ellipse([648, 344, 704, 400], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([648, 334, 704, 390], 180, 360, fill=(185, 178, 161))
    d.polygon([(636, 408), (716, 408), (728, 470), (624, 470)], fill=(140, 154, 110))
    d.rectangle([690, 416, 756, 452], fill=(253, 251, 242), outline=(168, 155, 124), width=3)
    d.line([(690, 416), (723, 436)], fill=(168, 155, 124), width=3)
    d.line([(723, 436), (756, 416)], fill=(168, 155, 124), width=3)
    band(d, ["八月一日で、", "親の紙は入れ替わる"], "森町ライフハック／手続き・制度")


def scene_nationwide_record(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 104, 646, 692, 736], 300)
    # 中景：段になった茶畑と家並み
    d.polygon([(0, 292), (760, 284), (760, 330), (0, 340)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 298 + i * 13), (760, 290 + i * 13)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 334), (760, 324), (760, BAND_TOP), (0, BAND_TOP)], fill=(224, 230, 213))
    for x, w in ((22, 88), (132, 72), (628, 92)):
        d.rectangle([x, 342, x + w, 380], fill=(238, 232, 218))
        d.polygon([(x - 8, 344), (x + w // 2, 316), (x + w + 8, 344)], fill=(133, 148, 156))
    d.polygon([(0, 384), (760, 374), (760, 398), (0, 408)], fill=(111, 154, 88))
    # 庭の柿の木
    d.rectangle([678, 356, 692, 424], fill=(138, 106, 72))
    d.ellipse([632, 296, 738, 384], fill=(95, 140, 76))
    for cx, cy in ((656, 330), (706, 316), (718, 356)):
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(224, 138, 60), outline=(181, 106, 38), width=2)
    # 座敷の床と縁側
    d.rectangle([0, 468, 760, 486], fill=(201, 168, 119))
    d.rectangle([0, 486, 760, BAND_TOP], fill=(221, 201, 164))
    for y0 in (512, 550):
        d.line([(0, y0), (760, y0)], fill=(196, 171, 132), width=3)
    # 座卓
    d.rectangle([182, 494, 574, 520], fill=(185, 143, 93))
    d.rectangle([182, 520, 574, 532], fill=(156, 118, 72))
    # 広げた日本地図
    d.rectangle([206, 414, 462, 500], fill=(246, 242, 226), outline=(168, 155, 124), width=4)
    d.line([(222, 476), (262, 458)], fill=(159, 188, 208), width=4)
    d.line([(262, 458), (306, 470)], fill=(159, 188, 208), width=4)
    d.line([(306, 470), (352, 452)], fill=(159, 188, 208), width=4)
    d.line([(352, 452), (400, 464)], fill=(159, 188, 208), width=4)
    d.line([(400, 464), (446, 450)], fill=(159, 188, 208), width=4)
    d.line([(214, 492), (268, 484)], fill=(201, 191, 162), width=4)
    d.line([(268, 484), (330, 492)], fill=(201, 191, 162), width=4)
    d.line([(330, 492), (400, 482)], fill=(201, 191, 162), width=4)
    d.line([(400, 482), (452, 490)], fill=(201, 191, 162), width=4)
    # 森町の旗（緑）と町外の旗（赤）
    d.rectangle([302, 440, 306, 470], fill=(90, 74, 52))
    d.polygon([(306, 440), (340, 447), (306, 454)], fill=(63, 127, 76))
    d.rectangle([242, 430, 246, 458], fill=(90, 74, 52))
    d.polygon([(246, 430), (276, 437), (246, 444)], fill=(192, 86, 60))
    d.rectangle([400, 446, 404, 474], fill=(90, 74, 52))
    d.polygon([(404, 446), (434, 453), (404, 460)], fill=(192, 86, 60))
    # 名寄帳の綴りと全国分の証明書
    d.rectangle([484, 442, 560, 500], fill=(233, 226, 205), outline=(168, 155, 124), width=3)
    d.rectangle([484, 442, 498, 500], fill=(141, 95, 67))
    for y0 in (460, 474, 488):
        d.line([(508, y0), (550, y0)], fill=(193, 182, 150), width=3)
    d.rectangle([478, 392, 596, 440], fill=(255, 255, 255), outline=(152, 162, 168), width=3)
    d.rectangle([478, 392, 596, 408], fill=(31, 62, 82))
    for y0 in (418, 430):
        d.line([(490, y0), (584, y0)], fill=(184, 193, 198), width=3)
    # 地図をたどる人
    d.ellipse([120, 424, 168, 472], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([120, 416, 168, 464], 180, 360, fill=(75, 66, 56))
    d.polygon([(112, 478), (176, 478), (186, BAND_TOP), (102, BAND_TOP)], fill=(92, 134, 160))
    d.line([(174, 490), (214, 470)], fill=(240, 210, 176), width=10)
    # 綴りをめくる人
    d.ellipse([600, 420, 648, 468], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([600, 412, 648, 460], 180, 360, fill=(87, 73, 60))
    d.polygon([(592, 474), (656, 474), (666, BAND_TOP), (582, BAND_TOP)], fill=(160, 106, 124))
    d.line([(596, 488), (562, 478)], fill=(240, 210, 176), width=10)
    # 壁の暦（2月2日に丸）
    f = ImageFont.truetype(FONT_BOLD, 22)
    d.rectangle([222, 330, 402, 410], fill=(253, 251, 242), outline=(141, 131, 104), width=4)
    d.rectangle([222, 330, 402, 358], fill=(125, 63, 44))
    d.text((246, 334), "2月2日 開始", font=f, fill="#ffffff")
    for i in range(2):
        d.line([(222, 378 + i * 18), (402, 378 + i * 18)], fill=(195, 189, 166), width=3)
    d.ellipse([238, 372, 266, 400], outline=(192, 86, 60), width=6)
    band(d, ["親の土地は、", "町外にもあるかもしれない"], "森町ライフハック／空き家・実家・相続")


def scene_ten_year_limit(d):
    sky(d)
    mountains(d)
    cedars(d, [16, 60, 104, 646, 692, 736], 300)
    # 中景：段になった茶畑と家並み
    d.polygon([(0, 292), (760, 284), (760, 330), (0, 340)], fill=(133, 178, 92))
    for i in range(3):
        d.line([(0, 298 + i * 13), (760, 290 + i * 13)], fill=(90, 134, 62), width=3)
    d.polygon([(0, 334), (760, 324), (760, BAND_TOP), (0, BAND_TOP)], fill=(224, 230, 213))
    for x, w in ((20, 86), (128, 70), (632, 92)):
        d.rectangle([x, 342, x + w, 380], fill=(238, 232, 218))
        d.polygon([(x - 8, 344), (x + w // 2, 316), (x + w + 8, 344)], fill=(133, 148, 156))
    d.polygon([(0, 384), (760, 374), (760, 398), (0, 408)], fill=(111, 154, 88))
    # 庭の柿の木
    d.rectangle([680, 356, 694, 424], fill=(138, 106, 72))
    d.ellipse([634, 296, 740, 384], fill=(95, 140, 76))
    for cx, cy in ((658, 330), (708, 316), (720, 356)):
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(224, 138, 60), outline=(181, 106, 38), width=2)
    # 座敷の床と縁側
    d.rectangle([0, 468, 760, 486], fill=(201, 168, 119))
    d.rectangle([0, 486, 760, BAND_TOP], fill=(221, 201, 164))
    for y0 in (512, 550):
        d.line([(0, y0), (760, y0)], fill=(196, 171, 132), width=3)
    # 座卓・湯呑み・菓子鉢・封をしたままの書類
    d.rectangle([214, 494, 566, 520], fill=(185, 143, 93))
    d.rectangle([214, 520, 566, 532], fill=(156, 118, 72))
    for x in (238, 288, 338):
        d.rectangle([x, 464, x + 30, 492], fill=(244, 241, 230), outline=(179, 172, 150), width=3)
    d.ellipse([392, 462, 462, 492], fill=(228, 220, 196), outline=(179, 168, 135), width=3)
    for cx in (410, 428, 444):
        d.ellipse([cx - 7, 468, cx + 7, 482], fill=(201, 138, 82))
    d.rectangle([482, 448, 560, 484], fill=(253, 251, 242), outline=(168, 155, 124), width=3)
    d.line([(482, 448), (521, 470)], fill=(168, 155, 124), width=3)
    d.line([(521, 470), (560, 448)], fill=(168, 155, 124), width=3)
    d.rectangle([492, 434, 570, 470], fill=(246, 242, 226), outline=(168, 155, 124), width=3)
    d.line([(492, 434), (531, 456)], fill=(168, 155, 124), width=3)
    d.line([(531, 456), (570, 434)], fill=(168, 155, 124), width=3)
    # 向かい合ったまま視線を落とす二人
    d.ellipse([132, 424, 180, 472], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([132, 416, 180, 464], 180, 360, fill=(75, 66, 56))
    d.polygon([(124, 478), (188, 478), (198, BAND_TOP), (114, BAND_TOP)], fill=(92, 134, 160))
    d.line([(186, 494), (222, 508)], fill=(240, 210, 176), width=10)
    d.ellipse([600, 420, 648, 468], fill=(240, 210, 176), outline=(194, 161, 129), width=3)
    d.chord([600, 412, 648, 460], 180, 360, fill=(87, 73, 60))
    d.polygon([(592, 474), (656, 474), (666, BAND_TOP), (582, BAND_TOP)], fill=(160, 106, 124))
    d.line([(598, 490), (562, 504)], fill=(240, 210, 176), width=10)
    # 壁に重ねて掛けた十年分の暦
    f = ImageFont.truetype(FONT_BOLD, 22)
    for i, off in enumerate((24, 16, 8)):
        d.rectangle([200 + off, 330 + off, 396 + off, 412 + off],
                    fill=(243, 239, 224), outline=(176, 168, 142), width=3)
    d.rectangle([200, 330, 396, 412], fill=(253, 251, 242), outline=(141, 131, 104), width=4)
    d.rectangle([200, 330, 396, 358], fill=(125, 63, 44))
    d.text((252, 334), "10年目の暦", font=f, fill="#ffffff")
    for i in range(2):
        d.line([(200, 380 + i * 18), (396, 380 + i * 18)], fill=(195, 189, 166), width=3)
    d.ellipse([216, 374, 244, 402], outline=(192, 86, 60), width=6)
    band(d, ["今年もまとまらなかった、", "その十年目に何が変わるか"], "森町ライフハック／空き家・実家・相続")


SCENES = {
    "20260818-ten-year-limit-special-benefit": scene_ten_year_limit,
    "20260818-nationwide-property-record-certificate": scene_nationwide_record,
    "20260817-august-insurance-care-papers": scene_insurance_care_papers,
    "20260817-heir-representative-tax-notice": scene_heir_representative,
    "20260816-moving-in-timing-for-children": scene_moving_in_timing,
    "20260816-marriage-new-life-subsidy": scene_marriage_subsidy,
    "20260815-children-roles-in-district": scene_children_roles,
    "20260815-mori-matsuri-district-choice": scene_mori_matsuri_choice,
    "20260815-kasanboko-first-bon": scene_kasanboko,
    "20260814-bridge-pavement-tunnel-plans": scene_bridge_plans,
    "20260814-license-return-district-feet": scene_license_return,
    "20260813-august-grass-mowing": scene_august_grass,
    "20260813-kokko-kizoku-forest": scene_kokko_forest,
    "20260813-tanbo-lease-contract": scene_tanbo_lease,
    "20260812-amenomiya-nagi-garden-tree": scene_nagi,
    "20260812-ishimatsu-grave-rebuilt": scene_ishimatsu,
    "20260812-tomodake-kayabuki-value-cost": scene_tomodake,
    "20260811-obon-clean-center-days": scene_obon_clean_center,
    "20260811-souzoku-houki-three-months": scene_souzoku_houki,
    "20260811-nayosecho-all-parcels": scene_nayosecho,
    "20260811-water-shutoff-joining-fee": scene_water_shutoff,
    "20260811-akiya-plan-ten-years": scene_akiya_plan,
    "20260810-proxy-certificates-for-parents": scene_proxy_certificates,
    "20260810-consultation-reservation-split": scene_consult_split,
    "20260810-obon-week-town-hall-hours": scene_obon_window,
    "20260806-electric-fence-subsidy": scene_electric_fence,
    "20260809-tencomori-three-conditions": scene_tencomori,
    "20260809-akiya-august-afternoon-viewing": scene_akiya_august,
    "20260809-nothing-special-sunday": scene_quiet_sunday,
    "20260806-cadastral-survey-boundary": scene_cadastral,
    "20260807-smart-ic-livability": scene_smart_ic,
    "20260807-water-supply-routes": scene_water_routes,
    "20260807-tenhama-station-frequency": scene_tenhama_station,
    "20260807-obon-three-days-walk": scene_obon_walk,
    "20260808-hanabi-river-area": scene_hanabi_river,
    "20260808-yatai-storage-ownership": scene_yatai_storage,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SCENES:
        print("使い方: python scripts/make_cover_scene.py <slug>")
        print("対応する slug: " + " / ".join(sorted(SCENES)))
        return 1
    slug = sys.argv[1]
    img = Image.new("RGB", (S, S), (255, 255, 255))
    SCENES[slug](ImageDraw.Draw(img))
    out = os.path.join(BLOG_DIR, slug, "cover.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "JPEG", quality=88)
    print("生成:", os.path.relpath(out, ROOT).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
