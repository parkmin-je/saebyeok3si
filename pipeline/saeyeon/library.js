// 느린 우체통 장면 라이브러리.
// 장면 하나 = { build(o) → SVG 문자열 (viewBox 0 0 2040 1200), tick(root, t, p, o) → 움직임 }
//   t = 영상 전체 시각(초), p = 이 장면 안에서의 진행 0~1, o = 장면 옵션 {time: dawn|day|dusk|night, ...}
// 같은 시각이면 언제나 같은 그림 (난수는 시드 고정) → 프레임 단위로 다시 그려도 똑같다.

const SKY = {
  dawn: ['#1c2638', '#6f7f99', '#e8c3a0'],
  day: ['#7fb0d8', '#bcd8ec', '#f4ead6'],
  dusk: ['#2b2140', '#b0574a', '#f0a35e'],
  night: ['#0b1020', '#1c2640', '#38405a'],
};
const sky = (id, time) => {
  const c = SKY[time] || SKY.day;
  return `<linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c[0]}"/><stop offset=".6" stop-color="${c[1]}"/><stop offset="1" stop-color="${c[2]}"/></linearGradient>`;
};
const glow = (id, c = '#ffd890') =>
  `<radialGradient id="${id}"><stop offset="0" stop-color="${c}" stop-opacity=".9"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`;
const seeded = s => () => (s = (s * 16807) % 2147483647) / 2147483647;
const $$ = (root, id) => root.querySelector('#' + (root.dataset.px || '') + id);
const set = (el, a, v) => el && el.setAttribute(a, v);

// 사람 실루엣 (서 있는 어른). hat=true면 중절모, coat 색
const person = (id, {hat = false, fill = '#141821', bag = false, skirt = false} = {}) => `
 <g id="${id}" fill="${fill}">
  <ellipse cx="0" cy="-268" rx="30" ry="34"/>
  ${hat ? '<path d="M-46 -298 h92 l-10 -26 h-72z"/><rect x="-62" y="-302" width="124" height="10" rx="5"/>' : '<path d="M-32 -282 q32 -40 64 0 q-6 -30 -32 -32 q-26 2 -32 32z"/>'}
  ${skirt ? '<path d="M-54 -230 q54 -22 108 0 l30 200 h-168z"/><rect x="-30" y="-30" width="22" height="100"/><rect x="8" y="-30" width="22" height="100"/>'
          : '<path d="M-58 -230 q58 -22 116 0 l20 230 h-156z"/><rect x="-40" y="0" width="28" height="70"/><rect x="12" y="0" width="28" height="70"/>'}
  ${bag ? '<rect x="58" y="-130" width="44" height="70" rx="6" fill="#3a2d22"/>' : ''}
 </g>`;

const S = {};

// ───────── 우체통과 편지 (매 편 여는·닫는 장면) ─────────
S.mailbox = {
  build: o => `
  <defs>${sky('mb-sky', o.time || 'dusk')}${glow('mb-glow', '#ffe2a8')}
   <linearGradient id="mb-red" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9e1f1f"/><stop offset=".5" stop-color="#d23a2f"/><stop offset="1" stop-color="#8a1a1a"/></linearGradient>
   <linearGradient id="mb-paper" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbf3e0"/><stop offset="1" stop-color="#eadbb8"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="url(#mb-sky)"/>
  <path d="M0 820 Q500 760 1020 800 T2040 790 V1200 H0Z" fill="#3a2a2a"/>
  <rect x="0" y="900" width="2040" height="300" fill="#2a1e1e"/>
  <circle cx="1500" cy="420" r="260" fill="url(#mb-glow)" opacity=".55"/>
  <g id="mb-box" transform="translate(1020 0)">
   <rect x="-12" y="760" width="24" height="200" fill="#5a1414"/>
   <rect x="-150" y="420" width="300" height="360" rx="26" fill="url(#mb-red)"/>
   <path d="M-150 470 q150 -120 300 0 v-30 q-150 -110 -300 0z" fill="#b42a24"/>
   <rect x="-100" y="520" width="200" height="22" rx="11" fill="#3a0d0d"/>
   <text x="0" y="640" font-family="Myeongjo" font-size="56" fill="#ffe9c6" text-anchor="middle">우 체 통</text>
   <rect x="-60" y="680" width="120" height="40" rx="6" fill="#ffe9c6" opacity=".85"/>
   <text x="0" y="709" font-family="Gothic" font-size="24" fill="#8a1a1a" text-anchor="middle">느린 우편</text>
  </g>
  <g id="mb-letter">
   <rect x="-210" y="-130" width="420" height="260" rx="10" fill="url(#mb-paper)" stroke="#c9b48a" stroke-width="3"/>
   <path d="M-210 -130 L0 20 L210 -130" fill="none" stroke="#c9b48a" stroke-width="3"/>
   <rect x="120" y="-110" width="70" height="86" fill="#e8d4a2" stroke="#b9925a" stroke-width="2" stroke-dasharray="6 4"/>
   <circle cx="155" cy="-67" r="22" fill="none" stroke="#a3322a" stroke-width="3"/>
   <text id="mb-to" x="-170" y="70" font-family="Myeongjo" font-size="34" fill="#4a3a26">${o.to || '받는 사람: 당신께'}</text>
  </g>`,
  tick(r, t, p) {
    // 편지가 위에서 천천히 내려와 우체통 앞에 멈추고 살짝 흔들린다
    const k = Math.min(1, p * 1.6), e = 1 - Math.pow(1 - k, 3);
    set($$(r, 'mb-letter'), 'transform', `translate(${560 + e * 200} ${180 + e * 380}) rotate(${-14 + e * 10 + Math.sin(t * 1.4) * 1.5})`);
  },
};

// ───────── 시장 골목 (저녁, 불 켜진 가게) ─────────
S.alley = {
  build: o => `
  <defs>${sky('al-sky', o.time || 'dusk')}${glow('al-glow')}
   <linearGradient id="al-win" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe2a3"/><stop offset="1" stop-color="#f2a65a"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="url(#al-sky)"/>
  <g fill="#3b2a35" opacity=".85"><rect x="0" y="420" width="260" height="500"/><rect x="250" y="360" width="200" height="560"/><rect x="1580" y="380" width="230" height="540"/><rect x="1800" y="430" width="260" height="500"/><path d="M1580 380 L1695 330 L1810 380Z"/></g>
  <path d="M0 300 L560 470 L560 1200 L0 1200Z" fill="#231722"/>
  <path d="M2040 300 L1480 470 L1480 1200 L2040 1200Z" fill="#231722"/>
  <path d="M560 470 L1480 470 L1480 1200 L560 1200Z" fill="#2c1e1c"/>
  <path d="M560 1200 L860 760 L1180 760 L1480 1200Z" fill="#4a3528"/>
  <g stroke="#1a1015" stroke-width="5" opacity=".7"><line x1="0" y1="250" x2="2040" y2="210"/><line x1="0" y1="275" x2="2040" y2="300"/></g>
  <rect x="780" y="520" width="480" height="300" fill="#3a2620"/>
  <rect x="820" y="560" width="250" height="200" fill="url(#al-win)"/>
  <g stroke="#3a2620" stroke-width="8"><line x1="945" y1="560" x2="945" y2="760"/><line x1="820" y1="660" x2="1070" y2="660"/></g>
  <circle cx="880" cy="615" r="28" fill="none" stroke="#7a4a2a" stroke-width="6"/><circle cx="1010" cy="710" r="22" fill="none" stroke="#7a4a2a" stroke-width="5"/>
  <rect x="1100" y="580" width="120" height="240" fill="#21150f"/><rect x="1100" y="580" width="120" height="240" fill="url(#al-win)" opacity=".25"/>
  <rect x="800" y="480" width="440" height="50" fill="#5a3a26"/>
  <text x="1020" y="518" font-family="Gothic" font-size="34" fill="#f6dfb5" text-anchor="middle" letter-spacing="10">${o.sign || '시 계 수 리'}</text>
  <g id="al-lamp"><line x1="1290" y1="210" x2="1290" y2="430" stroke="#1a1015" stroke-width="4"/>
   <circle cx="1290" cy="460" r="200" fill="url(#al-glow)"/><path d="M1255 430 h70 l-12 55 h-46z" fill="#ffcf7a"/></g>
  <circle cx="700" cy="420" r="150" fill="url(#al-glow)" opacity=".6"/>
  ${person('al-walker', {hat: true, fill: '#120b0e'})}`,
  tick(r, t, p) {
    const x = 380 + p * 560, y = 1150 - p * 330 + Math.sin(t * 6.5) * 6 * (1 - p), s = 1 - p * 0.55;
    set($$(r, 'al-walker'), 'transform', `translate(${x} ${y}) scale(${s})`);
    set($$(r, 'al-lamp'), 'transform', `rotate(${Math.sin(t * 1.3) * 2.5} 1290 210)`);
  },
};

// ───────── 손목시계 클로즈업 (초침이 돈다) ─────────
S.watch = {
  build: o => {
    let ticks = '';
    for (let i = 0; i < 60; i++) { const L = i % 5 ? 14 : 34, w = i % 5 ? 3 : 8; ticks += `<rect x="${-w / 2}" y="-258" width="${w}" height="${L}" fill="#4a3b2a" transform="rotate(${i * 6})"/>`; }
    for (let h = 1; h <= 12; h++) { const a = (h * 30 - 90) * Math.PI / 180; ticks += `<text x="${Math.cos(a) * 195}" y="${Math.sin(a) * 195 + 16}" font-family="Myeongjo" font-size="46" fill="#3a2c1e" text-anchor="middle">${h}</text>`; }
    return `
  <defs><linearGradient id="wa-wood" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6b4226"/><stop offset="1" stop-color="#3b2314"/></linearGradient>
   <radialGradient id="wa-face" cx=".45" cy=".4"><stop offset="0" stop-color="#fffaf0"/><stop offset="1" stop-color="#e7d9bd"/></radialGradient>
   <radialGradient id="wa-spot" cx=".5" cy=".45"><stop offset="0" stop-color="#fff0c8" stop-opacity=".55"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
   <linearGradient id="wa-gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f5d48a"/><stop offset=".5" stop-color="#b88a3e"/><stop offset="1" stop-color="#f0cf86"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="url(#wa-wood)"/>
  <g stroke="#2e1a0e" stroke-width="3" opacity=".35"><path d="M0 200 q500 40 1020 0 t1020 10"/><path d="M0 520 q600 -30 1100 10 t940 -20"/><path d="M0 900 q500 30 1000 -10 t1040 20"/></g>
  <rect width="2040" height="1200" fill="url(#wa-spot)"/>
  <g transform="translate(1020 520) scale(.78)">
   <path d="M-150 -560 h300 l-20 330 h-260z" fill="#4a2b1a"/><path d="M-150 560 h300 l-20 -330 h-260z" fill="#4a2b1a"/>
   <circle r="300" fill="url(#wa-gold)"/><circle r="268" fill="url(#wa-face)"/>${ticks}
   <text y="-150" font-family="Myeongjo" font-size="34" fill="#5a4630" text-anchor="middle" letter-spacing="6">${o.year || '1974'}</text>
   <g id="wa-h"><rect x="-9" y="-140" width="18" height="160" rx="9" fill="#2a1d12"/></g>
   <g id="wa-m"><rect x="-6" y="-215" width="12" height="235" rx="6" fill="#2a1d12"/></g>
   <g id="wa-s"><rect x="-2.5" y="-240" width="5" height="290" fill="#a3322a"/><circle r="14" fill="#a3322a"/></g>
   <circle r="6" fill="#f0cf86"/><ellipse cx="-90" cy="-130" rx="120" ry="60" fill="#fff" opacity=".18" transform="rotate(-30)"/>
  </g>`;
  },
  tick(r, t) {
    const sec = t % 60;
    set($$(r, 'wa-s'), 'transform', `rotate(${Math.floor(sec) * 6})`);
    set($$(r, 'wa-m'), 'transform', `rotate(${(47 + sec / 60) * 6})`);
    set($$(r, 'wa-h'), 'transform', `rotate(${(5 + 47 / 60) * 30})`);
  },
};

// ───────── 시계 속 톱니 ─────────
const gearPath = (r, n, d) => {
  let s = '';
  for (let i = 0; i < n; i++) {
    const P = (a, rr) => `${(Math.cos(a) * rr).toFixed(1)} ${(Math.sin(a) * rr).toFixed(1)}`;
    const a0 = i / n * 2 * Math.PI, a1 = (i + .25) / n * 2 * Math.PI, a2 = (i + .5) / n * 2 * Math.PI, a3 = (i + .75) / n * 2 * Math.PI;
    s += (i ? 'L' : 'M') + P(a0, r) + ' L' + P(a1, r + d) + ' L' + P(a2, r + d) + ' L' + P(a3, r);
  }
  return s + 'Z';
};
const GEARS = [[1020, 600, 190, 30, 1, 'ge-brass'], [1300, 380, 110, 18, -1.7, 'ge-steel'], [760, 860, 140, 22, -1.36, 'ge-brass'], [1330, 840, 80, 14, 2.4, 'ge-brass'], [700, 380, 90, 16, 2.1, 'ge-steel']];
S.gears = {
  build: () => `
  <defs><radialGradient id="ge-dark" cx=".5" cy=".5"><stop offset="0" stop-color="#3b2d22"/><stop offset="1" stop-color="#120c08"/></radialGradient>
   <linearGradient id="ge-brass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f3d68f"/><stop offset=".6" stop-color="#b48535"/><stop offset="1" stop-color="#7d5a22"/></linearGradient>
   <linearGradient id="ge-steel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e6e6e6"/><stop offset="1" stop-color="#8b8f96"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="url(#ge-dark)"/>
  ${GEARS.map((g, i) => `<g id="ge-${i}" transform="translate(${g[0]} ${g[1]})"><path d="${gearPath(g[2], g[3], g[2] * .13)}" fill="url(#${g[5]})" stroke="#4a3415" stroke-width="3"/>
   <circle r="${g[2] * .62}" fill="#2a1e14" opacity=".55"/><circle r="${g[2] * .18}" fill="url(#${g[5]})"/>
   ${[0, 1, 2, 3, 4].map(k => `<rect x="-8" y="${-g[2] * .6}" width="16" height="${g[2] * .42}" fill="url(#${g[5]})" transform="rotate(${k * 72})"/>`).join('')}
   <circle r="10" fill="#a3322a"/></g>`).join('')}
  <circle cx="1020" cy="600" r="520" fill="none" stroke="#b48535" stroke-width="14" opacity=".5"/>`,
  tick(r, t) { GEARS.forEach((g, i) => set($$(r, 'ge-' + i), 'transform', `translate(${g[0]} ${g[1]}) rotate(${t * 14 * g[4]})`)); },
};

// ───────── 버스 정류장 (새벽 첫차) ─────────
S.busstop = {
  build: o => `
  <defs>${sky('bs-sky', o.time || 'dawn')}<radialGradient id="bs-head"><stop offset="0" stop-color="#fff4cf"/><stop offset="1" stop-color="#fff4cf" stop-opacity="0"/></radialGradient></defs>
  <rect width="2040" height="1200" fill="url(#bs-sky)"/>
  <g fill="#26303f"><rect x="0" y="560" width="2040" height="90"/><path d="M0 560 L120 470 L260 520 L420 430 L600 500 L800 440 L1000 510 L1240 420 L1460 500 L1700 450 L2040 520 V560Z"/></g>
  <rect x="0" y="650" width="2040" height="550" fill="#3d4553"/>
  <g stroke="#cfc6b0" stroke-width="10" stroke-dasharray="80 70" opacity=".6"><line x1="0" y1="900" x2="2040" y2="900"/></g>
  <g transform="translate(560 0)"><rect x="0" y="380" width="16" height="300" fill="#1d1f24"/><rect x="-60" y="330" width="140" height="70" rx="8" fill="#e8dcc0"/>
   <text x="10" y="377" font-family="Gothic" font-size="36" fill="#2b2b2b" text-anchor="middle">정 류 장</text></g>
  <g transform="translate(760 690)">${person('bs-man', {hat: true, bag: true})}</g>
  <g id="bs-bus"><rect x="0" y="560" width="520" height="260" rx="30" fill="#2d4a6b"/><rect x="30" y="600" width="400" height="90" fill="#cfd8e0" opacity=".85"/>
   <rect x="440" y="600" width="60" height="150" fill="#cfd8e0" opacity=".7"/><circle cx="110" cy="830" r="44" fill="#111"/><circle cx="410" cy="830" r="44" fill="#111"/>
   <circle cx="515" cy="770" r="140" fill="url(#bs-head)"/><rect x="40" y="570" width="200" height="26" fill="#e9d48a"/></g>
  ${o.year ? `<text id="bs-year" x="1840" y="160" font-family="Myeongjo" font-size="64" fill="#efe3c8" text-anchor="end" opacity=".85">${o.year}</text>` : ''}`,
  tick(r, t, p) {
    const e = x => x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
    set($$(r, 'bs-bus'), 'transform', `translate(${2100 - e(p) * 1100} 0)`);
    set($$(r, 'bs-man'), 'transform', `translate(${e(Math.max(0, (p - .55) / .45)) * 60} 0)`);
  },
};

// ───────── 해돋이 언덕 ─────────
S.sunrise = {
  build: o => `
  <defs><linearGradient id="sr-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3e5f8a"/><stop offset=".6" stop-color="#f3b07a"/><stop offset="1" stop-color="#ffe0b0"/></linearGradient>
   <radialGradient id="sr-sun"><stop offset="0" stop-color="#fff6d8"/><stop offset=".35" stop-color="#ffd27a"/><stop offset="1" stop-color="#ffb35a" stop-opacity="0"/></radialGradient></defs>
  <rect width="2040" height="1200" fill="url(#sr-sky)"/>
  <circle id="sr-ball" cx="1020" cy="820" r="420" fill="url(#sr-sun)"/>
  <path d="M0 860 Q300 720 620 820 T1260 790 T2040 840 V1200 H0Z" fill="#5a4a5e" opacity=".85"/>
  <path d="M0 960 Q400 860 900 940 T2040 920 V1200 H0Z" fill="#3a2f3e"/>
  ${o.wrist !== false ? `<g id="sr-wrist" fill="#1e1620"><path d="M-40 1200 L560 760 Q610 730 650 760 L700 800 Q720 840 690 870 L120 1200Z"/>
   <circle cx="610" cy="800" r="70" fill="#2a1f25" stroke="#e7b462" stroke-width="10"/>
   <line x1="610" y1="800" x2="610" y2="752" stroke="#e7b462" stroke-width="7"/><line x1="610" y1="800" x2="642" y2="808" stroke="#e7b462" stroke-width="7"/></g>` : ''}`,
  tick(r, t, p) {
    const e = 1 - Math.pow(1 - p, 2);
    set($$(r, 'sr-ball'), 'cy', 860 - e * 260);
    set($$(r, 'sr-wrist'), 'transform', `translate(${-80 + e * 60} ${40 - e * 40})`);
  },
};

// ───────── 시골집 마당 (감나무, 장독대, 평상) ─────────
S.countryhouse = {
  build: o => {
    const R = seeded(11); let persim = '';
    for (let i = 0; i < 26; i++) persim += `<circle cx="${1450 + (R() - .5) * 420}" cy="${330 + R() * 260}" r="${12 + R() * 6}" fill="#f08a24"/>`;
    return `
  <defs>${sky('ch-sky', o.time || 'day')}<linearGradient id="ch-ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d8c09a"/><stop offset="1" stop-color="#b89a70"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="url(#ch-sky)"/>
  <path d="M0 600 Q400 470 900 560 T2040 520 V700 H0Z" fill="#7d8f6a" opacity=".8"/>
  <rect x="0" y="680" width="2040" height="520" fill="url(#ch-ground)"/>
  <!-- 기와집 -->
  <g transform="translate(260 0)">
   <path d="M-40 430 Q400 330 840 430 L780 470 Q400 400 20 470Z" fill="#3c3f48"/>
   <path d="M20 470 h760 v40 h-760z" fill="#2c2e35"/>
   <rect x="60" y="510" width="680" height="240" fill="#efe2c8"/>
   <g fill="#8a6a46"><rect x="60" y="510" width="20" height="240"/><rect x="390" y="510" width="20" height="240"/><rect x="720" y="510" width="20" height="240"/></g>
   <g fill="#f7efdc" stroke="#8a6a46" stroke-width="6"><rect x="120" y="560" width="230" height="150"/><rect x="450" y="560" width="230" height="150"/></g>
   <g stroke="#b8a07a" stroke-width="3"><line x1="235" y1="560" x2="235" y2="710"/><line x1="120" y1="635" x2="350" y2="635"/><line x1="565" y1="560" x2="565" y2="710"/><line x1="450" y1="635" x2="680" y2="635"/></g>
   <rect x="40" y="750" width="720" height="40" fill="#9a7a52"/>
   <!-- 평상 -->
   <rect x="120" y="840" width="420" height="30" fill="#a27a4c"/><rect x="140" y="870" width="16" height="60" fill="#7a5a36"/><rect x="504" y="870" width="16" height="60" fill="#7a5a36"/>
  </g>
  <!-- 장독대 -->
  <g fill="#5a3a2a"><ellipse cx="1080" cy="880" rx="70" ry="80"/><ellipse cx="1190" cy="900" rx="56" ry="62"/><ellipse cx="1000" cy="905" rx="46" ry="52"/></g>
  <g fill="#3e2a1e"><ellipse cx="1080" cy="805" rx="50" ry="12"/><ellipse cx="1190" cy="842" rx="40" ry="10"/><ellipse cx="1000" cy="856" rx="32" ry="8"/></g>
  <!-- 감나무 -->
  <path d="M1460 980 q-20 -200 10 -400 M1470 700 q-120 -80 -200 -170 M1475 640 q120 -60 200 -160 M1468 560 q-40 -90 -10 -180" stroke="#4a3426" stroke-width="26" fill="none" stroke-linecap="round"/>
  <g id="ch-leaves" fill="#6b7a3e" opacity=".85"><ellipse cx="1450" cy="430" rx="260" ry="170"/><ellipse cx="1300" cy="520" rx="150" ry="100"/><ellipse cx="1620" cy="500" rx="150" ry="110"/></g>
  <g id="ch-persim">${persim}</g>
  ${o.person ? `<g transform="translate(820 940) scale(.9)">${person('ch-p', {fill: '#2a2220', skirt: o.person === 'woman'})}</g>` : ''}`;
  },
  tick(r, t) {
    set($$(r, 'ch-leaves'), 'transform', `translate(${Math.sin(t * .8) * 6} 0)`);
    set($$(r, 'ch-persim'), 'transform', `translate(${Math.sin(t * .8) * 6} 0)`);
  },
};

// ───────── 연탄 부엌 (아궁이, 양은 도시락, 김) ─────────
S.kitchen = {
  build: o => `
  <defs><radialGradient id="ki-light" cx=".7" cy=".25"><stop offset="0" stop-color="#fff0c8" stop-opacity=".7"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
   <radialGradient id="ki-fire"><stop offset="0" stop-color="#ffcf6a"/><stop offset=".5" stop-color="#e2582a"/><stop offset="1" stop-color="#4a120a" stop-opacity="0"/></radialGradient>
   <linearGradient id="ki-tin" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2f2f0"/><stop offset=".5" stop-color="#b9bcc0"/><stop offset="1" stop-color="#e6e6e4"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="#4a3a30"/>
  <rect x="0" y="0" width="2040" height="640" fill="#6a5646"/>
  <rect x="1300" y="120" width="420" height="300" fill="#d9e6ee"/><g stroke="#4a3a30" stroke-width="12"><line x1="1510" y1="120" x2="1510" y2="420"/><line x1="1300" y1="270" x2="1720" y2="270"/></g>
  <rect width="2040" height="1200" fill="url(#ki-light)"/>
  <rect x="0" y="640" width="2040" height="560" fill="#3a2c24"/>
  <!-- 아궁이와 연탄 -->
  <rect x="200" y="560" width="520" height="320" rx="20" fill="#5a4a40"/>
  <rect x="300" y="700" width="200" height="140" rx="60" fill="#1a1210"/>
  <circle id="ki-flame" cx="400" cy="790" r="110" fill="url(#ki-fire)"/>
  <g fill="#2a2420"><rect x="760" y="760" width="110" height="120" rx="10"/><rect x="760" y="640" width="110" height="120" rx="10"/></g>
  <g fill="#5a5450">${[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => `<circle cx="${785 + (i % 3) * 30}" cy="${670 + Math.floor(i / 3) * 30}" r="8"/>`).join('')}</g>
  <!-- 솥과 김 -->
  <ellipse cx="400" cy="560" rx="200" ry="40" fill="#2a2a2a"/><path d="M220 560 q180 120 360 0z" fill="#3a3a3a"/>
  <g id="ki-steam" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round" opacity=".35">
   <path d="M360 500 q-30 -60 0 -120 t0 -120"/><path d="M440 500 q30 -60 0 -120 t0 -120"/></g>
  <!-- 양은 도시락 -->
  <g transform="translate(1250 860)">
   <rect x="-200" y="-90" width="400" height="180" rx="22" fill="url(#ki-tin)" stroke="#8a8d92" stroke-width="4"/>
   <rect x="-200" y="-110" width="400" height="40" rx="14" fill="#d7d9dc" stroke="#8a8d92" stroke-width="4"/>
   <rect x="-120" y="-150" width="240" height="20" rx="10" fill="#8a8d92"/>
   <path d="M-150 20 q150 -30 300 0" fill="none" stroke="#9a9da2" stroke-width="3"/>
   ${o.egg ? '<g transform="translate(60 -100)"><ellipse rx="70" ry="44" fill="#fffaf0"/><circle r="26" fill="#f6b42a"/></g>' : ''}
  </g>
  ${o.person ? `<g transform="translate(1700 980)">${person('ki-p', {fill: '#2a1e1a', skirt: o.person === 'woman'})}</g>` : ''}`,
  tick(r, t) {
    set($$(r, 'ki-flame'), 'r', 105 + Math.sin(t * 7) * 6 + Math.sin(t * 13) * 4);
    set($$(r, 'ki-steam'), 'transform', `translate(${Math.sin(t * .9) * 12} ${-(t * 30 % 60)})`);
    set($$(r, 'ki-steam'), 'opacity', .25 + .1 * Math.sin(t * 1.7));
  },
};

// ───────── 기차역 플랫폼 (기차가 들어오고 떠난다) ─────────
S.station = {
  build: o => `
  <defs>${sky('st-sky', o.time || 'day')}</defs>
  <rect width="2040" height="1200" fill="url(#st-sky)"/>
  <path d="M0 520 Q500 420 1020 500 T2040 470 V600 H0Z" fill="#6e7c88" opacity=".7"/>
  <!-- 지붕 -->
  <path d="M0 120 L2040 120 L2040 190 L0 190Z" fill="#3e3a38"/>
  ${[0, 1, 2, 3, 4].map(i => `<rect x="${150 + i * 440}" y="190" width="22" height="560" fill="#4a4442"/>`).join('')}
  <rect x="0" y="700" width="2040" height="60" fill="#8a8078"/>
  <rect x="0" y="760" width="2040" height="440" fill="#6a625c"/>
  <g stroke="#2a2624" stroke-width="12"><line x1="0" y1="640" x2="2040" y2="640"/><line x1="0" y1="690" x2="2040" y2="690"/></g>
  <rect x="900" y="230" width="240" height="70" rx="8" fill="#f2ead6"/>
  <text x="1020" y="278" font-family="Myeongjo" font-size="40" fill="#2a2a2a" text-anchor="middle">${o.name || '서 울 역'}</text>
  <g id="st-train">
   <rect x="0" y="420" width="1500" height="250" rx="20" fill="${o.color || '#2f5a46'}"/>
   <rect x="0" y="600" width="1500" height="30" fill="#e6d29a"/>
   ${[0, 1, 2, 3, 4, 5, 6].map(i => `<rect x="${60 + i * 200}" y="460" width="150" height="100" rx="10" fill="#e8eef0" opacity=".9"/>`).join('')}
   ${[0, 1, 2, 3, 4, 5].map(i => `<circle cx="${140 + i * 240}" cy="680" r="40" fill="#1a1a1a"/>`).join('')}
  </g>
  <g transform="translate(1500 1020)">${person('st-p', {fill: '#1e1c22', hat: !!o.hat, bag: true})}</g>
  ${o.bike ? `<g transform="translate(1200 1010)" fill="none" stroke="#1e1c22" stroke-width="10"><circle cx="-110" cy="0" r="80"/><circle cx="110" cy="0" r="80"/><path d="M-110 0 L-20 -110 L90 -110 L110 0 M-20 -110 L0 0 L-110 0 M90 -110 L100 -150 h40"/><path d="M-30 -130 h-50"/></g>` : ''}`,
  tick(r, t, p, o) {
    // 들어와서 멈췄다가(가운데) 떠난다
    const arrive = Math.min(1, p / .35), leave = Math.max(0, (p - .7) / .3);
    const x = (o.leave ? -1 : 0) * 0 + (1 - (1 - Math.pow(1 - arrive, 3))) * 2100 - Math.pow(leave, 2) * 2300 + 270;
    set($$(r, 'st-train'), 'transform', `translate(${x} ${Math.sin(t * 20) * (arrive < 1 || leave > 0 ? 2 : 0)})`);
  },
};

// ───────── 바닷가 (파도, 갈매기) ─────────
S.sea = {
  build: o => `
  <defs>${sky('se-sky', o.time || 'dusk')}<linearGradient id="se-water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a6a8a"/><stop offset="1" stop-color="#1e3048"/></linearGradient>
   ${glow('se-sun', '#ffd27a')}</defs>
  <rect width="2040" height="1200" fill="url(#se-sky)"/>
  <circle cx="1400" cy="560" r="220" fill="url(#se-sun)"/>
  <rect x="0" y="600" width="2040" height="600" fill="url(#se-water)"/>
  <g id="se-waves" fill="none" stroke="#cfe0ee" stroke-width="5" opacity=".5">
   ${[0, 1, 2, 3, 4, 5].map(i => `<path d="M-200 ${660 + i * 60} q100 -18 200 0 t200 0 t200 0 t200 0 t200 0 t200 0 t200 0 t200 0 t200 0 t200 0 t200 0 t200 0"/>`).join('')}</g>
  <path d="M0 960 Q600 880 1200 940 T2040 920 V1200 H0Z" fill="#d8c4a0"/>
  <path id="se-foam" d="M0 950 Q600 870 1200 930 T2040 910" fill="none" stroke="#fff" stroke-width="10" opacity=".6"/>
  <g id="se-gull" fill="none" stroke="#2a2a34" stroke-width="6" stroke-linecap="round"><path d="M-30 0 q15 -18 30 0 q15 -18 30 0"/></g>
  ${o.person ? `<g transform="translate(700 1080) scale(.9)">${person('se-p', {fill: '#1e1a24', skirt: o.person === 'woman'})}</g>` : ''}
  ${o.person2 ? `<g transform="translate(840 1090) scale(.85)">${person('se-p2', {fill: '#1e1a24', hat: true})}</g>` : ''}`,
  tick(r, t) {
    set($$(r, 'se-waves'), 'transform', `translate(${(t * 40) % 200 - 100} ${Math.sin(t) * 6})`);
    set($$(r, 'se-foam'), 'opacity', .45 + .2 * Math.sin(t * 1.3));
    set($$(r, 'se-gull'), 'transform', `translate(${300 + (t * 60) % 1700} ${300 + Math.sin(t * .7) * 40}) scale(${1 + .1 * Math.sin(t * 6)} 1)`);
  },
};

// ───────── 다방 (창가 자리, 커피잔 김, 레코드) ─────────
S.dabang = {
  build: o => `
  <defs>${sky('da-sky', o.time || 'day')}<radialGradient id="da-lamp"><stop offset="0" stop-color="#ffd9a0" stop-opacity=".8"/><stop offset="1" stop-color="#ffd9a0" stop-opacity="0"/></radialGradient></defs>
  <rect width="2040" height="1200" fill="#5a3a2c"/>
  <rect x="0" y="0" width="2040" height="760" fill="#7a5038"/>
  <g fill="#6a4430">${[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => `<rect x="${i * 210}" y="0" width="8" height="760"/>`).join('')}</g>
  <rect x="1180" y="240" width="640" height="400" fill="url(#da-sky)"/>
  <g stroke="#3a2418" stroke-width="16"><rect x="1180" y="240" width="640" height="400" fill="none"/><line x1="1500" y1="240" x2="1500" y2="640"/></g>
  <rect x="1340" y="150" width="320" height="64" rx="8" fill="#3a2418"/><text x="1500" y="197" font-family="Myeongjo" font-size="42" fill="#f2dcb4" text-anchor="middle">${o.name || '청 춘 다 방'}</text>
  <circle cx="560" cy="200" r="260" fill="url(#da-lamp)"/>
  <path d="M520 120 h80 l40 80 h-160z" fill="#e8b86a"/><line x1="560" y1="0" x2="560" y2="120" stroke="#2a1a12" stroke-width="4"/>
  <!-- 탁자와 커피잔 -->
  <ellipse cx="980" cy="860" rx="520" ry="90" fill="#3a2418"/><rect x="960" y="860" width="40" height="300" fill="#2a1810"/>
  <g transform="translate(860 800)"><ellipse cx="0" cy="34" rx="90" ry="20" fill="#f2ece0"/><path d="M-56 -40 h112 l-12 70 h-88z" fill="#f7f2e8"/><path d="M56 -26 q40 0 30 30 q-8 20 -36 18" fill="none" stroke="#f7f2e8" stroke-width="12"/>
   <ellipse cx="0" cy="-40" rx="56" ry="12" fill="#5a3418"/>
   <g id="da-steam" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" opacity=".35"><path d="M-14 -60 q-20 -40 0 -80 t0 -80"/><path d="M18 -60 q20 -40 0 -80 t0 -80"/></g></g>
  <g transform="translate(1120 800)"><ellipse cx="0" cy="34" rx="90" ry="20" fill="#f2ece0"/><path d="M-56 -40 h112 l-12 70 h-88z" fill="#f7f2e8"/><ellipse cx="0" cy="-40" rx="56" ry="12" fill="#5a3418"/></g>
  <!-- 레코드 -->
  <g transform="translate(260 760)"><rect x="-150" y="-30" width="300" height="200" rx="10" fill="#4a2e20"/>
   <g id="da-lp"><circle r="110" cy="-30" fill="#141414"/><circle r="36" cy="-30" fill="#c23a2a"/><circle r="70" cy="-30" fill="none" stroke="#2a2a2a" stroke-width="3"/></g></g>`,
  tick(r, t) {
    set($$(r, 'da-steam'), 'transform', `translate(${Math.sin(t) * 8} ${-(t * 24 % 40)})`);
    set($$(r, 'da-lp'), 'transform', `rotate(${t * 200} 0 -30)`);
  },
};

// ───────── 교실 (난로 위 도시락, 칠판) ─────────
S.classroom = {
  build: o => `
  <defs><linearGradient id="cl-win" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfe2ee"/><stop offset="1" stop-color="#f6efe0"/></linearGradient>
   <radialGradient id="cl-heat"><stop offset="0" stop-color="#ff9a4a" stop-opacity=".6"/><stop offset="1" stop-color="#ff9a4a" stop-opacity="0"/></radialGradient></defs>
  <rect width="2040" height="1200" fill="#d8c8aa"/>
  <rect x="0" y="760" width="2040" height="440" fill="#9a7a56"/>
  <g stroke="#8a6a46" stroke-width="3" opacity=".5">${[0, 1, 2, 3, 4, 5, 6].map(i => `<line x1="0" y1="${800 + i * 60}" x2="2040" y2="${800 + i * 60}"/>`).join('')}</g>
  <rect x="160" y="160" width="900" height="440" fill="#2e4a3a" stroke="#7a5a3a" stroke-width="24"/>
  <text x="610" y="300" font-family="Myeongjo" font-size="56" fill="#e8f0e0" text-anchor="middle">${o.board || '오늘의 당번'}</text>
  <text x="610" y="400" font-family="Myeongjo" font-size="44" fill="#e8f0e0" text-anchor="middle" opacity=".85">${o.board2 || ''}</text>
  <rect x="1280" y="140" width="600" height="420" fill="url(#cl-win)" stroke="#7a5a3a" stroke-width="16"/>
  <line x1="1580" y1="140" x2="1580" y2="560" stroke="#7a5a3a" stroke-width="12"/>
  <!-- 난로와 쌓인 도시락 -->
  <circle cx="1020" cy="800" r="260" fill="url(#cl-heat)"/>
  <rect x="940" y="740" width="160" height="200" rx="20" fill="#2a2420"/><rect x="1000" y="300" width="40" height="440" fill="#4a4440"/>
  <g id="cl-boxes">${[0, 1, 2, 3].map(i => `<rect x="${955 + (i % 2) * 6}" y="${700 - i * 38}" width="130" height="36" rx="6" fill="#c8cacc" stroke="#8a8d92" stroke-width="3"/>`).join('')}</g>
  <!-- 책상들 -->
  ${[0, 1, 2, 3].map(i => `<g transform="translate(${200 + i * 470} 980)"><rect x="-130" y="-40" width="260" height="30" fill="#b8925e"/><rect x="-110" y="-10" width="16" height="140" fill="#6a4a2e"/><rect x="94" y="-10" width="16" height="140" fill="#6a4a2e"/></g>`).join('')}`,
  tick(r, t) { set($$(r, 'cl-boxes'), 'transform', `translate(0 ${Math.sin(t * 2) * 1.5})`); },
};

// ───────── 눈 내리는 밤길 (가로등, 발자국) ─────────
S.snowroad = {
  build: o => `
  <defs>${sky('sn-sky', 'night')}${glow('sn-lamp', '#ffe2a8')}</defs>
  <rect width="2040" height="1200" fill="url(#sn-sky)"/>
  <g fill="#1a2030"><rect x="0" y="480" width="400" height="360"/><rect x="380" y="430" width="300" height="410"/><rect x="1480" y="460" width="320" height="380"/><rect x="1780" y="500" width="300" height="340"/></g>
  <g fill="#ffd98a" opacity=".8"><rect x="80" y="560" width="60" height="70"/><rect x="460" y="520" width="60" height="70"/><rect x="1560" y="560" width="60" height="70"/><rect x="1860" y="600" width="60" height="70"/></g>
  <path d="M0 840 L2040 840 L2040 1200 L0 1200Z" fill="#dfe6ee"/>
  <path d="M700 1200 L960 840 L1080 840 L1340 1200Z" fill="#c8d2de"/>
  <g transform="translate(1320 0)"><rect x="-10" y="420" width="20" height="440" fill="#1e2230"/><path d="M-10 430 q-60 0 -60 40" fill="none" stroke="#1e2230" stroke-width="12"/>
   <circle cx="-70" cy="490" r="260" fill="url(#sn-lamp)"/><rect x="-95" y="465" width="50" height="40" rx="8" fill="#ffe8b8"/></g>
  <g fill="#aab6c4">${[0, 1, 2, 3, 4, 5, 6, 7].map(i => `<ellipse cx="${1000 + (i % 2 ? 22 : -22) + i * 4}" cy="${1180 - i * 42}" rx="${14 - i}" ry="${8 - i * .6}"/>`).join('')}</g>
  ${o.person ? `<g transform="translate(1030 900) scale(.55)">${person('sn-p', {fill: '#141a26', hat: o.person === 'man'})}</g>` : ''}`,
  tick() {},
};

// 장면에 공통으로 얹는 눈 (o.snow) — 엔진이 쓴다
const snowLayer = n => {
  const R = seeded(5); let s = '';
  for (let i = 0; i < n; i++) s += `<circle class="flake" data-x="${R() * 2040}" data-y="${R() * 1200}" data-v="${40 + R() * 60}" data-w="${R() * 6.28}" r="${3 + R() * 5}" fill="#fff" opacity="${.5 + R() * .5}"/>`;
  return s;
};
const tickSnow = (g, t) => g.querySelectorAll('.flake').forEach(f => {
  const x = +f.dataset.x + Math.sin(t * .8 + +f.dataset.w) * 30, y = (+f.dataset.y + t * +f.dataset.v) % 1260 - 30;
  f.setAttribute('cx', x); f.setAttribute('cy', y);
});

window.SCENE_LIBRARY = S;
window.SNOW = {snowLayer, tickSnow};
