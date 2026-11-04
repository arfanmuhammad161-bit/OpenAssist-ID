"""Audio ambient 100% sintesis: pad paduan suara, lonceng, angin, efek per adegan. Tanpa alat musik/perkusi."""
import numpy as np, wave
from common import *
SR = 44100; N = int(DUR * SR)
rs = np.random.RandomState(21)
B = {k: [np.zeros(N, np.float32), np.zeros(N, np.float32)] for k in ("dry", "wet", "fx")}
def add(bus, sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    s = sig[max(0, -i):]; i = max(i, 0); n = min(len(s), N - i)
    B[bus][0][i:i + n] += s[:n] * g * np.cos((pan + 1) * np.pi / 4)
    B[bus][1][i:i + n] += s[:n] * g * np.sin((pan + 1) * np.pi / 4)
def tt(d): return np.arange(int(d * SR)) / SR
def adsr(n, a, r):
    e = np.ones(n, np.float32); a = int(a * SR); r = int(r * SR)
    e[:a] = np.linspace(0, 1, max(a, 1)) ** 1.5
    e[-r:] *= np.linspace(1, 0, r) ** 1.5
    return e
def formant(h, f0):
    fr = f0 * h
    return 1 / h ** 1.2 * (1 + 2.2 * np.exp(-((fr - 700) / 220) ** 2) + 1.6 * np.exp(-((fr - 1150) / 260) ** 2))
def choir(f, d, a=1.6):
    t = tt(d); out = np.zeros_like(t)
    for det in (-0.006, 0.0, 0.006):
        vib = 1 + 0.0035 * np.sin(2 * np.pi * (4.8 + det * 100) * t + rs.rand() * 6)
        ph = 2 * np.pi * np.cumsum(f * (1 + det) * vib) / SR
        for h in range(1, 14): out += formant(h, f) * np.sin(ph * h + h)
    return (out * adsr(len(t), a, 2.0) / 40).astype(np.float32)
def bell(f, d=3.0):
    t = tt(d); s = np.zeros_like(t)
    for r_, a in ((1, 1), (2.01, .45), (2.76, .35), (4.1, .2), (5.4, .12)): s += a * np.sin(2 * np.pi * f * r_ * t) * np.exp(-t * (1.1 + r_ * .6))
    return (s * np.minimum(t * 900, 1) * 0.45).astype(np.float32)
def noise_lp(d, k):
    n = rs.randn(int(d * SR))
    for _ in range(3): n = np.convolve(n, np.ones(k) / k, "same")
    return n.astype(np.float32)
def swell(d, rev=False):
    t = tt(d); n = noise_lp(d, 6) * 6
    e = (t / d) ** 2 if not rev else (1 - t / d) ** 2
    f = 220 * (18 ** (t / d))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return ((n + s) * e * np.sin(np.pi * np.minimum(t / d, 1) * .5 + .0)).astype(np.float32) * 0.5
def boom(d=3.5, f0=48):
    t = tt(d); f = f0 + 40 * np.exp(-t * 4)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3) + 0.5 * noise_lp(d, 40) * np.exp(-t * 2)
    return (s * 0.9).astype(np.float32)
def chirp(f0, d=0.13):
    t = tt(d); f = f0 + 900 * np.sin(np.pi * t / d) + 500 * t / d
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 1.5).astype(np.float32) * 0.16

HJ = [293.66, 311.13, 369.99, 392.0, 440.0, 466.16, 523.25, 587.33]
BOUND = [s[0] for s in SCENES] + [DUR]
CH = [[146.83, 220, 293.66], [155.56, 233.08, 293.66], [196, 233.08, 293.66], [146.83, 185, 220, 293.66], [146.83, 185, 220, 293.66, 369.99],
       [155.56, 196, 233.08, 311.13], [146.83, 220, 261.63], [196, 233.08, 293.66, 311.13], [146.83, 185, 220, 293.66, 369.99, 440]]
for i, (a, b, *_ ) in enumerate(SCENES):
    d = (b - a) + 3.0
    for f in CH[i]:
        add("wet", choir(f, d, 1.8), a - 0.3 if i else 0, rs.uniform(-.7, .7), 0.16 + (0.05 if i == 8 else 0))
    add("dry", choir(CH[i][0] / 2, d, 2.0), a, 0, 0.14)
# dengung dasar D2
t = tt(DUR); dr = (np.sin(2 * np.pi * 73.42 * t) + 0.5 * np.sin(2 * np.pi * 110.0 * t + 1) + 0.25 * np.sin(2 * np.pi * 146.83 * t)) * (0.7 + 0.3 * np.sin(2 * np.pi * t / 9))
add("dry", (dr * 0.16).astype(np.float32), 0, 0, 1)
# angin gurun
w = noise_lp(DUR, 9); wv = 0.5 + 0.5 * np.sin(2 * np.pi * t / 6.5 + np.sin(t * .7))
add("fx", (w * wv * 0.5).astype(np.float32), 0, 0, 0.5)
# lonceng hijaz — rapat tergantung adegan
dens = [0.7, 0.9, 0.55, 1.0, 1.2, 0.9, 0.5, 0.6, 1.3]
for i, (a, b, *_ ) in enumerate(SCENES):
    tcur = a + 0.8
    while tcur < b - 0.4:
        f = HJ[rs.randint(0, len(HJ))] * rs.choice([1, 1, 2])
        add("wet", bell(f, 3.2), tcur, rs.uniform(-.8, .8), 0.22)
        tcur += rs.choice([0.5, 0.75, 1.0, 1.5]) / dens[i]
# transisi: dentuman lembut + swell
for (a, *_ ) in SCENES[1:]:
    add("fx", boom(3.0), a, 0, 0.6)
    add("fx", swell(1.4), a - 1.4, 0, 0.7)
# rewind 3.0-4.0 (membalik waktu)
add("fx", swell(1.2, True), 3.0, 0, 0.9)
# adegan 2: burung & kerikil
for tb in np.arange(11.8, 14.6, 0.16):
    add("fx", chirp(rs.uniform(2500, 4200)), tb, rs.uniform(-.9, .9), 1.0)
for tb in np.arange(12.6, 14.4, 0.07):
    n = noise_lp(0.03, 3) * np.exp(-tt(0.03) * 120)
    add("fx", n.astype(np.float32), tb, rs.uniform(-.7, .7), 0.5)
# adegan 3: batu terangkat
add("wet", bell(880, 4), 20.2, 0, 0.35); add("wet", bell(1318.5, 4), 20.35, 0.3, 0.3); add("fx", boom(2.0, 70), 18.5, 0, 0.4)
# adegan 4: cahaya
add("fx", swell(1.6), 20.4, 0, 1.0)
for k, f in enumerate([587.33, 739.99, 880, 1174.66, 1479.98]): add("wet", bell(f, 4.5), 22.0 + k * 0.1, 0.5 * (-1) ** k, 0.32)
# adegan 5: api
for tc in np.arange(27.1, 29.4, 0.03):
    n = noise_lp(0.02, 2) * np.exp(-tt(0.02) * 150) * rs.rand()
    add("fx", n.astype(np.float32), tc, rs.uniform(-.8, .8), 0.9)
add("fx", (noise_lp(2.5, 14) * np.sin(np.pi * tt(2.5) / 2.5)).astype(np.float32) * 3, 27.0, 0, 0.6)
# adegan 6: gemuruh + lonceng kembali
add("fx", boom(4.0, 36), 33.0, 0, 0.8); add("wet", bell(587.33, 5), 36.2, 0, 0.4); add("wet", bell(880, 5), 36.45, 0.3, 0.3)
# adegan 7: hujan, air, guruh
add("fx", (noise_lp(6.0, 3) * np.sin(np.pi * tt(6.0) / 6.0) ** 0.8).astype(np.float32) * 1.4, 37.0, 0, 0.35)
add("fx", (noise_lp(3.0, 28) * np.sin(np.pi * tt(3.0) / 3.0)).astype(np.float32) * 5, 37.6, -0.2, 0.7)
add("fx", boom(3.0, 40), 38.6, 0, 0.9)
# adegan 8: akhir
for k, f in enumerate([880, 1174.66, 1479.98, 1760, 2349.3]): add("wet", bell(f, 5), 46.8 + k * 0.12, 0.4 * (-1) ** k, 0.28)
add("fx", boom(4.5, 55), 46.8, 0, 0.8)
# mixing
def reverb(x, seed, decay=1.6, length=3.2):
    r = np.random.RandomState(seed); tI = np.arange(int(length * SR)) / SR
    h = np.convolve(r.randn(len(tI)) * np.exp(-tI * decay), np.ones(3) / 3, "same").astype(np.float32) * 0.035
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)].astype(np.float32)
out = []
for c in (0, 1):
    out.append(B["dry"][c] + reverb(B["wet"][c], 3 + c) * 1.7 + B["fx"][c] * 0.9 + reverb(B["fx"][c] * 0.4, 7 + c) * 0.8)
g = np.ones(N, np.float32); g[:int(1.2 * SR)] *= np.linspace(0, 1, int(1.2 * SR)); g[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR)) ** 1.5
out = [o * g for o in out]; pk = max(abs(o).max() for o in out)
out = [np.tanh(o / pk * 1.6) * 0.89 for o in out]
pcm = (np.stack(out, 1) * 32767).astype("<i2")
with wave.open("audio.wav", "wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
print("audio ok", N / SR)
