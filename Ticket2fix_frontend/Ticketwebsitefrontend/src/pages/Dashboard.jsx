import { Link } from 'react-router-dom'
import { useTickets } from '../hooks/useTicket.js'
import StatusBadge from '../components/StatusBadge.jsx'
import Avatar from '../components/Avatar.jsx'
import { statusInfo } from '../content/agents.js'
import { HEAD } from '../content/assets.js'

export default function Dashboard() {
  const { data: tickets, isLoading, error } = useTickets()

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="brush text-2xl">Tickets</h1>
        <Link to="/submit" className="btn-mint text-sm">+ New ticket</Link>
      </div>

      {isLoading && <p className="text-slate-500">Loading…</p>}

      {error && (
        <div className="wood-card flex items-center gap-4 p-5">
          <img src={HEAD.dragon} alt="" className="bob h-16 w-auto" />
          <p className="text-sm text-red-700">Oh no! Could not reach the backend: {error.message}</p>
        </div>
      )}

      {tickets?.length === 0 && (
        <div className="wood-card flex flex-col items-center gap-2 p-8 text-center">
          <img src={HEAD.dog} alt="" className="bob h-20 w-auto" />
          <p className="font-display text-lg font-semibold text-ink">No tickets yet</p>
          <p className="text-sm">Everyone is napping 💤 Report a bug to wake the team up!</p>
          <Link to="/submit" className="btn-red mt-2">Report a bug</Link>
        </div>
      )}

      <div className="space-y-3">
        {tickets?.map((t) => {
          const info = statusInfo(t.status)
          return (
            <Link key={t.id} to={`/tickets/${t.id}`}
                  className="wood-card flex items-center gap-4 px-4 py-3 transition hover:-translate-y-0.5 hover:shadow-lg">
              <Avatar src={info.head} emoji={info.emoji} className="h-12 w-12" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-display text-base font-semibold text-ink">#{t.id} {t.title}</p>
                <p className="text-xs text-slate-500">{info.text} · {new Date(t.created_at).toLocaleString()}</p>
              </div>
              <StatusBadge status={t.status} />
            </Link>
          )
        })}
      </div>
    </div>
  )
}
