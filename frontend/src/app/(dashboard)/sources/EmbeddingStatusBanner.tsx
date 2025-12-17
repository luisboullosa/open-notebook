"use client"

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api/client'
import { Loader2 } from 'lucide-react'

async function fetchEmbeddingSummary() {
  try {
    const res = await apiClient.get('/commands/embedding/status')
    return res.data?.summary ?? null
  } catch {
    return null
  }
}

export function EmbeddingStatusBanner() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['embedding-tasks-summary'],
    queryFn: fetchEmbeddingSummary,
    refetchInterval: 5000,
    staleTime: 3000,
  })

  if (!summary) return null

  const running = summary.running || 0
  const queued = summary.queued || 0
  const pending = summary.pending || 0

  if (running === 0 && queued === 0 && pending === 0) return null

  return (
    <div className="mb-4 rounded-md bg-yellow-50 border border-yellow-200 px-4 py-2 flex items-center gap-3">
      <div className="flex items-center gap-2">
        <Loader2 className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
      </div>
      <div className="text-sm">
        Embedding jobs: {running} running{queued ? `, ${queued} queued` : ''}{pending ? `, ${pending} pending` : ''} — processing continues in background.
      </div>
    </div>
  )
}
