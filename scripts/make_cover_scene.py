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


SCENES = {
    "20260806-electric-fence-subsidy": scene_electric_fence,
    "20260809-tencomori-three-conditions": scene_tencomori,
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
