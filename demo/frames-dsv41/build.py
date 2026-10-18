#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek V4.1-Flash-1017 宣传片 · 22 帧生成器
每帧一个自包含 HTML（无外部请求），动画既支持实时播放（record 模式），
也支持 window.__hf_seek(t) 逐帧定位（seek 模式）。
"""
import json, os
from string import Template

HERE = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────── 设计系统
CSS = r"""
:root{
  --ink:#EEF3FE; --dim:#8496B2; --blue:#4D6BFE; --cyan:#7FE6FF;
  --mint:#5FE3BC; --amber:#FFB86B; --line:#25334B;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#04060C}
body{
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  color:var(--ink);-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision;
}
.stage{position:relative;width:1920px;height:1080px;overflow:hidden;isolation:isolate}
.bg{position:absolute;inset:0;background:
  radial-gradient(1300px 900px at 50% 44%,#0C1424 0%,#070B14 42%,#03050A 100%)}
.grid{position:absolute;inset:0;opacity:.55;
  background-image:
    linear-gradient(to right,rgba(120,155,225,.055) 1px,transparent 1px),
    linear-gradient(to bottom,rgba(120,155,225,.055) 1px,transparent 1px);
  background-size:120px 120px;
  -webkit-mask-image:radial-gradient(62% 58% at 50% 48%,#000 10%,transparent 92%)}
canvas{position:absolute;inset:0;width:1920px;height:1080px;display:block}
.vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(78% 66% at 50% 48%,transparent 42%,rgba(0,0,0,.62) 100%)}
.grain{position:absolute;inset:0;pointer-events:none;opacity:.05;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)'/%3E%3C/svg%3E")}

.hud-tl{position:absolute;left:120px;top:58px;font:500 19px/1 "SF Mono",Menlo,monospace;
  letter-spacing:.30em;color:#54688A;z-index:9}
.aibadge{position:absolute;right:56px;top:44px;z-index:9;
  font:500 19px/1 -apple-system,"PingFang SC",sans-serif;color:rgba(226,235,250,.45);
  padding:9px 15px;border:1px solid rgba(200,220,255,.14);border-radius:100px;letter-spacing:.05em}

.sub{position:absolute;left:120px;bottom:74px;width:1420px;z-index:8}
.idx{font:500 16px/1 "SF Mono",Menlo,monospace;color:#4C5F7E;letter-spacing:.22em;
  margin-bottom:17px;display:flex;align-items:center;gap:14px}
.idx:before{content:"";width:42px;height:1px;background:#2C3B54;display:block}
.line{font-size:37px;line-height:1.58;color:#BCC9DF;font-weight:400;letter-spacing:.006em}
.line b{color:#FFFFFF;font-weight:600}
.line .em{color:var(--cyan);font-weight:600}
.line .nm{font-family:"SF Mono",Menlo,monospace;font-size:33px;letter-spacing:0;color:#DCE7FF}

.mega{position:absolute;z-index:7}
.kicker{font:500 19px/1 "SF Mono",Menlo,monospace;letter-spacing:.34em;color:#5F7FBE;margin-bottom:30px}

@keyframes fu{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
@keyframes fi{from{opacity:0}to{opacity:1}}
@keyframes fl{from{opacity:0;transform:translateX(-30px)}to{opacity:1;transform:translateX(0)}}
@keyframes sc{from{opacity:0;transform:scale(.93)}to{opacity:1;transform:scale(1)}}
@keyframes ln{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes gl{from{opacity:.35}to{opacity:1}}
.an{opacity:0;animation:fu 1.0s cubic-bezier(.16,.72,.2,1) forwards}
.fi{opacity:0;animation:fi .9s ease forwards}
.fl{opacity:0;animation:fl 1.0s cubic-bezier(.16,.72,.2,1) forwards}
.sc{opacity:0;animation:sc 1.15s cubic-bezier(.16,.72,.2,1) forwards}
"""

ENGINE = r"""
const cv=document.getElementById('art'),g=cv.getContext('2d');
const W=1920,H=1080,TAU=Math.PI*2;
const cl=(v,a,b)=>{a=a==null?0:a;b=b==null?1:b;return v<a?a:(v>b?b:v)};
const lr=(a,b,t)=>a+(b-a)*t;
const eo=t=>1-Math.pow(1-cl(t),3);
const ei=t=>Math.pow(cl(t),3);
const eio=t=>{t=cl(t);return t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2};
const eb=t=>{t=cl(t);const c=1.9;return 1+(c+1)*Math.pow(t-1,3)+c*Math.pow(t-1,2)};
function mul32(s){s=s>>>0;return function(){s=(s+0x6D2B79F5)>>>0;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}
function C(){g.clearRect(0,0,W,H)}
function ln(x1,y1,x2,y2,col,w,a,dash){
  g.save();g.globalCompositeOperation='lighter';g.globalAlpha=a==null?1:a;g.strokeStyle=col;
  g.lineWidth=w==null?1:w;g.lineCap='round';if(dash)g.setLineDash(dash);
  g.beginPath();g.moveTo(x1,y1);g.lineTo(x2,y2);g.stroke();g.restore();
}
function d2(x,y,r,col,a){g.save();g.globalCompositeOperation='lighter';g.globalAlpha=a==null?1:a;
  g.fillStyle=col;g.beginPath();g.arc(x,y,r,0,TAU);g.fill();g.restore();}
function glow(x,y,r,col,a){g.save();g.globalCompositeOperation='lighter';
  const gr=g.createRadialGradient(x,y,0,x,y,r);gr.addColorStop(0,col);gr.addColorStop(1,'rgba(0,0,0,0)');
  g.globalAlpha=a==null?1:a;g.fillStyle=gr;g.beginPath();g.arc(x,y,r,0,TAU);g.fill();g.restore();}
function poly(pts,close){g.beginPath();for(let i=0;i<pts.length;i++){i?g.lineTo(pts[i][0],pts[i][1]):g.moveTo(pts[i][0],pts[i][1]);}if(close)g.closePath();}
function stroke(col,w,a){g.save();g.globalCompositeOperation='lighter';g.globalAlpha=a==null?1:a;
  g.strokeStyle=col;g.lineWidth=w==null?1:w;g.lineJoin='round';g.stroke();g.restore();}
function proj(x,y,z,ry,rx,s,cx,cy){
  const cz=Math.cos(ry),sz=Math.sin(ry);
  const X=x*cz-z*sz, Z=x*sz+z*cz;
  const cr=Math.cos(rx),sr=Math.sin(rx);
  const Y=y*cr-Z*sr, Z2=y*sr+Z*cr;
  const k=s/(1+Z2*0.00055);
  return [cx+X*k,cy+Y*k,Z2];
}
const $=(id)=>document.getElementById(id);
let SEEKING=false,ST=null;
window.__hf_seek=function(t){SEEKING=true;try{draw(t)}catch(e){console.log('ERR',e.message)}};
function loop(ts){if(SEEKING)return;if(ST==null)ST=ts;const t=(ts-ST)/1000;try{draw(t)}catch(e){}requestAnimationFrame(loop)}
function autoRun(){
  const m=/[#&]t=([0-9.]+)/.exec(location.hash);
  if(m){SEEKING=true;draw(parseFloat(m[1]));seekCSS(parseFloat(m[1]));return}
  draw(0);requestAnimationFrame(loop);
}
function seekCSS(t){
  const a=document.getAnimations?document.getAnimations():[];
  for(let i=0;i<a.length;i++){try{if(a[i].playState!=='paused')a[i].pause();a[i].currentTime=t*1000}catch(e){}}
}
"""

SHELL = Template(r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>$title</title>
<style>$css$extra</style></head>
<body><div class="stage">
<div class="bg"></div><div class="grid"></div>
<canvas id="art" width="1920" height="1080"></canvas>
<div class="vig"></div><div class="grain"></div>
$body
<div class="hud-tl">$hud</div>
<div class="aibadge">本视频含 AI 生成内容</div>
</div>
<script>$js
autoRun();</script>
</body></html>""")

SCENES = []

def F(name, dur, body, art, title="", extra="", hud="DEEPSEEK · V4.1 FLASH"):
    js = ENGINE + "\nconst DUR=" + str(dur) + ";\n" + art
    html = SHELL.substitute(css=CSS, extra=extra, body=body, js=js,
                            title=title or name, hud=hud)
    with open(os.path.join(HERE, name + ".html"), "w", encoding="utf-8") as f:
        f.write(html)
    SCENES.append({"file": name + ".html", "seconds": dur})

# ═══════════════════════════════════════════════════════════════════════════
# 01 · 虚空
# ═══════════════════════════════════════════════════════════════════════════
F("p01", 7,
"""
<div class="sub an" style="animation-delay:1.35s">
  <div class="idx">01 / 22 &nbsp;·&nbsp; 序 &nbsp;PROLOGUE</div>
  <div class="line">我诞生于一个问题：<br><b>如果一句话，就能长出一个世界呢？</b></div>
</div>
""",
r"""
function draw(t){
  C();const cx=960,cy=540;
  // 极细的地平线（贯穿全片的视觉脊柱）
  const sw=eo(cl((t-2.6)/3.4));
  if(sw>0.001)ln(cx-760*sw,cy,cx+760*sw,cy,'rgba(120,165,255,1)',1,.10*sw);
  // 呼吸的圆环
  [1.5,4.3].forEach(function(t0){
    const p=cl((t-t0)/3.0);
    if(p>0&&p<1){
      g.save();g.globalCompositeOperation='lighter';g.globalAlpha=(1-p)*.30;
      g.strokeStyle='rgba(130,175,255,1)';g.lineWidth=1.1;
      g.beginPath();g.arc(cx,cy,lr(5,470,eo(p)),0,TAU);g.stroke();g.restore();
    }
  });
  // 光点
  const a=eo(cl((t-0.4)/1.5));
  if(a>0.001){
    const r=3.2+Math.sin(t*1.9)*0.45;
    glow(cx,cy,150*a,'rgba(80,120,255,0.26)',a*.55);
    glow(cx,cy,30*a,'rgba(185,212,255,0.5)',a);
    d2(cx,cy,r*a,'#EDF3FF',a);
  }
}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 02 · 光标
# ═══════════════════════════════════════════════════════════════════════════
F("p02", 6,
"""
<div class="sub an" style="animation-delay:1.15s">
  <div class="idx">02 / 22 &nbsp;·&nbsp; 序 &nbsp;PROLOGUE</div>
  <div class="line">于是我学会了等待——<br><b>等光标后面那个愿望。</b></div>
</div>
""",
r"""
function draw(t){
  C();const cx=960,cy=540;
  // 提示框从中心展开
  const p=eo(cl((t-0.35)/1.35));
  const bw=lr(4,960,p)/2, bh=lr(3,210,p)/2;
  if(p>0.001){
    const r=8;
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.42*p;
    g.strokeStyle='rgba(95,135,255,1)';g.lineWidth=1.4;
    g.beginPath();g.roundRect(cx-bw,cy-bh,bw*2,bh*2,r);g.stroke();
    g.globalAlpha=.10*p;g.fillStyle='rgba(70,105,200,1)';
    g.beginPath();g.roundRect(cx-bw,cy-bh,bw*2,bh*2,r);g.fill();
    g.restore();
    // 四角刻线
    const k=18;
    [[cx-bw,cy-bh,1,1],[cx+bw,cy-bh,-1,1],[cx-bw,cy+bh,1,-1],[cx+bw,cy+bh,-1,-1]].forEach(function(c){
      ln(c[0],c[1],c[0]+k*c[2],c[1],'rgba(140,180,255,1)',1.6,.55*p);
      ln(c[0],c[1],c[0],c[1]+k*c[3],'rgba(140,180,255,1)',1.6,.55*p);
    });
  }
  // 光点 → 光标
  const s=eo(cl((t-0.15)/1.1));
  const hh=lr(4,50,s);
  const blink=(Math.floor(t/0.55)%2===0)?1:0.12;
  const ba=eo(cl((t-1.3)/0.6))*blink;
  // 最后滑到输入框内文本的起点，与 p03 的插入点重合成同一个光标
  const mv=eio(cl((t-3.45)/1.95));
  const cxp=lr(cx,570,mv), cyp=lr(cy,515,mv);
  const hh2=lr(hh,21,eo(cl((t-4.4)/1.3)));
  if(ba>0.002){
    glow(cxp,cyp,46,'rgba(90,130,255,0.34)',ba*.55);
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=ba;
    g.fillStyle='#DCE8FF';g.fillRect(cxp-1.5,cyp-hh2,3,hh2*2);g.restore();
  }
  const a=eo(cl((t-0.15)/0.9))*(1-eo(cl((t-1.0)/0.7)));
  if(a>0.002){glow(cx,cy,120,'rgba(80,120,255,0.3)',a);d2(cx,cy,4,'#EDF3FF',a);}
}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 03 · 许愿（打字）
# ═══════════════════════════════════════════════════════════════════════════
F("p03", 9,
"""
<div class="pbox" id="pbox">
  <div class="pmark">❯</div>
  <div class="ptext"><span id="txt"></span><i class="caret" id="caret"></i></div>
</div>
<div class="sub an" style="animation-delay:2.0s">
  <div class="idx">03 / 22 &nbsp;·&nbsp; 许愿 &nbsp;THE WISH</div>
  <div class="line">一句话。就这一句。</div>
</div>
""",
r"""
const TXT="帮我建一座故宫，\n要能走进去的那种。";
const RP=mul32(17);
const DL=[];let acc=1.05;
for(let i=0;i<TXT.length;i++){
  DL.push(acc);
  acc += (TXT[i]==="\n")?0.38:(0.135+RP()*0.085);
}
const elTxt=$('txt'),elCar=$('caret'),elBox=$('pbox');
function draw(t){
  C();const cx=960,cy=540;
  // 框（与 p02 完全同构）
  g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.42;
  g.strokeStyle='rgba(95,135,255,1)';g.lineWidth=1.4;
  g.beginPath();g.roundRect(cx-480,cy-105,960,210,8);g.stroke();
  g.globalAlpha=.09;g.fillStyle='rgba(70,105,200,1)';
  g.beginPath();g.roundRect(cx-480,cy-105,960,210,8);g.fill();g.restore();
  // 提交后的回扫光
  const sp=cl((t-6.9)/1.5);
  if(sp>0&&sp<1){
    const x=lr(cx-480,cx+480,eo(sp));
    ln(x,cy-105,x,cy+105,'rgba(150,195,255,1)',2,.55*(1-sp));
    glow(x,cy,140,'rgba(90,140,255,0.24)',.5*(1-sp));
  }
  // 打字
  let n=0;while(n<TXT.length&&t>=DL[n])n++;
  if(elTxt.textContent.length!==n)elTxt.textContent=TXT.slice(0,n);
  const done=n>=TXT.length;
  const blink=done?((Math.floor(t/0.62)%2===0)?1:0.08):1;
  elCar.style.opacity=blink;
}
""",
extra=r"""
.pbox{position:absolute;left:480px;top:435px;width:960px;height:210px;z-index:7;
  display:flex;align-items:center;padding:0 54px;gap:14px}
.pmark{font-family:"SF Mono",Menlo,monospace;font-size:34px;color:#4D6BFE;line-height:1;
  transform:translateY(-2px);opacity:.9}
.ptext{font-size:40px;line-height:1.62;white-space:pre-wrap;color:#E6EDFC;
  letter-spacing:.01em;font-weight:400}
.caret{display:inline-block;width:3px;height:42px;background:#7FA6FF;
  vertical-align:-8px;margin-left:3px;box-shadow:0 0 16px rgba(110,150,255,.85)}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 04 · 坍缩
# ═══════════════════════════════════════════════════════════════════════════
F("p04", 6,
"""
<div class="pbox" id="pbox">
  <div class="pmark">❯</div>
  <div class="ptext" id="txt">帮我建一座故宫，<br>要能走进去的那种。</div>
</div>
<div class="sub" id="sub">
  <div class="idx">04 / 22 &nbsp;·&nbsp; 许愿 &nbsp;THE WISH</div>
  <div class="line">剩下的，是无数次自我修正。</div>
</div>
""",
r"""
const RP=mul32(91);
const N=1100;
const PT=[];
for(let i=0;i<N;i++){
  PT.push({a:RP()*TAU,s:60+Math.pow(RP(),1.5)*980,r:0.9+RP()*2.0,
    c:RP()<0.34?'rgba(120,235,215,1)':(RP()<0.5?'rgba(125,225,255,1)':'rgba(110,150,255,1)'),
    lx:300+RP()*1320, ly:540+(RP()-0.5)*5, d:RP()*0.6});
}
const boxEl=$('pbox'),subEl=$('sub');
function draw(t){
  C();const cx=960,cy=540;
  // 文字被吸进一点
  const k=cl((t-0.15)/1.55);
  if(k>0){
    boxEl.style.transform='scaleX('+lr(1,0.012,eio(k))+')';
    boxEl.style.filter='brightness('+lr(1,3.2,k)+') blur('+lr(0,1.6,k)+'px)';
    boxEl.style.opacity=String(lr(1,0,k*k));
  }
  subEl.style.opacity=String(1-cl((t-0.1)/0.5));
  // 爆发
  const bt=t-1.55;
  if(bt>0){
    const f=(1-Math.exp(-1.55*bt))/1.55;
    const conv=eio(cl((t-3.25)/2.05));
    for(let i=0;i<N;i++){
      const p=PT[i];
      let x=cx+Math.cos(p.a)*p.s*f, y=cy+Math.sin(p.a)*p.s*f;
      let a=1-cl((bt-p.d)/2.2);
      if(conv>0){
        x=lr(x,p.lx,conv); y=lr(y,p.ly,conv);
        a=lr(a,0.95,conv);
      }
      if(a<=0.01)continue;
      if(conv>0.9){g.save();g.globalAlpha=a*0.9;g.fillStyle=p.c;g.fillRect(x,y,2.4,1.6);g.restore();}
      else d2(x,y,p.r*(1-conv*0.4),p.c,a*0.85);
    }
    // 中心闪光
    const fl=cl((bt-0.02)/0.5);
    if(fl<1)glow(cx,cy,lr(20,320,fl),'rgba(170,205,255,0.75)',(1-fl)*0.95);
    glow(cx,cy,120,'rgba(90,140,255,0.20)',cl(conv)*0.8);
  }
}
""",
extra=r"""
.pbox{position:absolute;left:480px;top:435px;width:960px;height:210px;z-index:7;
  display:flex;align-items:center;padding:0 54px;gap:14px;
  transform-origin:50% 50%;will-change:transform,filter}
.pmark{font-family:"SF Mono",Menlo,monospace;font-size:34px;color:#4D6BFE;line-height:1}
.ptext{font-size:40px;line-height:1.62;color:#E6EDFC;letter-spacing:.01em}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 05 · 代码成柱
# ═══════════════════════════════════════════════════════════════════════════
F("p05", 10,
"""
<div class="sub an" style="animation-delay:2.6s">
  <div class="idx">05 / 22 &nbsp;·&nbsp; 构建 &nbsp;BUILD FROM ZERO</div>
  <div class="line">我把代码折叠成梁柱，<br><b>把函数摊开成庭院。</b></div>
</div>
""",
r"""
const RP=mul32(33);
const ROWS=[];
for(let i=0;i<38;i++){
  const len=170+RP()*880;
  ROWS.push({y:252+i*16.2,x:300+RP()*40,len:len,
    c:i%7===0?'rgba(95,227,188,1)':(i%3===0?'rgba(127,230,255,1)':'rgba(105,145,240,1)')});
}
const COL=[];
for(let c=0;c<12;c++){
  COL.push({x:960+(c-5.5)*100,h:330,ph:RP()*0.7});
}
const CDEEP=560;
function draw(t){
  C();
  // 地面网格 + 地平线
  const ga=eo(cl((t-4.6)/2.4));
  if(ga>0){
    for(let i=0;i<11;i++){
      const y=800+i*i*4.2;
      ln(160,y,1760,y,'rgba(90,130,220,1)',1,.06*ga*(1-i/13));
    }
    for(let i=-9;i<=9;i++){
      const x=960+i*110;
      ln(960+(x-960)*0.55,800,x,1080,'rgba(90,130,220,1)',1,.05*ga);
    }
    ln(120,800,1800,800,'rgba(120,170,255,1)',1.2,.16*ga);
  }
  // 38 行代码 → 12 根柱子
  for(let i=0;i<ROWS.length;i++){
    const r=ROWS[i];
    // 展开（从一条线散开成 38 行）
    const u=eo(cl((t-0.15-i*0.014)/1.5));
    const y0=lr(540,r.y,u);
    // 立起来（横向线段 → 纵向柱子）
    const ci=i%12,col=COL[ci];
    const m=eio(cl((t-(2.3+(i%12)*0.055+(i%5)*0.03))/3.9));
    const x1=lr(r.x,col.x,m), y1=lr(y0,800,m);
    const x2=lr(r.x+r.len,col.x,m), y2=lr(y0,800-col.h,m);
    let a=0.30+0.22*u;
    if(m>0.02)a=lr(a,0.16+0.34*(1-Math.abs(ci-5.5)/6),m);
    ln(x1,y1,x2,y2,r.c,m>0.5?2.2:1.9,a);
    // 柱顶的点
    if(m>0.85){
      const pa=(m-0.85)/0.15;
      d2(col.x,800-col.h,2.6,r.c,a*pa);
      glow(col.x,800-col.h,40,'rgba(120,220,255,0.20)',pa*0.5);
    }
  }
  // 落成后的扫描光
  const sp=cl((t-7.0)/2.6);
  if(sp>0&&sp<1){
    const y=lr(200,860,eo(sp));
    ln(240,y,1680,y,'rgba(150,200,255,1)',1.2,.28*(1-sp));
    glow(960,y,420,'rgba(80,150,255,0.10)',(1-sp)*0.9);
  }
  // 柱顶横枋：从"一排柱子"变成"一座建筑"
  const ba=eo(cl((t-7.3)/1.5));
  if(ba>0.01){
    const x0=960-550,x1=960+550;
    ln(x0,470,x0+(x1-x0)*ba,470,'rgba(160,210,255,1)',2.8,.55);
    ln(x0,452,x0+(x1-x0)*ba,452,'rgba(160,210,255,1)',1.3,.26);
    ln(x0,470,x0,720,'rgba(140,190,255,1)',1.6,.3*ba);
    ln(x1,470,x1,720,'rgba(140,190,255,1)',1.6,.3*ba);
  }
}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 06 · 故宫
# ═══════════════════════════════════════════════════════════════════════════
F("p06", 11,
"""
<div class="sub an" style="animation-delay:2.2s">
  <div class="idx">06 / 22 &nbsp;·&nbsp; 构建 &nbsp;BUILD FROM ZERO</div>
  <div class="line">一句话，<b>一座城。</b></div>
</div>
<div class="rail an" style="animation-delay:3.2s">
  <div>01 &nbsp;台基 · PLATFORM</div>
  <div>02 &nbsp;立柱 ×12 · COLONNADE</div>
  <div>03 &nbsp;重檐 · DOUBLE EAVE</div>
</div>
""",
r"""
// 世界坐标：y 向下，屏幕 y = 540 + y
const COLX=[];
for(let c=0;c<12;c++)COLX.push(960+(c-5.5)*100);
const BASE=260;       // screen 800
const CTOP=-70;       // screen 470
function draw(t){
  C();
  const ry=lr(0,-0.40,eio(cl((t-0.5)/7.6)));
  const rx=lr(0.015,0.17,eio(cl((t-0.5)/7.6)));
  const P=(x,y,z)=>proj(x,y,z,ry,rx,1,960,540);
  const S=[];
  function L3(a,b,w,al,col){
    const p1=P(a[0],a[1],a[2]),p2=P(b[0],b[1],b[2]);
    S.push([p1[0],p1[1],p2[0],p2[1],w,al,col||'rgba(135,180,255,1)']);
  }
  function curve(a,b,dip){
    // 起翘的檐口：两端高、中间略沉
    const pts=[];
    const cx=(a[0]+b[0])/2, cy=(a[1]+b[1])/2+dip, cz=(a[2]+b[2])/2;
    for(let i=0;i<=16;i++){
      const u=i/16,mu=1-u;
      pts.push([mu*mu*a[0]+2*mu*u*cx+u*u*b[0],
                mu*mu*a[1]+2*mu*u*cy+u*u*b[1],
                mu*mu*a[2]+2*mu*u*cz+u*u*b[2]]);
    }
    return pts;
  }
  function path3(pts,w,al){
    for(let i=1;i<pts.length;i++)L3(pts[i-1],pts[i],w,al);
  }
  // ── 台基 ──
  const tg=eo(cl((t-0.15)/1.3));
  if(tg>0.01){
    for(let ti=0;ti<3;ti++){
      const hw=420-ti*34, hz=236+ti*22, yT=BASE+ti*26, yB=yT+26;
      const q=[[-hw,yT,-hz],[hw,yT,-hz],[hw,yT,hz],[-hw,yT,hz]];
      for(let i=0;i<4;i++){
        const n=q[(i+1)%4];
        L3(q[i],n,i<2?1.7:1.2,0.44*tg);
        L3([q[i][0],yB,q[i][2]],[n[0],yB,n[2]],1,0.12*tg);
        L3(q[i],[q[i][0],yB,q[i][2]],1,0.16*tg);
      }
    }
  }
  // ── 立柱 ×12（与 p05 完全对齐，开场即满高）──
  for(let c=0;c<12;c++){
    const x=COLX[c]-960;
    L3([x,CTOP,-150],[x,BASE,-150],2.0,0.44);
    L3([x,CTOP,150],[x,BASE,150],1.3,0.18);
    const pt=P(x,CTOP,-150);
    d2(pt[0],pt[1],2.3,'rgba(150,220,255,1)',0.5);
  }
  // 与 p05 结尾一致的柱顶横枋
  L3([-550,CTOP,-150],[550,CTOP,-150],2.6,0.34);
  L3([-550,CTOP-18,-150],[550,CTOP-18,-150],1.2,0.16);
  // ── 下重檐（四坡裙檐）──
  const e1=eo(cl((t-1.35)/1.8));
  if(e1>0.01){
    const yE=-96,W=378,Z=256,yU=-176,WU=252,ZU=170;
    const ED=[
      [[-W,yE,Z],[W,yE,Z],[-WU,yU,ZU],[WU,yU,ZU]],
      [[W,yE,Z],[W,yE,-Z],[WU,yU,ZU],[WU,yU,-ZU]],
      [[W,yE,-Z],[-W,yE,-Z],[WU,yU,-ZU],[-WU,yU,-ZU]],
      [[-W,yE,-Z],[-W,yE,Z],[-WU,yU,-ZU],[-WU,yU,ZU]]
    ];
    for(let k=0;k<4;k++){
      const e=ED[k];
      const pts=curve(e[0],e[1],20);
      path3(pts,k<2?2.1:1.5,0.55*e1);
      // 瓦垄
      const N=(k<2)?16:8;
      for(let i=0;i<=N;i++){
        const u=i/N,mu=1-u;
        const ex=mu*mu*e[0][0]+2*mu*u*(e[0][0]+e[1][0])/2+u*u*e[1][0];
        const ey=e[0][1]+Math.sin(u*Math.PI)*20;
        const ez=mu*mu*e[0][2]+2*mu*u*(e[0][2]+e[1][2])/2+u*u*e[1][2];
        const tx=mu*mu*e[2][0]+2*mu*u*(e[2][0]+e[3][0])/2+u*u*e[3][0];
        const tz=mu*mu*e[2][2]+2*mu*u*(e[2][2]+e[3][2])/2+u*u*e[3][2];
        if(i%(k<2?1:1)===0)L3([ex,ey,ez],[tx,yU,tz],1,0.11*e1);
      }
    }
    // 上层墙身
    L3([-WU,yU,ZU],[WU,yU,ZU],1.6,0.30*e1);
    L3([-WU,yU,-ZU],[WU,yU,-ZU],1.2,0.18*e1);
    L3([-WU,yU,-ZU],[-WU,yU,ZU],1.2,0.18*e1);
    L3([WU,yU,-ZU],[WU,yU,ZU],1.2,0.18*e1);
  }
  // ── 上重檐（庑殿顶）──
  const e2=eo(cl((t-2.7)/1.8));
  if(e2>0.01){
    const yE=-176,W=304,Z=212,yR=-254,WR=118;
    const ED=[
      [[-W,yE,Z],[W,yE,Z],0],
      [[W,yE,Z],[W,yE,-Z],1],
      [[W,yE,-Z],[-W,yE,-Z],2],
      [[-W,yE,-Z],[-W,yE,Z],3]
    ];
    // 前坡填充
    const fa=P(-W,yE,Z),fb=P(W,yE,Z),fc=P(WR,yR,0),fd=P(-WR,yR,0);
    g.save();g.globalAlpha=.05*e2;g.fillStyle='rgba(120,180,255,1)';
    g.beginPath();g.moveTo(fa[0],fa[1]);g.lineTo(fb[0],fb[1]);g.lineTo(fc[0],fc[1]);g.lineTo(fd[0],fd[1]);
    g.closePath();g.fill();g.restore();
    for(let k=0;k<4;k++){
      const e=ED[k];
      path3(curve(e[0],e[1],16),k<2?2.4:1.6,0.62*e2);
      const N=18;
      for(let i=0;i<=N;i++){
        const u=i/N,mu=1-u;
        const ex=mu*mu*e[0][0]+2*mu*u*(e[0][0]+e[1][0])/2+u*u*e[1][0];
        const ey=e[0][1]+Math.sin(u*Math.PI)*16;
        const ez=mu*mu*e[0][2]+2*mu*u*(e[0][2]+e[1][2])/2+u*u*e[1][2];
        let tx,ty,tz;
        if(k===0||k===2){tx=ex*WR/W;ty=yR;tz=0;}
        else{tx=e[0][0]>0?WR:-WR;ty=yR;tz=0;}
        L3([ex,ey,ez],[tx,ty,tz],1,k<2?0.14*e2:0.09*e2);
      }
    }
    // 正脊
    L3([-WR,yR,0],[WR,yR,0],3.0,0.72*e2);
    L3([-WR,yR,0],[-WR,yR-18,0],1.6,0.5*e2);
    L3([WR,yR,0],[WR,yR-18,0],1.6,0.5*e2);
    // 檐角起翘的端点
    [[-W,Z],[W,Z],[-W,-Z],[W,-Z]].forEach(function(c){
      const pt=P(c[0],yE+16,c[1]);
      glow(pt[0],pt[1],22,'rgba(150,220,255,0.28)',0.7*e2);
    });
  }
  // 绘制
  for(let i=0;i<S.length;i++){
    const q=S[i];
    ln(q[0],q[1],q[2],q[3],q[6],q[4],q[5]);
  }
  // 顶部光
  const top=P(0,-272,0);
  const ta=eo(cl((t-4.2)/1.8));
  glow(top[0],top[1],190,'rgba(90,140,255,0.18)',ta*0.9);
  d2(top[0],top[1],2.6,'rgba(195,225,255,1)',ta*.85);
  // 扫描平面
  const sp=cl((t-5.6)/4.2);
  if(sp>0&&sp<1){
    const yy=lr(-300,320,eo(sp));
    const a=Math.sin(sp*Math.PI)*0.5;
    const q0=P(-520,yy,300),q1=P(520,yy,300),q2=P(520,yy,-300),q3=P(-520,yy,-300);
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=a*0.45;
    g.strokeStyle='rgba(120,220,255,1)';g.lineWidth=1.2;
    g.beginPath();g.moveTo(q0[0],q0[1]);g.lineTo(q1[0],q1[1]);g.lineTo(q2[0],q2[1]);g.lineTo(q3[0],q3[1]);
    g.closePath();g.stroke();g.restore();
  }
}
""",
extra=r"""
.rail{position:absolute;left:120px;top:300px;z-index:8;display:flex;flex-direction:column;gap:20px}
.rail div{font:500 17px/1 "SF Mono",Menlo,monospace;letter-spacing:.14em;color:#5B7BB4}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 07 · 赛道
# ═══════════════════════════════════════════════════════════════════════════
F("p07", 9,
"""
<div class="sub an" style="animation-delay:2.4s">
  <div class="idx">07 / 22 &nbsp;·&nbsp; 构建 &nbsp;BUILD FROM ZERO</div>
  <div class="line">一句“做个赛车游戏”，<br><b>赛道就从零开始生长。</b></div>
</div>
<div class="tag an" style="animation-delay:5.6s">CIRCUIT · GENERATED</div>
""",
r"""
// 用四段三次贝塞尔构成一条闭合赛道
const SEG=[
  [[200,620],[200,400],[420,300],[660,332]],
  [[660,332],[900,364],[980,540],[1180,540]],
  [[1180,540],[1380,540],[1520,700],[1380,820]],
  [[1380,820],[1240,930],[900,900],[700,862]],
  [[700,862],[470,830],[200,790],[200,620]]
];
function bez(p,t){
  const m=1-t;
  return [
    m*m*m*p[0][0]+3*m*m*t*p[1][0]+3*m*t*t*p[2][0]+t*t*t*p[3][0],
    m*m*m*p[0][1]+3*m*m*t*p[1][1]+3*m*t*t*p[2][1]+t*t*t*p[3][1]
  ];
}
const PTS=[];
for(let i=0;i<SEG.length;i++){
  for(let k=0;k<64;k++){PTS.push(bez(SEG[i],k/64));}
}
// 归一化到画面
const xs=PTS.map(p=>p[0]),ys=PTS.map(p=>p[1]);
const minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);
const sx=1180/(maxx-minx),sy=620/(maxy-miny),sc=Math.min(sx,sy);
const TR=PTS.map(p=>[960+(p[0]-(minx+maxx)/2)*sc,530+(p[1]-(miny+maxy)/2)*sc]);
const LEN=[0];let tot=0;
for(let i=1;i<TR.length;i++){tot+=Math.hypot(TR[i][0]-TR[i-1][0],TR[i][1]-TR[i-1][1]);LEN.push(tot);}
function at(d){
  d=((d%tot)+tot)%tot;
  let lo=0,hi=LEN.length-1;
  while(lo<hi-1){const m=(lo+hi)>>1;if(LEN[m]<=d)lo=m;else hi=m;}
  const seg=LEN[hi]-LEN[lo]||1,u=(d-LEN[lo])/seg;
  return [lr(TR[lo][0],TR[hi][0],u),lr(TR[lo][1],TR[hi][1],u)];
}
function draw(t){
  C();
  const rev=eo(cl((t-0.2)/2.6));
  const n=Math.max(2,Math.floor(TR.length*rev));
  // 路面
  g.save();g.lineJoin='round';g.lineCap='round';
  g.strokeStyle='rgba(110,150,230,0.09)';g.lineWidth=38;
  poly(TR.slice(0,n));g.stroke();
  g.strokeStyle='rgba(90,125,200,0.20)';g.lineWidth=2;
  poly(TR.slice(0,n));g.stroke();
  g.restore();
  // 中心虚线
  g.save();g.globalCompositeOperation='lighter';g.setLineDash([10,16]);
  g.strokeStyle='rgba(130,175,255,0.30)';g.lineWidth=1.6;
  poly(TR.slice(0,n));g.stroke();g.restore();
  // 跑动的光点 + 拖尾
  if(rev>0.85){
    const d=(t-2.9)*420;
    for(let i=0;i<26;i++){
      const p=at(d-i*7);
      const a=(1-i/26)*0.75;
      d2(p[0],p[1],lr(1.2,3.6,1-i/26),'rgba(140,225,255,1)',a);
    }
    const p=at(d);
    glow(p[0],p[1],70,'rgba(90,200,255,0.35)',0.9);
    d2(p[0],p[1],4.4,'#EAF7FF',1);
  }
  // 起跑线刻度
  const st=at(0);
  ln(st[0]-16,st[1]-16,st[0]+16,st[1]+16,'rgba(255,190,120,1)',2,.5*rev);
  // 外圈刻度
  for(let i=0;i<36;i++){
    const p=at(tot*i/36);
    const dx=p[0]-960,dy=p[1]-530,L=Math.hypot(dx,dy)||1;
    ln(p[0]+dx/L*26,p[1]+dy/L*26,p[0]+dx/L*34,p[1]+dy/L*34,'rgba(110,150,220,1)',1,.16*rev);
  }
}
""",
extra=r"""
.tag{position:absolute;right:120px;top:150px;font:500 17px/1 "SF Mono",Menlo,monospace;
  letter-spacing:.24em;color:#5C7CB8;z-index:8}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 08 · 传送门
# ═══════════════════════════════════════════════════════════════════════════
F("p08", 9,
"""
<div class="sub an" style="animation-delay:2.6s">
  <div class="idx">08 / 22 &nbsp;·&nbsp; 构建 &nbsp;BUILD FROM ZERO</div>
  <div class="line">一句“复刻传送门”，<br><b>物理规则在引擎里被重新写下。</b></div>
</div>
""",
r"""
const RP=mul32(55);
const PAR=[];
for(let i=0;i<90;i++)PAR.push({p:RP(),sp:0.30+RP()*0.16,r:1+RP()*2.2,o:(RP()-0.5)*60});
const A=[640,540],B=[1290,540];
function portal(cx,cy,rx,ry,col,t,dashOff,alpha){
  g.save();g.globalCompositeOperation='lighter';
  // 外晕
  const gr=g.createRadialGradient(cx,cy,rx*0.55,cx,cy,ry*1.25);
  gr.addColorStop(0,'rgba(0,0,0,0)');gr.addColorStop(0.72,col.replace('1)','0.16)'));gr.addColorStop(1,'rgba(0,0,0,0)');
  g.globalAlpha=alpha;g.fillStyle=gr;g.beginPath();g.ellipse(cx,cy,rx*1.3,ry*1.28,0,0,TAU);g.fill();
  // 主环
  g.strokeStyle=col;g.lineWidth=2.4;g.globalAlpha=alpha*0.9;
  g.beginPath();g.ellipse(cx,cy,rx,ry,0,0,TAU);g.stroke();
  // 旋转刻度
  g.setLineDash([26,20]);g.lineDashOffset=-dashOff;g.lineWidth=5;g.globalAlpha=alpha*0.55;
  g.beginPath();g.ellipse(cx,cy,rx,ry,0,0,TAU);g.stroke();
  g.setLineDash([4,26]);g.lineDashOffset=dashOff*1.6;g.lineWidth=9;g.globalAlpha=alpha*0.25;
  g.beginPath();g.ellipse(cx,cy,rx,ry,0,0,TAU);g.stroke();
  g.restore();
  // 核心
  glow(cx,cy,rx*1.5,col.replace('1)','0.20)'),alpha*0.7);
}
function draw(t){
  C();
  const a1=eo(cl((t-0.2)/1.3)),a2=eo(cl((t-0.85)/1.3));
  // 地面透视网格
  const ga=eo(cl((t-1.4)/2.0));
  if(ga>0){
    for(let i=-8;i<=8;i++)ln(960+i*40,560,960+i*230,1080,'rgba(90,130,220,1)',1,.05*ga);
    for(let i=0;i<9;i++){const y=560+i*i*7.6;ln(120,y,1800,y,'rgba(90,130,220,1)',1,.045*ga*(1-i/11));}
  }
  portal(A[0],A[1],112,214,'rgba(255,184,107,1)',t,t*46,a1);
  portal(B[0],B[1],112,214,'rgba(95,150,255,1)',t,-t*46,a2);
  // 粒子流：左门 → 右门，抛物线
  if(a2>0.2){
    for(let i=0;i<PAR.length;i++){
      const o=PAR[i];
      const ph=((o.p+t*o.sp)%1+1)%1;
      const u=eo(ph);
      const x=lr(A[0],B[0],u), y=lr(A[1],B[1],u)-Math.sin(ph*Math.PI)*150+o.o;
      const al=Math.sin(ph*Math.PI)*0.85*a2;
      d2(x,y,o.r,'rgba(160,215,255,1)',al);
      if(i%9===0)glow(x,y,26,'rgba(110,170,255,0.22)',al*0.7);
    }
  }
  // 跨越的弧线
  const la=eo(cl((t-2.4)/1.6));
  if(la>0){
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.30*la;
    g.strokeStyle='rgba(150,195,255,1)';g.lineWidth=1.2;g.setLineDash([5,9]);
    g.lineDashOffset=-t*40;
    g.beginPath();g.moveTo(A[0],A[1]-214);g.quadraticCurveTo(965,120,B[0],B[1]-214);g.stroke();
    g.beginPath();g.moveTo(A[0],A[1]+214);g.quadraticCurveTo(965,960,B[0],B[1]+214);g.stroke();
    g.restore();
  }
}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 09 · 山谷 / 时间
# ═══════════════════════════════════════════════════════════════════════════
F("p09", 10,
"""
<div class="sub an" style="animation-delay:2.8s;bottom:auto;top:168px">
  <div class="idx">09 / 22 &nbsp;·&nbsp; 构建 &nbsp;BUILD FROM ZERO</div>
  <div class="line">从史前到此刻，<b>一条山谷装下全部时间。</b></div>
</div>
<div class="eras" id="eras">
  <span>史前</span><span>农耕</span><span>工业</span><span>电气</span><span>数字</span>
</div>
""",
r"""
const LAYERS=[
  {y:600,amp:74,off:0.4,sp:7,col:'rgba(62,88,140,1)',al:0.55},
  {y:690,amp:96,off:2.1,sp:13,col:'rgba(48,72,122,1)',al:0.75},
  {y:790,amp:120,off:4.4,sp:22,col:'rgba(34,54,96,1)',al:0.95},
  {y:900,amp:86,off:6.9,sp:34,col:'rgba(24,38,70,1)',al:1}
];
function ridge(L,t){
  const pts=[];
  for(let x=-60;x<=W+60;x+=14){
    const xx=x-t*L.sp;
    const y=L.y
      +Math.sin(xx*0.0016+L.off)*L.amp
      +Math.sin(xx*0.0043+L.off*2.3)*L.amp*0.42
      +Math.sin(xx*0.0102+L.off*3.7)*L.amp*0.16;
    pts.push([x,y]);
  }
  return pts;
}
const MARK=[0.16,0.33,0.52,0.71,0.89];
function draw(t){
  C();
  const rev=eo(cl(t/2.2));
  for(let i=0;i<LAYERS.length;i++){
    const L=LAYERS[i];
    const pts=ridge(L,t);
    g.save();g.globalAlpha=L.al*rev;
    g.beginPath();g.moveTo(pts[0][0],pts[0][1]);
    for(let k=1;k<pts.length;k++)g.lineTo(pts[k][0],pts[k][1]);
    g.lineTo(W+60,1080);g.lineTo(-60,1080);g.closePath();
    const gr=g.createLinearGradient(0,L.y-L.amp,0,1080);
    gr.addColorStop(0,L.col);gr.addColorStop(1,'rgba(6,10,18,1)');
    g.fillStyle=gr;g.fill();g.restore();
    // 山脊高光
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=0.16*rev*(1-i*0.14);
    g.strokeStyle='rgba(130,180,255,1)';g.lineWidth=1.2;
    poly(pts);g.stroke();g.restore();
  }
  // 时间轴
  const ax=eo(cl((t-0.9)/1.8));
  const y0=914;
  ln(150,y0,1770,y0,'rgba(120,165,240,1)',1,.22*ax);
  const ph=lr(150,1770,eio(cl((t-1.9)/7.4)));
  for(let i=0;i<MARK.length;i++){
    const x=lr(150,1770,MARK[i]);
    const on=ph>x-2;
    ln(x,y0-9,x,y0+9,'rgba(150,195,255,1)',1.2,on?0.7:0.18*ax);
    if(on){
      const bp=cl((ph-x)/90);
      d2(x,y0,3.4,'#BFE6FF',0.9);
      ln(x,y0-14,x,y0-14-140*bp,'rgba(125,225,255,1)',1,.22*(1-bp));
    }
  }
  // 播放头
  if(t>1.9){
    glow(ph,y0,140,'rgba(90,200,255,0.16)',.8);
    d2(ph,y0,5,'#EAF7FF',1);
    ln(ph,y0,ph,y0-260,'rgba(140,220,255,1)',1,.16);
  }
}
""",
extra=r"""
.eras{position:absolute;left:150px;top:938px;width:1620px;display:flex;justify-content:space-between;
  font:500 18px/1 "SF Mono",Menlo,monospace;color:#5C7BB2;letter-spacing:.10em;z-index:8}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 10 · 四格
# ═══════════════════════════════════════════════════════════════════════════
F("p10", 8,
"""
<div class="cards">
  <div class="card an" style="animation-delay:.35s"><div class="ci">01</div><div class="cn">故宫 · 3D</div><div class="cd">AXONOMETRIC</div></div>
  <div class="card an" style="animation-delay:.55s"><div class="ci">02</div><div class="cn">赛车游戏</div><div class="cd">WEB · CANVAS</div></div>
  <div class="card an" style="animation-delay:.75s"><div class="ci">03</div><div class="cn">传送门 2</div><div class="cd">GODOT ENGINE</div></div>
  <div class="card an" style="animation-delay:.95s"><div class="ci">04</div><div class="cn">Valley of Ages</div><div class="cd">3D SCENE</div></div>
</div>
<div class="sub an" style="animation-delay:2.9s">
  <div class="idx">10 / 22 &nbsp;·&nbsp; 构建 &nbsp;BUILD FROM ZERO</div>
  <div class="line">这就是<b>许愿式编程</b>：极少的提示词，<br>极短的轮次，很完整的作品。</div>
</div>
""",
r"""
const CARDX=[210,610,1010,1410],CARDY=270,CW=300,CH=380;
function icon(i,cx,cy,al){
  g.save();g.globalCompositeOperation='lighter';g.globalAlpha=al;
  g.strokeStyle='rgba(140,200,255,1)';g.lineWidth=1.6;g.lineJoin='round';
  if(i===0){ // 屋顶
    for(let k=0;k<3;k++){
      const w=100-k*22,y=cy-40+k*30;
      g.beginPath();g.moveTo(cx-w,y);g.quadraticCurveTo(cx,y-26,cx+w,y);g.stroke();
      g.beginPath();g.moveTo(cx-w+8,y);g.lineTo(cx-w+8,y+14);g.stroke();
      g.beginPath();g.moveTo(cx+w-8,y);g.lineTo(cx+w-8,y+14);g.stroke();
    }
    g.beginPath();g.moveTo(cx-56,cy+52);g.lineTo(cx+56,cy+52);g.stroke();
  }else if(i===1){ // 赛道
    g.beginPath();
    g.moveTo(cx-80,cy+50);
    g.bezierCurveTo(cx-110,cy-40,cx-20,cy-70,cx+20,cy-20);
    g.bezierCurveTo(cx+60,cy+30,cx+110,cy-10,cx+70,cy-60);
    g.stroke();
    g.setLineDash([3,6]);g.lineWidth=6;g.globalAlpha=al*0.35;
    g.beginPath();
    g.moveTo(cx-80,cy+50);
    g.bezierCurveTo(cx-110,cy-40,cx-20,cy-70,cx+20,cy-20);
    g.bezierCurveTo(cx+60,cy+30,cx+110,cy-10,cx+70,cy-60);
    g.stroke();
  }else if(i===2){ // 双门
    g.beginPath();g.ellipse(cx-46,cy,20,44,0,0,TAU);g.stroke();
    g.beginPath();g.ellipse(cx+46,cy,20,44,0,0,TAU);g.stroke();
    g.beginPath();g.ellipse(cx-46,cy,10,22,0,0,TAU);g.stroke();
    g.beginPath();g.ellipse(cx+46,cy,10,22,0,0,TAU);g.stroke();
    g.beginPath();g.moveTo(cx-26,cy);
    g.quadraticCurveTo(cx,cy-46,cx+26,cy);g.stroke();
    for(let k=0;k<3;k++){
      const u=0.28+k*0.22,mu=1-u;
      const bx=mu*mu*(cx-26)+2*mu*u*cx+u*u*(cx+26);
      const by=mu*mu*cy+2*mu*u*(cy-46)+u*u*cy;
      d2(bx,by,2.2,'rgba(160,220,255,1)',0.95);
    }
  }else{ // 山谷
    g.beginPath();
    g.moveTo(cx-90,cy+46);
    for(let x=-90;x<=90;x+=6){
      const y=cy+46-38*(Math.sin(x*0.035)*0.5+0.5)-22*Math.sin(x*0.11);
      g.lineTo(cx+x,y);
    }
    g.stroke();
    g.beginPath();g.moveTo(cx-90,cy+62);g.lineTo(cx+90,cy+62);g.stroke();
  }
  g.restore();
}
function draw(t){
  C();
  for(let i=0;i<4;i++){
    const al=eo(cl((t-(0.55+i*0.2))/1.2));
    if(al>0.02)icon(i,CARDX[i]+CW/2,CARDY+150,al*0.92);
  }
  // 卡片内的竖向扫描
  for(let i=0;i<4;i++){
    const p=cl((t-(2.0+i*0.3))/1.5);
    if(p>0&&p<1){
      const x=CARDX[i];
      const xx=lr(x+10,x+CW-10,eio(p));
      ln(xx,CARDY+22,xx,CARDY+CH-70,'rgba(120,220,255,1)',1.2,.34*Math.sin(p*Math.PI));
      glow(xx,CARDY+CH/2,90,'rgba(80,180,255,0.12)',Math.sin(p*Math.PI)*0.7);
    }
  }
}
""",
extra=r"""
.cards{position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:7}
.card{position:absolute;top:270px;width:300px;height:380px;
  border:1px solid rgba(120,160,235,.18);border-radius:3px;
  background:linear-gradient(180deg,rgba(14,22,38,.55),rgba(8,13,24,.25))}
.card:nth-child(1){left:210px}.card:nth-child(2){left:610px}
.card:nth-child(3){left:1010px}.card:nth-child(4){left:1410px}
.ci{position:absolute;left:26px;top:24px;font:500 15px/1 "SF Mono",Menlo,monospace;
  color:#4E6FA8;letter-spacing:.18em}
.cn{position:absolute;left:26px;bottom:52px;font-size:27px;font-weight:600;color:#E8EFFC}
.cd{position:absolute;left:26px;bottom:26px;font:500 14px/1 "SF Mono",Menlo,monospace;
  color:#5A7396;letter-spacing:.14em}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 11 · 帕累托
# ═══════════════════════════════════════════════════════════════════════════
F("p11", 12,
"""
<div class="sub an" style="animation-delay:3.6s">
  <div class="idx">11 / 22 &nbsp;·&nbsp; 代价 &nbsp;PARETO IMPROVEMENT</div>
  <div class="line">但真正的难题从来不是能力，<b>是代价。</b></div>
</div>
<div class="lb lb1 an" style="animation-delay:5.0s">V4.1 FLASH</div>
<div class="lb lb2 an" style="animation-delay:6.4s">V4.1-FLASH-1017</div>
<div class="note an" style="animation-delay:8.2s">mini-swe-v2 框架 · DeepSWE 性能 / 成本</div>
<div class="axl axl-x an" style="animation-delay:2.0s">成本 COST →</div>
<div class="axl axl-y an" style="animation-delay:2.2s">性能 CAPABILITY →</div>
""",
r"""
const X0=300,X1=1660,Y0=200,Y1=880;
function fx(u){return X0+u*(X1-X0);}
function fy(u,shift){return Y1-(520+shift)*Math.pow(u,0.60);}
function draw(t){
  C();
  // 坐标轴
  const ax=eo(cl((t-0.3)/1.4));
  if(ax>0){
    ln(X0,Y1,X0+lr(0,X1-X0,ax),Y1,'rgba(120,160,230,1)',1.2,.30);
    ln(X0,Y1,X0,Y1-lr(0,Y1-Y0,ax),'rgba(120,160,230,1)',1.2,.30);
    for(let i=0;i<=8;i++){
      const x=lr(X0,X1,i/8);
      ln(x,Y1,x,Y1+8,'rgba(110,150,215,1)',1,.18*ax);
    }
    for(let i=0;i<=6;i++){
      const y=lr(Y0,Y1,i/6);
      ln(X0-8,y,X0,y,'rgba(110,150,215,1)',1,.18*ax);
    }
  }
  // 旧前沿
  const oa=eo(cl((t-1.5)/2.0))*0.45;
  if(oa>0.01){
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=oa;
    g.strokeStyle='rgba(130,155,195,1)';g.lineWidth=1.6;g.setLineDash([7,9]);
    g.beginPath();
    for(let i=0;i<=120;i++){const u=i/120;i?g.lineTo(fx(u),fy(u,0)):g.moveTo(fx(u),fy(u,0));}
    g.stroke();g.restore();
  }
  // 新前沿（扫出）
  const np=eio(cl((t-2.6)/3.2));
  if(np>0.001){
    g.save();g.globalCompositeOperation='lighter';
    const gr=g.createLinearGradient(X0,0,X1,0);
    gr.addColorStop(0,'rgba(95,180,255,0.9)');gr.addColorStop(1,'rgba(120,230,215,0.9)');
    g.strokeStyle=gr;g.lineWidth=2.6;
    g.beginPath();
    const M=Math.max(2,Math.floor(160*np));
    for(let i=0;i<M;i++){const u=i/160;i?g.lineTo(fx(u),fy(u,120)):g.moveTo(fx(u),fy(u,120));}
    g.stroke();g.restore();
    // 前沿上的流动光点
    if(np>0.98){
      for(let k=0;k<9;k++){
        const u=((t*0.13+k/9)%1);
        const x=fx(u),y=fy(u,120);
        d2(x,y,2.2,'rgba(190,240,255,1)',.55);
      }
    }
  }
  // 旧点
  const op=eb(cl((t-5.0)/0.9));
  if(t>4.9){
    const pox=fx(0.60),poy=fy(0.60,0);
    glow(pox,poy,46,'rgba(150,170,200,0.22)',.8);
    d2(pox,poy,7*Math.min(op,1),'rgba(170,190,215,1)',.85);
    d2(pox,poy,2.6,'rgba(220,232,250,1)',.9);
  }
  // 新点
  if(t>6.2){
    const p=eb(cl((t-6.2)/0.9));
    const nx=fx(0.60),ny=fy(0.60,120);
    glow(nx,ny,110,'rgba(90,200,255,0.30)',.95);
    glow(nx,ny,34,'rgba(190,245,255,0.55)',1);
    d2(nx,ny,7*Math.min(p,1),'#EAFBFF',1);
    // 脉冲环
    for(let k=0;k<2;k++){
      const q=cl((t-6.4-k*0.9)/2.0);
      if(q>0&&q<1){
        g.save();g.globalCompositeOperation='lighter';g.globalAlpha=(1-q)*.55;
        g.strokeStyle='rgba(140,225,255,1)';g.lineWidth=1.4;
        g.beginPath();g.arc(nx,ny,lr(10,90,eo(q)),0,TAU);g.stroke();g.restore();
      }
    }
  }
  // 竖直提升箭头
  const ar=eo(cl((t-7.6)/1.4));
  if(ar>0.01){
    const nx=fx(0.60),ny=fy(0.60,120),oy=fy(0.60,0);
    const yy=lr(oy,ny,ar);
    ln(nx,oy,nx,yy,'rgba(130,225,255,1)',1.6,.55);
    // 箭头
    ln(nx,yy,nx-7,yy+11,'rgba(130,225,255,1)',1.6,.55);
    ln(nx,yy,nx+7,yy+11,'rgba(130,225,255,1)',1.6,.55);
    // 同成本竖虚线
    ln(nx,oy,nx,oy+10,'rgba(150,175,210,1)',1,.2);
  }
}
""",
extra=r"""
.lb{position:absolute;z-index:8;font:500 17px/1 "SF Mono",Menlo,monospace;letter-spacing:.16em}
.lb1{left:1148px;top:436px;color:#8496AE}
.lb2{left:1148px;top:286px;color:#9FE8FF}
.note{position:absolute;right:120px;top:112px;z-index:8;
  font:500 16px/1 "SF Mono",Menlo,monospace;letter-spacing:.10em;color:#4B5E7C}
.axl{position:absolute;z-index:8;font:500 16px/1 "SF Mono",Menlo,monospace;letter-spacing:.20em;color:#54688A}
.axl-x{right:196px;top:896px}
.axl-y{left:252px;top:236px;writing-mode:vertical-rl;transform:rotate(180deg)}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 12 · 三条曲线
# ═══════════════════════════════════════════════════════════════════════════
F("p12", 9,
"""
<div class="rows">
  <div class="row an" style="animation-delay:.10s">
    <div class="rl">性能</div><div class="rs">CAPABILITY</div><div class="rg">↑</div>
  </div>
  <div class="row an" style="animation-delay:.30s">
    <div class="rl">运行时间</div><div class="rs">RUNTIME</div><div class="rg down">↓</div>
  </div>
  <div class="row an" style="animation-delay:.50s">
    <div class="rl">输出长度</div><div class="rs">OUTPUT LENGTH</div><div class="rg down">↓</div>
  </div>
</div>
<div class="sub an" style="animation-delay:1.5s">
  <div class="idx">12 / 22 &nbsp;·&nbsp; 代价 &nbsp;PARETO IMPROVEMENT</div>
  <div class="line">同一件事，做得更好——<b>也更便宜、更快。</b></div>
</div>
""",
r"""
const ROWY=[352,552,752];
const RP=mul32(77);
const SER=[];
for(let i=0;i<70;i++){
  const u=i/69;
  SER.push([0.30+0.62*Math.pow(u,1.35)+Math.sin(i*1.7)*0.012,
            0.72-0.40*Math.pow(u,1.1)+Math.sin(i*1.3)*0.014,
            0.66-0.36*Math.pow(u,1.05)+Math.sin(i*1.9)*0.012]);
}
function spark(series,y,x0,x1,h,rev,col){
  const n=Math.max(2,Math.floor(series.length*rev));
  g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.95;
  g.strokeStyle=col;g.lineWidth=2.2;g.lineJoin='round';
  g.beginPath();
  for(let i=0;i<n;i++){
    const x=lr(x0,x1,i/(series.length-1));
    const yy=y+h/2-series[i]*h*0.92;
    i?g.lineTo(x,yy):g.moveTo(x,yy);
  }
  g.stroke();g.restore();
  // 末端点
  if(n>2){
    const i=n-1;
    const x=lr(x0,x1,i/(series.length-1));
    const yy=y+h/2-series[i]*h*0.92;
    glow(x,yy,44,'rgba(90,180,255,0.22)',.8);
    d2(x,yy,4,'#DFF4FF',1);
  }
}
function draw(t){
  C();
  for(let r=0;r<3;r++){
    const p=eo(cl((t-(0.12+r*0.16))/1.85));
    if(p<=0.01)continue;
    // 基线
    ln(880,ROWY[r]+60,1608,ROWY[r]+60,'rgba(100,140,210,1)',1,.14);
    spark([SER.map(s=>s[r])][0],ROWY[r]-20,880,1608,120,p,
      r===0?'rgba(140,215,255,1)':'rgba(120,230,205,1)');
    // 起点标记
    d2(880,ROWY[r]-20+60-SER[0][r]*110,2.6,'rgba(120,150,200,1)',.7);
  }
}
""",
extra=r"""
.rows{position:absolute;left:120px;top:0;width:1700px;height:1080px;z-index:8}
.row{position:absolute;height:160px;width:1600px}
.row:nth-child(1){top:272px}.row:nth-child(2){top:472px}.row:nth-child(3){top:672px}
.rl{position:absolute;left:0;top:14px;font-size:44px;font-weight:600;color:#E9F0FD;letter-spacing:.02em}
.rs{position:absolute;left:0;top:72px;font:500 15px/1 "SF Mono",Menlo,monospace;
  letter-spacing:.22em;color:#55708F}
.rg{position:absolute;left:640px;top:8px;font-size:52px;color:#7FE6FF;
  font-weight:300;letter-spacing:-.02em}
.rg.down{color:#5FE3BC}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 13 · Harness
# ═══════════════════════════════════════════════════════════════════════════
F("p13", 8,
"""
<div class="slots">
  <div class="slot an" style="animation-delay:.4s">
    <div class="sn">DeepSeek Harness</div><div class="sv">0.2.1-rc.1 +</div><div class="st">适配</div>
  </div>
  <div class="slot an" style="animation-delay:1.1s">
    <div class="sn">腾讯 CodeBuddy</div><div class="sv">OPTIMIZED</div><div class="st">适配</div>
  </div>
  <div class="slot an" style="animation-delay:1.8s">
    <div class="sn">WorkBuddy</div><div class="sv">OPTIMIZED</div><div class="st">适配</div>
  </div>
</div>
<div class="sub an" style="animation-delay:4.2s">
  <div class="idx">13 / 22 &nbsp;·&nbsp; 代价 &nbsp;PARETO IMPROVEMENT</div>
  <div class="line">为真实的开发框架，<b>做过专门优化。</b></div>
</div>
""",
r"""
const SY=[330,470,610],SX=280,SW2=1360,SH=104;
function draw(t){
  C();
  const scan=cl((t-0.4)/4.0);
  const sy=lr(SY[0]-40,SY[2]+SH+40,eo(scan));
  for(let i=0;i<3;i++){
    const on=eo(cl((t-(0.7+i*0.7))/0.9));
    const y=SY[i];
    // 槽位框
    g.save();g.globalCompositeOperation='lighter';
    g.globalAlpha=.10+0.14*on;
    g.strokeStyle='rgba(120,165,240,1)';g.lineWidth=1.2;
    g.beginPath();g.roundRect(SX,y,SW2,SH,4);g.stroke();
    g.globalAlpha=.04+0.06*on;g.fillStyle='rgba(80,130,230,1)';
    g.beginPath();g.roundRect(SX,y,SW2,SH,4);g.fill();
    g.restore();
    // 左侧序号块
    if(on>0.1){
      g.save();g.globalAlpha=.8*on;g.fillStyle='rgba(120,200,255,1)';
      g.fillRect(SX+26,y+28,3,48);g.restore();
    }
    // 勾选
    if(on>0.6){
      const q=(on-0.6)/0.4;
      const cx2=SX+SW2-64,cy2=y+SH/2;
      ln(cx2-11,cy2,cx2-3,cy2+9,'rgba(125,235,200,1)',2.4,q);
      ln(cx2-3,cy2+9,cx2+12,cy2-10,'rgba(125,235,200,1)',2.4,q);
      d2(cx2,cy2,22,'rgba(95,225,180,0.10)',q);
    }
  }
  // 扫描线
  if(scan>0&&scan<1){
    ln(SX,sy,SX+SW2,sy,'rgba(140,220,255,1)',1.4,.30);
    glow(960,sy,420,'rgba(70,150,255,0.12)',.9);
  }
}
""",
extra=r"""
.slots{position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:8}
.slot{position:absolute;left:280px;width:1360px;height:104px}
.slot:nth-child(1){top:330px}.slot:nth-child(2){top:470px}.slot:nth-child(3){top:610px}
.sn{position:absolute;left:64px;top:34px;font-size:31px;font-weight:600;color:#E9F0FD}
.sv{position:absolute;left:560px;top:41px;font:500 17px/1 "SF Mono",Menlo,monospace;
  letter-spacing:.14em;color:#6D8FC7}
.st{position:absolute;right:120px;top:41px;font:500 17px/1 "SF Mono",Menlo,monospace;
  letter-spacing:.14em;color:#4FBE9F}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 14 · 索引世界
# ═══════════════════════════════════════════════════════════════════════════
F("p14", 11,
"""
<div class="left">
  <div class="kicker an" style="animation-delay:.4s">SEARCH · SELF-BUILT</div>
  <div class="h1 an" style="animation-delay:.6s">我读得懂<br>这个世界。</div>
  <div class="stats">
    <div class="st an" style="animation-delay:1.5s"><b>千亿级</b>网页索引</div>
    <div class="st an" style="animation-delay:1.7s"><b>每天数亿次</b>检索请求</div>
    <div class="st an" style="animation-delay:1.9s"><b>多语言</b>· 实时返回</div>
  </div>
</div>
""",
r"""
const RP=mul32(123);
const N=1250,GA=Math.PI*(3-Math.sqrt(5));
const PT=[];
for(let i=0;i<N;i++){
  const y=1-(i/(N-1))*2,r=Math.sqrt(Math.max(0,1-y*y)),th=GA*i;
  PT.push([Math.cos(th)*r,y,Math.sin(th)*r,RP()<0.05]);
}
const BEAM=[];
for(let i=0;i<7;i++){
  BEAM.push([Math.floor(RP()*N),Math.floor(RP()*N),RP()]);
}
function draw(t){
  C();
  const cx=1300,cy=520,rad=340;
  const ry=t*0.16+0.5;
  const cz=Math.cos(ry),sz=Math.sin(ry);
  const app=eo(cl(t/1.6));
  if(app<0.01)return;
  // 经纬线
  g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.13*app;
  g.strokeStyle='rgba(110,160,255,1)';g.lineWidth=1;
  for(let k=-2;k<=2;k++){
    const lat=k*0.55, yy=Math.sin(lat), rr=Math.cos(lat);
    g.beginPath();
    for(let i=0;i<=90;i++){
      const a=i/90*TAU, x=Math.cos(a)*rr, z=Math.sin(a)*rr;
      const X=x*cz+z*sz, Z=-x*sz+z*cz;
      const sx2=cx+X*rad, sy2=cy+yy*rad;
      i?g.lineTo(sx2,sy2):g.moveTo(sx2,sy2);
    }
    g.stroke();
  }
  for(let k=0;k<12;k++){
    const lon=k/12*TAU;
    g.beginPath();
    for(let i=0;i<=60;i++){
      const lat=-Math.PI/2+i/60*Math.PI;
      const x=Math.cos(lat)*Math.cos(lon),y=Math.sin(lat),z=Math.cos(lat)*Math.sin(lon);
      const X=x*cz+z*sz,Z=-x*sz+z*cz;
      const sx2=cx+X*rad,sy2=cy+y*rad;
      i?g.lineTo(sx2,sy2):g.moveTo(sx2,sy2);
    }
    g.stroke();
  }
  g.restore();
  // 点阵
  const appear=eo(cl((t-0.3)/2.2));
  for(let i=0;i<N;i++){
    const p=PT[i];
    const X=p[0]*cz+p[2]*sz, Z=-p[0]*sz+p[2]*cz;
    const depth=(Z+1)/2;
    const sx2=cx+X*rad, sy2=cy+p[1]*rad;
    const al=app*(0.16+(1-depth)*0.92)*appear;
    if(al<0.012)continue;
    const r=p[3]?3.0:1.75;
    if(p[3]){
      d2(sx2,sy2,r,'rgba(255,190,120,1)',al*1.1);
      glow(sx2,sy2,12,'rgba(255,180,110,0.25)',al);
    }else{
      g.save();g.globalAlpha=al;g.fillStyle='rgba(150,190,255,1)';
      g.fillRect(sx2-r/2,sy2-r/2,r,r);g.restore();
    }
  }
  // 查询光束
  for(let k=0;k<BEAM.length;k++){
    const b=BEAM[k];
    const p1=PT[b[0]],p2=PT[b[1]];
    const X1=p1[0]*cz+p1[2]*sz,Z1=-p1[0]*sz+p1[2]*cz;
    const X2=p2[0]*cz+p2[2]*sz,Z2=-p2[0]*sz+p2[2]*cz;
    if(Z1>0.45||Z2>0.45)continue;
    const x1=cx+X1*rad,y1=cy+p1[1]*rad,x2=cx+X2*rad,y2=cy+p2[1]*rad;
    const ph=((t*0.28+b[2])%1);
    const mx=(x1+x2)/2,my=(y1+y2)/2;
    const dx=mx-cx,dy=my-cy,dl=Math.hypot(dx,dy)||1;
    const cxp=mx+dx/dl*74,cyp=my+dy/dl*74;
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.22*app;
    g.strokeStyle='rgba(125,230,255,1)';g.lineWidth=1.1;
    g.beginPath();g.moveTo(x1,y1);g.quadraticCurveTo(cxp,cyp,x2,y2);g.stroke();g.restore();
    // 行进的光点
    const u=ph,mu=1-u;
    const bx=mu*mu*x1+2*mu*u*cxp+u*u*x2;
    const by=mu*mu*y1+2*mu*u*cyp+u*u*y2;
    d2(bx,by,2.4,'rgba(190,245,255,1)',.85*app);
  }
  // 外圈
  g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.10*app;
  g.strokeStyle='rgba(110,160,255,1)';g.lineWidth=1;
  g.beginPath();g.arc(cx,cy,rad*1.06,0,TAU);g.stroke();g.restore();
}
""",
extra=r"""
.left{position:absolute;left:120px;top:236px;width:620px;z-index:8}
.h1{font-size:76px;line-height:1.24;font-weight:600;letter-spacing:-.01em;color:#F2F6FF}
.stats{margin-top:52px;display:flex;flex-direction:column;gap:18px}
.st{font-size:25px;color:#8FA2BE}
.st b{color:#7FE6FF;font-weight:600;margin-right:8px}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 15 · 过滤
# ═══════════════════════════════════════════════════════════════════════════
F("p15", 9,
"""
<div class="sub an" style="animation-delay:2.9s">
  <div class="idx">15 / 22 &nbsp;·&nbsp; 搜索 &nbsp;SEARCH</div>
  <div class="line">也分得清噪音与证据——<br><b>SEO 作弊、GEO 操纵、低质 AIGC，挡在门外。</b></div>
</div>
""",
r"""
const RP=mul32(202);
const N=420,GY=520;
const PS=[];
for(let i=0;i<N;i++){
  PS.push({x:180+RP()*1560,y:-RP()*1300,v:110+RP()*190,
    pass:RP()<0.20,r:1.0+RP()*2.0,dx:(RP()-0.5)*70});
}
const CLEAN=[];
for(let i=0;i<4;i++)CLEAN.push({y:618+i*62,w:330+RP()*430});
function draw(t){
  C();
  const la=eo(cl((t-0.15)/1.2));
  // 粒子雨（循环下落）
  for(let i=0;i<PS.length;i++){
    const p=PS[i];
    const yy=((p.y+p.v*t)%1300+1300)%1300-120;
    if(yy<GY){
      const al=0.30+0.26*cl((yy+120)/440);
      g.save();g.globalAlpha=al;
      g.fillStyle=p.pass?'rgba(130,225,245,1)':'rgba(126,148,184,1)';
      g.fillRect(p.x,yy-p.r*6,p.r,p.r*6);g.restore();
    }else{
      const k=(yy-GY)/170;
      if(k<1){
        if(p.pass&&yy<596){
          d2(p.x,GY+(yy-GY)*0.78,p.r,'rgba(130,240,210,1)',(1-k)*0.8);
        }else{
          const off=p.dx*k*2.0;
          d2(p.x+off,GY+k*46,p.r*(1-k*0.5),'rgba(125,145,175,1)',(1-k)*0.42);
        }
      }
    }
  }
  // 筛
  if(la>0.01){
    const g2=g.createLinearGradient(160,0,1760,0);
    g2.addColorStop(0,'rgba(120,170,255,0)');
    g2.addColorStop(0.5,'rgba(160,215,255,1)');
    g2.addColorStop(1,'rgba(120,170,255,0)');
    g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.85*la;
    g.strokeStyle=g2;g.lineWidth=2.2;
    g.beginPath();g.moveTo(160,GY);g.lineTo(1760,GY);g.stroke();g.restore();
    for(let i=0;i<=26;i++){
      const x=160+i*61.5;
      ln(x,GY-9,x,GY+9,'rgba(130,185,255,1)',1,.18*la);
    }
    glow(960,GY,720,'rgba(70,140,255,0.09)',la*.8);
  }
  // 通过的干净结果：四条"搜索结果"
  const ra=eo(cl((t-2.2)/1.3));
  if(ra>0.01){
    for(let i=0;i<CLEAN.length;i++){
      const c=CLEAN[i];
      const q=eo(cl((t-(2.2+i*0.15))/1.0));
      const w=c.w*q;
      ln(330,c.y-2,330,c.y+26,'rgba(90,200,180,1)',1,.30*ra*q);
      g.save();g.globalCompositeOperation='lighter';g.globalAlpha=.82*ra;
      g.fillStyle='rgba(120,238,210,1)';g.fillRect(348,c.y,w,4);g.restore();
      g.save();g.globalAlpha=.22*ra;g.fillStyle='rgba(160,200,255,1)';
      g.fillRect(348,c.y+15,Math.min(680,w*1.35),2);
      g.fillRect(348,c.y+23,Math.min(520,w*0.95),2);g.restore();
      d2(1180,c.y+2,3,'rgba(120,238,210,1)',.55*ra*q);
    }
  }
}
""")

F("p16", 9,
"""
<div class="apiwrap">
  <div class="api an" style="animation-delay:.35s">
    <div class="chip">POST</div>
    <div class="path">/search</div>
    <div class="body">{ "query": "…"<br>&nbsp;&nbsp;"lang": "auto" }</div>
    <div class="price">¥5 <span>/ 千次</span></div>
  </div>
  <div class="api an" style="animation-delay:.7s">
    <div class="chip">POST</div>
    <div class="path">/fetch</div>
    <div class="body">{ "url": "…"<br>&nbsp;&nbsp;"format": "md" }</div>
    <div class="price">¥5 <span>/ 千次</span></div>
  </div>
</div>
<div class="sub an" style="animation-delay:2.6s">
  <div class="idx">16 / 22 &nbsp;·&nbsp; 搜索 &nbsp;SEARCH</div>
  <div class="line">现在，搜索与抓取，<b>向所有人开放。</b></div>
</div>
""",
r"""
function draw(t){
  C();
  // 卡片背后的数据流线
  const p=eo(cl((t-1.4)/2.4));
  if(p>0.01){
    // 卡片上下的细导流线（不穿过卡片）
    for(let i=0;i<2;i++){
      const y=i?596:190;
      ln(120,y,1800,y,'rgba(100,150,225,1)',1,.055*p);
    }
    for(let k=0;k<6;k++){
      const ph=((t*0.18+k*0.17)%1);
      const x=lr(120,1800,ph);
      d2(x,k%2?596:190,1.8,'rgba(125,225,255,1)',.4*p);
    }
  }
}
""",
extra=r"""
.apiwrap{position:absolute;left:120px;top:226px;width:1680px;display:flex;gap:60px;z-index:8}
.api{position:relative;width:810px;height:330px;border:1px solid rgba(120,160,235,.20);
  border-radius:4px;background:linear-gradient(160deg,rgba(16,25,44,.72),rgba(8,12,22,.35));
  padding:34px 40px}
.chip{display:inline-block;font:600 15px/1 "SF Mono",Menlo,monospace;letter-spacing:.16em;
  color:#04121F;background:#7FE6FF;padding:7px 11px;border-radius:2px}
.path{position:absolute;left:150px;top:34px;font:500 40px/1 "SF Mono",Menlo,monospace;
  color:#EDF4FF;letter-spacing:-.01em}
.body{margin-top:80px;font:400 22px/1.75 "SF Mono",Menlo,monospace;color:#6E86A8}
.price{position:absolute;right:40px;bottom:30px;font:300 46px/1 -apple-system,sans-serif;
  color:#7FE6FF;letter-spacing:-.01em}
.price span{font-size:20px;color:#6E86A8;letter-spacing:.04em}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 17 · 开源
# ═══════════════════════════════════════════════════════════════════════════
F("p17", 8,
"""
<div class="wt">
  <div class="w1 an" style="animation-delay:1.5s">HuggingFace</div>
  <div class="w2 an" style="animation-delay:2.0s">ModelScope</div>
</div>
<div class="sub an" style="animation-delay:3.0s">
  <div class="idx">17 / 22 &nbsp;·&nbsp; 开源 &nbsp;OPEN WEIGHTS</div>
  <div class="line">权重也是。<b>拿得走，改得动。</b></div>
</div>
""",
r"""
function cube(cx,cy,s,ry,rx,al,col){
  const E=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]];
  const P=E.map(p=>proj(p[0]*s,p[1]*s,p[2]*s,ry,rx,1,cx,cy));
  const L=[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
  for(let i=0;i<L.length;i++){
    const a=P[L[i][0]],b=P[L[i][1]];
    const dep=(a[2]+b[2])/2;
    ln(a[0],a[1],b[0],b[1],col,1.5,al*(0.55-dep*0.0016));
  }
}
function draw(t){
  C();
  const cx=960,cy=400;
  const mv=eio(cl((t-0.2)/1.4));
  const ry=t*0.5;
  // 主方块
  if(mv>0){
    glow(cx,cy,260,'rgba(80,130,255,0.10)',0.7);
    cube(cx,cy,58,ry,0.5,0.75*mv,'rgba(150,200,255,1)');
  }
  // 分裂成两份
  const sp=eio(cl((t-1.5)/2.0));
  if(sp>0){
    const x1=lr(cx,520,sp),x2=lr(cx,1400,sp);
    cube(x1,cy+30,44,ry+sp*1.2,0.5,0.62*sp,'rgba(140,190,255,1)');
    cube(x2,cy+30,44,ry-sp*1.2,0.5,0.62*sp,'rgba(140,190,255,1)');
    // 连接的光路
    ln(cx,cy+30,x1+40,cy+30,'rgba(120,200,255,1)',1,.22*sp);
    ln(cx,cy+30,x2-40,cy+30,'rgba(120,200,255,1)',1,.22*sp);
    // 飞行中的数据点
    for(let k=0;k<8;k++){
      const ph=((t*0.6+k/8)%1);
      const u=eo(ph);
      d2(lr(cx,x1+40,u),cy+30+Math.sin(ph*Math.PI)*24,2,'rgba(170,235,255,1)',(1-ph)*0.7*sp);
      d2(lr(cx,x2-40,u),cy+30-Math.sin(ph*Math.PI)*24,2,'rgba(170,235,255,1)',(1-ph)*0.7*sp);
    }
  }
}
""",
extra=r"""
.wt{position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:8}
.w1,.w2{position:absolute;top:520px;width:420px;text-align:center;
  font:500 30px/1 -apple-system,"PingFang SC",sans-serif;letter-spacing:.02em;color:#DCE7F9}
.w1{left:310px}.w2{left:1190px}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 18 · 汇聚
# ═══════════════════════════════════════════════════════════════════════════
F("p18", 9,
"""
<div class="sub an" style="animation-delay:2.4s">
  <div class="idx">18 / 22 &nbsp;·&nbsp; 归 &nbsp;CONVERGE</div>
  <div class="line">所有这些，<b>回到一个句子开始的地方。</b></div>
</div>
""",
r"""
const RP=mul32(404);
const GLYPH=[];
for(let i=0;i<14;i++){
  const a=i/14*TAU-0.5;
  GLYPH.push({a:a,r:520+RP()*90,rot:(RP()-0.5)*2,type:i%5,sz:0.8+RP()*0.5});
}
function glyph(type,x,y,s,rot,al){
  g.save();g.translate(x,y);g.rotate(rot);g.scale(s,s);
  g.globalCompositeOperation='lighter';g.globalAlpha=al;
  g.strokeStyle='rgba(140,195,255,1)';g.lineWidth=1.6;
  if(type===0){
    for(let k=0;k<3;k++){const w=54-k*12,yy=-26+k*15;
      g.beginPath();g.moveTo(-w,yy);g.quadraticCurveTo(0,yy-15,w,yy);g.stroke();}
  }else if(type===1){
    g.beginPath();g.arc(0,0,32,0.4,5.0);g.stroke();
    g.beginPath();g.arc(0,0,18,1.2,5.8);g.stroke();
  }else if(type===2){
    g.beginPath();g.ellipse(-16,0,14,30,0,0,TAU);g.stroke();
    g.beginPath();g.ellipse(16,0,14,30,0,0,TAU);g.stroke();
  }else if(type===3){
    g.beginPath();g.moveTo(-40,12);
    for(let k=-40;k<=40;k+=5)g.lineTo(k,12-20*(Math.sin(k*0.06)*0.5+0.5));
    g.stroke();
  }else{
    g.beginPath();g.arc(0,0,30,0,TAU);g.stroke();
    g.beginPath();g.moveTo(0,-30);g.lineTo(0,30);g.stroke();
    g.beginPath();g.ellipse(0,0,30,12,0,0,TAU);g.stroke();
  }
  g.restore();
}
function draw(t){
  C();const cx=960,cy=540;
  const pull=eio(cl((t-1.4)/5.0));
  for(let i=0;i<GLYPH.length;i++){
    const q=GLYPH[i];
    const r=lr(q.r,0,pull);
    const a=q.a+pull*3.4;
    const x=cx+Math.cos(a)*r, y=cy+Math.sin(a)*r*0.72;
    const al=(1-pull*0.9)*(0.35+0.5*Math.sin(t*0.9+i)*0.5+0.25);
    if(al>0.02){
      glyph(q.type,x,y,q.sz*lerp1(pull),q.rot+pull*4,al*0.7);
      // 拖尾
      const x2=cx+Math.cos(a-0.06)*(r*1.03),y2=cy+Math.sin(a-0.06)*(r*1.03)*0.72;
      ln(x,y,x2,y2,'rgba(120,180,255,1)',1,al*0.25);
    }
  }
  function lerp1(p){return 1-p*0.75}
  // 中心的点
  const ca=eo(cl((t-5.9)/1.3));
  if(ca>0.01){
    glow(cx,cy,140,'rgba(90,140,255,0.28)',ca*.8);
    glow(cx,cy,26,'rgba(200,225,255,0.5)',ca);
    d2(cx,cy,3.2,'#EDF3FF',ca);
  }
  // 静止的尘埃（让画面不至于完全空掉）
  if(t>4.2){
    const RD=mul32(88);
    const da=eo(cl((t-4.2)/1.6));
    for(let i=0;i<70;i++){
      const a0=RD()*TAU, r0=90+RD()*330, sp2=0.04+RD()*0.05;
      const aa=a0+t*sp2;
      d2(cx+Math.cos(aa)*r0,cy+Math.sin(aa)*r0*0.7,1.1,'rgba(150,190,255,1)',(0.10+RD()*0.10)*da);
    }
  }
  // 汇聚的吸积环
  for(let k=0;k<3;k++){
    const q=cl((t-(5.6+k*0.45))/1.9);
    if(q>0&&q<1){
      g.save();g.globalCompositeOperation='lighter';g.globalAlpha=(1-q)*.35;
      g.strokeStyle='rgba(140,200,255,1)';g.lineWidth=1.2;
      g.beginPath();g.ellipse(cx,cy,lr(360,4,eo(q)),lr(260,3,eo(q)),0,0,TAU);g.stroke();g.restore();
    }
  }
}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 19 · 探索未至之境
# ═══════════════════════════════════════════════════════════════════════════
F("p19", 8,
"""
<div class="brandwrap">
  <div class="en an" style="animation-delay:.5s">DEEPSEEK</div>
  <div class="zh" id="zh">探索未至之境</div>
  <div class="sub2 an" style="animation-delay:2.6s">EXPLORE&nbsp;&nbsp;THE&nbsp;&nbsp;UNEXPLORED</div>
</div>
""",
r"""
function draw(t){
  C();const cx=960,cy=470;
  // 地平线
  const sw=eo(cl((t-0.2)/2.0));
  ln(cx-620*sw,cy+150,cx+620*sw,cy+150,'rgba(110,155,235,1)',1,.14*sw);
  // 背后的光
  const p=eo(cl((t-0.9)/2.6));
  glow(cx,cy,700,'rgba(60,110,230,0.10)',p*0.9);
  glow(cx,cy,300,'rgba(80,140,255,0.10)',p*0.7);
  // 光扫过文字
  const swp=cl((t-1.9)/2.4);
  if(swp>0&&swp<1){
    const x=lr(cx-760,cx+760,eio(swp));
    g.save();g.translate(x,cy-6);g.scale(1,0.62);
    glow(0,0,300,'rgba(125,190,255,0.16)',Math.sin(swp*Math.PI)*0.9);
    g.restore();
  }
  // 收尾：光点
  const d=eo(cl((t-4.8)/1.2));
  if(d>0.01){glow(cx,cy+268,60,'rgba(90,140,255,0.3)',d*.8);d2(cx,cy+268,2.6,'#DDEBFF',d);}
}
""",
extra=r"""
.brandwrap{position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:8;
  display:flex;flex-direction:column;align-items:center;justify-content:center}
.en{font:500 20px/1 "SF Mono",Menlo,monospace;letter-spacing:.62em;color:#5B78AE;
  margin-bottom:44px;padding-left:.62em}
.zh{font-size:118px;font-weight:600;letter-spacing:.16em;padding-left:.16em;
  color:#F4F8FF;text-shadow:0 0 60px rgba(90,140,255,.28)}
.sub2{font:500 17px/1 "SF Mono",Menlo,monospace;letter-spacing:.34em;color:#5D7BB0;
  margin-top:40px;padding-left:.34em}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 20 · 型号
# ═══════════════════════════════════════════════════════════════════════════
F("p20", 7,
"""
<div class="modwrap">
  <div class="date an" style="animation-delay:.4s">2026.10.17</div>
  <div class="model" id="model">V4.1-Flash-1017</div>
  <div class="rule" id="rule"></div>
  <div class="tagl an" style="animation-delay:2.2s">DeepSeek V4.1 Flash · 全量更新</div>
</div>
""",
r"""
function draw(t){
  C();const cx=960;
  // 垂直刻度尺
  const a=eo(cl((t-0.2)/1.6));
  for(let i=0;i<=40;i++){
    const x=lerp(120,1800,i/40);
    const h=i%5===0?16:7;
    ln(x,268,x,268+h,'rgba(110,155,230,1)',1,.18*a);
    ln(x,812-h,x,812,'rgba(110,155,230,1)',1,.18*a);
  }
  function lerp(a2,b2,u){return a2+(b2-a2)*u}
  // 横向光带
  const s=cl((t-1.1)/2.2);
  if(s>0&&s<1){
    const x=lr(120,1800,eio(s));
    ln(x,268,x,812,'rgba(140,210,255,1)',1.2,.28*(1-s));
    glow(x,540,320,'rgba(70,140,255,0.10)',.8*(1-s));
  }
  // 背景辉光
  glow(cx,540,760,'rgba(55,100,220,0.10)',eo(cl(t/2))*0.9);
  // 分隔线生长
  const rl=eo(cl((t-1.5)/1.6));
  $('rule').style.width=(520*rl)+'px';
  $('rule').style.opacity=String(rl);
}
""",
extra=r"""
.modwrap{position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:8;
  display:flex;flex-direction:column;align-items:center;justify-content:center}
.date{font:500 21px/1 "SF Mono",Menlo,monospace;letter-spacing:.42em;color:#7A93BE;
  margin-bottom:34px;padding-left:.42em}
.model{font:600 116px/1 -apple-system,"SF Pro Display",sans-serif;letter-spacing:-.028em;
  color:#F6F9FF;font-variant-numeric:tabular-nums;text-shadow:0 0 70px rgba(100,150,255,.30)}
.rule{width:0;height:1px;background:rgba(140,185,255,.75);margin-top:46px;box-shadow:0 0 12px rgba(110,160,255,.5)}
.tagl{margin-top:26px;font-size:26px;color:#8FA5C6;letter-spacing:.04em}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 21 · 三入口
# ═══════════════════════════════════════════════════════════════════════════
F("p21", 7,
"""
<div class="entries">
  <div class="en1 an" style="animation-delay:.35s"><span class="n">01</span><span class="t">网页端</span><span class="u">chat.deepseek.com</span></div>
  <div class="en1 an" style="animation-delay:.75s"><span class="n">02</span><span class="t">移动应用</span><span class="u">iOS / Android</span></div>
  <div class="en1 an" style="animation-delay:1.15s"><span class="n">03</span><span class="t">API</span><span class="u">platform.deepseek.com</span></div>
</div>
<div class="sub an" style="animation-delay:2.7s">
  <div class="idx">21 / 22 &nbsp;·&nbsp; 可用 &nbsp;AVAILABLE</div>
  <div class="line">网页端、APP、API，<b>同步更新。</b></div>
</div>
""",
r"""
function draw(t){
  C();
  // 三条轨道
  const a=eo(cl((t-0.2)/1.6));
  for(let i=0;i<3;i++){
    const y=352+i*136;
    ln(120,y+52,1800,y+52,'rgba(100,145,220,1)',1,.07*a);
    const ph=((t*0.25+i*0.33)%1);
    const x=lr(120,1800,ph);
    d2(x,y+52,2,'rgba(125,225,255,1)',.0*a);
  }
}
""",
extra=r"""
.entries{position:absolute;left:120px;top:300px;width:1700px;z-index:8}
.en1{position:relative;height:136px;display:flex;align-items:center}
.en1 .n{width:76px;font:500 16px/1 "SF Mono",Menlo,monospace;color:#46618C;letter-spacing:.16em}
.en1 .t{width:340px;font-size:52px;font-weight:600;color:#EFF4FE;letter-spacing:.01em}
.en1 .u{font:400 25px/1 "SF Mono",Menlo,monospace;color:#6E8DBC;letter-spacing:.01em}
""")

# ═══════════════════════════════════════════════════════════════════════════
# 22 · 尾卡
# ═══════════════════════════════════════════════════════════════════════════
F("p22", 9,
"""
<div class="endwrap">
  <div class="lg an" style="animation-delay:.4s">DeepSeek</div>
  <div class="sl an" style="animation-delay:.9s">探索未至之境</div>
  <div class="hr" id="hr"></div>
  <div class="meta an" style="animation-delay:1.9s">
    <div>权重开源 &nbsp;huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017</div>
    <div>权重开源 &nbsp;modelscope.cn/models/deepseek-ai/DeepSeek-V4.1-Flash-1017</div>
  </div>
</div>
<div class="fin an" style="animation-delay:2.6s">V4.1-Flash-1017&nbsp;&nbsp;·&nbsp;&nbsp;2026</div>
""",
r"""
function draw(t){
  C();const cx=960,cy=430;
  const a=eo(cl(t/1.6));
  glow(cx,cy-40,760,'rgba(55,105,225,0.10)',a*0.9);
  ln(760,cy+10,1160-a*0,cy+10,'rgba(0,0,0,0)',1,0);
  // 最后收束成一点
  const c=eo(cl((t-6.4)/1.6));
  if(c>0.01){
    glow(960,880,120,'rgba(80,130,255,0.22)',c*0.8);
    d2(960,880,2.6,'#DDEBFF',c);
  }
}
""",
extra=r"""
.endwrap{position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:8;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding-bottom:90px}
.lg{font:600 74px/1 -apple-system,"SF Pro Display",sans-serif;letter-spacing:-.02em;color:#F5F9FF}
.sl{margin-top:22px;font-size:25px;letter-spacing:.34em;color:#7E96BC;padding-left:.34em}
.hr{width:520px;height:1px;background:rgba(120,165,240,.22);margin:52px 0 40px}
.meta{display:flex;flex-direction:column;gap:14px;align-items:center;
  font:400 18px/1.5 "SF Mono",Menlo,monospace;color:#546C90;letter-spacing:.01em}
.fin{position:absolute;left:0;bottom:56px;width:1920px;text-align:center;
  font:500 16px/1 "SF Mono",Menlo,monospace;letter-spacing:.26em;color:#3E5474;z-index:8}
""")

# ─────────────────────────────────────────────────────────────── 清单
with open(os.path.join(HERE, "scenes.json"), "w", encoding="utf-8") as f:
    json.dump(SCENES, f, ensure_ascii=False, indent=2)

total = sum(s["seconds"] for s in SCENES)
print("frames:", len(SCENES), " raw total:", round(total, 1), "s",
      " after xfade:", round(total - 0.4 * (len(SCENES) - 1), 1), "s")
