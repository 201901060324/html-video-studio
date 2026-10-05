// 抽帧验布局：不开渲染，只把每帧截成 PNG 给你看。
// 渲一帧 16~31 秒，截一张图 1 秒——布局问题在这里挡掉，别等到成片。
//
//   FRAMES_DIR=frames-x SCENES_FILE=frames-x/scenes.json node shot.mjs
//   FRAMES_DIR=frames-x AT=2.5 node shot.mjs          # 指定看第 2.5 秒的状态
//   FRAMES_DIR=frames-x ONLY=p3.html node shot.mjs    # 只看一帧
//
// AT  默认 end（动画全部走完的静止终态，最容易暴露溢出/重叠）；也可给数字秒数
// OUT_DIR 默认 /tmp/hvs-shots
// JOBS 默认 4

import { chromium } from "playwright";
import { mkdirSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RESOLVE = (p) => (path.isAbsolute(p) ? p : path.join(HERE, p));

const FRAMES = RESOLVE(process.env.FRAMES_DIR || "frames");
const OUT = process.env.OUT_DIR || "/tmp/hvs-shots";
const AT = process.env.AT || "end";
const ONLY = process.env.ONLY || "";
const JOBS = Math.max(1, Number(process.env.JOBS || 4));
const CANVAS_W = Number(process.env.CANVAS_W || 1920);
const CANVAS_H = Number(process.env.CANVAS_H || 1080);

let files;
if (process.env.SCENES_FILE) {
  const raw = JSON.parse(readFileSync(RESOLVE(process.env.SCENES_FILE), "utf8"));
  files = raw.map((s) => s.file);
} else if (ONLY) {
  files = [ONLY];
} else {
  files = readdirSync(FRAMES).filter((f) => f.endsWith(".html")).sort();
}
if (ONLY && !process.env.SCENES_FILE) files = [ONLY];

mkdirSync(OUT, { recursive: true });

// 把动画拨到指定时刻：end 表示拨到各自 endTime（终态），否则拨到 AT 秒
function settle(at) {
  const anims = typeof document.getAnimations === "function" ? document.getAnimations() : [];
  for (let i = 0; i < anims.length; i++) {
    const a = anims[i];
    try {
      if (a.playState !== "paused") a.pause();
      if (at === "end") {
        const end = a.effect && a.effect.getComputedTiming
          ? a.effect.getComputedTiming().endTime
          : null;
        a.currentTime = end == null || !isFinite(end) ? 1e7 : end;
      } else {
        a.currentTime = Number(at) * 1000;
      }
    } catch (e) {}
  }
}

const browser = await chromium.launch({
  args: ["--force-device-scale-factor=1", "--hide-scrollbars"],
});
const shots = [];

async function shoot(i, file) {
  const context = await browser.newContext({
    viewport: { width: CANVAS_W, height: CANVAS_H },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await page.goto("file://" + path.join(FRAMES, file), { waitUntil: "load" });
  await page.evaluate(() => (document.fonts ? document.fonts.ready : Promise.resolve()));
  await page.waitForTimeout(250);
  await page.evaluate(settle, AT);
  await page.waitForTimeout(120);
  const target = path.join(OUT, file.replace(/\.html$/, "") + ".png");
  await page.screenshot({ path: target, type: "png" });
  await context.close();
  shots.push(target);
}

let cursor = 0;
await Promise.all(
  Array.from({ length: Math.min(JOBS, files.length) }, async () => {
    for (;;) {
      const i = cursor++;
      if (i >= files.length) return;
      await shoot(i, files[i]);
    }
  })
);
await browser.close();

console.log("AT=" + AT + "  " + shots.length + " 张 -> " + OUT);
shots.sort().forEach((p) => console.log("  " + p));
