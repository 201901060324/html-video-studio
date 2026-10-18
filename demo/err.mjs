import { chromium } from "playwright";
import path from "node:path";
const f = process.argv[2];
const b = await chromium.launch();
for (const tt of [0.5, 2, 4, 7]) {
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = [];
  p.on("pageerror", e => errs.push(e.message));
  p.on("console", m => { if (m.type() === "error" || m.type()==="log") errs.push("log:"+m.text()); });
  await p.goto("file://" + path.resolve(f) + "#t=" + tt);
  await p.waitForTimeout(300);
  console.log("t="+tt, errs.slice(0,4));
  await p.close();
}
await b.close();
