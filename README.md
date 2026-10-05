# html-video-studio

程序化视频（programmatic video）实验工作空间：不调用视频生成模型，
用「HTML 页面 → headless Chromium 录制 → ffmpeg 编码」在本地出 MP4。

## 目录

```
html-video-studio/
├── demo/                  我实际跑通的最小链路
│   ├── frames/            3 个自包含 HTML 帧（纯 CSS 动画，无 CDN 依赖）
│   ├── render.mjs         Chromium 录制 → webm → ffmpeg → mp4 → concat
│   ├── out/demo.mp4       产物：13.1s / 1920x1080 / 30fps / H.264 / 485KB
│   └── README.md          demo 的使用与排障
└── html-video/            上游项目 nexu-io/html-video 的 clone（21 个官方模板，不入库）
```

## 上游项目

`html-video/` 是[上游项目](https://github.com/nexu-io/html-video)的独立 clone，
**不纳入本仓库**（它是另一个 git 仓库，且带 457MB node_modules）。
用到官方模板时再拉：

```bash
git clone --depth 1 https://github.com/nexu-io/html-video.git
cd html-video && pnpm install
```

只有 `demo/` 这条最小链路是完全自包含的，不依赖上游。

## 快速开始

```bash
cd demo

# 依赖（已装在工作区外的隔离目录，node_modules 是指向它的软链）
# 若换机器：npm install playwright && npx playwright install chromium

export FFMPEG_BIN=/Users/songzhigui/.workbuddy/binaries/node/workspace/bin/ffmpeg
node render.mjs          # 约 17 秒，产出 out/demo.mp4
```

所有可调项都走环境变量（详见 `demo/README.md`）：

```bash
WIDTH=1280 HEIGHT=720 node render.mjs                            # 限制输出分辨率
BGM=./assets/bgm-loop.mp3 BGM_VOLUME=0.35 node render.mjs        # 挂背景音乐（自动循环 + 首尾淡变）
CRF=23 FPS=24 OUT_NAME=v2.mp4 node render.mjs                    # 画质 / 帧率 / 文件名
```

改文案 → 编辑 `frames/*.html` → 重跑，就是这套方案的核心体验：
**改一句话，重渲一版，结果完全可复现。**

## 为什么是这条路

2026 年 AI 视频已经分成两个成熟范式，本工作空间站在右边这一支：

| | 生成式扩散模型 | 程序化渲染（本仓库） |
|---|---|---|
| 代表 | Veo 3.1 · Seedance 2.5 · Kling 3.0 | Remotion · html-video · PPTX→MP4 |
| 画面 | 电影感、原生音频 | 由代码决定 |
| 可复现 | 否，每次抽样不同 | 是，同样输入同一输出 |
| 成本 | 按次计费，要 GPU | 笔记本 CPU，19 秒出 13 秒 1080p |
| 适合 | 品牌片、氛围空镜 | 讲解、汇报、课程、产品演示 |

当下的主流做法是**合流**：主体页面走确定性渲染，只有需要电影感空镜时才调生成模型。
这也是 `OpenMontage`(62.9k★)、`claude-code-video-toolkit`(2.1k★) 这类 agentic 项目在做的事。

一个佐证信号：OpenAI 已于 2026-04-26 停掉 Sora 消费端、2026-09-24 关闭 Videos API
与全部 Sora 2 模型，官方 deprecations 页的"推荐替代"一栏是空的。

## 环境备忘

- Node v22.22.2；ffmpeg 4.4 在 `~/.workbuddy/binaries/node/workspace/bin/ffmpeg`（支持 libx264 + aac）
- Playwright 浏览器在 `~/Library/Caches/ms-playwright/`（chromium-1243 + headless-shell + ffmpeg-1011）
- `demo/node_modules` 是指向隔离 workspace 的软链；ESM 的 `import "playwright"` 不认 NODE_PATH，靠它解析
- 完整 `pnpm install` html-video 会拉 remotion 的大二进制，走 Hyperframes 路线其实不需要它——
  只装 `@html-video/adapter-hyperframes` 即可（仅依赖 core + playwright）

## 下一步可以做

1. 接 `presenton`（开源 Gamma 替代，10.9k★）生成 PPTX → 走本链路渲染，完成「话题 → AI 出页面 → 本地出片」
2. 试 html-video 官方模板：把 `render.mjs` 里 `scenes` 指向 `html-video/templates/<模板名>/source/index.html`
3. 完整安装 html-video（CLI + studio 网页界面 + agent 接入），用它的 21 个模板和 content-graph 多帧编排
