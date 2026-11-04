"""Audio sintesis: drone, pad, petikan, genderang maqsum, efek (numpy)."""
import numpy as np, wave
from common import *
SR = 44100; N = int(DUR * SR); rs = np.random.RandomState(31)
B = {k: [np.zeros(N, np.float32), np.zeros(N, np.float32)] for k in ("dry", "wet", "drum", "fx")}
def add(bus, sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    s = sig[max(0, -i):]; i = max(i, 0); n = min(len(s), N - i)
    B[bus][0][i:i + n] += s[:n] * g * np.cos((pan + 1) * np.pi / 4); B[bus][1][i:i + n] += s[:n] * g * np.sin((pan + 1) * np.pi / 4)
def tt(d): return np.arange(int(d * SR)) / SR
def pad(f, d, a=1.5):
    t = tt(d); s = np.zeros_like(t)
    for det in (-.005, 0, .005):
        for h in range(1, 9): s += np.sin(2 * np.pi * f * (1 + det) * h * t + h) / h ** 1.5
    e = np.ones_like(t); na = int(a * SR); nr = int(1.8 * SR); e[:na] = np.linspace(0, 1, na) ** 1.5; e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return (s * e / 22).astype(np.float32)
def pluck(f, d=1.4):
    t = tt(d); s = np.zeros_like(t)
    for h in range(1, 14): s += np.sin(2 * np.pi * f * h * t + h * .4) / h ** 0.9 * np.exp(-t * (3.2 + h * 1.6))
    return (s * np.minimum(t * 900, 1) * 0.55).astype(np.float32)
def bell(f, d=3.0):
    t = tt(d); s = np.zeros_like(t)
    for r_, a in ((1, 1), (2.01, .45), (2.76, .35), (4.1, .2)): s += a * np.sin(2 * np.pi * f * r_ * t) * np.exp(-t * (1.1 + r_ * .6))
    return (s * np.minimum(t * 900, 1) * 0.4).astype(np.float32)
def nlp(d, k):
    n = rs.randn(int(d * SR))
    for _ in range(3): n = np.convolve(n, np.ones(k) / k, "same")
    return n.astype(np.float32)
def doum(a=1.0):
    t = tt(0.4); f = 70 + 80 * np.exp(-t * 30); return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * a).astype(np.float32)
def tak(a=.5):
    t = tt(0.12); n = np.diff(rs.randn(len(t)), prepend=0); return ((n * .6 + np.sin(2 * np.pi * 900 * t)) * np.exp(-t * 45) * a).astype(np.float32) * .5
def swell(d, rev=False):
    t = tt(d); e = (t / d) ** 2 if not rev else (1 - t / d) ** 2
    f = 200 * (20 ** (t / d)); return ((nlp(d, 6) * 6 + np.sin(2 * np.pi * np.cumsum(f) / SR) * .25) * e).astype(np.float32) * .5
def boom(d=3.5, f0=44):
    t = tt(d); f = f0 + 40 * np.exp(-t * 4); return ((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3) + .5 * nlp(d, 40) * np.exp(-t * 2)) * .9).astype(np.float32)

BND = [s[0] for s in SCENES] + [DUR]
CH = [[164.81, 246.94, 329.63], [164.81, 246.94, 329.63], [174.61, 220, 261.63], [164.81, 207.65, 246.94, 293.66], [220, 261.63, 329.63], [164.81, 207.65, 246.94, 329.63], [174.61, 220, 261.63, 329.63], [130.81, 196, 329.63], [164.81, 207.65, 246.94, 329.63, 415.3]]
CH = [CH[0], CH[1], CH[2], CH[3], CH[4], CH[5], CH[6], CH[8]]
for i, (a, b, *_ ) in enumerate(SCENES):
    d = b - a + 3.0
    for f in CH[i]: add("wet", pad(f, d), max(a - .3, 0), rs.uniform(-.7, .7), .17)
    add("dry", pad(CH[i][0] / 2, d, 2.0), a, 0, .16)
t = tt(DUR); dr = np.sin(2 * np.pi * 82.41 * t) + .5 * np.sin(2 * np.pi * 123.47 * t + 1) + .25 * np.sin(2 * np.pi * 164.81 * t)
add("dry", (dr * .14 * (.7 + .3 * np.sin(2 * np.pi * t / 8))).astype(np.float32), 0, 0, 1)
add("fx", (nlp(DUR, 9) * (.5 + .5 * np.sin(2 * np.pi * t / 6 + np.sin(t * .6)))).astype(np.float32), 0, 0, .45)
# melodi petikan (fraigis Frigia dominan di E)
SC = [329.63, 349.23, 415.30, 440.0, 493.88, 523.25, 587.33, 659.25]
mel_dens = [0.6, 0.8, 0.9, 1.1, 1.0, 0.7, 0.8, 1.2]
BP = 60 / 90 / 2
for i, (a, b, *_ ) in enumerate(SCENES):
    tc = a + 0.7; k = 0; idx = rs.randint(0, 5)
    while tc < b - 0.4:
        idx = int(np.clip(idx + rs.choice([-2, -1, -1, 0, 1, 1, 2]), 0, 7))
        add("wet", pluck(SC[idx]), tc, rs.uniform(-.5, .5), .35); add("dry", pluck(SC[idx], .8), tc, 0, .12)
        tc += rs.choice([1, 1, 2, 2, 3, 4]) * BP / mel_dens[i]
# genderang maqsum (adegan 3 sangat aktif, lainnya lembut)
vol = {1: .0, 2: .45, 3: 1.0, 4: .75, 5: .5, 6: .55, 7: .9}
for i, (a, b, *_ ) in enumerate(SCENES):
    v = vol.get(i, 0)
    if v <= 0: continue
    tc = a + 1.0
    while tc < b - 0.3:
        for step, kind in ((0, "D"), (1, "T"), (3, "T"), (4, "D"), (6, "T")):
            tk = tc + step * BP
            if tk < b - .2: add("drum", doum(v) if kind == "D" else tak(.8 * v), tk, 0, .7)
        tc += 8 * BP
for (a, *_ ) in SCENES[1:]:
    add("fx", boom(3.0), a, 0, .6); add("fx", swell(1.4), a - 1.4, 0, .7)
add("fx", swell(1.2, True), 3.0, 0, .9)
# adegan 3: batu diseret & palu
for tc in np.arange(16.6, 23.0, 0.37):
    add("fx", (nlp(0.25, 8) * np.sin(np.pi * tt(0.25) / .25)).astype(np.float32), tc, rs.uniform(-.7, .7), .35)
for tc in np.arange(16.8, 23.0, 0.55):
    t_ = tt(0.05); add("fx", (np.sin(2 * np.pi * 1100 * t_) * np.exp(-t_ * 90)).astype(np.float32), tc, rs.uniform(-.6, .6), .3)
for k, f in enumerate([659.25, 830.6, 987.77, 1318.5]): add("wet", bell(f, 4), 23.1 + k * .15, .4 * (-1) ** k, .3)   # selimut putih
# gempa 1303
add("fx", (nlp(2.4, 30) * np.sin(np.pi * tt(2.4) / 2.4) ** .7).astype(np.float32) * 6, 32.3, 0, .8); add("fx", boom(3.0, 36), 32.4, 0, .9)
for tc in np.arange(32.5, 34.2, 0.09):
    add("fx", (nlp(0.06, 4) * np.exp(-tt(0.06) * 60) * rs.rand()).astype(np.float32), tc, rs.uniform(-.8, .8), 1.2)
for k, f in enumerate([659.25, 987.77, 1318.5, 1760]): add("wet", bell(f, 5), 46.8 + k * .12, .4 * (-1) ** k, .28)
add("fx", boom(4.5, 55), 46.8, 0, .8)
def reverb(x, seed):
    r = np.random.RandomState(seed); tI = np.arange(int(3.0 * SR)) / SR
    h = np.convolve(r.randn(len(tI)) * np.exp(-tI * 1.8), np.ones(3) / 3, "same").astype(np.float32) * .035
    n = 1 << int(np.ceil(np.log2(len(x) + len(h)))); return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)].astype(np.float32)
out = []
for c in (0, 1): out.append(B["dry"][c] + reverb(B["wet"][c], 3 + c) * 1.7 + B["drum"][c] * .9 + B["fx"][c] * .9 + reverb(B["fx"][c] * .4, 7 + c) * .8 + reverb(B["drum"][c] * .3, 9 + c) * .5)
g = np.ones(N, np.float32); g[:int(1.2 * SR)] *= np.linspace(0, 1, int(1.2 * SR)); g[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR)) ** 1.5
out = [o * g for o in out]; pk = max(abs(o).max() for o in out); out = [np.tanh(o / pk * 1.6) * .89 for o in out]
pcm = (np.stack(out, 1) * 32767).astype("<i2")
with wave.open("audio.wav", "wb") as wf: wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
print("audio ok")
