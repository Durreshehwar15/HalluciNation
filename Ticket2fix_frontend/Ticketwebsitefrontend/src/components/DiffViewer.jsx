// Lightweight unified-diff renderer (no extra dependency).
export default function DiffViewer({ file, diff }) {
  const lines = diff.split('\n')
  const added = lines.filter((l) => l.startsWith('+') && !l.startsWith('+++')).length
  const removed = lines.filter((l) => l.startsWith('-') && !l.startsWith('---')).length

  return (
    <div className="overflow-hidden rounded-2xl border-[3px] border-[#e2c39a] bg-[#4a2f1d] shadow-[0_4px_0_#c9955f]">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#f5e6cc]/15 bg-[#6b4630] px-4 py-2.5">
        <span className="font-display text-sm font-semibold text-[#f9e4c3]">📄 {file}</span>
        <div className="flex gap-2 font-display text-xs font-semibold">
          <span className="rounded-full bg-[#b8d98a]/20 px-2 py-0.5 text-[#d6ecae]">+{added}</span>
          <span className="rounded-full bg-[#ff9d7a]/20 px-2 py-0.5 text-[#ffc9b0]">−{removed}</span>
        </div>
      </div>

      <pre className="overflow-x-auto py-2 font-mono text-xs leading-6">
        {lines.map((line, i) => {
          let cls = 'text-[#f5e6cc]'
          let sign = ' '
          if (line.startsWith('+++') || line.startsWith('---')) cls = 'text-[#b89a78]'
          else if (line.startsWith('+')) { cls = 'bg-[#b8d98a]/15 text-[#d6ecae]'; sign = '+' }
          else if (line.startsWith('-')) { cls = 'bg-[#ff9d7a]/15 text-[#ffc9b0]'; sign = '−' }
          else if (line.startsWith('@@')) cls = 'bg-[#c9955f]/25 text-[#f0cf9f]'
          return (
            <div key={i} className={`flex px-2 ${cls}`}>
              <span className="w-5 shrink-0 select-none text-center opacity-70">{sign}</span>
              <span className="whitespace-pre pr-4">{sign === ' ' ? line : line.slice(1) || ' '}</span>
            </div>
          )
        })}
      </pre>
    </div>
  )
}