import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTicket } from '../hooks/useTicket.js'
import { api } from '../api/client.js'
import DiffViewer from '../components/DiffViewer.jsx'
import TestResults from '../components/TestResults.jsx'
import Avatar from '../components/Avatar.jsx'
import { HEAD } from '../content/assets.js'

export default function Approval() {
  const { id } = useParams()
  const qc = useQueryClient()
  const { data: t, isLoading } = useTicket(id)
  const [feedback, setFeedback] = useState('')
  const done = () => qc.invalidateQueries({ queryKey: ['ticket', id] })
  const approve = useMutation({ mutationFn: () => api.approve(id), onSuccess: done })
  const reject = useMutation({ mutationFn: () => api.reject(id, feedback), onSuccess: done })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-3 py-16">
        <img src={HEAD.dog} alt="" className="bob h-16 w-auto" />
        <p className="font-display text-lg text-ink">Loading…</p>
      </div>
    )
  }

  if (!t.patch) {
    return (
      <div className="wood-card flex flex-col items-center gap-3 p-8 text-center">
        <img src={HEAD.dog} alt="" className="bob h-20 w-auto" />
        <p className="font-display text-lg font-semibold text-ink">No patch yet</p>
        <p className="text-sm">The Fix Agent is still working on it.</p>
        <Link to={`/tickets/${id}`} className="btn-mint mt-2 text-sm">Back to progress</Link>
      </div>
    )
  }

  const canDecide = t.status === 'awaiting_approval'
  const verdictGood = t.review?.verdict === 'approved'

  return (
    <div className="space-y-8">
      {/* header */}
      <div className="wood-card p-6 md:p-8">
        <Link
  to={`/tickets/${id}`}
  className="group inline-flex items-center gap-2 rounded-full border-2 border-[#e2c39a] bg-white px-4 py-1.5 font-display text-sm font-semibold text-ink shadow-[0_3px_0_#e2c39a] transition hover:-translate-y-0.5 hover:border-mint hover:text-mint hover:shadow-[0_3px_0_#8a5cc8]"
>
  Back to ticket #{id}
</Link>
        <span className="mt-4 block w-fit rounded-full bg-tomato px-3 py-0.5 font-display text-sm font-bold text-white shadow-[0_3px_0_#a9570f]">
          Approve fix
        </span>
        <h1 className="mt-3 text-2xl font-bold leading-tight md:text-4xl">{t.title}</h1>
        <p className="mt-2 text-sm">Nothing is merged until you say yes.</p>
      </div>

      {/* code change */}
      <section>
        <h2 className="mb-3 font-display text-lg font-semibold">🔧 Code change</h2>
        <DiffViewer file={t.patch.file} diff={t.patch.diff} />
      </section>

      {/* tests + verdict */}
      {(t.test_results || t.review) && (
        <div className="grid items-stretch gap-6 md:grid-cols-2">
          {t.test_results && <TestResults results={t.test_results} />}
          {t.review && (
            <div className="wood-card h-full p-5">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <Avatar src={HEAD.cat} className="h-11 w-11 border-[3px]" />
                  <h3 className="font-display text-lg font-semibold">Reviewer verdict</h3>
                </div>
                <span className={`rounded-full border-2 border-white/60 px-3 py-0.5 font-display text-sm font-semibold shadow-sm ${verdictGood ? 'bg-[#e3f6ea] text-[#3a9b5c]' : 'bg-orange-100 text-orange-700'}`}>
                  {t.review.verdict}
                </span>
              </div>
              <ul className="mt-4 space-y-2">
                {t.review.comments.map((c) => (
                  <li key={c} className="flex gap-2 text-sm leading-relaxed">
                    <span className="mt-0.5 text-[#4cc27a]">●</span>{c}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* decision */}
      {canDecide ? (
        <section className="wood-card border-tomato bg-[#fff0d6] p-6 shadow-[0_0_0_4px_rgba(221,116,36,.15)]">
          <div className="mb-3 flex items-center gap-3">
            <img src={HEAD.dragon} alt="" className="bob h-12 w-auto" />
            <h2 className="font-display text-xl font-semibold">Your decision</h2>
          </div>
          <textarea
            rows={3}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Feedback (required to request changes)"
            className="w-full rounded-2xl border-2 border-[#e2c39a] bg-white px-4 py-2.5 text-sm outline-none transition focus:border-mint focus:ring-4 focus:ring-mint/20"
          />
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              onClick={() => approve.mutate()}
              disabled={approve.isPending || reject.isPending}
              className="btn-mint cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
            >
              {approve.isPending ? 'Creating PR…' : 'Approve & create PR'}
            </button>
            <button
              onClick={() => reject.mutate()}
              disabled={!feedback.trim() || reject.isPending || approve.isPending}
              className="cursor-pointer rounded-full border-2 border-tomato bg-white px-5 py-2 font-display font-semibold text-tomato transition hover:bg-tomato hover:text-white disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white disabled:hover:text-tomato"
            >
              {reject.isPending ? 'Sending…' : '↩ Request changes'}
            </button>
          </div>
          {(approve.error || reject.error) && (
            <p className="mt-3 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
              {(approve.error || reject.error).message}
            </p>
          )}
        </section>
      ) : (
        <section className="wood-card flex flex-wrap items-center gap-4 p-5">
          <span className="text-2xl" aria-hidden="true"></span>
          <p className="text-sm">
            Decision recorded: <b className="text-ink">{t.status.replace(/_/g, ' ')}</b>
          </p>
          {t.pr_url && (
            <a className="btn-mint ml-auto text-sm" href={t.pr_url} target="_blank" rel="noreferrer">View PR ↗</a>
          )}
        </section>
      )}
    </div>
  )
}