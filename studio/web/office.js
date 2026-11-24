// 콩사원 AI 생존기 캐릭터 (art.js·apt.js 다음에 불러온다)
// dog2 = 콩사원·콩알이 (art.js), cat2 = 냥팀장 (apt.js), robot = AI대리 (여기)
// AI대리: 팀장 앞에선 웃고, 콩이 앞에선 비웃는 로봇 (o.smug)
function robot(id, o = {}) {
  return `<g id="${id}"><defs>${rad(id + 'b', '#e8eef8', '#8c9ab4', .35, .25, .9)}${rad(id + 's', '#1a2a4a', '#060c1a', .4, .3, .9)}${blur(id + 'f', 12)}${halo(id + 'g', '#5ab0ff', .9)}</defs>
  <g transform="translate(0 4)">${shadow(id + 'f', 170, 28, .3)}</g>
  <rect x="-130" y="-250" width="260" height="250" rx="60" fill="url(#${id}b)"/>
  <path d="M-30 -250 l30 120 l30 -120z" fill="#fff"/><path d="M-14 -240 h28 l10 110 l-24 30 l-24 -30z" fill="#ff4a5a"/>
  <rect x="-70" y="-120" width="140" height="60" rx="14" fill="#5a6a8a"/><circle cx="-36" cy="-90" r="10" fill="#7dffb0"/><circle cx="0" cy="-90" r="10" fill="#ffd23f"/><circle cx="36" cy="-90" r="10" fill="#ff6a7a"/>
  <g id="${id}-head" transform="translate(0 -370)">
   <path d="M0 -150 v-70" stroke="#8c9ab4" stroke-width="12"/><circle id="${id}-ant" cy="-230" r="22" fill="#5ab0ff"/><circle cy="-230" r="60" fill="url(#${id}g)" opacity=".6"/>
   <rect x="-170" y="-150" width="340" height="270" rx="70" fill="url(#${id}b)"/>
   <rect x="-140" y="-120" width="280" height="200" rx="46" fill="url(#${id}s)"/>
   <rect x="-200" y="-50" width="34" height="90" rx="14" fill="#8c9ab4"/><rect x="166" y="-50" width="34" height="90" rx="14" fill="#8c9ab4"/>
   ${o.smug
     ? `<path d="M-100 -30 q35 -26 70 0" stroke="#5ab0ff" stroke-width="16" fill="none" stroke-linecap="round"/><path d="M30 -20 h70" stroke="#5ab0ff" stroke-width="16" stroke-linecap="round"/><path d="M-60 30 q60 10 110 -26" stroke="#5ab0ff" stroke-width="14" fill="none" stroke-linecap="round"/>`
     : `<path d="M-100 -10 q35 -40 70 0 M30 -10 q35 -40 70 0" stroke="#5ab0ff" stroke-width="16" fill="none" stroke-linecap="round"/><path d="M-50 22 q50 40 100 0" stroke="#5ab0ff" stroke-width="14" fill="none" stroke-linecap="round"/>`}
  </g></g>`;
}

// 로봇 애니메이션: 말할 때 입 화면이 깜빡이고 머리가 까딱, smug 면 비웃는 얼굴로
function tickRobot(root, id, t, seed = 0, o = {}) {
  const talking = window.SPEAK === (o.who || 'bot');
  at(q(root, id + '-head'), 'transform', `translate(0 ${-370 + (talking ? Math.sin(t * 8) * 5 : Math.sin(t * 1.2 + seed) * 3)}) rotate(${Math.sin(t * .9 + seed) * 2.5})`);
  const ant = q(root, id + '-ant');
  if (ant) at(ant, 'opacity', .5 + .5 * Math.abs(Math.sin(t * 3)));
}

// ───────── 콩사원네 사무실 ─────────
// o = {kong:{face,sweat,tear}, cat:{show,lids,shock,x,from}, bot:{show,smug,enter,glitch,x}, board, alert, alarm}
// 자리: 냥팀장 x≈380 (문 앞), 콩사원 x≈1020 (가운데 책상), AI대리 x≈1720
const OT = (x, y, s, c, t, a = 'middle', ex = '') => `<text x="${x}" y="${y}" font-family="Gothic" font-size="${s}" fill="${c}" text-anchor="${a}" ${ex}>${t}</text>`;
A.office = {
  build: o => {
    const k = o.kong || {}, c = o.cat || {}, b = o.bot || {};
    const city = Array.from({length: 22}, (_, i) => {
      const w = 90 + (i * 37) % 80, h = 180 + (i * 131) % 380, x = -460 + i * 135;
      const win = Array.from({length: Math.floor(h / 60)}, (_, r) => `<rect x="${x + 18}" y="${300 - h + 20 + r * 60}" width="${w - 36}" height="22" fill="#fff3c4" opacity="${(i + r) % 3 ? .5 : .15}"/>`).join('');
      return `<rect x="${x}" y="${300 - h}" width="${w}" height="${h}" fill="${i % 2 ? '#5d7aa6' : '#4a6690'}"/>${win}`;
    }).join('');
    return `<defs>${lin('of-w', '#e8eef7', '#c9d4e4')}${lin('of-sky', '#8fc4ff', '#d8ecff')}${lin('of-f', '#58667e', '#3c475c')}
      ${lin('of-d', '#d9b88a', '#a9845a')}${lin('of-m', '#1a2742', '#0b1426')}${halo('of-l', '#fffbe0', .8)}${halo('of-s', '#5ab0ff', .6)}</defs>
    <rect x="-600" y="-1500" width="3240" height="2700" fill="url(#of-w)"/>
    <g>${Array.from({length: 5}, (_, i) => `<rect x="${-300 + i * 640}" y="-1380" width="420" height="40" rx="20" fill="#fffef4"/><circle cx="${-90 + i * 640}" cy="-1300" r="320" fill="url(#of-l)" opacity=".35"/>`).join('')}</g>
    <g><rect x="-480" y="-560" width="3000" height="880" rx="20" fill="url(#of-sky)"/>${city}
      <g stroke="#e8eef7" stroke-width="26">${Array.from({length: 6}, (_, i) => `<path d="M${-480 + i * 600} -560 v880"/>`).join('')}<path d="M-480 -120 h3000"/></g>
      <rect x="-480" y="-560" width="3000" height="880" rx="20" fill="none" stroke="#b8c4d6" stroke-width="20"/></g>
    <g transform="translate(-80 -1000)"><rect width="760" height="380" rx="18" fill="#fff" stroke="#9aa8bd" stroke-width="14"/>
      ${OT(380, 120, 56, '#3a4a66', (o.board || '이번 분기 목표').split('|')[0])}${OT(380, 250, 92, '#ff4a5a', (o.board || '|AI 도입 100%').split('|')[1] || '')}
      <path d="M120 300 q120 -40 240 0 t240 0" stroke="#2fbf71" stroke-width="10" fill="none"/></g>
    <g transform="translate(1560 -1000)"><rect width="520" height="300" rx="16" fill="#2a3654"/>${OT(260, 90, 46, '#9fb4d8', 'AI대리 환영합니다')}${OT(260, 210, 84, '#ffd23f', '환영!')}</g>
    <g transform="translate(380 1250)"><rect x="-260" y="-1160" width="520" height="1160" fill="#a7b4c8"/><rect x="-220" y="-1120" width="440" height="1120" fill="#8796ae"/>
      <circle cx="160" cy="-560" r="18" fill="#e8d24a"/>${OT(0, -1180, 44, '#3a4a66', '회의실')}</g>
    <rect x="-600" y="1200" width="3240" height="1100" fill="url(#of-f)"/>
    <g stroke="#4a566c" stroke-width="4" opacity=".6">${Array.from({length: 14}, (_, i) => `<path d="M${-600 + i * 260} 1200 l-${200 - i * 30} 1100"/>`).join('')}</g>
    ${c.show !== false ? `<g id="of-cat" transform="translate(${c.x || 380} 1260) scale(.92)">${cat2('of-c', {glasses: true, scarf: '#c8302a', lids: c.lids, slit: c.shock})}${c.shock ? '<g transform="translate(150 -560)"><path d="M0 0 q14 30 0 44 q-14 -14 0 -44z" fill="#8fd0ff"/></g>' : ''}</g>` : ''}
    <g id="of-kong" transform="translate(1020 1150) scale(.78)">${dog2('of-k', {face: k.face, sweat: k.sweat, tear: k.tear, bag: '#3a7ad8'})}</g>
    <g transform="translate(1020 1000)">
      <g transform="translate(450 -10) scale(.85)"><rect x="-190" y="-300" width="380" height="250" rx="18" fill="#2a3450"/><rect x="-170" y="-282" width="340" height="214" rx="10" fill="url(#of-m)"/>
        <g id="of-code" fill="#5ab0ff">${Array.from({length: 6}, (_, i) => `<rect x="-150" y="${-262 + i * 30}" width="${120 + (i * 53) % 170}" height="12" rx="6" opacity=".8"/>`).join('')}</g>
        <rect x="-20" y="-50" width="40" height="50" fill="#3a3a44"/></g>
      <path d="M-520 0 h1040 l-40 70 h-960z" fill="url(#of-d)"/><rect x="-480" y="70" width="960" height="200" fill="#8a6440"/>
      <g transform="translate(-300 -10)"><rect x="-90" y="-60" width="180" height="60" rx="10" fill="#fff"/>${OT(0, -18, 34, '#3a4a66', '콩사원')}</g>
      <g transform="translate(-160 -40)"><rect x="-30" y="-50" width="60" height="70" rx="12" fill="#fff"/><path d="M30 -30 q30 0 30 25 q0 25 -30 25" stroke="#fff" stroke-width="10" fill="none"/></g></g>
    ${b.show !== false ? `<g id="of-bot" transform="translate(${b.x || 1720} 1260) scale(.82)">${robot('of-b', {smug: b.smug})}
      ${b.glitch ? `<g id="of-gl" transform="translate(0 -370)">${Array.from({length: 7}, (_, i) => `<rect x="-140" y="${-120 + i * 30}" width="280" height="12" fill="${i % 2 ? '#ff4a5a' : '#5ab0ff'}" opacity=".7"/>`).join('')}${OT(0, 20, 70, '#fff', 'ERROR')}</g>` : ''}</g>` : ''}
    ${o.alert ? `<g id="of-alert" transform="translate(1530 560)"><rect x="-300" y="-250" width="600" height="520" rx="30" fill="#1a0a10" stroke="#ff4a5a" stroke-width="14"/>
      <rect x="-300" y="-250" width="600" height="96" rx="30" fill="#ff4a5a"/>${OT(0, -185, 50, '#fff', '고객 명단 (배포됨)')}
      ${['홍길동', '홍길동', '홍길동', '홍길동'].map((n, i) => `${OT(-240, -80 + i * 82, 50, '#9fb4d8', String(i + 1).padStart(3, '0'), 'start')}${OT(-90, -80 + i * 82, 56, '#ffd23f', n, 'start')}`).join('')}
      ${OT(0, 245, 40, '#ff8a96', '…외 9,996명 전부 홍길동')}</g>` : ''}
    ${o.alarm ? `<rect id="of-alarm" x="-600" y="-1500" width="3240" height="3800" fill="#ff2a3a" opacity="0"/>` : ''}`;
  },
  tick: (root, t, p, o) => {
    const k = o.kong || {}, b = o.bot || {};
    tickDog2(root, 'of-k', t, 0, {who: 'kong', tilt: k.tilt || 0});
    const c = o.cat || {};
    if (c.show !== false) {
      tickCat(root, 'of-c', t, 1, 'cat');
      const x = c.x || 380, x0 = c.from !== undefined ? c.from : x, e = JE(p / .6);
      at(q(root, 'of-cat'), 'transform', `translate(${x0 + (x - x0) * e} ${1260 - (e < 1 ? Math.abs(Math.sin(p * 12)) * 24 : 0)}) scale(.92)`);
    }
    const al = q(root, 'of-alarm');
    if (al) at(al, 'opacity', .1 + .1 * Math.sin(t * 9));
    const pop = q(root, 'of-alert');
    if (pop) { const a = JE(p / .3); at(pop, 'transform', `translate(1530 560) scale(${.4 + .6 * a}) rotate(${(1 - a) * -8})`); at(pop, 'opacity', a); }
    const gl = q(root, 'of-gl');
    if (gl) { at(gl, 'opacity', Math.sin(t * 37) > -.2 ? 1 : 0); at(gl, 'transform', `translate(${Math.sin(t * 61) * 10} -370)`); }
    if (b.show !== false) {
      tickRobot(root, 'of-b', t, 2, {who: 'bot'});
      const e = b.enter ? JE(p / .7) : 1;
      const bx = (b.x || 1720) + (b.glitch ? Math.sin(t * 53) * 8 : 0);
      at(q(root, 'of-bot'), 'transform', `translate(${bx + (1 - e) * 900} ${1260 - Math.abs(Math.sin(p * 9)) * (1 - e) * 30}) scale(.82)`);
    }
    const code = q(root, 'of-code');
    if (code) at(code, 'transform', `translate(0 ${-((t * 30) % 30)})`);
  },
};
Object.assign(window.SCENE_LIBRARY, A);
