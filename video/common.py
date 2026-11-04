"""Konstanta & timeline bersama untuk video 'Dunia dari Kode' (video + audio)."""
import numpy as np

W, H, FPS = 1080, 1920, 30
DUR = 30.0
BPM = 120
BEAT = 60.0 / BPM          # 0.5 s
BAR = BEAT * 4             # 2.0 s

T_TYPE0 = 0.5              # mulai mengetik kode
T_REVEAL = 6.0             # iris dunia terbuka (bar 3)
T_REVEAL_END = 7.4
T_WORLD0, T_WORLD1 = 6.0, 22.0   # siklus siang-malam
T_FINAL = 22.0             # dentuman final / galaksi
T_TITLE = 23.2

KW, ST, NU, CM, FN, PL, AT = ("kw", "st", "nu", "cm", "fn", "pl", "at")
CODE = [
    [("# dunia.py — dibuat oleh kode", CM)],
    [("import ", KW), ("numpy ", PL), ("as ", KW), ("np", PL)],
    [("from ", KW), ("PIL ", PL), ("import ", KW), ("Image", FN)],
    [],
    [("world ", PL), ("= ", KW), ("World", FN), ("(seed=", PL), ("42", NU), (")", PL)],
    [("world", PL), (".sun.", AT), ("rise", FN), ("(at=", PL), ('"05:30"', ST), (")", PL)],
    [("world", PL), (".", AT), ("add", FN), ("(Mountains(layers=", PL), ("3", NU), ("))", PL)],
    [("world", PL), (".", AT), ("add", FN), ("(Clouds(), Birds(n=", PL), ("7", NU), ("))", PL)],
    [("world", PL), (".night.", AT), ("fall", FN), ("(stars=", PL), ("True", KW), (")", PL)],
    [("world", PL), (".", AT), ("render", FN), ("(fps=", PL), ("30", NU), (", audio=", PL), ("True", KW), (")", PL)],
]
FLAT = [(ch, col, li) for li, line in enumerate(CODE) for seg, col in line for ch in seg]
_rs = np.random.RandomState(7)
TYPE_TIMES = []
_t = T_TYPE0
_prev = 0
for ch, col, li in FLAT:
    if li != _prev:
        _t += 0.10
        _prev = li
    TYPE_TIMES.append(_t)
    _t += _rs.uniform(0.010, 0.022)
T_TYPE_END = _t
T_PROGRESS0, T_PROGRESS1 = T_TYPE_END + 0.2, 5.9

SHOOTING = [(16.6, 0.80, 0.16), (18.9, 0.62, 0.10), (20.5, 0.9, 0.22)]  # (t, x frac, y frac)


def tod(t):
    return float(np.clip((t - T_WORLD0) / (T_WORLD1 - T_WORLD0), 0, 1))
