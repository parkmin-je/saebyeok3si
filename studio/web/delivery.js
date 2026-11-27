// 공포 4화 "배달 완료". 배달 완료 사진이 계속 온다. 사진마다 그것이 조금씩 가까워진다.
// 장면: hdeliv(어둠 속 휴대폰, 배달 알림 대화 + 사진), hroom(불 꺼진 원룸, 침대에서 휴대폰 보는 나의 뒷모습)
// o.msgs = [[종류, 글 또는 사진 종류], ...]  종류: 'txt' 기사 말풍선, 'pic' 사진('door0'|'door1'|'door2'|'inside'|'back'), 'me' 내 말풍선
// o.reveal = [초, ...] 각 메시지가 뜨는 시각. o.scroll = 위로 밀린 칸 수 ([[초, 칸]...])

// 배달 사진 한 장 (320×400)
function delivPhoto(kind) {
  const door = fig => `<rect width="320" height="400" fill="#3b3a36"/>
    <path d="M0 0 H320 L250 90 H70z" fill="#4c4a45"/><path d="M0 400 L70 300 H250 L320 400z" fill="#2c2b28"/>
    <path d="M0 0 L70 90 V300 L0 400z" fill="#44423d"/><path d="M320 0 L250 90 V300 L320 400z" fill="#403e3a"/>
    <rect x="70" y="90" width="180" height="210" fill="#1a1a19"/>
    <path d="M86 120 L150 110 V330 L86 360z" fill="#4a3d33" stroke="#252019" stroke-width="3"/>
    <text x="118" y="104" font-family="Gothic" font-size="14" fill="#ddd" text-anchor="middle">1204</text>
    <rect x="100" y="330" width="60" height="40" fill="#b08a5a"/><path d="M100 345 h60" stroke="#7a5d3a" stroke-width="3"/>
    ${fig === 1 ? `<g transform="translate(200 250) scale(.32)" opacity=".85" style="filter:blur(1.2px)">${standing('#050505')}</g>` : ''}
    ${fig === 2 ? `<g transform="translate(184 368) scale(.95)" style="filter:blur(.8px)">${standing('#030303')}</g>` : ''}
    <ellipse cx="160" cy="40" rx="140" ry="60" fill="#fff6dc" opacity=".2"/>`;
  if (kind === 'door0') return door(0);
  if (kind === 'door1') return door(1);
  if (kind === 'door2') return door(2);
  if (kind === 'inside') return `<rect width="320" height="400" fill="#121317"/>
    <rect x="60" y="20" width="200" height="360" fill="#1e2128"/><rect x="72" y="32" width="176" height="336" fill="none" stroke="#2b2f37" stroke-width="3"/>
    <rect x="200" y="150" width="30" height="80" rx="8" fill="#3a3f48"/><rect x="206" y="165" width="18" height="7" fill="#5fb8ff"/>
    <path d="M60 380 L0 400 H320 L260 380z" fill="#191a1e"/><rect x="80" y="370" width="50" height="20" fill="#2a2024"/>
    <ellipse cx="160" cy="200" rx="200" ry="220" fill="#000" opacity=".25"/>`;
  // 'back': 어두운 방, 침대에서 휴대폰 보는 사람의 뒷모습 (= 지금 hroom 과 같은 구도)
  return `<rect width="320" height="400" fill="#16181f"/>
    <rect x="190" y="40" width="90" height="120" fill="#2c3b58"/><path d="M235 40 V160 M190 100 H280" stroke="#0b0d12" stroke-width="5"/>
    <path d="M0 270 H320 V400 H0z" fill="#0e0f13"/><path d="M0 250 q160 -14 320 0 v50 h-320z" fill="#262a34"/>
    <g transform="translate(150 330)"><path d="M-70 0 q-6 -100 70 -110 q76 10 70 110z" fill="#050506"/><circle cx="0" cy="-140" r="36" fill="#050506"/>
      <path d="M-36 -150 q36 -40 72 0" stroke="#7d9cd8" stroke-width="3" fill="none" opacity=".5"/></g>
    <ellipse cx="150" cy="260" rx="70" ry="40" fill="#9fc2ff" opacity=".25"/>`;
}

A.hdeliv = {
  build: o => {
    const msgs = o.msgs || [];
    let y = -470;
    const items = msgs.map((m, i) => {
      const me = m[0] === 'me', pic = m[0] === 'pic', y0 = y;
      if (pic) {
        y += 470;
        return `<g id="hd-m${i}" opacity="0"><rect x="-300" y="${y0}" width="340" height="420" rx="24" fill="#2a3242"/>
          <svg x="-290" y="${y0 + 10}" width="320" height="400" viewBox="0 0 320 400"><clipPath id="hd-pc${i}"><rect width="320" height="400" rx="18"/></clipPath><g clip-path="url(#hd-pc${i})">${delivPhoto(m[1])}</g></svg></g>`;
      }
      const w = Math.min(600, 60 + m[1].length * 38);
      y += 160;
      return `<g id="hd-m${i}" opacity="0"><rect x="${me ? 300 - w : -300}" y="${y0}" width="${w}" height="120" rx="40" fill="${me ? '#f2d34a' : '#2a3242'}"/>
        <text x="${me ? 300 - w / 2 : -300 + w / 2}" y="${y0 + 76}" font-family="Gothic" font-size="40" fill="${me ? '#1a1608' : '#eef2f7'}" text-anchor="middle">${m[1]}</text></g>`;
    }).join('');
    return `<defs>${halo('hd-g', '#bcd6ff', .55)}${lin('hd-s', '#0e1118', '#151a24')}
        <clipPath id="hd-clip"><rect x="-340" y="-550" width="680" height="1230"/></clipPath></defs>
      <rect x="-400" y="-500" width="1880" height="2900" fill="#020204"/>
      <ellipse cx="540" cy="980" rx="760" ry="1000" fill="url(#hd-g)" opacity=".35"/>
      <g transform="translate(540 1000) rotate(-3)">
        <path d="M-470 520 q-80 160 -30 520 h520 q60 -260 0 -480z" fill="#1a1412"/>
        <rect x="-370" y="-760" width="740" height="1480" rx="90" fill="#050506"/>
        <rect x="-340" y="-720" width="680" height="1400" rx="64" fill="url(#hd-s)"/>
        <g clip-path="url(#hd-clip)"><g id="hd-list">${items}</g></g>
        <rect x="-340" y="-720" width="680" height="170" rx="64" fill="#1c2230"/>
        <circle cx="-250" cy="-630" r="44" fill="#2fb383"/><text x="-250" y="-616" font-family="Gothic" font-size="36" fill="#fff" text-anchor="middle">배</text>
        <text x="-180" y="-620" font-family="Gothic" font-size="44" fill="#e8eef6">배달 기사님</text>
        <text x="-180" y="-578" font-family="Gothic" font-size="28" fill="#8fa0b4">주문 1건 · 배달 중</text>
      </g>`;
  },
  tick: (root, t, lt, o) => {
    (o.msgs || []).forEach((m, i) => at(q(root, 'hd-m' + i), 'opacity', clamp((lt - ((o.reveal || [])[i] ?? 0)) / .12)));
    const sc = (o.scroll || []).reduce((v, [s, n]) => v + n * ease(clamp((lt - s) / .4)), o.scroll0 || 0);
    at(q(root, 'hd-list'), 'transform', `translate(0 ${-sc})`);
  },
};

// 불 꺼진 원룸. 침대에 앉아 휴대폰 보는 나 (뒷모습). o.behind: 뒤에 선 것이 나타나는 시각
A.hroom = {
  build: o => `<defs>${halo('hr-ph', '#9fc2ff', .8)}${lin('hr-w', '#0b0c10', '#050507')}${blur('hr-b', 3)}</defs>
    <rect x="-400" y="-500" width="1880" height="2900" fill="#1a1d26"/>
    <rect x="620" y="300" width="300" height="420" fill="#0d1220"/><path d="M770 300 V720 M620 510 H920" stroke="#05070c" stroke-width="12"/>
    <rect x="620" y="300" width="300" height="420" fill="#4a6aa0" opacity=".25"/>
    <path d="M620 720 L300 1300 H1100 L920 720z" fill="#3a5288" opacity=".08"/>
    <path d="M-400 1300 H1480 V2400 H-400z" fill="#0a0b0e"/>
    <g id="hr-back" opacity="0" style="filter:blur(1.5px)"><g transform="translate(720 1330) scale(1.95)">${standing('#010102')}</g>
      <ellipse cx="728" cy="690" rx="24" ry="31" fill="#c9cdcd" opacity=".9"/><circle cx="719" cy="686" r="3.5" fill="#000"/><circle cx="737" cy="686" r="3.5" fill="#000"/>
      <path d="M700 660 q28 -20 56 0 l-6 70 q-22 -40 -44 0z" fill="#010102"/></g>
    <path d="M-100 1180 q600 -60 1300 0 v300 h-1300z" fill="#161820"/><path d="M-100 1160 h1300 v60 h-1300z" fill="#1f222b"/>
    <g transform="translate(540 1300)">
      <path d="M-210 0 q-20 -330 210 -360 q230 30 210 360z" fill="#030304"/>
      <circle cx="0" cy="-430" r="110" fill="#030304"/>
      <path d="M-100 -470 q100 -90 200 0" stroke="#8fb0f0" stroke-width="6" fill="none" opacity=".35"/>
      <path d="M-200 -40 q-10 -250 150 -310" stroke="#8fb0f0" stroke-width="5" fill="none" opacity=".25"/>
      <ellipse cx="0" cy="-260" rx="330" ry="260" fill="url(#hr-ph)" opacity=".45"/>
    </g>
`,
  tick: (root, t, lt, o) => {
    at(q(root, 'hr-back'), 'opacity', o.behind != null && lt >= o.behind ? (lt - o.behind < .1 ? .4 : 1) : 0);
  },
};

Object.assign(window.SCENE_LIBRARY, A);
