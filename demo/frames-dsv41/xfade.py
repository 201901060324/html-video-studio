#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 22 个分镜用 0.4s 交叉溶解串成一条片子，并混入配乐。
切点几何对齐 + 溶解，是本片"丝滑"的两个手段。
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.dirname(HERE)
OUT = os.path.join(DEMO, "out-dsv41")
FF = "/Users/songzhigui/.workbuddy/binaries/node/workspace/bin/ffmpeg"
FADE = 0.40

scenes = json.load(open(os.path.join(HERE, "scenes.json"), encoding="utf-8"))
n = len(scenes)
clips = [os.path.join(OUT, "clip%d.mp4" % (i + 1)) for i in range(n)]
for c in clips:
    if not os.path.exists(c):
        sys.exit("缺少片段: " + c)

args = [FF, "-y"]
for c in clips:
    args += ["-i", c]

fc, labels = [], []
for i in range(n):
    fc.append("[%d:v]settb=AVTB,fps=30,format=yuv420p,setpts=PTS-STARTPTS[v%d]" % (i, i))
    labels.append("v%d" % i)

prev = "v0"
acc = scenes[0]["seconds"]
for i in range(1, n):
    off = acc - FADE
    out = "x%d" % i
    fc.append("[%s][v%d]xfade=transition=fade:duration=%.3f:offset=%.3f[%s]"
              % (prev, i, FADE, off, out))
    acc = acc + scenes[i]["seconds"] - FADE
    prev = out

silent = os.path.join(OUT, "dsv41-silent.mp4")
args += ["-filter_complex", ";".join(fc), "-map", "[%s]" % prev,
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", silent]
print("拼接中… 预计 %.1fs" % acc)
subprocess.run(args, check=True)

final = os.path.join(OUT, "DeepSeek-V4.1-Flash-1017.mp4")
subprocess.run([FF, "-y", "-i", silent, "-i", os.path.join(HERE, "bgm.wav"),
                "-filter_complex", "[1:a]volume=0.94,afade=t=out:st=%.2f:d=2.5[a]" % (acc - 2.5),
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", final], check=True)
print("DONE ->", final)
