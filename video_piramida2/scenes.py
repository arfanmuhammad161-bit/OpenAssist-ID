import math, json, numpy as np
from engine import *
TL = json.load(open("timeline.json")); SC = TL["scenes"]
def ck(S, i): c = S["chunks"][i]; return c["t0"], c["t1"]
def rs(seed): return np.random.RandomState(seed)

def counter_fmt(n, dec=False):
    s = f"{int(n):,}".replace(",", "."); return s

# ---------------- latar umum ----------------
def desert(cv, hy, cols, par=(.25, .55, 1.0), t=0):
    dune(cv, hy - 10, 26, .006, 1.0, cols[0], par[0]); dune(cv, hy + 50, 34, .0048, 2.2, cols[1], par[1]); dune(cv, hy + 130, 40, .0035, 4.0, cols[2], par[2])
    cv.poly([(-800, hy + 190), (1900, hy + 190), (1900, 2900), (-800, 2900)], cols[2], par[2])

def giza(cv, t, dy=0, sunset=1.0, crack=0.0, tint=None):
    """tiga piramida Giza (dipakai S1 dan S8 -> bookend)."""
    base = 1260 + dy
    for (bx, w, h, par) in ((150, 250, 280, .8), (930, 160, 180, .9), (540, 370, 430, 1.0)):
        cl = mix(PAL["sand"], PAL["orange"], .35 * sunset); cr = mix(PAL["sandd"], PAL["shadow"], .45)
        draw_pyramid(cv, bx, base + (0 if par == 1.0 else 20), w, h, cl, cr, par, courses=14 if w > 300 else 9)
    if crack > 0:
        A, L, M, R = pyr_pts(540, base, 370, 430)
        zz = [(A[0] - 10, A[1] + 30), (A[0] + 22, A[1] + 120), (A[0] - 18, A[1] + 200), (A[0] + 26, A[1] + 290), (A[0] - 6, A[1] + 360)]
        n = int(len(zz) * clamp(crack)) + 1
        cv.line(zz[:max(2, n)], PAL["red"], 11)

# ---------------- S1 ----------------
class S1:
    def bg(self, tl, S):
        g = clamp((tl - ck(S, 3)[0] - .5) / .3)
        return sky_array(mix(PAL["navy"], hexc("#3A0B22"), g * .8), mix(PAL["orange"], PAL["red"], g * .5), (700, 1000, PAL["orange"]), 1.0, .58)
    def draw(self, cv, tl, S):
        c1, c2, c3 = ck(S, 1), ck(S, 2), ck(S, 3)
        ta = c3[0] + (c3[1] - c3[0]) * .52
        k = ease_io(tl / S["dur"]); crash = math.exp(-max(0, tl - ta) * 5) * (tl >= ta)
        cv.cam(540, 1050 - 40 * k, 1.0 + .12 * k + .22 * crash, 0, 8 * crash * math.sin(tl * 90), 6 * crash * math.cos(tl * 70))
        stars(cv, 70, 3, tl, .9, .5)
        # matahari + sinar
        sx, sy = 700, 1010
        for i in range(18):
            a = i / 18 * 2 * math.pi + tl * .18
            cv.poly([(sx + math.cos(a - .05) * 220, sy + math.sin(a - .05) * 220), (sx + math.cos(a) * 1500, sy + math.sin(a) * 1500), (sx + math.cos(a + .05) * 220, sy + math.sin(a + .05) * 220)], (255, 200, 120, 26), .2)
        cv.ell(sx, sy, 175, 175, mix(PAL["accent"], PAL["white"], .35), .2)
        desert(cv, 1160, [mix(PAL["purple"], PAL["orange"], .5), mix(PAL["purple"], PAL["orange"], .3), mix(PAL["shadow"], PAL["purple"], .45)], t=tl)
        giza(cv, tl, 0, 1.0, crack=clamp((tl - ta - .1) / .5))
        # lingkaran tangan "sempurna"
        pr = ease_out((tl - c2[0]) / .7); fade = 1 - clamp((tl - ta) / .15)
        if pr > 0 and fade > 0: pen_circle(cv, 540, 1040, 260, 300, pr, mix(PAL["accent"], (255, 255, 255, 255), .2) if False else PAL["accent"], 10, 7)
        if c2[0] <= tl < ta: tag(cv, 540, 690, "SEMPURNA?", 52, PAL["accent"], PAL["navy"], scale=ease_out((tl - c2[0]) / .4), rot=0)
        # counter 4.500
        cvv = ease_out(tl / 1.1) * 4500; pop = 1 + .10 * math.exp(-max(0, tl - 1.1) * 9) * (tl > 1.1)
        cv.text(540, 470, counter_fmt(cvv), "black", 270 * pop, PAL["cream"], stroke=10, stroke_fill=PAL["shadow"], z_scale=True)
        cv.text(540, 640, "TAHUN", "black", 96, PAL["accent"], stroke=6, stroke_fill=PAL["shadow"])
        # stempel GAGAL
        if tl >= ta:
            sc = back_out((tl - ta) / .22) ; shake = 4 * math.sin(tl * 80) * math.exp(-(tl - ta) * 4)
            cv.d.polygon([], fill=None) if False else None
            tag(cv, 540 + shake, 800, "GAGAL", 190, PAL["red"], PAL["white"], scale=sc, font="black")
        return dict(flash=(PAL["red"], .55 * math.exp(-max(0, tl - ta) * 8)) if tl >= ta else None, glitch=(tl >= ta and tl < ta + .28), shake=0)

# ---------------- S2 ----------------
class S2:
    def bg(self, tl, S): return sky_array(hexc("#6FB7F5"), hexc("#FFE6B0"), (200, 520, hexc("#FFFFFF")), .2, .64)
    def draw(self, cv, tl, S):
        c0, c1, c2, c3, c4 = [ck(S, i) for i in range(5)]
        k = ease_io(tl / S["dur"]); cv.cam(540, 1250 - 330 * ease_io(clamp((tl - c2[0]) / 2.2)), 1.28 - .28 * ease_io(clamp((tl - c1[0]) / 3.5)), 0, 0, 0)
        # awan
        for i, (x, y, s) in enumerate(((150, 360, 1), (800, 280, .8), (520, 520, .6))):
            xx = (x + tl * 14 * s) % 1500 - 200
            for dx, dy, r in ((0, 0, 70), (60, -25, 60), (-60, 10, 55), (110, 15, 48)): cv.ell(xx + dx * s, y + dy * s, r * s, r * s * .7, (255, 255, 255, 235), .15)
        desert(cv, 1290, [hexc("#F2C57A"), hexc("#EDB866"), hexc("#E6A95A")], t=tl)
        # grid kertas teknik
        for gx in range(-400, 1500, 90): cv.line([(gx, 700), (gx, 1900)], (255, 255, 255, 36), 2, cap=False)
        gy = 1290
        widths = [720, 610, 500, 400, 300, 200]; hh = 100; dep = 38; cols = [PAL["stone"], mix(PAL["stone"], PAL["sandl"], .25)]
        built = []
        for kx in range(6):
            t0 = c1[0] + .15 + kx * .40; p = (tl - t0)
            if p < 0: continue
            w = widths[kx]; by = gy - kx * hh; drop = (1 - back_out(p / .32, 1.5)) * 520 if p < .32 else 0
            y1 = by - drop
            L, R = 540 - w / 2, 540 + w / 2
            cv.poly([(L, y1), (R, y1), (R, y1 - hh), (L, y1 - hh)], mix(PAL["stone"], PAL["sandl"], .08 * (kx % 2)))
            for q in (1, 2): cv.line([(L, y1 - hh * q / 3), (R, y1 - hh * q / 3)], (120, 80, 35, 90), 3, cap=False)
            for bxx in range(int(L) + 60, int(R), 120): cv.line([(bxx + (kx % 2) * 30, y1 - hh), (bxx + (kx % 2) * 30, y1 - hh * 2 / 3)], (120, 80, 35, 70), 3, cap=False)
            cv.poly([(R, y1), (R + dep, y1 - dep * .8), (R + dep, y1 - hh - dep * .8), (R, y1 - hh)], PAL["stoned"])
            cv.poly([(L, y1 - hh), (R, y1 - hh), (R + dep, y1 - hh - dep * .8), (L + dep, y1 - hh - dep * .8)], PAL["sandl"])
            cv.ell(L + 46, y1 - hh / 2, 30, 30, PAL["navy"]); cv.text(L + 46, y1 - hh / 2 + 2, str(kx + 1), "black", 38, PAL["accent"])
            if 0 < p < .5:  # debu
                for i in range(7):
                    a = i / 7 * math.pi; r = 20 + 130 * p
                    cv.ell(540 + math.cos(a) * (w / 2 + 10) * (1 if i % 2 else -1) , by + 4, 16 * (1 - p * 1.4) + 4, 12 * (1 - p), (255, 240, 210, int(200 * (1 - p * 2))))
        top = gy - 6 * hh - dep * .8
        # lingkaran pena + label
        pr = ease_out((tl - c3[0]) / .6)
        if pr > 0: pen_circle(cv, 540, gy - 300, 450, 400, pr, PAL["pen"], 12, 11)
        if tl > c3[0] + .5: tag(cv, 700, gy - 790, "6 TINGKAT", 56, PAL["accent"], PAL["navy"], scale=back_out((tl - c3[0] - .5) / .3))
        # dimensi 62 m
        pd = ease_out((tl - c4[0]) / .6)
        if pd > 0:
            x = 960; pen_line(cv, (x, gy), (x, gy + (top - gy) * pd), 1.0, PAL["white"], 8, 3)
            cv.line([(x - 26, top), (x + 26, top)], PAL["white"], 8); cv.line([(x - 26, gy), (x + 26, gy)], PAL["white"], 8)
            v = ease_out((tl - c4[0]) / .9) * 62
            tag(cv, 760, top - 150, f"{int(v)} m", 120, PAL["accent"], PAL["navy"], scale=back_out((tl - c4[0]) / .3))
            # skala manusia
            person(cv, 120, gy + 10, 70, par=1.0); cv.text(120, gy + 56, "manusia", "sb", 30, PAL["navy"]); pen_line(cv, (150, gy - 62), (L_ := 540 - 360, gy - 62), clamp((tl - c4[0] - .4) / .5), PAL["pen"], 5, 4)
        return dict()

# ---------------- S3 ----------------
BX, BY = 540, 1270
def bent_profile(m=0.0):
    W2 = 475; kx = lerp(284, 194, m); kh = 262; Hh = lerp(527, 443, m)
    return W2, kx, kh, Hh
def lerp(a, b, k): return a + (b - a) * k
class S3:
    def bg(self, tl, S):
        c2 = ck(S, 2)[0]; g = ease_out((tl - c2) / .2) * (1 - ease_io((tl - c2 - .5) / 1.2))
        return sky_array(mix(hexc("#2A0E3A"), hexc("#5A0F1E"), g), mix(hexc("#7A1F5D"), hexc("#B02A2A"), g), None, 0, .8)
    def draw(self, cv, tl, S):
        c0, c1, c2, c3, c4 = [ck(S, i) for i in range(5)]
        zoom = 1 + .55 * ease_io((tl - c3[0] + .2) / .8) * (1 - ease_io((tl - S['marks']['d'] - .2) / .9))
        shake = math.exp(-max(0, tl - c2[0]) * 3.5) * (tl > c2[0])
        wz = (zoom - 1) / .55
        cv.cam(540 + (BX - 284 - 540) * wz, 960 + (BY - 262 - 960) * wz, zoom, 0, 12 * shake * math.sin(tl * 80), 9 * shake * math.cos(tl * 63))
        for gx in range(-400, 1500, 90): cv.line([(gx, 0), (gx, 2400)], (255, 255, 255, 18), 2, .5, cap=False)
        for gy in range(0, 2400, 90): cv.line([(-400, gy), (1500, gy)], (255, 255, 255, 18), 2, .5, cap=False)
        cv.poly([(-600, BY), (1700, BY), (1700, 2600), (-600, 2600)], hexc("#3A1230"))
        for hx in range(-600, 1700, 70): cv.line([(hx, BY + 8), (hx - 160, BY + 170)], (255, 255, 255, 22), 3, cap=False)
        cv.line([(-300, BY), (1400, BY)], PAL["cream"], 6)
        W2, kx, kh, Hh = bent_profile(0)
        BL, BR = (BX - W2, BY), (BX + W2, BY); KL, KR = (BX - kx, BY - kh), (BX + kx, BY - kh); AP = (BX, BY - Hh)
        # rencana ideal (54 derajat)
        ideal = (BX, BY - W2 * math.tan(math.radians(54)))
        pi_ = ease_out((tl - c0[0]) / 1.0)
        if pi_ > 0:
            pen_line(cv, BL, (BL[0] + (ideal[0] - BL[0]) * pi_, BL[1] + (ideal[1] - BL[1]) * pi_), 1.0, PAL["green"], 6, 9) if False else cv.line([BL, (BL[0] + (ideal[0] - BL[0]) * pi_, BL[1] + (ideal[1] - BL[1]) * pi_)], PAL["green"], 7, dash=(24, 16))
            cv.line([BR, (BR[0] + (ideal[0] - BR[0]) * pi_, BR[1] + (ideal[1] - BR[1]) * pi_)], PAL["green"], 7, dash=(24, 16))
            if tl < c2[0] + .1 and pi_ > .6: tag(cv, BX, ideal[1] - 70, "RENCANA", 46, PAL["green"], PAL["navy"], scale=ease_out((tl - c0[0] - .7) / .3))
        # bagian bawah tumbuh
        gl = ease_out((tl - c0[0] - .2) / (c2[0] - c0[0] - .2 if c2[0] > c0[0] + .5 else 1)) if tl < c2[0] else 1.0
        h_now = kh * clamp(gl)
        run = h_now / math.tan(math.radians(54))
        lowL = (BX - W2 + run, BY - h_now); lowR = (BX + W2 - run, BY - h_now)
        cv.poly([BL, BR, lowR, lowL], PAL["sand"]); cv.poly([(BX, BY), BR, lowR, (BX, lowR[1])], PAL["sandd"])
        for i in range(1, 6): 
            yy = BY - h_now * i / 6; f = i / 6
            cv.line([(BX - W2 + (W2 - 0) * 0 + run * f, yy), (BX + W2 - run * f, yy)], (120, 80, 35, 80), 3, cap=False)
        # sudut 54
        if tl > c1[0] and h_now > kh * .9 and tl < S['marks']['d']:
            ang = ease_out((tl - c1[0]) / .5)
            pts = [(BL[0] + 120 * math.cos(-math.radians(54) * ang * 1.0) , BL[1] + 120 * math.sin(-math.radians(54) * ang)) for ang in np.linspace(0, ang, 14)]
            cv.line(pts, PAL["accent"], 7); tag(cv, BL[0] + 175, BL[1] - 62, "54°", 70, PAL["accent"], PAL["navy"], scale=back_out((tl - c1[0]) / .3))
        # retak
        if tl >= c2[0]:
            pr = ease_out((tl - c2[0]) / .3)
            zig = [(KL[0] + 14, KL[1] + 10), (KL[0] + 52, KL[1] - 40), (KL[0] + 20, KL[1] - 86), (KL[0] + 70, KL[1] - 140)]
            zig2 = [(KR[0] - 14, KR[1] + 10), (KR[0] - 48, KR[1] - 36), (KR[0] - 18, KR[1] - 84)]
            for z_ in (zig, zig2): cv.line(z_[:max(2, int(len(z_) * pr) + 1)], PAL["red"], 12)
            if tl < c3[0] + .3: tag(cv, BX + 250, BY - 520, "RETAK!", 110, PAL["red"], PAL["white"], scale=back_out((tl - c2[0]) / .25), font="black")
        # bagian atas (dipangkas, sudut 43)
        if tl >= c3[0]:
            up = ease_out((tl - c3[0]) / .8)
            ux0, uy0 = KL[0] + (AP[0] - KL[0]) * up, KL[1] + (AP[1] - KL[1]) * up
            ux1 = KR[0] + (AP[0] - KR[0]) * up
            cv.poly([KL, KR, (ux1, uy0), (ux0, uy0)], mix(PAL["sandl"], PAL["white"], .35)); cv.poly([(BX, KL[1]), KR, (ux1, uy0), (BX, uy0)], mix(PAL["sandd"], PAL["sand"], .3))
            for i in range(1, 6):
                f = i / 6; yy = KL[1] + (AP[1] - KL[1]) * f * up
                cv.line([(KL[0] + (AP[0] - KL[0]) * f * up, yy), (KR[0] + (AP[0] - KR[0]) * f * up, yy)], (120, 80, 35, 70), 3, cap=False)
        cv.line([BL, KL, AP, KR, BR], PAL["cream"] if tl >= c3[0] else PAL["cream"], 6) if tl >= c3[0] + .9 else None
        # tag sudut akhir
        if tl >= c3[0] + .8 and tl < S["marks"]["d"] + .3:
            pen_circle(cv, KL[0], KL[1], 80, 80, ease_out((tl - c3[0] - .8) / .5), PAL["accent"], 9, 4); tag(cv, KL[0] - 20, KL[1] - 130, "TITIK PATAH", 40, PAL["accent"], PAL["navy"], scale=back_out((tl - c3[0] - 1.0) / .3))
        md, me = S["marks"]["d"], S["marks"]["e"]
        if tl >= md:
            tag(cv, BX - 400, BY - 110, "54°", 70, PAL["red"], PAL["white"], scale=back_out((tl - md) / .35))
        if tl >= me:
            a = back_out((tl - me) / .35); arrow(cv, (BX - 330, BY - 110), (BX - 230, BY - 175), PAL["cream"], 8)
            tag(cv, BX - 130, BY - 230, "43°", 100, PAL["green"], PAL["navy"], scale=a)
        return dict(flash=(PAL["red"], .45 * math.exp(-(tl - c2[0]) * 7)) if tl >= c2[0] else None, glitch=(c2[0] <= tl < c2[0] + .24))

# ---------------- S4 ----------------
class S4:
    def bg(self, tl, S): return sky_array(hexc("#FF7A5A"), hexc("#FFD58A"), (540, 900, hexc("#FFFFFF")), .25, .7)
    def draw(self, cv, tl, S):
        c0, c1, c2, c3 = [ck(S, i) for i in range(4)]
        cv.cam(540, 960 + 60 * (1 - ease_io(tl / (S["dur"] * .8))), 1.12 - .12 * ease_io(tl / (S["dur"] * .8)), 0, 0, 0)
        for i in range(10):
            a = i / 10 * 6.28 + tl * .4; cv.poly([(540, 980), (540 + math.cos(a - .08) * 1800, 980 + math.sin(a - .08) * 1800), (540 + math.cos(a + .08) * 1800, 980 + math.sin(a + .08) * 1800)], (255, 255, 255, 30), .3)
        for gy in range(0, 2400, 90): cv.line([(-400, gy), (1500, gy)], (255, 255, 255, 22), 2, .5, cap=False)
        cv.poly([(-600, BY), (1700, BY), (1700, 2600), (-600, 2600)], hexc("#E8A25A"))
        cv.line([(-300, BY), (1400, BY)], PAL["navy"], 6)
        m = ease_io((tl - c0[0] - .2) / .9)
        W2, kx, kh, Hh = bent_profile(m)
        BL, BR = (BX - W2, BY), (BX + W2, BY); KL, KR = (BX - kx, BY - kh), (BX + kx, BY - kh); AP = (BX, BY - Hh)
        red = ease_io((tl - c1[0]) / .8)
        cl = mix(PAL["sand"], hexc("#E2735A"), red); cr = mix(PAL["sandd"], hexc("#9A3D2C"), red)
        cv.poly([BL, KL, AP, (BX, AP[1]), (BX, BY)], cl); cv.poly([BR, KR, AP, (BX, AP[1]), (BX, BY)], cr)
        for i in range(1, 9):
            f = i / 9; yy = BY - Hh * f
            if yy > KL[1]: xl = BX - W2 + (W2 - kx) * (BY - yy) / kh
            else: xl = BX - kx * (1 - (KL[1] - yy) / (KL[1] - AP[1]))
            cv.line([(xl, yy), (2 * BX - xl, yy)], (80, 30, 20, 70), 3, cap=False)
        cv.line([BL, KL, AP, KR, BR], PAL["navy"], 6)
        if tl > c1[0]:
            pen_check(cv, BX - 290, BY - 650, 150, ease_out((tl - c1[0] - .2) / .5), PAL["green"], 26)
            tag(cv, BX + 20, BY - 740, "PIRAMIDA MERAH", 60, PAL["navy"], PAL["accent"], scale=back_out((tl - c1[0]) / .35))
            tag(cv, BX + 200, BY - 650, "43° • 105 m", 50, PAL["white"], PAL["navy"], scale=back_out((tl - c1[0] - .3) / .3))
        if tl > c3[0]:
            tag(cv, BX, BY + 110, "MULUS PERTAMA!", 60, PAL["green"], PAL["navy"], scale=back_out((tl - c3[0]) / .3))
            r = rs(5)
            for i in range(26):
                a = r.rand() * 6.28; sp = 150 + r.rand() * 520; p = (tl - c3[0]) * 1.0
                x = BX + math.cos(a) * sp * p; y = BY - 500 + math.sin(a) * sp * p + 220 * p * p
                cv.ell(x, y, 11, 11, [PAL["accent"], PAL["white"], PAL["green"]][i % 3] if p < 1.2 else (0, 0, 0, 0))
        return dict(flash=(PAL["white"], .35 * math.exp(-(tl - c1[0]) * 7)) if tl >= c1[0] else None)

# ---------------- S5 ----------------
def monas(cv, x, by, s, col):
    cv.poly([(x - 60 * s, by), (x + 60 * s, by), (x + 50 * s, by - 18 * s), (x - 50 * s, by - 18 * s)], mix(col, (0, 0, 0, 255), .15))
    cv.poly([(x - 18 * s, by - 18 * s), (x + 18 * s, by - 18 * s), (x + 8 * s, by - 120 * s), (x - 8 * s, by - 120 * s)], col)
    cv.poly([(x - 26 * s, by - 120 * s), (x + 26 * s, by - 120 * s), (x + 20 * s, by - 132 * s), (x - 20 * s, by - 132 * s)], mix(col, (255, 255, 255, 255), .15))
    cv.ell(x, by - 148 * s, 11 * s, 20 * s, PAL["accent"])
class S5:
    def bg(self, tl, S): return sky_array(hexc("#12082B"), hexc("#5A2A86"), (540, 1000, PAL["purple"]), .4, .75)
    def draw(self, cv, tl, S):
        c0, c1, c2, c3, c4 = [ck(S, i) for i in range(5)]
        stars(cv, 90, 9, tl, .9, .6)
        if tl < c4[0]:
            cv.cam(540, 1060, 1.0 + .05 * ease_io(tl / S["dur"]), 0, 0, 0)
            # piramida dibangun per baris dari bawah
            grow = clamp((tl - .15) / (c2[1] - .15))
            n = 46
            rr = rs(2)
            def pop(j):
                age = (tl - .15) - (j / n) * (c2[1] - .15); return 22 * max(0, 1 - age * 4) if age > 0 else 0
            cv.poly([(-600, 1335), (1700, 1335), (1700, 2600), (-600, 2600)], hexc("#2A1450"))
            draw_pyramid(cv, 540, 1330, 400, 470, PAL["sand"], PAL["sandd"], 1.0, courses=n, grow=grow, pop=pop)
            cv.line([(-300, 1335), (1400, 1335)], PAL["cream"], 5)
            v = ease_out((tl - .15) / (c2[1] - .15)) * 2300000
            big = 1 + .06 * math.exp(-((tl * 10) % 1) * 3) * (grow < 1)
            ty = 470 if tl < c3[0] else 470 - 120 * ease_io((tl - c3[0]) / .4)
            cv.text(540, ty, counter_fmt(v), "black", 150 * (1 if tl < c3[0] else 1 - .3 * ease_io((tl - c3[0]) / .4)), PAL["accent"], stroke=8, stroke_fill=PAL["shadow"])
            cv.text(540, ty + 105 * (1 if tl < c3[0] else .8), "BALOK BATU", "black", 64 * (1 if tl < c3[0] else .75), PAL["cream"], stroke=5, stroke_fill=PAL["shadow"])
            if tl >= c3[0]:
                a = back_out((tl - c3[0]) / .4)
                cv.text(540, 640, "20 TAHUN", "black", 170 * a, PAL["white"], stroke=8, stroke_fill=PAL["shadow"])
                m = int(20 * ease_out((tl - c3[0] - .1) / (c3[1] - c3[0] - .1)))
                for i in range(20):
                    x = 120 + i * 42.5; on = i < m
                    cv.rrect(x, 760, x + 32, 820, 8, PAL["accent"] if on else (255, 255, 255, 50))
        else:
            q = tl - c4[0]; k = ease_out(q / .5)
            cv.cam(540, 960, 1.0, 0, 0, 0)
            sc = 3.0; gy = 1300
            Hk = 146.6 * sc; Wk = 115 * sc; Hm = 132 * sc
            cv.poly([(-600, gy), (1700, gy), (1700, 2600), (-600, 2600)], hexc("#2A1450"))
            cv.line([(0, gy), (1080, gy)], PAL["cream"], 6)
            # Khufu (profil)
            hh = Hk * k
            cv.poly([(715 - Wk, gy), (715, gy - hh), (715, gy)], PAL["sand"]); cv.poly([(715, gy), (715, gy - hh), (715 + Wk, gy)], PAL["sandd"])
            monas(cv, 200, gy, 3.0 * k, hexc("#E7E3D8"))
            # garis perbandingan
            pl = ease_out((q - .5) / .5)
            if pl > 0:
                cv.line([(40, gy - Hk), (40 + 1000 * pl, gy - Hk)], PAL["accent"], 6, dash=(22, 14)); cv.line([(40, gy - Hm * 1.0), (400 * pl, gy - Hm * 1.0)], PAL["white"], 5, dash=(14, 12))
                tag(cv, 470, gy - Hk - 60, "+14,6 m", 90, PAL["accent"], PAL["navy"], scale=back_out((q - .8) / .3))
                tag(cv, 240, gy + 80, "MONAS 132 m", 44, PAL["white"], PAL["navy"], scale=ease_out((q - .6) / .3)); tag(cv, 760, gy + 80, "KHUFU 146,6 m", 44, PAL["accent"], PAL["navy"], scale=ease_out((q - .6) / .3))
            cv.text(540, 360, "LEBIH TINGGI", "black", 104, PAL["cream"], stroke=7, stroke_fill=PAL["shadow"]); cv.text(540, 490, "DARI MONAS", "black", 124, PAL["accent"], stroke=8, stroke_fill=PAL["shadow"])
        return dict(wipe=(c4[0] - .05, c4[0] + .15))

# ---------------- S6 ----------------
class S6:
    def bg(self, tl, S): return sky_array(hexc("#7EC4F8"), hexc("#FFE7B4"), (860, 420, hexc("#FFFFFF")), .5, .68)
    def draw(self, cv, tl, S):
        c0, c1, c2, c3 = [ck(S, i) for i in range(4)]
        cv.cam(540, 980, 1.0 + .06 * ease_io(tl / S["dur"]), 0, 0, 0)
        cv.ell(860, 420, 110, 110, mix(PAL["accent"], PAL["white"], .5), .2)
        desert(cv, 1400, [hexc("#F2C57A"), hexc("#EDB866"), hexc("#E6A95A")], t=tl)
        # tembok piramida (kanan) + tanjakan
        cv.poly([(700, 1330), (1500, 1330), (1500, 760), (1180, 940)], PAL["stone"]); cv.poly([(1180, 940), (1500, 760), (1500, 700), (1210, 700)], PAL["sandl"])
        for i in range(1, 6): cv.line([(700 + i * 52, 1470 - i * 106), (1500, 1470 - i * 106)], (120, 80, 35, 80), 3, cap=False)
        ramp = [(-100, 1470), (1180, 940), (1180, 1330)]
        cv.poly(ramp, PAL["sandl"]); cv.line([(-100, 1470), (1180, 940)], PAL["sandd"], 8)
        ang = math.atan2(940 - 1470, 1180 + 100); L = math.hypot(1280, 530)
        def onr(s): return (-100 + math.cos(ang) * s, 1470 + math.sin(ang) * s)
        prog = (tl * 95) % (L * 0.55) + 160
        # balok + kereta luncur
        bx, by = onr(prog + 380); 
        cv.poly([(bx - 120, by - 8), (bx + 120, by - 8), (bx + 120 + 20, by - 140), (bx - 120 + 20, by - 140)], PAL["stone"], outline=PAL["stoned"], w=4)
        cv.poly([(bx - 140, by + 4), (bx + 150, by + 4), (bx + 150, by - 8), (bx - 140, by - 8)], PAL["stoned"])
        # tali + pekerja
        for i in range(7):
            sx, sy = onr(prog + 70 - i * 105); lean = -.5
            cv.line([(sx + 10, sy - 70), (bx - 130, by - 20)], hexc("#7A5A2E"), 5)
            person(cv, sx, sy, 150, swing=math.sin(tl * 6 + i * .9) * .55, lean=math.cos(ang) * 0.0 + .8)
        cnt = ease_out((tl - .2) / 1.2) * 20000
        cv.text(540, 470, counter_fmt(cnt) + "+", "black", 200, PAL["cream"], stroke=9, stroke_fill=PAL["navy"]); cv.text(540, 610, "PEKERJA TERAMPIL", "black", 70, PAL["accent"], stroke=6, stroke_fill=PAL["navy"])
        # BUKAN BUDAK
        if c1[0] <= tl < c2[0] + .1:
            q = tl - c1[0]; tag(cv, 540, 780, "BUDAK", 110, PAL["red"], PAL["white"], scale=back_out(q / .3), font="black")
            if q > .3: pen_x(cv, 540, 780, 120, ease_out((q - .3) / .3), PAL["navy"], 20)
        if tl >= c3[0]:
            q = tl - c3[0]
            for i, (nm, col) in enumerate((("DIBAYAR", "#FFD23F"), ("DIBERI MAKAN", "#FF8A3D"), ("TERAMPIL", "#35D07F"))):
                a = back_out((q - i * .18) / .3); x = 190 + i * 350
                tag(cv, x, 770, nm, 40 if i != 1 else 36, hexc(col), PAL["navy"], scale=a)
                pen_check(cv, x, 860, 70, ease_out((q - i * .18 - .2) / .4), PAL["green"], 14)
        return dict()

# ---------------- S7 ----------------
class S7:
    def bg(self, tl, S):
        S_c2 = ck(S, 2)[0]; q = ease_io((tl - S_c2) / .6)
        return sky_array(mix(hexc("#5EA8F0"), hexc("#7A8BA0"), q), mix(hexc("#FFF0C8"), hexc("#D8C2A0"), q), (860, 520, hexc("#FFFFFF")), .6 * (1 - q * .6), .66)
    def draw(self, cv, tl, S):
        c0, c1, c2, c3 = [ck(S, i) for i in range(4)]
        tq = c2[0]; shake = math.exp(-max(0, tl - tq) * 2.2) * (tl > tq)
        cv.cam(540, 1060, 1.0 + .08 * ease_io(tl / S["dur"]), 0, 14 * shake * math.sin(tl * 85), 11 * shake * math.cos(tl * 71))
        desert(cv, 1280, [hexc("#F2C57A"), hexc("#EDB866"), hexc("#E6A95A")], t=tl)
        gy = 1335; bx = 540; w = 400; h = 470
        # inti bertingkat
        steps = 14; 
        for j in range(steps):
            f0 = j / steps; f1 = (j + 1) / steps; ww0 = w * (1 - f0) * .98; ww1 = w * (1 - f1)
            y0 = gy - h * f0; y1 = gy - h * f1
            cv.poly([(bx - ww0, y0), (bx + ww0 * .12, y0 + 52 * (1 - f0)), (bx + ww0 * .12, y1 + 52 * (1 - f1) - 4), (bx - ww1, y1 - 2)], PAL["stone"] if j % 2 else mix(PAL["stone"], PAL["sandl"], .2))
            cv.poly([(bx + ww0 * .12, y0 + 52 * (1 - f0)), (bx + ww0, y0), (bx + ww1, y1), (bx + ww0 * .12, y1 + 52 * (1 - f1) - 4)], PAL["stoned"])
        # selimut putih (pita-pita yang bisa lepas)
        n = 22
        for j in range(n):
            f0 = j / n; f1 = (j + 1) / n
            tf = tq + .15 + (1 - f0) * 0.55 + (j * 7 % 5) * .08
            age = tl - tf
            if age > 1.1: continue
            off = 0.0; rot = 0.0; al = 255
            if age > 0: off = 420 * age * age + 60 * age; rot = (.12 + (j % 3) * .1) * age * (1 if j % 2 else -1); al = int(255 * (1 - clamp(age / 1.1)))
            def P(px, py): 
                return (px + math.sin(rot) * 60 * age * (1 if j % 2 else -1) if age > 0 else px, py + off)
            A, L_, M_, R_ = pyr_pts(bx, gy, w, h)
            def pe(P_, u): return (A[0] + (P_[0] - A[0]) * (1 - u), A[1] + (P_[1] - A[1]) * (1 - u))
            lt = (244, 238, 222, al); dk = (168, 182, 208, al)
            cv.poly([P(*pe(L_, f0)), P(*pe(M_, f0)), P(*pe(M_, f1)), P(*pe(L_, f1))], lt)
            cv.poly([P(*pe(M_, f0)), P(*pe(R_, f0)), P(*pe(R_, f1)), P(*pe(M_, f1))], dk)
            if age <= 0: cv.line([P(*pe(L_, f0)), P(*pe(M_, f0)), P(*pe(R_, f0))], (120, 130, 150, 130), 3, cap=False)
        # kilau
        if tl < tq:
            r = rs(4)
            for i in range(10):
                x = bx - 260 + r.rand() * 500; y = gy - 40 - r.rand() * 420; ph = (tl * 1.3 + i * .37) % 1; s = 26 * math.sin(math.pi * ph)
                if s > 1: cv.line([(x - s, y), (x + s, y)], PAL["white"], 5); cv.line([(x, y - s), (x, y + s)], PAL["white"], 5)
        # debu
        if tl > tq:
            r = rs(8)
            for i in range(26):
                p = (tl - tq) * .6; x = 140 + r.rand() * 800; y = gy - r.rand() * 80 - p * 120 * r.rand(); rad = 40 + 80 * p * r.rand()
                cv.ell(x, y, rad, rad * .55, (210, 175, 125, int(120 * (1 - clamp(p / 1.8)) * (min(1, p * 4)))))
        # penghitung tinggi
        hv = 146.6 if tl < tq + 1.2 else lerp(146.6, 138.5, ease_io((tl - tq - 1.2) / 1.0))
        txt = f"{hv:.1f}".replace(".", ",") + " m"
        cv.text(540, 440, txt, "black", 190, PAL["navy"] if tl < tq else PAL["red"], stroke=0)
        if tl < tq: cv.text(540, 580, "TINGGI ASLI", "black", 66, PAL["navy"])
        else: cv.text(540, 580, "TINGGI KINI", "black", 66, PAL["red"])
        if tl > c2[0]: tag(cv, 540, 740, "GEMPA 1303 M", 64, PAL["red"], PAL["white"], scale=back_out((tl - c2[0]) / .3))
        return dict(flash=(PAL["white"], .5 * math.exp(-(tl - tq) * 9)) if tl >= tq else None, glitch=(tq <= tl < tq + .2))

# ---------------- S8 ----------------
class S8:
    def bg(self, tl, S):
        c2 = ck(S, 2)[0]; k = ease_io((tl - c2) / .9)
        return sky_array(mix(hexc("#2A0E3A"), PAL["navy"], k), mix(hexc("#7A1F5D"), PAL["orange"], k), (700, 1010, PAL["orange"]), k * 1.0, .58)
    def draw(self, cv, tl, S):
        c0, c1, c2, c3 = [ck(S, i) for i in range(4)]
        k2 = ease_io((tl - c2[0]) / 1.0)
        cv.cam(540, 1000 - 0 * k2, 1.05 - .0 * k2 + .0, 0, 0, 0)
        if k2 < 1:
            a = 1 - k2
            W2, kx, kh, Hh = bent_profile(0); BL, BR = (BX - W2, BY), (BX + W2, BY); KL, KR = (BX - kx, BY - kh), (BX + kx, BY - kh); AP = (BX, BY - Hh)
            cv.poly([BL, KL, AP, (BX, AP[1]), (BX, BY)], (232, 178, 106, int(255 * a))); cv.poly([BR, KR, AP, (BX, AP[1]), (BX, BY)], (185, 121, 58, int(255 * a)))
            cv.line([BL, KL, AP, KR, BR], (255, 244, 214, int(255 * a)), 6)
            if tl >= c1[0]:
                q = tl - c1[0]; fx = ease_out((q - .0) / .35)
                if q < 1.4: pen_x(cv, BX, BY - 260, 230, fx, PAL["red"], 28)
                else: pen_check(cv, BX, BY - 250, 260, ease_out((q - 1.4) / .4), PAL["green"], 34)
                if q < 1.4: tag(cv, BX, BY - 640, "GAGAL", 110, PAL["red"], PAL["white"], scale=back_out(q / .3), font="black")
                else: tag(cv, BX, BY - 640, "PONDASI KEAJAIBAN", 62, PAL["accent"], PAL["navy"], scale=back_out((q - 1.4) / .3))
        if k2 > 0:
            stars(cv, 70, 3, tl, .9 * k2, .5)
            sx, sy = 700, 1010
            cv.ell(sx, sy, 175, 175, mix(PAL["accent"], PAL["white"], .35), .2)
            desert(cv, 1160, [mix(PAL["purple"], PAL["orange"], .5), mix(PAL["purple"], PAL["orange"], .3), mix(PAL["shadow"], PAL["purple"], .45)], t=tl)
            giza(cv, tl, 0, 1.0)
            cv.text(540, 470, "DARI GAGAL", "black", 112, PAL["cream"], stroke=8, stroke_fill=PAL["shadow"]); cv.text(540, 600, "JADI KEAJAIBAN", "black", 96, PAL["accent"], stroke=8, stroke_fill=PAL["shadow"])
            if tl >= c3[1] - .1:
                q = tl - (c3[1] - .1); a = ease_out(q / .6)
                tag(cv, 540, 770, "SEJARAH DUNIA KUNO • BAGIAN 1", 40, PAL["white"], PAL["navy"], scale=a)
        return dict()
SCENE_OBJS = [S1(), S2(), S3(), S4(), S5(), S6(), S7(), S8()]
