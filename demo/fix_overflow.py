#!/usr/bin/env python3
"""按实测高度一次性修正 frames-landing 各帧的溢出。"""
from pathlib import Path

D = Path("frames-landing")

# (文件, [(旧串, 新串), ...])
PATCH = {
    "p2-split.html": [
        (".bar { display:flex; align-items:center; gap:32px; margin-bottom:20px; height:84px; }",
         ".bar { display:flex; align-items:center; gap:32px; margin-bottom:18px; height:78px; }"),
        (".bar .tr { flex:1; height:84px;", ".bar .tr { flex:1; height:78px;"),
    ],
    "p3-spoiler.html": [
        ("h1 { font-size:66px;", "h1 { font-size:58px;"),
        (".main { margin-top:30px; display:flex; gap:56px; align-items:flex-start; }",
         ".main { margin-top:26px; display:flex; gap:52px; align-items:stretch; height:404px; }"),
        (".diagram { flex:none; width:840px; height:400px;",
         ".diagram { flex:none; width:840px; height:404px;"),
        ('<svg width="768" height="356" viewBox="0 0 768 380">',
         '<svg width="768" height="360" viewBox="0 0 768 380">'),
        (".steps { flex:1; display:flex; flex-direction:column; gap:16px; }",
         ".steps { flex:1; display:flex; flex-direction:column; gap:14px; justify-content:center; }"),
        (".st { display:flex; gap:24px; padding:20px 26px;",
         ".st { display:flex; gap:22px; padding:16px 24px;"),
        (".st .bd .h { font-size:28px;", ".st .bd .h { font-size:27px;"),
        (".st .bd .p { font-size:22px; color:#8497AC; line-height:1.5; }",
         ".st .bd .p { font-size:21px; color:#8497AC; line-height:1.45; }"),
        (".key { margin-top:auto; display:flex; gap:36px; align-items:stretch; padding-bottom:52px; }",
         ".key { margin-top:22px; display:flex; gap:36px; align-items:stretch; }"),
        (".kb { flex:1; padding:20px 32px;", ".kb { flex:1; padding:16px 30px;"),
        (".kb .n { font-size:36px;", ".kb .n { font-size:32px;"),
        (".kb .d { margin-top:8px; font-size:21px; color:#8497AC; line-height:1.45; }",
         ".kb .d { margin-top:6px; font-size:20px; color:#8497AC; line-height:1.4; }"),
    ],
    "p4-reverse.html": [
        ('<svg width="788" height="488" viewBox="0 0 808 500">',
         '<svg width="788" height="440" viewBox="0 0 808 500">'),
        (".side { flex:1; display:flex; flex-direction:column; gap:18px; }",
         ".side { flex:1; display:flex; flex-direction:column; gap:14px; }"),
        (".bx { flex:1; padding:20px 26px;", ".bx { flex:1; padding:16px 24px;"),
        (".bx .d { margin-top:8px; font-size:22px; color:#8497AC; line-height:1.45; }",
         ".bx .d { margin-top:6px; font-size:21px; color:#8497AC; line-height:1.4; }"),
        (".ladder { padding:22px 28px;", ".ladder { padding:18px 26px;"),
        (".ladder .h { font-size:25px; color:#E4C57E; margin-bottom:14px;",
         ".ladder .h { font-size:24px; color:#E4C57E; margin-bottom:12px;"),
        (".rung { display:flex; align-items:center; gap:18px; margin-bottom:13px; }",
         ".rung { display:flex; align-items:center; gap:18px; margin-bottom:10px; }"),
        (".rung .tr { flex:1; height:36px;", ".rung .tr { flex:1; height:32px;"),
    ],
    "p5-wheelbrake.html": [
        ("h1 { font-size:70px;", "h1 { font-size:58px;"),
        (".main { margin-top:30px; display:flex; gap:52px; align-items:stretch; margin-bottom:44px; }",
         ".main { margin-top:26px; display:flex; gap:48px; align-items:stretch; }"),
        (".side { flex:1; display:flex; flex-direction:column; gap:16px; }",
         ".side { flex:1; display:flex; flex-direction:column; gap:14px; }"),
        (".bx { padding:20px 26px;", ".bx { padding:16px 24px;"),
        (".bx .d { margin-top:8px; font-size:22px; color:#8497AC; line-height:1.5; }",
         ".bx .d { margin-top:6px; font-size:21px; color:#8497AC; line-height:1.4; }"),
        (".hc .bar2 { height:104px;", ".hc .bar2 { height:72px;"),
        (".hc .lb { margin-top:8px; font-size:22px; color:#8497AC; }",
         ".hc .lb { margin-top:6px; font-size:20px; color:#8497AC; }"),
        (".hc .vv { margin-top:3px; font-size:22px;", ".hc .vv { margin-top:2px; font-size:20px;"),
    ],
    "p6-handoff.html": [
        (".chart { margin-top:36px; position:relative; height:420px;",
         ".chart { margin-top:30px; position:relative; height:382px;"),
        ('<svg class="chartSvg" width="1720" height="310" viewBox="0 0 1720 310">',
         '<svg class="chartSvg" width="1720" height="286" viewBox="0 0 1720 310">'),
        (".bx { flex:1; padding:22px 30px;", ".bx { flex:1; padding:18px 28px;"),
        (".bx .n { font-size:36px;", ".bx .n { font-size:33px;"),
        (".bx .d { margin-top:8px; font-size:22px; color:#8497AC; line-height:1.45; }",
         ".bx .d { margin-top:6px; font-size:21px; color:#8497AC; line-height:1.4; }"),
    ],
    "p7-prelanding.html": [
        ("h1 { font-size:70px;", "h1 { font-size:62px;"),
        (".chart { margin-top:36px; position:relative; height:420px;",
         ".chart { margin-top:28px; position:relative; height:340px;"),
        ('<svg class="chartSvg" width="1780" height="392" viewBox="0 0 1840 424">',
         '<svg class="chartSvg" width="1780" height="310" viewBox="0 0 1840 424">'),
        (".bx { flex:1; padding:22px 30px;", ".bx { flex:1; padding:18px 28px;"),
        (".bx .n { font-size:32px;", ".bx .n { font-size:30px;"),
        (".bx .d { margin-top:8px; font-size:22px; color:#8497AC; line-height:1.45; }",
         ".bx .d { margin-top:6px; font-size:21px; color:#8497AC; line-height:1.4; }"),
    ],
    "p9-temperature.html": [
        (".chain .h { font-size:25px; color:#E4C57E; margin-bottom:18px;",
         ".chain .h { font-size:24px; color:#E4C57E; margin-bottom:14px;"),
        (".node { display:flex; gap:20px; align-items:flex-start; margin-bottom:16px; }",
         ".node { display:flex; gap:18px; align-items:flex-start; margin-bottom:12px; }"),
        (".chain { padding:24px 30px;", ".chain { padding:20px 28px;"),
        (".ab { padding:22px 28px;", ".ab { padding:18px 26px;"),
        (".abrow { display:flex; align-items:center; gap:20px; margin-bottom:14px; }",
         ".abrow { display:flex; align-items:center; gap:20px; margin-bottom:11px; }"),
        (".abrow .tr { flex:1; height:38px;", ".abrow .tr { flex:1; height:34px;"),
    ],
}

for name, pairs in PATCH.items():
    p = D / name
    s = p.read_text(encoding="utf-8")
    missed = []
    for old, new in pairs:
        if old not in s:
            missed.append(old[:60])
        else:
            s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print(name, "OK" if not missed else f"未命中: {missed}")
