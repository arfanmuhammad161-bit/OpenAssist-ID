"""Menyusun timeline dari durasi narasi ElevenLabs + membuat track suara (vo.wav)."""
import json, subprocess, numpy as np, wave
SR = 44100
CHUNKS = [
 [("Piramida Giza", "Piramida Giza"), ("berdiri 4.500 tahun.", "sudah berdiri empat ribu lima ratus tahun."), ("Tapi bentuk sempurnanya…", "Tapi bentuk sempurnanya"), ("lahir dari KEGAGALAN.", "lahir dari kegagalan.")],
 [("Awalnya, orang Mesir", "Awalnya, orang Mesir"), ("hanya menumpuk batu.", "hanya menumpuk batu."), ("Piramida Djoser:", "Piramida Djoser"), ("6 tingkat,", "punya enam tingkat,"), ("setinggi 62 meter.", "setinggi enam puluh dua meter.")],
 [("Raja Snefru ingin", "Lalu Raja Snefru ingin"), ("sisi yang mulus.", "sisi yang mulus."), ("Tapi bangunan mulai RETAK,", "Tapi bangunan mulai retak,"), ("jadi sudutnya dipangkas,", "jadi di tengah jalan sudutnya dipangkas,"), ("dari 54° menjadi 43°.", "dari lima puluh empat, menjadi empat puluh tiga derajat.")],
 [("Mereka tidak menyerah.", "Mereka tidak menyerah."), ("Piramida Merah akhirnya", "Piramida Merah akhirnya"), ("jadi piramida mulus", "jadi piramida bersisi mulus"), ("yang PERTAMA.", "yang pertama.")],
 [("Putranya, Khufu,", "Putranya, Khufu,"), ("membangun yang terbesar.", "membangun yang terbesar."), ("2,3 juta balok batu,", "Dua koma tiga juta balok batu,"), ("dalam 20 tahun.", "dalam dua puluh tahun."), ("Lebih tinggi dari MONAS.", "Lebih tinggi dari Monas.")],
 [("Dan pekerjanya", "Dan pekerjanya"), ("BUKAN BUDAK.", "bukan budak."), ("Puluhan ribu tenaga terampil,", "Mereka puluhan ribu tenaga terampil,"), ("dibayar dan diberi makan.", "yang dibayar dan diberi makan.")],
 [("Dulu, dilapisi batu putih", "Dulu, ia dilapisi batu putih"), ("berkilau.", "berkilau."), ("Setelah gempa 1303,", "Setelah gempa tahun seribu tiga ratus tiga,"), ("banyak lapisannya LEPAS.", "banyak batu pelapisnya lepas.")],
 [("Tanpa piramida", "Tanpa piramida"), ("yang GAGAL itu,", "yang gagal itu,"), ("tak ada keajaiban dunia", "tak akan ada keajaiban dunia"), ("yang masih berdiri.", "yang masih berdiri hari ini.")],
]
durs = [float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"vo/v{i}.wav"])) for i in range(1, 9)]
LEAD, GAP, OUTRO = 0.12, 0.30, 2.2
SIL = {1: [(3.247, 1.297), (6.049, .375)], 2: [(.652, .272), (2.454, .376), (4.499, .408)], 3: [(2.278, .429), (4.132, .451), (6.619, .325), (8.062, .317)],
       4: [(1.007, .347)], 5: [(.682, .151), (1.313, .236), (2.685, .332), (4.98, .148), (6.248, .295)], 6: [(1.198, .425), (3.409, .391)],
       7: [(2.426, .358), (4.879, .253)], 8: [(1.693, .277)]}
MAP = {1: [0, 0, 1, 2], 2: [0, 1, 2, 2, 3], 3: [0, 0, 1, 2, (3, 4)], 4: [0, 1, 1, 1], 5: [(0, 1), 2, 3, 4, 5], 6: [0, 0, 1, 2], 7: [0, 0, 1, 2], 8: [0, 0, 1, 1]}
scenes = []; t = 0.0
for i, d in enumerate(durs):
    L = LEAD + d + GAP + (OUTRO if i == 7 else 0)
    sil = SIL[i + 1]; bounds = [0.0] + [x for (a, b) in sil for x in (a, a + b)] + [d]
    segs = [(bounds[2 * k], bounds[2 * k + 1]) for k in range(len(sil) + 1)]
    ch = [None] * len(CHUNKS[i]); mp = MAP[i + 1]
    # chunk yang berbagi satu segmen -> bagi sebanding bobot
    for sg in sorted(set(m for m in mp if isinstance(m, int))):
        idx = [k for k, m in enumerate(mp) if m == sg]; ws = [len(CHUNKS[i][k][1]) + (4 if CHUNKS[i][k][1].rstrip().endswith((",", ".")) else 0) for k in idx]
        a, b = segs[sg]; acc = a
        for k, w in zip(idx, ws):
            span = (b - a) * w / sum(ws); ch[k] = dict(text=CHUNKS[i][k][0], t0=round(LEAD + acc, 3), t1=round(LEAD + acc + span, 3)); acc += span
    for k, m in enumerate(mp):
        if isinstance(m, tuple): ch[k] = dict(text=CHUNKS[i][k][0], t0=round(LEAD + segs[m[0]][0], 3), t1=round(LEAD + segs[m[1]][1], 3))
    marks = {}
    if i == 2: marks = dict(d=round(LEAD + segs[3][0], 3), e=round(LEAD + segs[4][0], 3))
    scenes.append(dict(i=i + 1, start=round(t, 3), dur=round(L, 3), vo_start=round(t + LEAD, 3), vo_dur=d, chunks=ch, marks=marks, segs=[(round(LEAD + a, 3), round(LEAD + b, 3)) for a, b in segs])); t += L
total = round(t, 3)
json.dump(dict(total=total, scenes=scenes), open("timeline.json", "w"), ensure_ascii=False, indent=1)
# track suara
N = int((total + 0.5) * SR); out = np.zeros(N, np.float32)
for i, s in enumerate(scenes):
    with wave.open(f"vo/v{i+1}.wav") as wf: a = np.frombuffer(wf.readframes(wf.getnframes()), "<i2").astype(np.float32) / 32768
    k = int(s["vo_start"] * SR); out[k:k + len(a)] += a
pk = np.abs(out).max(); out = out / pk * 0.92
with wave.open("vo.wav", "wb") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((out * 32767).astype("<i2").tobytes())
print("total", total, [round(s["start"], 2) for s in scenes])
