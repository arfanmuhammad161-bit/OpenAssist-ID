"""Render 'Sejarah Ka'bah' — 3D wireframe-polygon renderer buatan sendiri (numpy + Pillow)."""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *

F_ = "/usr/share/fonts/truetype/dejavu/"
def font(n, s): return ImageFont.truetype(F_ + n, s)
SANSB = font("DejaVuSans-Bold.ttf", 44); SANSB_S = font("DejaVuSans-Bold.ttf", 34)
SANS_S = font("DejaVuSans.ttf", 30); SANSB_BIG = font("DejaVuSans-Bold.ttf", 108); SANSB_YR = font("DejaVuSans-Bold.ttf", 92)
SANS_TAG = font("DejaVuSans.ttf", 38); SANS_TINY = font("DejaVuSans.ttf", 24); SANSB_TL = font("DejaVuSans-Bold.ttf", 22)

def sstep(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def ease(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def eio(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def kf(t, pts):  # interpolasi keyframe [(t,v),...] (v bisa tuple)
    ts = [p[0] for p in pts]; vs = np.array([p[1] for p in pts], float)
    if vs.ndim == 1: return float(np.interp(t, ts, vs))
    return np.array([np.interp(t, ts, vs[:, c]) for c in range(vs.shape[1])])

CX, CY, FOC = 540, 880, 1500
PITCH = 0.12
HY = int(CY - FOC * math.tan(PITCH))
XX = np.arange(W, dtype=np.float32)[None, :]; YY = np.arange(H, dtype=np.float32)[:, None]
rng = np.random.RandomState(4)

# ---- palet langit per adegan (waktu, top, horizon)
SKY = [
 (0, (.01, .02, .07), (.10, .12, .26)), (3.5, (.02, .03, .09), (.12, .14, .28)), (5.5, (.10, .13, .32), (.95, .60, .35)),
 (9, (.14, .24, .52), (.98, .75, .50)), (11.5, (.10, .05, .10), (.72, .25, .15)), (14.5, (.14, .08, .12), (.80, .40, .25)),
 (17, (.30, .50, .85), (.95, .80, .55)), (21, (.30, .50, .85), (.95, .80, .55)), (23, (.35, .60, .95), (1, .90, .70)),
 (26, (.35, .60, .95), (1, .88, .68)), (28, (.07, .04, .12), (.80, .30, .10)), (31, (.10, .06, .14), (.75, .32, .14)),
 (33.5, (.01, .01, .04), (.09, .08, .16)), (36.5, (.01, .01, .04), (.09, .08, .16)), (38, (.08, .12, .20), (.30, .40, .50)),
 (42, (.12, .17, .26), (.36, .46, .56)), (44, (.01, .03, .10), (.12, .15, .30)), (50, (.01, .03, .10), (.12, .15, .30))]
def sky_pal(t):
    ts = [s[0] for s in SKY]
    top = np.array([np.interp(t, ts, [s[1][c] for s in SKY]) for c in range(3)], np.float32)
    hor = np.array([np.interp(t, ts, [s[2][c] for s in SKY]) for c in range(3)], np.float32)
    return top, hor
STARVIS = [(0, 1), (4, 1), (5.5, .2), (7, 0), (11, .15), (14, .1), (16, 0), (26, 0), (28, .3), (31, .5), (33.5, 1), (37, 1), (38, 0), (43, 0), (44, 1), (50, 1)]
# benda langit (t, x, y, r, rgb, alpha)
BODY = [
 (0, 800, 330, 62, (.95, .97, 1), 1), (3.4, 800, 330, 62, (.95, .97, 1), 1), (4.4, 800, 330, 62, (.95, .97, 1), 0),
 (4.2, 300, HY + 70, 92, (1, .65, .35), 0), (5.0, 300, HY + 20, 92, (1, .65, .35), 1), (9.6, 300, HY - 150, 92, (1, .8, .5), 1), (10.6, 300, HY - 150, 92, (1, .8, .5), 0),
 (10.8, 880, HY - 30, 84, (1, .35, .2), 0), (11.8, 880, HY - 30, 84, (1, .35, .2), .9), (14.6, 880, HY - 20, 84, (1, .35, .2), .9), (15.4, 880, HY - 20, 84, (1, .35, .2), 0),
 (15.6, 700, 330, 86, (1, .97, .85), 0), (16.6, 700, 330, 86, (1, .97, .85), 1), (21.6, 700, 330, 86, (1, .97, .85), 1), (22.2, 540, 280, 100, (1, 1, .9), 1), (26.6, 540, 280, 100, (1, 1, .9), 1),
 (27.4, 200, HY - 10, 90, (1, .5, .2), 0), (28.0, 200, HY - 10, 90, (1, .5, .2), .9), (31.5, 200, HY + 20, 90, (1, .45, .2), .9), (32.5, 200, HY + 80, 90, (1, .45, .2), 0),
 (43.3, 230, 330, 70, (.95, .97, 1), 0), (44.5, 230, 330, 70, (.95, .97, 1), 1), (50, 230, 330, 70, (.95, .97, 1), 1)]
# --- bintang, gunung, awan statis
NS = 420; S_X = rng.rand(NS) * W; S_Y = rng.rand(NS) ** 0.9 * (HY - 60); S_B = rng.rand(NS) ** 2.2; S_P = rng.rand(NS) * 6.28; S_F = rng.rand(NS) * 2 + 1
def smooth_noise1d(n, scale, seed):
    r = np.random.RandomState(seed); k = int(n / scale) + 3; pts = r.rand(k); x = np.arange(n) / scale
    i = x.astype(int); f = x - i; f = f * f * (3 - 2 * f); return pts[i] * (1 - f) + pts[i + 1] * f
def fbm1d(n, seed, base, octs=5):
    s = np.zeros(n); a = 1; tot = 0
    for o in range(octs): s += a * smooth_noise1d(n, base / 2 ** o, seed + o); tot += a; a *= .5
    return s / tot
MW = W * 3
RIDGE = [HY - (70 + 190 * (1 - np.abs(fbm1d(MW, 3 + 7 * k, 220 - 50 * k) - .5) * 2) ** 1.2 * (1 - 0.25 * k)) for k in range(2)]
CW_, CH_ = W * 2, 560
def make_clouds():
    acc = np.zeros((CH_, CW_), np.float32); a = 1; tot = 0
    for o in range(6):
        r = np.random.RandomState(100 + o).rand(3 * 2 ** o + 1, 5 * 2 ** o + 1).astype(np.float32)
        acc += a * np.asarray(Image.fromarray((r * 255).astype(np.uint8)).resize((CW_, CH_), Image.BICUBIC), np.float32) / 255; tot += a; a *= .5
    return acc / tot
CLOUD = make_clouds()
DUST = [(rng.rand() * W, rng.rand() * H, rng.rand() * 1.5 + .5, rng.rand() * 6.28) for _ in range(90)]

def radial_q(cx, cy, sigma, qs=4):
    h, w = H // qs, W // qs
    xx = np.arange(w, dtype=np.float32)[None, :] * qs; yy = np.arange(h, dtype=np.float32)[:, None] * qs
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2)))
    return np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR), np.float32)

# ---------- parameter dunia per waktu ----------
def p_height(t):
    return kf(t, [(0, 13), (3.0, 13), (3.9, 0.0), (4.2, 0.0), (8.6, 4.5), (15.8, 4.5), (18.6, 9.0), (28.2, 9.0), (30.4, 13.0), (38.0, 13.0), (39.4, 8.5), (40.0, 8.5), (42.2, 13.0), (50, 13)])
def p_kiswa(t):  # 0 batu, 1 kiswah
    return kf(t, [(0, 1), (3.0, 1), (3.8, 0), (22.0, 0), (22.7, 1), (50, 1)])
def p_black(t):  # kiswah marun -> hitam
    return kf(t, [(0, 0), (22.9, 0), (23.0, 1), (38.0, 1), (41.0, 0), (50, 0)])
def p_depth(t):  # faktor denah (683 M: lebih panjang karena Hijr dimasukkan)
    return kf(t, [(0, 1), (27.6, 1), (29.5, 1.38), (31.0, 1.38), (32.4, 1.0), (50, 1)])
def p_hijr(t):
    return kf(t, [(0, 0), (18.6, 0), (19.5, 1), (27.4, 1), (28.0, 0), (31.8, 0), (32.6, 1), (50, 1)])
def p_dist(t):
    return kf(t, [(0, 44), (3.0, 44), (4.3, 29), (8.6, 29), (15, 31), (19, 35), (26, 38), (28, 40), (31, 44), (43, 46), (50, 53)])
def p_yaw(t): return 0.35 + 0.052 * t + 0.1 * math.sin(t * 0.3)
def p_crowd(t):
    return kf(t, [(0, .10), (3, .10), (4, 0), (9, 0), (10, .04), (15, .1), (19, .3), (22, .35), (26, .55), (28, .35), (30, .25), (33, .08), (36, .0), (37.4, 0), (43, .0), (44, 1.0), (50, 1)])
def p_light(t):
    top, hor = sky_pal(t); return float(np.clip(0.30 + 1.15 * top.mean() + 0.55 * hor.mean(), 0.28, 1.15))
def p_water(t):
    return kf(t, [(0, 0), (37.4, 0), (38.7, 2.4), (39.6, 3.2), (41.0, 1.2), (42.4, 0), (50, 0)])
def p_warm(t):   # cahaya hangat lampu masjid
    return kf(t, [(0, .5), (3, .5), (4, 0), (43, 0), (44.5, 1), (50, 1)])

# ---------- 3D ----------
def make_cam(t):
    Hc = p_height(t); D = p_dist(t); yaw = p_yaw(t)
    ty = 0.38 * max(Hc, 4.5) + 0.8
    return dict(D=D, yaw=yaw, ty=ty, ca=math.cos(yaw), sa=math.sin(yaw), cp=math.cos(PITCH), sp=math.sin(PITCH))
def proj(P, c):
    P = np.atleast_2d(np.asarray(P, float)); x = P[:, 0]; y = P[:, 1] - c["ty"]; z = P[:, 2]
    x1 = c["ca"] * x + c["sa"] * z; z1 = -c["sa"] * x + c["ca"] * z
    y2 = c["cp"] * y + c["sp"] * z1; z2 = c["cp"] * z1 - c["sp"] * y
    zc = z2 + c["D"]
    return np.stack([CX + FOC * x1 / zc, CY - FOC * y2 / zc], 1), zc
def rotn(n, c):
    x1 = c["ca"] * n[0] + c["sa"] * n[2]; z1 = -c["sa"] * n[0] + c["ca"] * n[2]
    return np.array([x1, c["cp"] * n[1] + c["sp"] * z1, c["cp"] * z1 - c["sp"] * n[1]])

# batu-batu: potongan acak per sisi & lapisan
BLK = {}
for fi in range(4):
    rows = []
    for j in range(40):
        n = rng.randint(4, 7); cuts = np.sort(rng.rand(n - 1)); cuts = np.concatenate([[0], cuts * .9 + .05, [1]])
        rows.append((cuts, rng.uniform(.82, 1.06, len(cuts) - 1)))
    BLK[fi] = rows
LDIR = np.array([-.5, .55, -.65]); LDIR /= np.linalg.norm(LDIR)
COURSE = 0.5

def scene_items(t, c, ss):
    """kembalikan daftar (kedalaman, fungsi gambar) untuk lapisan objek 3D"""
    items = []
    Hh = p_height(t); kk = p_kiswa(t); blk = p_black(t); dep = p_depth(t); light = p_light(t); warm = p_warm(t)
    hw, hd = 5.5, 6.45 * dep
    corners = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    normals = [np.array([0, 0, -1.]), np.array([1., 0, 0]), np.array([0, 0, 1.]), np.array([-1., 0, 0])]
    kc = np.array([70, 22, 28]) * blk + np.array([13, 13, 16]) * (1 - blk)
    glow_k = 0.0
    def P3(u, v, fi, Hv):
        a = corners[fi]; b = corners[(fi + 1) % 4]
        return (a[0] + u * (b[0] - a[0]), v * Hv, a[1] + u * (b[1] - a[1]))
    def quad(fi, u0, u1, v0, v1, Hv):
        pts3 = [P3(u0, v0, fi, Hv), P3(u1, v0, fi, Hv), P3(u1, v1, fi, Hv), P3(u0, v1, fi, Hv)]
        return proj(np.array(pts3), c)
    # lantai marmer + cincin + air
    def draw_floor(d, off):
        ang = np.linspace(0, 2 * np.pi, 72)
        fs = min(1.0, (c["D"] - 7) / 40)
        for r_, col in ((40, (26, 24, 24)), (36, (150, 146, 134)), (30, (162, 158, 146))):
            r_ = r_ * fs
            pts, _ = proj(np.stack([r_ * np.cos(ang), np.zeros_like(ang), r_ * np.sin(ang)], 1), c)
            f_ = tuple(int(v_ * (0.25 + 0.75 * light)) for v_ in col)
            d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=f_ + (255,))
        for r_ in range(8, 36, 4):
            r_ = r_ * fs
            pts, _ = proj(np.stack([r_ * np.cos(ang), np.zeros_like(ang), r_ * np.sin(ang)], 1), c)
            d.line([(x * ss, (y - off) * ss) for x, y in pts], fill=(int(110 * (.3 + .7 * light)),) * 3 + (90,), width=max(1, ss))
        # tepi plaza hangat di malam akhir
        if warm > 0.05:
            pts, _ = proj(np.stack([37 * fs * np.cos(ang), np.zeros_like(ang), 37 * fs * np.sin(ang)], 1), c)
            d.line([(x * ss, (y - off) * ss) for x, y in pts], fill=(255, 200, 110, int(200 * warm)), width=3 * ss)
    items.append((1e9, draw_floor))
    # Hijr Ismail: dinding setengah lingkaran di sisi belakang
    hj = p_hijr(t)
    if hj > 0.02:
        ang = np.linspace(-np.pi / 2, np.pi / 2, 18)
        zc0 = hd - 0.1
        for k in range(len(ang) - 1):
            a0, a1 = ang[k], ang[k + 1]
            def seg(a):
                return (3.4 * math.sin(a) * 1.0, zc0 + 3.2 * math.cos(a) if False else 0)
            p0 = np.array([3.5 * math.sin(a0), 0, zc0 + 3.5 * math.cos(a0) * 0 + 3.5 * (1 - math.cos(a0)) * -0 + 3.5 * math.cos(a0)])
            p1 = np.array([3.5 * math.sin(a1), 0, zc0 + 3.5 * math.cos(a1)])
            hh = 1.5 * hj
            pts, zs = proj(np.array([p0, p1, p1 + [0, hh, 0], p0 + [0, hh, 0]]), c)
            col = tuple(int(v_ * (0.35 + 0.65 * light)) for v_ in (225, 220, 205))
            def dr(d, off, pts=pts, col=col):
                d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=col + (255,), outline=(90, 85, 75, 255))
            items.append((float(zs.mean()), dr))
    # tawaf: titik-titik berputar
    crowd = p_crowd(t)
    nd = 0
    for ri, r_ in enumerate(np.linspace(9, 34, 14)):
        n = int(r_ * 4.2)
        omega = 0.9 / (1 + r_ * 0.07) * 0.5
        for k in range(n):
            if RK[ri][k % len(RK[ri])] > crowd: continue
            th = 2 * np.pi * k / n + RJ[ri][k % len(RJ[ri])] * .2 + omega * t * (1 + .15 * RJ[ri][(k * 3) % len(RJ[ri])])
            rr = r_ + RJ[ri][(k * 7) % len(RJ[ri])] * .8
            # hindari menembus Ka'bah
            if abs(rr * math.cos(th)) < hw + 1.2 and abs(rr * math.sin(th)) < hd + 1.2: continue
            if p_water(t) > 0.1: continue
            pt, zz = proj(np.array([[rr * math.cos(th), 0.0, rr * math.sin(th)]]), c)
            if zz[0] < 6: continue
            x, y = pt[0]; rad = max(1.6, 0.30 * FOC / zz[0] * 0.55)
            def dr(d, off, x=x, y=y, rad=rad, ri=ri):
                col = (250, 245, 232, 255)
                d.ellipse([(x - rad) * ss, (y - off - rad * 0.8) * ss, (x + rad) * ss, (y - off + rad * 0.8) * ss], fill=col)
            items.append((float(zz[0]) - 0.0, dr))
    # Ka'bah
    if Hh > 0.05:
        # atap
        top = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
        pts, zs = proj(np.array([(x, Hh, z) for x, z in top]), c)
        def dr_roof(d, off, pts=pts):
            d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=(34, 30, 28, 255), outline=(60, 55, 50, 255))
        items.append((1e8, dr_roof))
        for fi in range(4):
            n_w = normals[fi]
            fc = np.array([(corners[fi][0] + corners[(fi + 1) % 4][0]) / 2, Hh / 2, (corners[fi][1] + corners[(fi + 1) % 4][1]) / 2])
            pc, zc_ = proj(fc[None], c)
            nv = rotn(n_w, c)
            # posisi pusat sisi dalam koordinat kamera
            P = fc - np.array([0, c["ty"], 0]); x1 = c["ca"] * P[0] + c["sa"] * P[2]; z1 = -c["sa"] * P[0] + c["ca"] * P[2]
            pv = np.array([x1, c["cp"] * P[1] + c["sp"] * z1, c["cp"] * z1 - c["sp"] * P[1] + c["D"]])
            if np.dot(nv, pv) >= 0: continue
            shade = (0.30 + 0.70 * max(0, float(np.dot(n_w, LDIR)))) * (0.35 + 0.65 * light) + 0.10 * warm
            depth = float(zc_[0])
            # batu
            if kk < 0.999:
                for j in range(int(math.ceil(Hh / COURSE))):
                    v0 = j * COURSE; v1 = min((j + 1) * COURSE, Hh)
                    if j == int(Hh / COURSE) and Hh < 8.6 and (t < 9 or 16 < t < 19):  # lapisan atas sedang diletakkan
                        v1 = v0 + (Hh - v0)
                    cuts, br = BLK[fi][j % 40]
                    sh = 0 if j % 2 == 0 else 0.5 / 5
                    for bi in range(len(br)):
                        u0 = cuts[bi]; u1 = cuts[bi + 1]
                        if u1 - u0 < 0.02: continue
                        pts, _ = proj(np.array([P3(u0, v0 / Hh, fi, Hh), P3(u1, v0 / Hh, fi, Hh), P3(u1, v1 / Hh, fi, Hh), P3(u0, v1 / Hh, fi, Hh)]), c)
                        col = tuple(int(min(255, v_ * br[bi] * shade)) for v_ in (176, 160, 134))
                        def dr(d, off, pts=pts, col=col, a=int(255 * (1 - kk))):
                            d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=col + (a,), outline=(60, 52, 44, a))
                        items.append((depth + 0.6 + 1e-3 * j, dr))
            if kk > 0.001:
                pts, _ = quad(fi, 0, 1, 0, 1, Hh)
                col = tuple(int(min(255, v_ * (0.5 + shade))) for v_ in kc)
                def dr(d, off, pts=pts, col=col, a=int(255 * kk)):
                    d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=col + (a,), outline=(40, 40, 46, a))
                items.append((depth + 0.5, dr))
                # lipatan kain
                for fu in np.linspace(.08, .92, 9):
                    p2, _ = proj(np.array([P3(fu, 0.0, fi, Hh), P3(fu, 1.0, fi, Hh)]), c)
                    def dr(d, off, p2=p2, a=int(40 * kk), shade=shade):
                        d.line([(x * ss, (y - off) * ss) for x, y in p2], fill=(190, 190, 215, a), width=ss)
                    items.append((depth + 0.4, dr))
                # hizam emas (sabuk) + ornamen
                gold = tuple(int(min(255, v_ * (0.55 + shade * 0.9))) for v_ in (222, 176, 76))
                v0, v1 = 0.60, 0.78
                pts, _ = quad(fi, 0.02, 0.98, v0, v1, Hh)
                def dr(d, off, pts=pts, gold=gold, a=int(255 * kk), kc_=tuple(int(x) for x in kc)):
                    d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=gold + (a,))
                items.append((depth + 0.3, dr))
                pts, _ = quad(fi, 0.035, 0.965, v0 + .012, v1 - .012, Hh)
                def dr(d, off, pts=pts, a=int(255 * kk), kc_=tuple(int(x * .9) for x in kc)):
                    d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=kc_ + (a,))
                items.append((depth + 0.29, dr))
                for ui in range(10):
                    u0 = 0.06 + ui * 0.0905
                    pts, _ = quad(fi, u0, u0 + 0.06, v0 + .028, v1 - .028, Hh)
                    def dr(d, off, pts=pts, gold=gold, a=int(240 * kk)):
                        d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=gold + (a,))
                    items.append((depth + 0.28, dr))
                    pts, _ = quad(fi, u0 + .015, u0 + .045, v0 + .05, v1 - .05, Hh)
                    def dr(d, off, pts=pts, a=int(240 * kk), kc_=tuple(int(x * .9) for x in kc)):
                        d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=kc_ + (a,))
                    items.append((depth + 0.27, dr))
            # pintu emas (sisi 0)
            if fi == 0 and Hh > 8:
                pts, _ = quad(0, 0.30, 0.58, 0.17 * 13 / Hh * 0.6 + 0.04, 0.56 * 13 / Hh * 0.6 + 0.03, Hh) if False else quad(0, 0.30, 0.58, 0.08, 0.52, Hh)
                g2 = tuple(int(min(255, v_ * (0.6 + shade))) for v_ in (235, 190, 90))
                def dr(d, off, pts=pts, g2=g2):
                    d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=g2 + (255,), outline=(140, 100, 30, 255))
                items.append((depth + 0.2, dr))
                pts, _ = quad(0, 0.32, 0.56, 0.10, 0.50, Hh)
                def dr(d, off, pts=pts, g2=g2):
                    d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=tuple(int(v_ * .55) for v_ in g2) + (255,), outline=(255, 225, 140, 255))
                items.append((depth + 0.19, dr))
        # Hajar Aswad di sudut (tampak jika tidak hilang)
        if Hh > 4 and not (33.5 < t < 36.0):
            hp, hz = proj(np.array([(hw + .05, 1.5, -hd - .05)]), c)
            x, y = hp[0]; rad = 0.30 * FOC / hz[0]
            def dr(d, off, x=x, y=y, rad=rad):
                d.ellipse([(x - rad) * ss, (y - off - rad * 1.2) * ss, (x + rad) * ss, (y - off + rad * 1.2) * ss], fill=(190, 192, 200, 255))
                d.ellipse([(x - rad * .75) * ss, (y - off - rad * .9) * ss, (x + rad * .75) * ss, (y - off + rad * .9) * ss], fill=(18, 16, 18, 255))
            items.append((float(hz[0]) - 0.5, dr))
    # banjir
    wl = p_water(t)
    if wl > 0.02:
        def draw_water(d, off):
            ang = np.linspace(0, 2 * np.pi, 60)
            pts, _ = proj(np.stack([30 * np.cos(ang), np.full_like(ang, wl), 30 * np.sin(ang)], 1), c)
            d.polygon([(x * ss, (y - off) * ss) for x, y in pts], fill=(48, 96, 128, 140))
            for r_ in range(3, 30, 4):
                ph = (t * 1.4 + r_) % 4
                pts, _ = proj(np.stack([(r_ + ph) * np.cos(ang), np.full_like(ang, wl), (r_ + ph) * np.sin(ang)], 1), c)
                d.line([(x * ss, (y - off) * ss) for x, y in pts], fill=(200, 230, 250, 90), width=2 * ss)
        items.append((-1e9, draw_water))
    items.sort(key=lambda it: -it[0])
    return items
RK = [rng.rand(200) for _ in range(14)]; RJ = [rng.randn(200) for _ in range(14)]

# ---------- latar ----------
def background(t, c):
    top, hor = sky_pal(t)
    v = np.clip(YY[:HY] / HY, 0, 1) ** 1.5
    img = np.zeros((H, W, 3), np.float32)
    img[:HY] = np.repeat((top[None, None] * (1 - v[..., None]) + hor[None, None] * v[..., None]), W, 1)
    # benda langit
    bodies = []
    for (kx, ky, kr, ka) in ((None,) * 4,): pass
    ts = [b[0] for b in BODY]
    # kunci benda dipisah menurut kelompok (waktu naik) -> hitung semua kelompok
    groups = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19], [20, 21, 22]]
    glow = np.zeros((H, W, 3), np.float32)
    for g in groups:
        tg = [BODY[i][0] for i in g]
        if not (tg[0] <= t <= tg[-1]): continue
        x = np.interp(t, tg, [BODY[i][1] for i in g]); y = np.interp(t, tg, [BODY[i][2] for i in g]); r = np.interp(t, tg, [BODY[i][3] for i in g])
        a = np.interp(t, tg, [BODY[i][5] for i in g]); col = np.array(BODY[g[0]][4], np.float32)
        if a < 0.01: continue
        glow += radial_q(x, y, r * 2.4)[..., None] * col * 0.42 * a + radial_q(x, y, r * 6, 8)[..., None] * col * 0.14 * a
        d = np.sqrt((XX - x) ** 2 + (YY[:HY] - y) ** 2); disc = np.clip((r - d) / 2 + .5, 0, 1)[..., None] * a
        img[:HY] = img[:HY] * (1 - disc) + col * 1.15 * disc
    img += glow
    # bintang
    sv = kf(t, STARVIS)
    spark = Image.new("RGB", (W, H)); sd = ImageDraw.Draw(spark)
    if sv > .02:
        tw_ = 0.55 + .45 * np.sin(t * S_F * 2 + S_P)
        for i in range(NS):
            b = S_B[i] * tw_[i] * sv * 1.9 * (0.3 + 0.7 * min(1, (HY - S_Y[i]) / 400))
            if b < .05: continue
            cc = int(255 * min(b, 1)); x, y = S_X[i], S_Y[i]
            if S_B[i] > .55: sd.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(cc, cc, int(cc * .9)))
            else: sd.point((x, y), fill=(cc, cc, cc))
    # awan (badai / asap)
    cvis = kf(t, [(0, .05), (9, .1), (11, .55), (14.5, .5), (16, .1), (36, .1), (37.2, .55), (38.4, 1.0), (42, .9), (43.5, .1), (50, .1)])
    ccol = kf(t, [(0, (.35, .4, .55)), (10, (.5, .3, .3)), (11.5, (.45, .18, .14)), (15.5, (.9, .85, .8)), (36.5, (.5, .55, .65)), (38, (.25, .3, .38)), (43, (.4, .45, .55)), (50, (.2, .25, .4))])
    if cvis > .02:
        ox = int(t * 22) % W; cl = CLOUD[:, ox:ox + W]
        ca = sstep(.5, .78, cl) * cvis * np.clip(1 - np.arange(CH_)[:, None] / CH_ * .15, 0, 1)
        y0 = 40
        img[y0:y0 + CH_] = img[y0:y0 + CH_] * (1 - ca[..., None]) + (ccol * (0.35 + .6 * p_light(t)))[None, None] * ca[..., None]
    # gunung gurun mengelilingi Makkah (paralaks mengikuti rotasi kamera)
    shift = int((c["sa"] * 400 * 2 + 0)) % W
    for k in range(2):
        top_ = RIDGE[k][W + shift:2 * W + shift][None, :]
        cov = np.clip(YY[:HY] + .5 - top_, 0, 1)
        base = np.array([(.26, .19, .16), (.14, .10, .09)][k], np.float32) * (0.25 + .75 * p_light(t))
        fog = [.45, .18][k]
        col = base * (1 - fog) + hor * fog
        img[:HY] = img[:HY] * (1 - cov[..., None]) + col * cov[..., None]
    # tanah di bawah horizon
    g = np.clip((YY[HY:] - HY) / (H - HY), 0, 1)[..., None]
    gc = hor * 0.55 * (1 - g ** .5) + np.array([.10, .08, .07], np.float32) * (0.3 + .7 * p_light(t)) * g ** .5 + hor * 0.05
    img[HY:] = np.repeat(gc, W, 1)
    # kilau hangat
    wm = p_warm(t)
    if wm > .02:
        ky = CY + FOC * 4 / c["D"]
        img += radial_q(CX, ky - 150, 420)[..., None] * np.array([1, .72, .35], np.float32) * 0.28 * wm
    # sinar cahaya Fathu Makkah
    ray = float(sstep(21.7, 22.1, t) * (1 - sstep(24.6, 26.4, t))) + 1.4 * float(np.exp(-((t - 22.0) / .18) ** 2))
    if ray > .02:
        ang = np.arctan2(YY - 760, XX - CX); dd = np.sqrt((XX - CX) ** 2 + (YY - 760) ** 2)
        rays = (0.5 + .5 * np.sin(ang * 14 + t * .8)) ** 4 * np.exp(-dd / 1100)
        img += rays[..., None] * np.array([1, .92, .65], np.float32) * 0.55 * min(ray, 1.5)
    # api & bara (adegan 5)
    fr = float(sstep(27.0, 27.6, t) * (1 - sstep(29.0, 30.0, t)))
    if fr > .02:
        img += radial_q(CX, 1000, 330)[..., None] * np.array([1, .45, .12], np.float32) * (0.7 + .2 * math.sin(t * 17) * math.sin(t * 5)) * fr
        for i in range(70):
            ph = (t * (0.4 + (i % 7) * .08) + i * .37) % 1
            x = CX + 360 * math.sin(i * 12.9 + t * .5) * (0.3 + ph); y = 1020 - ph * 700
            cc = int(255 * (1 - ph) * fr)
            sd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(cc, int(cc * .5), int(cc * .15)))
    # debu melayang
    for (x, y, sp_, ph) in DUST:
        xx = (x + t * 14 * sp_) % W; yy = (y - t * 6 * sp_) % H
        cc = int(60 + 40 * math.sin(t + ph)); sd.ellipse([xx - 1.5, yy - 1.5, xx + 1.5, yy + 1.5], fill=(cc, cc, int(cc * .85)))
    sp_ = np.asarray(spark, np.float32) / 255
    bl = np.asarray(spark.filter(ImageFilter.GaussianBlur(8)), np.float32) / 255
    img += sp_ + bl * 1.4
    return img

# ---------- overlay: burung/pasukan, inset Hajar Aswad, teks ----------
def draw_army_birds(img, t):
    if not 10.0 < t < 15.2: return img
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    a_army = float(sstep(10.2, 11.0, t) * (1 - sstep(13.4, 14.8, t)))
    for i in range(64):
        row, col = i // 16, i % 16
        x = 40 + col * 30 + (t - 10.2) * 60 + row * 8; y = 1230 + row * 52 + 6 * math.sin(t * 3 + col)
        if x > 520: continue
        d.rectangle([x, y, x + 8, y + 40], fill=(20, 12, 12, int(220 * a_army)))
        d.polygon([(x + 8, y), (x + 30, y + 8), (x + 8, y + 16)], fill=(120, 20, 20, int(200 * a_army)))
    b_a = float(sstep(11.6, 12.4, t) * (1 - sstep(14.4, 15.0, t)))
    r = np.random.RandomState(8)
    for i in range(46):
        u = (t - 11.6) * 0.5 + r.rand() * .12; x0 = 1100 - r.rand() * 200; y0 = 140 + r.rand() * 220
        tx = 40 + r.rand() * 430; ty = 1220 + r.rand() * 180
        q = min(1, max(0, (t - 11.7 - r.rand() * .5) / 1.4)); q = q * q * (3 - 2 * q)
        x = x0 + (tx - x0) * q; y = y0 + (ty - y0) * q - 120 * math.sin(math.pi * q)
        f = math.sin(t * 14 + i); s = 18 + r.rand() * 10
        dk = int(235 * (1 - 0.0))
        d.line([(x - s, y + f * s * .6 - 4), (x - s * .5, y + f * s * .2 - 6), (x, y), (x + s * .5, y + f * s * .2 - 6), (x + s, y + f * s * .6 - 4)], fill=(245, 240, 225, int(255 * b_a)), width=4, joint="curve")
        # kerikil jatuh
        if q > .55:
            for k in range(3):
                ph = (t * 3 + i * .31 + k * .33) % 1
                d.ellipse([x - 3, y + ph * 190, x + 3, y + ph * 190 + 6], fill=(255, 200, 120, int(255 * b_a * (1 - ph))))
    out = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).convert("RGBA"); out.alpha_composite(ov)
    return np.asarray(out.convert("RGB"), np.float32) / 255

def stone_shape(d, cx, cy, s, alpha=255):
    d.ellipse([cx - 56 * s, cy - 74 * s, cx + 56 * s, cy + 74 * s], fill=(196, 198, 206, alpha))
    d.ellipse([cx - 44 * s, cy - 62 * s, cx + 44 * s, cy + 62 * s], fill=(20, 17, 19, alpha))
    for (ox, oy, rx, ry) in ((-16, -26, 18, 22), (14, -30, 16, 18), (-22, 8, 14, 20), (10, 6, 22, 16), (-6, 36, 18, 14), (24, 34, 12, 14)):
        d.ellipse([cx + (ox - rx) * s * .8, cy + (oy - ry) * s * .8, cx + (ox + rx) * s * .8, cy + (oy + ry) * s * .8], fill=(44, 38, 40, alpha), outline=(70, 64, 66, alpha))

def inset(img, t):
    mode = None
    if 18.6 < t < 22.0: mode = 3; tl = t - 18.6
    elif 33.3 < t < 37.0: mode = 6; tl = t - 33.3
    if mode is None: return img
    vis = ease(min((t - (18.6 if mode == 3 else 33.3)) / .5, ((22.0 if mode == 3 else 37.0) - t) / .5, 1))
    R = 130; cx, cy = 540, 580
    pan = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0)); d = ImageDraw.Draw(pan)
    d.ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=(10, 12, 24, 235))
    ox, oy = R, R + 10
    if mode == 3:
        lift = ease((tl - .8) / 1.6)
        # kain
        cw = 150 - 20 * lift; yy = oy + 60 - 40 * lift
        d.polygon([(ox, yy - 50 * (1 - .4 * lift)), (ox + cw, yy), (ox, yy + 50 * (1 - .4 * lift)), (ox - cw, yy)], fill=(238, 232, 214, 255), outline=(190, 180, 160, 255))
        stone_shape(d, ox, yy - 18 - 55 * lift, .55)
        for (px, py) in ((ox, yy - 50 * (1 - .4 * lift)), (ox + cw, yy), (ox, yy + 50 * (1 - .4 * lift)), (ox - cw, yy)):
            d.line([(px, py), (px, py - 60 * lift)], fill=(255, 220, 140, 255), width=3)
            d.ellipse([px - 7, py - 60 * lift - 7, px + 7, py - 60 * lift + 7], fill=(255, 220, 140, 255))
    else:
        out_p = sstep(0.4, 1.8, tl); back_p = sstep(2.5, 3.5, tl)
        x_off = (out_p * 330) if tl < 2.3 else (-330 + back_p * 330)
        stone_shape(d, ox + x_off, oy, .75)
        if tl > 2.8: d.ellipse([ox - 84, oy - 98, ox + 84, oy + 98], outline=(255, 220, 140, int(200 * back_p)), width=4)
    mask = Image.new("L", (2 * R, 2 * R), 0); ImageDraw.Draw(mask).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=int(255 * vis))
    ring = Image.new("RGBA", (2 * R + 12, 2 * R + 12), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([2, 2, 2 * R + 9, 2 * R + 9], outline=(240, 200, 110, int(255 * vis)), width=5)
    base = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).convert("RGBA")
    base.paste(pan, (cx - R, cy - R), Image.composite(pan.split()[3], Image.new("L", pan.size, 0), mask))
    base.alpha_composite(ring, (cx - R - 6, cy - R - 6))
    d2 = ImageDraw.Draw(base)
    lab = "Hajar Aswad" if mode == 3 else ("Dirampas — 930 M" if tl < 2.6 else "Kembali — 952 M")
    tw_ = d2.textlength(lab, font=SANS_S)
    d2.text((cx - tw_ / 2 + 2, cy + R + 18), lab, font=SANS_S, fill=(0, 0, 0, int(220 * vis)))
    d2.text((cx - tw_ / 2, cy + R + 16), lab, font=SANS_S, fill=(255, 235, 190, int(255 * vis)))
    return np.asarray(base.convert("RGB"), np.float32) / 255

def hud(img, t):
    out = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # garis waktu
    if t > 4.0:
        k = ease((t - 4.0) / .8) * (1 - ease((t - 48.8) / .8))
        y = 110; x0, x1 = 90, W - 90
        d.line([(x0, y), (x1, y)], fill=(255, 235, 190, int(110 * k)), width=3)
        idx = max(0, sum(1 for s in SCENES[1:] if t >= s[0]) - 1)
        prog = (idx + min(1, (t - SCENES[idx + 1][0]) / (SCENES[idx + 1][1] - SCENES[idx + 1][0]))) / (len(NODES) - 1)
        d.line([(x0, y), (x0 + (x1 - x0) * min(prog, 1) , y)], fill=(255, 215, 130, int(255 * k)), width=5)
        for i, n in enumerate(NODES):
            x = x0 + (x1 - x0) * i / (len(NODES) - 1); on = i <= idx
            rr = 11 if i == idx else 7
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 215, 130, int(255 * k)) if on else (40, 40, 60, int(220 * k)), outline=(255, 235, 190, int(255 * k)))
            if i == idx:
                tw_ = d.textlength(n, font=SANSB_TL); d.text((min(max(x - tw_ / 2, 20), W - tw_ - 20), y + 26), n, font=SANSB_TL, fill=(255, 235, 190, int(255 * k)))
    # tahun + judul adegan
    for (a, b, yr, tag) in SCENES[1:]:
        if a <= t < b:
            k = ease(min((t - a) / .7, (b - t) / .5, 1)); 
            if yr:
                tw_ = d.textlength(yr, font=SANSB_YR)
                mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
                md.text(((W - tw_) / 2, 215 + (1 - k) * 30), yr, font=SANSB_YR, fill=int(255 * k))
                grad = np.zeros((H, W, 3), np.uint8); gy = (np.arange(H)[:, None] - 215) / 110.0
                gy = np.clip(gy, 0, 1)[..., None]; grad[:] = (np.array([255, 236, 170]) * (1 - gy) + np.array([232, 160, 60]) * gy).astype(np.uint8)
                gl = mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .55))
                sh_ = mask.filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, int(v * 1.0)))
                lay.paste(Image.new("RGBA", (W, H), (0, 0, 0, 150)), (0, 0), sh_)
                lay.paste(Image.fromarray(grad), (0, 0), gl); lay.paste(Image.fromarray(grad), (0, 0), mask)
                tw2 = d.textlength(tag, font=SANS_TAG)
                d.text(((W - tw2) / 2 + 2, 327 + (1 - k) * 20), tag, font=SANS_TAG, fill=(0, 0, 0, int(200 * k)))
                d.text(((W - tw2) / 2, 325 + (1 - k) * 20), tag, font=SANS_TAG, fill=(255, 245, 225, int(255 * k)))
    # subtitle
    for (a, b, txt, ref) in CAPS:
        if a <= t <= b:
            k = ease(min((t - a) / .45, (b - t) / .45, 1))
            words = txt.split(" "); lines = [""]
            for w_ in words:
                if d.textlength((lines[-1] + " " + w_).strip(), font=SANSB) > 880: lines.append(w_)
                else: lines[-1] = (lines[-1] + " " + w_).strip()
            hh = 28 + 58 * len(lines) + (40 if ref else 0)
            wmax = max(d.textlength(l, font=SANSB) for l in lines)
            top = 1560 + (1 - k) * 24
            d.rounded_rectangle((W / 2 - wmax / 2 - 40, top, W / 2 + wmax / 2 + 40, top + hh), 36, fill=(6, 8, 20, int(165 * k)))
            for j, l in enumerate(lines):
                lw = d.textlength(l, font=SANSB); d.text(((W - lw) / 2, top + 18 + 58 * j), l, font=SANSB, fill=(255, 255, 255, int(255 * k)))
            if ref:
                rw = d.textlength(ref, font=SANS_S); d.text(((W - rw) / 2, top + 22 + 58 * len(lines)), ref, font=SANS_S, fill=(255, 215, 140, int(255 * k)))
    # judul pembuka
    if t < 4.2:
        k = ease((t - .5) / 1.0) * (1 - ease((t - 3.2) / .7))
        for txt, y, f_, col in (("SEJARAH", 330, SANSB_BIG, (255, 236, 180)), ("KA'BAH", 450, SANSB_BIG, (240, 190, 90))):
            tw_ = d.textlength(txt, font=f_)
            d.text(((W - tw_) / 2 + 4, y + 4 + (1 - k) * 40), txt, font=f_, fill=(0, 0, 0, int(160 * k))); d.text(((W - tw_) / 2, y + (1 - k) * 40), txt, font=f_, fill=col + (int(255 * k),))
        s = "Rumah pertama untuk beribadah"; tw_ = d.textlength(s, font=SANS_TAG)
        d.text(((W - tw_) / 2, 600), s, font=SANS_TAG, fill=(220, 225, 255, int(230 * k)))
    # penutup
    if t > 46.6:
        k = ease((t - 46.8) / .9); k2 = ease((t - 47.9) / .9)
        for txt, y, f_, col in (("KIBLAT SATU UMAT", 330, SANSB_BIG if False else font("DejaVuSans-Bold.ttf", 84), (255, 232, 170)),):
            tw_ = d.textlength(txt, font=f_); d.text(((W - tw_) / 2 + 3, y + 3 + (1 - k) * 30), txt, font=f_, fill=(0, 0, 0, int(170 * k))); d.text(((W - tw_) / 2, y + (1 - k) * 30), txt, font=f_, fill=col + (int(255 * k),))
        for txt, y, f_, col in (("Jutaan orang bertawaf mengelilinginya setiap tahun.", 440, SANS_S, (220, 226, 255)), ("Dibuat 100% dengan kode • Python · NumPy · Pillow", 1690, SANS_TINY, (170, 180, 215))):
            tw_ = d.textlength(txt, font=f_); d.text(((W - tw_) / 2, y), txt, font=f_, fill=col + (int(255 * k2),))
    out.alpha_composite(lay)
    return np.asarray(out.convert("RGB"), np.float32) / 255

NOISE = np.random.RandomState(1).randn(H, W).astype(np.float32) * 0.012
VIG = (1 - 0.40 * np.clip(((XX - W / 2) / (W * .75)) ** 2 + ((YY - H / 2) / (H * .7)) ** 2, 0, 1))[..., None].astype(np.float32)

SS = 2; Y0, HH = 520, 1400
def frame(i):
    t = i / FPS
    c = make_cam(t)
    img = background(t, c)
    # objek 3D (supersampling) pada region
    lay = Image.new("RGBA", (W * SS, HH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    for dep, fn in scene_items(t, c, SS):
        fn(d, Y0)
    lay = lay.resize((W, HH), Image.LANCZOS)
    la = np.asarray(lay, np.float32) / 255
    region = img[Y0:Y0 + HH]
    img[Y0:Y0 + HH] = region * (1 - la[..., 3:4]) + la[..., :3] * la[..., 3:4]
    # bloom
    sm = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    bm = np.clip(np.asarray(sm, np.float32) / 255 - .78, 0, 1) * 2.2
    bm = np.asarray(Image.fromarray(np.clip(bm * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR), np.float32) / 255
    img += bm * .8
    # hujan (adegan 7) + kilat
    rv = float(sstep(37.2, 38.0, t) * (1 - sstep(41.5, 43, t)))
    if rv > .02:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); r = np.random.RandomState(3)
        for k in range(160):
            x = (r.rand() * W + t * 120) % W; y = ((r.rand() * H) + t * 1500 * (0.7 + r.rand() * .6)) % H
            od.line([(x, y), (x - 14, y + 70)], fill=(200, 220, 240, int(110 * rv)), width=2)
        im_ = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).convert("RGBA"); im_.alpha_composite(ov); img = np.asarray(im_.convert("RGB"), np.float32) / 255
        img += 0.6 * np.exp(-((t - 38.6) / .08) ** 2) + .35 * np.exp(-((t - 39.1) / .06) ** 2)
    img = draw_army_birds(img, t)
    img = inset(img, t)
    # kilatan: rewind & Fathu Makkah
    img += 0.8 * np.exp(-((t - 22.0) / .14) ** 2) + 0.35 * np.exp(-((t - 3.5) / .12) ** 2)
    img = img * VIG
    sh = (np.random.RandomState(i % 9).randint(0, H), np.random.RandomState(i % 7).randint(0, W))
    img = img + np.roll(NOISE, sh, (0, 1))[..., None]
    img = np.clip(img, 0, 1) ** (1 / 1.04)
    f = 1.0
    if t < .4: f = t / .4
    if t > DUR - 1.6: f = max(0, (DUR - t) / 1.6)
    img = hud(img, t)
    return (np.clip(img * f, 0, 1) * 255).astype(np.uint8)

def work(i): return frame(i).tobytes()
if __name__ == "__main__":
    sp = "/tmp/claude-0/-home-user-OpenAssist-ID/e20ba525-a73c-5b58-a6ed-7c91748afa16/scratchpad/"
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        for ts in sys.argv[2:]: Image.fromarray(frame(int(float(ts) * FPS))).save(sp + f"k_{ts}.png")
        sys.exit()
    import multiprocessing as mp
    out = sys.argv[1] if len(sys.argv) > 1 else "sejarah_kabah.mp4"; n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    with mp.Pool(4) as p:
        for k, b in enumerate(p.imap(work, range(n), chunksize=2)):
            ff.stdin.write(b)
            if k % 100 == 0: print("frame", k, "/", n, flush=True)
    ff.stdin.close(); ff.wait(); print("selesai", out)
