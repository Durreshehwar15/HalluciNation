import { HEAD } from '../content/assets.js'

export default function TestResults({ results }) {
  const ok = results.failed === 0
  return (
    <div className="wood-card h-full p-5">
      <div className="flex items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 font-display text-lg font-semibold">
          <img src={HEAD.tester} alt="" className="h-9 w-auto object-contain" />
          Test results
        </h3>
        <span className={`rounded-full border-2 border-white/60 px-3 py-0.5 font-display text-sm font-semibold shadow-sm ${ok ? 'bg-[#e3f6ea] text-[#3a9b5c]' : 'bg-red-100 text-red-700'}`}>
          {results.passed}/{results.total} passed
        </span>
      </div>

      <ul className="mt-4 space-y-2">
        {results.cases.map((c) => {
          const isNew = c.name.endsWith(' (new)')
          const name = isNew ? c.name.replace(' (new)', '') : c.name
          const pass = c.status === 'passed'
          return (
            <li key={c.name} className="flex items-center gap-3 rounded-xl border-2 border-[#ead9bf] bg-white px-3 py-2">
              <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${pass ? 'bg-[#4cc27a]' : 'bg-red-500'}`}>
                {pass ? '✓' : '✕'}
              </span>
              <span className="min-w-0 flex-1 truncate font-mono text-xs text-ink">{name}</span>
              {isNew && <span className="rounded-full bg-tomato px-2 py-0.5 text-[10px] font-bold uppercase text-white">new</span>}
            </li>
          )
        })}
      </ul>
    </div>
  )
}