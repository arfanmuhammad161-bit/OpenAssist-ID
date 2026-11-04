"""Render 'Sejarah Piramida' — renderer 3D polygon buatan sendiri (numpy + Pillow)."""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *

F_ = "/usr/share/fonts/truetype/dejavu/"
def font(n, s): return ImageFont.truetype(F_ + n, s)
SANSB = font("DejaVuSans-Bold.ttf", 44); SANS_S = font("DejaVuSans.ttf", 30); SANSB_BIG = font("DejaVuSans-Bold.ttf", 104)
SANSB_YR = font("DejaVuSans-Bold.ttf", 88); SANS_TAG = font("DejaVuSans.ttf", 38); SANS_TINY = font("DejaVuSans.ttf", 24)
SANSB_TL = font("DejaVuSans-Bold.ttf", 22); SANSB_M = font("DejaVuSans-Bold.ttf", 46)

def sstep(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def ease(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def lerp(a, b, k): return a + (b - a) * k
def kf(t, pts):
    ts = [p[0] for p in pts]; vs = np.array([p[1] for p in pts], float)
    if vs.ndim == 1: return float(np.interp(t, ts, vs))
    return np.array([np.interp(t, ts, vs[:, c]) for c in range(vs.shape[1])])
def vis(t, a, b, f=.6): return float(sstep(a, a + f, t) * (1 - sstep(b - f, b, t)))

CX, CY, FOC = 540, 880, 1500
PITCH = 0.13
HY = int(CY - FOC * math.tan(PITCH))
XX = np.arange(W, dtype=np.float32)[None, :]; YY = np.arange(H, dtype=np.float32)[:, None]
rng = np.random.RandomState(6)

SKY = [(0, (.01, .02, .07), (.14, .12, .24)), (3.6, (.01, .02, .07), (.14, .12, .24)), (5, (.15, .2, .45), (1, .62, .35)), (8, (.28, .45, .8), (1, .8, .55)),
       (11, (.2, .5, .9), (.9, .9, .92)), (23, (.2, .48, .88), (.92, .9, .8)), (25, (.28, .4, .78), (1, .78, .5)), (29.5, (.28, .4, .78), (1, .75, .48)),
       (31, (.22, .5, .92), (.9, .93, .97)), (34.8, (.22, .5, .92), (.9, .93, .97)), (36, (.22, .14, .36), (1, .45, .22)), (40.5, (.15, .1, .3), (.95, .4, .22)),
       (43, (.08, .07, .2), (.7, .35, .3)), (45.5, (.01, .02, .08), (.15, .12, .25)), (50, (.01, .02, .08), (.15, .12, .25))]
def sky_pal(t):
    ts = [s[0] for s in SKY]
    return (np.array([np.interp(t, ts, [s[1][c] for s in SKY]) for c in range(3)], np.float32),
            np.array([np.interp(t, ts, [s[2][c] for s in SKY]) for c in range(3)], np.float32))
def p_light(t):
    top, hor = sky_pal(t); return float(np.clip(0.22 + 1.15 * top.mean() + 0.6 * hor.mean(), 0.22, 1.15))
STARVIS = [(0, 1), (4, 1), (5.5, .15), (7, 0), (40, 0), (41.5, .2), (44, 1), (50, 1)]
BODIES = [((.95, .97, 1), [(0, 760, 330, 60, 1), (3.4, 760, 330, 60, 1), (4.4, 760, 330, 60, 0)]),
          ((1, .7, .4), [(4.2, 300, HY + 60, 90, 0), (5, 300, HY + 10, 90, 1), (9.6, 260, HY - 170, 90, 1), (10.4, 260, HY - 170, 90, 0)]),
          ((1, .97, .85), [(10, 820, 300, 86, 0), (11, 820, 300, 86, 1), (22, 700, 320, 86, 1), (25, 230, HY - 140, 90, 1), (30, 200, HY - 100, 90, 1), (34.8, 200, HY - 100, 90, 1), (35.4, 200, HY - 100, 90, 0)]),
          ((1, .5, .25), [(35, 700, HY - 20, 100, 0), (36, 700, HY - 20, 100, 1), (40.5, 700, HY + 30, 100, .9), (41.6, 700, HY + 90, 100, 0)]),
          ((.95, .97, 1), [(43.5, 800, 340, 66, 0), (45, 800, 340, 66, 1), (50, 800, 340, 66, 1)])]
NS = 420; S_X = rng.rand(NS) * W; S_Y = rng.rand(NS) ** .9 * (HY - 60); S_B = rng.rand(NS) ** 2.2; S_P = rng.rand(NS) * 6.28; S_F = rng.rand(NS) * 2 + 1
DUST = [(rng.rand() * W, rng.rand() * H, rng.rand() * 1.5 + .5, rng.rand() * 6.28) for _ in range(110)]
def radial_q(cx, cy, sigma, qs=4):
    h, w = H // qs, W // qs
    xx = np.arange(w, dtype=np.float32)[None, :] * qs; yy = np.arange(h, dtype=np.float32)[:, None] * qs
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2)))
    return np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR), np.float32)

# ---------- kamera ----------
def p_dist(t):
    return kf(t, [(0, 1100), (3, 1100), (4.3, 280), (9.8, 320), (10.6, 440), (16, 450), (16.8, 560), (22.5, 640), (23.5, 760), (24.6, 1250), (29.8, 1150), (30.6, 700), (35, 900),
                  (35.8, 110), (41, 125), (41.8, 1100), (50, 1300)])
def p_ty(t):
    return kf(t, [(0, 50), (4.3, 24), (9.8, 26), (10.6, 40), (16, 42), (16.8, 40), (22.5, 62), (24.6, 55), (30.6, 62), (35, 62), (35.8, 7), (41, 8), (41.8, 55), (50, 55)])
def p_yaw(t): return 0.5 + 0.045 * t + 0.12 * math.sin(t * .25)
def shake(t):
    a = float(np.exp(-((t - 33.4) / 1.0) ** 2)) * float(sstep(32.3, 32.5, t))
    return (a * 9 * math.sin(t * 61), a * 7 * math.sin(t * 47 + 1))
def make_cam(t):
    yaw = p_yaw(t); sx, sy = shake(t)
    return dict(D=p_dist(t), yaw=yaw, ty=p_ty(t), ca=math.cos(yaw), sa=math.sin(yaw), cp=math.cos(PITCH), sp=math.sin(PITCH), sx=sx, sy=sy)
def proj(P, c):
    P = np.atleast_2d(np.asarray(P, float)); x = P[:, 0]; y = P[:, 1] - c["ty"]; z = P[:, 2]
    x1 = c["ca"] * x + c["sa"] * z; z1 = -c["sa"] * x + c["ca"] * z
    y2 = c["cp"] * y + c["sp"] * z1; z2 = c["cp"] * z1 - c["sp"] * y
    zc = z2 + c["D"]
    return np.stack([CX + c["sx"] + FOC * x1 / zc, CY + c["sy"] - FOC * y2 / zc], 1), zc

# ---------- piramida ----------
SAND = np.array([208, 172, 114], float); WEATH = np.array([188, 152, 100], float); WHITE = np.array([246, 240, 224], float)
REDT = np.array([196, 120, 92], float); NUBC = np.array([176, 118, 78], float)
TV = rng.uniform(.93, 1.05, 400)
LD = np.array([-.45, .65, -.6]); LD /= np.linalg.norm(LD)

def prof_tiers(H, kfun, n, rough, Hcut):
    out = []; dh = H / n
    for j in range(n):
        h0 = j * dh; h1 = (j + 1) * dh
        if h0 >= Hcut - 1e-6: break
        k0 = kfun(h0 / H); k1 = kfun(min(h1, H) / H)
        if h1 > Hcut:
            k1 = kfun(Hcut / H); h1 = Hcut
        kt = k0 - (k0 - k1) * (1 - 0.72 * rough)
        out.append((h0, h1, k0, kt))
    return out
DJ_H = [11.5, 10.5, 10.5, 10, 9.5, 9.5]; DJ_K = [1, .86, .73, .60, .47, .34]
def djoser_tiers(n):
    out = []; h = 0
    for i in range(6):
        f = float(np.clip(n - i, 0, 1))
        if f <= 0: break
        out.append((h, h + DJ_H[i] * f, DJ_K[i], DJ_K[i] - .03 if f >= 1 else DJ_K[i] - .03 * f)); h += DJ_H[i]
    return out

def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3: return pts
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def draw_pyr(d, off, ss, c, P, light, elev):
    """P: dict(x,z,hw,hd,tiers,col(array),casing(0..1 sweep),H,alpha,rough)"""
    a255 = int(255 * P["alpha"])
    if a255 < 3 or not P["tiers"]: return
    x0, z0, hw, hd = P["x"], P["z"], P["hw"], P["hd"]
    top = P["tiers"][-1]
    amb = 0.40 + 0.60 * light
    # bayangan
    Ht = top[1]
    sh_dir = np.array([-LD[0], -LD[2]]) / max(elev, .15)
    base = [(x0 - hw, z0 - hd), (x0 + hw, z0 - hd), (x0 + hw, z0 + hd), (x0 - hw, z0 + hd)]
    apex = (x0 + sh_dir[0] * Ht * (1 - top[3]) * 0 + sh_dir[0] * Ht * LD[1], z0 + sh_dir[1] * Ht * LD[1])
    hp = hull(base + [(x0 + top[3] * hw + sh_dir[0] * Ht * .65, z0 + sh_dir[1] * Ht * .65), (x0 - top[3] * hw + sh_dir[0] * Ht * .65, z0 + sh_dir[1] * Ht * .65)])
    if len(hp) >= 3:
        pts, _ = proj(np.array([(p[0], 0, p[1]) for p in hp]), c)
        d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=(10, 8, 14, int(95 * P["alpha"] * (0.4 + .6 * light))))
    # tingkat
    for ti, (h0, h1, k0, k1) in enumerate(P["tiers"]):
        a, b0, a1, b1 = hw * k0, hd * k0, hw * k1, hd * k1
        bc = [(x0 - a, z0 - b0), (x0 + a, z0 - b0), (x0 + a, z0 + b0), (x0 - a, z0 + b0)]
        tc = [(x0 - a1, z0 - b1), (x0 + a1, z0 - b1), (x0 + a1, z0 + b1), (x0 - a1, z0 + b1)]
        mid = (h0 + h1) / 2 / max(P["H"], 1)
        cased = P["casing"] > 0.001 and mid >= 1 - P["casing"]
        col = WHITE if cased else (WEATH * (1 - P["rough"]) + P["col"] * P["rough"] if False else P["col"])
        if P.get("bent", 0) > .01 and mid > .4476: col = col * (1 - .4 * P["bent"]) + WHITE * .4 * P["bent"]
        if not cased and P["rough"] > 0.2: col = col * (1 - .1 * P["rough"]) + WEATH * .1 * P["rough"]
        var = TV[(ti * 7) % 400] if not cased else 1.0 + .01 * math.sin(ti)
        for i in range(4):
            j = (i + 1) % 4
            p0 = np.array([bc[i][0], h0, bc[i][1]]); p1 = np.array([bc[j][0], h0, bc[j][1]]); p3 = np.array([tc[i][0], h1, tc[i][1]]); p2 = np.array([tc[j][0], h1, tc[j][1]])
            nrm = np.cross(p1 - p0, p3 - p0); ln = np.linalg.norm(nrm)
            if ln < 1e-9: continue
            nrm /= ln
            mid_pt = (p0 + p1 + p2 + p3) / 4
            if np.dot(nrm, mid_pt - np.array([x0, 0, z0])) < 0: nrm = -nrm
            # terlihat?
            Pm = mid_pt - np.array([0, c["ty"], 0]); x1 = c["ca"] * Pm[0] + c["sa"] * Pm[2]; z1 = -c["sa"] * Pm[0] + c["ca"] * Pm[2]
            pv = np.array([x1, c["cp"] * Pm[1] + c["sp"] * z1, c["cp"] * z1 - c["sp"] * Pm[1] + c["D"]])
            nv = np.array([c["ca"] * nrm[0] + c["sa"] * nrm[2], 0, 0]); n1z = -c["sa"] * nrm[0] + c["ca"] * nrm[2]
            nv = np.array([nv[0], c["cp"] * nrm[1] + c["sp"] * n1z, c["cp"] * n1z - c["sp"] * nrm[1]])
            if np.dot(nv, pv) >= 0: continue
            diff = max(0.0, float(np.dot(nrm, LD)))
            sh = (amb * (0.55 + 0.9 * diff)) * var * (1.35 if cased else 1.0) + (P.get("glow", 0) * 0.35)
            fc = tuple(int(np.clip(v * sh, 0, 255)) for v in col)
            pts, _ = proj(np.array([p0, p1, p2, p3]), c)
            oc = tuple(int(v * .86) for v in fc) if (not cased or True) else fc
            d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=fc + (a255,), outline=oc + (a255,))
        # bidang atas (teras) jika ada undakan
        if ti + 1 < len(P["tiers"]) and P["tiers"][ti + 1][2] < k1 - 1e-4 or ti == len(P["tiers"]) - 1:
            if k1 > 0.002:
                pts, _ = proj(np.array([(x, h1, z) for x, z in tc]), c)
                fc = tuple(int(np.clip(v * amb * 0.95 * var, 0, 255)) for v in col)
                d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=fc + (a255,), outline=tuple(int(v * .8) for v in fc) + (a255,))
    # kilau puncak jika berselimut
    if P["casing"] > .95 and P["alpha"] > .5:
        tp, _ = proj(np.array([(x0, top[1], z0)]), c)
        x, y = tp[0]; r = 10 + 6 * math.sin(P.get("tw", 0) * 5)
        d.line([(x - r * 3, (y - off)), (x + r * 3, (y - off))], fill=(255, 255, 240, 200), width=2 * ss // 2 + 1)
        d.line([(x, (y - off) - r * 3), (x, (y - off) + r * 3)], fill=(255, 255, 240, 200), width=2 * ss // 2 + 1)

# keyframes per piramida
T_K = (-300.0, -300.0); T_F = (0.0, 0.0); T_M = (260.0, 260.0)
def khufu_state(t):
    H = 146.6
    hc = kf(t, [(0, 138.5), (3.0, 138.5), (3.9, 0), (16.3, 0), (22.6, 146.6), (32.3, 146.6), (33.9, 138.5), (50, 138.5)])
    px = kf(t, [(0, T_K[0]), (15.0, T_K[0]), (15.8, 0), (23.2, 0), (24.8, T_K[0]), (50, T_K[0])]); pz = kf(t, [(0, T_K[1]), (15.0, T_K[1]), (15.8, 0), (23.2, 0), (24.8, T_K[1]), (50, T_K[1])])
    cs = kf(t, [(0, 0), (22.6, 0), (24.0, 1), (32.3, 1), (33.9, 0), (50, 0)])
    rg = kf(t, [(0, .55), (22.6, .6), (24.0, 0), (32.3, 0), (33.9, .55), (50, .55)])
    al = (1 - vis(t, 34.8, 41, .7) * 1.0) if 34.8 <= t <= 41.8 else 1.0
    al = 1.0 - float(sstep(34.8, 35.5, t)) * (1 - float(sstep(40.7, 41.5, t)))
    return dict(x=px, z=pz, hw=115, hd=115, H=H, hcut=hc, casing=cs, rough=rg, alpha=al, col=SAND)
def khafre_state(t):
    hc = kf(t, [(0, 136), (3.0, 136), (3.9, 0), (23.8, 0), (25.0, 143.9), (50, 143.9)])
    cs = kf(t, [(0, .28), (24.2, .28), (24.9, 1), (32.3, 1), (33.9, .28), (50, .28)]); rg = kf(t, [(0, .55), (24.9, 0), (32.3, 0), (33.9, .55), (50, .55)])
    al = 1.0 - float(sstep(34.8, 35.5, t)) * (1 - float(sstep(40.7, 41.5, t)))
    return dict(x=T_F[0], z=T_F[1], hw=107.5, hd=107.5, H=143.9, hcut=hc, casing=cs, rough=rg, alpha=al, col=SAND)
def menk_state(t):
    hc = kf(t, [(0, 62), (3.0, 62), (3.9, 0), (24.3, 0), (25.4, 65), (50, 65)])
    cs = kf(t, [(0, 0), (24.5, 0), (25.2, 1), (32.3, 1), (33.9, 0), (50, 0)]); rg = kf(t, [(0, .55), (25.2, 0), (32.3, 0), (33.9, .55), (50, .55)])
    al = 1.0 - float(sstep(34.8, 35.5, t)) * (1 - float(sstep(40.7, 41.5, t)))
    return dict(x=T_M[0], z=T_M[1], hw=51.5, hd=51.5, H=65, hcut=hc, casing=cs, rough=rg, alpha=al, col=SAND)
NUB = [(-55, 0, 6.5), (-33, 12, 4.5), (-14, -6, 5.5), (6, 10, 4.0), (25, -3, 3.5), (48, 6, 6.0)]

def build_pyramids(t):
    L = []
    # Djoser
    a = vis(t, 4.0, 10.4, .6)
    if a > .01:
        n = kf(t, [(4.0, 0), (4.4, 0), (9.0, 6), (50, 6)])
        L.append(dict(x=0, z=0, hw=60.5, hd=54.5, H=62, tiers=djoser_tiers(n), col=SAND * .98, casing=0, rough=1, alpha=a))
    # Snefru: Bent -> Red
    a = vis(t, 10.0, 16.4, .6)
    if a > .01:
        m = float(ease((t - 13.1) / 1.3))
        kb = lambda f: float(np.interp(f, [0, .4476, 1], [1, .71, 0])); kr = lambda f: 1 - f
        kfun = lambda f: lerp(kb(f), kr(f), m)
        hw = lerp(94, 110, m)
        L.append(dict(x=0, z=0, hw=hw, hd=hw, H=105, tiers=prof_tiers(105, kfun, 64, .35, 105), col=SAND * (1 - m * .35) + REDT * m * .35, casing=0, rough=.35, alpha=a, bent=1 - m))
    # trio
    for st in (khafre_state(t), menk_state(t), khufu_state(t)):
        if st["hcut"] > 0.3 and st["alpha"] > .01:
            kfun = lambda f: max(0.0, 1 - f)
            P = dict(x=st["x"], z=st["z"], hw=st["hw"], hd=st["hd"], H=st["H"], tiers=prof_tiers(st["H"], kfun, 90 if st["H"] > 100 else 50, st["rough"], st["hcut"]),
                     col=st["col"], casing=st["casing"], rough=st["rough"], alpha=st["alpha"])
            P["tw"] = t
            P["glow"] = float(kf(t, [(0, 0), (43, 0), (45, .45), (50, .5)]))
            L.append(P)
    # Nubia
    a = vis(t, 35.0, 41.8, .7)
    if a > .01:
        for (x, z, hw) in NUB:
            Hn = hw * 2.7
            L.append(dict(x=x, z=z, hw=hw, hd=hw, H=Hn, tiers=prof_tiers(Hn, lambda f: 1 - f, 22, .8, Hn), col=NUBC, casing=0, rough=.8, alpha=a))
    return L

def sun_elev(t): return kf(t, [(0, .5), (5, .35), (9, .6), (11, .85), (23, .8), (25, .45), (30, .4), (31, .8), (35, .8), (36, .3), (41, .2), (44, .5), (50, .5)])

# ---------- latar ----------
def ground_img(t, c, light, hor):
    rows = np.arange(HY + 1, H, 2, dtype=np.float32)[:, None]; cols = np.arange(0, W, 2, dtype=np.float32)[None, :]
    a_ = -(rows - CY) / FOC
    s = (-c["ty"] - c["sp"] * c["D"]) / (c["cp"] * a_ - c["sp"] + 1e-9)
    s = np.clip(s, 1, 60000)
    X1 = (cols - CX) / FOC * s; Y2 = a_ * s; Z2 = s - c["D"]
    yw = c["cp"] * Y2 - c["sp"] * Z2; z1 = c["sp"] * Y2 + c["cp"] * Z2
    xw = c["ca"] * X1 - c["sa"] * z1; zw = c["sa"] * X1 + c["ca"] * z1
    big = .5 + .5 * np.sin(zw * .0105 + 2.2 * np.sin(xw * .006 + zw * .0035))
    big2 = .5 + .5 * np.sin(xw * .0075 - zw * .0055 + 1.7 * np.sin(zw * .004))
    fine = np.sin(xw * .5 + zw * .21 + 3 * np.sin(zw * .09)) * np.clip(1 - s / 700, 0, 1) * .5 + .5
    sh = .78 + .16 * big + .08 * big2 + .06 * fine
    base = np.array([.80, .64, .42], np.float32) * (0.30 + 0.70 * light)
    col = base[None, None] * sh[..., None]
    haze = 1 - np.exp(-s / 2600.0)
    col = col * (1 - haze[..., None]) + hor[None, None] * haze[..., None] * .95
    im = Image.fromarray(np.clip(col * 255, 0, 255).astype(np.uint8)).resize((W, H - HY - 1), Image.BILINEAR)
    return np.asarray(im, np.float32) / 255

def background(t, c, light):
    top, hor = sky_pal(t)
    v = np.clip(YY[:HY] / HY, 0, 1) ** 1.5
    img = np.zeros((H, W, 3), np.float32)
    img[:HY] = np.repeat(top[None, None] * (1 - v[..., None]) + hor[None, None] * v[..., None], W, 1)
    glow = np.zeros((H, W, 3), np.float32)
    for col, keys in BODIES:
        tg = [k[0] for k in keys]
        if not tg[0] <= t <= tg[-1]: continue
        x, y, r, a = [np.interp(t, tg, [k[i] for k in keys]) for i in (1, 2, 3, 4)]
        if a < .01: continue
        col = np.array(col, np.float32)
        gk = 1 - .62 * min(1, max(0, (light - .45) / .6))
        glow += radial_q(x, y, r * 2.4)[..., None] * col * .42 * a * gk + radial_q(x, y, r * 6, 8)[..., None] * col * .15 * a * gk
        dd = np.sqrt((XX - x) ** 2 + (YY[:HY] - y) ** 2); disc = np.clip((r - dd) / 2 + .5, 0, 1)[..., None] * a
        img[:HY] = img[:HY] * (1 - disc) + col * 1.15 * disc
    img += glow
    img[HY + 1:] = ground_img(t, c, light, hor)
    img[HY] = img[HY + 1]
    sv = kf(t, STARVIS)
    spark = Image.new("RGB", (W, H)); sd = ImageDraw.Draw(spark)
    if sv > .02:
        tw_ = .55 + .45 * np.sin(t * S_F * 2 + S_P)
        for i in range(NS):
            b = S_B[i] * tw_[i] * sv * 1.9 * (.3 + .7 * min(1, (HY - S_Y[i]) / 400))
            if b < .05: continue
            cc = int(255 * min(b, 1)); x, y = S_X[i], S_Y[i]
            if S_B[i] > .55: sd.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(cc, cc, int(cc * .9)))
            else: sd.point((x, y), fill=(cc, cc, cc))
    for (x, y, sp_, ph) in DUST:
        xx = (x + t * 26 * sp_) % W; yy = (y - t * 4 * sp_) % H
        cc = int(55 + 35 * math.sin(t + ph)); sd.ellipse([xx - 1.5, yy - 1.5, xx + 1.5, yy + 1.5], fill=(cc, int(cc * .9), int(cc * .7)))
    # debu gempa
    dq = float(sstep(32.4, 32.8, t) * (1 - sstep(34.2, 36.0, t)))
    if dq > .02:
        bp, _ = proj(np.array([(0, 0, 0)]), c)
        for i in range(36):
            ang = i * 2.4; r_ = 60 + 40 * (i % 7) + (t - 32.4) * 60
            x = CX + math.cos(ang) * r_ * 1.6; y = bp[0][1] + 20 - (t - 32.4) * 40 * (1 + i % 3) * .5 + math.sin(ang) * 30
            rad = 30 + 6 * (i % 5) + (t - 32.4) * 14; cc = int(42 * dq)
            sd.ellipse([x - rad, y - rad * .6, x + rad, y + rad * .6], fill=(cc, int(cc * .85), int(cc * .6)))
    sp_ = np.asarray(spark, np.float32) / 255; bl = np.asarray(spark.filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
    return img + sp_ * (1 if sv > .02 else .8) + bl * 1.0

# ---------- overlay ----------
def ramp_and_workers(d, off, ss, c, t, khufu):
    if not 16.4 < t < 23.2: return
    hc = khufu["hcut"]
    if hc < 4: return
    # pilih sisi yang menghadap kamera-kiri
    vd = np.array([-math.sin(.6), -math.cos(.6)])
    wd = np.array([c["ca"] * vd[0] - c["sa"] * vd[1], c["sa"] * vd[0] + c["ca"] * vd[1]])
    normals = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    fi = int(np.argmax([wd[0] * n[0] + wd[1] * n[1] for n in normals])); n = np.array(normals[fi], float); tg = np.array([-n[1], n[0]])
    kt = 1 - hc / khufu["H"]; hw = khufu["hw"]
    base_pt = np.array([khufu["x"], khufu["z"]]) + n * (hw + 280); top_pt = np.array([khufu["x"], khufu["z"]]) + n * hw * kt
    wdt = 14
    q = [base_pt - tg * wdt, base_pt + tg * wdt, top_pt + tg * wdt, top_pt - tg * wdt]
    hs = [0, 0, hc, hc]
    pts, _ = proj(np.array([(p[0], h_, p[1]) for p, h_ in zip(q, hs)]), c)
    d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=(228, 206, 160, 255), outline=(150, 120, 80, 255))
    for k in range(18):
        u = ((t * .12 + k / 18) % 1.0)
        pos = base_pt + (top_pt - base_pt) * u; hh = hc * u
        pp, zz = proj(np.array([(pos[0], hh + 1.2, pos[1])]), c)
        rad = max(2.2, 0.0 + 6.5 * FOC / zz[0] * .55)
        x, y = pp[0]
        d.rectangle([(x - rad) * ss, (y - off - rad) * ss, (x + rad) * ss, (y - off + rad) * ss], fill=(110, 82, 52, 255), outline=(60, 44, 28, 255))

def render_layer(t, c, light):
    ss = 2; Y0, HH = 380, 1300
    lay = Image.new("RGBA", (W * ss, HH * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    pyrs = build_pyramids(t); elev = sun_elev(t)
    for P in pyrs: P["dep"] = float(proj(np.array([(P["x"], 0, P["z"])]), c)[1][0])
    pyrs.sort(key=lambda P: -P["dep"])
    # bayangan dulu agar tidak menimpa piramida lain
    kh = khufu_state(t)
    for P in pyrs:
        draw_pyr(d, Y0, ss, c, P, light, elev)
        if P is not None and abs(P["x"] - kh["x"]) < 1 and abs(P["z"] - kh["z"]) < 1 and P["hw"] == 115:
            ramp_and_workers(d, Y0, ss, c, t, kh)
    lay = lay.resize((W, HH), Image.LANCZOS)
    return np.asarray(lay, np.float32) / 255, Y0, HH, kh

def hud(img, t, kh):
    out = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if t > 4.0:
        k = ease((t - 4.0) / .8) * (1 - ease((t - 48.8) / .8)); y = 110; x0, x1 = 90, W - 90
        d.line([(x0, y), (x1, y)], fill=(255, 235, 190, int(110 * k)), width=3)
        idx = max(0, sum(1 for s in SCENES[1:] if t >= s[0]) - 1)
        prog = (idx + min(1, (t - SCENES[idx + 1][0]) / (SCENES[idx + 1][1] - SCENES[idx + 1][0]))) / (len(NODES) - 1)
        d.line([(x0, y), (x0 + (x1 - x0) * min(prog, 1), y)], fill=(255, 215, 130, int(255 * k)), width=5)
        for i, n in enumerate(NODES):
            x = x0 + (x1 - x0) * i / (len(NODES) - 1); on = i <= idx; rr = 11 if i == idx else 7
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 215, 130, int(255 * k)) if on else (40, 40, 60, int(220 * k)), outline=(255, 235, 190, int(255 * k)))
            if i == idx:
                tw_ = d.textlength(n, font=SANSB_TL); d.text((min(max(x - tw_ / 2, 20), W - tw_ - 20), y + 26), n, font=SANSB_TL, fill=(255, 235, 190, int(255 * k)))
    for (a, b, yr, tag) in SCENES[1:]:
        if a <= t < b:
            k = ease(min((t - a) / .7, (b - t) / .5, 1))
            tw_ = d.textlength(yr, font=SANSB_YR)
            mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text(((W - tw_) / 2, 215 + (1 - k) * 30), yr, font=SANSB_YR, fill=int(255 * k))
            grad = np.zeros((H, W, 3), np.uint8); gy = np.clip((np.arange(H)[:, None] - 215) / 105.0, 0, 1)[..., None]
            grad[:] = (np.array([255, 236, 170]) * (1 - gy) + np.array([232, 160, 60]) * gy).astype(np.uint8)
            lay.paste(Image.new("RGBA", (W, H), (0, 0, 0, 150)), (0, 0), mask.filter(ImageFilter.GaussianBlur(10)))
            lay.paste(Image.fromarray(grad), (0, 0), mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .55))); lay.paste(Image.fromarray(grad), (0, 0), mask)
            tw2 = d.textlength(tag, font=SANS_TAG)
            d.text(((W - tw2) / 2 + 2, 322 + (1 - k) * 20), tag, font=SANS_TAG, fill=(0, 0, 0, int(200 * k))); d.text(((W - tw2) / 2, 320 + (1 - k) * 20), tag, font=SANS_TAG, fill=(255, 245, 225, int(255 * k)))
    for (a, b, txt) in INFO:
        if a <= t <= b:
            k = ease(min((t - a) / .5, (b - t) / .5, 1)); tw_ = d.textlength(txt, font=SANS_S)
            d.text(((W - tw_) / 2 + 2, 384), txt, font=SANS_S, fill=(0, 0, 0, int(210 * k))); d.text(((W - tw_) / 2, 382), txt, font=SANS_S, fill=(255, 215, 140, int(255 * k)))
    # penghitung pembangunan Khufu
    if 16.6 < t < 23.6:
        k = ease(min((t - 16.6) / .6, (23.6 - t) / .5, 1)); fr = float(np.clip(kh["hcut"] / 146.6, 0, 1))
        n = int(2300000 * fr); s = f"{n:,}".replace(",", ".") + " balok"; yrs = f"Tahun ke-{1 + int(19 * fr)} dari ± 20"
        wmax = max(d.textlength(s, font=SANSB_M), d.textlength(yrs, font=SANS_S))
        d.rounded_rectangle((W / 2 - wmax / 2 - 36, 1370, W / 2 + wmax / 2 + 36, 1370 + 118), 32, fill=(6, 8, 20, int(165 * k)))
        d.text(((W - d.textlength(s, font=SANSB_M)) / 2, 1382), s, font=SANSB_M, fill=(255, 226, 150, int(255 * k)))
        d.text(((W - d.textlength(yrs, font=SANS_S)) / 2, 1440), yrs, font=SANS_S, fill=(225, 230, 255, int(255 * k)))
    for (a, b, txt, ref) in CAPS:
        if a <= t <= b:
            k = ease(min((t - a) / .45, (b - t) / .45, 1)); words = txt.split(" "); lines = [""]
            for w_ in words:
                if d.textlength((lines[-1] + " " + w_).strip(), font=SANSB) > 880: lines.append(w_)
                else: lines[-1] = (lines[-1] + " " + w_).strip()
            hh = 28 + 58 * len(lines); wmax = max(d.textlength(l, font=SANSB) for l in lines); top = 1560 + (1 - k) * 24
            d.rounded_rectangle((W / 2 - wmax / 2 - 40, top, W / 2 + wmax / 2 + 40, top + hh), 36, fill=(6, 8, 20, int(165 * k)))
            for j, l in enumerate(lines): d.text(((W - d.textlength(l, font=SANSB)) / 2, top + 18 + 58 * j), l, font=SANSB, fill=(255, 255, 255, int(255 * k)))
    if t < 4.2:
        k = ease((t - .5) / 1.0) * (1 - ease((t - 3.2) / .7))
        for txt, y, col in (("SEJARAH", 300, (255, 236, 180)), ("PIRAMIDA", 420, (240, 190, 90))):
            tw_ = d.textlength(txt, font=SANSB_BIG); d.text(((W - tw_) / 2 + 4, y + 4 + (1 - k) * 40), txt, font=SANSB_BIG, fill=(0, 0, 0, int(160 * k))); d.text(((W - tw_) / 2, y + (1 - k) * 40), txt, font=SANSB_BIG, fill=col + (int(255 * k),))
        s = "Keajaiban dunia kuno yang masih berdiri"; tw_ = d.textlength(s, font=SANS_TAG); d.text(((W - tw_) / 2, 575), s, font=SANS_TAG, fill=(220, 225, 255, int(230 * k)))
    if t > 46.6:
        k = ease((t - 46.8) / .9); k2 = ease((t - 47.9) / .9); f_ = font("DejaVuSans-Bold.ttf", 92); txt = "4.500 TAHUN"
        tw_ = d.textlength(txt, font=f_); d.text(((W - tw_) / 2 + 3, 600 + 3 + (1 - k) * 30), txt, font=f_, fill=(0, 0, 0, int(170 * k))); d.text(((W - tw_) / 2, 600 + (1 - k) * 30), txt, font=f_, fill=(255, 232, 170, int(255 * k)))
        for txt, y, f2, col in (("berdiri menantang waktu. Warisan Dunia UNESCO sejak 1979.", 715, SANS_S, (225, 230, 255)), ("Dibuat 100% dengan kode • Python · NumPy · Pillow", 1700, SANS_TINY, (180, 185, 215))):
            tw_ = d.textlength(txt, font=f2); d.text(((W - tw_) / 2, y), txt, font=f2, fill=col + (int(255 * k2),))
    out.alpha_composite(lay)
    return np.asarray(out.convert("RGB"), np.float32) / 255

NOISE = np.random.RandomState(1).randn(H, W).astype(np.float32) * 0.012
VIG = (1 - 0.38 * np.clip(((XX - W / 2) / (W * .75)) ** 2 + ((YY - H / 2) / (H * .7)) ** 2, 0, 1))[..., None].astype(np.float32)

def frame(i):
    t = i / FPS; c = make_cam(t); light = p_light(t)
    img = background(t, c, light)
    la, Y0, HH, kh = render_layer(t, c, light)
    img[Y0:Y0 + HH] = img[Y0:Y0 + HH] * (1 - la[..., 3:4]) + la[..., :3] * la[..., 3:4]
    sm = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    bm = np.clip(np.asarray(sm, np.float32) / 255 - .8, 0, 1) * 2.0
    bm = np.asarray(Image.fromarray(np.clip(bm * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR), np.float32) / 255
    img += bm * .8
    img += .8 * np.exp(-((t - 23.2) / .14) ** 2) * 0.5 + .35 * np.exp(-((t - 3.5) / .12) ** 2)
    img = img * VIG
    sh = (np.random.RandomState(i % 9).randint(0, H), np.random.RandomState(i % 7).randint(0, W))
    img = np.clip(img + np.roll(NOISE, sh, (0, 1))[..., None], 0, 1) ** (1 / 1.04)
    f = 1.0
    if t < .4: f = t / .4
    if t > DUR - 1.6: f = max(0, (DUR - t) / 1.6)
    img = hud(img, t, kh)
    return (np.clip(img * f, 0, 1) * 255).astype(np.uint8)

def work(i): return frame(i).tobytes()
if __name__ == "__main__":
    sp = "/tmp/claude-0/-home-user-OpenAssist-ID/e20ba525-a73c-5b58-a6ed-7c91748afa16/scratchpad/"
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        for ts in sys.argv[2:]: Image.fromarray(frame(int(float(ts) * FPS))).save(sp + f"p_{ts}.png")
        sys.exit()
    import multiprocessing as mp
    out = sys.argv[1] if len(sys.argv) > 1 else "sejarah_piramida.mp4"; n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    with mp.Pool(4) as p:
        for k, b in enumerate(p.imap(work, range(n), chunksize=2)):
            ff.stdin.write(b)
            if k % 100 == 0: print("frame", k, "/", n, flush=True)
    ff.stdin.close(); ff.wait(); print("selesai", out)
