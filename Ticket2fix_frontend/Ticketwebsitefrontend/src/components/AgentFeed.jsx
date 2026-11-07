import { AGENTS } from '../content/agents.js'
import { HEAD } from '../content/assets.js'
import Avatar from './Avatar.jsx'

const BY_NAME = Object.fromEntries(AGENTS.map((a) => [a.name, a]))
const EMOJI = { Switch: '🔗' }

const ACCENT = {
  'Triage Agent': '#f2a6c4',
  'Code Investigation Agent': '#e0b36a',
  'Fix Agent': '#8a5cc8',
  'Testing Agent': '#4cc27a',
  'Reviewer Agent': '#dd7424',
  Switch: '#6b46a8',
}

export default function AgentFeed({ events = [] }) {
  if (!events.length) {
    return (
      <div className="wood-card flex items-center gap-4 border-dashed p-5">
        <img src={HEAD.dog} alt="" className="bob h-16 w-auto" />
        <p className="text-sm">Shh… the agents are getting ready. 💤</p>
      </div>
    )
  }
  return (
    <ul className="relative space-y-4">
      {/* vertical timeline line behind the avatars */}
      <span className="absolute bottom-6 left-6 top-6 w-0.5 bg-[#e2c39a]" aria-hidden="true" />
      {events.map((e, i) => {
        const accent = ACCENT[e.agent] || '#8a5cc8'
        return (
          <li key={i} className="relative flex gap-4">
            <Avatar
              src={BY_NAME[e.agent]?.head}
              emoji={EMOJI[e.agent] || e.agent[0]}
              className="z-10 mt-1 h-12 w-12 border-[3px] shadow-sm"
            />
            <div
              className="relative min-w-0 flex-1 rounded-2xl border-2 border-[#ead9bf] bg-white p-4 shadow-[0_3px_0_#ead9bf]"
              style={{ borderLeft: `6px solid ${accent}` }}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span
                  className="rounded-full px-3 py-0.5 font-display text-sm font-semibold text-white"
                  style={{ background: accent }}
                >
                  {e.agent}
                </span>
                <time className="text-xs text-[#a58f73]">{new Date(e.timestamp).toLocaleTimeString()}</time>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[#4a3566]">{e.message}</p>
              {e.evidence && (
                <pre className="mt-3 overflow-x-auto rounded-xl bg-[#2e2142] p-3 font-mono text-xs leading-5 text-[#e9dcff]">
                  {e.evidence}
                </pre>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}