// 만약에 쇼츠 손그림 장면 (고급판). 세로 카메라로 어디를 잘라도 비지 않게 배경을 넓게(x -400~2440, y -800~2000) 그린다.
// 장면 = {build(o) → SVG 문자열, tick(root, t, p, o)}. 인물·강아지는 그라데이션 명암 + 부드러운 그림자 + 테두리 빛.
// window.SPEAK = 지금 말하는 인물. 강아지는 'dog' 차례에 입이 움직인다.
const A = {};
const q = (root, id) => root.querySelector('#' + (root.dataset.px || '') + id);
const at = (el, k, v) => el && el.setAttribute(k, v);

const lin = (id, c1, c2, x2 = 0, y2 = 1) => `<linearGradient id="${id}" x1="0" y1="0" x2="${x2}" y2="${y2}"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient>`;
const rad = (id, c1, c2, cx = .35, cy = .3, r = .8) => `<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="${r}"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></radialGradient>`;
const halo = (id, c, o = .9) => `<radialGradient id="${id}"><stop offset="0" stop-color="${c}" stop-opacity="${o}"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`;
const blur = (id, s) => `<filter id="${id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${s}"/></filter>`;
const shadow = (id, rx, ry, o = .35) => `<ellipse cx="0" cy="0" rx="${rx}" ry="${ry}" fill="#000" opacity="${o}" filter="url(#${id})"/>`;

// ───────── 강아지 (시바, 정면 3/4) 원점 = 엉덩이 아래 바닥, 키 약 560 ─────────
function dog2(id, o = {}) {
  const fur = o.fur || '#e8914a', fur2 = o.fur2 || '#b8612a', cream = o.cream || '#fff3e2';
  const old = !!o.old;
  return `<g id="${id}" data-mouth="${o.face === 'shock' ? .9 : o.face === 'worried' ? .15 : o.mouth || 0}">
  <defs>${rad(id + 'b', o.furL || '#f6b070', fur2, .35, .25, .9)}${rad(id + 'h', o.furL || '#f8b878', fur2, .38, .3, .85)}
   ${rad(id + 'c', '#ffffff', cream, .4, .3, .9)}${rad(id + 'e', '#5a3418', '#120a06', .4, .35, .7)}${blur(id + 'f', 14)}</defs>
  <g transform="translate(0 4)">${shadow(id + 'f', 230, 40, .32)}</g>
  <g id="${id}-tail" transform="translate(-150 -120)">
   <path d="M0 0 q-120 -30 -100 -190 q30 -70 80 -30 q40 40 -10 90 q-20 40 50 110z" fill="url(#${id}b)"/>
   <path d="M-88 -196 q30 -40 66 -14 q-30 4 -40 40z" fill="${cream}"/></g>
  ${o.bag ? `<g transform="translate(-150 -330) rotate(-10)"><rect x="-70" y="-20" width="150" height="190" rx="40" fill="${o.bag}"/><rect x="-52" y="60" width="114" height="70" rx="20" fill="#000" opacity=".18"/><path d="M-50 10 q60 -40 120 0" stroke="#fff" stroke-width="8" fill="none" opacity=".5"/></g>` : ''}
  <path d="M-200 0 q-50 -250 70 -330 q120 -70 230 10 q90 80 60 320z" fill="url(#${id}b)"/>
  <path d="M-30 -320 q130 20 130 180 q0 110 -50 140 h-150 q-50 -170 70 -320z" fill="url(#${id}c)"/>
  <path d="M-10 -300 l20 30 l18 -26 l14 34 l20 -24" stroke="${cream}" stroke-width="10" fill="none" stroke-linejoin="round"/>
  <g fill="url(#${id}b)"><rect x="-40" y="-170" width="62" height="172" rx="31"/><rect x="50" y="-170" width="62" height="172" rx="31"/></g>
  <g fill="${cream}"><ellipse cx="-9" cy="-6" rx="40" ry="16"/><ellipse cx="81" cy="-6" rx="40" ry="16"/></g>
  <g stroke="${fur2}" stroke-width="4" opacity=".5"><path d="M-24 -6 v-10 M-6 -6 v-12 M10 -6 v-10 M66 -6 v-10 M84 -6 v-12 M100 -6 v-10"/></g>
  ${o.vest ? `<path d="M-170 -290 q130 -50 260 0 l14 170 h-288z" fill="${o.vest}"/><rect x="-110" y="-250" width="150" height="56" rx="10" fill="#ffd84a"/>
   <path d="M-170 -290 q130 -50 260 0" stroke="#fff" stroke-width="8" fill="none" opacity=".6"/>` : ''}
  ${o.bag ? `<path d="M-150 -320 q60 120 40 260 M120 -300 q-30 120 0 250" stroke="${o.bag}" stroke-width="22" fill="none" stroke-linecap="round"/>` : ''}
  ${o.cape ? `<path d="M-180 -300 q140 -40 270 10 l60 280 q-200 30 -380 -10z" fill="${o.cape}" opacity=".95"/>` : ''}
  <path d="M-90 -300 q130 50 250 -16" stroke="#c8302a" stroke-width="26" fill="none" stroke-linecap="round"/>
  <path d="M-90 -306 q130 46 250 -20" stroke="#ff6a5a" stroke-width="6" fill="none" stroke-linecap="round" opacity=".7"/>
  <g transform="translate(40 -268)"><circle r="22" fill="#f2c24a"/><circle r="22" fill="none" stroke="#b88a1a" stroke-width="4"/><circle cx="-7" cy="-7" r="6" fill="#fff6c8"/></g>
  ${o.tie ? `<path d="M40 -280 l-26 26 l26 140 l26 -140z" fill="#24407a"/><path d="M28 -292 h24 l-12 26z" fill="#162a52"/>` : ''}
  <g id="${id}-head" transform="translate(30 -440)">
   <path d="M-150 -40 l-30 -190 q10 -20 30 -10 l110 120z" fill="url(#${id}h)"/><path d="M-138 -70 l-20 -120 l70 72z" fill="#f4b3a0"/>
   <path d="M60 -110 l90 -150 q20 -10 28 10 l12 190z" fill="url(#${id}h)"/><path d="M86 -110 l62 -104 l10 116z" fill="#f4b3a0"/>
   <ellipse cx="0" cy="0" rx="190" ry="165" fill="url(#${id}h)"/>
   <path d="M-190 10 q-10 70 40 110 q-10 -50 10 -60z M180 0 q20 70 -30 116 q4 -50 -16 -62z" fill="${fur}"/>
   <path d="M-120 60 q100 140 260 50 q30 -60 -10 -90 q-130 -20 -250 40z" fill="url(#${id}c)"/>
   ${old ? `<path d="M-100 50 q90 110 220 40 q20 -50 -10 -70 q-110 -10 -210 30z" fill="#e9e4de"/><path d="M-60 -90 q30 -16 60 -6 M40 -96 q30 -12 56 4" stroke="#e9e4de" stroke-width="12" fill="none" stroke-linecap="round"/>` : ''}
   <ellipse cx="-110" cy="30" rx="46" ry="34" fill="url(#${id}c)"/><ellipse cx="128" cy="26" rx="40" ry="30" fill="url(#${id}c)"/>
   <ellipse cx="-118" cy="44" rx="30" ry="16" fill="#ff8a8a" opacity=".35"/><ellipse cx="134" cy="40" rx="26" ry="14" fill="#ff8a8a" opacity=".35"/>
   <g id="${id}-eyes">
    ${o.face === 'shock' ? `<ellipse cx="-62" cy="-34" rx="36" ry="42" fill="#fff" stroke="#3a2016" stroke-width="6"/><ellipse cx="72" cy="-38" rx="34" ry="40" fill="#fff" stroke="#3a2016" stroke-width="6"/><circle cx="-60" cy="-30" r="11" fill="#120a06"/><circle cx="70" cy="-34" r="10" fill="#120a06"/>`
    : `<ellipse cx="-62" cy="-28" rx="${old ? 24 : 30}" ry="${old ? 26 : 36}" fill="url(#${id}e)"/><ellipse cx="72" cy="-32" rx="${old ? 22 : 28}" ry="${old ? 24 : 34}" fill="url(#${id}e)"/>
    <circle cx="-52" cy="-42" r="11" fill="#fff"/><circle cx="-72" cy="-16" r="5" fill="#fff" opacity=".8"/>
    <circle cx="81" cy="-46" r="10" fill="#fff"/><circle cx="62" cy="-20" r="5" fill="#fff" opacity=".8"/>`}
    ${o.face === 'sly' ? `<path d="M-96 -70 h70 v34 q-36 -8 -70 6z M38 -74 h68 v36 q-34 -10 -68 4z" fill="${fur}"/>` : ''}
    ${o.tear ? `<path d="M-74 4 q-8 22 0 34 q10 -10 0 -34z" fill="#bfe6ff" opacity=".9"/>` : ''}
    ${o.glasses ? `<g fill="none" stroke="#2a2a2a" stroke-width="8"><circle cx="-62" cy="-28" r="50"/><circle cx="72" cy="-32" r="48"/><path d="M-12 -30 h36"/></g>` : ''}
   </g>
   <path d="${o.face === 'worried' ? 'M-100 -86 q36 -6 72 -34 M40 -120 q36 4 68 30' : o.face === 'shock' ? 'M-104 -118 q36 -30 76 -12 M40 -126 q36 -20 72 6' : o.face === 'sly' ? 'M-100 -84 q36 4 72 -2 M40 -90 q36 -8 68 -10' : 'M-100 -96 q36 -26 72 -8 M40 -104 q36 -16 68 6'}" stroke="${fur2}" stroke-width="10" fill="none" stroke-linecap="round" id="${id}-brow"/>
   ${o.sweat ? `<path id="${id}-sweat" d="M150 -120 q-22 40 0 56 q22 -16 0 -56z" fill="#bfe6ff" stroke="#7ab8e8" stroke-width="4"/>` : ''}
   <ellipse cx="10" cy="44" rx="36" ry="26" fill="#1d120c"/><ellipse cx="0" cy="36" rx="12" ry="7" fill="#fff" opacity=".6"/>
   <g id="${id}-jaw" transform="translate(10 84)"><path d="M-46 0 q46 8 92 0 q-6 60 -46 64 q-40 -4 -46 -64z" fill="#7a2228"/>
    <ellipse cx="0" cy="40" rx="26" ry="16" fill="#ff7a86"/></g>
   <path d="${o.face === 'shock' || o.face === 'worried' ? 'M10 70 v14 M10 84 q-28 -12 -50 12 M10 84 q28 -12 50 12' : 'M10 70 v14 M10 84 q-30 18 -54 -4 M10 84 q30 18 54 -4'}" stroke="#3a2016" stroke-width="7" fill="none" stroke-linecap="round"/>
   ${o.headset ? `<path d="M-200 -20 q0 -230 200 -230 q200 0 200 230" stroke="#2a2a3a" stroke-width="26" fill="none"/><rect x="-232" y="-40" width="60" height="110" rx="24" fill="#3a3a5a"/><rect x="172" y="-40" width="60" height="110" rx="24" fill="#3a3a5a"/>` : ''}
   ${o.bow ? `<g transform="translate(-110 -150) rotate(-20)"><path d="M0 0 l-70 -40 q-20 40 0 80z M0 0 l70 -40 q20 40 0 80z" fill="${o.bow}"/><circle r="20" fill="${o.bow}"/><circle cx="-6" cy="-6" r="7" fill="#fff" opacity=".6"/></g>` : ''}
   ${o.lamp ? `<rect x="-90" y="-176" width="180" height="40" rx="14" fill="#2a2a2a"/><circle cx="0" cy="-160" r="26" fill="#fff8c0"/>` : ''}
  </g>
 </g>`;
}

function tickDog2(root, id, t, seed = 0, o = {}) {
  const talking = window.SPEAK === (o.who || 'dog');
  const me = q(root, id);
  if (!me) return;
  const tail = q(root, id + '-tail');
  at(tail, 'transform', `translate(-150 -120) rotate(${Math.sin(t * (o.old ? 4 : 10) + seed) * (o.old ? 8 : 18)})`);
  // 숨쉬기 + 말할 때 몸이 살짝 들썩
  const br = 1 + Math.sin(t * 2.4 + seed) * .012 + (talking ? Math.abs(Math.sin(t * 7.5)) * .025 : 0);
  at(me, 'transform', `scale(${2 - br} ${br})`);
  const bob = talking ? Math.sin(t * 7.5) * 6 : Math.sin(t * 1.4 + seed) * 4;
  at(q(root, id + '-head'), 'transform', `translate(30 ${-440 + bob}) rotate(${Math.sin(t * .8 + seed) * 3 + (o.tilt || 0)})`);
  const base = o.mouth !== undefined ? o.mouth : +(me.dataset.mouth || 0);
  const open = talking ? Math.max(base * .6, Math.sin(t * 16) * .55 + Math.sin(t * 6.1) * .5) : base;
  at(q(root, id + '-jaw'), 'transform', `translate(10 ${84 + open * 20}) scale(1 ${.35 + open * .9})`);
  const blink = o.closed || ((t + seed * 1.37) % 3.8) < .11;
  at(q(root, id + '-eyes'), 'transform', blink ? 'translate(0 -30) scale(1 .12) translate(0 30)' : '');
  const sw = q(root, id + '-sweat');
  if (sw) at(sw, 'transform', `translate(0 ${(t * 40) % 30})`);
}

// ───────── 사람 (단발머리 주인 등) 원점 = 발 밑, 키 약 900 ─────────
function human(id, o = {}) {
  const skin = o.skin || '#f6cfb0', hair = o.hair || '#1d1620', shirt = o.shirt || '#7fb6e8', pants = o.pants || '#3a4a6a';
  const pose = o.pose || 'stand';
  const arms = {
    stand: '<path d="M-110 -620 q-50 120 -40 240" /><path d="M110 -620 q50 120 40 240"/>',
    shock: '<path d="M-110 -620 q-120 -60 -110 -220"/><path d="M110 -620 q120 -60 110 -220"/>',
    drop: '<path d="M-110 -620 q-90 40 -150 -40"/><path d="M110 -620 q100 20 150 -60"/>',
    hug: '<path d="M-110 -620 q120 60 260 40"/><path d="M110 -620 q80 80 200 80"/>',
  }[pose];
  const hands = {
    stand: '<circle cx="-150" cy="-380" r="34"/><circle cx="150" cy="-380" r="34"/>',
    shock: '<circle cx="-220" cy="-840" r="36"/><circle cx="220" cy="-840" r="36"/>',
    drop: '<circle cx="-260" cy="-660" r="34"/><circle cx="260" cy="-680" r="34"/>',
    hug: '<circle cx="150" cy="-580" r="34"/><circle cx="310" cy="-540" r="34"/>',
  }[pose];
  const mouth = o.mouth === 'o' ? '<ellipse cx="0" cy="56" rx="26" ry="34" fill="#6a1e26"/><ellipse cx="0" cy="72" rx="16" ry="12" fill="#ff8a90"/>'
    : o.mouth === 'sad' ? '<path d="M-26 66 q26 -18 52 0" stroke="#6a2a2a" stroke-width="8" fill="none" stroke-linecap="round"/>'
    : '<path d="M-34 50 q34 34 68 0" stroke="#6a2a2a" stroke-width="9" fill="none" stroke-linecap="round"/>';
  const eyes = o.eyes === 'closed' ? '<path d="M-74 0 q22 16 44 0 M30 0 q22 16 44 0" stroke="#2a1a1a" stroke-width="9" fill="none" stroke-linecap="round"/>'
    : o.eyes === 'wide' ? '<circle cx="-52" cy="-4" r="24" fill="#fff"/><circle cx="52" cy="-4" r="24" fill="#fff"/><circle cx="-52" cy="-4" r="11" fill="#1a1010"/><circle cx="52" cy="-4" r="11" fill="#1a1010"/>'
    : '<ellipse cx="-52" cy="0" rx="13" ry="17" fill="#1a1010"/><ellipse cx="52" cy="0" rx="13" ry="17" fill="#1a1010"/><circle cx="-47" cy="-6" r="5" fill="#fff"/><circle cx="57" cy="-6" r="5" fill="#fff"/>';
  return `<g id="${id}">
  <defs>${lin(id + 's', o.shirtL || '#a8d2f6', shirt, 1, 1)}${rad(id + 'k', '#ffe2cc', skin, .4, .3, .8)}${blur(id + 'f', 16)}</defs>
  ${o.noShadow ? '' : shadow(id + 'f', 200, 34, .3)}
  ${o.sitting ? `<path d="M-120 -330 h240 v80 h-240z" fill="${pants}"/><path d="M60 -300 h200 v300 h-80 v-220 h-120z" fill="${pants}"/>`
    : `<path d="M-100 -340 h200 l-10 340 h-70 l-20 -260 l-20 260 h-70z" fill="${pants}"/><ellipse cx="-50" cy="-4" rx="56" ry="20" fill="#2a2a2a"/><ellipse cx="50" cy="-4" rx="56" ry="20" fill="#2a2a2a"/>`}
  <path d="M-130 -640 q130 -50 260 0 l20 330 h-300z" fill="url(#${id}s)"/>
  ${o.pajama ? `<g fill="#fff" opacity=".5">${[0, 1, 2, 3].map(i => `<circle cx="${-60 + (i % 2) * 110}" cy="${-560 + i * 60}" r="12"/>`).join('')}</g>` : ''}
  <g stroke="url(#${id}s)" stroke-width="66" stroke-linecap="round" fill="none">${arms}</g>
  <g fill="url(#${id}k)">${hands}</g>
  <rect x="-34" y="-700" width="68" height="70" fill="${skin}"/>
  <g id="${id}-head" transform="translate(0 -820)">
   ${o.short ? `<path d="M-132 0 q-10 -160 132 -164 q142 4 132 164 l-10 20 h-244z" fill="${hair}"/><ellipse cx="-128" cy="20" rx="26" ry="36" fill="${skin}"/><ellipse cx="128" cy="20" rx="26" ry="36" fill="${skin}"/>` : `<path d="M-150 -20 q-20 -170 150 -180 q170 10 150 180 l10 150 q-40 20 -60 -10 l-10 -90 h-180 l-10 90 q-20 30 -60 10z" fill="${hair}"/>`}
   <ellipse cx="0" cy="0" rx="124" ry="140" fill="url(#${id}k)"/>
   <path d="M-128 -30 q10 -130 128 -136 q118 6 128 136 q-60 -70 -128 -76 q-70 6 -128 76z" fill="${hair}"/>
   ${o.cap ? `<path d="M-140 -60 q0 -130 140 -130 q140 0 140 130z" fill="${o.cap}"/><path d="M-150 -60 h300 q20 0 10 20 h-320 q-10 -20 10 -20z" fill="#1a2238"/><path d="M-40 -60 q40 34 160 14 q-40 -10 -60 -14z" fill="#141a2c"/><g transform="translate(0 -120)"><path d="M0 -26 l22 10 v20 q0 20 -22 28 q-22 -8 -22 -28 v-20z" fill="#f2c24a"/></g>` : ''}
   ${o.stache ? `<path d="M-60 36 q30 -24 60 -4 q30 -20 60 4 q-30 20 -60 6 q-30 14 -60 -6z" fill="${o.hair || '#2a2228'}"/>` : ''}
   ${o.gray ? `<path d="M-60 -150 q60 -20 120 0" stroke="#bdb6b0" stroke-width="12" fill="none" opacity=".8"/>` : ''}
   <g id="${id}-eyes">${eyes}</g>
   <ellipse cx="-80" cy="40" rx="24" ry="13" fill="#ff8a8a" opacity=".4"/><ellipse cx="80" cy="40" rx="24" ry="13" fill="#ff8a8a" opacity=".4"/>
   ${mouth}
   ${o.tear ? '<path d="M-56 20 q-12 34 0 52 q14 -16 0 -52z M56 20 q-12 34 0 52 q14 -16 0 -52z" fill="#9fd8ff" opacity=".9"/>' : ''}
  </g>
 </g>`;
}

// ───────── 장면 ─────────
// 1. 침실 아침: 침대에서 비명 지르는 주인 + 이불 위 강아지
A.bedroom = {
  build: o => `<defs>${lin('br-w', '#ffe9cf', '#f2c9a0')}${halo('br-sun', '#fff2c0', .85)}${lin('br-bl', '#9cc6ff', '#5f8fe0', 1, 1)}${blur('br-b', 30)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#br-w)"/>
  <g transform="translate(1250 -250)"><rect x="0" y="0" width="560" height="760" rx="20" fill="#bfe4ff"/><circle cx="400" cy="200" r="90" fill="#fffbe0"/>
   <path d="M0 0 h560 v760 h-560z M280 0 v760 M0 380 h560" stroke="#fff" stroke-width="22" fill="none"/>
   <path d="M-60 -40 q90 400 40 860 h-80z M620 -40 q-90 400 -40 860 h80z" fill="#f28a6a"/></g>
  <path d="M1250 -250 L300 1500 L1100 1500 L1810 510z" fill="#fff6d0" opacity=".22"/>
  <circle cx="1530" cy="0" r="700" fill="url(#br-sun)" opacity=".6"/>
  <rect x="-600" y="1150" width="3240" height="900" fill="#c58a5a"/><path d="M-600 1150 h3240" stroke="#a86e40" stroke-width="12"/>
  <rect x="-200" y="330" width="260" height="840" rx="30" fill="#8a5a3a"/>
  <path d="M0 760 q900 -60 1700 0 v400 h-1700z" fill="#fffaf2"/>
  <g transform="translate(520 1010) scale(.95)">${human('br-p', o.calm ? {pose: 'stand', shirt: '#f29ab8', shirtL: '#ffc8da', pajama: true, sitting: true, noShadow: true} : {pose: 'shock', mouth: 'o', eyes: 'wide', shirt: '#f29ab8', shirtL: '#ffc8da', pajama: true, sitting: true, noShadow: true})}</g>
  <path d="M-40 840 q900 -90 1780 -10 l40 380 h-1860z" fill="url(#br-bl)"/>
  <path d="M100 900 q300 -40 600 10 M800 880 q400 -40 800 10" stroke="#fff" stroke-width="10" fill="none" opacity=".4"/>
  <ellipse cx="300" cy="700" rx="230" ry="90" fill="#fff" />
  <g transform="translate(1320 1040) scale(.9)">${dog2('br-d')}</g>
  ${o.gift ? `<g transform="translate(1700 1050)"><rect x="-150" y="-180" width="300" height="180" rx="12" fill="#5ab0e8"/><rect x="-160" y="-210" width="320" height="50" rx="10" fill="#4a98d0"/><rect x="-20" y="-210" width="40" height="210" fill="#ff5a6a"/><path d="M0 -210 q-80 -90 -100 -20 q40 20 100 20 q60 0 100 -20 q-20 -70 -100 20z" fill="#ff5a6a"/></g>` : ''}`,
  tick: (root, t, p, o) => {
    tickDog2(root, 'br-d', t, 0);
    if (!o.calm) at(q(root, 'br-p-head'), 'transform', `translate(${Math.sin(t * 40) * 4} -820)`);
  },
};

// 2. 부엌: 빈 밥그릇 + 커피잔 떨어뜨리는 주인
A.kitchen2 = {
  build: o => `<defs>${lin('k2-w', '#e8f4ee', '#cfe3d8')}${halo('k2-l', '#fff7d8', .8)}${lin('k2-c', '#ffffff', '#dfe6ea')}${blur('k2-b', 10)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#k2-w)"/>
  <g fill="#fff" stroke="#d6e4dc" stroke-width="4">${Array.from({length: 60}, (_, i) => `<rect x="${-400 + (i % 12) * 240}" y="${-200 + Math.floor(i / 12) * 140}" width="240" height="140"/>`).join('')}</g>
  <rect x="-600" y="-900" width="3240" height="700" fill="#cfe3d8"/>
  <g>${[0, 1, 2, 3].map(i => `<rect x="${-300 + i * 520}" y="-700" width="480" height="440" rx="16" fill="#7fb59a"/><circle cx="${-90 + i * 520}" cy="-300" r="12" fill="#e8c86a"/>`).join('')}</g>
  <rect x="-600" y="560" width="3240" height="60" fill="#f4efe6"/><rect x="-600" y="620" width="3240" height="560" fill="#7fb59a"/>
  <g>${[0, 1, 2, 3, 4, 5].map(i => `<rect x="${-560 + i * 520}" y="660" width="480" height="480" rx="14" fill="#8fc5aa"/><rect x="${-340 + i * 520}" y="700" width="40" height="12" rx="6" fill="#e8c86a"/>`).join('')}</g>
  <rect x="-600" y="1180" width="3240" height="900" fill="#e4d2b4"/>
  <g fill="none" stroke="#d2bc98" stroke-width="5">${Array.from({length: 14}, (_, i) => `<path d="M${-600 + i * 260} 1180 l-200 900"/>`).join('')}</g>
  <circle cx="1020" cy="-200" r="800" fill="url(#k2-l)" opacity=".4"/>
  <g transform="translate(560 1260) scale(.95)">${human('k2-p', {pose: o.pose || 'drop', mouth: 'o', eyes: 'wide', shirt: '#f29ab8', shirtL: '#ffc8da', pajama: true})}</g>
  ${o.mug !== false ? `<g id="k2-mug"><g transform="rotate(30)"><rect x="-50" y="-60" width="100" height="120" rx="16" fill="url(#k2-c)"/><path d="M50 -30 q50 0 50 30 q0 30 -50 30" stroke="#dfe6ea" stroke-width="16" fill="none"/></g>
   <g id="k2-splash" fill="#7a4a2a">${Array.from({length: 9}, (_, i) => `<circle cx="${Math.cos(i) * 90}" cy="${-70 - Math.sin(i * 1.7) * 60}" r="${10 + (i % 3) * 6}"/>`).join('')}<path d="M-50 -60 q50 -80 100 0z"/></g></g>` : ''}
  <g transform="translate(1360 1420)"><ellipse rx="150" ry="40" fill="#2d64b8"/><path d="M-150 0 q150 90 300 0" fill="#1f4f98"/><ellipse rx="120" ry="26" fill="#173e7a"/></g>
  <g transform="translate(1560 1440) scale(.95)">${dog2('k2-d', {tilt: -6})}</g>`,
  tick: (root, t, p) => {
    tickDog2(root, 'k2-d', t, 1, {tilt: -6});
    const m = q(root, 'k2-mug');
    if (m) { const f = (t * 1.3) % 1; at(m, 'transform', `translate(${860 + f * 60} ${520 + f * f * 600}) rotate(${f * 200})`); }
  },
};

// 3. 뉴스 스튜디오
A.news2 = {
  build: o => `<defs>${rad('n2-bg', '#3d7ae0', '#06142e', .5, .35, .9)}${lin('n2-d', '#ffffff', '#c9d6ea')}${halo('n2-s', '#9cc8ff', .7)}${blur('n2-b', 6)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#n2-bg)"/>
  <g opacity=".5">${Array.from({length: 7}, (_, i) => `<rect x="${-300 + i * 400}" y="-700" width="340" height="560" rx="10" fill="#0e2550" stroke="#4f8ae0" stroke-width="4"/>`).join('')}</g>
  <g stroke="#8ab8ff" stroke-width="3" fill="none" opacity=".45"><circle cx="1020" cy="200" r="460"/><ellipse cx="1020" cy="200" rx="200" ry="460"/><path d="M560 200 h920 M620 0 h800 M620 400 h800"/></g>
  <circle cx="1020" cy="200" r="700" fill="url(#n2-s)" opacity=".35"/>
  <g transform="translate(1340 -260)"><rect width="600" height="380" rx="20" fill="#0a1c3e" stroke="#bcd6ff" stroke-width="8"/>
   <rect x="0" y="0" width="600" height="90" rx="20" fill="#e0382c"/><text x="300" y="66" font-family="Gothic" font-size="58" fill="#fff" text-anchor="middle">속보</text>
   <text x="300" y="200" font-family="Gothic" font-size="56" fill="#fff" text-anchor="middle">${o.screen1 || '강아지가'}</text>
   <text x="300" y="290" font-family="Gothic" font-size="56" fill="#ffd84a" text-anchor="middle">${o.screen2 || '말을 한다'}</text></g>
  <g transform="translate(1020 1120)">${dog2('n2-d', {tie: true})}</g>
  <path d="M120 1000 h1800 l-120 420 h-1560z" fill="url(#n2-d)"/><path d="M120 1000 h1800 v50 h-1800z" fill="#e0382c"/>
  <path d="M240 1100 h1560" stroke="#9fb4d4" stroke-width="4"/>
  <text x="1020" y="1260" font-family="Gothic" font-size="80" fill="#13284e" text-anchor="middle">멍멍 뉴스</text>
  <rect x="-600" y="1420" width="3240" height="700" fill="#0a1630"/>`,
  tick: (root, t) => tickDog2(root, 'n2-d', t, 2),
};

// 4. 소파 + 간식 더미 + 창가 고양이
A.sofa = {
  build: o => `<defs>${lin('sf-w', '#f6d9b8', '#e8b98e')}${rad('sf-c', '#ff9a7a', '#c4503a', .4, .2, .9)}${halo('sf-l', '#fff2c8', .8)}${rad('sf-cat', '#c8ccd6', '#6a7080', .35, .3, .85)}${blur('sf-b', 18)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#sf-w)"/>
  <g transform="translate(1300 -420)"><rect width="700" height="700" rx="16" fill="#9fd4ff"/><circle cx="560" cy="160" r="80" fill="#fffbe0"/>
   <path d="M0 0 h700 v700 h-700z M350 0 v700" stroke="#fff" stroke-width="22" fill="none"/><rect x="-40" y="690" width="780" height="50" rx="10" fill="#fff"/></g>
  <circle cx="1650" cy="-100" r="700" fill="url(#sf-l)" opacity=".5"/>
  <g transform="translate(1640 280)"><g transform="translate(0 4)">${shadow('sf-b', 140, 20, .25)}</g>
   <path id="sf-tail" d="M110 -10 q120 -20 110 -150" stroke="url(#sf-cat)" stroke-width="40" fill="none" stroke-linecap="round"/>
   <path d="M-140 0 q-20 -200 140 -210 q160 10 140 210z" fill="url(#sf-cat)"/>
   <g transform="translate(-10 -250)"><path d="M-110 -40 l-10 -120 l90 70z M110 -40 l10 -120 l-90 70z" fill="#8a909c"/>
    <ellipse rx="130" ry="110" fill="url(#sf-cat)"/>
    <path d="M-80 -10 q26 14 52 0 M28 -10 q26 14 52 0" stroke="#2a2a30" stroke-width="10" fill="none" stroke-linecap="round"/>
    <path d="M-6 30 l12 0 l-6 10z" fill="#e88a9a"/><path d="M0 40 q-20 20 -36 6 M0 40 q20 20 36 6" stroke="#3a3a40" stroke-width="5" fill="none"/>
    <path d="M-60 40 h-90 M-60 56 h-80 M60 40 h90 M60 56 h80" stroke="#fff" stroke-width="3" opacity=".7"/></g></g>
  <rect x="-600" y="1250" width="3240" height="900" fill="#b07a4e"/>
  <path d="M-300 700 q100 -80 300 -60 h1000 q200 -20 300 60 v560 h-1600z" fill="url(#sf-c)"/>
  <rect x="-200" y="900" width="1400" height="240" rx="60" fill="#e0705a"/>
  <rect x="-380" y="700" width="200" height="560" rx="80" fill="#c4503a"/><rect x="1200" y="700" width="200" height="560" rx="80" fill="#c4503a"/>
  <g opacity="${o.owner ? 0 : 1}">${Array.from({length: 14}, (_, i) => `<g transform="translate(${150 + (i * 97) % 900} ${900 - (i % 4) * 40}) rotate(${(i * 37) % 60 - 30})">
    ${i % 3 ? `<rect x="-60" y="-80" width="120" height="160" rx="14" fill="${['#ffcf3a', '#3ab0ff', '#ff6a8a'][i % 3]}"/><rect x="-60" y="-80" width="120" height="30" fill="#fff" opacity=".6"/>`
      : `<path d="M-60 -20 a26 26 0 1 1 30 -20 h60 a26 26 0 1 1 30 20 a26 26 0 1 1 -30 20 h-60 a26 26 0 1 1 -30 -20z" fill="#fff4dc" stroke="#e8c89a" stroke-width="6"/>`}</g>`).join('')}</g>
  ${o.night ? `<rect x="-600" y="-900" width="3240" height="3000" fill="#0a1030" opacity=".5"/><circle cx="600" cy="700" r="800" fill="url(#sf-l)" opacity=".35"/>` : ''}
  ${o.owner ? `<g transform="translate(220 1180) scale(.95)">${human('sf-p', {sitting: true, eyes: o.owner === 'laugh' ? 'closed' : 'closed', mouth: o.owner === 'laugh' ? 'smile' : 'sad', tear: true, shirt: '#9a8ac8', shirtL: '#c8bce8', noShadow: true})}</g>` : ''}
  <g transform="translate(${o.owner ? 820 : 640} 1060) rotate(${o.owner ? 0 : -8}) scale(.95)">${dog2('sf-d', {mouth: o.owner ? 0 : .5})}</g>`,
  tick: (root, t, p, o) => {
    tickDog2(root, 'sf-d', t, 3, {mouth: o.owner ? 0 : .5});
    at(q(root, 'sf-tail'), 'transform', `rotate(${Math.sin(t * 1.5) * 8} 110 -10)`);
  },
};

// 5. 공항 보안 검색대
A.airport2 = {
  build: o => `<defs>${lin('a2-w', '#eef3f8', '#c6d2de')}${lin('a2-m', '#6a7686', '#3a4452')}${halo('a2-l', '#ffffff', .8)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#a2-w)"/>
  <g fill="#dbe4ee">${Array.from({length: 9}, (_, i) => `<rect x="${-560 + i * 380}" y="-800" width="340" height="1100" rx="8"/>`).join('')}</g>
  <g fill="#ffffff" opacity=".8">${Array.from({length: 9}, (_, i) => `<rect x="${-500 + i * 380}" y="-860" width="220" height="30" rx="15"/>`).join('')}</g>
  <rect x="160" y="-300" width="720" height="140" rx="16" fill="#f5c400"/><text x="520" y="-205" font-family="Gothic" font-size="84" fill="#1a1a1a" text-anchor="middle">보안 검색</text>
  <g opacity=".75">${[0, 1, 2, 3].map(i => `<g transform="translate(${1460 + i * 230} 980) scale(.62)">${human('a2-q' + i, {shirt: ['#6a8ab0', '#b08a6a', '#8ab08a', '#a06a8a'][i], shirtL: '#d8e0ea', hair: '#2a2228', noShadow: true})}</g>`).join('')}</g>
  <rect x="-600" y="980" width="3240" height="1100" fill="#aab6c4"/><path d="M-600 980 h3240" stroke="#8a96a4" stroke-width="10"/>
  <rect x="-300" y="700" width="1700" height="90" rx="12" fill="#2e3642"/><rect x="-300" y="790" width="1700" height="200" fill="#4a5462"/>
  <rect x="380" y="300" width="480" height="420" rx="30" fill="url(#a2-m)"/><rect x="430" y="350" width="380" height="370" rx="14" fill="#141a24"/>
  <g id="a2-al" transform="translate(620 250)"><circle r="56" fill="#ff3a2a"/><circle r="90" fill="#ff3a2a" opacity=".25"/><text y="24" font-family="Gothic" font-size="74" fill="#fff" text-anchor="middle">!</text></g>
  <svg x="-300" y="540" width="1700" height="170" overflow="hidden"><g id="a2-bags">
   ${Array.from({length: 8}, (_, i) => `<g transform="translate(${i * 380} 0)"><rect x="0" y="40" width="260" height="130" rx="20" fill="${['#e0603a', '#3a7ad8', '#4aa86a', '#9a5ad8'][i % 4]}"/><rect x="95" y="14" width="70" height="32" rx="10" fill="none" stroke="#222" stroke-width="10"/></g>`).join('')}</g></svg>
  <g transform="translate(1180 1250) scale(.95)">${dog2('a2-d', {vest: '#2f62b0'})}</g>
  <text x="1124" y="955" font-family="Gothic" font-size="34" fill="#1d2a44" text-anchor="middle">보안</text>`,
  tick: (root, t) => {
    tickDog2(root, 'a2-d', t, 4);
    at(q(root, 'a2-bags'), 'transform', `translate(${-((t * 110) % 380)} 0)`);
    at(q(root, 'a2-al'), 'opacity', Math.sin(t * 9) > 0 ? 1 : .35);
  },
};

// 6. 눈 덮인 산 구조견 (밤)
A.rescue = {
  build: o => `<defs>${lin('rs-s', '#0a1430', '#2a3a6a')}${halo('rs-h', '#fff6c8', .9)}${lin('rs-m', '#e8f0ff', '#9fb2d8')}${blur('rs-b', 8)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#rs-s)"/>
  <g fill="#fff">${Array.from({length: 80}, (_, i) => `<circle cx="${(i * 233) % 3200 - 600}" cy="${(i * 137) % 1200 - 800}" r="${1 + i % 3}" opacity="${.3 + (i % 5) / 8}"/>`).join('')}</g>
  <path d="M-600 500 l500 -700 l400 500 l500 -900 l600 800 l400 -400 l700 900 v2000 h-3240z" fill="#3a4a78"/>
  <path d="M-100 -200 l100 140 l80 -60 l120 120 M900 -400 l160 220 l100 -80 l140 160" stroke="#e8f0ff" stroke-width="30" fill="none" stroke-linejoin="round"/>
  <path d="M-600 900 q800 -260 1600 -100 q900 160 1640 -80 v1400 h-3240z" fill="url(#rs-m)"/>
  <g>${[0, 1, 2].map(i => `<g transform="translate(${1500 + i * 220} 800)"><circle r="70" fill="url(#rs-h)"/><circle r="14" fill="#fffbe0"/></g>`).join('')}</g>
  <path id="rs-beam" d="M1060 760 L-400 200 L-400 1300z" fill="#fff6c8" opacity=".18"/>
  <g transform="translate(1000 1200)">${dog2('rs-d', {vest: '#ff7a1a', lamp: true})}</g>
  <g id="rs-snow" fill="#fff">${Array.from({length: 120}, (_, i) => `<circle cx="${(i * 173) % 3240 - 600}" cy="${(i * 97) % 2600 - 900}" r="${3 + i % 5}" opacity=".8"/>`).join('')}</g>`,
  tick: (root, t) => {
    tickDog2(root, 'rs-d', t, 5);
    at(q(root, 'rs-snow'), 'transform', `translate(${Math.sin(t) * 40} ${(t * 120) % 400})`);
    at(q(root, 'rs-beam'), 'opacity', .14 + Math.sin(t * 2) * .04);
  },
};

// 7. 강아지 선생님 교실
A.school = {
  build: o => `<defs>${lin('sc-w', '#fff4d8', '#f2dcae')}${halo('sc-l', '#fffbe8', .8)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#sc-w)"/>
  <rect x="200" y="-300" width="1640" height="820" rx="20" fill="#2f6a4a" stroke="#a87a4a" stroke-width="30"/>
  <text x="1020" y="-80" font-family="Gothic" font-size="110" fill="#f2f6ea" text-anchor="middle">${o.board || '오늘의 수업'}</text>
  <text x="1020" y="80" font-family="Gothic" font-size="90" fill="#ffe08a" text-anchor="middle">${o.board2 || '산책 줄 당기지 않기'}</text>
  <path d="M380 200 q200 -60 400 0 t400 0" stroke="#f2f6ea" stroke-width="10" fill="none" opacity=".6"/>
  <rect x="-600" y="1150" width="3240" height="900" fill="#d8a878"/>
  <g transform="translate(1400 1100) scale(.9)">${dog2('sc-d', {glasses: true})}</g>
  ${[0, 1, 2, 3, 4].map(i => `<g transform="translate(${-80 + i * 400} ${1560 + (i % 2) * 60})">
    <rect x="-160" y="-80" width="320" height="40" rx="10" fill="#b87a4a"/><rect x="-140" y="-40" width="24" height="200" fill="#8a5a3a"/><rect x="116" y="-40" width="24" height="200" fill="#8a5a3a"/>
    <g transform="translate(0 -60) scale(.42)">${dog2('sc-p' + i, {fur: ['#e8914a', '#f4efe6', '#4a3a30', '#c9a26a', '#e8914a'][i], furL: ['#f6b070', '#ffffff', '#7a6050', '#e8c890', '#f6b070'][i], fur2: ['#b8612a', '#c8c0b8', '#2a1e18', '#9a7a4a', '#b8612a'][i]})}</g></g>`).join('')}`,
  tick: (root, t) => { tickDog2(root, 'sc-d', t, 6); [0, 1, 2, 3, 4].forEach(i => tickDog2(root, 'sc-p' + i, t, i + 2, {who: 'none'})); },
};

// 8. 5년 뒤 도시 (네온, 강아지와 걷는 사람들)
A.city2 = {
  build: o => `<defs>${lin('c2-s', '#1a1040', '#e0705a')}${halo('c2-n', '#ff7ad0', .8)}${halo('c2-n2', '#5af0ff', .8)}${lin('c2-r', '#2a2036', '#120c1c')}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#c2-s)"/>
  <g fill="#2a1e40">${Array.from({length: 12}, (_, i) => `<rect x="${-600 + i * 290}" y="${-500 + (i * 173) % 500}" width="260" height="1800"/>`).join('')}</g>
  <g fill="#ffd98a" opacity=".85">${Array.from({length: 160}, (_, i) => `<rect x="${-570 + (i % 24) * 145 + (Math.floor(i / 24) % 2) * 40}" y="${-300 + Math.floor(i / 24) * 150}" width="40" height="60" opacity="${(i * 7) % 3 ? 1 : .25}"/>`).join('')}</g>
  <g transform="translate(120 200)"><rect width="560" height="200" rx="30" fill="#2a0a2a" stroke="#ff7ad0" stroke-width="12"/><circle cx="280" cy="100" r="360" fill="url(#c2-n)" opacity=".35"/>
   <text x="280" y="130" font-family="Gothic" font-size="96" fill="#ffd0f0" text-anchor="middle">멍 카페</text></g>
  <g transform="translate(1340 120)"><rect width="580" height="200" rx="30" fill="#0a2a30" stroke="#5af0ff" stroke-width="12"/><circle cx="290" cy="100" r="360" fill="url(#c2-n2)" opacity=".35"/>
   <text x="290" y="130" font-family="Gothic" font-size="96" fill="#d0fbff" text-anchor="middle">멍 학원</text></g>
  <rect x="-600" y="1150" width="3240" height="1000" fill="url(#c2-r)"/>
  <path d="M-600 1500 h3240" stroke="#ffd84a" stroke-width="12" stroke-dasharray="120 90" opacity=".7"/>
  <g id="c2-walk">${[0, 1, 2, 3, 4].map(i => `<g transform="translate(${-200 + i * 560} ${1250 + (i % 2) * 80}) scale(.8)">
    ${human('c2-h' + i, {shirt: ['#ff7a7a', '#7ab0ff', '#ffd27a', '#9a7aff', '#7affc8'][i], shirtL: '#ffffff', hair: ['#1d1620', '#5a3a2a', '#1d1620', '#2a2a2a', '#8a5a3a'][i]})}
    <path d="M150 -380 q120 120 220 300" stroke="#ff4a6a" stroke-width="6" fill="none"/>
    <g transform="translate(360 0) scale(.5)">${dog2('c2-d' + i, {fur: ['#e8914a', '#f4efe6', '#4a3a30', '#c9a26a', '#e8914a'][i], furL: ['#f6b070', '#ffffff', '#7a6050', '#e8c890', '#f6b070'][i], fur2: ['#b8612a', '#c8c0b8', '#2a1e18', '#9a7a4a', '#b8612a'][i]})}</g></g>`).join('')}</g>`,
  tick: (root, t) => {
    at(q(root, 'c2-walk'), 'transform', `translate(${-((t * 70) % 560)} 0)`);
    [0, 1, 2, 3, 4].forEach(i => tickDog2(root, 'c2-d' + i, t, i, {who: 'none'}));
  },
};

// 9. 강아지 방송 (RGB 방)
A.stream = {
  build: o => `<defs>${lin('st-w', '#3a1a6a', '#120a2a')}${halo('st-r', '#ffffff', .9)}${halo('st-p', '#ff4ad0', .7)}${halo('st-b', '#4ad8ff', .7)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#st-w)"/>
  <circle cx="-100" cy="0" r="700" fill="url(#st-p)" opacity=".55"/><circle cx="2140" cy="200" r="700" fill="url(#st-b)" opacity=".55"/>
  <g stroke-width="14" fill="none" opacity=".8"><path d="M-400 -600 h2840" stroke="#ff4ad0"/><path d="M-400 -560 h2840" stroke="#4ad8ff"/></g>
  <g transform="translate(1050 640)"><circle r="520" fill="none" stroke="#fff" stroke-width="40" opacity=".9"/><circle r="520" fill="url(#st-r)" opacity=".18"/></g>
  <g transform="translate(1500 -360)"><rect width="440" height="300" rx="20" fill="#0a0a18" stroke="#ff4ad0" stroke-width="8"/>
   <text x="220" y="110" font-family="Gothic" font-size="56" fill="#ff4a4a" text-anchor="middle">● LIVE</text>
   <text x="220" y="210" font-family="Gothic" font-size="54" fill="#fff" text-anchor="middle">시청자 1,203만</text></g>
  <g transform="translate(1020 1180)">${dog2('st-d', {headset: true})}</g>
  <rect x="-600" y="1100" width="3240" height="1000" fill="#1a1028"/><rect x="-200" y="1060" width="2440" height="80" rx="20" fill="#2a1a40"/>
  <g transform="translate(560 860)"><rect x="-30" y="0" width="60" height="220" fill="#2a2a3a"/><rect x="-70" y="-160" width="140" height="200" rx="70" fill="#3a3a5a"/><g fill="#6a6a8a">${[0, 1, 2, 3].map(i => `<rect x="-50" y="${-130 + i * 40}" width="100" height="10" rx="5"/>`).join('')}</g></g>`,
  tick: (root, t) => tickDog2(root, 'st-d', t, 7),
};

// 10. 투표소 앞 줄 선 강아지들
A.vote = {
  build: o => `<defs>${lin('vt-w', '#e8eef8', '#c8d4e8')}${halo('vt-l', '#ffffff', .7)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#vt-w)"/>
  <g fill="#b8c6dc">${Array.from({length: 8}, (_, i) => `<rect x="${-560 + i * 420}" y="-800" width="120" height="1900"/>`).join('')}</g>
  <rect x="100" y="-500" width="1840" height="180" rx="20" fill="#2a4a8a"/><text x="1020" y="-375" font-family="Gothic" font-size="100" fill="#fff" text-anchor="middle">투표소</text>
  <g transform="translate(1600 520)"><rect x="-180" y="0" width="360" height="560" fill="#5a7ab8"/><rect x="-220" y="-40" width="440" height="60" rx="10" fill="#3a5a98"/>
   <path d="M-180 0 h360 v120 h-360z" fill="#7a9ad8"/></g>
  <g transform="translate(1180 700)"><rect x="-120" y="0" width="240" height="220" rx="10" fill="#fff" stroke="#9aaccc" stroke-width="8"/><rect x="-70" y="-6" width="140" height="16" fill="#3a3a3a"/></g>
  <rect x="-600" y="1100" width="3240" height="1000" fill="#9aa8c0"/>
  ${[0, 1, 2, 3, 4].map(i => `<g transform="translate(${880 - i * 360} ${1260 + (i % 2) * 40}) scale(${.62 - i * .03})">${dog2('vt-d' + i, {fur: ['#e8914a', '#f4efe6', '#4a3a30', '#c9a26a', '#d8784a'][i], furL: ['#f6b070', '#ffffff', '#7a6050', '#e8c890', '#f0a070'][i], fur2: ['#b8612a', '#c8c0b8', '#2a1e18', '#9a7a4a', '#a85a30'][i]})}
    <rect x="120" y="-370" width="90" height="60" rx="6" fill="#fff" stroke="#9aaccc" stroke-width="5" transform="rotate(-12)"/></g>`).join('')}`,
  tick: (root, t) => [0, 1, 2, 3, 4].forEach(i => tickDog2(root, 'vt-d' + i, t, i, {who: 'none'})),
};

// 11. 10년 뒤 노을 진 마루 (뒷모습: 주인 + 늙은 강아지)
A.porch = {
  build: o => `<defs>${lin('pc-s', '#2a1a4a', '#ffb060')}${halo('pc-sun', '#fff0b0', .95)}${lin('pc-f', '#7a4a2a', '#4a2a18')}${blur('pc-b', 4)}</defs>
  <rect x="-600" y="-900" width="3240" height="3000" fill="url(#pc-s)"/>
  <circle cx="1100" cy="560" r="160" fill="#fff4c8"/><circle cx="1100" cy="560" r="760" fill="url(#pc-sun)" opacity=".75"/>
  <path d="M-600 720 q500 -120 1000 -40 q600 100 1200 -60 q500 -100 1040 20 v1400 h-3240z" fill="#5a3a5a" opacity=".85"/>
  <path d="M-600 860 q700 -80 1500 0 q800 70 1740 -20 v1300 h-3240z" fill="#3a2a3a"/>
  <g fill="#2a1a28">${[0, 1, 2, 3, 4, 5].map(i => `<path d="M${-500 + i * 520} 860 q20 -220 60 -300 q40 80 60 300z"/>`).join('')}</g>
  <rect x="-600" y="1080" width="3240" height="1000" fill="url(#pc-f)"/>
  <g stroke="#3a2010" stroke-width="6">${Array.from({length: 12}, (_, i) => `<path d="M-600 ${1120 + i * 80} h3240"/>`).join('')}</g>
  <rect x="-600" y="1060" width="3240" height="40" fill="#8a5a3a"/>
  <g transform="translate(720 1260) scale(-.9 .9)">${human('pc-p', {sitting: true, shirt: '#7a8ab0', shirtL: '#c8d0e8', gray: true, eyes: o.hug ? 'closed' : 'normal', pose: o.hug ? 'hug' : 'stand', noShadow: true})}</g>
  <g transform="translate(1180 1290) scale(.92)">${dog2('pc-d', {old: true, tear: !!o.tear})}</g>
  <g fill="#ffe8a8" opacity=".6">${Array.from({length: 26}, (_, i) => `<circle cx="${(i * 211) % 2400 - 200}" cy="${(i * 113) % 900 + 100}" r="${3 + i % 4}"/>`).join('')}</g>`,
  tick: (root, t) => tickDog2(root, 'pc-d', t, 8, {old: true, who: 'olddog'}),
};

Object.assign(window.SCENE_LIBRARY = window.SCENE_LIBRARY || {}, A);
