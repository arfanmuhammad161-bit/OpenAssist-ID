"""Musik + SFX + mix suara (narasi ElevenLabs di vo.wav) -> audio.wav"""
import json, wave, numpy as np
TL = json.load(open("timeline.json")); SC = TL["scenes"]; TOTAL = TL["total"]
SR = 44100; N = int((TOTAL + .3) * SR); rs = np.random.RandomState(77)
M = [np.zeros(N, np.float32), np.zeros(N, np.float32)]; X = [np.zeros(N, np.float32), np.zeros(N, np.float32)]
def add(bus, sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    s = sig[max(0, -i):]; i = max(i, 0); n = min(len(s), N - i)
    bus[0][i:i + n] += s[:n] * g * np.cos((pan + 1) * np.pi / 4); bus[1][i:i + n] += s[:n] * g * np.sin((pan + 1) * np.pi / 4)
def tt(d): return np.arange(int(d * SR)) / SR
def nlp(d, k):
    n = rs.randn(int(d * SR))
    for _ in range(2): n = np.convolve(n, np.ones(k) / k, "same")
    return n.astype(np.float32)
def tick(f=1800, d=.012, a=.5):
    t = tt(d); return ((np.sin(2 * np.pi * f * t) + .4 * rs.randn(len(t))) * np.exp(-t * 350) * a).astype(np.float32)
def thud(f=60, d=.5, a=1.0):
    t = tt(d); ff = f + 90 * np.exp(-t * 28); return ((np.sin(2 * np.pi * np.cumsum(ff) / SR) + .3 * nlp(d, 30)) * np.exp(-t * 9) * a).astype(np.float32)
def whoosh(d=.45, up=True, a=.6):
    t = tt(d); n = rs.randn(len(t)).astype(np.float32)
    for _ in range(2): n = np.convolve(n, np.ones(3) / 3, "same")
    e = np.sin(np.pi * (t / d)) ** 1.6; f = 300 * (14 ** (t / d if up else 1 - t / d))
    return ((n * .7 + np.sin(2 * np.pi * np.cumsum(f) / SR) * .25) * e * a).astype(np.float32)
def ding(f=1318, d=1.2, a=.5):
    t = tt(d); s = np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.01 * t) + .2 * np.sin(2 * np.pi * f * 3.02 * t)
    return (s * np.exp(-t * 4.5) * np.minimum(t * 800, 1) * a).astype(np.float32)
def scribble(d=.5, a=.35):
    t = tt(d); n = rs.randn(len(t)); n = n - np.convolve(n, np.ones(10) / 10, "same"); e = (np.sin(2 * np.pi * 9 * t) * .5 + .5) ** .5 * np.sin(np.pi * t / d)
    return (n * e * a).astype(np.float32)
def sparkle(n=8, span=.8, f0=2200, a=.25):
    out = np.zeros(int((span + .8) * SR), np.float32)
    for k in range(n):
        s = ding(f0 * rs.choice([1, 1.25, 1.5, 2]), .6, a); i = int(k / n * span * SR); out[i:i + len(s)] += s[:len(out) - i]
    return out
def crack(a=.8):
    out = np.zeros(int(.5 * SR), np.float32)
    for k in range(6):
        i = int(rs.rand() * .25 * SR); s = (nlp(.06, 2) * np.exp(-tt(.06) * 70) * a).astype(np.float32); out[i:i + len(s)] += s
    return out
def rumble(d=2.5, a=.7):
    t = tt(d); return (nlp(d, 40) * 6 * np.sin(np.pi * t / d) ** .7 * a).astype(np.float32)
def pad(f, d, a=1.0):
    t = tt(d); s = np.zeros_like(t)
    for det in (-.004, 0, .004):
        for h in range(1, 7): s += np.sin(2 * np.pi * f * (1 + det) * h * t + h) / h ** 1.6
    e = np.minimum(t / 1.2, 1) * np.minimum((d - t) / 1.5, 1); return (s * e / 14 * a).astype(np.float32)
def pluck(f, d=.5):
    t = tt(d); s = sum(np.sin(2 * np.pi * f * h * t) / h * np.exp(-t * (6 + h * 3)) for h in range(1, 9)); return (s * np.minimum(t * 900, 1) * .5).astype(np.float32)
def sc(i): return SC[i - 1]
def ct(i, k, off=0.0): s = sc(i); return s["start"] + s["chunks"][k]["t0"] + off

# ---------- musik: dron + denyut + petikan ----------
t_all = tt(TOTAL + .3)
dr = (np.sin(2 * np.pi * 82.41 * t_all) + .5 * np.sin(2 * np.pi * 123.47 * t_all + 1) + .3 * np.sin(2 * np.pi * 164.81 * t_all)) * (.8 + .2 * np.sin(2 * np.pi * t_all / 7))
add(M, (dr * .12).astype(np.float32), 0, 0, 1)
CH = [[164.81, 246.94, 329.63], [164.81, 207.65, 246.94], [174.61, 220, 261.63], [220, 261.63, 329.63], [164.81, 207.65, 246.94, 329.63], [174.61, 220, 261.63, 329.63], [164.81, 246.94, 329.63], [164.81, 207.65, 246.94, 329.63, 415.3]]
for i, s in enumerate(SC):
    for f in CH[i]: add(M, pad(f, s["dur"] + 2.5), s["start"] - .5 if i else 0, rs.uniform(-.6, .6), .18)
BPM = 100; BE = 60 / BPM
SCALE = [329.63, 349.23, 415.30, 440, 493.88, 523.25, 587.33, 659.25]
for i, s in enumerate(SC):
    k = 0; tcur = s["start"] + .3
    dens = [.8, .9, 1.0, .9, 1.1, 1.0, .9, .8][i]
    while tcur < s["start"] + s["dur"] - .2:
        f = SCALE[[0, 2, 4, 3, 5, 4, 2, 1][k % 8] + (1 if (k // 8) % 2 else 0)] * (1 if k % 4 else 2) / 2
        add(M, pluck(f, .45), tcur, ((k % 4) - 1.5) * .3, .22 * dens); k += 1; tcur += BE / 2
    # denyut rendah tiap birama dari adegan 2
    if i >= 1:
        tb = s["start"]
        while tb < s["start"] + s["dur"] - .3:
            add(M, thud(48, .55, .9), tb, 0, .35); add(M, thud(48, .55, .9), tb + BE * 1.5, 0, .25); tb += BE * 4

# ---------- SFX ----------
# transisi adegan
for i in range(2, 9):
    s0 = sc(i)["start"]; add(X, whoosh(.5, True, .8), s0 - .22, 0, .9); add(X, thud(55, .7, 1.0), s0, 0, .9)
# S1
add(X, thud(45, 1.2, 1.2), 0.0, 0, 1.0); add(X, whoosh(.5, True, .8), 0.0, 0, .6)
for k in range(30): add(X, tick(1400 + k * 55, .012, .5), k * (1.1 / 30) , 0, .55)
ta = sc(1)["start"] + sc(1)["chunks"][3]["t0"] + (sc(1)["chunks"][3]["t1"] - sc(1)["chunks"][3]["t0"]) * .52
add(X, thud(40, 1.4, 1.6), ta, 0, 1.0); add(X, crack(1.0), ta + .05, 0, .9); add(X, (nlp(.25, 2) * np.exp(-tt(.25) * 8)).astype(np.float32), ta, 0, .9)
add(X, scribble(.5, .4), ct(1, 2, .0), 0, .7); add(X, ding(1046, .5, .4), ct(1, 2, .5), 0, .5)
# S2
for k in range(6): add(X, thud(70 - k * 4, .5, 1.0), ct(2, 1, .15 + k * .40 + .3), (k - 2.5) * .12, .9); add(X, nlp(.3, 6) * np.exp(-tt(.3) * 12), ct(2, 1, .15 + k * .40 + .3), 0, .35)
add(X, scribble(.6, .5), ct(2, 3, 0), 0, .7); add(X, ding(1175, .8, .5), ct(2, 3, .55), 0, .6)
add(X, whoosh(.4, True, .7), ct(2, 4, 0), 0, .6)
for k in range(24): add(X, tick(1600 + k * 40, .012, .5), ct(2, 4, .0 + k * .035), 0, .5)
add(X, ding(1568, 1.0, .6), ct(2, 4, .9), 0, .7)
# S3
add(X, whoosh(.9, True, .5), ct(3, 0, 0), .3, .5); add(X, ding(880, .6, .5), ct(3, 1, .6), 0, .5)
cs = ct(3, 2, 0); add(X, crack(1.0), cs, 0, 1.0); add(X, thud(42, 1.2, 1.4), cs, 0, 1.0); add(X, rumble(1.4, .6), cs, 0, .6)
add(X, whoosh(.35, False, .8), ct(3, 3, 0), 0, .8); add(X, scribble(.5, .4), ct(3, 3, .8), 0, .6)
add(X, ding(698, .7, .5), sc(3)["start"] + sc(3)["marks"]["d"], 0, .5); add(X, ding(1318, 1.0, .6), sc(3)["start"] + sc(3)["marks"]["e"], 0, .7)
# S4
add(X, whoosh(.9, True, .6), ct(4, 0, .1), 0, .6); add(X, sparkle(10, .9, 2400, .3), ct(4, 1, 0), 0, .8); add(X, ding(1568, 1.2, .6), ct(4, 1, .25), 0, .7)
add(X, sparkle(14, 1.2, 2000, .3), ct(4, 3, 0), 0, .9)
# S5
for k in range(46): add(X, tick(900 + (k % 6) * 140, .014, .6), ct(5, 0, .15 + k * (sc(5)["chunks"][2]["t1"] - .3) / 46), (k % 7 - 3) * .1, .6)
for k in range(20): add(X, tick(2000 + k * 40, .012, .6), ct(5, 3, .1 + k * (sc(5)["chunks"][3]["t1"] - sc(5)["chunks"][3]["t0"] - .2) / 20), .2, .5)
add(X, thud(50, .8, 1.0), ct(5, 3, 0), 0, .8)
add(X, whoosh(.4, True, .8), ct(5, 4, -.08), 0, .8); add(X, ding(1046, 1.0, .6), ct(5, 4, .8), 0, .6); add(X, thud(60, .8, 1.0), ct(5, 4, .5), 0, .6)
# S6
for k in range(int(sc(6)["dur"] / .28)): add(X, (nlp(.12, 4) * np.exp(-tt(.12) * 14) * .5).astype(np.float32), sc(6)["start"] + k * .28, 0, .35)
add(X, (nlp(sc(6)["dur"], 20) * .4).astype(np.float32), sc(6)["start"], 0, .35)
add(X, thud(55, .6, 1.2), ct(6, 1, 0), 0, 1.0); add(X, scribble(.4, .5), ct(6, 1, .3), 0, .7)
for k in range(3): add(X, ding([1046, 1318, 1568][k], .9, .6), ct(6, 3, k * .18 + .1), 0, .6)
# S7
add(X, sparkle(12, 2.0, 2600, .22), ct(7, 0, .2), 0, .8)
tq = ct(7, 2, 0); add(X, thud(36, 1.6, 1.6), tq, 0, 1.0); add(X, rumble(2.6, 1.0), tq, 0, 1.0); add(X, crack(1.0), tq + .2, 0, 1.0)
for k in range(14): add(X, (nlp(.3, 12) * np.exp(-tt(.3) * 9)).astype(np.float32), tq + .3 + k * .07, rs.uniform(-.6, .6), .6); 
add(X, ding(523, 1.2, .5), tq + 1.4, 0, .6)
# S8
add(X, scribble(.4, .5), ct(8, 1, 0), 0, .6); add(X, thud(48, .8, 1.2), ct(8, 1, .0), 0, .9)
add(X, ding(1318, 1.4, .7), ct(8, 1, 1.5), 0, .8); add(X, sparkle(10, 1.0, 2600, .3), ct(8, 1, 1.5), 0, .8)
add(X, whoosh(1.2, True, .7), ct(8, 2, -.2), 0, .8); add(X, thud(44, 1.5, 1.2), ct(8, 2, .6), 0, .8)
end = sc(8)["start"] + sc(8)["dur"]
for k, f in enumerate([660, 990, 1320, 1760]): add(X, ding(f, 3.0, .5), end - 2.3 + k * .1, .4 * (-1) ** k, .6)
add(X, thud(40, 2.0, 1.2), end - 2.3, 0, .8)

# ---------- mix ----------
with wave.open("vo.wav") as wf: vo = np.frombuffer(wf.readframes(wf.getnframes()), "<i2").astype(np.float32) / 32768
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
env = np.abs(vo); k = int(.08 * SR); env = np.convolve(env, np.ones(k) / k, "same"); env = np.convolve(env, np.ones(k) / k, "same")
duck = 1 - .6 * np.clip(env / .12, 0, 1)
def reverb(x, seed):
    r = np.random.RandomState(seed); tI = np.arange(int(1.6 * SR)) / SR
    h = np.convolve(r.randn(len(tI)) * np.exp(-tI * 3.2), np.ones(3) / 3, "same").astype(np.float32) * .03
    n = 1 << int(np.ceil(np.log2(len(x) + len(h)))); return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)].astype(np.float32)
out = []
for c in (0, 1):
    music = (M[c] + reverb(M[c], 1 + c) * .8) * duck * .85
    sfx = X[c] + reverb(X[c], 5 + c) * .25
    voice = vo * 1.0
    out.append(music + sfx * .85 + voice * 1.0)
g = np.ones(N, np.float32); g[:int(.05 * SR)] *= np.linspace(.2, 1, int(.05 * SR)); g[-int(.7 * SR):] *= np.linspace(1, 0, int(.7 * SR))
out = [o * g for o in out]; pk = max(abs(o).max() for o in out); out = [np.tanh(o / pk * 1.35) * .9 for o in out]
pcm = (np.stack(out, 1) * 32767).astype("<i2")
with wave.open("audio.wav", "wb") as wf: wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
print("audio ok")
