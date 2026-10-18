#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek V4.1-Flash-1017 宣传片 · 原创配乐（程序合成，无版权问题）
按分镜时间点编排：前奏 / 打字脉冲 / 坠落-爆发 / 主律动 / 断奏 / 终章。
"""
import json, os, sys
import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
FADE = 0.40

# ── 分镜时间（与 xfade 对齐）─────────────────────────────────────────────
scenes = json.load(open(os.path.join(HERE, "scenes.json"), encoding="utf-8"))
cuts, acc = [], 0.0
for i, s in enumerate(scenes):
    cuts.append((s["file"], round(acc - i * FADE, 3)))
    acc += s["seconds"]
TOTAL = round(acc - FADE * (len(scenes) - 1), 3)
T = float(TOTAL)
N = int(SR * (T + 1.0))
print("总长 %.2fs" % T, "镜头", len(cuts))

# 关键节点
C = {name.replace(".html", ""): t for name, t in cuts}
K = dict(typ=C["p03"], drop=C["p04"], build=C["p05"], palace=C["p06"], race=C["p07"],
         portal=C["p08"], valley=C["p09"], cards=C["p10"], pareto=C["p11"], bars=C["p12"],
         harness=C["p13"], globe=C["p14"], filter=C["p15"], api=C["p16"], openw=C["p17"],
         converge=C["p18"], brand=C["p19"], model=C["p20"], entries=C["p21"], end=C["p22"])
print({k: round(v, 1) for k, v in K.items()})

BPM = 92.0
BEAT = 60.0 / BPM
BAR = BEAT * 4

def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)

# ── 基础音色 ────────────────────────────────────────────────────────────
rng = np.random.default_rng(20261017)

_PC = {}
def pad(f, dur, amp=1.0):
    key = (round(f, 3), round(dur, 3))
    if key in _PC:
        return _PC[key] * amp
    n = int(dur * SR); t = np.arange(n) / SR
    w = np.zeros(n)
    for h, g in ((1, 1.0), (2, 0.42), (3, 0.22), (4, 0.12), (5, 0.07)):
        for dt in (-0.0012, 0.0, 0.0013):
            w += g * np.sin(2 * np.pi * f * h * (1 + dt) * t + h * 1.7 + dt * 900)
    w /= 3.0
    a = np.clip(t / 0.55, 0, 1) ** 2
    r = np.clip((dur - t) / 0.9, 0, 1) ** 1.5
    out = (w * a * r).astype(np.float32)
    _PC[key] = out
    return out * amp

def pluck(f, dur, amp=1.0, dec=7.0):
    n = int(dur * SR); t = np.arange(n) / SR
    w = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(4 * np.pi * f * t) + 0.10 * np.sin(6 * np.pi * f * t)
    e = np.exp(-t * dec) * (1 - np.exp(-t * 320))
    return (amp * w * e).astype(np.float32)

def bell(f, dur, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    w = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.01 * t) + 0.28 * np.sin(2 * np.pi * f * 3.02 * t)
    e = np.exp(-t * 1.4) * (1 - np.exp(-t * 200))
    return (amp * w * e).astype(np.float32)

def bass(f, dur, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    w = np.sin(2 * np.pi * f * t) + 0.30 * np.sin(4 * np.pi * f * t) + 0.10 * np.sin(6 * np.pi * f * t)
    e = np.clip(t / 0.008, 0, 1) * np.exp(-t * 2.2)
    return (amp * w * e).astype(np.float32)

def kick(amp=1.0):
    n = int(0.55 * SR); t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 26)
    w = np.sin(2 * np.pi * np.cumsum(f) / SR)
    e = np.exp(-t * 6.5)
    ck = rng.standard_normal(n) * np.exp(-t * 220) * 0.25
    return (amp * (w * e + ck)).astype(np.float32)

def hat(amp=1.0, dec=70.0):
    n = int(0.14 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))
    return (amp * x * np.exp(-t * dec) * 0.5).astype(np.float32)

def snare(amp=1.0):
    n = int(0.30 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-t * 16)
    x = np.diff(np.concatenate([[0], x])) * 0.6
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28) * 0.5
    return (amp * (x + tone)).astype(np.float32)

def riser(dur, amp=1.0, f0=180, f1=3800):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    # 简易时变带通：用两段信号交叉淡化近似
    b = np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * 0.25
    e = (t / dur) ** 2.2
    return (amp * (x * 0.10 + b) * e).astype(np.float32)

def swell(dur, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    e = (t / dur) ** 3
    return (amp * x * e * 0.5).astype(np.float32)

# ── 总线 ────────────────────────────────────────────────────────────────
L = np.zeros(N, dtype=np.float32)
R = np.zeros(N, dtype=np.float32)
SEND = np.zeros(N, dtype=np.float32)

def add(buf, t0, amp=1.0, pan=0.0, send=0.25):
    if t0 >= T + 0.5: return
    i0 = int(t0 * SR)
    n = min(len(buf), N - i0)
    if n <= 0: return
    seg = buf[:n] * amp
    l = np.sqrt((1 - pan) / 2 + 0.5) * 0.9
    r = np.sqrt((1 + pan) / 2 + 0.5) * 0.9
    L[i0:i0 + n] += seg * l
    R[i0:i0 + n] += seg * r
    SEND[i0:i0 + n] += seg * send

def gain_curve(pts):
    xs = np.array([p[0] for p in pts]); ys = np.array([p[1] for p in pts])
    tt = np.arange(N) / SR
    return np.interp(tt, xs, ys).astype(np.float32), None

def at(curve, t):
    i = int(min(max(t, 0) * SR, N - 1))
    return float(curve[i])

# 各层能量曲线
G_DRUM, _ = gain_curve([(0, 0), (K["typ"], 0), (K["drop"], 0.10), (K["build"] + .2, 0.85),
                        (K["cards"], 0.9), (K["cards"] + .3, 0.0), (K["pareto"] + .2, 0.72),
                        (K["converge"], 0.55), (K["converge"] + .3, 0.0), (K["brand"], 0.42),
                        (K["end"], 0.0), (T, 0)])
G_ARP, _ = gain_curve([(0, 0), (K["typ"], 0.12), (K["drop"], 0.25), (K["build"], 0.5),
                       (K["cards"], 0.55), (K["cards"] + .3, 0.30), (K["pareto"], 0.55),
                       (K["converge"], 0.45), (K["brand"], 0.38), (K["end"], 0.16), (T, 0)])
G_BASS, _ = gain_curve([(0, 0.0), (K["typ"], 0.18), (K["drop"], 0.35), (K["build"], 0.75),
                        (K["cards"], 0.8), (K["cards"] + .3, 0.0), (K["pareto"], 0.7),
                        (K["converge"], 0.6), (K["converge"] + .3, 0.0), (K["brand"], 0.55),
                        (K["end"], 0.25), (T, 0)])
G_PAD, _ = gain_curve([(0, 0.2), (K["typ"], 0.45), (K["drop"], 0.6), (K["build"], 0.5),
                       (K["cards"], 0.55), (K["cards"] + .3, 0.85), (K["pareto"], 0.5),
                       (K["converge"], 0.7), (K["converge"] + .3, 0.85), (K["brand"], 0.9),
                       (K["end"], 0.8), (T, 0.0)])

# ── 和声：Dm – Bb – F – C（每和弦 2 小节）──────────────────────────────
CHORDS = [
    (50, [62, 65, 69, 74]),   # Dm
    (46, [58, 62, 65, 70]),   # Bb
    (41, [57, 60, 65, 69]),   # F
    (48, [55, 60, 64, 69]),   # C
]
n_bars = int(T / BAR) + 2

# 前奏单独铺一条 Dm 长音
for b in range(0, n_bars):
    t0 = b * BAR
    ch = CHORDS[(b // 2) % 4]
    root, notes = ch
    e = at(G_PAD, t0 + .1)
    if e < 0.02: continue
    for j, m in enumerate(notes):
        add(pad(m2f(m - 12), BAR * 2.05, 0.26), t0, e, pan=(j - 1.5) * 0.22, send=0.55)
    # 低音铺底
    add(pad(m2f(root - 12), BAR * 2.05, 0.11), t0, at(G_BASS, t0 + .1) * 0.8, 0, 0.2)

# 脉冲（打字动机）：16 分音符的木鱼感
for k in range(int(T / (BEAT / 4)) + 1):
    t0 = k * BEAT / 4
    if k % 2 == 0:
        continue
    e = at(G_ARP, t0) * 0.10
    if e > 0.004:
        add(pluck(2100 if k % 4 else 2450, 0.09, e*0.45, dec=55), t0, 1.0, (k % 8 - 4) * 0.06, 0.3)

# 琶音
for k in range(int(T / (BEAT / 2)) + 1):
    t0 = k * BEAT / 2
    b = int(t0 / BAR)
    ch = CHORDS[(b // 2) % 4]
    notes = ch[1]
    e = at(G_ARP, t0)
    if e < 0.02: continue
    m = notes[[0, 2, 1, 3, 2, 0, 3, 1][k % 8]] + 12
    add(pluck(m2f(m), 0.55, 0.115 * e, dec=6.5), t0, 1.0, ((k % 4) - 1.5) * 0.3, 0.45)

# 鼓组
for k in range(int(T / (BEAT / 2)) + 1):
    t0 = k * BEAT / 2
    e = at(G_DRUM, t0)
    if e < 0.03: continue
    if k % 4 == 0:
        add(kick(0.55 * e), t0, 1.0, 0, 0.08)
    if k % 4 == 2 and e > 0.35:
        add(hat(0.15 * e), t0, 1.0, 0.25, 0.12)
    if k % 8 == 6 and e > 0.5:
        add(hat(0.11 * e, 30), t0, 1.0, -0.25, 0.12)
    if e > 0.62 and k % 8 in (3, 7):
        add(snare(0.20 * e), t0, 1.0, 0, 0.32)

# 低音律动
for k in range(int(T / (BEAT / 2)) + 1):
    t0 = k * BEAT / 2
    b = int(t0 / BAR)
    root = CHORDS[(b // 2) % 4][0]
    e = at(G_BASS, t0)
    if e < 0.03: continue
    if k % 2 == 0:
        add(bass(m2f(root - 12), BEAT * 0.9, 0.17 * e), t0, 1.0, 0, 0.1)

# 主题旋律：在帕累托 / 品牌段出现
THEME = [(0, 74, 1.5), (1.5, 77, .5), (2, 76, 1), (3, 74, 2),
         (4, 69, 1.5), (5.5, 72, .5), (6, 74, 2),
         (8, 77, 1.5), (9.5, 79, .5), (10, 77, 1), (11, 76, 2),
         (12, 72, 2), (14, 74, 2)]
for seg_start, seg_end, amp in ((K["pareto"], K["harness"] + 1, 0.10),
                                (K["globe"], K["converge"], 0.09),
                                (K["brand"], T - 3, 0.15)):
    b0 = int(seg_start / BAR)
    for rep in range(0, int((seg_end - seg_start) / (BAR * 4)) + 1):
        base = (b0 + rep * 4) * BAR
        for off, m, d in THEME:
            t0 = base + off * BEAT
            if seg_start - 0.5 <= t0 <= seg_end:
                fadei = min(1.0, (t0 - seg_start) / 1.5, max(0.05, (seg_end - t0) / 2.0))
                add(bell(m2f(m), d * BEAT * 1.6, amp * 1.5 * fadei), t0, 1.0, 0.0, 0.7)

# 前奏的稀疏钟声（给黑暗留一点空气）
for t0, m, a in ((1.2, 86, 0.10), (5.4, 81, 0.075), (9.6, 77, 0.065), (12.4, 74, 0.06)):
    add(bell(m2f(m), 5.0, a), t0, 1.0, (0.4 if m % 2 else -0.4), 0.9)

# 转场音效
add(swell(2.2, 0.22), K["drop"] - 2.2, 1.0, 0, 0.6)
add(riser(4.4, 0.16), K["build"] - 4.4, 1.0, 0, 0.5)
add(swell(1.8, 0.18), K["pareto"] - 1.8, 1.0, 0, 0.7)
add(riser(8.0, 0.20, 120, 5200), K["converge"], 1.0, 0, 0.55)
add(swell(2.6, 0.24), K["brand"] - 2.6, 1.0, 0, 0.7)
# 收尾：一声低频落地 + 长尾
add(kick(0.5), K["brand"], 1.0, 0, 0.4)
add(kick(0.42), K["model"], 1.0, 0, 0.4)

# ── 混响（Schroeder）──────────────────────────────────────────────────
def comb(x, d, g):
    y = x.copy()
    n = len(y)
    for s in range(d, n, d):
        e = min(s + d, n)
        y[s:e] += g * y[s - d:e - d]
    return y

def allpass(x, d, g):
    y = np.zeros_like(x)
    n = len(x)
    for s in range(0, n, d):
        e = min(s + d, n)
        y[s:e] = -g * x[s:e] + (x[s - d:e - d] if s >= d else 0) + (g * y[s - d:e - d] if s >= d else 0)
    return y

def reverb(sig):
    outL = np.zeros_like(sig); outR = np.zeros_like(sig)
    for d, g in ((2143, 0.80), (2791, 0.78), (3301, 0.76), (3907, 0.74)):
        outL += comb(sig, d, g) * 0.25
        outR += comb(sig, d + 37, g) * 0.25
    for d, g in ((137, 0.62), (263, 0.60)):
        outL = allpass(outL, d, g); outR = allpass(outR, d + 11, g)
    return outL, outR

print("混响计算…")
rl, rr = reverb(SEND * 0.55)
L += rl * 0.55
R += rr * 0.55

# ── 母带 ────────────────────────────────────────────────────────────────
# 轻度高通去低频浑浊
mix = np.stack([L, R], axis=1)
# 软化削波
mix = np.tanh(mix * 1.15) * 0.92
peak = float(np.max(np.abs(mix)))
mix = mix / max(peak, 1e-6) * 0.94

# 首尾淡入淡出
n_in = int(1.6 * SR); n_out = int(4.0 * SR)
mix[:n_in] *= np.linspace(0, 1, n_in)[:, None] ** 1.4
mix[-n_out:] *= np.linspace(1, 0, n_out)[:, None] ** 1.6

out = os.path.join(HERE, "bgm.wav")
wavfile.write(out, SR, (mix * 32767).astype(np.int16))
print("写出", out, "%.1fs" % (len(mix) / SR), "peak %.2f dB" % (20 * np.log10(np.max(np.abs(mix)))))
