// 공포 2화 "도어락" 장면들. 새벽 아파트, 누가 밖에서 우리 집 비밀번호를 누른다.
// 장면: hhall(방문에서 본 어두운 복도 끝 현관), hlock(현관문 안쪽 도어락 클로즈업),
//       hpeep(문 구멍 어안 렌즈), hwall(거실 월패드 화면 속 복도 CCTV)
// 공통 o: beeps=[초..] 번호 누름, fail=초 틀림, ok=초 열림 (모두 컷 시작부터 초. 효과음과 같은 숫자를 쓴다)

const DLT = (x, y, s, c, t, a = 'start', f = 'Gothic', ex = '') => `<text x="${x}" y="${y}" font-family="${f}" font-size="${s}" fill="${c}" text-anchor="${a}" ${ex}>${t}</text>`;

// 지금 도어락 상태: 몇 자리 눌렀는지, 불빛 색
function lockAt(o, lt) {
  let n = 0, flash = null;
  (o.beeps || []).forEach(b => { if (lt >= b) { n++; if (lt - b < .14) flash = 'b'; } });
  if (o.fail != null && lt >= o.fail) {
    n = 0;
    if (lt - o.fail < 1.1) flash = Math.floor((lt - o.fail) * 9) % 2 ? 'r' : 'r2';
  }
  if (o.ok != null && lt >= o.ok) { n = 4; flash = 'g'; }
  return {n: Math.min(4, n), flash};
}
const LEDC = {b: '#5fb8ff', r: '#ff2a2a', r2: '#7a0c0c', g: '#46ff8a'};

// 긴 머리 여자가 웅크린 모습 / 선 모습 (얼굴 없음, 머리카락이 얼굴을 덮는다)
function crouch(c = '#0a0a0a') {
  return `<path d="M-40 0 q-30 -60 -10 -120 q10 -50 60 -60 q50 0 60 40 q20 40 10 90 q30 20 30 50 z" fill="${c}"/>
    <path d="M-6 -176 q-46 -4 -50 50 q-6 70 -20 110 l14 0 q10 -40 16 -70 q6 40 2 80 l12 -2 q4 -40 6 -60 q10 30 8 66 l12 -4 q0 -60 -6 -110 q20 -40 4 -60z" fill="${c}"/>
    <path d="M40 -120 q40 -40 56 -110 l10 4 q-10 70 -52 120z" fill="${c}"/>`;
}
function standing(c = '#0a0a0a') {
  return `<path d="M-30 -330 q-6 -60 34 -64 q40 4 34 64 q2 40 -8 60 l14 14 q26 18 30 64 l10 150 l-10 6 l-12 -130 l-6 130 l6 130 h-26 l-10 -124 l-8 124 h-26 l6 -130 l-6 -130 l-12 130 l-10 -6 l10 -150 q4 -46 30 -64 l14 -14 q-10 -20 -8 -60z" fill="${c}"/>
    <path d="M-34 -350 q-16 60 -20 150 l14 -4 q4 -80 14 -120z M34 -350 q16 60 20 150 l-14 -4 q-4 -80 -14 -120z" fill="${c}"/>`;
}

// 방문 앞에서 내다본 어두운 복도. 끝에 현관문. 세상 1080×1920, 소실점 (540, 860)
A.hhall = {
  build: o => `<defs>${lin('hh-w', '#0d0f14', '#050608')}${lin('hh-fl', '#141016', '#060507')}${halo('hh-sn', '#ffd9a0', .95)}${halo('hh-moon', '#6f8fc0', .6)}
      ${blur('hh-b', 6)}${blur('hh-b2', 22)}${lin('hh-door', '#1c1f26', '#101217')}${halo('hh-led', '#5fb8ff', 1)}</defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="#040406"/>
    <!-- 천장, 벽, 바닥 (원근) -->
    <path d="M-400 -500 H1480 L700 560 H380z" fill="#08090c"/>
    <path d="M-400 -500 L380 560 V1120 L-400 2400z" fill="url(#hh-w)"/>
    <path d="M1480 -500 L700 560 V1120 L1480 2400z" fill="url(#hh-w)"/>
    <path d="M-400 2400 L380 1120 H700 L1480 2400z" fill="url(#hh-fl)"/>
    ${Array.from({length: 10}, (_, i) => `<path d="M${380 + i * 35.5} 1120 L${-400 + i * 210} 2400" stroke="#000" stroke-width="3" opacity=".5"/>`).join('')}
    <!-- 왼쪽 방문 틈으로 새는 푸른 빛 -->
    <path d="M-60 300 L160 540 V1260 L-60 1620z" fill="#0b1018"/>
    <path d="M160 560 L230 640 V1200 L160 1250z" fill="url(#hh-moon)" opacity=".5"/>
    <ellipse cx="200" cy="1500" rx="260" ry="90" fill="url(#hh-moon)" opacity=".25"/>
    <!-- 액자 하나 (오른쪽 벽) -->
    <path d="M860 520 L960 470 V700 L860 730z" fill="#121318" stroke="#1d1f26" stroke-width="6"/>
    <!-- 현관 (한 칸 낮은 타일) -->
    <path d="M360 1100 H720 L760 1160 H320z" fill="#1a1b20"/>
    <g opacity=".9"><path d="M420 1132 q20 -16 48 -8 l6 18 h-60z" fill="#22252c"/><path d="M600 1140 q24 -14 54 -4 l2 16 h-62z" fill="#2a2024"/></g>
    <!-- 젖은 발자국: 현관에서 이쪽으로 -->
    <g id="hh-prints">${Array.from({length: 8}, (_, k) => { const y = 1150 + k * k * 11 + k * 40, sc = 1 + k * .32, x = 540 + (k % 2 ? 1 : -1) * (20 + k * 12);
      return `<g id="hh-p${k}" opacity="0" transform="translate(${x} ${y}) scale(${sc} ${sc * .55})"><path d="M-12 30 q-8 -30 -4 -50 q6 -16 18 -10 q8 6 6 24 q-2 20 -4 36 q-8 10 -16 0z" fill="#0c1419" opacity=".95"/>
        ${[[-10, -34, 5], [-2, -38, 4.5], [6, -37, 4], [12, -33, 3.5], [16, -27, 3]].map(([a, b, r]) => `<circle cx="${a}" cy="${b}" r="${r}" fill="#0c1419" opacity=".95"/>`).join('')}
        <path d="M-8 20 q-4 -20 0 -36" stroke="#8aa6b8" stroke-width="3" fill="none" opacity=".35"/></g>`; }).join('')}</g>
    <!-- 현관문 -->
    <g id="hh-doorg">
      <rect x="398" y="580" width="284" height="530" fill="#000"/>
      <g id="hh-door"><rect x="398" y="580" width="284" height="530" fill="url(#hh-door)"/>
        <rect x="414" y="600" width="252" height="490" fill="none" stroke="#252932" stroke-width="5"/>
        <!-- 도어락 안쪽 몸체 -->
        <rect x="612" y="760" width="44" height="150" rx="12" fill="#2a2e36"/>
        <rect x="620" y="790" width="28" height="10" rx="4" fill="#0c0e12"/>
        <rect id="hh-led" x="620" y="790" width="28" height="10" rx="4" fill="#5fb8ff" opacity="0"/>
        <path d="M630 840 h-46 q-8 0 -8 8 v6 q0 8 8 8 h46z" fill="#3a3f48"/>
      </g>
      <circle id="hh-ledglow" cx="634" cy="795" r="120" fill="url(#hh-led)" opacity="0"/>
      <rect x="390" y="572" width="300" height="546" fill="none" stroke="#14161b" stroke-width="16"/>
    </g>
    <!-- 현관 센서등 -->
    <ellipse cx="540" cy="540" rx="46" ry="12" fill="#1b1c20"/>
    <g id="hh-sensor" opacity="0">
      <ellipse cx="540" cy="540" rx="40" ry="10" fill="#fff2d6"/>
      <ellipse cx="540" cy="840" rx="520" ry="560" fill="url(#hh-sn)" opacity=".55"/>
      <path d="M500 548 L360 1140 H720 L580 548z" fill="#ffe7c0" opacity=".12"/>
    </g>
    <!-- 문틈 (빛이 닿지 않는 바깥 어둠) 과 틈을 잡는 손가락 -->
    <rect id="hh-gap" x="682" y="580" width="0" height="530" fill="#000"/>
    <!-- 문틈 안에서 들여다보는 얼굴 반쪽 (틈 밖으로는 안 나온다) -->
    <clipPath id="hh-gc"><rect id="hh-gcr" x="682" y="580" width="0" height="530"/></clipPath>
    <g id="hh-hand" opacity="0" clip-path="url(#hh-gc)"><g id="hh-face">
      <radialGradient id="hh-sk" cx=".45" cy=".42" r=".6"><stop offset="0" stop-color="#b8bdbb"/><stop offset=".7" stop-color="#7d8482"/><stop offset="1" stop-color="#2a2e2e"/></radialGradient>
      <ellipse cx="700" cy="728" rx="40" ry="64" fill="url(#hh-sk)"/>
      <ellipse cx="684" cy="716" rx="16" ry="12" fill="#2a2626" opacity=".7"/>
      <ellipse cx="684" cy="716" rx="11" ry="9" fill="#eceee8"/>
      <circle cx="682" cy="717" r="2.6" fill="#000"/>
      <path d="M680 780 q10 3 20 -1" stroke="#3e3030" stroke-width="2.5" fill="none" opacity=".8"/>
      <path d="M640 620 q60 -30 110 10 v280 l-14 -6 q-6 -110 -24 -190 q-20 -26 -40 -24 q-22 6 -34 40 q-6 80 -6 170 l-12 4 q-6 -170 20 -284z" fill="#030303"/>
      <path d="M664 660 q-2 70 8 180" stroke="#030303" stroke-width="5" fill="none"/>
      <path d="M694 664 q6 40 0 90" stroke="#030303" stroke-width="3" fill="none"/>
    </g></g>
    <!-- 앞쪽 방 문틀 (보는 사람이 서 있는 곳) -->
    <path d="M-400 -500 H60 V2400 H-400z M1020 -500 H1480 V2400 H1020z" fill="#020203"/>
    <path d="M60 -500 V2400" stroke="#0e0f13" stroke-width="22"/><path d="M1020 -500 V2400" stroke="#0e0f13" stroke-width="22"/>`,
  tick: (root, t, lt, o) => {
    const s = lockAt(o, lt);
    at(q(root, 'hh-led'), 'opacity', s.flash ? 1 : 0);
    at(q(root, 'hh-led'), 'fill', LEDC[s.flash] || '#5fb8ff');
    at(q(root, 'hh-ledglow'), 'opacity', s.flash === 'r2' ? .15 : s.flash ? .45 : 0);
    // 문이 천천히 열린다 (경첩은 왼쪽, 오른쪽에 틈)
    const op = o.openAt != null ? clamp((lt - o.openAt) / (o.openDur || 3)) : 0;
    const gap = ease(op) * (o.open || .2) * 284;
    at(q(root, 'hh-door'), 'transform', `translate(398 0) scale(${1 - gap / 284} 1) translate(-398 0)`);
    const hand = q(root, 'hh-hand');
    at(hand, 'opacity', o.handAt != null ? clamp((lt - o.handAt) / .5) : 0);
    at(q(root, 'hh-gcr'), 'x', 682 - gap);
    at(q(root, 'hh-gcr'), 'width', gap);
    at(q(root, 'hh-face'), 'transform', `translate(${-gap * .3} 0)`);
    at(q(root, 'hh-gap'), 'x', 682 - gap);
    at(q(root, 'hh-gap'), 'width', gap);
    // 센서등: 딸깍 켜지고 조금 떨린다
    const sn = o.sensorAt != null && lt >= o.sensorAt && !(o.sensorOff != null && lt >= o.sensorOff);
    for (let k = 0; k < 8; k++) at(q(root, 'hh-p' + k), 'opacity', o.prints != null && k < (o.printN ?? 8) && lt >= o.prints + k * (o.printStep || .5) ? 1 : 0);
    at(q(root, 'hh-sensor'), 'opacity', sn ? (lt - o.sensorAt < .08 ? .5 : .95 + .05 * Math.sin(t * 40)) : 0);
  },
};

// 현관문 안쪽 도어락 클로즈업. 아래 문틈으로 복도 불빛, 그 빛을 가리는 두 발 그림자.
A.hlock = {
  build: o => `<defs>${lin('hl-d', '#20232a', '#0f1115')}${lin('hl-m', '#3b4049', '#1d2026')}${lin('hl-h', '#4a505a', '#22262d')}${halo('hl-g', '#ffd9a0', .9)}${halo('hl-led', '#5fb8ff', 1)}${blur('hl-b', 8)}</defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="url(#hl-d)"/>
    ${Array.from({length: 7}, (_, i) => `<path d="M-400 ${-200 + i * 300} H1480" stroke="#0a0b0e" stroke-width="4" opacity=".7"/>`).join('')}
    <!-- 문 아래 틈 빛 -->
    <rect x="-400" y="1760" width="1880" height="16" fill="#ffd9a0" opacity=".85"/>
    <ellipse cx="540" cy="1800" rx="1000" ry="120" fill="url(#hl-g)" opacity=".35"/>
    <g id="hl-feet" opacity="0"><rect x="370" y="1756" width="130" height="22" fill="#050505" filter="url(#hl-b)"/><rect x="590" y="1756" width="130" height="22" fill="#050505" filter="url(#hl-b)"/></g>
    <rect x="-400" y="1776" width="1880" height="700" fill="#0a0907"/>
    <!-- 도어락 몸체 -->
    <g transform="translate(540 900)">
      <rect x="-200" y="-470" width="400" height="900" rx="60" fill="#000" opacity=".5" filter="url(#hl-b)" transform="translate(14 22)"/>
      <rect x="-200" y="-470" width="400" height="900" rx="60" fill="url(#hl-m)"/>
      <rect x="-200" y="-470" width="400" height="900" rx="60" fill="none" stroke="#545b66" stroke-width="4"/>
      <!-- 표시창 -->
      <rect x="-140" y="-380" width="280" height="120" rx="26" fill="#07090c"/>
      <g id="hl-dots">${[0, 1, 2, 3].map(k => `<circle id="hl-d${k}" cx="${-84 + k * 56}" cy="-320" r="16" fill="#1a2430"/>`).join('')}</g>
      <g id="hl-x" opacity="0">${DLT(0, -296, 70, '#ff2a2a', '✕', 'middle')}</g>
      <circle id="hl-ledg" cx="0" cy="-320" r="230" fill="url(#hl-led)" opacity="0"/>
      <!-- 손잡이 -->
      <g id="hl-handle" transform="translate(0 80)">
        <rect x="-60" y="-60" width="120" height="120" rx="30" fill="#2b3038"/>
        <path d="M-30 -24 H-330 q-30 0 -30 30 v12 q0 30 30 30 H-30z" fill="url(#hl-h)"/>
        <circle cx="0" cy="0" r="40" fill="#3a404a"/>
      </g>
      <rect x="-50" y="300" width="100" height="40" rx="12" fill="#1a1d22"/>${DLT(0, 330, 26, '#6b737e', 'OPEN', 'middle')}
    </g>`,
  tick: (root, t, lt, o) => {
    const s = lockAt(o, lt);
    [0, 1, 2, 3].forEach(k => at(q(root, 'hl-d' + k), 'fill', k < s.n ? (s.flash === 'g' ? '#46ff8a' : '#5fb8ff') : '#1a2430'));
    const red = s.flash === 'r' || s.flash === 'r2';
    at(q(root, 'hl-x'), 'opacity', s.flash === 'r' ? 1 : s.flash === 'r2' ? .3 : 0);
    if (red) [0, 1, 2, 3].forEach(k => at(q(root, 'hl-d' + k), 'fill', '#3a0a0a'));
    at(q(root, 'hl-ledg'), 'opacity', s.flash === 'g' ? .6 : s.flash === 'b' ? .45 : s.flash === 'r' ? .5 : 0);
    at(q(root, 'hl-ledg'), 'fill', `url(#${root.dataset.px}hl-led)`);
    q(root, 'hl-ledg') && (q(root, 'hl-ledg').style.filter = s.flash === 'r' ? 'hue-rotate(150deg) saturate(3)' : s.flash === 'g' ? 'hue-rotate(-80deg)' : '');
    at(q(root, 'hl-feet'), 'opacity', o.feetAt != null ? clamp((lt - o.feetAt) / .6) : 0);
    // 손잡이가 밖에서 눌린다 (덜컥, 덜컥)
    const tu = o.turnAt != null && lt >= o.turnAt ? Math.min(28, (lt - o.turnAt) * 60) * (Math.sin((lt - o.turnAt) * 18) > -.3 ? 1 : .6) : 0;
    at(q(root, 'hl-handle'), 'transform', `translate(0 80) rotate(${-tu})`);
  },
};

// 문 구멍(어안 렌즈)으로 본 복도. o.lightOn: 복도 센서등 켜진 시각, o.hairAt: 렌즈 아래로 머리카락 끝이 보이기 시작
A.hpeep = {
  build: o => `<defs>${rad('hp-v', '#000', '#000', .5, .5, .5)}${halo('hp-l', '#fff1d0', .9)}${lin('hp-w', '#5b5a55', '#2b2a27')}
      <clipPath id="hp-c"><circle cx="540" cy="900" r="420"/></clipPath>
      <radialGradient id="hp-edge" cx=".5" cy=".5" r=".5"><stop offset=".72" stop-color="#000" stop-opacity="0"/><stop offset=".97" stop-color="#000" stop-opacity=".95"/><stop offset="1" stop-color="#000"/></radialGradient>
      ${blur('hp-b', 2.5)}</defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="#000"/>
    <g clip-path="url(#hp-c)"><g id="hp-scene" filter="url(#hp-b)">
      <rect x="100" y="460" width="880" height="880" fill="#24231f"/>
      <!-- 맞은편 벽과 휘어진 복도 -->
      <path d="M100 460 Q540 640 980 460 V1340 Q540 1160 100 1340z" fill="url(#hp-w)"/>
      <path d="M100 1340 Q540 1100 980 1340 V1400 H100z" fill="#3a3832"/>
      <path d="M100 460 Q540 700 980 460 V420 H100z" fill="#4a4842"/>
      <!-- 맞은편 집 문 -->
      <path d="M430 650 Q540 630 650 650 V1150 Q540 1130 430 1150z" fill="#3e352c" stroke="#24201b" stroke-width="10"/>
      <rect x="606" y="880" width="20" height="70" rx="6" fill="#1b1a18"/>
      ${DLT(540, 615, 34, '#1c1b18', '1203', 'middle')}
      <!-- 소화전 -->
      <path d="M760 760 Q800 750 840 760 V1000 Q800 990 760 1000z" fill="#6b1a16"/>
      <!-- 복도 센서등 빛 -->
      <ellipse id="hp-lamp" cx="540" cy="520" rx="60" ry="16" fill="#fff6e0" opacity=".2"/>
      <ellipse id="hp-glow" cx="540" cy="760" rx="520" ry="520" fill="url(#hp-l)" opacity=".1"/>
      <!-- 렌즈 아래에서 올라오는 머리카락 끝 -->
      <g id="hp-hair" opacity="0">
        <ellipse cx="540" cy="1400" rx="300" ry="190" fill="#060606"/>
        ${Array.from({length: 22}, (_, k) => `<path d="M540 ${1230 + (k % 3) * 6} Q${300 + k * 22} ${1290 + Math.abs(k - 11) * 4} ${250 + k * 27} 1480" stroke="#1c1c1c" stroke-width="3" fill="none" opacity=".8"/>`).join('')}
        <path d="M540 1228 v14" stroke="#2a2a2a" stroke-width="4"/></g>
      <rect id="hp-dim" x="100" y="420" width="880" height="1000" fill="#000" opacity=".55"/>
    </g></g>
    <circle cx="540" cy="900" r="421" fill="url(#hp-edge)"/>
    <circle cx="540" cy="900" r="424" fill="none" stroke="#111" stroke-width="10"/>`,
  tick: (root, t, lt, o) => {
    const on = o.lightOn != null && lt >= o.lightOn && !(o.lightOff != null && lt >= o.lightOff);
    const fl = on && (Math.sin(t * 29) > .9) ? .4 : 1;
    at(q(root, 'hp-dim'), 'opacity', on ? .08 * fl + (1 - fl) * .5 : .7);
    at(q(root, 'hp-glow'), 'opacity', on ? .35 * fl : .03);
    at(q(root, 'hp-lamp'), 'opacity', on ? .95 * fl : .1);
    const h = q(root, 'hp-hair');
    const hp = o.hairAt != null ? clamp((lt - o.hairAt) / 2.2) : 0;
    at(h, 'opacity', hp ? 1 : 0);
    at(h, 'transform', `translate(0 ${200 - ease(hp) * 170})`);
    // 들여다보는 사람 숨에 따라 살짝 흔들림
    at(q(root, 'hp-scene'), 'transform', `translate(${Math.sin(t * 1.3) * 4} ${Math.sin(t * .9) * 3})`);
  },
};

// 거실 벽 월패드. 화면 = 우리 집 앞 복도 CCTV (흑백).
// o.fig: 'crouch' 웅크림 / 'stand' 서 있음, o.standAt: 일어서기 시작, o.lookAt: 고개를 카메라 쪽으로, o.offAt: 화면 꺼짐
A.hwall = {
  build: o => `<defs>${lin('hw-wall', '#121317', '#08090b')}${halo('hw-sg', '#cfe3ff', .7)}${lin('hw-body', '#d9dcdf', '#a9adb2')}${lin('hw-cf', '#6d6f72', '#2c2d30')}
      <clipPath id="hw-clip"><rect x="0" y="0" width="640" height="420"/></clipPath>${blur('hw-b', 1.6)}${blur('hw-bb', 30)}</defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="url(#hw-wall)"/>
    <ellipse id="hw-spill" cx="540" cy="900" rx="760" ry="640" fill="url(#hw-sg)" opacity=".35"/>
    <!-- 월패드 몸체 -->
    <g transform="translate(540 900)">
      <rect x="-410" y="-330" width="820" height="620" rx="36" fill="#000" opacity=".6" filter="url(#hw-bb)" transform="translate(10 26)"/>
      <rect x="-410" y="-330" width="820" height="620" rx="36" fill="url(#hw-body)"/>
      <rect x="-360" y="-290" width="720" height="470" rx="14" fill="#050608"/>
      <g transform="translate(-320 -264)">
        <g id="hw-screen" clip-path="url(#hw-clip)"><g filter="url(#hw-b)">
          <rect width="640" height="420" fill="#2a2b2e"/>
          <!-- 천장 구석에서 내려다본 복도 -->
          <path d="M0 0 H640 L400 120 H250z" fill="#3a3b3e"/>
          <path d="M0 0 L250 120 V260 L0 420z" fill="#4a4b4e"/>
          <path d="M640 0 L400 120 V260 L640 420z" fill="#55575a"/>
          <path d="M0 420 L250 260 H400 L640 420z" fill="url(#hw-cf)"/>
          <rect x="250" y="120" width="150" height="140" fill="#1e1f21"/>
          <!-- 우리 집 문 (오른쪽 벽, 가까이) -->
          <path d="M470 60 L590 0 V370 L470 330z" fill="#3a3530" stroke="#222" stroke-width="5"/>
          <rect x="482" y="190" width="14" height="40" fill="#151515"/>
          ${DLT(530, 50, 22, '#ddd', '1204', 'middle', 'Gothic', 'transform="skewY(-20)"')}
          <!-- 사람 -->
          <g id="hw-crouch" transform="translate(452 338) scale(.8)">${crouch()}</g>
          <g id="hw-stand" transform="translate(440 352) scale(.9)" opacity="0">${standing()}
            <g id="hw-face" opacity="0"><ellipse cx="0" cy="-322" rx="22" ry="28" fill="#e8e8e8"/><ellipse cx="-8" cy="-326" rx="5" ry="7" fill="#000"/><ellipse cx="8" cy="-326" rx="5" ry="7" fill="#000"/><path d="M-30 -350 q30 -16 60 0 l-4 40 q-26 -24 -52 0z" fill="#0a0a0a"/></g></g>
          <ellipse cx="320" cy="40" rx="260" ry="120" fill="#fff" opacity=".12"/>
        </g>
        <g id="hw-noise"><rect width="640" height="420" fill="#fff" opacity="0"/></g>
        ${DLT(16, 34, 24, '#e8ffe8', '세대현관 CAM', 'start', 'Gothic', 'opacity=".9"')}
        ${DLT(624, 404, 24, '#e8ffe8', '03:13', 'end', 'Gothic', 'id="hw-clock"')}
        ${DLT(624, 34, 24, '#ff5040', '● REC', 'end', 'Gothic')}
        </g>
        <rect id="hw-off" x="0" y="0" width="640" height="420" fill="#000" opacity="0"/>
      </g>
      <!-- 버튼 -->
      ${['통화', '문열림', '종료'].map((b, i) => `<rect x="${-300 + i * 220}" y="200" width="160" height="60" rx="30" fill="#c3c6ca" stroke="#9a9ea4" stroke-width="3"/>${DLT(-220 + i * 220, 241, 28, '#4a4e55', b, 'middle')}`).join('')}
    </g>`,
  tick: (root, t, lt, o) => {
    const stand = o.fig === 'stand' || (o.standAt != null && lt >= o.standAt);
    const sp = o.standAt != null ? clamp((lt - o.standAt) / 1.2) : (o.fig === 'stand' ? 1 : 0);
    at(q(root, 'hw-crouch'), 'opacity', stand ? 1 - sp : 1);
    const st = q(root, 'hw-stand');
    at(st, 'opacity', stand ? sp : 0);
    at(st, 'transform', `translate(440 ${352 + (1 - ease(sp)) * 60}) scale(.9 ${.9 * (.6 + .4 * ease(sp))})`);
    at(q(root, 'hw-face'), 'opacity', o.lookAt != null && lt >= o.lookAt ? (lt - o.lookAt < .1 ? .4 : 1) : 0);
    // 화면 지직거림
    const glitch = Math.sin(t * 37) > .94 || (o.lookAt != null && lt >= o.lookAt && lt - o.lookAt < .5);
    at(q(root, 'hw-noise').firstChild, 'opacity', glitch ? .18 : 0);
    const off = o.offAt != null && lt >= o.offAt;
    at(q(root, 'hw-off'), 'opacity', off ? 1 : 0);
    at(q(root, 'hw-spill'), 'opacity', off ? 0 : .35);
    at(q(root, 'hw-clock'), 'opacity', (t % 1) < .5 ? .95 : .5);
  },
};

Object.assign(window.SCENE_LIBRARY, A);

// 침대에 누워서 본 내 방 문. 문 아래 틈으로 복도 불빛. o.lightOn/lightOff, o.feetAt(발 그림자), o.fingersAt(틈 아래로 나온 손가락)
A.hbed = {
  build: o => `<defs>${lin('hb-w', '#0b0c10', '#060709')}${halo('hb-g', '#ffd9a0', .9)}${blur('hb-b', 6)}${lin('hb-bl', '#1c1e26', '#0c0d11')}</defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="url(#hb-w)"/>
    <path d="M-400 1420 H1480 V2400 H-400z" fill="#08080a"/>
    <!-- 문 -->
    <rect x="380" y="560" width="320" height="760" fill="#121419"/><rect x="380" y="560" width="320" height="760" fill="none" stroke="#1b1e25" stroke-width="14"/>
    <circle cx="660" cy="960" r="14" fill="#262a32"/>
    <!-- 문 아래 틈 -->
    <rect id="hb-gap" x="386" y="1316" width="308" height="12" fill="#ffd9a0" opacity="0"/>
    <ellipse id="hb-glow" cx="540" cy="1340" rx="380" ry="70" fill="url(#hb-g)" opacity="0"/>
    <g id="hb-feet" opacity="0"><rect x="440" y="1314" width="80" height="16" fill="#050505" filter="url(#hb-b)"/><rect x="560" y="1314" width="80" height="16" fill="#050505" filter="url(#hb-b)"/></g>
    <g id="hb-fing" opacity="0">${[0, 1, 2, 3].map(k => `<path d="M${470 + k * 34} 1326 q${-6 + k * 3} 50 ${-4 + k * 2} 110 q7 12 14 0 q2 -60 -2 -110z" fill="#b9bfbf"/><path d="M${470 + k * 34 - 2 + k} 1428 l6 8" stroke="#3a2c2a" stroke-width="5" stroke-linecap="round"/>`).join('')}</g>
    <!-- 이불 (앞) -->
    <path d="M-400 1700 q500 -140 1000 -60 q500 60 880 0 V2400 H-400z" fill="url(#hb-bl)"/>
    <path d="M-400 1720 q500 -140 1000 -60 q500 60 880 0" stroke="#262935" stroke-width="10" fill="none"/>
    <rect id="hb-dim" x="-400" y="-500" width="1880" height="2900" fill="#000" opacity="0"/>`,
  tick: (root, t, lt, o) => {
    const on = o.lightOn != null && lt >= o.lightOn && !(o.lightOff != null && lt >= o.lightOff);
    at(q(root, 'hb-gap'), 'opacity', on ? .9 : 0);
    at(q(root, 'hb-glow'), 'opacity', on ? .35 : 0);
    at(q(root, 'hb-feet'), 'opacity', on && o.feetAt != null ? clamp((lt - o.feetAt) / .6) : 0);
    const f = o.fingersAt != null ? clamp((lt - o.fingersAt) / 1.8) : 0;
    at(q(root, 'hb-fing'), 'opacity', f ? 1 : 0);
    at(q(root, 'hb-fing'), 'transform', `translate(0 1326) scale(1 ${.15 + .85 * ease(f)}) translate(0 -1326)`);
    at(q(root, 'hb-dim'), 'opacity', o.dim || 0);
  },
};

Object.assign(window.SCENE_LIBRARY, A);
