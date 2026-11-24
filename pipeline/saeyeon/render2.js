// 느린 우체통 렌더러: engine.html + timeline.json → 30fps JPEG 프레임
// node render2.js <timeline.json> <out_dir> [full | t1,t2,...] [start_s] [end_s]
// 긴 영상은 구간을 나눠 여러 프로세스로 동시에 돌린다 (start_s~end_s).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const [, , tlPath, out, mode = 'full', s0, s1] = process.argv;
  const tl = JSON.parse(fs.readFileSync(tlPath));
  const fps = 30;
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.addInitScript(`window.TIMELINE=${JSON.stringify(tl)}`);
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + path.join(__dirname, 'engine.html'));
  await p.evaluate(() => document.fonts.ready);
  let frames;
  if (mode === 'full') {
    const a = Math.round((+s0 || 0) * fps), z = Math.round((s1 ? +s1 : tl.total) * fps);
    frames = []; for (let i = a; i < z; i++) frames.push([i, i / fps]);
  } else frames = mode.split(',').map((x, i) => [i, +x]);
  const t0 = Date.now();
  for (const [i, t] of frames) {
    await p.evaluate(t => window.render(t), t);
    await p.screenshot({ path: `${out}/${String(i).padStart(6, '0')}.jpg`, type: 'jpeg', quality: 90 });
    if (i % 300 === 0) console.log('frame', i, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  await b.close();
})();
