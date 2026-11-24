// "만약에 ~라면?" 쇼츠 장면. library.js 의 sky·glow·person·$$·set·S 를 그대로 쓴다.
// window.SPEAK = 지금 말하는 인물(who). 강아지는 자기 차례에 입을 움직인다.

// 앉아 있는 강아지 (오른쪽을 봄). 원점 = 발 밑 가운데, 키 약 420
const dog = (id, {fill = '#d98a43', chest = '#fbeedd', tie = false, vest = false, gray = false, scale = 1} = {}) => `
 <g id="${id}" transform="scale(${scale})">
  <g id="${id}-tail" transform="translate(-120 -90)">
   <path d="M0 0 q-90 -40 -60 -150 q20 -40 50 -10 q-30 60 30 120z" fill="${fill}"/>
   <path d="M-52 -150 q20 -40 46 -12 q-24 10 -30 30z" fill="${chest}"/>
  </g>
  <path d="M-150 0 q-30 -190 60 -250 q90 -50 170 10 q60 60 40 240z" fill="${fill}"/>
  <path d="M10 -240 q70 30 60 150 q-10 60 -40 90 h-60 q-20 -130 40 -240z" fill="${chest}"/>
  <rect x="-10" y="-120" width="44" height="120" rx="22" fill="${fill}"/>
  <rect x="50" y="-120" width="44" height="120" rx="22" fill="${fill}"/>
  <ellipse cx="12" cy="-4" rx="30" ry="12" fill="${chest}"/><ellipse cx="72" cy="-4" rx="30" ry="12" fill="${chest}"/>
  ${vest ? `<path d="M-120 -200 q100 -40 190 0 l10 130 h-210z" fill="#2f5d9a"/><rect x="-80" y="-170" width="120" height="44" rx="8" fill="#f5d34a"/>
   <text x="-20" y="-138" font-family="Gothic" font-size="30" fill="#1d2a44" text-anchor="middle">보안</text>` : ''}
  <g id="${id}-head" transform="translate(40 -300)">
   <path d="M-100 -40 l-10 -130 l90 70z" fill="${fill}"/><path d="M-90 -60 l-6 -80 l50 45z" fill="#f2b9a0"/>
   <path d="M40 -90 l60 -110 l30 140z" fill="${fill}"/><path d="M60 -90 l36 -70 l18 86z" fill="#f2b9a0"/>
   <ellipse cx="0" cy="0" rx="130" ry="115" fill="${fill}"/>
   <path d="M-40 30 q50 90 170 30 q20 -40 -10 -60 q-80 -10 -160 30z" fill="${chest}"/>
   ${gray ? '<path d="M-30 40 q60 70 150 20 q10 -30 -10 -40 q-70 0 -140 20z" fill="#e8e4df"/>' : ''}
   <ellipse cx="-70" cy="20" rx="34" ry="26" fill="${chest}"/>
   <g id="${id}-eyes"><ellipse cx="-10" cy="-20" rx="17" ry="20" fill="#1d140e"/><ellipse cx="74" cy="-24" rx="15" ry="19" fill="#1d140e"/>
    <circle cx="-4" cy="-28" r="6" fill="#fff"/><circle cx="79" cy="-31" r="5" fill="#fff"/></g>
   <path d="M-40 -58 q30 -16 52 -2" stroke="#8a5428" stroke-width="7" fill="none" stroke-linecap="round"/>
   <ellipse cx="128" cy="12" rx="24" ry="17" fill="#1d140e"/>
   <g id="${id}-jaw" transform="translate(96 46)"><path d="M-40 0 q40 0 60 -6 q-4 30 -30 34 q-26 0 -30 -28z" fill="#7a2a2a"/>
    <ellipse cx="-12" cy="16" rx="16" ry="9" fill="#e86f7a"/></g>
   <path d="M128 28 q-6 22 -30 18 M98 46 q-30 6 -50 -10" stroke="#3a2416" stroke-width="6" fill="none" stroke-linecap="round"/>
  </g>
  <path d="M-60 -210 q100 40 190 -10" stroke="#c8352c" stroke-width="20" fill="none" stroke-linecap="round"/>
  <circle cx="44" cy="-188" r="16" fill="#f2c24a"/>
  ${tie ? '<path d="M44 -196 l-20 20 l20 110 l20 -110z" fill="#2c3f7a"/><path d="M34 -200 h20 l-10 22z" fill="#1d2a52"/>' : ''}
 </g>`;

function tickDog(root, id, t, seed = 0) {
  const tail = $$(root, id + '-tail');
  if (tail) set(tail, 'transform', `translate(-120 -90) rotate(${Math.sin(t * 9 + seed) * 16})`);
  const head = $$(root, id + '-head');
  const talking = window.SPEAK === 'dog' && !window.SPEAK_OFF;
  const bob = talking ? Math.sin(t * 7) * 4 : Math.sin(t * 1.3 + seed) * 3;
  if (head) set(head, 'transform', `translate(40 ${-300 + bob}) rotate(${Math.sin(t * .9 + seed) * 3})`);
  const jaw = $$(root, id + '-jaw');
  const open = talking ? Math.max(0, Math.sin(t * 15) * .6 + Math.sin(t * 6.3) * .5) : 0;
  if (jaw) set(jaw, 'transform', `translate(96 ${46 + open * 26}) scale(1 ${.4 + open})`);
  const eyes = $$(root, id + '-eyes');
  const blink = ((t + seed * 1.7) % 3.6) < .12;
  if (eyes) set(eyes, 'transform', blink ? 'translate(0 -22) scale(1 .1) translate(0 22)' : '');
}

// 앉은 사람 (소파 위). old=true면 흰머리·지팡이
const sitter = (id, {fill = '#2b2430', old = false} = {}) => `
 <g id="${id}" fill="${fill}">
  <circle cx="0" cy="-330" r="44" fill="${old ? '#3a3236' : fill}"/>
  ${old ? '<path d="M-44 -340 q44 -60 88 0 q-10 -40 -44 -44 q-34 4 -44 44z" fill="#d9d4cf"/>' : '<path d="M-46 -330 q46 -64 92 0 q-8 -46 -46 -50 q-38 4 -46 50z"/>'}
  <path d="M-70 -280 q70 -30 140 0 l16 170 h-172z"/>
  <path d="M-80 -120 h200 q30 0 30 30 v20 h-230z"/>
  <rect x="110" y="-90" width="34" height="150" rx="14"/>
  ${old ? '<path d="M180 -150 v210" stroke="#5a4030" stroke-width="10"/>' : ''}
 </g>`;

// ───────── 거실 (첫날 아침 / 10년 뒤 저녁) ─────────
S.wf_home = {
  build: o => {
    const eve = o.time === 'dusk' || o.time === 'night';
    return `
  <defs>${sky('wh-sky', o.time || 'day')}${glow('wh-glow', eve ? '#ffcf8a' : '#fff1c8')}
   <linearGradient id="wh-wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${eve ? '#4a3a40' : '#f3e6d0'}"/><stop offset="1" stop-color="${eve ? '#5e4848' : '#e8d4b4'}"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="url(#wh-wall)"/>
  <rect x="1180" y="150" width="620" height="460" rx="10" fill="url(#wh-sky)"/>
  <path d="M1180 150 h620 v460 h-620z M1490 150 v460 M1180 380 h620" stroke="${eve ? '#2e2228' : '#fff'}" stroke-width="18" fill="none"/>
  ${eve ? '<circle cx="1640" cy="260" r="40" fill="#fff6dc" opacity=".9"/>' : '<circle cx="1640" cy="250" r="60" fill="#fff6c0" opacity=".85"/>'}
  <rect x="0" y="880" width="2040" height="320" fill="${eve ? '#3a2a24' : '#c99a6a'}"/>
  <path d="M0 880 h2040" stroke="${eve ? '#2a1e1a' : '#a87a50'}" stroke-width="10"/>
  <ellipse cx="1100" cy="1060" rx="520" ry="70" fill="${eve ? '#5a3030' : '#b5523f'}" opacity=".8"/>
  <g transform="translate(330 0)"><rect x="0" y="600" width="640" height="300" rx="40" fill="${eve ? '#6a4a3a' : '#7a9a8a'}"/>
   <rect x="-30" y="560" width="80" height="340" rx="36" fill="${eve ? '#5a3c30' : '#6a8a7a'}"/><rect x="590" y="560" width="80" height="340" rx="36" fill="${eve ? '#5a3c30' : '#6a8a7a'}"/>
   <rect x="40" y="480" width="560" height="160" rx="40" fill="${eve ? '#7a5644' : '#8aaa9a'}"/></g>
  ${eve ? `<g transform="translate(1660 0)"><rect x="-6" y="420" width="12" height="470" fill="#2a2020"/><path d="M-90 420 h180 l-40 -120 h-100z" fill="#f6d49a"/>
   <circle cx="0" cy="430" r="300" fill="url(#wh-glow)" opacity=".55"/></g>` : `<circle cx="1500" cy="380" r="520" fill="url(#wh-glow)" opacity=".35"/>`}
  <g transform="translate(640 880)">${sitter('wh-p', {old: !!o.old, fill: eve ? '#4a3c46' : '#3a3442'})}</g>
  <g id="wh-dog" transform="translate(1180 1010)">${dog('wh-d', {gray: !!o.old})}</g>
  ${o.bowl ? '<g transform="translate(1560 1010)"><ellipse rx="90" ry="26" fill="#3a6aa8"/><path d="M-90 0 q90 60 180 0" fill="#2a5a98"/></g>' : ''}`;
  },
  tick: (root, t) => tickDog(root, 'wh-d', t),
};

// ───────── 뉴스 스튜디오 (강아지 앵커) ─────────
S.wf_news = {
  build: o => `
  <defs><radialGradient id="wn-bg" cx=".5" cy=".4" r=".8"><stop offset="0" stop-color="#2a5ab0"/><stop offset="1" stop-color="#0b1a3a"/></radialGradient></defs>
  <rect width="2040" height="1200" fill="url(#wn-bg)"/>
  <g stroke="#6fa0ff" stroke-width="3" fill="none" opacity=".35"><circle cx="1020" cy="430" r="300"/><ellipse cx="1020" cy="430" rx="130" ry="300"/><path d="M720 430 h600 M760 290 h520 M760 570 h520"/></g>
  <rect x="1180" y="170" width="480" height="300" rx="14" fill="#0e1c38" stroke="#9cc0ff" stroke-width="6"/>
  <text x="1420" y="270" font-family="Gothic" font-size="62" fill="#ff5a4a" text-anchor="middle">속 보</text>
  <text x="1420" y="370" font-family="Gothic" font-size="40" fill="#fff" text-anchor="middle">${o.screen || '강아지, 말 시작'}</text>
  <g id="wn-dog" transform="translate(860 860)">${dog('wn-d', {tie: true})}</g>
  <path d="M300 760 h1440 l-80 260 h-1280z" fill="#e8eef8"/><path d="M300 760 h1440 v40 h-1440z" fill="#c03a30"/>
  <text x="1020" y="900" font-family="Gothic" font-size="56" fill="#1a2a4a" text-anchor="middle">멍멍 뉴스</text>
  <rect x="0" y="1060" width="2040" height="100" fill="#c03a30"/>
  <rect x="0" y="1060" width="260" height="100" fill="#8a1e18"/><text x="130" y="1128" font-family="Gothic" font-size="46" fill="#fff" text-anchor="middle">LIVE</text>
  <svg x="260" y="1060" width="1780" height="100"><text id="wn-tk" x="1800" y="68" font-family="Gothic" font-size="48" fill="#fff">${o.ticker || ''}</text></svg>`,
  tick: (root, t, p) => {
    tickDog(root, 'wn-d', t, 1);
    set($$(root, 'wn-tk'), 'x', 1800 - ((t * 260) % 4200));
  },
};

// ───────── 공항 보안 검색대 ─────────
S.wf_airport = {
  build: o => `
  <defs><linearGradient id="wa-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#dfe6ee"/><stop offset="1" stop-color="#b9c4d0"/></linearGradient></defs>
  <rect width="2040" height="1200" fill="url(#wa-bg)"/>
  <g fill="#cfd8e2">${[0, 1, 2, 3, 4, 5].map(i => `<rect x="${60 + i * 340}" y="60" width="300" height="420" rx="6"/>`).join('')}</g>
  <rect x="1120" y="130" width="520" height="110" rx="12" fill="#f5c400"/><text x="1380" y="206" font-family="Gothic" font-size="64" fill="#1a1a1a" text-anchor="middle">보안 검색</text>
  <g fill="#7a8696" opacity=".8">${[0, 1, 2].map(i => `<g transform="translate(${1500 + i * 150} 900) scale(.8)">${person('wa-q' + i, {fill: '#6a7686', bag: i === 1})}</g>`).join('')}</g>
  <rect x="0" y="880" width="2040" height="320" fill="#9aa6b4"/>
  <rect x="200" y="700" width="1240" height="70" rx="10" fill="#3a4250"/>
  <rect x="560" y="470" width="360" height="300" rx="20" fill="#5a6474"/><rect x="600" y="510" width="280" height="240" rx="10" fill="#1e2430"/>
  <svg x="200" y="560" width="1240" height="140"><g id="wa-bags">
   ${[0, 1, 2, 3].map(i => `<g transform="translate(${i * 380} 0)"><rect x="0" y="30" width="220" height="110" rx="16" fill="${['#c0503a', '#3a6aa8', '#4a8a5a', '#8a5aa8'][i]}"/><rect x="80" y="10" width="60" height="26" rx="8" fill="none" stroke="#222" stroke-width="8"/></g>`).join('')}</g></svg>
  <g id="wa-dog" transform="translate(1180 1060)">${dog('wa-d', {vest: true, fill: '#b8834a'})}</g>
  ${o.alert ? '<g id="wa-alert" transform="translate(760 430)"><circle r="46" fill="#ff4a3a"/><text y="20" font-family="Gothic" font-size="60" fill="#fff" text-anchor="middle">!</text></g>' : ''}`,
  tick: (root, t) => {
    tickDog(root, 'wa-d', t, 2);
    set($$(root, 'wa-bags'), 'transform', `translate(${-((t * 90) % 380)} 0)`);
    const a = $$(root, 'wa-alert'); if (a) set(a, 'opacity', (Math.sin(t * 8) > 0) ? 1 : .3);
  },
};

// ───────── 5년 뒤 거리 (강아지와 함께 사는 도시) ─────────
S.wf_city = {
  build: o => `
  <defs>${sky('wc-sky', o.time || 'dusk')}${glow('wc-g', '#ffd890')}</defs>
  <rect width="2040" height="1200" fill="url(#wc-sky)"/>
  <g fill="#3a3046">
   <rect x="0" y="260" width="420" height="700"/><rect x="430" y="180" width="380" height="780"/><rect x="1240" y="220" width="400" height="740"/><rect x="1650" y="300" width="390" height="660"/></g>
  <g fill="#ffd98a" opacity=".85">${Array.from({length: 24}, (_, i) => `<rect x="${(i % 2 ? 470 : 40) + (i % 4) * 80}" y="${300 + Math.floor(i / 4) * 90}" width="44" height="54"/>`).join('')}
   ${Array.from({length: 18}, (_, i) => `<rect x="${1280 + (i % 3) * 110}" y="${280 + Math.floor(i / 3) * 100}" width="50" height="60"/>`).join('')}</g>
  <rect x="820" y="120" width="410" height="420" rx="16" fill="#1c1a2a" stroke="#ffb84a" stroke-width="8"/>
  <g transform="translate(1025 470) scale(.6)">${dog('wc-bd', {fill: '#e8a050'})}</g>
  <rect x="820" y="40" width="410" height="70" rx="12" fill="#ffb84a"/><text x="1025" y="92" font-family="Gothic" font-size="44" fill="#1c1a2a" text-anchor="middle">${o.board || '구독자 1위 멍튜버'}</text>
  <rect x="60" y="760" width="340" height="80" rx="12" fill="#c0503a"/><text x="230" y="816" font-family="Gothic" font-size="46" fill="#fff" text-anchor="middle">${o.shop1 || '멍 카페'}</text>
  <rect x="1680" y="760" width="320" height="80" rx="12" fill="#3a7a6a"/><text x="1840" y="816" font-family="Gothic" font-size="46" fill="#fff" text-anchor="middle">${o.shop2 || '멍 학원'}</text>
  <rect x="0" y="960" width="2040" height="240" fill="#2a2430"/><path d="M0 1080 h2040" stroke="#5a5060" stroke-width="8" stroke-dasharray="60 50"/>
  <g id="wc-walk">${[0, 1, 2, 3].map(i => `<g transform="translate(${300 + i * 620} 1000)"><g transform="scale(.85)">${person('wc-p' + i, {fill: '#1a1622', skirt: i % 2 === 1})}</g>
    <g transform="translate(120 0)">${dog('wc-d' + i, {scale: .42, fill: ['#d98a43', '#f2efe8', '#4a3a30', '#c9a26a'][i], chest: ['#fbeedd', '#ffffff', '#d8c8b0', '#fff4e0'][i]})}</g></g>`).join('')}</g>`,
  tick: (root, t) => {
    set($$(root, 'wc-walk'), 'transform', `translate(${-((t * 60) % 620)} 0)`);
    [0, 1, 2, 3].forEach(i => tickDog(root, 'wc-d' + i, t, i));
    tickDog(root, 'wc-bd', t, 4);
  },
};
