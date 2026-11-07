import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTicket } from '../hooks/useTicket.js'
import PipelineStepper from '../components/PipelineStepper.jsx'
import AgentFeed from '../components/AgentFeed.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { HEAD } from '../content/assets.js'

export default function TicketDetail() {
  const { id } = useParams()
  const { data: t, isLoading, error } = useTicket(id)
  const [open, setOpen] = useState(null) // screenshot shown full size

  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-3 py-16">
        <img src={HEAD.dog} alt="" className="bob h-16 w-auto" />
        <p className="font-display text-lg text-ink">Loading…</p>
      </div>
    )
  }
  if (error) {
    return <p className="wood-card p-5 text-red-700">{error.message}</p>
  }

  return (
    <div className="space-y-8">
      {/* header */}
      <div className="wood-card p-6 md:p-8">
        <Link
          to="/tickets"
          className="group inline-flex items-center gap-2 rounded-full border-2 border-[#e2c39a] bg-white px-4 py-1.5 font-display text-sm font-semibold text-ink shadow-[0_3px_0_#e2c39a] transition hover:-translate-y-0.5 hover:border-mint hover:text-mint hover:shadow-[0_3px_0_#8a5cc8]"
        >
          All tickets
        </Link>

        <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <span className="inline-block rounded-full bg-tomato px-3 py-0.5 font-display text-sm font-bold text-white shadow-[0_3px_0_#a9570f]">
              Ticket #{t.id}
            </span>
            <h1 className="mt-3 text-2xl font-bold leading-tight md:text-4xl">{t.title}</h1>
            <p className="mt-3 max-w-2xl text-base leading-relaxed">{t.description}</p>
          </div>
          <div className="shrink-0 sm:pt-1"><StatusBadge status={t.status} /></div>
        </div>
      </div>

      {/* screenshots */}
      {t.images?.length > 0 && (
        <section>
          <h2 className="mb-3 font-display text-lg font-semibold">📎 Attached screenshots</h2>
          <div className="flex flex-wrap gap-3">
            {t.images.map((img, i) => {
              const src = img.data || img.url
              return (
                <button key={i} type="button" onClick={() => setOpen(src)}
                        className="cursor-pointer overflow-hidden rounded-2xl border-[3px] border-[#e2c39a] shadow-[0_3px_0_#e2c39a] transition hover:-translate-y-0.5 hover:shadow-lg">
                  <img src={src} alt={img.name || `Screenshot ${i + 1}`} className="h-24 w-36 object-cover" />
                </button>
              )
            })}
          </div>
        </section>
      )}

      {/* progress */}
      <PipelineStepper status={t.status} />

      {/* call to action when it's the human's turn */}
      {t.status === 'awaiting_approval' && (
        <div className="wood-card flex flex-col items-center gap-4 border-tomato bg-[#fff0d6] p-5 shadow-[0_0_0_4px_rgba(221,116,36,.15)] sm:flex-row sm:justify-between">
          <div className="flex items-center gap-4">
            <img src={HEAD.dragon} alt="" className="bob h-16 w-auto" />
            <div>
              <p className="font-display text-lg font-semibold text-ink">Your turn!</p>
              <p className="text-sm">The agents are done. Review the patch and decide.</p>
            </div>
          </div>
          <Link to={`/tickets/${t.id}/approve`} className="btn-red whitespace-nowrap">
            Review patch &amp; approve 
          </Link>
        </div>
      )}

      {t.pr_url && (
        <a href={t.pr_url} target="_blank" rel="noreferrer" className="btn-mint">
          View pull request ↗
        </a>
      )}

      {/* agent activity */}
      <section>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <h2 className="brush text-lg">Agent activity</h2>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#e3f6ea] px-2.5 py-0.5 text-xs font-semibold text-[#3a9b5c]">
            <span className="h-2 w-2 animate-pulse rounded-full bg-[#4cc27a]" />
            live via Switch
          </span>
        </div>
        <AgentFeed events={t.events} />
      </section>

      {/* screenshot lightbox */}
      {open && (
        <div className="fixed inset-0 z-50 flex cursor-zoom-out items-center justify-center bg-black/70 p-4" onClick={() => setOpen(null)}>
          <img src={open} alt="" className="max-h-full max-w-full rounded-xl shadow-2xl" />
        </div>
      )}
    </div>
  )
}