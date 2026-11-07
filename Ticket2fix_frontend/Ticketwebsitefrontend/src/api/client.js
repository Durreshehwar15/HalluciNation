const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function http(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!res.ok) {
    const message = await res.text()
    throw new Error(`${res.status}: ${message}`)
  }

  return res.json()
}

const normalize = (ticket) => ({
  ...ticket,
  id: ticket.ticket_id ?? ticket.id,
})

export const api = {
  listTickets: async () => {
    const result = await http('/tickets')
    return (result.items || []).map(normalize)
  },

  getTicket: async (id) =>
    normalize(await http(`/tickets/${encodeURIComponent(id)}`)),

  createTicket: async (data) => {
    const description = data.logs?.trim()
      ? `${data.description}\n\nError logs:\n${data.logs}`
      : data.description

    return normalize(await http('/tickets', {
      method: 'POST',
      body: JSON.stringify({
        title: data.title,
        description,
        repository: data.repository,
        branch: data.branch || 'main',
        priority: data.priority || 'medium',
      }),
    }))
  },

  analyze: async (id) =>
    normalize(await http(`/tickets/${encodeURIComponent(id)}/analyze`, {
      method: 'POST',
    })),

  getPatch: (id) =>
    http(`/tickets/${encodeURIComponent(id)}/patch`),

  getEvents: (id, afterId = 0) =>
    http(`/tickets/${encodeURIComponent(id)}/events?after_id=${afterId}`),

  verify: (id) =>
    http(`/tickets/${encodeURIComponent(id)}/verify`, {
      method: 'POST',
    }),

  approve: async () => {
    throw new Error('Human approval requires the secured approval credential and exact patch details.')
  },

  reject: async () => {
    throw new Error('The backend does not currently provide a reject endpoint.')
  },
}
