// 콩이의 AI 직업 생존 판정: 스튜디오 한 장면 + 큰 모니터 화면 여러 종류 (o.screen)
// 화면 좌표: 모니터 안 0..1000 x 0..660. 숫자·바늘·목록은 컷 안 시간(p)에 맞춰 움직인다.
const JE = x => x < 0 ? 0 : x > 1 ? 1 : 1 - Math.pow(1 - x, 3);
const T = (x, y, s, c, t, a = 'middle', extra = '') => `<text x="${x}" y="${y}" font-family="Gothic" font-size="${s}" fill="${c}" text-anchor="${a}" ${extra}>${t}</text>`;

const SCREENS = {
  // 직업 이름 + 큰 물음표
  q: o => `${T(500, 150, 60, '#9fb4d8', 'AI 생존 판정')}${T(500, 300, 110, '#fff', o.job || '경리·회계 사무원')}
    <g id="js-q">${T(500, 560, 220, '#ffd23f', '?')}</g>`,
  // 순위 목록, o.hl 번째 강조
  list: o => `${T(500, 90, 52, '#9fb4d8', o.title || '')}
    ${(o.items || []).map((it, i) => `<g id="js-li${i}" opacity="0"><rect x="70" y="${130 + i * 74}" width="860" height="62" rx="14" fill="${i === o.hl ? '#ff4a5a' : '#1c2a48'}"/>
      ${T(110, 175 + i * 74, 40, i === o.hl ? '#fff' : '#ffd23f', i + 1, 'start')}${T(170, 175 + i * 74, 40, '#fff', it, 'start')}</g>`).join('')}`,
  // 큰 숫자 카운트업 (o.num, o.unit, o.sub)
  big: o => `${T(500, 140, 54, '#9fb4d8', o.title || '')}<text id="js-num" x="500" y="400" font-family="Gothic" font-size="230" fill="#ffd23f" text-anchor="middle">0</text>
    ${T(500, 500, 64, '#fff', o.unit || '')}${T(500, 590, 44, '#9fb4d8', o.sub || '')}`,
  // 위험 업무 vs 살아남는 업무
  tasks: o => `<rect x="40" y="40" width="440" height="80" rx="16" fill="#ff4a5a"/>${T(260, 97, 46, '#fff', 'AI가 가져갈 일')}
    <rect x="520" y="40" width="440" height="80" rx="16" fill="#2fbf71"/>${T(740, 97, 46, '#fff', '사람이 남는 일')}
    ${(o.bad || []).map((t, i) => `<g id="js-b${i}" opacity="0">${T(260, 220 + i * 120, 46, '#ffd0d4', '✕ ' + t)}</g>`).join('')}
    ${(o.good || []).map((t, i) => `<g id="js-g${i}" opacity="0">${T(740, 220 + i * 120, 46, '#c8ffd8', '○ ' + t)}</g>`).join('')}`,
  // 생존 점수 게이지 (o.score)
  score: o => `${T(500, 110, 56, '#9fb4d8', '콩이 판정 생존 점수')}
    <g transform="translate(500 520)"><path d="M-360 0 A360 360 0 0 1 360 0" stroke="#2a3654" stroke-width="70" fill="none"/>
     <path d="M-360 0 A360 360 0 0 1 -180 -312" stroke="#ff4a5a" stroke-width="70" fill="none"/><path d="M-180 -312 A360 360 0 0 1 180 -312" stroke="#ffb02a" stroke-width="70" fill="none"/>
     <path d="M180 -312 A360 360 0 0 1 360 0" stroke="#2fbf71" stroke-width="70" fill="none"/>
     <g id="js-needle"><path d="M-14 0 L0 -160 L14 0z" fill="#fff"/></g><circle r="34" fill="#fff"/>
     <text id="js-sc" y="-185" font-family="Gothic" font-size="150" fill="#fff" text-anchor="middle">0</text></g>`,
  // 오늘 할 일
  todo: o => `${T(500, 120, 58, '#9fb4d8', '콩이 잔소리 · 오늘 할 일')}
    ${(o.items || []).map((t, i) => `<g id="js-t${i}" opacity="0"><rect x="80" y="${180 + i * 140}" width="840" height="110" rx="20" fill="#1c2a48"/>
      <rect x="110" y="${205 + i * 140}" width="60" height="60" rx="12" fill="none" stroke="#2fbf71" stroke-width="8"/>
      <path id="js-c${i}" d="M122 ${235 + i * 140} l18 18 l34 -40" stroke="#2fbf71" stroke-width="12" fill="none" opacity="0"/>${T(200, 255 + i * 140, 48, '#fff', t, 'start')}</g>`).join('')}`,
};

A.studio = {
  build: o => `<defs>${lin('jb-w', '#1a2238', '#0c1020')}${halo('jb-g', '#5ab0ff', .7)}${halo('jb-y', '#ffd27a', .8)}${lin('jb-d', '#c8a070', '#8a6440')}${lin('jb-m', '#0f1a33', '#081022')}</defs>
  <rect x="-600" y="-1500" width="3240" height="3800" fill="url(#jb-w)"/>
  <g stroke="#24304c" stroke-width="4">${Array.from({length: 16}, (_, i) => `<path d="M${-600 + i * 220} -1500 v3800"/>`).join('')}</g>
  <circle cx="1020" cy="100" r="1000" fill="url(#jb-g)" opacity=".25"/>
  <g transform="translate(-300 500)"><rect x="-120" y="-420" width="240" height="420" rx="20" fill="#24304c"/><path d="M0 -420 q-90 -160 -20 -300 q40 120 20 300 M0 -420 q90 -140 40 -280 q-60 100 -40 280" fill="#2fa86a"/></g>
  <g transform="translate(2300 500)"><rect x="-120" y="-420" width="240" height="420" rx="20" fill="#24304c"/><path d="M0 -420 q-90 -160 -20 -300 q40 120 20 300 M0 -420 q90 -140 40 -280 q-60 100 -40 280" fill="#2fa86a"/></g>
  <g transform="translate(1020 -720)"><rect x="-500" y="-60" width="1000" height="120" rx="60" fill="#0a0f1e" stroke="#ffd23f" stroke-width="8"/>
   <circle r="420" fill="url(#jb-y)" opacity=".18"/>${T(0, 26, 70, '#ffd23f', '콩이의 AI 직업 판정소')}</g>
  <g transform="translate(520 -580)"><rect x="-30" y="-30" width="1060" height="720" rx="40" fill="#2a3450"/><rect width="1000" height="660" rx="24" fill="url(#jb-m)"/>
   <g id="js-scr">${(SCREENS[o.screen || 'q'] || SCREENS.q)(o)}</g>
   ${o.src ? `<rect x="0" y="610" width="1000" height="50" fill="#000" opacity=".45"/>${T(980, 646, 30, '#cfd8ea', '출처: ' + o.src, 'end')}` : ''}
   <rect width="1000" height="660" rx="24" fill="none" stroke="#5ab0ff" stroke-width="4" opacity=".5"/></g>
  <rect x="-600" y="1000" width="3240" height="1300" fill="#141a2c"/>
  <g transform="translate(1020 1110) scale(.95)">${dog2('jb-d', {face: o.face, sweat: o.sweat, glasses: true})}</g>
  <path d="M-200 900 h2440 l-80 120 h-2280z" fill="url(#jb-d)"/><rect x="-120" y="1020" width="2280" height="1200" fill="#6a4a30"/>
  <g transform="translate(1500 900)"><rect x="-150" y="-20" width="300" height="20" rx="6" fill="#3a3a44"/><path d="M-130 -20 l20 -180 h220 l20 180z" fill="#4a4a58"/><circle cy="-110" r="22" fill="#9ab"/></g>
  <g transform="translate(560 900)"><rect x="-60" y="-140" width="120" height="140" rx="16" fill="#f2f2f2"/>${T(0, -55, 40, '#c8302a', 'AI')}</g>
  ${o.stamp ? `<g id="js-stamp" transform="translate(1020 100)" opacity="0"><rect x="-330" y="-110" width="660" height="220" rx="30" fill="none" stroke="${o.stampC || '#ff4a5a'}" stroke-width="18"/>${T(0, 40, 110, o.stampC || '#ff4a5a', o.stamp)}</g>` : ''}`,
  tick: (root, t, p, o) => {
    tickDog2(root, 'jb-d', t, 0, {tilt: Math.sin(t * .6) * 4});
    const g = id => q(root, id);
    const s = o.screen || 'q';
    if (s === 'q') at(g('js-q'), 'transform', `translate(500 480) scale(${1 + Math.sin(t * 4) * .06}) translate(-500 -480)`);
    if (s === 'list') (o.items || []).forEach((_, i) => { const k = JE((p - .1 - i * .12) / .25); at(g('js-li' + i), 'opacity', k); at(g('js-li' + i), 'transform', `translate(${(1 - k) * 80} 0)`); });
    if (s === 'list' && o.hl !== undefined) { const el = g('js-li' + o.hl); if (el && p > 1.6) at(el, 'transform', `translate(500 ${167 + o.hl * 74}) scale(${1 + Math.abs(Math.sin(t * 5)) * .04}) translate(-500 ${-(167 + o.hl * 74)})`); }
    if (s === 'big') { const n = g('js-num'); if (n) n.textContent = Math.round((o.num || 0) * JE(p / 1.4)).toLocaleString('ko-KR') + (o.suffix || ''); }
    if (s === 'tasks') { (o.bad || []).forEach((_, i) => at(g('js-b' + i), 'opacity', JE((p - .2 - i * .35) / .25))); (o.good || []).forEach((_, i) => at(g('js-g' + i), 'opacity', JE((p - (o.goodAt || 1.4) - i * .35) / .25))); }
    if (s === 'score') { const k = JE(p / 1.6) * (o.score || 0); at(g('js-needle'), 'transform', `rotate(${-90 + k * 1.8 + (p > 1.6 ? Math.sin(t * 9) * 1.5 : 0)})`); const sc = g('js-sc'); if (sc) sc.textContent = Math.round(k); }
    if (s === 'todo') (o.items || []).forEach((_, i) => { at(g('js-t' + i), 'opacity', JE((p - .2 - i * .5) / .25)); at(g('js-c' + i), 'opacity', p > .6 + i * .5 ? 1 : 0); });
    const st = g('js-stamp');
    if (st) { const k = JE((p - (o.stampAt || .3)) / .2); at(st, 'opacity', k); at(st, 'transform', `translate(1020 100) scale(${2.2 - 1.2 * k}) rotate(-8)`); }
  },
};
Object.assign(window.SCENE_LIBRARY, A);
