// Little hand-drawn style characters, one per agent. Pure SVG, no images needed.
export default function Mascot({ kind = 'antenna', color = '#f06292', size = 110, className = '' }) {
  const ink = '#2b3a40'
  const robot = kind === 'robot'
  const fuzzy = kind === 'fuzzy'
  const eyes = fuzzy ? [[36, 60], [50, 50], [64, 60]] : [[38, 62], [62, 62]]
  return (
    <svg viewBox="0 0 100 110" width={size} height={size * 1.1} className={className} aria-hidden="true">
      {kind === 'antenna' && <g><line x1="50" y1="36" x2="50" y2="8" stroke={ink} strokeWidth="3" /><circle cx="50" cy="8" r="6" fill="#ffd54f" /></g>}
      {robot && <g><line x1="50" y1="30" x2="50" y2="10" stroke={ink} strokeWidth="3" /><circle cx="50" cy="9" r="5" fill="#ef4b4b" /></g>}
      {/* arms */}
      <ellipse cx="14" cy="78" rx="8" ry="13" fill={color} transform="rotate(25 14 78)" />
      <ellipse cx="86" cy="78" rx="8" ry="13" fill={color} transform="rotate(-25 86 78)" />
      {/* body */}
      {robot
        ? <rect x="18" y="32" width="64" height="70" rx="16" fill={color} />
        : <ellipse cx="50" cy="68" rx="34" ry="36" fill={color} stroke={fuzzy ? '#9a73d0' : 'none'} strokeWidth={fuzzy ? 6 : 0} strokeDasharray={fuzzy ? '2 4' : undefined} />}
      {kind === 'helmet' && <circle cx="50" cy="62" r="44" fill="rgba(150,215,240,.35)" stroke="rgba(255,255,255,.9)" strokeWidth="3" />}
      {kind === 'hat' && <g><ellipse cx="50" cy="36" rx="32" ry="7" fill="#8d5a2b" /><path d="M34 36 Q36 14 50 14 Q64 14 66 36Z" fill="#a8703a" /></g>}
      {/* face */}
      {eyes.map(([x, y], i) => (
        <g key={i}><circle cx={x} cy={y} r={fuzzy ? 6 : 8} fill="#fff" /><circle cx={x + 1} cy={y + 1} r={fuzzy ? 2.6 : 3.6} fill={ink} /></g>
      ))}
      <path d="M38 82 Q50 94 62 82" stroke={ink} strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  )
}
