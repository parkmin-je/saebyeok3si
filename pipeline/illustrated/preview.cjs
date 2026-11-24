// 확인용 스틸 컷: node preview.cjs <scene.html> <outdir> t1 t2 ...
const { chromium } = require("playwright");
const { pathToFileURL } = require("node:url");
const path = require("node:path");
(async () => {
  const [html, outdir, ...ts] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on("pageerror", e => console.error("pageerror", e.message));
  await p.goto(pathToFileURL(path.resolve(html)).href);
  await p.evaluate(() => window.ready);
  for (const t of ts) { await p.evaluate(x => window.render(x), Number(t)); await p.screenshot({ path: `${outdir}/t${t}.jpg`, type: "jpeg", quality: 80 }); }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
