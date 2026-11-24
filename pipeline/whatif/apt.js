// 새벽 3시 아파트의 비밀: 장면 (art.js 의 dog2·human·lin·rad·halo·blur·shadow 를 그대로 쓴다)
// 인물 who: dog 콩이, mong 몽실(몰티즈), cat 나비 회장(고양이), guard 경비 아저씨, nar 내레이터

const KONG = {bag: '#3a7ad8'};
const MONG = {fur: '#f4efe6', furL: '#ffffff', fur2: '#cfc6bc', cream: '#ffffff', bow: '#ff6a9a'};
const PETS = [
  {fur: '#4a3a30', furL: '#7a6050', fur2: '#2a1e18'}, {fur: '#c9a26a', furL: '#e8c890', fur2: '#9a7a4a'},
  {fur: '#f4efe6', furL: '#ffffff', fur2: '#c8c0b8'}, {fur: '#8a8a92', furL: '#b8b8c2', fur2: '#55555e'},
  {fur: '#d8784a', furL: '#f0a070', fur2: '#a85a30'}, {fur: '#2a2a30', furL: '#55555e', fur2: '#111116'},
];

// ───────── 고양이 (앉은 정면) 원점 = 바닥, 키 약 520 ─────────
function cat2(id, o = {}) {
  const c1 = o.c1 || '#c8ccd6', c2 = o.c2 || '#6a7080';
  return `<g id="${id}"><defs>${rad(id + 'b', c1, c2, .35, .3, .85)}${blur(id + 'f', 12)}${halo(id + 'g', '#ffe36a', .9)}</defs>
  <g transform="translate(0 4)">${shadow(id + 'f', 170, 28, .3)}</g>
  <path id="${id}-tail" d="M120 -20 q150 -10 130 -190" stroke="url(#${id}b)" stroke-width="44" fill="none" stroke-linecap="round"/>
  <path d="M-160 0 q-30 -230 160 -250 q190 20 160 250z" fill="url(#${id}b)"/>
  <path d="M-60 -200 q60 -20 120 0 q20 120 -60 200 q-80 -80 -60 -200z" fill="#fff" opacity=".55"/>
  <g fill="url(#${id}b)"><ellipse cx="-60" cy="-14" rx="46" ry="22"/><ellipse cx="60" cy="-14" rx="46" ry="22"/></g>
  ${o.scarf ? `<path d="M-120 -250 q120 50 240 0 l6 40 q-126 50 -252 0z" fill="${o.scarf}"/><path d="M60 -230 l20 120 l40 -10 l-20 -110z" fill="${o.scarf}"/>` : ''}
  <g id="${id}-head" transform="translate(0 -320)">
   <path d="M-130 -40 l-20 -150 l110 80z M130 -40 l20 -150 l-110 80z" fill="url(#${id}b)"/><path d="M-120 -70 l-12 -90 l60 46z M120 -70 l12 -90 l-60 46z" fill="#f4b3c0"/>
   <ellipse rx="160" ry="135" fill="url(#${id}b)"/>
   <path d="M-40 -130 l10 40 M0 -134 v44 M40 -130 l-10 40" stroke="${c2}" stroke-width="10" stroke-linecap="round" opacity=".6"/>
   <g id="${id}-eyes">${o.glow ? `<circle cx="-56" cy="-10" r="60" fill="url(#${id}g)" opacity=".6"/><circle cx="56" cy="-10" r="60" fill="url(#${id}g)" opacity=".6"/>` : ''}
    <ellipse cx="-56" cy="-10" rx="34" ry="30" fill="#e8d24a"/><ellipse cx="56" cy="-10" rx="34" ry="30" fill="#e8d24a"/>
    <ellipse cx="-56" cy="-10" rx="${o.slit ? 7 : 14}" ry="26" fill="#14100a"/><ellipse cx="56" cy="-10" rx="${o.slit ? 7 : 14}" ry="26" fill="#14100a"/>
    <circle cx="-48" cy="-20" r="7" fill="#fff"/><circle cx="64" cy="-20" r="7" fill="#fff"/>
    ${o.lids ? `<path d="M-94 -40 q38 -10 76 6 v-30 h-76z M18 -34 q38 -16 76 -6 v-30 h-76z" fill="${c2}"/>` : ''}</g>
   ${o.scar ? '<path d="M70 -70 l40 60 M84 -74 l-10 20 M98 -52 l-12 16" stroke="#8a4a4a" stroke-width="7" stroke-linecap="round"/>' : ''}
   <path d="M-12 34 h24 l-12 14z" fill="#e88a9a"/>
   <g id="${id}-jaw" transform="translate(0 52)"><path d="M-30 0 q30 6 60 0 q-4 40 -30 42 q-26 -2 -30 -42z" fill="#6a1e26"/></g>
   <path d="M0 48 q-24 22 -44 4 M0 48 q24 22 44 4" stroke="#3a3a40" stroke-width="6" fill="none" stroke-linecap="round"/>
   <path d="M-70 40 h-110 M-70 58 h-100 M70 40 h110 M70 58 h100" stroke="#fff" stroke-width="4" opacity=".75"/>
   ${o.glasses ? `<g fill="none" stroke="#c8a040" stroke-width="7"><circle cx="-56" cy="-10" r="44"/><circle cx="56" cy="-10" r="44"/><path d="M-12 -12 h24"/></g>` : ''}
  </g></g>`;
}
function tickCat(root, id, t, seed = 0, who = 'cat') {
  const talking = window.SPEAK === who;
  at(q(root, id + '-tail'), 'transform', `rotate(${Math.sin(t * 1.6 + seed) * 10} 120 -20)`);
  at(q(root, id + '-head'), 'transform', `translate(0 ${-320 + (talking ? Math.sin(t * 6) * 4 : 0)}) rotate(${Math.sin(t * .7 + seed) * 2})`);
  const open = talking ? Math.max(0, Math.sin(t * 14) * .55 + Math.sin(t * 5.3) * .5) : 0;
  at(q(root, id + '-jaw'), 'transform', `translate(0 52) scale(1 ${.2 + open})`);
  const blink = ((t + seed * 1.7) % 4.3) < .1;
  at(q(root, id + '-eyes'), 'transform', blink ? 'translate(0 -10) scale(1 .1) translate(0 10)' : '');
}

// 둥둥 떠다니는 빛 먼지 (공기감)
const motes = (id, n, c, w = 2400, h = 1800) => `<g id="${id}" fill="${c}">${Array.from({length: n}, (_, i) => `<circle cx="${(i * 211) % w - 400}" cy="${(i * 137) % h - 300}" r="${2 + i % 4}" opacity="${.2 + (i % 5) / 10}"/>`).join('')}</g>`;

// 1. 엘리베이터 안 (새벽, 형광등)
A.elev = {
  build: o => `<defs>${lin('ev-w', '#b8c2c8', '#7a868e', 1, 0)}${lin('ev-w2', '#d4dce0', '#8a969e', 1, 0)}${halo('ev-l', '#eaffff', .8)}${lin('ev-f', '#5a5048', '#2a2420')}${blur('ev-b', 4)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="#3a4248"/>
  <rect x="-200" y="-700" width="2440" height="2000" fill="url(#ev-w)"/>
  <g stroke="#6a767e" stroke-width="6">${Array.from({length: 9}, (_, i) => `<path d="M${-200 + i * 300} -700 v2000"/>`).join('')}</g>
  <g opacity=".35">${Array.from({length: 9}, (_, i) => `<rect x="${-180 + i * 300}" y="-680" width="40" height="1960" fill="#fff"/>`).join('')}</g>
  <rect x="-200" y="-760" width="2440" height="120" fill="#e8f4f4"/><rect x="200" y="-700" width="1640" height="30" rx="15" fill="#ffffff"/>
  <circle cx="1020" cy="-640" r="900" fill="url(#ev-l)" opacity=".45"/>
  <rect x="-200" y="360" width="2440" height="40" rx="20" fill="#d8dde0"/><rect x="-200" y="380" width="2440" height="12" fill="#8a969e"/>
  <rect x="-200" y="1200" width="2440" height="900" fill="url(#ev-f)"/><path d="M-200 1200 h2440" stroke="#9aa4aa" stroke-width="14"/>
  <g transform="translate(1600 -260)"><rect x="-150" y="-60" width="300" height="760" rx="20" fill="url(#ev-w2)" stroke="#5a666e" stroke-width="6"/>
   <rect x="-110" y="-30" width="220" height="110" rx="10" fill="#120a06"/><text id="ev-fl" x="0" y="50" font-family="Gothic" font-size="78" fill="#ff7a2a" text-anchor="middle">${o.floor || '12'}</text>
   ${['R', '15', '14', '13', '12', '11', '10', '9', '8'].map((f, i) => `<g transform="translate(${(i % 2) * 120 - 60} ${150 + Math.floor(i / 2) * 120})"><circle r="44" fill="#e8eef0" stroke="#5a666e" stroke-width="5"/>
    <circle r="44" fill="#ffb02a" opacity="${f === 'R' ? 1 : f === (o.lit || '') ? .9 : 0}" id="${f === 'R' ? 'ev-r' : ''}"/><text y="16" font-family="Gothic" font-size="42" fill="#2a2a2a" text-anchor="middle">${f}</text></g>`).join('')}</g>
  ${o.mong ? `<g transform="translate(560 1330) scale(.78)">${dog2('ev-m', MONG)}</g>` : ''}
  <g transform="translate(${o.mong ? 1180 : 1080} 1360) scale(.85)">${dog2('ev-d', {...KONG, tilt: o.look ? -10 : 0})}</g>
  ${o.paw ? `<g id="ev-paw"><path d="M1230 790 q160 -60 300 -80" stroke="#e8914a" stroke-width="54" stroke-linecap="round" fill="none"/><circle cx="1540" cy="710" r="34" fill="#fff3e2"/></g>` : ''}`,
  tick: (root, t, p, o) => {
    tickDog2(root, 'ev-d', t, 0, {tilt: o.look ? -10 : 0});
    if (o.mong) tickDog2(root, 'ev-m', t, 2, {who: 'mong', tilt: 6});
    const fl = q(root, 'ev-fl');
    if (fl && o.rise) fl.textContent = ['12', '13', '14', '15', 'R'][Math.min(4, Math.floor((t % 30) * 1.4) % 5)];
    const paw = q(root, 'ev-paw');
    if (paw) at(paw, 'transform', `translate(${Math.sin(t * 3) * 10} 0)`);
  },
};

// 2. 밤 침실: 자는 누나 + 눈 뜬 콩이
A.nbed = {
  build: o => `<defs>${lin('nb-w', '#1c2448', '#0c1028')}${halo('nb-m', '#cfe0ff', .8)}${lin('nb-bl', '#4a5aa0', '#2a3468', 1, 1)}${halo('nb-c', '#ffe3a0', .7)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#nb-w)"/>
  <g transform="translate(1300 -300)"><rect width="560" height="720" rx="20" fill="#24346a"/><circle cx="380" cy="200" r="100" fill="#f4f2d8"/><circle cx="420" cy="180" r="90" fill="#24346a"/>
   <g fill="#fff">${Array.from({length: 14}, (_, i) => `<circle cx="${(i * 97) % 520 + 20}" cy="${(i * 61) % 640 + 30}" r="${2 + i % 3}"/>`).join('')}</g>
   <path d="M0 0 h560 v720 h-560z M280 0 v720 M0 360 h560" stroke="#3a4a80" stroke-width="22" fill="none"/></g>
  <path d="M1300 -300 L200 1600 L1000 1600 L1860 420z" fill="#bcd0ff" opacity=".12"/>
  <circle cx="1580" cy="0" r="700" fill="url(#nb-m)" opacity=".25"/>
  <rect x="-600" y="1150" width="3240" height="900" fill="#1a1830"/>
  <path d="M-100 760 q900 -60 1800 0 v400 h-1800z" fill="#2a2c50"/>
  <ellipse cx="360" cy="730" rx="250" ry="96" fill="#c8cce8"/>
  <g transform="translate(330 640)"><path d="M-130 30 q-20 -170 130 -170 q150 0 130 170z" fill="#1d1620"/><ellipse cx="0" cy="40" rx="104" ry="96" fill="#e8c0a8"/>
   <path d="M-110 10 q20 -110 110 -112 q90 2 110 112 q-50 -60 -110 -62 q-60 2 -110 62z" fill="#1d1620"/>
   <path d="M-60 50 q20 14 40 0 M20 50 q20 14 40 0" stroke="#2a1a1a" stroke-width="8" fill="none" stroke-linecap="round"/>
   <path d="M-14 96 q14 8 28 0" stroke="#6a2a2a" stroke-width="6" fill="none" stroke-linecap="round"/></g>
  <path d="M-40 820 q900 -110 1780 -20 l40 400 h-1860z" fill="url(#nb-bl)"/>
  <path d="M100 900 q300 -40 600 10 M800 880 q400 -40 800 10" stroke="#8a9ad8" stroke-width="10" fill="none" opacity=".4"/>
  <g id="nb-z" font-family="Gothic" fill="#cfe0ff">${[0, 1, 2].map(i => `<text x="${560 + i * 70}" y="${520 - i * 90}" font-size="${60 + i * 20}" opacity=".8">Z</text>`).join('')}</g>
  <g transform="translate(1320 1060) scale(.9)">${dog2('nb-d', {...KONG})}</g>
  <circle cx="1350" cy="560" r="300" fill="url(#nb-c)" opacity=".18"/>
  ${motes('nb-mo', 30, '#cfe0ff')}`,
  tick: (root, t) => {
    tickDog2(root, 'nb-d', t, 1, {tilt: 8});
    at(q(root, 'nb-z'), 'transform', `translate(${Math.sin(t) * 10} ${-((t * 30) % 60)})`);
    at(q(root, 'nb-mo'), 'transform', `translate(${Math.sin(t * .3) * 30} ${-t * 8})`);
  },
};

// 3. 현관 도어락 (신발 상자 밟고 코로 누르기)
A.door = {
  build: o => `<defs>${lin('dr-w', '#2a2a44', '#14142a')}${lin('dr-d', '#6a5a4a', '#3a2e24', 1, 0)}${halo('dr-k', '#7ad8ff', .9)}${halo('dr-o', '#fff0c0', .9)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#dr-w)"/>
  <rect x="600" y="-500" width="900" height="1700" rx="10" fill="url(#dr-d)"/><rect x="560" y="-540" width="980" height="40" fill="#4a4a5a"/>
  <rect x="640" y="-460" width="820" height="1620" rx="8" fill="none" stroke="#2a2018" stroke-width="10" opacity=".6"/>
  ${o.open ? `<path d="M1500 -500 L1500 1200 L2000 1500 L2000 -800z" fill="#fff0c0" opacity=".2"/><rect x="1440" y="-500" width="60" height="1700" fill="#fff3d0"/>` : ''}
  <g transform="translate(1300 420)"><rect x="-80" y="-180" width="160" height="320" rx="20" fill="#1a1a22" stroke="#555" stroke-width="5"/>
   <circle r="220" fill="url(#dr-k)" opacity=".35"/>
   <g id="dr-keys" font-family="Gothic" font-size="34" fill="#9ae8ff" text-anchor="middle">${[1, 2, 3, 4, 5, 6, 7, 8, 9, '*', 0, '#'].map((k, i) => `<g transform="translate(${(i % 3) * 46 - 46} ${-130 + Math.floor(i / 3) * 62})"><rect x="-18" y="-24" width="36" height="40" rx="6" fill="#2a3a4a" id="dr-k${i}"/><text y="8">${k}</text></g>`).join('')}</g></g>
  <rect x="1360" y="560" width="40" height="200" rx="16" fill="#b8b8c0"/>
  <rect x="-600" y="1200" width="3240" height="900" fill="#3a3040"/><rect x="-600" y="1200" width="3240" height="30" fill="#5a4a5a"/>
  <g transform="translate(250 1200)"><rect x="-300" y="-220" width="600" height="220" rx="10" fill="#e8c890"/><path d="M-300 -150 h600" stroke="#c8a870" stroke-width="8"/>
   <text y="-70" font-family="Gothic" font-size="56" fill="#8a6a3a" text-anchor="middle">누나 운동화</text></g>
  <g transform="translate(1000 1220)"><rect x="-200" y="-260" width="400" height="260" rx="14" fill="#c8a06a"/><text y="-110" font-family="Gothic" font-size="54" fill="#6a4a2a" text-anchor="middle">택배 상자</text></g>
  <g transform="translate(1060 960) scale(.85)">${dog2('dr-d', {...KONG})}</g>`,
  tick: (root, t, p) => {
    tickDog2(root, 'dr-d', t, 2, {tilt: -14});
    const k = Math.floor(t * 4) % 12;
    for (let i = 0; i < 12; i++) at(q(root, 'dr-k' + i), 'fill', i === k ? '#7ad8ff' : '#2a3a4a');
  },
};

// 4. 경비실 CCTV 모니터 앞 경비 아저씨
A.guard = {
  build: o => `<defs>${lin('gd-w', '#2a3038', '#14181e')}${halo('gd-s', '#9affd8', .8)}${halo('gd-l', '#ffcf7a', .8)}${lin('gd-mon', '#1a2a24', '#0a1410')}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#gd-w)"/>
  <g transform="translate(-100 -560)">${[0, 1, 2, 3, 4, 5].map(i => `<g transform="translate(${(i % 3) * 560} ${Math.floor(i / 3) * 420})"><rect width="520" height="380" rx="16" fill="#3a3a40"/>
   <rect x="20" y="20" width="480" height="340" rx="8" fill="url(#gd-mon)"/>
   <g opacity=".55" stroke="#9affd8" stroke-width="4" fill="none">${i === 4 ? `<rect x="80" y="60" width="360" height="280"/><path d="M80 60 l-40 -30 M440 60 l40 -30"/>` : `<path d="M40 300 h440 M120 300 v-180 h280 v180"/>`}</g>
   ${i === 4 ? `<g transform="translate(260 330) scale(.36)" opacity=".9">${dog2('gd-mini', {...KONG})}</g>` : ''}
   <text x="40" y="60" font-family="Gothic" font-size="28" fill="#9affd8" opacity=".8">CAM ${i + 1}${i === 4 ? ' 엘리베이터' : ''}</text>
   <circle cx="470" cy="50" r="10" fill="#ff3a2a"/></g>`).join('')}</g>
  <circle cx="1020" cy="-200" r="1100" fill="url(#gd-s)" opacity=".22"/>
  <g transform="translate(1020 1500) scale(1.05)">${human('gd-p', {short: true, cap: '#24304c', stache: true, hair: '#3a3a3a', shirt: '#4a5a7a', shirtL: '#7a8ab0', skin: '#e8b898', noShadow: true, sitting: true,
    eyes: o.smile ? 'normal' : 'normal', mouth: o.smile ? 'smile' : 'sad'})}</g>
  <rect x="-600" y="1000" width="3240" height="1100" fill="#2a2420"/><rect x="-400" y="940" width="2840" height="90" rx="14" fill="#5a4a3a"/>
  <g transform="translate(1520 930)"><rect x="-50" y="-110" width="100" height="120" rx="14" fill="#e8e0d0"/><path d="M50 -80 q46 0 46 30 q0 30 -46 30" stroke="#e8e0d0" stroke-width="14" fill="none"/>
   <g id="gd-st" stroke="#fff" stroke-width="6" fill="none" opacity=".5"><path d="M-20 -130 q-14 -30 0 -60 M14 -130 q-14 -30 0 -60"/></g></g>
  ${o.smile ? `<rect x="-600" y="-900" width="3240" height="3000" fill="#000" opacity=".45"/><circle cx="1020" cy="700" r="500" fill="url(#gd-s)" opacity=".35"/>
   <g transform="translate(1020 1500) scale(1.05)"><g transform="translate(0 -820)"><path d="M-34 50 q34 34 68 0" stroke="#3a1a1a" stroke-width="9" fill="none"/>
   <circle cx="-52" cy="0" r="10" fill="#9affd8"/><circle cx="52" cy="0" r="10" fill="#9affd8"/></g></g>` : ''}`,
  tick: (root, t, p, o) => {
    at(q(root, 'gd-st'), 'transform', `translate(0 ${-((t * 20) % 20)})`);
    tickDog2(root, 'gd-mini', t, 3, {who: 'none'});
    if (!o.smile) at(q(root, 'gd-p-head'), 'transform', `translate(0 ${-820 + Math.sin(t * 1.2) * 3})`);
  },
};

// 5. 옥상 새벽 반상회
A.roof = {
  build: o => `<defs>${lin('rf-s', '#060a22', '#2a2a5a')}${halo('rf-m', '#fff6d0', .9)}${halo('rf-b', '#ffd27a', .9)}${halo('rf-e', '#c8ff6a', .95)}${lin('rf-f', '#3a3a4a', '#1a1a26')}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#rf-s)"/>
  <g fill="#fff">${Array.from({length: 70}, (_, i) => `<circle cx="${(i * 233) % 3200 - 600}" cy="${(i * 137) % 900 - 850}" r="${1 + i % 3}" opacity="${.3 + (i % 5) / 8}"/>`).join('')}</g>
  <circle cx="1500" cy="-420" r="150" fill="#fff8e0"/><circle cx="1500" cy="-420" r="600" fill="url(#rf-m)" opacity=".4"/>
  <g fill="#14142e">${Array.from({length: 14}, (_, i) => `<rect x="${-600 + i * 240}" y="${80 + (i * 97) % 260}" width="220" height="900"/>`).join('')}</g>
  <g fill="#ffd98a">${Array.from({length: 90}, (_, i) => `<rect x="${-580 + (i % 15) * 220 + (Math.floor(i / 15) % 2) * 50}" y="${200 + Math.floor(i / 15) * 80}" width="30" height="40" opacity="${(i * 7) % 4 ? .15 : .8}"/>`).join('')}</g>
  <g transform="translate(-300 -60)"><rect x="0" y="0" width="420" height="520" rx="30" fill="#5a6a8a"/><ellipse cx="210" cy="0" rx="210" ry="50" fill="#7a8aaa"/><text x="210" y="300" font-family="Gothic" font-size="64" fill="#3a4a6a" text-anchor="middle">물탱크</text></g>
  <rect x="-600" y="620" width="3240" height="1500" fill="url(#rf-f)"/>
  <g stroke="#6a6a80" stroke-width="12">${Array.from({length: 18}, (_, i) => `<path d="M${-600 + i * 190} 470 v150"/>`).join('')}<path d="M-600 470 h3240"/></g>
  <path d="M-100 -120 q1120 220 2240 0" stroke="#3a3a3a" stroke-width="5" fill="none"/>
  <g id="rf-bulbs">${Array.from({length: 12}, (_, i) => { const x = -100 + i * 204, y = -120 + 220 * 4 * (i / 11) * (1 - i / 11) * .5; return `<g transform="translate(${x} ${y + 30})"><circle r="60" fill="url(#rf-b)" opacity=".6"/><circle r="16" fill="#fff0b0"/></g>`; }).join('')}</g>
  <g transform="translate(1020 20)"><rect x="-460" y="-70" width="920" height="150" rx="16" fill="#fff6e0"/><rect x="-460" y="-70" width="920" height="150" rx="16" fill="none" stroke="#c8302a" stroke-width="10"/>
   <text y="40" font-family="Gothic" font-size="86" fill="#c8302a" text-anchor="middle">제1회 새벽 반상회</text></g>
  <g transform="translate(1020 760)"><rect x="-190" y="-170" width="380" height="170" rx="10" fill="#b8844a"/><path d="M-190 -110 h380 M-190 -55 h380" stroke="#8a5a2a" stroke-width="8"/>
   <text y="-70" font-family="Gothic" font-size="44" fill="#6a3a1a" text-anchor="middle">사과 상자</text></g>
  <g transform="translate(1020 600) scale(.95)">${cat2('rf-c', {scarf: '#c8302a', glasses: true, scar: true})}</g>
  ${[0, 1, 2].map(r => Array.from({length: 7}, (_, i) => { const x = -280 + i * 400 + (r % 2) * 200, y = 1080 + r * 300, s = .42 + r * .08, k = (i + r * 3) % 6;
    return (i + r) % 4 === 3 ? `<g transform="translate(${x} ${y}) scale(${s * 1.1})">${cat2(`rf-k${r}${i}`, {c1: ['#f0c890', '#3a3a40', '#f4f0e8'][r], c2: ['#c08a4a', '#141418', '#bcb4a8'][r]})}</g>`
      : `<g transform="translate(${x} ${y}) scale(${s})">${dog2(`rf-p${r}${i}`, PETS[k])}</g>`; }).join('')).join('')}
  ${o.kong ? `<g transform="translate(1700 1820) scale(.78)">${dog2('rf-d', {...KONG})}</g><g transform="translate(1260 1840) scale(.66)">${dog2('rf-m', MONG)}</g>` : ''}
  ${o.dark ? `<rect x="-600" y="-900" width="3240" height="3000" fill="#02030a" opacity=".93"/>
   <g id="rf-eyes">${Array.from({length: 26}, (_, i) => { const x = (i * 263) % 2400 - 250, y = 900 + (i * 151) % 900; return `<g transform="translate(${x} ${y})" opacity="${.6 + (i % 3) / 6}"><circle cx="-26" r="38" fill="url(#rf-e)"/><circle cx="26" r="38" fill="url(#rf-e)"/><circle cx="-26" r="10" fill="#f6ffd0"/><circle cx="26" r="10" fill="#f6ffd0"/></g>`; }).join('')}</g>
   <path d="M1020 -900 L700 2100 L1340 2100z" fill="#fff6d0" opacity=".06"/>` : ''}`,
  tick: (root, t, p, o) => {
    tickCat(root, 'rf-c', t, 0, 'cat');
    for (let r = 0; r < 3; r++) for (let i = 0; i < 7; i++) {
      if ((i + r) % 4 === 3) tickCat(root, `rf-k${r}${i}`, t, i + r, 'none'); else tickDog2(root, `rf-p${r}${i}`, t, i + r * 2, {who: 'none'});
    }
    if (o.kong) { tickDog2(root, 'rf-d', t, 4, {tilt: -8}); tickDog2(root, 'rf-m', t, 5, {who: 'mong', tilt: 8}); }
    const e = q(root, 'rf-eyes');
    if (e) at(e, 'opacity', ((t * 1.3) % 3) < .12 ? .1 : 1);
    at(q(root, 'rf-bulbs'), 'opacity', .85 + Math.sin(t * 3) * .15);
  },
};

// 6. 나비 회장 클로즈업 (어두운 배경 + 전구빛)
A.boss = {
  build: o => `<defs>${rad('bs-w', '#3a2a4a', '#0a0612', .5, .4, .8)}${halo('bs-b', '#ffd27a', .9)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#bs-w)"/>
  ${Array.from({length: 7}, (_, i) => `<circle cx="${-300 + i * 420}" cy="${-300 + (i % 2) * 80}" r="120" fill="url(#bs-b)" opacity=".35"/>`).join('')}
  <rect x="-600" y="1180" width="3240" height="900" fill="#1a1622"/>
  <g transform="translate(1020 1180)"><rect x="-260" y="-200" width="520" height="200" rx="10" fill="#b8844a"/><path d="M-260 -130 h520 M-260 -65 h520" stroke="#8a5a2a" stroke-width="8"/></g>
  <g transform="translate(1020 990) scale(1.25)">${cat2('bs-c', {scarf: '#c8302a', glasses: true, scar: true, slit: !!o.slit, lids: !!o.lids, glow: !!o.slit})}</g>
  ${motes('bs-mo', 30, '#ffe8b0')}`,
  tick: (root, t) => { tickCat(root, 'bs-c', t, 1, 'cat'); at(q(root, 'bs-mo'), 'transform', `translate(${Math.sin(t * .4) * 30} ${-t * 10})`); },
};
Object.assign(window.SCENE_LIBRARY, A);
