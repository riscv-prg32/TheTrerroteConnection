#!/usr/bin/env python3
"""The eight views of the journey, painted from what stands at each real place.

Every view is 368 x 80 (320 on screen plus 24 pixels each side for parallax),
looking across the road, and is painted with Pillow at three times that size
from nothing but this file: no photograph is traced or sampled. Silhouettes and
their arrangement follow the real landmarks, listed per view in docs/art.md.
The light moves through the day from Naples in the morning to the sunset at
Baia Domizia.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

W, H = 368, 80
S = 3  # supersampling


class Paint:
    def __init__(self, seed: int):
        self.img = Image.new("RGB", (W * S, H * S))
        self.d = ImageDraw.Draw(self.img)
        self.rng = random.Random(seed)

    def rect(self, x, y, w, h, c):
        self.d.rectangle([x * S, y * S, (x + w) * S - 1, (y + h) * S - 1], fill=c)

    def poly(self, pts, c):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=c)

    def disc(self, x, y, rx, ry, c):
        self.d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S], fill=c)

    def line(self, x0, y0, x1, y1, c, w=1.0):
        self.d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=c, width=max(1, round(w * S)))

    def sky(self, stops):
        """Bands of colour from top to bottom: flat bands compress, gradients do not."""
        for i in range(len(stops) - 1):
            (y0, a), (y1, b) = stops[i], stops[i + 1]
            bands = max(1, (y1 - y0) // 5)
            for k in range(bands):
                t = k / bands
                c = tuple(round(a[j] + (b[j] - a[j]) * t) for j in range(3))
                self.rect(0, y0 + (y1 - y0) * k / bands, W, (y1 - y0) / bands + 1, c)

    def cloud(self, x, y, w, c):
        r = self.rng
        for _ in range(7):
            dx = r.uniform(-w / 2, w / 2)
            self.disc(x + dx, y + r.uniform(-1, 1), r.uniform(w / 8, w / 4) * (1 - abs(dx) / w), r.uniform(1, 2.6), c)

    def ridge(self, x0, x1, heights, base, c, rough=1.2, step=2):
        """A mountain silhouette through (x, height) knots, with a little noise."""
        pts = [(x0, base)]
        r = self.rng
        x = x0
        while x <= x1:
            for (ax, ah), (bx, bh) in zip(heights, heights[1:]):
                if ax <= x <= bx:
                    t = (x - ax) / max(bx - ax, 1)
                    t = t * t * (3 - 2 * t)
                    y = ah + (bh - ah) * t
                    break
            else:
                y = heights[-1][1]
            pts.append((x, base - y + r.uniform(-rough, rough)))
            x += step
        pts.append((x1, base))
        self.poly(pts, c)

    def sea(self, y0, y1, far, near, glint=None, glints=40):
        for k in range(y1 - y0):
            t = k / max(y1 - y0 - 1, 1)
            c = tuple(round(far[j] + (near[j] - far[j]) * (int(t * 4) / 3)) for j in range(3))
            self.rect(0, y0 + k, W, 1, c)
        if glint:
            r = self.rng
            for _ in range(glints):
                y = r.uniform(y0, y1)
                self.rect(r.uniform(0, W), y, r.uniform(2, 5 + (y - y0)), 0.5, glint)

    def houses(self, x0, x1, base, hmin, hmax, tones, roof=None, wmin=5, wmax=11, windows=(52, 46, 44)):
        """A dense block of southern houses: flat walls, dark window dots."""
        r = self.rng
        x = x0
        while x < x1:
            w = r.uniform(wmin, wmax)
            h = r.uniform(hmin, hmax)
            c = r.choice(tones)
            self.rect(x, base - h, w, h, c)
            shade = tuple(max(v - 28, 0) for v in c)
            self.rect(x + w - 1.2, base - h, 1.2, h, shade)
            if roof and r.random() < 0.45:
                self.poly([(x - 0.3, base - h), (x + w / 2, base - h - 2), (x + w + 0.3, base - h)], roof)
            if h > 6 and windows:
                for wy in range(int(base - h + 2), int(base - 2), 3):
                    for wx in range(int(x + 1.5), int(x + w - 1.5), 3):
                        if r.random() < 0.65:
                            self.rect(wx, wy, 1, 1.2, windows)
            x += w * r.uniform(0.75, 1.0)

    def palm(self, x, base, h, trunk=(92, 70, 48), frond=(36, 88, 52), frond2=(58, 118, 66)):
        lean = self.rng.uniform(-1.5, 1.5)
        self.line(x, base, x + lean, base - h, trunk, 1.4)
        top = (x + lean, base - h)
        for k in range(9):
            a = math.pi * (k / 8) + self.rng.uniform(-0.1, 0.1)
            ln = h * 0.42
            ex, ey = top[0] + math.cos(a) * ln, top[1] - math.sin(a) * ln * 0.55 + ln * 0.28
            mx, my = top[0] + math.cos(a) * ln * 0.55, top[1] - math.sin(a) * ln * 0.55
            c = frond if k % 2 else frond2
            self.line(top[0], top[1], mx, my, c, 1.1)
            self.line(mx, my, ex, ey, c, 0.8)

    def pine(self, x, base, h, trunk=(60, 42, 34), crown=(34, 72, 48), light=(58, 98, 58)):
        """The umbrella pine of the Domitian coast."""
        self.line(x, base, x, base - h * 0.75, trunk, 1.2)
        w = h * 0.55
        for _ in range(7):
            dx = self.rng.uniform(-w, w)
            self.disc(x + dx, base - h * 0.8 + self.rng.uniform(-1.5, 1.5), w * 0.45, h * 0.12, crown)
        for _ in range(4):
            dx = self.rng.uniform(-w * 0.7, w * 0.7)
            self.disc(x + dx, base - h * 0.87, w * 0.25, h * 0.06, light)

    def towers(self, xs, base, h, r, c, shade, top):
        """Round towers with a crenellated crown: the Angevin castle's signature."""
        for x in xs:
            self.rect(x - r, base - h, 2 * r, h, c)
            self.rect(x + r * 0.35, base - h, r * 0.65, h, shade)
            self.rect(x - r - 0.8, base - h - 2, 2 * r + 1.6, 2, top)
            for k in range(-2, 3):
                self.rect(x + k * r * 0.48 - 0.5, base - h - 3.5, 1, 1.6, top)

    def done(self) -> Image.Image:
        return self.img.resize((W, H), Image.BOX)


# ---- 1. Villa Comunale: Castel dell'Ovo and Vesuvius across the morning gulf --
def villa_comunale() -> Image.Image:
    p = Paint(11)
    p.sky([(0, (120, 182, 226)), (44, (176, 216, 236)), (64, (226, 232, 226))])
    p.cloud(70, 14, 70, (245, 247, 244))
    p.cloud(250, 9, 90, (242, 245, 244))
    # Vesuvius: the broken ridge of Somma on the left, the Gran Cono on the right.
    haze, haze2 = (118, 134, 162), (98, 114, 146)
    p.ridge(136, 330, [(136, 2), (170, 14), (196, 28), (212, 33), (226, 31), (238, 27)], 66, haze, 1.3)
    p.ridge(226, 340, [(226, 26), (244, 32), (262, 42), (272, 46), (286, 46), (298, 40), (318, 22), (340, 4)], 66, haze2, 0.6)
    p.line(272, 21, 262, 34, (130, 146, 172), 1)
    p.line(284, 21, 292, 35, (130, 146, 172), 1)
    p.ridge(330, 368, [(330, 2), (352, 16), (368, 20)], 66, (140, 158, 182), 0.8)
    # The towns at its foot.
    p.houses(140, 340, 66, 1.5, 4, [(206, 200, 188), (222, 212, 194), (188, 182, 176)], wmin=3, wmax=6, windows=None)
    p.sea(66, 80, (86, 158, 196), (42, 124, 170), (196, 228, 238))
    # Castel dell'Ovo on its islet: long tuff walls, the square keep, the causeway.
    tuff, tuffd, tuffl = (196, 164, 104), (150, 120, 76), (218, 190, 132)
    p.rect(20, 69, 100, 2, (120, 98, 72))
    p.rect(68, 54, 64, 16, tuff)
    p.poly([(68, 54), (80, 48), (120, 48), (132, 54)], tuffd)
    p.rect(84, 42, 26, 12, tuff)
    p.rect(104, 42, 6, 12, tuffd)
    p.rect(92, 36, 11, 7, tuffl)
    p.rect(99, 36, 4, 7, tuff)
    for x in (72, 84, 96, 108, 120):
        p.rect(x, 60, 3, 4, (92, 76, 60))
    for x in range(68, 132, 4):
        p.rect(x, 52.5, 2, 1.5, tuffl)
    p.rect(66, 68, 68, 3, tuffd)
    # The Villa's own palms and railing on the left, on the pavement of via Caracciolo.
    p.rect(0, 74, 60, 6, (168, 158, 140))
    p.rect(0, 73, 60, 1, (70, 72, 80))
    for x, h in ((8, 50), (24, 58), (44, 46)):
        p.palm(x, 74, h)
    return p.done()


# ---- 2. Molo Beverello: Castel Nuovo, the Stazione Marittima, a ferry waiting --
def porto() -> Image.Image:
    p = Paint(22)
    p.sky([(0, (126, 186, 224)), (40, (186, 218, 232)), (64, (228, 230, 220))])
    p.cloud(290, 12, 80, (246, 247, 244))
    p.cloud(180, 7, 50, (244, 246, 244))
    # The Vomero hill, with Castel Sant'Elmo and the Certosa on top.
    p.ridge(0, 190, [(0, 40), (36, 56), (80, 60), (130, 42), (190, 12)], 70, (92, 120, 96), 1.0)
    p.houses(0, 170, 68, 16, 34, [(206, 190, 162), (190, 170, 150), (216, 200, 170)], wmin=4, wmax=8, windows=(120, 110, 100))
    p.poly([(44, 22), (52, 16), (84, 16), (92, 22), (88, 27), (48, 27)], (170, 150, 112))
    p.rect(56, 11, 20, 6, (186, 166, 126))
    p.rect(92, 19, 18, 8, (226, 216, 198))
    p.poly([(99, 19), (102, 14), (105, 19)], (190, 170, 150))
    # Vesuvius, far and hazy, beyond the port.
    p.ridge(226, 368, [(226, 2), (262, 24), (290, 34), (306, 33), (334, 20), (368, 8)], 62, (150, 168, 192), 0.5)
    p.sea(62, 80, (86, 150, 186), (46, 118, 160), (190, 222, 232))
    # Castel Nuovo, the Maschio Angioino: dark piperno towers, white marble arch.
    stone, shade, crown = (84, 78, 80), (58, 54, 60), (112, 104, 102)
    p.rect(92, 30, 72, 36, (98, 92, 90))
    p.towers((96, 123, 160), 66, 36, 11, stone, shade, crown)
    p.rect(108, 26, 11, 40, (226, 222, 210))
    p.rect(108, 34, 11, 1.4, (178, 172, 160))
    p.rect(108, 42, 11, 1.4, (178, 172, 160))
    p.disc(113.5, 52, 4, 4, (66, 60, 62))
    p.rect(109.5, 52, 8, 14, (66, 60, 62))
    p.rect(160, 64, 40, 2, (120, 104, 84))
    # The Stazione Marittima: long and white, 1930s.
    p.rect(196, 54, 58, 12, (232, 228, 218))
    p.rect(196, 54, 58, 2, (196, 190, 180))
    p.rect(210, 44, 14, 10, (232, 228, 218))
    for x in range(199, 252, 5):
        p.rect(x, 58, 3, 4, (108, 128, 146))
    # A harbour crane and the ferry for Ischia, white with a blue funnel.
    p.line(262, 66, 262, 34, (86, 92, 104), 1.4)
    p.line(262, 36, 288, 42, (86, 92, 104), 1)
    p.rect(258, 66, 110, 3, (150, 142, 128))
    hull, deck = (238, 238, 232), (214, 216, 216)
    p.poly([(270, 72), (356, 72), (362, 60), (266, 60)], hull)
    p.rect(266, 66, 96, 2, (44, 88, 142))
    p.rect(278, 50, 66, 10, deck)
    p.rect(288, 42, 40, 8, hull)
    p.rect(312, 32, 8, 10, (44, 88, 142))
    for x in range(282, 342, 6):
        p.rect(x, 53, 3, 3, (84, 104, 122))
    p.rect(0, 70, 92, 10, (150, 140, 124))
    return p.done()


# ---- 3. Ischia: the Castello Aragonese on its rock, the bridge, Monte Epomeo --
def ischia() -> Image.Image:
    p = Paint(33)
    p.sky([(0, (108, 180, 232)), (44, (170, 218, 240)), (62, (222, 236, 232))])
    p.cloud(100, 11, 80, (250, 251, 248))
    p.cloud(320, 16, 50, (248, 250, 248))
    # Monte Epomeo behind the town: green slopes, its bare tuff summit.
    p.ridge(0, 196, [(0, 22), (40, 36), (72, 48), (88, 54), (108, 46), (146, 26), (196, 6)], 66, (84, 128, 104), 1.2)
    p.poly([(78, 18), (88, 12), (98, 18), (92, 22), (84, 22)], (186, 176, 150))
    p.sea(66, 80, (74, 170, 196), (28, 128, 166), (210, 240, 244))
    # Ischia Ponte: the pastel town, and the long Ponte Aragonese.
    p.houses(0, 146, 70, 8, 18, [(238, 214, 166), (232, 186, 150), (224, 226, 206), (240, 200, 180), (206, 222, 214)],
             roof=(176, 112, 84), wmin=6, wmax=12, windows=(96, 84, 80))
    p.rect(0, 69, 150, 5, (214, 200, 170))
    p.rect(140, 67, 80, 3, (176, 158, 124))
    for x in range(146, 218, 12):
        p.rect(x, 70, 3, 5, (150, 132, 100))
    # The rock.
    rock, rockd, green, greend = (120, 104, 84), (88, 76, 66), (66, 110, 66), (46, 86, 56)
    p.ridge(204, 346, [(204, 4), (216, 22), (232, 34), (262, 42), (296, 40), (322, 30), (338, 14), (346, 2)], 72, rock, 1.8)
    p.ridge(226, 340, [(226, 8), (244, 22), (270, 30), (300, 26), (326, 14), (340, 2)], 72, rockd, 2.0)
    for _ in range(26):
        x, y = p.rng.uniform(226, 330), p.rng.uniform(34, 58)
        p.disc(x, y, p.rng.uniform(2, 5), p.rng.uniform(1, 2.4), p.rng.choice((green, greend)))
    # On top: walls, the ruined cathedral, and the dome of the Immacolata.
    wall, walld, dome = (222, 196, 142), (178, 152, 106), (196, 186, 170)
    p.rect(232, 26, 74, 10, wall)
    p.rect(232, 34, 74, 2, walld)
    p.rect(250, 16, 26, 10, wall)
    p.rect(270, 16, 6, 10, walld)
    p.disc(263, 15, 8, 7, dome)
    p.rect(260, 5, 6, 4, (216, 206, 188))
    p.disc(263, 5, 2.5, 2, dome)
    p.rect(284, 14, 14, 12, (200, 170, 122))
    p.rect(287, 17, 3, 5, (96, 84, 76))
    p.rect(293, 17, 3, 5, (96, 84, 76))
    p.rect(238, 20, 8, 7, (236, 216, 170))
    p.rect(302, 22, 10, 8, (232, 208, 160))
    p.rect(208, 64, 130, 3, (214, 188, 136))
    p.rect(208, 70, 134, 3, (72, 66, 62))
    # Boats in the bay.
    for x in (346, 358):
        p.poly([(x, 72), (x + 7, 72), (x + 5, 74), (x + 1, 74)], (236, 236, 228))
    return p.done()


# ---- 4. Pozzuoli: the Serapeum's columns, Rione Terra, Capo Miseno far away ---
def pozzuoli() -> Image.Image:
    p = Paint(44)
    p.sky([(0, (128, 184, 222)), (40, (190, 216, 226)), (60, (236, 226, 204))])
    p.cloud(60, 10, 60, (248, 244, 234))
    p.cloud(250, 13, 80, (248, 244, 234))
    # Solfatara's hills inland, with the fumes that give the place its smell.
    p.ridge(0, 120, [(0, 38), (40, 30), (84, 20), (120, 8)], 62, (118, 134, 106), 0.9)
    for k in range(9):
        p.disc(34 + k * 1.2, 18 - k * 1.8, 2 + k * 0.5, 1.2 + k * 0.3, (232, 232, 224))
    # Capo Miseno far out: the flat-topped cone, and Baia's shore.
    p.ridge(292, 368, [(292, 2), (312, 6), (334, 18), (352, 19), (368, 8)], 62, (150, 164, 180), 0.4)
    p.sea(60, 80, (92, 164, 186), (44, 124, 156), (206, 232, 232))
    # The town climbing the slope.
    p.houses(0, 190, 62, 12, 26, [(226, 196, 150), (216, 170, 130), (232, 214, 180), (202, 178, 150)],
             roof=(160, 104, 78), wmin=6, wmax=12, windows=(100, 86, 80))
    # Rione Terra: the tuff headland crowded with the old town and the Duomo.
    tuff, tuffd = (182, 148, 92), (138, 110, 72)
    p.ridge(176, 292, [(176, 4), (192, 26), (214, 34), (256, 34), (278, 26), (292, 2)], 68, tuff, 1.0)
    for y in range(40, 66, 5):
        p.rect(188, y, 92, 0.8, tuffd)
    p.houses(192, 280, 38, 6, 16, [(226, 200, 150), (214, 186, 140), (232, 214, 176), (200, 170, 126)],
             roof=(158, 104, 78), wmin=6, wmax=12, windows=(98, 84, 76))
    p.rect(226, 14, 22, 12, (238, 226, 200))
    p.poly([(224, 14), (237, 6), (250, 14)], (220, 206, 178))
    p.rect(252, 12, 7, 14, (226, 210, 178))
    p.poly([(251, 12), (255.5, 7), (260, 12)], (160, 104, 78))
    # The port: the mole, and the ferry from Ischia.
    p.rect(286, 66, 82, 3, (154, 146, 132))
    hull = (236, 236, 230)
    p.poly([(304, 69), (352, 69), (356, 60), (300, 60)], hull)
    p.rect(300, 64, 56, 1.5, (44, 88, 142))
    p.rect(310, 52, 34, 8, (216, 216, 214))
    p.rect(330, 45, 5, 7, (44, 88, 142))
    # The Macellum, called the Temple of Serapis: the three marble columns
    # standing in their sunken brick ruin, with the sea's bite marks on them.
    p.rect(0, 62, 160, 18, (160, 118, 88))
    p.rect(0, 62, 160, 1.5, (120, 86, 68))
    for x in range(8, 156, 16):
        p.rect(x, 64, 8, 5, (122, 86, 66))
    p.rect(60, 70, 96, 10, (188, 170, 138))
    marble, marbled, bite = (232, 226, 214), (182, 174, 162), (118, 112, 106)
    for x in (72, 96, 120):
        p.rect(x - 3.5, 16, 7, 56, marble)
        p.rect(x + 1.2, 16, 2.3, 56, marbled)
        p.rect(x - 3.5, 42, 7, 7, bite)
        p.rect(x - 5.5, 13, 11, 3, marble)
        p.rect(x - 5, 71, 10, 3, marbled)
    for x in (50, 142):
        p.rect(x - 3, 58, 6, 14, marbled)
    return p.done()


# ---- 5. Casoria: the plain north of Naples, Somma-Vesuvius seen from behind ---
def casoria() -> Image.Image:
    p = Paint(50)
    p.sky([(0, (120, 174, 216)), (36, (184, 206, 218)), (60, (226, 218, 200))])
    p.cloud(70, 9, 70, (246, 242, 234))
    p.cloud(300, 14, 90, (246, 242, 234))
    # From the north the volcano shows its other face: the long wall of Monte
    # Somma in front, the cone of Vesuvius just showing over its right shoulder.
    p.ridge(150, 368, [(150, 2), (200, 22), (236, 34), (262, 38), (288, 34), (316, 26), (368, 8)],
            62, (132, 132, 150), 0.7)
    p.ridge(270, 352, [(270, 30), (298, 44), (312, 46), (330, 40), (352, 24)], 62, (150, 146, 160), 0.5)
    p.ridge(150, 368, [(150, 1), (220, 12), (262, 18), (300, 14), (368, 4)], 62, (110, 120, 112), 0.8)
    # The old centre: houses, and the bell tower and dome of San Mauro Abate.
    p.houses(0, 150, 62, 8, 16, [(226, 200, 160), (218, 182, 146), (234, 218, 188), (206, 186, 160)],
             roof=(164, 108, 82), wmin=6, wmax=11, windows=(102, 90, 84))
    church, churchd, dome = (238, 222, 192), (200, 182, 152), (110, 128, 120)
    p.rect(54, 34, 26, 28, church)
    p.rect(74, 34, 6, 28, churchd)
    p.rect(60, 28, 14, 6, church)
    p.disc(67, 28, 8, 7, dome)
    p.rect(66, 18, 2, 4, churchd)
    p.rect(88, 14, 10, 48, church)
    p.rect(95, 14, 3, 48, churchd)
    for y in (20, 32):
        p.rect(91, y, 4, 6, (70, 64, 66))
    p.poly([(87, 14), (93, 5), (99, 14)], dome)
    # The palazzoni of the sixties and seventies, balconies and washing.
    blocks = [(150, 26, 40), (180, 30, 50), (214, 24, 36), (242, 34, 46), (280, 26, 38), (310, 30, 52), (344, 24, 40)]
    tones = [(222, 196, 164), (210, 200, 188), (232, 184, 156), (204, 188, 164)]
    for k, (x, w, h) in enumerate(blocks):
        c = tones[k % len(tones)]
        top = 68 - h
        p.rect(x, top, w, h, c)
        p.rect(x + w - 3, top, 3, h, tuple(v - 30 for v in c))
        p.rect(x - 0.5, top - 1.5, w + 1, 1.5, (150, 140, 134))
        for y in range(int(top + 3), 64, 5):
            p.rect(x + 1.5, y + 2, w - 5, 1, (150, 140, 134))
            for wx in range(int(x + 3), int(x + w - 5), 5):
                p.rect(wx, y, 2, 2, (84, 80, 84))
            if p.rng.random() < 0.5:
                lx = x + p.rng.uniform(3, w - 12)
                for j in range(3):
                    p.rect(lx + j * 3, y + 3, 2, 1.6, ((240, 240, 236), (214, 82, 70), (80, 130, 186))[j])
    # The Asse Mediano on its viaduct, carrying the traffic of the plain.
    deck, decks = (186, 182, 176), (120, 116, 114)
    p.rect(0, 58, 368, 3, deck)
    p.rect(0, 61, 368, 1, decks)
    for x in range(10, 368, 34):
        p.rect(x, 62, 4, 10, decks)
    for x, c in ((30, (204, 62, 52)), (96, (236, 236, 230)), (170, (62, 96, 150)), (250, (232, 196, 70)),
                 (322, (236, 236, 230))):
        p.rect(x, 55.5, 9, 2.5, c)
        p.rect(x + 2, 54, 5, 1.5, (90, 110, 130))
    # The edge of town: a wall of posters, a petrol station, rough verge.
    p.rect(0, 70, 368, 10, (152, 142, 120))
    p.rect(0, 70, 368, 1, (186, 176, 150))
    for x, c in ((20, (236, 200, 70)), (44, (214, 82, 70)), (68, (80, 130, 186)), (92, (236, 236, 230))):
        p.rect(x, 64, 20, 8, c)
    p.rect(250, 64, 40, 2, (222, 64, 52))
    p.rect(254, 66, 3, 6, (200, 196, 190))
    p.rect(282, 66, 3, 6, (200, 196, 190))
    p.rect(264, 68, 6, 4, (236, 236, 230))
    return p.done()


# ---- 6. Torregaveta: the tuff cliff, the Cumana terminus, Procida and Epomeo --
def torregaveta() -> Image.Image:
    p = Paint(55)
    p.sky([(0, (118, 170, 212)), (40, (196, 212, 214)), (60, (244, 222, 180))])
    p.cloud(120, 12, 110, (250, 240, 224))
    p.cloud(320, 8, 60, (250, 240, 224))
    p.sea(58, 80, (100, 160, 180), (42, 116, 150), (240, 226, 190), 60)
    # On the horizon: Ischia with Epomeo, and low Procida nearer.
    p.ridge(70, 196, [(70, 2), (104, 10), (132, 22), (148, 24), (170, 10), (196, 1)], 58, (142, 152, 172), 0.4)
    p.ridge(150, 246, [(150, 1), (172, 5), (206, 6), (232, 4), (246, 1)], 59, (116, 132, 150), 0.4)
    p.houses(164, 236, 59, 1, 2.6, [(216, 200, 176), (232, 216, 190), (196, 180, 170)], wmin=2, wmax=4, windows=None)
    # The headland of Monte di Procida falling into the sea, layered yellow tuff.
    tuff, tuffd, tuffl, scrub = (188, 150, 92), (146, 110, 68), (212, 180, 124), (82, 112, 70)
    p.ridge(232, 368, [(232, 3), (246, 26), (262, 44), (290, 52), (330, 56), (368, 60)], 70, tuff, 1.2)
    for k, y in enumerate(range(24, 70, 4)):
        c = tuffd if k % 2 else tuffl
        x0 = 262 - (y - 24) * 0.6
        p.line(x0, y + p.rng.uniform(-1, 1), 368, y + p.rng.uniform(-2, 2), c, 0.8)
    for _ in range(22):
        x = p.rng.uniform(262, 368)
        p.disc(x, 18 + (368 - x) * 0.1 + p.rng.uniform(-3, 2), p.rng.uniform(3, 7), p.rng.uniform(1, 2.5), scrub)
    # White villas on the crest, and the old coastal tower that named the place.
    p.houses(276, 368, 18, 5, 12, [(238, 230, 214), (226, 214, 190), (240, 222, 196)], roof=(164, 104, 80),
             wmin=6, wmax=12, windows=(102, 96, 92))
    p.rect(244, 42, 12, 26, (160, 128, 86))
    p.rect(252, 42, 4, 26, (124, 98, 70))
    p.rect(243, 40, 14, 2.5, (178, 148, 104))
    # The beach and the Cumana terminus at the foot of the cliff.
    p.rect(0, 70, 368, 10, (226, 206, 160))
    p.rect(0, 70, 368, 1, (250, 244, 224))
    p.rect(0, 62, 110, 8, (214, 196, 160))
    p.rect(0, 60, 110, 2, (150, 92, 72))
    for x in range(4, 106, 8):
        p.rect(x, 64, 4, 4, (92, 92, 104))
    # The train: the little Cumana railway in its red.
    p.rect(14, 62, 76, 7, (186, 54, 44))
    p.rect(14, 62, 76, 1, (226, 222, 212))
    for x in range(18, 88, 7):
        p.rect(x, 64, 5, 2.5, (40, 48, 62))
    p.rect(14, 69, 76, 1, (40, 36, 40))
    # Fishing boats drawn up on the sand.
    for x in (130, 152, 196):
        p.poly([(x, 72), (x + 14, 72), (x + 11, 76), (x + 3, 76)], (64, 120, 170))
        p.rect(x, 71.5, 14, 1, (240, 240, 230))
    return p.done()


# ---- 7. Mondragone: Monte Petrino and its ruined Rocca, the flat coast --------
def mondragone() -> Image.Image:
    p = Paint(66)
    p.sky([(0, (130, 164, 204)), (36, (214, 206, 196)), (60, (250, 212, 158))])
    p.cloud(250, 14, 120, (252, 232, 206))
    p.cloud(90, 7, 60, (248, 228, 206))
    # The Massico range behind, then Monte Petrino's bare limestone hump.
    p.ridge(90, 300, [(90, 26), (140, 34), (200, 26), (250, 16), (300, 2)], 62, (136, 142, 150), 0.7)
    rock, rockd, green = (150, 148, 130), (116, 120, 104), (88, 116, 78)
    p.ridge(0, 196, [(0, 34), (28, 50), (58, 58), (82, 58), (116, 42), (150, 20), (196, 2)], 64, green, 1.0)
    for _ in range(30):
        x, y = p.rng.uniform(16, 122), p.rng.uniform(10, 36)
        p.disc(x, y, p.rng.uniform(2, 6), p.rng.uniform(0.8, 1.8), p.rng.choice((rock, rockd)))
    # The Rocca Montis Dragonis on the summit: a broken keep and curtain wall.
    wall, walld = (112, 100, 88), (82, 74, 70)
    p.rect(52, 0, 11, 9, wall)
    p.poly([(52, 0), (56, -2), (59, 1), (63, -1), (63, 2), (52, 2)], wall)
    p.rect(60, 0, 3, 9, walld)
    p.rect(40, 5, 12, 3, wall)
    p.rect(63, 4, 16, 4, wall)
    p.rect(68, 3, 2, 2, wall)
    p.rect(75, 2, 3, 3, wall)
    # The town along the flat, with a church, then the road to the lidos.
    p.houses(4, 198, 66, 7, 15, [(232, 206, 170), (222, 192, 158), (236, 222, 196), (210, 186, 160)],
             roof=(170, 112, 84), wmin=6, wmax=11, windows=(106, 92, 86))
    p.rect(96, 42, 10, 24, (238, 224, 198))
    p.poly([(95, 42), (101, 34), (107, 42)], (168, 108, 82))
    p.rect(106, 52, 20, 14, (232, 214, 186))
    p.poly([(105, 52), (116, 46), (127, 52)], (168, 108, 82))
    p.sea(62, 76, (110, 164, 176), (54, 124, 150), (252, 226, 180), 60)
    p.rect(198, 60, 170, 2, (120, 150, 164))
    # The long beach with its lido cabins.
    p.rect(0, 66, 200, 14, (120, 136, 92))
    p.rect(170, 72, 198, 8, (232, 208, 154))
    for x in range(204, 360, 12):
        c = (216, 74, 62) if (x // 12) % 2 else (64, 124, 176)
        p.rect(x, 66, 8, 7, (240, 234, 216))
        p.rect(x, 64.5, 8, 2, c)
    # The plain is buffalo country: where the mozzarella begins.
    for x, y in ((24, 74), (44, 76), (66, 73), (88, 76), (124, 74), (150, 76)):
        p.disc(x, y, 3.8, 1.8, (34, 30, 34))
        p.disc(x + 3.8, y - 1, 1.3, 1.1, (34, 30, 34))
        p.rect(x - 3, y + 1, 1, 2.2, (34, 30, 34))
        p.rect(x + 2, y + 1, 1, 2.2, (34, 30, 34))
    return p.done()


# ---- 8. Baia Domizia at sunset: the pines, the umbrellas, Ponza on the horizon -
def baia_domizia() -> Image.Image:
    p = Paint(77)
    p.sky([(0, (86, 104, 168)), (24, (196, 128, 142)), (46, (248, 170, 110)), (62, (254, 214, 130))])
    p.cloud(80, 10, 110, (232, 150, 140))
    p.cloud(180, 22, 110, (250, 176, 128))
    p.cloud(340, 7, 60, (222, 140, 146))
    # The sun goes down over the sea: this coast faces west.
    p.disc(246, 46, 13, 13, (255, 236, 164))
    p.sea(60, 74, (214, 150, 118), (116, 112, 132), (255, 224, 150), 30)
    for k in range(9):
        p.rect(246 - (5 + k * 2) / 1, 60 + k * 1.6, (5 + k * 2) * 2, 0.8, (255, 228, 150))
    # Ponza and its islets, faint on the horizon.
    p.ridge(306, 360, [(306, 1), (320, 4), (334, 3), (348, 5), (360, 1)], 60, (156, 118, 134), 0.3)
    # Inland: Monte Massico, and the old volcano of Roccamonfina behind.
    p.ridge(0, 140, [(0, 30), (34, 38), (66, 30), (104, 20), (140, 4)], 60, (136, 104, 132), 0.6)
    p.ridge(0, 100, [(0, 18), (30, 24), (62, 16), (100, 4)], 60, (108, 84, 112), 0.7)
    # The long Domitian beach, with its rows of umbrellas.
    p.rect(0, 66, 368, 14, (232, 190, 132))
    p.rect(120, 65, 248, 1, (255, 232, 180))
    for row, (y, step, size) in enumerate(((68, 16, 3.5), (72, 22, 5), (76, 30, 7))):
        for k, x in enumerate(range(124 + row * 7, 368, step)):
            c = ((224, 70, 58), (246, 234, 208), (58, 120, 172), (246, 200, 76))[(k + row) % 4]
            p.line(x, y, x, y + size * 0.9, (96, 78, 72), 0.6)
            p.poly([(x - size, y), (x, y - size * 0.55), (x + size, y)], c)
    # The pineta that gives the place its shade; the road runs behind it.
    for x, h in ((6, 52), (28, 60), (50, 48), (70, 56), (92, 50), (112, 44)):
        p.pine(x, 70, h, trunk=(64, 42, 40), crown=(46, 62, 56), light=(84, 86, 62))
    p.rect(0, 70, 124, 10, (108, 112, 72))
    return p.done()


VIEWS = [
    ("villa", "Villa Comunale, Naples", villa_comunale),
    ("porto", "Molo Beverello, Naples", porto),
    ("ischia", "Ischia Ponte", ischia),
    ("pozzuoli", "Pozzuoli", pozzuoli),
    ("casoria", "Casoria", casoria),
    ("torregaveta", "Torregaveta", torregaveta),
    ("mondragone", "Mondragone", mondragone),
    ("baia", "Baia Domizia", baia_domizia),
]

if __name__ == "__main__":
    import sys
    from pathlib import Path
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    sheet = Image.new("RGB", (W * 2, (H * 2 + 4) * len(VIEWS)))
    for i, (name, _, fn) in enumerate(VIEWS):
        sheet.paste(fn().resize((W * 2, H * 2), Image.NEAREST), (0, i * (H * 2 + 4)))
    sheet.save(out / "views.png")
