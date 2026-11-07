import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client.js'

export default function SubmitTicket() {
  const [form, setForm] = useState({
    title: '',
    description: '',
    logs: '',
    repository: 'Durreshehwar15/HalluciNation',
    branch: 'main',
    priority: 'high',
  })

  const navigate = useNavigate()
  const qc = useQueryClient()

  const create = useMutation({
    mutationFn: api.createTicket,
    onSuccess: (ticket) => {
      qc.invalidateQueries({ queryKey: ['tickets'] })
      navigate(`/tickets/${ticket.id}`)
    },
  })

  const update = (key) => (event) =>
    setForm((old) => ({ ...old, [key]: event.target.value }))

  const submit = (event) => {
    event.preventDefault()
    create.mutate(form)
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-5 py-10">
      <section className="wood-card p-6 md:p-8">
        <h1 className="font-display text-3xl font-bold text-ink">
          Submit a support ticket
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Report a bug so it can be tracked by the Support Ticket to Merged Fix system.
        </p>

        <form onSubmit={submit} className="mt-6 space-y-5">
          <label className="block">
            <span className="mb-2 block font-semibold">Issue title</span>
            <input required maxLength={200} value={form.title}
              onChange={update('title')}
              placeholder="Example: Payment page crashes on invalid coupon"
              className="w-full rounded-xl border-2 border-[#e2c39a] bg-white px-4 py-3 text-sm" />
          </label>

          <label className="block">
            <span className="mb-2 block font-semibold">Describe the issue</span>
            <textarea required rows={5} value={form.description}
              onChange={update('description')}
              placeholder="Steps to reproduce, expected result, and actual result..."
              className="w-full rounded-xl border-2 border-[#e2c39a] bg-white px-4 py-3 text-sm" />
          </label>

          <label className="block">
            <span className="mb-2 block font-semibold">Error logs (optional)</span>
            <textarea rows={4} value={form.logs}
              onChange={update('logs')}
              placeholder="Paste error messages or stack traces..."
              className="w-full rounded-xl border-2 border-[#e2c39a] bg-white px-4 py-3 font-mono text-sm" />
          </label>

          <label className="block">
            <span className="mb-2 block font-semibold">GitHub repository</span>
            <input required value={form.repository}
              onChange={update('repository')}
              placeholder="owner/repository"
              className="w-full rounded-xl border-2 border-[#e2c39a] bg-white px-4 py-3 text-sm" />
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="mb-2 block font-semibold">Branch</span>
              <input required value={form.branch}
                onChange={update('branch')}
                className="w-full rounded-xl border-2 border-[#e2c39a] bg-white px-4 py-3 text-sm" />
            </label>

            <label className="block">
              <span className="mb-2 block font-semibold">Priority</span>
              <select value={form.priority} onChange={update('priority')}
                className="w-full rounded-xl border-2 border-[#e2c39a] bg-white px-4 py-3 text-sm">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
          </div>

          {create.isError && (
            <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">
              {create.error.message}
            </p>
          )}

          <button type="submit"
            disabled={create.isPending || !form.title.trim() || !form.description.trim()}
            className="btn-red rounded-full px-6 py-3 font-semibold disabled:opacity-50">
            {create.isPending ? 'Submitting...' : 'Submit ticket'}
          </button>
        </form>
      </section>
    </main>
  )
}


