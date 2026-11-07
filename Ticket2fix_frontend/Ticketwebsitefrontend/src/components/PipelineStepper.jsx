const STEPS = [
  { label: 'Triage', statuses: ['triage'] },
  { label: 'Investigation', statuses: ['investigating'] },
  { label: 'Fix', statuses: ['fixing'] },
  { label: 'Testing', statuses: ['testing'] },
  { label: 'Review', statuses: ['review'] },
  { label: 'Human Approval', statuses: ['awaiting_approval', 'approved', 'pr_created', 'merged', 'rejected'] },
]
const ORDER = ['submitted', 'triage', 'investigating', 'fixing', 'testing', 'review', 'awaiting_approval', 'approved', 'pr_created', 'merged', 'rejected']

export default function PipelineStepper({ status }) {
  const current = STEPS.findIndex((s) => s.statuses.includes(status))
  const finished = ['approved', 'pr_created', 'merged'].includes(status)

  return (
    <ol className="flex items-center">
      {STEPS.map((step, i) => {
        const done = i < current || finished
        const active = i === current && !finished
        return (
          <li key={step.label} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold
                ${done ? 'bg-green-500 text-white' : active ? 'animate-pulse bg-mint text-white' : 'bg-slate-200 text-slate-500'}`}>
                {done ? '✓' : i + 1}
              </div>
              <span className="text-xs text-slate-600">{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`mx-2 mb-5 h-0.5 flex-1 ${done ? 'bg-green-500' : 'bg-slate-200'}`} />
            )}
          </li>
        )
      })}
    </ol>
  )
}
