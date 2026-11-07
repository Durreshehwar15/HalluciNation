const COLORS = {
  submitted: 'bg-slate-200 text-slate-700',
  triage: 'bg-blue-100 text-blue-700',
  investigating: 'bg-blue-100 text-blue-700',
  fixing: 'bg-amber-100 text-amber-700',
  testing: 'bg-amber-100 text-amber-700',
  review: 'bg-purple-100 text-purple-700',
  awaiting_approval: 'bg-orange-100 text-orange-700',
  approved: 'bg-green-100 text-green-700',
  pr_created: 'bg-green-100 text-green-700',
  merged: 'bg-green-200 text-green-800',
  rejected: 'bg-red-100 text-red-700',
}

export default function StatusBadge({ status }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${COLORS[status] || COLORS.submitted}`}>
      {status.replace('_', ' ')}
    </span>
  )
}
