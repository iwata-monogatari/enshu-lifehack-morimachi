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


SCENES = {
    "20260806-electric-fence-subsidy": scene_electric_fence,
    "20260806-cadastral-survey-boundary": scene_cadastral,
    "20260807-smart-ic-livability": scene_smart_ic,
    "20260807-water-supply-routes": scene_water_routes,
    "20260807-tenhama-station-frequency": scene_tenhama_station,
    "20260807-obon-three-days-walk": scene_obon_walk,
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
