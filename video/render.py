"""Render video 'Dunia dari Kode' — semua frame digambar dengan numpy + Pillow, lalu digabung dgn audio via ffmpeg."""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *

HY = 1180                      # garis horizon / permukaan danau
rng = np.random.RandomState(5)
F = "/usr/share/fonts/truetype/"
def font(p, s): return ImageFont.truetype(F + p, s)
MONO = font("jetbrains-mono/JetBrainsMono-Regular.ttf", 38)
MONOB = font("jetbrains-mono/JetBrainsMono-Bold.ttf", 38)
MONO_S = font("jetbrains-mono/JetBrainsMono-Regular.ttf", 30)
SANSB = font("dejavu/DejaVuSans-Bold.ttf", 44)
SANSB_BIG = font("dejavu/DejaVuSans-Bold.ttf", 118)
SANSB_H = font("dejavu/DejaVuSans-Bold.ttf", 72)
SANS = font("dejavu/DejaVuSans.ttf", 42)
SANS_S = font("dejavu/DejaVuSans.ttf", 36)

def sstep(a, b, x): 
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def ease(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def ease_io(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

XX = np.arange(W, dtype=np.float32)[None, :]
YY = np.arange(H, dtype=np.float32)[:, None]
DIST = None

# ---------- palet langit ----------
KEYS = [0.0, 0.15, 0.30, 0.45, 0.55, 0.68, 0.85, 1.0]
TOPS = np.array([(.12,.12,.32),(.22,.45,.82),(.20,.50,.90),(.25,.30,.65),(.18,.12,.38),(.06,.06,.20),(.01,.02,.07),(.005,.01,.05)])
HORS = np.array([(1.,.52,.38),(.98,.80,.62),(.70,.88,.98),(1.,.68,.35),(1.,.35,.30),(.45,.22,.42),(.08,.15,.32),(.07,.13,.28)])
def pal(tod_):
    top = np.array([np.interp(tod_, KEYS, TOPS[:, c]) for c in range(3)], np.float32)
    hor = np.array([np.interp(tod_, KEYS, HORS[:, c]) for c in range(3)], np.float32)
    return top, hor

# ---------- pra-komputasi dunia ----------
def smooth_noise1d(n, scale, seed):
    r = np.random.RandomState(seed)
    k = int(n / scale) + 3
    pts = r.rand(k)
    x = np.arange(n) / scale
    i = x.astype(int); f = x - i; f = f * f * (3 - 2 * f)
    return pts[i] * (1 - f) + pts[i + 1] * f

def fbm1d(n, seed, base=300, octs=5):
    s = np.zeros(n); a = 1.0; tot = 0
    for o in range(octs):
        s += a * smooth_noise1d(n, base / 2 ** o, seed + o); tot += a; a *= 0.5
    return s / tot

MARG = 500
MN = W + 2 * MARG
M_TOP = []   # y puncak tiap lapisan
cfg = [(380, 520, 1, 1.15), (300, 380, 20, 1.0), (240, 230, 40, 0.8)]
for k, (base, amp, seed, _) in enumerate(cfg):
    f = fbm1d(MN, seed, 260 - 60 * k)
    f = np.abs(f - 0.5) * 2         # ridged
    f = 1 - f
    h = base * 0.55 + amp * f ** 1.4 * 0.8
    M_TOP.append((HY - h).astype(np.float32))
M_H = [HY - m for m in M_TOP]

# awan
def make_clouds():
    CW, CH = W * 2, 760
    acc = np.zeros((CH, CW), np.float32); a = 1; tot = 0
    for o in range(6):
        sz = (5 * 2 ** o, 3 * 2 ** o)
        r = np.random.RandomState(100 + o).rand(sz[1] + 1, sz[0] + 1).astype(np.float32)
        im = Image.fromarray((r * 255).astype(np.uint8)).resize((CW, CH), Image.BICUBIC)
        acc += a * np.asarray(im, np.float32) / 255; tot += a; a *= 0.5
    acc /= tot
    yy = np.linspace(0, 1, CH)[:, None]
    acc *= (0.4 + 0.9 * np.exp(-((yy - 0.45) / 0.35) ** 2))   # lebih padat di tengah
    return acc
CLOUD = make_clouds()

# bintang
NS = 520
S_X = rng.rand(NS) * W; S_Y = rng.rand(NS) ** 0.8 * (HY - 120) + 20
S_B = rng.rand(NS) ** 2.5; S_P = rng.rand(NS) * 6.28; S_F = rng.rand(NS) * 2 + 1
# kunang-kunang
NF = 36
FF_X = rng.rand(NF) * W; FF_Y = HY + 90 + rng.rand(NF) * 500
FF_P = rng.rand(NF) * 6.28; FF_S = rng.rand(NF) * 1.2 + 0.4
# burung
BIRDS = [(rng.uniform(300, 640), rng.uniform(0.0, 1.0), rng.uniform(26, 40), rng.uniform(0, 6.28)) for _ in range(7)]

# foreground (tanjung + pinus + kabin) - pra-render 2x
def make_fg():
    S = 2
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (5, 7, 13, 255)
    def poly(pts): d.polygon([(x * S, y * S) for x, y in pts], fill=col)
    poly([(0, 1235), (70, 1228), (190, 1258), (300, 1308), (385, 1368), (430, 1430), (400, 1500), (260, 1560), (0, 1620)])
    poly([(W, 1262), (W - 80, 1254), (W - 200, 1280), (W - 320, 1330), (W - 410, 1400), (W - 440, 1470), (W - 380, 1540), (W - 200, 1600), (W, 1650)])
    poly([(0, 1760), (140, 1720), (330, 1740), (560, 1790), (800, 1760), (980, 1730), (W, 1740), (W, H), (0, H)])
    r = np.random.RandomState(9)
    def pine(x, base, h, w):
        tiers = 6
        poly([(x - w * 0.06, base), (x + w * 0.06, base), (x + w * 0.06, base - h * 0.12), (x - w * 0.06, base - h * 0.12)])
        for i in range(tiers):
            y1 = base - h * (0.08 + i * 0.15)
            y0 = base - h * (0.08 + (i + 1.35) * 0.15 + 0.02)
            ww = w * (1 - i / (tiers + 0.7)) * 0.5
            poly([(x - ww, y1), (x, y0), (x + ww, y1)])
    for x in np.linspace(10, 330, 9):
        b = 1250 + (x / 330) * 120 + r.uniform(-10, 20)
        pine(x + r.uniform(-14, 14), b, r.uniform(320, 640), r.uniform(100, 170))
    for x in np.linspace(W - 330, W - 10, 8):
        b = 1290 + ((W - x) / 330) * 100 + r.uniform(-10, 20)
        pine(x + r.uniform(-14, 14), b, r.uniform(300, 600), r.uniform(100, 170))
    # kabin kecil di tanjung kiri
    cx, cy = 190, 1330
    poly([(cx - 70, cy), (cx + 70, cy), (cx + 70, cy - 62), (cx - 70, cy - 62)])
    poly([(cx - 88, cy - 60), (cx, cy - 122), (cx + 88, cy - 60)])
    poly([(cx + 38, cy - 130), (cx + 54, cy - 130), (cx + 54, cy - 90), (cx + 38, cy - 98)])
    # alang-alang di bawah
    for x in np.linspace(0, W, 90):
        h = r.uniform(60, 190); xb = x + r.uniform(-6, 6)
        poly([(xb - 5, 1790 + (np.sin(x / 140) * 30)), (xb + r.uniform(-30, 30), 1790 - h), (xb + 5, 1790 + (np.sin(x / 140) * 30))])
    im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255
FG = make_fg()
CABIN_WIN = (190 - 22, 1330 - 42, 190 + 22, 1330 - 14)

def blur_arr(a, r):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255

def radial_q(cx, cy, sigma, qs=4):
    """kilau radial dihitung di resolusi 1/qs lalu diperbesar"""
    h, w = H // qs, W // qs
    xx = np.arange(w, dtype=np.float32)[None, :] * qs; yy = np.arange(h, dtype=np.float32)[:, None] * qs
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2)))
    return np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR), np.float32)

# ---------- DUNIA ----------
def world(t):
    td = tod(t)
    top, hor = pal(td)
    tw = t - T_WORLD0
    day = float(sstep(0.0, 0.18, td) * (1 - sstep(0.42, 0.66, td)))
    amb = 0.34 + 0.66 * day
    # langit
    v = np.clip(YY[:HY] / HY, 0, 1) ** 1.6
    sky = top[None, None, :] * (1 - v[..., None]) + hor[None, None, :] * v[..., None]
    sky = np.repeat(sky, W, axis=1).astype(np.float32)                   # (HY,W,3)
    img = np.zeros((H, W, 3), np.float32); img[:HY] = sky
    # aurora (malam)
    av = float(sstep(0.76, 0.92, td))
    if av > 0.01:
        qh, qw = HY // 3, W // 3
        xs = np.arange(qw, dtype=np.float32)[None, :] * 3; ys = np.arange(qh, dtype=np.float32)[:, None] * 3
        cy = 430 + 90 * np.sin(xs * 0.004 + tw * 0.5) + 55 * np.sin(xs * 0.011 - tw * 0.8)
        wd = 120 + 60 * np.sin(xs * 0.006 + tw * 0.3)
        ray = 0.55 + 0.45 * np.sin(xs * 0.09 + 3 * np.sin(xs * 0.01 + tw * 0.7) + tw * 1.3)
        a = np.exp(-((ys - cy) / wd) ** 2) * ray * (0.5 + 0.5 * np.sin(xs * 0.003 - tw * 0.4 + 1))
        a *= np.clip(1 - (ys - cy) / 500, 0.3, 1)
        m = np.clip((ys - cy) / (wd * 1.2), -1, 1) * 0.5 + 0.5
        c1 = np.array([0.15, 1.0, 0.55], np.float32); c2 = np.array([0.55, 0.3, 1.0], np.float32)
        col = c1[None, None] * (1 - m[..., None]) + c2[None, None] * m[..., None]
        aur = (a[..., None] * col * 0.85 * av).astype(np.float32)
        aur = np.asarray(Image.fromarray(np.clip(aur * 255, 0, 255).astype(np.uint8)).resize((W, HY), Image.BILINEAR), np.float32) / 255
        img[:HY] += aur
    # matahari / bulan: kilau
    s = tod_s = np.clip(td / 0.58, 0, 1)
    sx = W * (0.14 + 0.72 * s); sh = math.sin(math.pi * s)
    sy = HY + 55 - sh ** 0.85 * 930
    sun_on = float(sstep(-0.02, 0.05, td) * (1 - sstep(0.55, 0.60, td)))
    m_ = np.clip((td - 0.50) / 0.5, 0, 1)
    mx = W * (0.86 - 0.62 * m_); my = HY + 50 - (1 - (1 - m_) ** 2) * 700
    moon_on = float(sstep(0.50, 0.62, td))
    sun_col = np.array([1.0, 0.55, 0.28], np.float32) * (1 - sh) + np.array([1.0, 0.96, 0.82], np.float32) * sh
    glow = np.zeros((H, W, 3), np.float32)
    if sun_on > 0:
        g1 = radial_q(sx, sy, 210)[..., None] * sun_col * 0.5 * (1 - 0.55 * day)
        g2 = radial_q(sx, sy, 520, 8)[..., None] * sun_col * 0.16 * (1 - 0.7 * day)
        glow += (g1 + g2) * sun_on
    if moon_on > 0:
        mc = np.array([0.55, 0.7, 1.0], np.float32)
        glow += (radial_q(mx, my, 230)[..., None] * mc * 0.45 + radial_q(mx, my, 700, 8)[..., None] * mc * 0.12) * moon_on
    img += glow
    if sun_on > 0:
        d = np.sqrt((XX - sx) ** 2 + (YY[:HY] - sy) ** 2)
        disc = np.clip((98 - d) / 2 + 0.5, 0, 1)[..., None]
        img[:HY] = img[:HY] * (1 - disc * sun_on) + (sun_col * 1.15) * disc * sun_on
    if moon_on > 0:
        d = np.sqrt((XX - mx) ** 2 + (YY[:HY] - my) ** 2)
        disc = np.clip((82 - d) / 2 + 0.5, 0, 1)
        # kawah
        cr = np.zeros_like(disc)
        for (ox, oy, rr, k) in ((-25, -15, 20, .5), (28, 22, 26, .4), (10, -38, 13, .35), (-30, 32, 14, .3), (40, -12, 10, .3)):
            dd = np.sqrt((XX - (mx + ox)) ** 2 + (YY[:HY] - (my + oy)) ** 2)
            cr = np.maximum(cr, np.clip((rr - dd) / 3, 0, 1) * k)
        shade = np.clip(0.97 - cr * 0.28 - np.clip((d / 82), 0, 1) ** 3 * 0.1, 0, 1)
        mcol = np.array([0.93, 0.95, 1.0], np.float32)[None, None] * shade[..., None]
        img[:HY] = img[:HY] * (1 - disc[..., None] * moon_on) + mcol * disc[..., None] * moon_on
    # awan
    cv = (1 - 0.65 * float(sstep(0.62, 0.88, td)))
    dayf = float(sstep(0.08, 0.28, td) * (1 - sstep(0.40, 0.55, td)))
    ccol = hor * 1.05 * (1 - dayf) + np.array([1, 1, 1], np.float32) * dayf
    bright = np.clip(0.30 + 1.1 * float(top.mean()) + 0.55 * float(hor.mean()), 0.25, 1.1)
    ox = int(tw * 26) % W
    cl = CLOUD[:, ox:ox + W]
    ca = sstep(0.56, 0.80, cl) * cv * 0.9
    ca = np.concatenate([ca[:HY - 60 if 760 > HY - 60 else 760], np.zeros((max(HY - 760 - 0, 0) if False else 0, W), np.float32)], 0) if False else ca
    crow = ca.shape[0]
    y0 = 120
    shade_c = (0.78 + 0.22 * sstep(0.35, 0.75, cl))[..., None]
    region = img[y0:y0 + crow]
    cc = (ccol * bright)[None, None] * shade_c
    img[y0:y0 + crow] = region * (1 - ca[..., None]) + cc * ca[..., None]
    # bintang & percikan (RGB layer PIL)
    spark = Image.new("RGB", (W, H), (0, 0, 0)); sd = ImageDraw.Draw(spark)
    sv = float(sstep(0.58, 0.82, td))
    if sv > 0.01:
        tw_ = 0.55 + 0.45 * np.sin(t * S_F * 2.0 + S_P)
        for i in range(NS):
            b = S_B[i] * tw_[i] * sv * (0.25 + 0.75 * min(1, (HY - S_Y[i]) / 500)) * 1.9
            if b < 0.04: continue
            c = int(255 * min(b, 1)); col_ = (c, int(c * 0.95), int(c * (0.85 + 0.15 * (i % 3 == 0))))
            x, y = S_X[i], S_Y[i]
            if S_B[i] > 0.55:
                sd.ellipse([x - 2, y - 2, x + 2, y + 2], fill=col_)
                if S_B[i] > 0.8:
                    sd.line([(x - 7, y), (x + 7, y)], fill=col_, width=1); sd.line([(x, y - 7), (x, y + 7)], fill=col_, width=1)
            else:
                sd.point((x, y), fill=col_)
        for (ts, fx, fy) in SHOOTING:
            p = (t - ts) / 0.75
            if 0 <= p <= 1:
                ang = math.radians(205); L_ = 360
                hx = fx * W - math.cos(ang) * p * 700 * -1; hy = fy * HY + math.sin(ang) * p * 700 * -1
                hx = fx * W + math.cos(ang) * p * 800; hy = fy * HY - math.sin(ang) * p * 800
                for k in range(26):
                    q = k / 26; a_ = (1 - q) ** 1.6 * math.sin(math.pi * min(p * 1.2, 1))
                    x1 = hx - math.cos(ang) * L_ * q; y1 = hy + math.sin(ang) * L_ * q
                    c = int(255 * a_); sd.ellipse([x1 - 3 + q * 2, y1 - 3 + q * 2, x1 + 3 - q * 2, y1 + 3 - q * 2], fill=(c, c, int(c * 0.95)))
    # gunung
    offs = [tw * 3.0, tw * 6.0, tw * 10.0]
    for k in range(3):
        o = int(offs[k]) + MARG // 2
        top_ = M_TOP[k][o:o + W][None, :]
        cov = np.clip(YY[:HY] + 0.5 - top_, 0, 1)
        base = [(0.30, 0.32, 0.52), (0.17, 0.20, 0.36), (0.08, 0.10, 0.20)][k]
        fog = [0.55, 0.32, 0.12][k]
        c = (np.array(base, np.float32) * amb) * (1 - fog) + hor * fog
        if k == 2: c = c * 0.9
        col = np.repeat(c[None, None, :], W, 1)
        col = np.broadcast_to(c, (HY, W, 3)).copy()
        if k == 0:  # salju
            hh = M_H[0][o:o + W][None, :]
            sm = np.clip((hh - 470) / 90, 0, 1)
            wv = np.clip(1 - (YY[:HY] - top_) / (70 * sm + 1e-3), 0, 1) * (sm > 0)
            wv = wv * (0.7 + 0.3 * np.sin(XX * 0.17 + YY[:HY] * 0.05))
            snow = (hor * 0.45 + np.array([1, 1, 1], np.float32) * 0.55) * (0.35 + 0.65 * amb)
            col = col * (1 - wv[..., None]) + snow * wv[..., None]
        # bayangan lembut ke bawah (kabut)
        mist = np.clip((YY[:HY] - (HY - 140)) / 140, 0, 1)[..., None] * 0.55 * fog * 2
        col = col * (1 - mist) + hor * mist
        img[:HY] = img[:HY] * (1 - cov[..., None]) + col * cov[..., None]
    # bayangan di danau (cermin)
    Hw = H - HY
    ys = np.arange(Hw, dtype=np.float32)[:, None]
    ripple = np.sin(XX * 0.018 + ys * 0.11 + tw * 1.7) + 0.6 * np.sin(XX * 0.045 - ys * 0.07 + tw * 1.1)
    amp = 3 + ys * 0.045
    sx_ = np.clip((XX + ripple * amp).astype(np.int32), 0, W - 1)
    sy_ = np.clip((HY - 1 - ys * 0.92 + ripple[:, :1] * 0).astype(np.int32), 0, HY - 1)
    refl = img[:HY][sy_, sx_]
    depth = ys / Hw
    deep = top * 0.45 + hor * 0.08
    wc = refl * (0.78 - 0.30 * depth[..., None]) + deep[None, None] * (0.18 + 0.5 * depth[..., None])
    # kilau cahaya matahari/bulan
    rip = np.sin(XX * 0.11 + ys * 0.45 - tw * 2.4) * np.sin(XX * 0.07 - ys * 0.23 + tw * 1.6)
    for (lx, on, c_, st) in ((sx, sun_on * (1 if sy < HY else 0), sun_col, 1.0), (mx, moon_on, np.array([0.7, 0.8, 1.0], np.float32), 0.6)):
        if on > 0.01:
            wdt = 22 + ys * 0.22
            env = np.exp(-((XX - lx) / wdt) ** 2) * (1 - 0.35 * depth)
            sp = np.clip((rip - 0.2) * 2.2, 0, 1) * env * on * st
            wc = wc + sp[..., None] * c_[None, None] * 1.1 + env[..., None] * c_[None, None] * 0.06 * on
    wc = wc * (1 - 0.0) 
    # garis horizon cerah
    hl = np.exp(-((ys - 2) / 3) ** 2)[..., None] * hor[None, None] * 0.35
    img[HY:] = wc + hl
    # foreground
    fgcol = np.array([0.02, 0.03, 0.06], np.float32) + np.array([0.10, 0.07, 0.06], np.float32) * day * 0.4 + hor * 0.04
    a = FG[..., 3:4]
    img = img * (1 - a) + (fgcol[None, None] * (0.6 + 0.4 * amb)) * a
    # rim light halus pada tepi pohon dari glow horizon
    # jendela kabin + kunang-kunang + lampu
    nv = float(sstep(0.58, 0.8, td))
    if nv > 0.01:
        x0, y0_, x1, y1_ = CABIN_WIN
        fl = 0.9 + 0.1 * math.sin(t * 7.3) * math.sin(t * 3.1)
        sd.rectangle([x0, y0_, x1, y1_], fill=(int(255 * nv * fl), int(190 * nv * fl), int(90 * nv * fl)))
        sd.rectangle([x0 + 21, y0_, x0 + 23, y1_], fill=(30, 20, 8))
        for i in range(NF):
            bl = max(0, math.sin(t * FF_S[i] * 2 + FF_P[i])) ** 3 * nv
            x = FF_X[i] + 38 * math.sin(t * 0.6 * FF_S[i] + FF_P[i]); y = FF_Y[i] + 26 * math.cos(t * 0.5 * FF_S[i] + FF_P[i] * 2)
            c = int(255 * bl)
            if c > 10: sd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(c, int(c * 0.95), int(c * 0.4)))
    sp = np.asarray(spark, np.float32) / 255
    bl1 = np.asarray(spark.filter(ImageFilter.GaussianBlur(7)), np.float32) / 255
    bl2 = np.asarray(spark.filter(ImageFilter.GaussianBlur(26)), np.float32) / 255
    img += sp * 1.0 + bl1 * 1.4 + bl2 * 1.3
    # bloom dari area terang
    small = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    bm = np.asarray(small, np.float32) / 255
    bm = np.clip(bm - 0.85, 0, 1) * 2.0
    bm = np.asarray(Image.fromarray(np.clip(bm * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR), np.float32) / 255
    img += bm * 0.7
    out = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))
    # burung (siang)
    bv = float(sstep(0.0, 0.04, td) * (1 - sstep(0.42, 0.50, td)))
    if bv > 0.01:
        d = ImageDraw.Draw(out)
        for (by, ph, sz, p0) in BIRDS:
            u = (tw * 0.085 + ph * 0.18) % 1.4 - 0.2
            if not -0.15 < u < 1.15: continue
            x = u * W + 40 * math.sin(p0); y = by + 40 * math.sin(tw * 0.9 + p0) - u * 90
            f = math.sin(tw * 9 + p0)
            s_ = sz
            dark = (int(20 + 40 * (1 - amb)),) * 3
            pts_l = [(x - s_, y + f * s_ * 0.55 - 6), (x - s_ * 0.5, y + f * s_ * 0.2 - 10), (x, y)]
            pts_r = [(x, y), (x + s_ * 0.5, y + f * s_ * 0.2 - 10), (x + s_, y + f * s_ * 0.55 - 6)]
            d.line(pts_l, fill=dark, width=4, joint="curve"); d.line(pts_r, fill=dark, width=4, joint="curve")
    return np.asarray(out, np.float32) / 255

# ---------- SCENE KODE ----------
COL = {KW: (255, 121, 198), ST: (241, 250, 140), NU: (189, 147, 249), CM: (98, 114, 164), FN: (80, 250, 123), PL: (232, 236, 248), AT: (139, 233, 253)}
RAIN = []
for i in range(34):
    RAIN.append((i * 32 + 8, rng.uniform(80, 260), rng.uniform(0, 2500), [chr(c) for c in rng.choice(list(range(0x30, 0x3A)) + list(range(0x41, 0x5B)) + [0x7B, 0x7D, 0x3C, 0x3E, 0x2F, 0x3D, 0x28, 0x29], 60)]))
RFONT = font("jetbrains-mono/JetBrainsMono-Regular.ttf", 26)
WIN = (60, 430, 1020, 1330)
def make_codebg():
    top = np.array([6, 8, 20], np.float32); bot = np.array([16, 10, 38], np.float32)
    g = (YY / H)[..., None]
    base = top * (1 - g) + bot * g
    base = np.repeat(base, W, 1)
    # kilau di balik jendela
    glow = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(glow)
    d.rounded_rectangle(WIN, 28, fill=(40, 90, 200)); d.ellipse([-100, 1350, 500, 1900], fill=(110, 30, 160))
    glow = np.asarray(glow.filter(ImageFilter.GaussianBlur(120)), np.float32) * 0.55
    return (base + glow).astype(np.float32)
CODEBG = make_codebg()
CODE_WIN_IMG = None

def code_scene(t):
    img = Image.fromarray(np.clip(CODEBG, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    # hujan kode
    for (x, sp, ph, chars) in RAIN:
        head = (t * sp + ph) % (H + 700) - 300
        for j in range(14):
            y = head - j * 30
            if -30 < y < H:
                a = int(max(0, 120 * (1 - j / 14)) * (0.35 if WIN[0] < x < WIN[2] and WIN[1] < y < WIN[3] else 1))
                d.text((x, y), chars[(int(t * 8) + j * 7 + x) % 60], font=RFONT, fill=(90, 200, 255, int(a * 0.55)) if j else (220, 250, 255, a))
    # judul
    k = ease((t - 0.1) / 0.9)
    title = "Satu file. Satu dunia."
    tw_ = d.textlength(title, font=SANSB_H)
    yy = 250 + (1 - k) * 40
    for off, c in ((0, (120, 200, 255)),):
        d.text(((W - tw_) / 2 + 3, yy + 3), title, font=SANSB_H, fill=(0, 0, 0, int(180 * k)))
        d.text(((W - tw_) / 2, yy), title, font=SANSB_H, fill=(*c, int(255 * k)))
    sub = "dunia.py  →  video + audio"
    sw = d.textlength(sub, font=SANS_S)
    d.text(((W - sw) / 2, 352), sub, font=SANS_S, fill=(160, 175, 220, int(230 * k)))
    # jendela
    x0, y0, x1, y1 = WIN
    d.rounded_rectangle(WIN, 28, fill=(13, 16, 30, 245), outline=(70, 90, 160, 255), width=2)
    d.rounded_rectangle((x0, y0, x1, y0 + 66), 28, fill=(24, 28, 50, 255))
    d.rectangle((x0 + 2, y0 + 40, x1 - 2, y0 + 66), fill=(24, 28, 50, 255))
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((x0 + 30 + i * 36 - 9, y0 + 33 - 9, x0 + 30 + i * 36 + 9, y0 + 33 + 9), fill=c)
    d.text((x0 + 190, y0 + 18), "dunia.py", font=MONO_S, fill=(170, 180, 220))
    # teks kode
    n = sum(1 for tm in TYPE_TIMES if tm <= t)
    lh = 64; ty = y0 + 100; cw = d.textlength("M", font=MONO)
    li_last = -1; col_chars = 0; cur = None
    cx_ = {}
    idx = 0
    for li, line in enumerate(CODE):
        d.text((x0 + 22, ty + li * lh + 4), f"{li + 1:>2}", font=MONO_S, fill=(70, 82, 120))
        xx_ = x0 + 85
        for seg, c in line:
            part = seg[:max(0, n - idx)]
            if part:
                d.text((xx_, ty + li * lh), part, font=MONO, fill=COL[c])
                cur = (xx_ + len(part) * cw, ty + li * lh)
            xx_ += len(seg) * cw; idx += len(seg)
    if cur is None: cur = (x0 + 85, ty)
    if int(t * 2.2) % 2 == 0 and t < T_TYPE_END + 0.1 or t < T_TYPE_END:
        d.rectangle((cur[0] + 2, cur[1] + 4, cur[0] + 4 + cw * 0.6, cur[1] + 52), fill=(230, 240, 255, 230))
    # konsol / progres
    if t > T_TYPE_END + 0.05:
        p = np.clip((t - T_PROGRESS0) / (T_PROGRESS1 - T_PROGRESS0), 0, 1)
        d.text((x0, 1385), ">>> python dunia.py", font=MONO_S, fill=(120, 255, 160, 255))
        d.text((x0, 1432), f"Merender {int(p * 900):>3}/900 frame…", font=MONO_S, fill=(190, 200, 240, 255))
        d.rounded_rectangle((x0, 1490, x1, 1522), 14, fill=(30, 36, 64, 255))
        if p > 0.01:
            d.rounded_rectangle((x0, 1490, x0 + (x1 - x0) * p, 1522), 14, fill=(80, 200, 255, 255))
    return np.asarray(img, np.float32) / 255

# ---------- GALAKSI ----------
NG = 42000
g_r = (rng.rand(NG) ** 0.65) * 560
g_arm = rng.randint(0, 4, NG)
g_th = g_arm * (np.pi / 2) + 2.4 * np.log1p(g_r / 70) * 1.9 + rng.randn(NG) * (0.12 + g_r * 0.0007)
g_core_n = 9000
c_r = np.abs(rng.randn(g_core_n)) * 62; c_th = rng.rand(g_core_n) * 6.283
GR = np.concatenate([g_r, c_r]); GTH = np.concatenate([g_th, c_th])
GB = rng.rand(len(GR)) ** 1.6 * 0.8 + 0.2
G_NEB = None
def make_neb():
    acc = np.zeros((H // 4, W // 4, 3), np.float32)
    for col, seed in (((0.35, 0.1, 0.6), 1), ((0.1, 0.25, 0.6), 2), ((0.6, 0.15, 0.4), 3)):
        r = np.random.RandomState(seed)
        n = np.zeros((H // 4, W // 4), np.float32); a = 1
        for o in range(5):
            sz = (3 * 2 ** o, 5 * 2 ** o)
            m = r.rand(sz[1] + 1, sz[0] + 1).astype(np.float32)
            n += a * np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BICUBIC), np.float32) / 255; a *= .55
        n = sstep(0.5, 0.95, n / 1.8)
        acc += n[..., None] * np.array(col, np.float32)
    return np.asarray(Image.fromarray(np.clip(acc * 255 * 0.5, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
G_NEB = make_neb()
BG_STARS = [(rng.rand() * W, rng.rand() * H, rng.rand(), rng.rand() * 6.28) for _ in range(380)]

def galaxy(t, k_in):
    base = G_NEB * (0.45 + 0.25 * math.sin(t * 0.3))
    acc = np.zeros((H, W, 3), np.float32)
    ang = t * 0.35
    om = 1.0 / (1 + GR / 120) ** 0.7
    th = GTH + ang * om * 2.0
    sc = 0.35 + 0.65 * ease(k_in)
    x = GR * np.cos(th) * sc; y = GR * np.sin(th) * 0.42 * sc
    rot = math.radians(-22)
    xr = x * math.cos(rot) - y * math.sin(rot) + W / 2
    yr = x * math.sin(rot) + y * math.cos(rot) + 700
    rr = np.clip(GR / 560, 0, 1)[:, None]
    core = np.array([1.0, 0.82, 0.5], np.float32); mid = np.array([0.55, 0.75, 1.0], np.float32); outc = np.array([0.6, 0.35, 1.0], np.float32)
    c = np.where(rr < 0.35, core * (1 - rr / 0.35) + mid * (rr / 0.35), mid * (1 - (rr - 0.35) / 0.65) + outc * ((rr - 0.35) / 0.65)).astype(np.float32)
    bri = (GB * (1.1 - 0.5 * rr[:, 0]))[:, None] * 0.55
    ix = xr.astype(np.int32); iy = yr.astype(np.int32)
    fx = (xr - ix)[:, None]; fy = (yr - iy)[:, None]
    ok = (ix >= 0) & (ix < W - 1) & (iy >= 0) & (iy < H - 1)
    for dx, dy, w_ in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        np.add.at(acc, (iy[ok] + dy, ix[ok] + dx), (c * bri * w_)[ok])
    im = Image.fromarray(np.clip(acc * 255, 0, 255).astype(np.uint8))
    b1 = np.asarray(im.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    b2 = np.asarray(im.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
    b3 = np.asarray(im.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
    res = base + acc * 1.4 + b1 * 1.8 + b2 * 1.8 + b3 * 1.6
    # inti bersinar
    res += radial_q(W / 2, 700, 55)[..., None] * np.array([1.0, 0.85, 0.6], np.float32) * 0.9 * (0.4 + 0.6 * ease(k_in))
    star = Image.new("RGB", (W, H)); sd = ImageDraw.Draw(star)
    for (x_, y_, b, p) in BG_STARS:
        a = b * (0.5 + 0.5 * math.sin(t * 2 + p)); cc = int(255 * a ** 1.5)
        sd.ellipse([x_ - 1.3, y_ - 1.3, x_ + 1.3, y_ + 1.3], fill=(cc, cc, int(cc * .95))) if b > .6 else sd.point((x_, y_), fill=(cc, cc, cc))
    res += np.asarray(star, np.float32) / 255 * 0.9
    return np.clip(res, 0, 1.4)

# ---------- overlay teks ----------
CAPS = [(6.9, 10.4, "Fajar menyingsing di atas danau…"), (10.8, 14.6, "Gunung, awan, dan burung — semuanya dihitung."),
        (15.2, 18.8, "Lalu malam turun. Bintang pun menyala."), (19.2, 21.6, "Aurora menari… tanpa satu pun foto.")]
def caption(img, t):
    for (a, b, txt) in CAPS:
        if a <= t <= b:
            k = ease(min(1, (t - a) / 0.4, (b - t) / 0.4))
            lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            lines = [txt]
            if d.textlength(txt, font=SANSB) > 900:
                w_ = txt.split(" "); h = len(w_) // 2; lines = [" ".join(w_[:h]), " ".join(w_[h:])]
            wmax = max(d.textlength(l, font=SANSB) for l in lines)
            hh = 30 + 62 * len(lines)
            px = (W - wmax) / 2
            d.rounded_rectangle((px - 40, 14, px + wmax + 40, 14 + hh), 40, fill=(5, 8, 20, int(150 * k)))
            for j, l in enumerate(lines):
                lw = d.textlength(l, font=SANSB)
                d.text(((W - lw) / 2, 28 + 62 * j), l, font=SANSB, fill=(255, 255, 255, int(255 * k)))
            img.paste(lay, (0, int(1500 + (1 - k) * 25)), lay)
    return img

def title_overlay(img, t):
    if t < T_TITLE: return img
    q = t - T_TITLE
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    lines = [("DIBUAT 100%", 1320, SANSB_BIG, 0.0), ("DENGAN KODE", 1450, SANSB_BIG, 0.25)]
    for txt, y, f, delay in lines:
        k = ease((q - delay) / 0.7)
        if k <= 0: continue
        tw_ = d.textlength(txt, font=f)
        x = (W - tw_) / 2
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text((x, y + (1 - k) * 60), txt, font=f, fill=int(255 * k))
        grad = np.zeros((H, W, 3), np.uint8)
        gx = (np.arange(W)[None, :, None] / W + 0.15 * math.sin(t * 2)).clip(0, 1)
        c0 = np.array([90, 220, 255]); c1 = np.array([200, 120, 255]); c2 = np.array([255, 190, 120])
        gr = np.where(gx < 0.5, c0 * (1 - gx * 2) + c1 * gx * 2, c1 * (1 - (gx - .5) * 2) + c2 * (gx - .5) * 2)
        grad[:] = gr.astype(np.uint8)
        gl = mask.filter(ImageFilter.GaussianBlur(18))
        lay.paste(Image.fromarray(grad), (0, 0), gl.point(lambda v: int(v * 0.5)))
        lay.paste(Image.fromarray(grad), (0, 0), mask)
    k2 = ease((q - 0.9) / 0.8)
    if k2 > 0:
        for txt, y, f, c in (("Python  •  NumPy  •  Pillow  •  FFmpeg", 1640, SANS, (210, 220, 255)), ("Setiap piksel dan setiap bunyi — dihitung oleh kode.", 1710, SANS_S, (150, 165, 210))):
            tw_ = d.textlength(txt, font=f)
            d.text(((W - tw_) / 2, y + (1 - k2) * 20), txt, font=f, fill=(*c, int(255 * k2)))
    base = img.convert("RGBA"); base.alpha_composite(lay)
    return base.convert("RGB")

# ---------- komposisi frame ----------
NOISE = (np.random.RandomState(1).randn(H, W).astype(np.float32) * 0.018)
VIG = (1 - 0.42 * np.clip(((XX - W / 2) / (W * 0.75)) ** 2 + ((YY - H / 2) / (H * 0.7)) ** 2, 0, 1))[..., None].astype(np.float32)
DIST = np.sqrt((XX - W / 2) ** 2 + (YY - 880) ** 2)

def frame(i):
    t = i / FPS
    if t < T_REVEAL:
        out = code_scene(t)
        # zoom halus & kilat jelang reveal
        pre = sstep(T_REVEAL - 0.5, T_REVEAL, t)
        out = out * (1 + 0.5 * pre)
    elif t < T_REVEAL_END:
        c = code_scene(T_REVEAL)
        wd = world(t)
        r = ease((t - T_REVEAL) / (T_REVEAL_END - T_REVEAL)) * 1500
        m = np.clip((r - DIST) / 3 + 0.5, 0, 1)[..., None]
        ring = np.exp(-((DIST - r) / 22) ** 2)[..., None] * np.array([0.6, 0.9, 1.0], np.float32) * 1.2 * (1 - (t - T_REVEAL) / (T_REVEAL_END - T_REVEAL) * 0.6)
        out = c * 1.5 * (1 - 0.7 * (t - T_REVEAL) / (T_REVEAL_END - T_REVEAL)) * (1 - m) + wd * m + ring
    elif t < 21.0:
        out = world(t)
    else:
        wd = world(min(t, T_WORLD1))
        k = float(sstep(21.0, 22.6, t))
        z = 1 + 0.35 * ease((t - 21.0) / 1.6)
        if t > 21.0:
            cw, ch = W / z, H / z
            im = Image.fromarray(np.clip(wd * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H * 0.62 - ch * 0.62), (W + cw) / 2, (H * 0.62 + ch * 0.38)))
            wd = np.asarray(im, np.float32) / 255
        gx = galaxy(t, (t - 21.8) / 2.2)
        out = wd * (1 - k) + gx * k
        # kilatan di dentuman final
        fl = np.exp(-((t - T_FINAL - 0.05) / 0.12) ** 2 * (1 if t > T_FINAL else 0.25))
        out = out + 0.55 * fl
    # grading + vinyet + grain
    out = out * VIG
    sh = (np.random.RandomState(i % 9).randint(0, H), np.random.RandomState(i % 7).randint(0, W))
    out = out + np.roll(NOISE, sh, (0, 1))[..., None]
    out = np.clip(out, 0, 1)
    out = out ** (1 / 1.04)
    # fade
    f = 1.0
    if t < 0.35: f = t / 0.35
    if t > DUR - 1.8: f = max(0, (DUR - t) / 1.8)
    img = Image.fromarray((out * 255 * f).astype(np.uint8))
    img = caption(img, t)
    img = title_overlay(img, t) if f > 0 else img
    if f < 1: img = Image.fromarray((np.asarray(img, np.float32) * 1).astype(np.uint8))
    return np.asarray(img, np.uint8)

def work(i): return frame(i).tobytes()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        for ts in sys.argv[2:]:
            i = int(float(ts) * FPS); Image.fromarray(frame(i)).save(f"/tmp/claude-0/-home-user-OpenAssist-ID/e20ba525-a73c-5b58-a6ed-7c91748afa16/scratchpad/f_{ts}.png")
        sys.exit()
    import multiprocessing as mp
    out = sys.argv[1] if len(sys.argv) > 1 else "dunia_dari_kode.mp4"
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    with mp.Pool(4) as p:
        for k, b in enumerate(p.imap(work, range(n), chunksize=2)):
            ff.stdin.write(b)
            if k % 60 == 0: print("frame", k, "/", n, flush=True)
    ff.stdin.close(); ff.wait(); print("selesai", out)
