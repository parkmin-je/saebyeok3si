// 일러스트 HTML을 프레임 단위로 렌더해 ffmpeg로 넘긴다.
// 사용: node capture.cjs <scene.html> <timeline.json> <out.mp4> [fps]
// playwright는 전역 설치본을 쓴다: NODE_PATH=$(npm root -g)
const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const { readFileSync } = require("node:fs");
const { pathToFileURL } = require("node:url");
const path = require("node:path");

(async () => {

const [html, timelinePath, out, fpsArg] = process.argv.slice(2);
const fps = Number(fpsArg || 30);
const tl = JSON.parse(readFileSync(timelinePath, "utf8"));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve(html)).href);
await page.evaluate(() => window.ready);
await page.evaluate((scenes) => window.setTimeline(scenes), tl.scenes.map(s => ({ start: s.start, end: s.end })));
const total = await page.evaluate(() => window.DURATION);
const frames = Math.round(total * fps);

const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
  "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", out], { stdio: ["pipe", "inherit", "inherit"] });
const t0 = Date.now();
for (let i = 0; i < frames; i++) {
  await page.evaluate((t) => window.render(t), i / fps);
  const buf = await page.screenshot({ type: "jpeg", quality: 95 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  if (i % 150 === 0) console.log(`[frames] ${i}/${frames} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
ff.stdin.end();
await new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg " + c))));
await browser.close();
console.log(`[frames] 완료 ${frames}프레임`);
})().catch(e => { console.error(e); process.exit(1); });
