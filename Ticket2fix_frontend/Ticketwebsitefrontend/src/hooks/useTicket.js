import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client.js'

export function useTicket(id) {
  return useQuery({
    queryKey: ['ticket', id],
    queryFn: () => api.getTicket(id),
    enabled: Boolean(id),
    refetchInterval: 3000,
  })
}

export function useTickets() {
  return useQuery({
    queryKey: ['tickets'],
    queryFn: api.listTickets,
    refetchInterval: 3000,
  })
}
