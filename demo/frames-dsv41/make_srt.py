#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽出画面字幕，生成与成片对齐的 .srt（供平台上传或外挂字幕用）"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
FADE = 0.40
scenes = json.load(open(os.path.join(HERE, "scenes.json"), encoding="utf-8"))

cuts, acc = [], 0.0
for i, s in enumerate(scenes):
    cuts.append(round(acc - i * FADE, 3))
    acc += s["seconds"]
total = round(acc - FADE * (len(scenes) - 1), 3)


def block(src, cls):
    """取出 class 以 cls 开头的 div 及其配对内容"""
    i = src.find('class="%s' % cls)
    if i < 0:
        return None, ""
    st = src.rfind("<div", 0, i)
    depth, j = 0, st
    while True:
        nxt_open = src.find("<div", j + 1)
        nxt_close = src.find("</div>", j + 1)
        if nxt_close < 0:
            break
        if 0 <= nxt_open < nxt_close:
            depth += 1
            j = nxt_open
        else:
            if depth == 0:
                body = src[src.find(">", st) + 1:nxt_close]
                attrs = src[st:src.find(">", st)]
                return attrs, body
            depth -= 1
            j = nxt_close
    return None, ""


def plain(x):
    x = re.sub(r"<br\s*/?>", "\n", x)
    x = re.sub(r"<[^>]+>", "", x)
    x = html.unescape(x).replace("\u00a0", " ")
    return "\n".join(l.strip() for l in x.split("\n") if l.strip())


def ts(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return "%02d:%02d:%06.3f" % (h, m, s)


MANUAL = {"p14": ("我读得懂这个世界。千亿级网页索引，每天数亿次检索请求。", 0.55),
          "p19": ("探索未至之境。", 1.0)}

out = []
for i, s in enumerate(scenes):
    src = open(os.path.join(HERE, s["file"]), encoding="utf-8").read()
    name = s["file"][:-5]
    if name in MANUAL:
        txt, delay = MANUAL[name]
    else:
        attrs, body = block(src, "sub")
        if not body:
            continue
        txt = plain(body)
        txt = re.sub(r"^\d+\s*/\s*22\s*·\s*[^\n]*\n", "", txt).strip()
        d = re.search(r"animation-delay:\s*([\d.]+)s", attrs or "")
        delay = float(d.group(1)) if d else 0.6
    if not txt:
        continue
    start = cuts[i] + delay * 0.8
    end = min(cuts[i + 1] + 0.15 if i + 1 < len(cuts) else total, total - 0.2)
    out.append((start, end, txt))

with open(os.path.join(HERE, "DeepSeek-V4.1-Flash-1017.srt"), "w", encoding="utf-8") as f:
    for k, (a, b, t) in enumerate(out, 1):
        f.write("%d\n%s --> %s\n%s\n\n" % (k, ts(a), ts(b), t))
print("字幕条数", len(out), "总长 %.1fs" % total)
for a, b, t in out:
    print("%6.1f %6.1f  %s" % (a, b, t.replace("\n", " / ")))

with open(os.path.join(HERE, "subtitle-text.md"), "w", encoding="utf-8") as f:
    f.write("# 字幕 / 旁白文本\n\n")
    for a, b, t in out:
        f.write("%s  \n%s\n\n" % (ts(a).replace(",", "."), t.replace("\n", "  ")))
