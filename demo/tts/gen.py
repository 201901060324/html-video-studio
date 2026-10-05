#!/usr/bin/env python3
"""
为 html-video-studio 生成逐帧旁白，并产出与音频对齐的 scenes.json。

设计要点：音频驱动帧长 —— 先合成语音、测出真实时长，再反推每帧该停留多久，
而不是让画面硬套固定秒数。这样语速保持自然，画面也不会出现大段干等。

用法：
    python3 gen.py                                   # 默认云希男声、语速 +6%
    VOICE=zh-CN-XiaoxiaoNeural python3 gen.py        # 换晓晓女声
    RATE=+0% TAIL=1.2 python3 gen.py                 # 原速、念完多停留 1.2s
"""
import asyncio
import json
import os
import re
import subprocess
from pathlib import Path

import edge_tts

HERE = Path(__file__).parent
DEMO = HERE.parent

FFMPEG = os.environ.get(
    "FFMPEG_BIN", "/Users/songzhigui/.workbuddy/binaries/node/workspace/bin/ffmpeg"
)
# 常用中文音色：
#   zh-CN-YunxiNeural     云希 · 男声，温和自然（默认，知识区常用）
#   zh-CN-XiaoxiaoNeural  晓晓 · 女声，温柔
#   zh-CN-YunyangNeural   云扬 · 男声，新闻播报腔，正式感强
#   zh-CN-YunjianNeural   云健 · 男声，纪录片叙事感
VOICE = os.environ.get("VOICE", "zh-CN-YunxiNeural")
RATE = os.environ.get("RATE", "+6%")
PROXY = os.environ.get("PROXY") or None   # 需要时：http://127.0.0.1:7897
TAIL = float(os.environ.get("TAIL", "0.9"))        # 念完之后的画面停留
MIN_SEC = float(os.environ.get("MIN_SEC", "3.5"))  # 单帧最短时长，防抖
FRAMES = Path(os.environ.get("FRAMES_DIR", str(DEMO / "frames-pension")))
NARRATION = HERE / os.environ.get("NARRATION", "narration.json")


def duration(path: Path) -> float:
    """用 ffmpeg 解析音频时长（这个构建没带 ffprobe）。"""
    proc = subprocess.run(
        [FFMPEG, "-i", str(path)], capture_output=True, text=True
    )
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", proc.stderr)
    if not m:
        raise RuntimeError(f"无法解析时长: {path}\n{proc.stderr[-500:]}")
    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mi * 60 + s


async def synth(text: str, out: Path, retries: int = 3) -> None:
    """微软接口偶发 NoAudioReceived，指数退避重试，避免整批失败。"""
    for attempt in range(1, retries + 1):
        try:
            comm = edge_tts.Communicate(
                text, VOICE, rate=RATE, proxy=PROXY,
                connect_timeout=10, receive_timeout=60,
            )
            await comm.save(str(out))
            return
        except Exception as exc:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"    第 {attempt} 次失败（{type(exc).__name__}），{wait}s 后重试")
            await asyncio.sleep(wait)


async def main() -> None:
    items = json.loads(NARRATION.read_text(encoding="utf-8"))
    voice_dir = FRAMES / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)

    scenes = []
    for idx, item in enumerate(items, start=1):
        mp3 = voice_dir / f"p{idx}.mp3"
        await synth(item["text"], mp3)

        dur = duration(mp3)
        seconds = round(max(dur + TAIL, MIN_SEC), 2)
        print(f"p{idx}  语音 {dur:5.2f}s  ->  帧长 {seconds:5.2f}s   {item['text'][:18]}...")
        scenes.append(
            {
                "file": item["file"],
                "seconds": seconds,
                "audio": f"voice/p{idx}.mp3",
            }
        )

    total = sum(s["seconds"] for s in scenes)
    out = FRAMES / "scenes.json"
    out.write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n总时长 {total:.1f}s  ->  {out}")


asyncio.run(main())
