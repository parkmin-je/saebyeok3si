// 공포 장면들 (새벽 편의점 규칙 괴담). 세상 좌표 = 1080×1920 기준, 카메라 여유로 바깥도 조금 그린다.
// 무서움은 '안 보여주기'에서 나온다: 실루엣·유리 너머·CCTV 잡음·깜빡이는 형광등.
// 장면: hnote(규칙 쪽지), hstore(계산대에서 본 문), hcctv(천장 CCTV), hphone(어둠 속 휴대폰)

const HT = (x, y, s, c, t, a = 'start', f = 'Pen', ex = '') => `<text x="${x}" y="${y}" font-family="${f}" font-size="${s}" fill="${c}" text-anchor="${a}" ${ex}>${t}</text>`;
const RULES = [
  '1. 새벽 2시 이후엔 음악을 끄지 마세요.',
  '2. "아직 안 닫았죠?" 라고 물으면',
  '>절대 대답하지 마세요.',
  '3. 점장은 문을 두드리지 않습니다.',
  '4. 이상한 걸 봤다면, 못 본 척하세요.',
];

// 사람 실루엣 (긴 머리, 마른 몸, 팔이 길다). 얼굴은 그리지 않는다.
function figure(id, o = {}) {
  const c = o.color || '#050507';
  return `<g id="${id}">
    <path d="M-70 -560 q-10 -140 70 -150 q80 10 70 150 q4 90 -18 140 l30 30 q60 40 70 140 l24 330 q4 40 -20 44 l-10 -10 l-30 -300 l-14 300 l14 300 h-60 l-20 -280 l-20 280 h-60 l14 -300 l-14 -300 l-30 300 l-10 10 q-24 -4 -20 -44 l24 -330 q10 -100 70 -140 l30 -30 q-22 -50 -18 -140z" fill="${c}"/>
    <path d="M-74 -600 q-30 120 -40 260 l30 -10 q10 -150 30 -230z M74 -600 q30 120 40 260 l-30 -10 q-10 -150 -30 -230z" fill="${c}"/>
    ${o.eyes ? `<circle cx="-24" cy="-560" r="7" fill="#e8e8e8" opacity=".9"/><circle cx="24" cy="-560" r="7" fill="#e8e8e8" opacity=".9"/>` : ''}
  </g>`;
}

A.hnote = {
  build: o => `<defs>${rad('hn-l', '#fff6dc', '#000', .5, .48, .62)}${lin('hn-p', '#f4ecd6', '#d9ccaa')}${blur('hn-b', 18)}</defs>
    <rect x="-400" y="-400" width="1880" height="2720" fill="#07070a"/>
    <rect x="-400" y="-400" width="1880" height="2720" fill="url(#hn-l)" opacity=".55"/>
    <g opacity=".35">${Array.from({length: 14}, (_, i) => `<path d="M-400 ${-300 + i * 190} h1880" stroke="#000" stroke-width="3"/>`).join('')}</g>
    <g id="hn-paper" transform="translate(540 980) rotate(-3)">
      <rect x="-430" y="-560" width="880" height="1120" fill="#000" opacity=".5" filter="url(#hn-b)" transform="translate(16 24)"/>
      <rect x="-430" y="-560" width="860" height="1100" fill="url(#hn-p)"/>
      ${Array.from({length: 15}, (_, i) => `<path d="M-400 ${-380 + i * 62} h800" stroke="#9fb3c8" stroke-width="2" opacity=".5"/>`).join('')}
      <path d="M-330 -560 v1100" stroke="#e08a8a" stroke-width="3" opacity=".5"/>
      ${HT(0, -440, 84, '#1b1b22', '야간 근무 수칙', 'middle')}
      <path d="M-200 -410 q200 14 400 0" stroke="#1b1b22" stroke-width="5" fill="none"/>
      <g id="hn-rules">${RULES.map((r, i) => `<g id="hn-r${i}">${HT(r[0] === '>' ? -330 : -380, -300 + i * 124, 62, '#20202a', r.replace(/^>/, ''))}</g>`).join('')}</g>
      ${o.hl !== undefined ? `<rect id="hn-hl" x="-400" y="${-300 + o.hl * 124 - 66}" width="800" height="${o.hl === 1 ? 210 : 90}" fill="#ff2a2a" opacity=".18"/>` : ''}
      ${o.hl !== undefined ? `<path id="hn-ul" d="M-380 ${-300 + (o.hl + (o.hl === 1 ? 1 : 0)) * 124 + 18} q400 16 760 -4" stroke="#c0161c" stroke-width="7" fill="none" stroke-dasharray="900" stroke-dashoffset="900"/>` : ''}
      ${HT(160, 400, 50, '#20202a', '- 점장 -')}
      ${o.extra ? `<g id="hn-x" opacity="0">${HT(-380, 340, 60, '#8a0c10', '5. 이미 대답했다면, 뒤돌아보지 마세요.', 'start', 'Pen', 'transform="rotate(-2)"')}</g>` : ''}
    </g>
    <rect id="hn-dark" x="-400" y="-400" width="1880" height="2720" fill="#000" opacity="0"/>`,
  tick: (root, t, p, o) => {
    const ul = q(root, 'hn-ul');
    if (ul) at(ul, 'stroke-dashoffset', 900 * (1 - clamp((p - .15) / .4)));
    const x = q(root, 'hn-x');
    if (x) at(x, 'opacity', clamp((p - .3) / .5) * (.75 + .25 * Math.sin(t * 7)));
    // 손전등이 살짝 흔들리는 느낌
    at(q(root, 'hn-dark'), 'opacity', .06 + .05 * Math.sin(t * 2.3) + (Math.sin(t * 31) > .97 ? .3 : 0));
  },
};

// 계산대에서 정면으로 본 편의점 (문까지). 세상 1080×1920, 문은 가운데 위쪽.
A.hstore = {
  build: o => {
    const lightsOff = o.dark;
    const shelves = side => Array.from({length: 5}, (_, i) => {
      const y = 700 + i * 150, x = side < 0 ? -380 : 1100;
      return `<rect x="${x}" y="${y}" width="360" height="22" fill="#1d222b"/>` + Array.from({length: 6}, (_, k) => `<rect x="${x + 14 + k * 56}" y="${y - 70 - (k % 3) * 12}" width="44" height="${70 + (k % 3) * 12}" rx="6" fill="${['#3a2b3f', '#2b3a44', '#44362a', '#2f3f33'][(i + k) % 4]}"/>`).join('');
    }).join('');
    return `<defs>${lin('hs-f', '#2a2e36', '#0c0d10')}${lin('hs-w', '#1b1f27', '#0d0f14')}${halo('hs-l', '#e8fff4', .9)}${halo('hs-fr', '#7fe0ff', .7)}
        ${lin('hs-gl', '#0b1420', '#04070c')}${blur('hs-b', 10)}${blur('hs-b2', 4)}${halo('hs-st', '#ffcf7a', .8)}</defs>
      <rect x="-400" y="-500" width="1880" height="2900" fill="url(#hs-w)"/>
      <path d="M-400 1180 L360 900 H720 L1480 1180 V2400 H-400z" fill="url(#hs-f)"/>
      ${Array.from({length: 9}, (_, i) => `<path d="M${540 + (i - 4) * 40} 900 L${540 + (i - 4) * 420} 2400" stroke="#000" stroke-width="3" opacity=".35"/>`).join('')}
      <!-- 냉장고 (왼쪽 벽) -->
      <g id="hs-fridge"><path d="M-400 300 L320 560 V900 L-400 1180z" fill="#0f2430"/>
        <path d="M-400 340 L300 585 V880 L-400 1140z" fill="url(#hs-fr)" opacity="${lightsOff ? .15 : .45}"/>
        ${Array.from({length: 4}, (_, i) => `<path d="M${-380 + i * 170} ${380 + i * 60} V${1110 - i * 60}" stroke="#0a1218" stroke-width="10"/>`).join('')}</g>
      <g transform="translate(40 0)">${shelves(1)}</g>
      <!-- 유리문 -->
      <g transform="translate(540 0)">
        <rect x="-190" y="420" width="380" height="490" fill="url(#hs-gl)"/>
        <circle cx="120" cy="470" r="90" fill="url(#hs-st)" opacity=".35"/><circle cx="120" cy="470" r="14" fill="#ffe2a8" opacity=".8"/>
        <path d="M-190 860 H190" stroke="#121820" stroke-width="10" opacity=".6"/>
        ${o.fig === 'door' ? `<g id="hs-fig" transform="translate(${o.figx || -30} 912) scale(.62)" filter="url(#hs-b2)">${figure('hs-f', {color: '#000'})}</g>` : ''}
        ${o.hand ? `<g id="hs-hand" opacity="0" transform="translate(-40 640)"><path d="M-30 60 q-6 -60 6 -90 l10 40 l6 -80 l12 0 l2 80 l10 -86 l12 2 l-2 86 l12 -70 l12 4 l-8 80 q30 -30 40 -20 q-20 40 -40 74 q-20 30 -60 30z" fill="#c9d3dc" opacity=".35"/></g>` : ''}
        <rect x="-190" y="420" width="380" height="490" fill="none" stroke="#3a414c" stroke-width="18"/>
        <path d="M0 420 V910" stroke="#3a414c" stroke-width="12"/>
        <rect x="-40" y="640" width="24" height="90" rx="8" fill="#5a636e"/><rect x="16" y="640" width="24" height="90" rx="8" fill="#5a636e"/>
        ${HT(0, 395, 34, '#7fe0b0', 'OPEN 24', 'middle', 'Gothic', `id="hs-open" opacity="${lightsOff ? .15 : .9}"`)}
      </g>
      <!-- 천장 형광등 -->
      <g id="hs-lights">${[0, 1, 2].map(i => `<g id="hs-li${i}"><rect x="${300 - i * 60}" y="${120 + i * 90}" width="${480 + i * 120}" height="26" rx="10" fill="#f4fff8"/><ellipse cx="540" cy="${300 + i * 90}" rx="${700 + i * 200}" ry="360" fill="url(#hs-l)" opacity=".22"/></g>`).join('')}</g>
      <!-- 계산대 (아래) -->
      <path d="M-400 1500 H1480 V2400 H-400z" fill="#161a21"/><path d="M-400 1500 H1480 V1540 H-400z" fill="#2c323c"/>
      <rect x="640" y="1380" width="300" height="140" rx="12" fill="#0d1015"/><rect x="660" y="1395" width="260" height="100" rx="8" fill="#123" opacity=".9"/>
      ${HT(790, 1460, 40, '#59d38c', '03:33', 'middle', 'Gothic', 'id="hs-clock"')}
      <rect id="hs-dim" x="-400" y="-500" width="1880" height="2900" fill="#000" opacity="${lightsOff ? .55 : 0}"/>`;
  },
  tick: (root, t, p, o) => {
    // 형광등 깜빡임: 가끔 한두 개가 꺼졌다 켜진다
    [0, 1, 2].forEach(i => {
      const f = Math.sin(t * (13 + i * 7) + i * 2) > .93 || (o.flicker && Math.sin(t * 23 + i) > .4);
      at(q(root, 'hs-li' + i), 'opacity', o.dark ? .08 : f ? .15 : 1);
    });
    const fig = q(root, 'hs-fig');
    if (fig) {
      const knock = o.knock ? Math.max(0, Math.sin(t * 9)) ** 8 * 8 : 0;
      at(fig, 'transform', `translate(${(o.figx || -30) + knock} ${912 + Math.sin(t * .7) * 3}) scale(${.62 + p * (o.approach || 0)})`);
    }
    const hand = q(root, 'hs-hand');
    if (hand) at(hand, 'opacity', clamp((p - .2) / .3));
    const ck = q(root, 'hs-clock');
    if (ck) at(ck, 'opacity', (t % 1) < .5 ? 1 : .4);
  },
};

// 천장 구석 CCTV에서 내려다본 계산대. 직원은 뒷모습. o.fig: 'door' 면 문밖, 'behind' 면 직원 바로 뒤.
A.hcctv = {
  build: o => `<defs>${lin('hc-f', '#4a4f55', '#24272b')}${halo('hc-l', '#ffffff', .6)}${blur('hc-b', 3)}</defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="#2a2d31"/>
    <path d="M-400 600 L1480 300 V2400 H-400z" fill="url(#hc-f)"/>
    ${Array.from({length: 12}, (_, i) => `<path d="M${-400 + i * 180} ${600 - i * 28} L${-200 + i * 220} 2400" stroke="#000" stroke-width="3" opacity=".25"/>`).join('')}
    <!-- 문 (위쪽) -->
    <g transform="translate(700 380) skewY(-9)"><rect x="-170" y="-260" width="340" height="300" fill="#0b0d10"/><rect x="-170" y="-260" width="340" height="300" fill="none" stroke="#5a5f66" stroke-width="12"/><path d="M0 -260 V40" stroke="#5a5f66" stroke-width="8"/>
      ${o.fig === 'door' ? `<g transform="translate(-40 40) scale(.36)" filter="url(#hc-b)">${figure('hc-fd', {color: '#000'})}</g>` : ''}</g>
    <!-- 진열대 -->
    ${Array.from({length: 3}, (_, i) => `<path d="M${-200 + i * 260} ${700 - i * 40} l200 -30 v220 l-200 30z" fill="#3a3e44"/><path d="M${-200 + i * 260} ${700 - i * 40} l200 -30 l40 20 l-200 30z" fill="#555a61"/>`).join('')}
    <!-- 계산대와 직원 뒷모습 -->
    <path d="M-100 1320 L1180 1120 V1420 L-100 1640z" fill="#3c4047"/><path d="M-100 1320 L1180 1120 L1180 1160 L-100 1360z" fill="#686d75"/>
    <g transform="translate(560 1600)">
      <path d="M-230 40 q-10 -250 230 -280 q240 30 230 280z" fill="#4f7a63"/><path d="M-230 40 q-10 -250 230 -280 l0 40 q-190 30 -200 240z" fill="#3c5f4c"/>
      <path d="M-60 -236 l60 70 l60 -70" stroke="#d8efe0" stroke-width="10" fill="none"/>
      <ellipse cx="0" cy="-330" rx="96" ry="104" fill="#3a2a22"/><path d="M-96 -340 q10 -110 96 -112 q90 4 96 112 q-30 -60 -96 -60 q-66 0 -96 60z" fill="#1a120e"/>
      <ellipse cx="-96" cy="-320" rx="14" ry="26" fill="#c9a58a"/><ellipse cx="96" cy="-320" rx="14" ry="26" fill="#c9a58a"/>
    </g>
    ${o.fig === 'behind' ? `<g id="hc-fb" transform="translate(${o.fbx || 700} 1580) scale(.9)" filter="url(#hc-b)">${figure('hc-fbb', {color: '#050505', eyes: o.eyes})}</g>` : ''}
    <ellipse cx="540" cy="200" rx="900" ry="520" fill="url(#hc-l)" opacity=".18"/>`,
  tick: (root, t, p, o) => {
    const fb = q(root, 'hc-fb');
    if (fb) at(fb, 'opacity', o.pop ? (p > .35 ? 1 : 0) : 1);
  },
};

// 어둠 속에서 손에 든 휴대폰. 메신저 화면 (상표 없는 일반 디자인).
A.hphone = {
  build: o => {
    const msgs = o.msgs || [];
    return `<defs>${halo('hp-g', '#bcd6ff', .55)}${lin('hp-s', '#0e1118', '#151a24')}${blur('hp-b', 30)}</defs>
      <rect x="-400" y="-500" width="1880" height="2900" fill="#020204"/>
      <ellipse cx="540" cy="980" rx="760" ry="1000" fill="url(#hp-g)" opacity=".35"/>
      <g transform="translate(540 1000) rotate(-4)">
        <path d="M-470 520 q-80 160 -30 520 h520 q60 -260 0 -480z" fill="#1a1412"/>
        <rect x="-370" y="-760" width="740" height="1480" rx="90" fill="#050506"/>
        <rect x="-340" y="-720" width="680" height="1400" rx="64" fill="url(#hp-s)"/>
        <rect x="-340" y="-720" width="680" height="170" rx="64" fill="#1c2230"/>
        <circle cx="-250" cy="-630" r="44" fill="#4a5568"/>${HT(-250, -616, 40, '#cfd8e3', '점', 'middle', 'Gothic')}
        ${HT(-180, -610, 46, '#e8eef6', '점장님', 'start', 'Gothic')}
        ${msgs.map((m, i) => {
          const y = -420 + i * 230, me = m[0] === 'me', w = Math.min(560, 40 + m[1].length * 40);
          return `<g id="hp-m${i}" opacity="0"><rect x="${me ? 300 - w : -300}" y="${y}" width="${w}" height="130" rx="40" fill="${me ? '#f2d34a' : '#2a3242'}"/>
            ${HT(me ? 300 - w / 2 : -300 + w / 2, y + 82, 44, me ? '#1a1608' : '#eef2f7', m[1], 'middle', 'Gothic')}</g>`;
        }).join('')}
        ${o.typing ? `<g id="hp-ty" transform="translate(-230 ${-420 + msgs.length * 230 + 60})"><rect x="-70" y="-50" width="200" height="100" rx="40" fill="#2a3242"/>${[0, 1, 2].map(k => `<circle id="hp-d${k}" cx="${-20 + k * 50}" cy="0" r="14" fill="#9aa6b8"/>`).join('')}</g>` : ''}
      </g>`;
  },
  tick: (root, t, p, o) => {
    (o.msgs || []).forEach((m, i) => {
      const show = o.reveal ? clamp((p - (o.reveal[i] ?? 0)) / .08) : 1;
      const el = q(root, 'hp-m' + i);
      if (el) { at(el, 'opacity', show); }
    });
    [0, 1, 2].forEach(k => at(q(root, 'hp-d' + k), 'opacity', .3 + .7 * Math.max(0, Math.sin(t * 6 - k))));
  },
};

Object.assign(window.SCENE_LIBRARY, A);
