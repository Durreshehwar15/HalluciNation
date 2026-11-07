import { Link } from 'react-router-dom'
import GameBoard from '../components/GameBoard.jsx'
import DiffViewer from '../components/DiffViewer.jsx'
import { AGENTS } from '../content/agents.js'
import { STEPS } from '../content/guide.js'
import { IMG, STEP_IMG, STEP_MAS } from '../content/assets.js'
import { PATCH } from '../api/mockTicket.js'

export default function Home() {
  return (
    <div className="overflow-x-hidden">
      {/* ---------- 1. MAIN IMAGE (first thing visitors see) ---------- */}
      <section
        className="relative h-svh min-h-[600px] bg-cover bg-center"
        style={{ backgroundImage: `url("${encodeURI(IMG.main)}")` }}
      >
        {/* soft dark shadow at the top so the menu text stays readable */}
        <div className="absolute inset-x-0 top-0 h-44 bg-gradient-to-b from-[#24123a]/55 via-[#24123a]/20 to-transparent" />
        <a
          href="#board"
          className="bob absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full border-2 border-[#c9955f] bg-[#fff4e0]/95 px-8 py-4 text-xl font-display text-sm font-semibold text-[#6b3f27] shadow-lg"
        >
          Enter the town
        </a>
      </section>

      {/* ---------- 2. GAME BOARD ---------- */}
      <section id="board" className="bg-[#fff8ef] px-4 py-16">
        <div className="mx-auto mb-8 max-w-3xl text-center">
          <h2 className="brush text-3xl">Welcome to Ticket2fix town</h2>
          <p className="mt-4 text-sm leading-relaxed">
            Every character has a job. Click one to report a bug, watch the agents work,
            review the fix, or read the guide.
          </p>
        </div>
        <GameBoard />
      </section>

      {/* ---------- 3. MEET THE TEAM ---------- */}
      <section id="agents" className="bg-[#f5eefc] px-4 py-16">
        <div className="mx-auto max-w-5xl">
          <div className="text-center">
            <h2 className="brush text-3xl">Meet your unlikely new team</h2>
            <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed">
              Five specialist agents talk to each other through Switch. They hand over work, share evidence
              and challenge each other’s results before anything reaches you.
            </p>
          </div>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
            {AGENTS.map((a, i) => (
              <div key={a.name} className="wood-card p-4 text-center">
                <div className="flex h-44 items-end justify-center">
                  {a.img
                    ? <img src={a.img} alt={a.name} className="bob h-full w-auto object-contain" style={{ animationDelay: `${-i * 0.5}s` }} />
                    : <span className="bob flex h-28 w-28 items-center justify-center rounded-full bg-[#e5d6f8] text-5xl">{a.emoji}</span>}
                </div>
                <h3 className="mt-3 text-base font-semibold leading-tight">{a.name}</h3>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{a.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- 4. HUMAN CONTROL (artwork background) ---------- */}
      <section id="control" className="bg-[#fbeed8] px-2 py-10 sm:px-4">
        <div
          className="relative mx-auto max-w-6xl overflow-hidden rounded-3xl bg-cover bg-center lg:aspect-video"
          style={{ backgroundImage: `url("${encodeURI(IMG.charge)}")` }}
        >
          {/* on large screens the content sits inside the parchment of the picture */}
          <div className="grid items-center gap-0 px-6 py-12 lg:absolute lg:inset-y-[13%] lg:left-[12.5%] lg:right-[13.5%] lg:grid-cols-2 lg:p-0">
            <div>
              <h2 className="brush text-3xl">You stay in charge</h2>
              <p className="mt-5 max-w-sm text-sm leading-relaxed text-[#6b3f27]">
                Review the code diff, the test evidence and the reviewer’s verdict. Nothing is merged
                until a human presses approve.
              </p>
              <Link to="/tickets" className="btn-mint mt-5">See the tickets</Link>
            </div>
            <div className="min-w-0 shadow-xl"><DiffViewer file={PATCH.file} diff={PATCH.diff} /></div>
          </div>
        </div>
      </section>

      {/* ---------- 5. GUIDE PREVIEW ---------- */}
      <section id="guide" className="bg-[#f5eefc] px-4 py-16">
        <div className="mx-auto max-w-5xl">
          <div className="text-center"><h2 className="brush text-3xl">How to use this website</h2></div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s, i) => (
              <div key={s.n} className="wood-card relative p-5 pt-8 text-center">
                <span className="absolute -top-4 left-1/2 flex h-9 w-9 -translate-x-1/2 items-center justify-center rounded-full bg-tomato font-display text-lg font-bold text-white shadow">{s.n}</span>
                <img src={STEP_MAS[i]} alt="" className="mx-auto h-56 w-auto object-contain" />
                <h3 className="mt-2 text-lg font-semibold">{s.title}</h3>
                <p className="mt-1 text-sm text-slate-600">{s.short}</p>
              </div>
            ))}
          </div>
          <div className="mt-10 text-center"><Link to="/guide" className="btn-red">Read the full guide</Link></div>
        </div>
      </section>
    </div>
  )
}