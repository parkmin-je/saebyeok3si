// 공포 3화 "정원 초과". 새벽 엘리베이터, 혼자인데 정원 초과 경보가 울린다.
// 장면: helev(안에서 본 문과 층 표시), hpanel(버튼판 클로즈업), hecam(엘리베이터 천장 CCTV, 관리실 모니터)
// 시간 값은 전부 컷 시작부터 초. 효과음과 같은 숫자를 쓴다.

const EVT = (x, y, s, c, t, a = 'middle', f = 'Gothic', ex = '') => `<text x="${x}" y="${y}" font-family="${f}" font-size="${s}" fill="${c}" text-anchor="${a}" ${ex}>${t}</text>`;
// [[시각, 값], ...] 에서 지금 값
const timed = (list, lt, d = '') => (list || []).reduce((v, [t, x]) => (lt >= t ? x : v), d);
// 문 열림 정도 0..1 : o.open = [[열기 시작, 닫기 시작], ...]
function doorOpen(o, lt) {
  let v = 0;
  (o.open || []).forEach(([a, b]) => {
    if (lt >= a) v = ease(clamp((lt - a) / .9));
    if (b != null && lt >= b) v = 1 - ease(clamp((lt - b) / .9));
  });
  return v;
}

A.helev = {
  build: o => `<defs>${lin('he-st', '#8d939a', '#4b5057', 1, 0)}${lin('he-st2', '#4b5057', '#8d939a', 1, 0)}${lin('he-dr', '#a2a8ae', '#6f757c', 1, 0)}
      ${lin('he-fl', '#2b2d31', '#121316')}${halo('he-top', '#fff6e8', .8)}${halo('he-lob', '#ffe2b0', .9)}${blur('he-b', 6)}
      <clipPath id="he-gap"><rect x="250" y="520" width="580" height="980"/></clipPath></defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="#1a1c20"/>
    <!-- 천장 조명 -->
    <path d="M-400 -500 H1480 L1060 320 H20z" fill="#d9d6cf"/>
    <ellipse cx="540" cy="80" rx="700" ry="300" fill="url(#he-top)" opacity=".5"/>
    <!-- 양옆 벽 (스테인리스) -->
    <path d="M-400 -500 L20 320 V1700 L-400 2400z" fill="url(#he-st)"/>
    <path d="M1480 -500 L1060 320 V1700 L1480 2400z" fill="url(#he-st2)"/>
    ${Array.from({length: 6}, (_, i) => `<path d="M${-300 + i * 60} ${-300 + i * 120} V${2200 - i * 100}" stroke="#fff" stroke-width="2" opacity=".07"/>`).join('')}
    <!-- 정면 벽 -->
    <rect x="20" y="320" width="1040" height="1380" fill="#6a7077"/>
    <!-- 문 너머 (어두운 복도) -->
    <g clip-path="url(#he-gap)">
      <rect x="250" y="520" width="580" height="980" fill="#07080a"/>
      <path d="M250 1500 L380 1180 H700 L830 1500z" fill="#0d0e11"/>
      <g id="he-lobby" opacity="0"><ellipse cx="540" cy="760" rx="420" ry="520" fill="url(#he-lob)" opacity=".5"/><path d="M250 1500 L380 1180 H700 L830 1500z" fill="#2a2520" opacity=".8"/></g>
      ${EVT(540, 820, 120, '#1f2126', '', 'middle', 'Gothic', 'id="he-wallnum" font-weight="bold"')}
    </g>
    <!-- 문짝 두 개 -->
    <g id="he-dl"><rect x="250" y="520" width="290" height="980" fill="url(#he-dr)"/><path d="M538 520 V1500" stroke="#3a3e44" stroke-width="4"/></g>
    <g id="he-dr2"><rect x="540" y="520" width="290" height="980" fill="url(#he-dr)"/><path d="M542 520 V1500" stroke="#3a3e44" stroke-width="4"/></g>
    <rect x="236" y="506" width="608" height="1000" fill="none" stroke="#3c4046" stroke-width="28"/>
    <!-- 층 표시 -->
    <rect x="390" y="370" width="300" height="110" rx="10" fill="#050505"/>
    ${EVT(500, 455, 84, '#ff3b2a', '', 'middle', 'Gothic', 'id="he-floor"')}
    <path id="he-arrow" d="M610 440 l24 -40 l24 40z" fill="#ff3b2a"/>
    <g id="he-over" opacity="0"><rect x="300" y="360" width="480" height="130" rx="10" fill="#050505"/>${EVT(540, 448, 70, '#ff2020', '정원 초과', 'middle', 'Gothic', 'id="he-overt"')}</g>
    <!-- 바닥 -->
    <path d="M-400 2400 L20 1700 H1060 L1480 2400z" fill="url(#he-fl)"/>
    <!-- 오른쪽 버튼판 (작게) -->
    <path d="M1100 900 L1200 860 V1300 L1100 1320z" fill="#9aa0a6"/>
    <g id="he-btns">${Array.from({length: 7}, (_, i) => `<circle cx="1125" cy="${960 + i * 46}" r="10" fill="#555"/><circle cx="1170" cy="${944 + i * 46}" r="10" fill="#555"/>`).join('')}</g>
    <!-- 가까이 다가온 머리카락 (마지막) -->
    <g id="he-near" opacity="0"><ellipse cx="300" cy="880" rx="44" ry="150" fill="#b9bebe"/><ellipse cx="318" cy="840" rx="10" ry="7" fill="#1a1414"/>
      <path d="M-400 -500 H330 q-90 600 -20 1150 q-80 560 10 1750 H-400z" fill="#030303"/>
      ${Array.from({length: 14}, (_, k) => `<path d="M${240 + k * 8} ${-300 + k * 30} q${40 - k * 3} 900 ${-20 + k * 4} 2600" stroke="#030303" stroke-width="${4 + k % 3}" fill="none"/>`).join('')}</g>
    <rect id="he-dim" x="-400" y="-500" width="1880" height="2900" fill="#000" opacity="0"/>`,
  tick: (root, t, lt, o) => {
    const op = doorOpen(o, lt);
    at(q(root, 'he-dl'), 'transform', `translate(${-op * 280} 0)`);
    at(q(root, 'he-dr2'), 'transform', `translate(${op * 280} 0)`);
    const fl = timed(o.fl, lt, o.floor || '1');
    const fe = q(root, 'he-floor');
    if (fe) fe.textContent = fl;
    const wn = q(root, 'he-wallnum');
    if (wn) wn.textContent = o.wall || fl;
    at(q(root, 'he-arrow'), 'opacity', timed(o.moving, lt, 1) ? (t % 1 < .6 ? 1 : .3) : 0);
    const over = o.over != null && lt >= o.over;
    at(q(root, 'he-over'), 'opacity', over ? 1 : 0);
    at(q(root, 'he-overt'), 'opacity', over && (lt - o.over) % .5 >= .3 ? .25 : 1);
    at(q(root, 'he-lobby'), 'opacity', o.lobbyLight != null && lt >= o.lobbyLight ? .9 : 0);
    // 무게가 실린 듯 한 번 출렁
    const b = o.bounceAt != null && lt >= o.bounceAt ? Math.sin((lt - o.bounceAt) * 14) * Math.exp(-(lt - o.bounceAt) * 4) * 18 : 0;
    root.firstChild && (root.firstChild.style.transform = `translate(0px, ${b}px)`);
    const near = q(root, 'he-near');
    at(near, 'opacity', o.nearAt != null ? clamp((lt - o.nearAt) / .8) : 0);
    at(near, 'transform', `translate(${o.nearAt != null ? -120 + ease(clamp((lt - o.nearAt) / 1.6)) * 120 : -200} 0)`);
    at(q(root, 'he-dim'), 'opacity', o.dim || 0);
  },
};

// 버튼판 클로즈업. o.lit = {"12": 0, "4": 1.2} 번호가 켜지는 시각, o.off = {"4": 3} 꺼지는 시각
A.hpanel = {
  build: o => {
    const nums = ['15', '14', '13', '12', '11', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1', 'B1'];
    return `<defs>${lin('hpn-m', '#b4bac0', '#7c8288', 1, 1)}${halo('hpn-g', '#ffb347', 1)}${blur('hpn-b', 10)}</defs>
      <rect x="-400" y="-500" width="1880" height="2900" fill="#5f656c"/>
      ${Array.from({length: 40}, (_, i) => `<path d="M${-400 + i * 48} -500 V2400" stroke="#fff" stroke-width="1.5" opacity=".05"/>`).join('')}
      <rect x="240" y="180" width="600" height="1600" rx="30" fill="url(#hpn-m)"/>
      <rect x="320" y="240" width="440" height="160" rx="14" fill="#060606"/>
      ${EVT(540, 360, 110, '#ff3b2a', '', 'middle', 'Gothic', 'id="hpn-floor"')}
      <g id="hpn-over" opacity="0"><rect x="320" y="240" width="440" height="160" rx="14" fill="#060606"/>${EVT(540, 345, 76, '#ff2020', '정원 초과', 'middle', 'Gothic', 'id="hpn-overt"')}</g>
      ${nums.map((n, i) => {
        const x = 420 + (i % 2) * 240, y = 520 + Math.floor(i / 2) * 150;
        return `<g><circle id="hpn-g${n}" cx="${x}" cy="${y}" r="90" fill="url(#hpn-g)" opacity="0"/>
          <circle cx="${x}" cy="${y}" r="56" fill="#3a3d42"/><circle id="hpn-r${n}" cx="${x}" cy="${y}" r="56" fill="none" stroke="#2a2c30" stroke-width="8"/>
          <circle cx="${x}" cy="${y}" r="46" fill="#cfd3d7"/>${EVT(x, y + 18, 50, '#2a2d31', n)}</g>`;
      }).join('')}
      ${EVT(420, 1740, 34, '#2a2d31', '◀▶ 열림')}${EVT(660, 1740, 34, '#2a2d31', '▶◀ 닫힘')}`;
  },
  tick: (root, t, lt, o) => {
    const lit = o.lit || {}, off = o.off || {};
    Object.keys(lit).forEach(n => {
      const on = lt >= lit[n] && !(off[n] != null && lt >= off[n]);
      at(q(root, 'hpn-g' + n), 'opacity', on ? .8 : 0);
      at(q(root, 'hpn-r' + n), 'stroke', on ? '#ffb347' : '#2a2c30');
    });
    const fe = q(root, 'hpn-floor');
    if (fe) fe.textContent = timed(o.fl, lt, o.floor || '1');
    const ov = o.over != null && lt >= o.over;
    at(q(root, 'hpn-over'), 'opacity', ov ? 1 : 0);
    at(q(root, 'hpn-overt'), 'opacity', ov && (lt - o.over) % .5 >= .3 ? .25 : 1);
  },
};

// 엘리베이터 천장 구석 CCTV (흑백 어안). 관리실 모니터처럼 테두리 포함.
// o.crowdAt: 사람들이 보이기 시작 (빽빽하게), o.turnAt: 전부 고개를 '나' 쪽으로
A.hecam = {
  build: o => {
    const spots = [[300, 1180, .95], [430, 1230, 1.02], [560, 1190, .98], [380, 1380, 1.12], [520, 1420, 1.15], [660, 1350, 1.08], [250, 1480, 1.2], [610, 1560, 1.25]];
    return `<defs>${lin('hec-f', '#6a6a6a', '#3a3a3a')}${halo('hec-l', '#fff', .7)}${blur('hec-b', 2)}
        <clipPath id="hec-c"><rect x="60" y="560" width="960" height="1120" rx="20"/></clipPath></defs>
      <rect x="-400" y="-500" width="1880" height="2900" fill="#0b0c0e"/>
      <rect x="30" y="530" width="1020" height="1180" rx="34" fill="#1d1f23"/>
      <g clip-path="url(#hec-c)"><g filter="url(#hec-b)" style="filter:grayscale(1)">
        <rect x="60" y="560" width="960" height="1120" fill="#4a4a4a"/>
        <!-- 위에서 내려다본 엘리베이터 안 (바닥이 사다리꼴) -->
        <path d="M60 560 H1020 L900 900 H180z" fill="#5a5a5a"/>
        <path d="M60 560 L180 900 V1680 H60z" fill="#606060"/><path d="M1020 560 L900 900 V1680 H1020z" fill="#555"/>
        <path d="M180 900 H900 V1680 H180z" fill="url(#hec-f)"/>
        <rect x="380" y="880" width="320" height="30" fill="#222"/>
        <!-- 나: 오른쪽 아래 구석, 휴대폰 불빛 -->
        <g transform="translate(830 1600) scale(1.25)"><ellipse cx="0" cy="-70" rx="70" ry="80" fill="#2a2a2a"/><circle cx="0" cy="-150" r="44" fill="#1a1a1a"/><rect x="-26" y="-60" width="34" height="46" rx="6" fill="#eee" opacity=".8"/></g>
        <g id="hec-crowd" opacity="0">${spots.map(([x, y, s], i) => `<g transform="translate(${x} ${y}) scale(${s * .85})"><g transform="scale(1 .8)" style="filter:blur(${3 + i % 3}px)">${standing('#0b0b0b')}</g>
          <ellipse class="hec-face" cx="${10}" cy="-262" rx="15" ry="19" fill="#d8d8d8" opacity="0"/></g>`).join('')}</g>
        <ellipse cx="540" cy="700" rx="600" ry="300" fill="url(#hec-l)" opacity=".25"/>
      </g>
        <rect id="hec-noise" x="60" y="560" width="960" height="1120" fill="#fff" opacity="0"/>
      </g>
      ${EVT(100, 620, 36, '#e8ffe8', 'EV-2  CAM', 'start')}${EVT(980, 620, 36, '#ff5040', '● REC', 'end')}
      ${EVT(980, 1650, 36, '#e8ffe8', '', 'end', 'Gothic', 'id="hec-ts"')}
      ${EVT(540, 1780, 34, '#6b7078', '관리사무소 · 승강기 감시', 'middle')}`;
  },
  tick: (root, t, lt, o) => {
    at(q(root, 'hec-crowd'), 'opacity', o.crowdAt != null ? (lt >= o.crowdAt ? (lt - o.crowdAt < .12 ? .4 : 1) : 0) : 0);
    const turned = o.turnAt != null && lt >= o.turnAt;
    root.querySelectorAll('.hec-face').forEach(f => f.setAttribute('opacity', turned ? .95 : 0));
    const g = Math.sin(t * 41) > .93 || (o.crowdAt != null && Math.abs(lt - o.crowdAt) < .25);
    at(q(root, 'hec-noise'), 'opacity', g ? .2 : 0);
    const ts = q(root, 'hec-ts');
    if (ts) { const s = 7 + Math.floor(lt); ts.textContent = `2026-11-27 03:0${Math.floor(s / 60) + 4}:${String(s % 60).padStart(2, '0')}`; }
  },
};

Object.assign(window.SCENE_LIBRARY, A);
