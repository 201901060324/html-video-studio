import { chromium } from "playwright";
const b = await chromium.launch();
for (const f of ["p01","p04","p14","p11"]) {
  const ctx = await b.newContext({ viewport:{width:1920,height:1080}, deviceScaleFactor:1 });
  const p = await ctx.newPage();
  await p.goto("file://" + process.cwd() + "/frames-dsv41/" + f + ".html#t=1");
  await p.waitForTimeout(200);
  let t0=Date.now();
  for (let i=0;i<20;i++) await p.evaluate((t)=>window.__hf_seek(t), 1+i*0.05);
  const tDraw=(Date.now()-t0)/20;
  t0=Date.now();
  for (let i=0;i<10;i++) await p.screenshot({type:"png"});
  const tPng=(Date.now()-t0)/10;
  t0=Date.now();
  for (let i=0;i<10;i++) await p.screenshot({type:"jpeg",quality:95});
  const tJpg=(Date.now()-t0)/10;
  console.log(f, "seek+draw", tDraw.toFixed(0)+"ms", "png", tPng.toFixed(0)+"ms", "jpg", tJpg.toFixed(0)+"ms");
  await ctx.close();
}
await b.close();
