import { Link } from 'react-router-dom'
import StatusBadge from '../components/StatusBadge.jsx'
import { STEPS, STATUSES, FAQ } from '../content/guide.js'
import { STEP_MAS } from '../content/assets.js'

// only mas1..mas4 on this page (mas5 is ignored)
const GUIDE_IMGS = STEP_MAS.slice(0, 4)

// character on a round background
function CircleImg({ src, className = 'h-32 w-32', delay }) {
  return (
    <div
      className={`bob flex shrink-0 items-center justify-center rounded-full border-[3px] border-[#e2c39a] bg-[#ece0fb] shadow-[0_4px_0_#e2c39a] ${className}`}
      style={delay ? { animationDelay: delay } : undefined}
    >
      <img src={src} alt="" className="h-[78%] w-auto object-contain" />
    </div>
  )
}

export default function Guide() {
  return (
    <div>
      <section className="px-4 pt-12 text-center">
        <h1 className="brush text-4xl md:text-5xl">Website guide</h1>
        <div className="mt-8 flex flex-wrap items-end justify-center gap-5">
          {GUIDE_IMGS.map((src, i) => (
            <CircleImg key={src} src={src} className="h-28 w-28 md:h-32 md:w-32" delay={`${-i * 0.6}s`} />
          ))}
        </div>
      </section>

      <div className="mx-auto max-w-4xl space-y-16 px-4 py-14">
        <section id="steps" className="space-y-6">
          <h2 className="brush text-2xl">Step by step</h2>
          {STEPS.map((s, i) => (
            <article key={s.n} className="wood-card flex flex-col items-center gap-5 p-6 sm:flex-row sm:items-start">
              <div className="flex shrink-0 flex-col items-center">
                <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-tomato font-display text-lg font-bold text-white">{s.n}</span>
                <CircleImg src={GUIDE_IMGS[i]} className="h-32 w-32" delay={`${-i * 0.6}s`} />
              </div>
              <div>
                <h3 className="text-xl font-semibold">{s.title}</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed">
                  {s.long.map((l) => <li key={l}>{l}</li>)}
                </ul>
                <Link to={s.link} className="btn-mint mt-4 text-sm">{s.cta}</Link>
              </div>
            </article>
          ))}
        </section>

        <section id="statuses">
          <h2 className="brush text-2xl">What the statuses mean</h2>
          <div className="mt-6 overflow-hidden rounded-2xl border-2 border-[#e2c39a] bg-white">
            {STATUSES.map(([s, text]) => (
              <div key={s} className="flex items-center gap-4 border-b border-[#f0e3cf] px-4 py-2.5 text-sm last:border-b-0">
                <div className="w-40 shrink-0"><StatusBadge status={s} /></div>
                <span>{text}</span>
              </div>
            ))}
          </div>
        </section>

        <section id="faq">
          <h2 className="brush text-2xl">Questions</h2>
          <div className="mt-6 space-y-3">
            {FAQ.map(([q, a]) => (
              <details key={q} className="group wood-card px-5 py-3">
                <summary className="cursor-pointer list-none font-display text-lg font-semibold text-ink">
                  <span className="mr-2 text-mint group-open:hidden">+</span>
                  <span className="mr-2 hidden text-mint group-open:inline">–</span>{q}
                </summary>
                <p className="mt-2 text-sm leading-relaxed">{a}</p>
              </details>
            ))}
          </div>
        </section>

        <div className="text-center"><Link to="/submit" className="btn-red">Report my first bug</Link></div>
      </div>
    </div>
  )
}