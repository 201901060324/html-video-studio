import { chromium } from "playwright";
import { mkdirSync, existsSync, readdirSync, rmSync, writeFileSync, readFileSync } from "node:fs";
import { execFileSync, spawn } from "node:child_process";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RESOLVE = (p) => (path.isAbsolute(p) ? p : path.join(HERE, p));
const FRAMES = RESOLVE(process.env.FRAMES_DIR || "frames");
const OUT = RESOLVE(process.env.OUT_DIR || "out");
const CLIPS = path.join(OUT, "clips");

// ─────────────────────────────────────────────────────────────────────────────
// 可调旋钮（全部走环境变量，不传则用默认值）
//
//   渲染模式（新增 2026-10-05）
//     MODE                   record(默认, Playwright 实时录制 webm)
//                            seek(逐帧 seek + 截图 → image2pipe，帧数精确、可复现)
//     JOBS                   并行渲染的片段数，默认 4。1 = 串行（旧行为）
//     CACHE                  0 关闭分片缓存，默认开启
//     FORCE                  1 强制全量重渲（忽略缓存）
//     SEEK_JPEG_Q            seek 模式中间帧质量，默认 95（SEEK_FORMAT=jpeg 时生效）
//     SEEK_FORMAT            seek 模式中间帧格式，jpeg(默认) | png(无损但更慢)
//
//   录制画布（HTML 实际渲染尺寸，必须与 frames/*.html 里写的 px 一致）
//     CANVAS_W / CANVAS_H    默认 1920 / 1080
//
//   输出分辨率（ffmpeg 缩放目标，≤ 画布尺寸时不损失清晰度）
//     WIDTH / HEIGHT         默认等于画布尺寸
//     FIT                    cover(默认, 居中裁切铺满) | contain(补黑边留空)
//
//   多主题
//     FRAMES_DIR           帧目录，默认 ./frames
//     SCENES               "帧1.html:秒数,帧2.html:秒数"（逗号分隔）
//     SCENES_FILE          场景清单 json：[{ "file": "x.html", "seconds": 5 }, ...]
//
//   编码
//     FPS                    默认 30
//     CRF                    默认 20，越大越小、越糊
//
//   背景音乐
//     BGM                    音频文件路径（mp3/wav/m4a/aac 均可）
//     BGM_VOLUME             0~1，默认 0.6
//     BGM_FADE_IN            淡入秒数，默认 1.5
//     BGM_FADE_OUT           淡出秒数，默认 2
//     OUT_NAME               产物文件名，默认 demo.mp4
// ─────────────────────────────────────────────────────────────────────────────

const num = (key, dflt) => (process.env[key] ? Number(process.env[key]) : dflt);
const even = (n) => Math.max(2, Math.floor(n / 2) * 2);

const MODE = (process.env.MODE || "record").toLowerCase();
if (MODE !== "record" && MODE !== "seek") throw new Error("MODE 只支持 record | seek，收到: " + MODE);
const JOBS = Math.max(1, Math.floor(num("JOBS", 4)));
const CACHE_ON = process.env.CACHE !== "0";
const FORCE = process.env.FORCE === "1";
const SEEK_JPEG_Q = Math.min(100, Math.max(50, Math.floor(num("SEEK_JPEG_Q", 95))));
const SEEK_FORMAT = (process.env.SEEK_FORMAT || "jpeg").toLowerCase();
if (SEEK_FORMAT !== "jpeg" && SEEK_FORMAT !== "png") throw new Error("SEEK_FORMAT 只支持 jpeg | png");

const CANVAS_W = even(num("CANVAS_W", 1920));
const CANVAS_H = even(num("CANVAS_H", 1080));
const WIDTH = even(num("WIDTH", CANVAS_W));
const HEIGHT = even(num("HEIGHT", CANVAS_H));
const FPS = num("FPS", 30);
const CRF = num("CRF", 20);
const FIT = (process.env.FIT || "cover").toLowerCase();

const BGM = process.env.BGM || "";
const BGM_VOLUME = process.env.BGM_VOLUME || "0.6";
const BGM_FADE_IN = process.env.BGM_FADE_IN || "1.5";
const BGM_FADE_OUT = process.env.BGM_FADE_OUT || "2";
const OUT_NAME = process.env.OUT_NAME || "demo.mp4";

const DEFAULT_SCENES = [
  { file: "frame1-title.html", seconds: 4.6 },
  { file: "frame2-points.html", seconds: 4.6 },
  { file: "frame3-outro.html", seconds: 4.6 },
];

function loadScenes() {
  if (process.env.SCENES_FILE) {
    const raw = JSON.parse(readFileSync(RESOLVE(process.env.SCENES_FILE), "utf8"));
    if (!Array.isArray(raw) || raw.length === 0) throw new Error("SCENES_FILE 必须是非空数组");
    return raw.map((s) => ({
      file: s.file,
      seconds: Number(s.seconds),
      audio: s.audio || "",
    }));
  }
  if (process.env.SCENES) {
    return process.env.SCENES.split(",").map((chunk) => {
      const bits = chunk.split(":");
      if (bits.length !== 2) throw new Error("SCENES 格式应为 文件名:秒数,文件名:秒数 —— 收到: " + chunk);
      return { file: bits[0].trim(), seconds: Number(bits[1]) };
    });
  }
  return DEFAULT_SCENES;
}

const scenes = loadScenes();

const ffmpeg = process.env.FFMPEG_BIN || "ffmpeg";
const TOTAL = scenes.reduce((s, x) => s + x.seconds, 0);

if (existsSync(CLIPS)) rmSync(CLIPS, { recursive: true, force: true });
mkdirSync(CLIPS, { recursive: true });
mkdirSync(OUT, { recursive: true });

// 分辨率变换：先按 FIT 策略缩放到目标框内，再补齐到精确尺寸，最后兜底偶数化
// （H.264 + yuv420p 要求宽高均为偶数，否则会报 width not divisible by 2）
// 注意：数组里每个元素是一条完整滤镜，末尾不要带逗号，统一靠 join(",") 拼接
const geom = WIDTH + ":" + HEIGHT;
const vfParts = [
  "scale=" + geom + ":force_original_aspect_ratio=" +
    (FIT === "contain" ? "decrease" : "increase"),
  FIT === "contain"
    ? "pad=" + geom + ":(ow-iw)/2:(oh-ih)/2:color=black"
    : "crop=" + geom,
  "scale=trunc(iw/2)*2:trunc(ih/2)*2",
];
const vf = vfParts.join(",");

// ── 分片缓存：帧内容 + 渲染参数一起算指纹，没变就直接复用上次的 clipN.mp4 ──
function signature(scene) {
  const h = createHash("sha1");
  h.update(readFileSync(path.join(FRAMES, scene.file)));
  h.update(JSON.stringify({
    seconds: scene.seconds, MODE, CANVAS_W, CANVAS_H, WIDTH, HEIGHT, FPS, CRF, FIT,
  }));
  return h.digest("hex").slice(0, 12);
}

const clipPath = (i) => path.join(OUT, "clip" + (i + 1) + ".mp4");
const metaPath = (i) => path.join(OUT, "clip" + (i + 1) + ".meta.json");

function cached(i, scene) {
  if (!CACHE_ON || FORCE) return false;
  if (!existsSync(clipPath(i)) || !existsSync(metaPath(i))) return false;
  try {
    return JSON.parse(readFileSync(metaPath(i), "utf8")).sig === signature(scene);
  } catch {
    return false;
  }
}

// ── 把动画时间轴拨到 t 秒（seek 模式的核心） ──────────────────────────────
// 优先级：页面自己暴露的 __hf_seek(秒) > Web Animations API > video/audio 元素。
// CSS animation / transition 都能被 document.getAnimations() 抓到并暂停定位。
function seekScript(tSec) {
  const t = tSec * 1000;
  if (typeof window.__hf_seek === "function") {
    try { window.__hf_seek(tSec); } catch (e) {}
  }
  if (!window.__anims) {
    window.__anims = typeof document.getAnimations === "function" ? document.getAnimations() : [];
  }
  const anims = window.__anims;
  for (let i = 0; i < anims.length; i++) {
    const a = anims[i];
    try {
      if (a.playState !== "paused") a.pause();
      a.currentTime = t;
    } catch (e) {}
  }
  const media = document.querySelectorAll("video, audio");
  for (let i = 0; i < media.length; i++) {
    const el = media[i];
    try {
      el.pause();
      if (isFinite(el.duration)) el.currentTime = Math.min(tSec, el.duration);
    } catch (e) {}
  }
}

function spawnFfmpeg(args) {
  const ff = spawn(ffmpeg, args, { stdio: ["pipe", "inherit", "inherit"] });
  let pipeErr = null;
  // 每帧都挂一次 error 监听会把 EventEmitter 顶到告警阈值，只挂一次记下来
  ff.stdin.on("error", (e) => { pipeErr = e; });
  const finished = new Promise((res, rej) => {
    ff.on("error", rej);
    ff.on("close", (code) => (code === 0 ? res() : rej(new Error("ffmpeg 退出码 " + code))));
  });
  return {
    ff,
    finished,
    write(buf) {
      return new Promise((res, rej) => {
        if (pipeErr) return rej(pipeErr);
        if (ff.stdin.write(buf)) return res();
        ff.stdin.once("drain", () => (pipeErr ? rej(pipeErr) : res()));
      });
    },
    end() {
      ff.stdin.end();
      return finished;
    },
  };
}

console.log("模式 " + MODE + "  并行 " + JOBS + "  缓存 " + (CACHE_ON && !FORCE ? "开" : "关"));
console.log("画布 " + CANVAS_W + "x" + CANVAS_H + "  ->  输出 " + WIDTH + "x" + HEIGHT +
  "  " + FPS + "fps  crf=" + CRF + "  fit=" + FIT +
  (BGM ? "  bgm=" + path.basename(BGM) : "  bgm=无") + "\n");

const browser = await chromium.launch({
  args: ["--force-device-scale-factor=1", "--hide-scrollbars"],
});

async function renderScene(i, scene) {
  const target = path.join(FRAMES, scene.file);
  const mp4 = clipPath(i);

  if (cached(i, scene)) {
    console.log("clip" + (i + 1) + ".mp4  缓存命中，跳过 <- " + scene.file);
    return;
  }

  if (MODE === "record") {
    const clipDir = path.join(CLIPS, "s" + (i + 1));
    mkdirSync(clipDir, { recursive: true });
    // viewport 与 recordVideo.size 必须完全相等，否则录出来自带黑边
    const context = await browser.newContext({
      viewport: { width: CANVAS_W, height: CANVAS_H },
      deviceScaleFactor: 1,
      recordVideo: { dir: clipDir, size: { width: CANVAS_W, height: CANVAS_H } },
    });
    const page = await context.newPage();
    await page.goto("file://" + target, { waitUntil: "load" });
    await page.waitForTimeout(Math.round(scene.seconds * 1000));
    await context.close();

    const webm = readdirSync(clipDir).find((f) => f.endsWith(".webm"));
    if (!webm) throw new Error("no webm recorded for " + scene.file);

    const args = [
      "-y", "-i", path.join(clipDir, webm),
      "-t", String(scene.seconds),
      "-an",                                 // headless Chromium 不录音频，这里必然是纯视频
      "-c:v", "libx264", "-preset", "veryfast", "-crf", String(CRF),
      "-pix_fmt", "yuv420p", "-r", String(FPS),
    ];
    if (vf) args.push("-vf", vf);
    args.push(mp4);
    execFileSync(ffmpeg, args, { stdio: "inherit" });
  } else {
    // seek 模式：逐帧定位 → 截图 → 直接喂给 ffmpeg，帧数精确，不受 CPU 抖动影响
    const context = await browser.newContext({
      viewport: { width: CANVAS_W, height: CANVAS_H },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    await page.goto("file://" + target, { waitUntil: "load" });
    await page.evaluate(() => (document.fonts ? document.fonts.ready : Promise.resolve()));
    await page.waitForTimeout(200);

    const frames = Math.max(1, Math.round(scene.seconds * FPS));
    const args = [
      "-y", "-f", "image2pipe", "-framerate", String(FPS),
      "-c:v", SEEK_FORMAT === "png" ? "png" : "mjpeg", "-i", "-",
      "-an",
      "-c:v", "libx264", "-preset", "veryfast", "-crf", String(CRF),
      "-pix_fmt", "yuv420p", "-r", String(FPS),
    ];
    if (vf) args.push("-vf", vf);
    args.push(mp4);
    const sink = spawnFfmpeg(args);

    for (let f = 0; f < frames; f++) {
      await page.evaluate(seekScript, f / FPS);
      const buf = await page.screenshot(
        SEEK_FORMAT === "png" ? { type: "png" } : { type: "jpeg", quality: SEEK_JPEG_Q }
      );
      await sink.write(buf);
    }
    await context.close();
    await sink.end();
  }

  writeFileSync(metaPath(i), JSON.stringify({ sig: signature(scene), file: scene.file, seconds: scene.seconds, mode: MODE }));
  console.log("clip" + (i + 1) + ".mp4  <- " + scene.file);
}

// 简单并发池：一次最多放 JOBS 个片段出去，谁先空谁补位
async function pool(items, limit, fn) {
  let cursor = 0;
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    for (;;) {
      const i = cursor++;
      if (i >= items.length) return;
      await fn(i, items[i]);
    }
  });
  await Promise.all(workers);
}

await pool(scenes, JOBS, renderScene);

await browser.close();

const listFile = path.join(OUT, "concat.txt");
writeFileSync(
  listFile,
  scenes.map((_, i) => "file '" + clipPath(i) + "'").join("\n")
);

// ── 音轨：把每帧旁白按累计起点铺进时间轴，BGM 可再叠加进来 ────────────────
const mixInputs = [];
const mixFilters = [];
const mixLabels = [];
let inIdx = 1;      // 0 号输入是 concat 出来的总视频
let cursor = 0;     // 当前场景起始秒数

scenes.forEach((s, i) => {
  if (s.audio) {
    const p = path.isAbsolute(s.audio) ? s.audio : path.join(FRAMES, s.audio);
    if (!existsSync(p)) throw new Error("音频文件不存在: " + p);
    mixInputs.push("-i", p);
    const lbl = "n" + (i + 1);
    const ms = Math.round(cursor * 1000);
    mixFilters.push("[" + inIdx + ":a]adelay=" + ms + "|" + ms + "[" + lbl + "]");
    mixLabels.push("[" + lbl + "]");
    inIdx++;
  }
  cursor += s.seconds;
});

if (BGM) {
  if (!existsSync(BGM)) throw new Error("BGM 文件不存在: " + BGM);
  const fadeOutStart = Math.max(0, TOTAL - Number(BGM_FADE_OUT)).toFixed(2);
  mixInputs.push("-stream_loop", "-1", "-i", BGM);   // 音乐比视频短就循环
  mixFilters.push(
    "[" + inIdx + ":a]volume=" + BGM_VOLUME +
    ",afade=t=in:st=0:d=" + BGM_FADE_IN +
    ",afade=t=out:st=" + fadeOutStart + ":d=" + BGM_FADE_OUT + "[bgm]"
  );
  mixLabels.push("[bgm]");
  inIdx++;
}

const final = path.join(OUT, OUT_NAME);
const args = ["-y", "-f", "concat", "-safe", "0", "-i", listFile, ...mixInputs];

if (mixLabels.length) {
  mixFilters.push(
    mixLabels.join("") + "amix=inputs=" + mixLabels.length +
    ":normalize=0:dropout_transition=0[mix]"
  );
  args.push("-filter_complex", mixFilters.join(";"));
  args.push("-map", "0:v:0", "-map", "[mix]");
  args.push("-c:a", "aac", "-b:a", "192k");
  if (BGM) args.push("-shortest");   // BGM 无限循环时靠它收尾
} else {
  args.push("-map", "0:v:0");
}

args.push(
  "-c:v", "libx264", "-preset", "veryfast", "-crf", String(CRF),
  "-pix_fmt", "yuv420p", "-movflags", "+faststart",
  final,
);

execFileSync(ffmpeg, args, { stdio: "inherit" });

const narrCount = scenes.filter((s) => s.audio).length;
console.log("\nDONE -> " + final);
console.log(WIDTH + "x" + HEIGHT + "  " + TOTAL.toFixed(1) + "s  " + FPS + "fps  " +
  (narrCount ? "旁白 " + narrCount + " 段" : "无旁白") +
  (BGM ? " + 音乐" : ""));
