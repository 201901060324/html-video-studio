// 3D 帧专用截图：带 WebGL 硬件加速参数，等THREE_READY 再截。
//   FRAMES_DIR=frames-3d-test SCENES_FILE=frames-3d-test/scenes.json node shot3d.mjs
import { chromium } from "playwright";
import { mkdirSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RESOLVE = (p) => (path.isAbsolute(p) ? p : path.join(HERE, p));

const FRAMES = RESOLVE(process.env.FRAMES_DIR || "frames-3d-test");
const OUT = process.env.OUT_DIR || "/tmp/hvs-3d-shots";
const AT = process.env.AT || "3.2";
const JOBS = Math.max(1, Number(process.env.JOBS || 3));
const W = Number(process.env.WIDTH || 1920);
const H = Number(process.env.HEIGHT || 1080);

const GL_ARGS = [
  "--use-gl=angle",
  "--use-angle=metal",
  "--enable-unsafe-swiftshader",
  "--enable-webgl",
  "--ignore-gpu-blocklist",
];

let files = readdirSync(FRAMES).filter((f) => f.endsWith(".html")).sort();
if (process.env.SCENES_FILE) {
  const raw = JSON.parse(readFileSync(RESOLVE(process.env.SCENES_FILE), "utf8"));
  files = raw.map((x) => x.file);
}
if (process.env.ONLY) files = files.filter((f) => f === process.env.ONLY);

mkdirSync(OUT, { recursive: true });

let idx = 0;
const queue = files.slice();
const workers = Array.from({ length: Math.min(JOBS, queue.length) }, async () => {
  const browser = await chromium.launch({ args: GL_ARGS });
  while (queue.length) {
    const f = queue.shift();
    const page = await browser.newPage({ viewport: { width: W, height: H } });
    const errs = [];
    page.on("pageerror", (e) => errs.push(String(e).slice(0, 200)));
    page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
    const PORT = process.env.PORT || "8931";
    // HTTP 服务的根目录即SERVE_ROOT（默认 demo/），路径必须相对它
    const ROOT = process.env.SERVE_ROOT || HERE;
    const rel = path.relative(ROOT, path.join(FRAMES, f));
    const url = "http://127.0.0.1:" + PORT + "/" + rel.split(path.sep).join("/");
    await page.goto(url);
    try {
      await page.waitForFunction("window.__THREE_READY === true", { timeout: 25000 });
    } catch {
      console.log("  " + f + "  three未就绪");
    }
    if (process.env.AT !== "end") {
      await page.evaluate((sec) => window.__hf_seek && window.__hf_seek(sec), Number(AT));
    }
    await page.waitForTimeout(700);
    const out = path.join(OUT, f.replace(".html", ".png"));
    await page.screenshot({ path: out });
    console.log("  " + path.basename(out) + (errs.length ? "  ⚠ " + errs[0] : ""));
    await page.close();
  }
  await browser.close();
});
await Promise.all(workers);
console.log("DONE -> " + OUT);
