import { chromium } from "playwright";
import { readdirSync } from "node:fs";

const DIR = process.argv[2] || "frames-landing";
const files = readdirSync(DIR).filter((f) => f.endsWith(".html")).sort();
const b = await chromium.launch();
const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });

for (const f of files) {
  await pg.goto("file://" + process.cwd() + "/" + DIR + "/" + f);
  await pg.waitForTimeout(400);
  const r = await pg.evaluate(() => {
    const wrap = document.querySelector(".wrap");
    const out = [];
    let sum = 0;
    for (const el of wrap.children) {
      const cs = getComputedStyle(el);
      if (cs.position === "absolute") continue; // foot 等绝对定位元素不占流内高度
      const rect = el.getBoundingClientRect();
      const mt = parseFloat(cs.marginTop) || 0;
      const mb = parseFloat(cs.marginBottom) || 0;
      sum += rect.height + mt + mb;
      const cls = (el.className || el.tagName).toString().split(" ")[0];
      out.push(cls + " h=" + Math.round(rect.height) + " b=" + Math.round(rect.bottom));
    }
    return { sum: Math.round(sum), out };
  });
  const over = r.sum > 880 ? "  <<< 溢出 " + (r.sum - 880) + "px" : "";
  console.log(f.padEnd(24) + " sum=" + r.sum + over);
  console.log("    " + r.out.join(" | "));
}
await b.close();
