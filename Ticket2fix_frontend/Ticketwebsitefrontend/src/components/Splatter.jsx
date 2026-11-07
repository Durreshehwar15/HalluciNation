import { useMemo } from 'react'

// Paint-splatter dots, clustered towards one side. Purely decorative.
export default function Splatter({ color = '#2fa98a', count = 45, seed = 1, side = 'left', className = '' }) {
  const dots = useMemo(() => {
    let s = seed * 9301 + 49297
    const r = () => (s = (s * 9301 + 49297) % 233280) / 233280
    return Array.from({ length: count }, () => {
      const t = r()
      const x = side === 'center' ? t * 190 + 5 : (side === 'left' ? t * t : 1 - t * t) * 190 + 5
      return { x, y: r() * 290 + 5, r: 1 + r() * r() * 9 }
    })
  }, [color, count, seed, side])
  return (
    <svg viewBox="0 0 200 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"
         className={`pointer-events-none absolute ${className}`}>
      {dots.map((d, i) => <circle key={i} cx={d.x} cy={d.y} r={d.r} fill={color} />)}
    </svg>
  )
}
