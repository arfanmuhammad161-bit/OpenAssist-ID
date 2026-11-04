"""Mesin gambar 2D vektor bergaya motion explainer: kamera, paralaks, anotasi gambar-tangan."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS, SS = 1080, 1920, 30, 2
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype({"black": FD + "Inter-Black.otf", "xb": FD + "Inter-ExtraBold.otf", "sb": FD + "Inter-SemiBold.otf",
                                                   "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"}[name], max(6, int(size)))
    return _fc[k]
def hexc(h, a=255): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
def mix(a, b, k): return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)) + ((255,) if len(a) < 4 else (int(a[3] + (b[3] - a[3]) * k),))
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def back_out(x, s=1.9): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def sstep(a, b, x): return ease_io((x - a) / (b - a))

PAL = dict(navy=hexc("#1B1038"), purple=hexc("#4B2A7B"), orange=hexc("#FF8A3D"), accent=hexc("#FFD23F"), pen=hexc("#FF7A1A"), cream=hexc("#FFF4D6"),
           red=hexc("#FF4B4B"), green=hexc("#35D07F"), sand=hexc("#E8B26A"), sandd=hexc("#B9793A"), sandl=hexc("#F6D69A"), shadow=hexc("#2A1646"), white=hexc("#FFFFFF"),
           skin=hexc("#C98A5B"), kilt=hexc("#F2E9D0"), stone=hexc("#C9A66B"), stoned=hexc("#8E6A3C"))

def sky_array(top, hor, sun=None, glow=0.0, hy=0.62, curve=1.4):
    """gradien langit 1/4 resolusi -> array float (h,w,3) (0..255)."""
    h, w = H // 4, W // 4
    y = np.linspace(0, 1, h)[:, None]; v = np.clip(y / hy, 0, 1) ** curve
    img = np.array(top[:3], np.float32)[None, None] * (1 - v[..., None]) + np.array(hor[:3], np.float32)[None, None] * v[..., None]
    img = np.repeat(img, w, 1)
    if sun and glow > 0:
        sx, sy, col = sun; xx = np.linspace(0, W, w)[None, :]; yy = np.linspace(0, H, h)[:, None]
        d2 = ((xx - sx) ** 2 + (yy - sy) ** 2)
        g = np.exp(-d2 / (2 * 330.0 ** 2)) * glow + np.exp(-d2 / (2 * 760.0 ** 2)) * glow * .4
        img = img + g[..., None] * np.array(col[:3], np.float32)[None, None]
    return np.clip(img, 0, 255)

class Cv:
    def __init__(self, bg_arr):
        im = Image.fromarray(bg_arr.astype(np.uint8)).resize((W * SS, H * SS), Image.BILINEAR)
        self.im = im; self.d = ImageDraw.Draw(im, "RGBA")
        self.cx, self.cy, self.z, self.rot, self.sx, self.sy = 540.0, 960.0, 1.0, 0.0, 0.0, 0.0
    def cam(self, cx=540, cy=960, z=1.0, rot=0.0, sx=0.0, sy=0.0): self.cx, self.cy, self.z, self.rot, self.sx, self.sy = cx, cy, z, rot, sx, sy
    def T(self, x, y, par=1.0):
        z = 1 + (self.z - 1) * par; cx = 540 + (self.cx - 540) * par; cy = 960 + (self.cy - 960) * par
        dx, dy = (x - cx) * z, (y - cy) * z
        if self.rot:
            c, s = math.cos(self.rot), math.sin(self.rot); dx, dy = dx * c - dy * s, dx * s + dy * c
        return ((540 + dx + self.sx) * SS, (960 + dy + self.sy) * SS)
    def zz(self, par=1.0): return 1 + (self.z - 1) * par
    def poly(self, pts, fill, par=1.0, outline=None, w=0):
        P = [self.T(x, y, par) for x, y in pts]
        self.d.polygon(P, fill=fill)
        if outline and w: self.d.line(P + [P[0]], fill=outline, width=max(1, int(w * self.zz(par) * SS)), joint="curve")
    def line(self, pts, fill, w, par=1.0, dash=None, cap=True):
        P = [self.T(x, y, par) for x, y in pts]; ww = max(1, int(w * self.zz(par) * SS))
        if dash:
            on, off = dash
            for a, b in zip(P[:-1], P[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / ((on + off) * SS * self.zz(par))))
                for i in range(n):
                    t0 = i / n; t1 = t0 + (on / (on + off)) / n
                    self.d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=fill, width=ww)
        else:
            self.d.line(P, fill=fill, width=ww, joint="curve")
            if cap and ww > 4:
                for p in (P[0], P[-1]): self.d.ellipse([p[0] - ww / 2, p[1] - ww / 2, p[0] + ww / 2, p[1] + ww / 2], fill=fill)
    def ell(self, x, y, rx, ry, fill, par=1.0, outline=None, w=0):
        z = self.zz(par); cx, cy = self.T(x, y, par)
        self.d.ellipse([cx - rx * z * SS, cy - ry * z * SS, cx + rx * z * SS, cy + ry * z * SS], fill=fill, outline=outline, width=int(w * z * SS))
    def rrect(self, x0, y0, x1, y1, r, fill, par=1.0, outline=None, w=0):
        a = self.T(x0, y0, par); b = self.T(x1, y1, par); z = self.zz(par)
        self.d.rounded_rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])], r * z * SS, fill=fill, outline=outline, width=int(w * z * SS))
    def text(self, x, y, s, font="xb", size=60, fill=None, anchor="mm", par=1.0, stroke=0, stroke_fill=(0, 0, 0, 255), z_scale=True):
        z = self.zz(par) if z_scale else 1.0; f = F(font, size * z * SS); cx, cy = self.T(x, y, par)
        self.d.text((cx, cy), s, font=f, fill=fill or PAL["cream"], anchor=anchor, stroke_width=int(stroke * z * SS), stroke_fill=stroke_fill)
    def tw(self, s, font, size): return F(font, size * SS).getlength(s) / SS
    def final(self): return self.im.resize((W, H), Image.LANCZOS)

# ---- bentuk-bentuk dasar ----
def wob(seed, n, amp):
    r = np.random.RandomState(seed); return r.randn(n) * amp
def pen_circle(cv, x, y, rx, ry, prog, col=None, w=10, seed=1, par=1.0):
    col = col or PAL["pen"]; n = 48; pts = []
    wb = wob(seed, n + 12, 3.0)
    for i in range(int(n * 1.12 * clamp(prog)) + 1):
        a = -math.pi / 2 + i / n * 2 * math.pi; k = 1 + 0.04 * (i / n)
        pts.append((x + math.cos(a) * rx * k + wb[i % len(wb)], y + math.sin(a) * ry * k + wb[(i + 5) % len(wb)]))
    if len(pts) > 1: cv.line(pts, col, w, par)
def pen_line(cv, a, b, prog, col=None, w=9, seed=2, par=1.0):
    col = col or PAL["pen"]; n = 16; wb = wob(seed, n + 2, 2.2); pts = []
    for i in range(int(n * clamp(prog)) + 1):
        t = i / n; pts.append((a[0] + (b[0] - a[0]) * t + wb[i], a[1] + (b[1] - a[1]) * t + wb[i + 1]))
    if len(pts) > 1: cv.line(pts, col, w, par)
def pen_check(cv, x, y, s, prog, col=None, w=18, par=1.0):
    col = col or PAL["green"]; p = [(x - s * .5, y), (x - s * .12, y + s * .42), (x + s * .55, y - s * .45)]
    L1 = 0.35
    if prog <= L1: pts = [p[0], (p[0][0] + (p[1][0] - p[0][0]) * prog / L1, p[0][1] + (p[1][1] - p[0][1]) * prog / L1)]
    else:
        q = (prog - L1) / (1 - L1); pts = [p[0], p[1], (p[1][0] + (p[2][0] - p[1][0]) * q, p[1][1] + (p[2][1] - p[1][1]) * q)]
    if prog > 0: cv.line(pts, col, w, par)
def pen_x(cv, x, y, s, prog, col=None, w=18, par=1.0):
    col = col or PAL["red"]
    if prog > 0: cv.line([(x - s, y - s), (x - s + 2 * s * clamp(prog * 2), y - s + 2 * s * clamp(prog * 2))], col, w, par)
    if prog > .5: cv.line([(x + s, y - s), (x + s - 2 * s * clamp((prog - .5) * 2), y - s + 2 * s * clamp((prog - .5) * 2))], col, w, par)
def arrow(cv, a, b, col, w=8, par=1.0, head=26):
    cv.line([a, b], col, w, par); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        cv.line([b, (b[0] - head * math.cos(ang + s * .5), b[1] - head * math.sin(ang + s * .5))], col, w, par)
def tag(cv, x, y, txt, size=54, bg=None, fg=None, par=1.0, scale=1.0, rot=0.0, font="black"):
    bg = bg or PAL["accent"]; fg = fg or PAL["navy"]; tw_ = cv.tw(txt, font, size * scale) + 52 * scale; h = size * scale * 1.45
    cv.rrect(x - tw_ / 2 + 6, y - h / 2 + 8, x + tw_ / 2 + 6, y + h / 2 + 8, 16 * scale, (0, 0, 0, 90), par)
    cv.rrect(x - tw_ / 2, y - h / 2, x + tw_ / 2, y + h / 2, 16 * scale, bg, par)
    cv.text(x, y + 2, txt, font, size * scale, fg, par=par)
def person(cv, x, y, h, col=None, swing=0.0, lean=0.0, par=1.0, kilt=None):
    col = col or PAL["skin"]; kilt = kilt or PAL["kilt"]; hr = h * .11
    hx = x + lean * h * .25
    cv.line([(x - h * .05, y - h * .34), (x - h * .05 + math.sin(swing) * h * .22, y)], col, h * .08, par)
    cv.line([(x + h * .05, y - h * .34), (x + h * .05 - math.sin(swing) * h * .22, y)], col, h * .08, par)
    cv.poly([(x - h * .13, y - h * .34), (x + h * .13, y - h * .34), (hx + h * .11, y - h * .66), (hx - h * .11, y - h * .66)], col, par)
    cv.poly([(x - h * .15, y - h * .30), (x + h * .15, y - h * .30), (x + h * .12, y - h * .43), (x - h * .12, y - h * .43)], kilt, par)
    cv.ell(hx, y - h * .78, hr, hr * 1.1, col, par)
def stars(cv, n, seed, t, alpha=1.0, ymax=0.45):
    r = np.random.RandomState(seed)
    for i in range(n):
        x, y = r.rand() * W, r.rand() * H * ymax; b = (0.5 + 0.5 * math.sin(t * 2 + i)) * alpha
        if b > .05: cv.d.ellipse([x * SS - 3, y * SS - 3, x * SS + 3, y * SS + 3], fill=(255, 244, 214, int(255 * b)))

# ---- piramida datar 3D semu ----
def pyr_pts(bx, by, w, h):
    A = (bx, by - h); L = (bx - w, by); M = (bx + w * .12, by + w * .13); R = (bx + w, by - w * .02)
    return A, L, M, R
def draw_pyramid(cv, bx, by, w, h, cl, cr, par=1.0, courses=0, ccol_l=None, ccol_r=None, grow=1.0, edge=None, pop=None):
    A, L, M, R = pyr_pts(bx, by, w, h)
    if grow >= 0.999 and not pop:
        cv.poly([A, L, M], cl, par); cv.poly([A, M, R], cr, par)
        if courses:
            for i in range(1, courses):
                f = i / courses
                for (P, Q, col) in ((L, M, ccol_l), (M, R, ccol_r)):
                    pass
                a = (A[0] + (L[0] - A[0]) * f, A[1] + (L[1] - A[1]) * f); b = (A[0] + (M[0] - A[0]) * f, A[1] + (M[1] - A[1]) * f); c_ = (A[0] + (R[0] - A[0]) * f, A[1] + (R[1] - A[1]) * f)
                cv.line([a, b], ccol_l or mix(cl, (0, 0, 0, 255), .16), 3, par, cap=False); cv.line([b, c_], ccol_r or mix(cr, (0, 0, 0, 255), .16), 3, par, cap=False)
        if edge: cv.line([A, L, M, R, A], edge, 4, par)
        cv.line([A, M], mix(cl, (255, 255, 255, 255), .25), 3, par)
        return
    n = courses or 40
    for j in range(n):
        u0, u1 = j / n, (j + 1) / n
        if u0 >= grow: break
        u1 = min(u1, grow); dy = 0
        if pop: dy = -pop(j) if pop else 0
        def pe(P, u): return (A[0] + (P[0] - A[0]) * (1 - u), A[1] + (P[1] - A[1]) * (1 - u) + dy)
        shade = 0.9 + 0.1 * ((j % 2) * 2 - 1) * .5
        cv.poly([pe(L, u0), pe(M, u0), pe(M, u1), pe(L, u1)], tuple(int(c * shade) for c in cl[:3]) + (255,), par)
        cv.poly([pe(M, u0), pe(R, u0), pe(R, u1), pe(M, u1)], tuple(int(c * shade) for c in cr[:3]) + (255,), par)
        last = (j, u1)
    if grow < 0.999 and 'last' in dir():
        j, u1 = last
        def pe2(P, u): return (A[0] + (P[0] - A[0]) * (1 - u), A[1] + (P[1] - A[1]) * (1 - u) + (-pop(j) if pop else 0))
        Bk = (L[0] + R[0] - M[0], L[1] + R[1] - M[1])
        cv.poly([pe2(L, u1), pe2(M, u1), pe2(R, u1), pe2(Bk, u1)], mix(cl, (255, 255, 255, 255), .3), par)
def dune(cv, y0, amp, freq, ph, col, par, x0=-400, x1=W + 400, bottom=H + 900):
    pts = [(x, y0 + amp * math.sin(x * freq + ph) + amp * .45 * math.sin(x * freq * 2.3 + ph * 1.7)) for x in range(int(x0), int(x1) + 1, 40)]
    cv.poly(pts + [(x1, bottom), (x0, bottom)], col, par)
