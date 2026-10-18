import { chromium } from "playwright";
const [file, ...times] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
const errs = [];
p.on("pageerror", e => errs.push(e.message));
await p.goto("file://" + file + "#t=0");
await p.waitForTimeout(400);
for (const t of times) {
  await p.evaluate((x) => window.__hf_seek(x), Number(t));
  await p.waitForTimeout(60);
  await p.screenshot({ path: `/tmp/cine_${t}.png` });
}
console.log(errs.length ? errs.slice(0,3) : "no error");
await b.close();
