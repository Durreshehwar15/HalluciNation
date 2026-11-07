import { useNavigate } from 'react-router-dom'
import { IMG, MASCOT, DEMO_TICKET_ID } from '../content/assets.js'

// Positions are % of the board picture (1920x1080), measured from the reference "gameboard" image.
// cx = horizontal centre, feet = vertical position of the feet (bigger = lower / closer to the front),
// fit = size correction per character (1 = base size), ratio = width/height.
// gap = distance between the label and the character. More negative = label moves closer.
const BASE_H = 27   // same base height for every character (% of the board). Change this to resize all four.

const SPOTS = [
  { key: 'bunny',  label: 'Report a bug',     to: '/submit',                            img: MASCOT.bunny,  cx: 15.65, feet: 87.69, fit: 1.45, ratio: 0.509, gap: '-1.5rem', delay: '0s' },
  { key: 'dog',    label: 'Watch the agents', to: `/tickets/${DEMO_TICKET_ID}`,         img: MASCOT.dog,    cx: 66.28, feet: 40.09, fit: 1.0,  ratio: 0.857, gap: '-1rem',   delay: '-0.8s' },
  { key: 'dragon', label: 'Review & approve', to: `/tickets/${DEMO_TICKET_ID}/approve`, img: MASCOT.dragon, cx: 77.34, feet: 91.48, fit: 1.05, ratio: 0.747, gap: '-1.5rem', delay: '-1.6s' },
  { key: 'cat',    label: 'Read the guide',   to: '/guide',                             img: MASCOT.cat,    cx: 47.5,  feet: 51.5,  fit: 1.3,  ratio: 0.61,  gap: '-1.5rem', delay: '-2.2s' },
]

export default function GameBoard() {
  const navigate = useNavigate()
  return (
    <div className="relative mx-auto max-w-6xl overflow-hidden rounded-3xl border-4 border-[#e2c39a] shadow-xl">
      <img src={IMG.board} alt="Ticket2fix town square" className="block w-full select-none" draggable={false} />

      {SPOTS.map((s) => (
        <button
          key={s.key}
          type="button"
          aria-label={s.label}
          onClick={() => navigate(s.to)}
          className="mascot-hit absolute cursor-pointer"
          style={{
            left: `${s.cx}%`,
            top: `${s.feet}%`,
            height: `${BASE_H * s.fit}%`,
            aspectRatio: s.ratio,
            transform: 'translate(-50%, -100%)',
          }}
        >
          <div className="bob relative h-full w-full" style={{ animationDelay: s.delay }}>
            <span className="bubble" style={{ marginBottom: s.gap }}>{s.label}</span>
            <img src={s.img} alt="" className="h-full w-full object-contain" draggable={false} />
          </div>
        </button>
      ))}
    </div>
  )
}