import sys, math, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
import scenes
from scenes import SC, TL, SCENE_OBJS
TOTAL = TL["total"]; N = int(TOTAL * FPS)
NOISE = np.random.RandomState(1).randn(H, W).astype(np.float32) * 0.016
XX = np.arange(W, dtype=np.float32)[None, :]; YY = np.arange(H, dtype=np.float32)[:, None]
VIG = (1 - 0.34 * np.clip(((XX - W / 2) / (W * .8)) ** 2 + ((YY - H / 2) / (H * .72)) ** 2, 0, 1))[..., None].astype(np.float32)
KEY = ("kegagalan", "gagal", "retak", "pertama", "monas", "budak", "lepas")

def scene_at(t):
    for s in SC:
        if s["start"] <= t < s["start"] + s["dur"]: return s
    return SC[-1]

def subtitles(img, t, S):
    tl = t - S["start"]; ch = None
    for i, c in enumerate(S["chunks"]):
        t1 = c["t1"] if i + 1 == len(S["chunks"]) else S["chunks"][i + 1]["t0"]
        if c["t0"] - .08 <= tl < t1 + (.15 if i + 1 == len(S["chunks"]) else 0): ch = (i, c, t1); break
    if not ch: return img
    i, c, t1 = ch; words = c["text"].split(" ")
    d = ImageDraw.Draw(img, "RGBA"); f = F("black", 62)
    wl = [d.textlength(w + " ", font=f) for w in words]; tot = sum(wl)
    if tot > 940:   # dua baris
        mid = len(words) // 2; lines = [list(range(mid)), list(range(mid, len(words)))]
    else: lines = [list(range(len(words)))]
    prog = clamp((tl - c["t0"]) / max(.2, (t1 - c["t0"] - .05)))
    pop = back_out((tl - c["t0"] + .08) / .16, 1.6); cum = 0; tl_ = sum(len(w) + 1 for w in words); cur = None
    acc = 0
    for wi, w in enumerate(words):
        acc += len(w) + 1
        if acc / tl_ >= prog and cur is None: cur = wi
    y0 = 1400 - (len(lines) - 1) * 40
    for li, idxs in enumerate(lines):
        lw = sum(wl[j] for j in idxs); x = (W - lw) / 2; y = y0 + li * 84
        for j in idxs:
            w = words[j]; key = w.strip(".,…:!?").lower() in KEY or w.strip(".,…:!?").isupper() and len(w) > 3
            col = PAL["accent"] if key else (255, 255, 255, 255)
            if j == cur:
                d.rounded_rectangle([x - 8, y - 46, x + wl[j] - 12, y + 50], 18, fill=PAL["pen"] if not key else PAL["red"])
                col = (255, 255, 255, 255)
            d.text((x, y + 2), w, font=f, fill=col, anchor="lm", stroke_width=7 if j != cur else 0, stroke_fill=(20, 8, 40, 255))
            x += wl[j]
    return img

def frame(i):
    t = i / FPS; S = scene_at(t); tl = t - S["start"]; obj = SCENE_OBJS[S["i"] - 1]
    # J-cut kecil: penekanan punch-in di awal adegan
    cv = Cv(obj.bg(tl, S)); fx = obj.draw(cv, tl, S) or {}
    img = cv.final()
    arr = np.asarray(img, np.float32) / 255
    # bloom ringan
    sm = Image.fromarray((arr * 255).astype(np.uint8)).resize((W // 6, H // 6), Image.BILINEAR)
    bm = np.clip(np.asarray(sm, np.float32) / 255 - .78, 0, 1) * 1.6
    bm = np.asarray(Image.fromarray((bm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR), np.float32) / 255
    arr = arr + bm * .55
    if fx.get("glitch"):
        sh = int(14 * math.sin(t * 90)); arr[..., 0] = np.roll(arr[..., 0], sh, 1); arr[..., 2] = np.roll(arr[..., 2], -sh, 1)
        r = np.random.RandomState(i).randint(200, 1700); arr[r:r + 40] = np.roll(arr[r:r + 40], 30, 1)
    if fx.get("flash"):
        col, a = fx["flash"]; arr = arr + np.array(col[:3], np.float32)[None, None] / 255 * a
    # punch-in penutup adegan (zoom 1.10 -> 1 selama 10 frame) + wipe transisi di awal adegan
    if tl < .35 and S["i"] > 1:
        q = tl / .35; bar = (1 - q)
        x0 = W * (q * 1.6 - .3)
        # batang diagonal kuning
        m = (np.abs((XX + YY * .35) - (W * 1.3 * q - W * .15)) < 120 * (1 - q) + 8)
        arr = np.where(m[..., None], np.array(PAL["accent"][:3], np.float32)[None, None] / 255 * 1.0, arr)
    if fx.get("wipe") and fx["wipe"][0] <= tl <= fx["wipe"][1] + .2:
        q = clamp((tl - fx["wipe"][0]) / .35)
        m = (np.abs((XX + YY * .35) - (W * 1.3 * q - W * .15)) < 120 * (1 - q) + 8)
        arr = np.where(m[..., None], np.array(PAL["accent"][:3], np.float32)[None, None] / 255, arr)
    arr = arr * VIG + np.roll(NOISE, (np.random.RandomState(i % 11).randint(0, H), np.random.RandomState(i % 5).randint(0, W)), (0, 1))[..., None]
    arr = np.clip(arr, 0, 1)
    f = 1.0
    if t < .15: f = .6 + t / .15 * .4
    if t > TOTAL - .6: f = max(0, (TOTAL - t) / .6)
    img = Image.fromarray((arr * 255 * f).astype(np.uint8))
    img = subtitles(img, t, S)
    # chip seri
    d = ImageDraw.Draw(img, "RGBA"); chip = f"SEJARAH DUNIA KUNO  •  1"; ft = F("xb", 26); wv = d.textlength(chip, font=ft)
    d.rounded_rectangle([46, 150, 46 + wv + 40, 150 + 54], 27, fill=(20, 8, 40, 170)); d.text((66, 177), chip, font=ft, fill=(255, 244, 214, 255), anchor="lm")
    return np.asarray(img, np.uint8)

def work(i): return frame(i).tobytes()
if __name__ == "__main__":
    SP = "/tmp/claude-0/-home-user-OpenAssist-ID/e20ba525-a73c-5b58-a6ed-7c91748afa16/scratchpad/"
    if sys.argv[1] == "test":
        for ts in sys.argv[2:]: Image.fromarray(frame(int(float(ts) * FPS))).save(SP + f"q_{ts}.png")
        sys.exit()
    import multiprocessing as mp
    out = sys.argv[1]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    with mp.Pool(4) as p:
        for k, b in enumerate(p.imap(work, range(N), chunksize=2)):
            ff.stdin.write(b)
            if k % 100 == 0: print("frame", k, "/", N, flush=True)
    ff.stdin.close(); ff.wait(); print("selesai", out)
