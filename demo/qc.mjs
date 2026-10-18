// 逐帧质检：把每帧拨到指定时刻截图
// 用法：node qc.mjs [比例] [帧名过滤]
import { chromium } from "playwright";
import { mkdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FRAMES = path.join(HERE, "frames-dsv41");
const OUT = "/tmp/qc-dsv41";
const RATIO = Number(process.argv[2] || 0.92);
const FILTER = process.argv[3] || "";
const scenes = JSON.parse(readFileSync(path.join(FRAMES, "scenes.json"), "utf8"));
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ args: ["--force-device-scale-factor=1", "--hide-scrollbars"] });
const jobs = [];
for (const s of scenes) {
  if (FILTER && !s.file.includes(FILTER)) continue;
  jobs.push({ file: s.file, t: +(s.seconds * RATIO).toFixed(2) });
  if (!FILTER) jobs.push({ file: s.file, t: 0.05 });
}
let cur = 0;
const shots = [];
async function worker() {
  for (;;) {
    const i = cur++;
    if (i >= jobs.length) return;
    const j = jobs[i];
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    await page.goto("file://" + path.join(FRAMES, j.file) + "#t=" + j.t, { waitUntil: "load" });
    await page.evaluate(() => (document.fonts ? document.fonts.ready : Promise.resolve()));
    await page.waitForTimeout(220);
    const name = j.file.replace(".html", "") + "_t" + j.t + ".png";
    await page.screenshot({ path: path.join(OUT, name), type: "png" });
    shots.push(name);
    await ctx.close();
  }
}
await Promise.all([0, 1, 2, 3].map(() => worker()));
await browser.close();
console.log(shots.length + " -> " + OUT);
