// README 그림을 PNG로 굽는다: node assets/readme/render.js
const {chromium} = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({deviceScaleFactor: 1});
  const url = 'file://' + path.join(__dirname, 'art.html');
  for (const [m, w, h] of [['banner', 1600, 720], ['kong', 480, 480], ['cat', 480, 480], ['bot2', 480, 480], ['sis', 480, 480]]) {
    await p.setViewportSize({width: w, height: h});
    await p.goto(url + '#' + m);
    await p.reload();
    await p.waitForTimeout(400);
    await p.screenshot({path: path.join(__dirname, m + '.png'), clip: {x: 0, y: 0, width: w, height: h}});
  }
  await b.close();
})();
