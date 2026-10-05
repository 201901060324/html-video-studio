# html-video 本地渲染 demo

主题：不靠视频 AI，用「HTML 页面 → 逐帧录制 → MP4」的程序化渲染出片。

> **完整方法论沉淀在 skill 里**：`~/.workbuddy/skills/html-video-studio/SKILL.md`
> 含帧模板、布局避坑、配音集成、TTS 选型、AI 合规标注、质检流程。
> 本文件是工作区内的操作手册，只讲「怎么跑」。

## 目录

```
demo/
├── frames/                 原始最小链路的 3 帧（保留作参考）
├── frames-pension/         实战主题：养老分析（8 帧 1920x1080）
│   ├── p1-cover.html … p8-outro.html
│   ├── scenes.json         场景清单（由 tts/gen.py 生成，含 audio 字段）
│   └── voice/p1.mp3 …      逐帧旁白
├── tts/
│   ├── narration.json      旁白文案（改文案只动这里）
│   └── gen.py              合成语音 + 测时长 + 生成对齐的 scenes.json
├── assets/
│   └── bgm-loop.mp3        测试用背景音乐（ffmpeg 合成的 8s 和声，非真实音乐）
├── render.mjs              HTML → MP4（record 实时录制 / seek 逐帧两种模式，带分片缓存+并行）
├── shot.mjs                抽帧验布局：不渲染，只把每帧截成 PNG 给你看
├── out/                    最小链路产物
├── out-pension/            实战主题产物
└── README.md               本文件
```

## 流水线（与 html-video / Hyperframes 引擎一致）

```
HTML 帧 → headless Chromium 录制 → webm → ffmpeg libx264 → mp4 → concat
                                                    ↓
                                          旁白 adelay 铺轨 + amix
```

**注意 headless Chromium 只录画面不录声音**，所以音频必须在 ffmpeg 阶段加，
不要指望在 HTML 里放 `<audio autoplay>`。

`render.mjs` 最小实现：每个场景开一个带 `recordVideo` 的 Playwright context，
加载 HTML、等动画跑完、关闭 context 落 webm，再用 ffmpeg 转 mp4（裁到精确时长、
统一分辨率/yuv420p/30fps），最后 concat。多主题通过环境变量切换，不改源码。

### 两种渲染模式 + 分片缓存（2026-10-05）

- `MODE=record`（默认）：上面的实时录制链路。
- `MODE=seek`：逐帧拨动画时间轴 + 截图 → `image2pipe` 直接喂 ffmpeg。
  帧数精确（78.0 → 78.07，record 会短 0.5s）、同输入同输出、码率更干净；
  代价是比 record 慢一点（36s vs 31s，8 帧 78s 基准）。
- **分片缓存**：帧 HTML + 渲染参数算 sha1 存 `out/clipN.meta.json`，没变就跳过。
  改一帧只重渲那一帧。
- `JOBS`（默认 4）并行渲染片段。

实测（frames-pension 8 帧 / 78s / 1080p30 / M4）：
首渲 98s → **31s**；改 1 帧 → **16s**；无改动重跑 → **4s**。
`FORCE=1` 强制全量，`CACHE=0` 关缓存。**`OUT_DIR` 同时是缓存目录，同主题别换。**

## 渲染

### 基础（默认 3 帧）

```bash
cd /Users/songzhigui/WorkBuddy/html-video-studio/demo
export FFMPEG_BIN=/Users/songzhigui/.workbuddy/binaries/node/workspace/bin/ffmpeg
node render.mjs                      # 默认 1920x1080 静音，约 17 秒出片
```

### 多主题（实战用法）

```bash
FRAMES_DIR=frames-pension \
SCENES_FILE=frames-pension/scenes.json \
OUT_DIR=out-pension OUT_NAME=pension-voiced.mp4 \
node render.mjs
```

| 变量 | 含义 | 默认 |
|---|---|---|
| `FRAMES_DIR` | 帧目录 | `frames` |
| `SCENES` | `"a.html:5,b.html:4"` 逗号分隔 | 空 |
| `SCENES_FILE` | 场景清单 json `[{file,seconds,audio}]` | 空 |
| `OUT_DIR` | 产物目录（多主题时分开，避免覆盖） | `out` |
| `CANVAS_W` / `CANVAS_H` | **录制画布**，必须等于 `frames/*.html` 里写死的 px | 1920 / 1080 |
| `WIDTH` / `HEIGHT` | **输出分辨率**，ffmpeg 缩放目标 | 等于画布 |
| `FIT` | `cover` 居中裁切铺满 / `contain` 补黑边 | cover |
| `FPS` | 帧率 | 30 |
| `CRF` | 画质，越大越小越糊 | 20 |
| `BGM` | 音频文件路径（mp3/wav/m4a/aac 均可） | 空 = 静音 |
| `BGM_VOLUME` | 音量 0~1 | 0.6 |
| `BGM_FADE_IN` / `BGM_FADE_OUT` | 淡入/淡出秒数 | 1.5 / 2 |
| `OUT_NAME` | 产物文件名 | demo.mp4 |

限制输出分辨率：

```bash
WIDTH=1280 HEIGHT=720 node render.mjs                  # 720p
WIDTH=1080 HEIGHT=1080 FIT=cover node render.mjs       # 方图 1:1
WIDTH=900 HEIGHT=1600 node render.mjs                  # 竖版 9:16（靠 cover 从 16:9 裁出来）
```

## 配音（edge-tts）

已实现**音频驱动帧长**：先合成语音、测出真实时长，再反推每帧停留秒数，
而不是让画面硬套固定秒数（语速自然，画面不干等）。

```bash
# 1) 改文案：demo/tts/narration.json  [{ "file": "p1.html", "text": "..." }]
# 2) 合成语音 + 生成对齐后的 scenes.json
python3 tts/gen.py
# 3) 渲染（scenes.json 的 audio 字段会被自动铺进音轨）
node render.mjs          # 同上面的多主题命令
```

可覆盖的环境变量：`VOICE`（默认 `zh-CN-YunxiNeural`）、`RATE`（默认 `+6%`，
实战用 `+10%`）、`TAIL`（念完停留秒数，默认 0.9）、`MIN_SEC`（单帧最短，默认 3.5）、
`PROXY`（需要时 `http://127.0.0.1:7897`）、`FRAMES_DIR`、`NARRATION`。

常用中文音色：`zh-CN-YunxiNeural`（云希·温和男声）、`zh-CN-XiaoxiaoNeural`（晓晓·女声）、
`zh-CN-YunyangNeural`（云扬·新闻播报）、`zh-CN-YunjianNeural`（云健·纪录片叙事）。

依赖：`pip install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple`
（清华镜像实测比 pypi 直连快 6 倍）。微软接口偶发 `NoAudioReceived`，gen.py 已内建重试。

## AI 合规角标（2026 新规要求）

面向 B站/短视频平台发布时，画面内需有显式标注。现有 8 帧统一带
`.aibadge`（右上角常驻「本视频含 AI 生成内容」半透明黑底白字），
放在 `.stage` 内、`.wrap` 之外，避免被 flex 布局与入场动画影响。

**注意**：各帧 `padding-top` 均 ≥96px，角标取 `top:44px` 落在安全区，不压正文。
发布页还需勾选「该视频使用人工智能合成技术」，政策财经类另加免责声明。详见 skill。

## 布局避坑（实战踩过）

- **底部横幅不要用 `position:absolute; bottom`**。上方内容实际高度（含换行）一旦超出估算就会叠上去。
  正确做法：`.wrap` 用 `display:flex; flex-direction:column; padding-bottom:<给 foot 留的空间>`，
  底部横幅改流内 `margin-top:auto` 贴底，tag 加 `align-self:flex-start`，并预留 ≥30px 余量防换行。
- **改完布局必须先抽帧看图**再全量渲染：

```bash
node --input-type=module -e "
import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
await p.goto('file:///abs/path/frames-pension/p3-korea.html');
await p.waitForTimeout(2400);
await p.screenshot({ path: '/tmp/check.png' });
await b.close();
"
```

然后用 Read 工具看图确认。不要只信代码里的高度估算。

## 其他已知坑

- **headless Chromium 不录声音**，音频只能在 ffmpeg 阶段加。
- **宽高必须是偶数**（H.264/yuv420p），脚本已兜底 `scale=trunc(iw/2)*2`。
- `recordVideo.size` 与 `viewport` 必须完全相等，否则黑边。
- 窄一下能降体积，拉高没用：画布 1920x1080 时 `WIDTH=2560` 只会插值放大。
  真要 4K 得把 `frames/*.html` 的 px 和 `CANVAS_*` 一起改成 3840x2160。
- render.mjs 里 JS 常量必须先定义后使用（`RESOLVE` 曾因顺序报 TDZ 错误）。
- 改 `scenes.json` 结构后检查 `loadScenes()` 的字段映射（曾把 `audio` 字段丢掉）。
- 渲染耗时 ≈ 视频时长的 1.2–1.3 倍（M4 CPU，无 GPU），**必须 `run_in_background=true`**。

## 环境

- ffmpeg 4.4：`/Users/songzhigui/.workbuddy/binaries/node/workspace/bin/ffmpeg`
  （已验证 `--enable-libx264 --enable-libmp3lame`，aac 走内置原生编码器）
- Node v22.22.2（managed：`/Users/songzhigui/.workbuddy/binaries/node/versions/22.22.2-3/bin/node`）
- Playwright + Chromium 1243 在 `~/Library/Caches/ms-playwright/`
- `demo/node_modules` 是指向 `~/.workbuddy/binaries/node/workspace/node_modules` 的软链；
  ESM 的 `import "playwright"` 不认 NODE_PATH，靠它解析
- Python venv：`/Users/songzhigui/.workbuddy/binaries/python/envs/default/bin/python`

## 产物

| 文件 | 规格 |
|---|---|
| `out/demo.mp4` | 1920x1080 / 30fps / 13.7s / 286 kb/s，静音 |
| `out-pension/pension-analysis.mp4` | 1920x1080 / 30fps / 42.0s，静音版（8 帧） |
| `out-pension/pension-voiced.mp4` | 1920x1080 / 30fps / 77.6s，**中文旁白 + AI 角标**，发布用 |

## 改内容

帧就是普通 HTML + CSS 动画。改文案 → 编辑 `frames-<主题>/*.html` → 重跑 `node render.mjs`。
这就是这套方案的核心：**改一句话，重渲一版，结果完全可复现。**

想临时加背景音乐（视频比音乐短会自动循环 + 首尾淡变）：

```bash
BGM=./assets/bgm-loop.mp3 node render.mjs
$FFMPEG_BIN -y -f lavfi -i "sine=f=196:d=8" -f lavfi -i "sine=f=261.63:d=8" \
  -f lavfi -i "sine=f=329.63:d=8" \
  -filter_complex "[0:a][1:a][2:a]amix=inputs=3:normalize=0,volume=0.28,\
afade=t=in:st=0:d=0.6,afade=t=out:st=7.2:d=0.8" \
  -c:a libmp3lame -q:a 4 assets/bgm-loop.mp3
```

⚠️ 商用请注意版权，`assets/bgm-loop.mp3` 只是 ffmpeg 合成的纯正弦音，用来验链路的。
