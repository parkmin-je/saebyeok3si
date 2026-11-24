const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [,, dir, mode] = process.argv;
  const tl = JSON.parse(fs.readFileSync(dir + '/timeline.json'));
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.addInitScript(`window.TIMELINE=${JSON.stringify(tl)}`);
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + dir + '/story.html');
  await p.evaluate(() => document.fonts.ready);
  const fps = 30;
  const times = mode === 'preview' ? [2, 8, 14, 22, 28, 36, 42, 50, 57] : [...Array(Math.ceil(tl.total * fps)).keys()].map(i => i / fps);
  fs.mkdirSync(dir + (mode === 'preview' ? '/prev' : '/frames'), { recursive: true });
  for (let i = 0; i < times.length; i++) {
    await p.evaluate(t => window.render(t), times[i]);
    const f = mode === 'preview' ? `${dir}/prev/${String(times[i]).padStart(2, '0')}.jpg` : `${dir}/frames/${String(i).padStart(5, '0')}.jpg`;
    await p.screenshot({ path: f, type: 'jpeg', quality: 92 });
  }
  await b.close();
})();
