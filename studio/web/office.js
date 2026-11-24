// 콩사원 AI 생존기 캐릭터 (art.js·apt.js 다음에 불러온다)
// dog2 = 콩사원·콩알이 (art.js), cat2 = 냥팀장 (apt.js), robot = AI대리 (여기)
// AI대리: 팀장 앞에선 웃고, 콩이 앞에선 비웃는 로봇 (o.smug)
function robot(id, o = {}) {
  return `<g id="${id}"><defs>${rad(id + 'b', '#e8eef8', '#8c9ab4', .35, .25, .9)}${rad(id + 's', '#1a2a4a', '#060c1a', .4, .3, .9)}${blur(id + 'f', 12)}${halo(id + 'g', '#5ab0ff', .9)}</defs>
  <g transform="translate(0 4)">${shadow(id + 'f', 170, 28, .3)}</g>
  <rect x="-130" y="-250" width="260" height="250" rx="60" fill="url(#${id}b)"/>
  <path d="M-30 -250 l30 120 l30 -120z" fill="#fff"/><path d="M-14 -240 h28 l10 110 l-24 30 l-24 -30z" fill="#ff4a5a"/>
  <rect x="-70" y="-120" width="140" height="60" rx="14" fill="#5a6a8a"/><circle cx="-36" cy="-90" r="10" fill="#7dffb0"/><circle cx="0" cy="-90" r="10" fill="#ffd23f"/><circle cx="36" cy="-90" r="10" fill="#ff6a7a"/>
  <g transform="translate(0 -370)">
   <path d="M0 -150 v-70" stroke="#8c9ab4" stroke-width="12"/><circle cy="-230" r="22" fill="#5ab0ff"/><circle cy="-230" r="60" fill="url(#${id}g)" opacity=".6"/>
   <rect x="-170" y="-150" width="340" height="270" rx="70" fill="url(#${id}b)"/>
   <rect x="-140" y="-120" width="280" height="200" rx="46" fill="url(#${id}s)"/>
   <rect x="-200" y="-50" width="34" height="90" rx="14" fill="#8c9ab4"/><rect x="166" y="-50" width="34" height="90" rx="14" fill="#8c9ab4"/>
   ${o.smug
     ? `<path d="M-100 -30 q35 -26 70 0" stroke="#5ab0ff" stroke-width="16" fill="none" stroke-linecap="round"/><path d="M30 -20 h70" stroke="#5ab0ff" stroke-width="16" stroke-linecap="round"/><path d="M-60 30 q60 10 110 -26" stroke="#5ab0ff" stroke-width="14" fill="none" stroke-linecap="round"/>`
     : `<path d="M-100 -10 q35 -40 70 0 M30 -10 q35 -40 70 0" stroke="#5ab0ff" stroke-width="16" fill="none" stroke-linecap="round"/><path d="M-50 22 q50 40 100 0" stroke="#5ab0ff" stroke-width="14" fill="none" stroke-linecap="round"/>`}
  </g></g>`;
}
