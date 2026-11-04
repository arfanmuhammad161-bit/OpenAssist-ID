"""Sintesis audio 100% dari kode (numpy): musik, SFX, ambience -> audio.wav"""
import numpy as np, wave
from common import *

SR = 44100
N = int(DUR * SR)
rs = np.random.RandomState(11)
L = {k: np.zeros(N, np.float32) for k in ("dry", "wet", "drums", "fx")}
R = {k: np.zeros(N, np.float32) for k in L}


def add(bus, sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0:
        return
    s = sig[max(0, -i):]
    i = max(i, 0)
    n = min(len(s), N - i)
    gl = gain * np.cos((pan + 1) * np.pi / 4)
    gr = gain * np.sin((pan + 1) * np.pi / 4)
    L[bus][i:i + n] += s[:n] * gl
    R[bus][i:i + n] += s[:n] * gr


def tt(d):
    return np.arange(int(d * SR)) / SR


def env_adsr(n, a, d, s, r):
    e = np.ones(n, np.float32)
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e[:a] = np.linspace(0, 1, max(a, 1))
    e[a:a + d] = np.linspace(1, s, max(d, 1))[:max(0, n - a)][:len(e[a:a + d])]
    e[a + d:] = s
    if r > 0:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def pad_note(f, d, det=0.004):
    t = tt(d)
    sig = np.zeros_like(t)
    for dt in (-det, 0, det):
        ff = f * (1 + dt)
        for h in range(1, 9):
            sig += np.sin(2 * np.pi * ff * h * t + h * 1.3) / h ** 1.6
    sig *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t + f)  * 0.3 + 0.7
    return (sig * env_adsr(len(t), 0.5, 0.3, 0.8, 0.6) / 3).astype(np.float32)


def pluck(f, d=0.5, bright=1.0):
    t = tt(d)
    sig = np.zeros_like(t)
    for h in range(1, 12):
        sig += np.sin(2 * np.pi * f * h * t) / h * np.exp(-t * (6 + h * 4 / bright))
    return (sig * np.minimum(t * 600, 1)).astype(np.float32) * 0.6


def bell(f, d=2.0):
    t = tt(d)
    sig = np.zeros_like(t)
    for r_, a in ((1, 1), (2.76, .5), (5.4, .3), (8.93, .15)):
        sig += a * np.sin(2 * np.pi * f * r_ * t) * np.exp(-t * (1.6 + r_ * .7))
    return (sig * np.minimum(t * 800, 1)).astype(np.float32) * 0.5


def lead(f, d):
    t = tt(d)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(t * 3, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    sig = sum(np.sin(ph * h) / h ** 1.2 for h in range(1, 7))
    return (sig * env_adsr(len(t), 0.02, 0.1, 0.7, 0.25) * 0.5).astype(np.float32)


def kick(a=1.0):
    t = tt(0.45)
    f = 42 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 7) * a + 0.25 * rs.randn(len(t)) * np.exp(-t * 90)).astype(np.float32)


def hat(d=0.07, a=0.5):
    t = tt(d)
    n = rs.randn(len(t))
    n = np.diff(n, prepend=0)
    return (n * np.exp(-t * 60) * a).astype(np.float32)


def clap():
    t = tt(0.3)
    n = rs.randn(len(t))
    n = n - np.convolve(n, np.ones(8) / 8, "same")
    e = np.exp(-t * 18) + 0.6 * np.exp(-((t - 0.012) ** 2) * 60000)
    return (n * e * 0.5).astype(np.float32)


def tick(f=1800):
    t = tt(0.012)
    n = rs.randn(len(t)) * 0.5 + np.sin(2 * np.pi * f * t)
    return (n * np.exp(-t * 350)).astype(np.float32) * 0.35


def riser(d, f0=200, f1=4000):
    t = tt(d)
    n = rs.randn(len(t))
    for _ in range(3):
        n = np.convolve(n, np.ones(3) / 3, "same")      # warna lebih lembut
    n = n - np.convolve(n, np.ones(40) / 40, "same") * 0.9
    e = (t / d) ** 2.2
    f = f0 * (f1 / f0) ** (t / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return ((n * 2.2 + s * 0.5) * e).astype(np.float32) * 0.5


def impact(d=3.0):
    t = tt(d)
    f = 36 + 90 * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.5)
    n = rs.randn(len(t))
    n = np.convolve(n, np.ones(6) / 6, "same") * np.exp(-t * 2.2) * 0.8
    return (s + n * 0.5).astype(np.float32)


def sweep_down(d=0.9, f0=5000, f1=800):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2).astype(np.float32) * 0.3


def chirp(f0, d=0.14):
    t = tt(d)
    f = f0 + 900 * np.sin(np.pi * t / d) + 600 * t / d
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 1.5).astype(np.float32) * 0.18


def cricket(d=0.5):
    t = tt(d)
    g = (np.sin(2 * np.pi * 26 * t) > 0.3) * np.sin(np.pi * t / d)
    return (np.sin(2 * np.pi * 4700 * t) * g).astype(np.float32) * 0.04


# ---------------- komposisi ----------------
CH = [  # (bass, akord, ) per bar mod 4: Am F C G
    (110.0, [220.0, 261.63, 329.63]),
    (87.31, [174.61, 220.0, 261.63]),
    (130.81, [261.63, 329.63, 392.0]),
    (98.0, [196.0, 246.94, 293.66]),
]
MEL = [
    [(0, 659.25, 1.5), (1.5, 523.25, .5), (2, 587.33, 1), (3, 659.25, 1)],
    [(0, 698.46, 1.5), (1.5, 659.25, .5), (2, 523.25, 2)],
    [(0, 783.99, 1.5), (1.5, 659.25, .5), (2, 523.25, 1), (3, 659.25, 1)],
    [(0, 587.33, 1), (1, 659.25, 1), (2, 587.33, 1), (3, 493.88, 1)],
]
NB = int(DUR / BAR)
for b in range(NB):
    t0 = b * BAR
    bass, ch = CH[b % 4]
    # --- pad sepanjang lagu
    vol = 0.5 if b < 3 else 0.8
    if b >= 11:
        vol = 1.0
    for f in ch:
        add("wet", pad_note(f, BAR + 0.8), t0, rs.uniform(-.6, .6), 0.16 * vol)
        add("dry", pad_note(f / 2, BAR + 0.8), t0, 0, 0.08 * vol)
    # --- arpeggio pluck
    if b >= 1:
        steps = 8 if b >= 3 else 4
        for k in range(steps):
            seq = [0, 1, 2, 1, 2, 1, 2, 1] if True else None
            idx = [0, 1, 2, 3, 2, 1, 2, 3][k % 8]
            f = (ch + [ch[0] * 2])[idx] * 2
            tk = t0 + k * (BEAT / 2 if b >= 3 else BEAT)
            g = 0.22 if b >= 3 else 0.14
            add("wet", pluck(f, 0.6), tk, np.sin(k) * .5, g)
            add("dry", pluck(f, 0.4), tk, np.sin(k) * .5, g * .5)
    # --- drums & bass (bar 3..10, finale 11..13)
    groove = (3 <= b <= 9) or (11 <= b <= 13)
    build = (b == 2)
    if b in (10,):
        pass
    if groove:
        for k in range(4):
            tk = t0 + k * BEAT
            add("drums", kick(1.0), tk, 0, 0.9)
            add("drums", hat(0.09, 0.5), tk + BEAT / 2, 0.3, 0.35)
            if k in (1, 3):
                add("drums", clap(), tk, 0, 0.55)
        for k in range(8):
            add("drums", hat(0.04, 0.25), t0 + k * BEAT / 2 + BEAT / 4, -0.3, 0.2)
        # bass
        for k, off in enumerate((0, 1.5, 2, 3.5)):
            tb = t0 + off * BEAT
            tt_ = tt(BEAT * 1.4)
            s = np.sin(2 * np.pi * bass * tt_) + 0.35 * np.sin(2 * np.pi * bass * 2 * tt_)
            add("dry", (s * np.exp(-tt_ * 3.5) * np.minimum(tt_ * 400, 1)).astype(np.float32), tb, 0, 0.5)
    if build:
        for k in range(4):
            add("drums", kick(0.7), t0 + k * BEAT, 0, 0.6)
        # snare roll 16ths di bar terakhir sebelum reveal
    if b == 10:  # breakdown (tanpa kick) lalu naik
        pass
    # --- melodi lead
    if 5 <= b <= 9 or 11 <= b <= 13:
        for (off, f, dur) in MEL[b % 4]:
            add("wet", lead(f, dur * BEAT + 0.1), t0 + off * BEAT, 0.2, 0.17)
    # --- lonceng (malam) & akhir
    if 8 <= b <= 10 or b >= 12:
        for k, f in enumerate([ch[2] * 2, ch[1] * 2, ch[2] * 4, ch[0] * 4]):
            add("wet", bell(f, 2.0), t0 + k * BEAT, 0.6 * (-1) ** k, 0.18)

# snare roll sebelum reveal (5.0 - 6.0) & sebelum final (21 - 22)
for start, end in ((5.0, 6.0), (21.0, 22.0)):
    n = 8 if start == 5.0 else 12
    for k in range(n):
        tk = start + (end - start) * (k / n) ** 0.9
        add("drums", clap(), tk, 0, 0.2 + 0.4 * k / n)
# risers + impact
add("fx", riser(1.45, 250, 5000), 4.55, 0, 0.9)
add("fx", riser(2.0, 200, 6000), 20.0, 0, 1.0)
add("fx", impact(3.2), T_REVEAL, 0, 1.0)
add("fx", impact(4.5), T_FINAL, 0, 1.2)
add("fx", sweep_down(1.2, 6000, 600), T_REVEAL + 0.05, 0.4, 0.6)
add("fx", sweep_down(1.6, 7000, 400), T_FINAL + 0.05, -0.4, 0.6)
# kick besar di impact
add("drums", kick(1.4), T_REVEAL, 0, 1.0)
add("drums", kick(1.4), T_FINAL, 0, 1.1)
# detik hening sebelum final (duck) dibuat nanti lewat envelope master

# --- mengetik: tick
for k, (ch_, col, li) in enumerate(FLAT):
    if ch_ != " " and k % 2 == 0:
        add("fx", tick(1500 + 900 * rs.rand()), TYPE_TIMES[k], rs.uniform(-.3, .3), 0.9 + 0.3 * rs.rand())
# progress bar blip naik
for k in range(8):
    tk = T_PROGRESS0 + (T_PROGRESS1 - T_PROGRESS0) * k / 8
    add("fx", pluck(880 * 2 ** (k / 6), 0.25, 2), tk, 0.3, 0.18)
# enter di "run()"
add("fx", pluck(1320, .4, 2), T_TYPE_END + 0.05, 0, 0.3)

# --- ambience dunia: air, burung, jangkrik
t = tt(DUR - T_WORLD0 + 1)
w = rs.randn(len(t))
for _ in range(6):
    w = np.convolve(w, np.ones(5) / 5, "same")
wave_env = 0.5 + 0.5 * np.sin(2 * np.pi * t / 7.3)
amb = (w * (0.6 + 0.4 * wave_env) * 1.6 * np.minimum(t, 1)).astype(np.float32)
add("fx", amb, T_WORLD0, -0.1, 0.10)
for tb in np.arange(7.0, 13.5, 0.55):
    if rs.rand() < 0.75:
        for j in range(rs.randint(1, 4)):
            add("fx", chirp(rs.uniform(2600, 3600)), tb + j * 0.17, rs.uniform(-.8, .8), 1.0)
for tc in np.arange(15.8, 22.0, 0.5):
    add("fx", cricket(0.45), tc, rs.uniform(-.7, .7), 0.8)
for (ts, _, _) in SHOOTING:
    add("fx", sweep_down(0.8, 7500, 1500), ts, 0.5, 0.5)
# bunyi "sparkle" saat judul muncul
for k, f in enumerate([880, 1318, 1760, 2637]):
    add("wet", bell(f, 2.5), T_TITLE + k * 0.09, 0.3 * (-1) ** k, 0.22)
add("wet", bell(110 * 2, 5), T_FINAL, 0, 0.35)

# ---------------- mixing ----------------
def ir(n_s, decay, seed):
    r = np.random.RandomState(seed)
    t = np.arange(int(n_s * SR)) / SR
    x = r.randn(len(t)) * np.exp(-t * decay)
    x = np.convolve(x, np.ones(3) / 3, "same")
    return x.astype(np.float32) * 0.04


def reverb(x, seed):
    h = ir(2.4, 2.4, seed)
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    y = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)]
    return y.astype(np.float32)

# sidechain dari kick
kenv = np.zeros(N, np.float32)
kts = [b * BAR + k * BEAT for b in range(NB) for k in range(4) if (3 <= b <= 9) or (11 <= b <= 13)] + [T_REVEAL, T_FINAL]
for kt in kts:
    i = int(kt * SR)
    m = min(int(0.35 * SR), N - i)
    if m > 0:
        kenv[i:i + m] = np.maximum(kenv[i:i + m], np.exp(-np.arange(m) / SR * 9))
duck = 1 - 0.55 * kenv

outL = np.zeros(N, np.float32)
outR = np.zeros(N, np.float32)
wetL, wetR = reverb(L["wet"], 1), reverb(R["wet"], 2)
fxwL, fxwR = reverb(L["fx"] * 0.4, 3), reverb(R["fx"] * 0.4, 4)
outL = (L["dry"] + wetL * 1.6) * duck + L["drums"] * 0.9 + L["fx"] * 0.9 + fxwL * 0.8
outR = (R["dry"] + wetR * 1.6) * duck + R["drums"] * 0.9 + R["fx"] * 0.9 + fxwR * 0.8

# bar-5 sebelum final: tarik energi (duck singkat 0.18 dtk sebelum impact)
g = np.ones(N, np.float32)
for tcut in (T_REVEAL, T_FINAL):
    i = int((tcut - 0.12) * SR)
    g[i:i + int(0.12 * SR)] *= np.linspace(1, 0.15, int(0.12 * SR))
g[:int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
g[-int(2.2 * SR):] *= np.linspace(1, 0, int(2.2 * SR)) ** 1.5
outL *= g
outR *= g
peak = max(np.abs(outL).max(), np.abs(outR).max())
outL, outR = outL / peak * 1.5, outR / peak * 1.5
outL, outR = np.tanh(outL) * 0.89, np.tanh(outR) * 0.89
pcm = (np.stack([outL, outR], 1) * 32767).astype("<i2")
with wave.open("audio.wav", "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
print("audio ok", N / SR, "s; peak", np.abs(pcm).max())
