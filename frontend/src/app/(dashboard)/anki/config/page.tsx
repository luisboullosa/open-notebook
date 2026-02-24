'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ArrowLeft, RefreshCw, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { useAnkiConfigCheck } from '@/lib/hooks/use-anki'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

function StatusIcon({ status }: { status: string }) {
  if (status === 'healthy') return <CheckCircle2 className="h-5 w-5 text-green-500" />
  if (status === 'unhealthy') return <XCircle className="h-5 w-5 text-red-500" />
  return <AlertCircle className="h-5 w-5 text-yellow-500" />
}

function StatusBadge({ status }: { status: string }) {
  const variant = status === 'healthy' ? 'default' : status === 'unhealthy' ? 'destructive' : 'secondary'
  return <Badge variant={variant}>{status}</Badge>
}

export default function AnkiConfigPage() {
  const router = useRouter()
  const { data: config, isLoading, refetch } = useAnkiConfigCheck()

  return (
    <AppShell>
      <div className="container mx-auto py-8 px-4 max-w-3xl">
        <div className="flex items-center justify-between mb-6">
          <Button variant="ghost" size="sm" onClick={() => router.push('/anki')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Decks
          </Button>
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <h1 className="text-3xl font-bold mb-2">Anki Configuration Check</h1>
        <p className="text-muted-foreground mb-8">
          Verify that all required services and AI models are available for Anki card generation.
        </p>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : !config ? (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <p className="text-destructive">Failed to load configuration status. Is the API server running?</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Ollama / LLM Status */}
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <StatusIcon status={config.ollama.status} />
                <h2 className="text-xl font-semibold">Ollama (LLM Provider)</h2>
                <StatusBadge status={config.ollama.status} />
              </div>

              {config.ollama.error && (
                <p className="text-sm text-destructive mb-3">{config.ollama.error}</p>
              )}

              <p className="text-sm text-muted-foreground mb-4">
                {config.recommended_models.description}
              </p>

              {config.ollama.status === 'healthy' && (
                <>
                  {/* Required models */}
                  <div className="mb-3">
                    <p className="text-sm font-medium mb-2">Required models:</p>
                    <div className="flex flex-wrap gap-2">
                      {config.recommended_models.required.map(model => {
                        const installed = config.ollama.required_installed?.includes(model)
                        return (
                          <Badge
                            key={model}
                            variant={installed ? 'default' : 'destructive'}
                            className="text-xs"
                          >
                            {installed ? '✓' : '✗'} {model}
                          </Badge>
                        )
                      })}
                    </div>
                    {config.ollama.required_missing && config.ollama.required_missing.length > 0 && (
                      <p className="text-xs text-destructive mt-2">
                        Missing required models. Install with:{' '}
                        <code className="bg-muted px-1 rounded">
                          ollama pull {config.ollama.required_missing.join(' && ollama pull ')}
                        </code>
                      </p>
                    )}
                  </div>

                  {/* Recommended models */}
                  <div className="mb-3">
                    <p className="text-sm font-medium mb-2">Recommended models:</p>
                    <div className="flex flex-wrap gap-2">
                      {config.recommended_models.recommended.map(model => {
                        const installed = config.ollama.recommended_installed?.includes(model)
                        return (
                          <Badge
                            key={model}
                            variant={installed ? 'secondary' : 'outline'}
                            className="text-xs"
                          >
                            {installed ? '✓' : '○'} {model}
                          </Badge>
                        )
                      })}
                    </div>
                  </div>

                  {/* All installed models */}
                  {config.ollama.models.length > 0 && (
                    <details className="mt-3">
                      <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                        All installed models ({config.ollama.models.length})
                      </summary>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {config.ollama.models.map(model => (
                          <Badge key={model} variant="outline" className="text-xs font-mono">
                            {model}
                          </Badge>
                        ))}
                      </div>
                    </details>
                  )}
                </>
              )}

              {config.ollama.status === 'unhealthy' && (
                <div className="mt-3 text-sm">
                  <p className="font-medium text-muted-foreground">Troubleshooting:</p>
                  <ul className="list-disc list-inside text-muted-foreground mt-1 space-y-1">
                    <li>Make sure the Ollama service is running</li>
                    <li>Check that OLLAMA_API_BASE environment variable is set correctly</li>
                    <li>In Docker Compose, Ollama should be at <code className="bg-muted px-1 rounded">http://ollama:11434</code></li>
                  </ul>
                </div>
              )}
            </div>

            {/* Audio (Piper TTS) */}
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-3 mb-3">
                <StatusIcon status={config.piper_tts.status} />
                <h2 className="text-xl font-semibold">Piper TTS (Text-to-Speech)</h2>
                <StatusBadge status={config.piper_tts.status} />
              </div>
              <p className="text-sm text-muted-foreground">
                Used to generate pronunciation audio for Dutch vocabulary cards.
                Optional — cards can be created without audio.
              </p>
              {config.piper_tts.error && (
                <p className="text-xs text-destructive mt-2">{config.piper_tts.error}</p>
              )}
            </div>

            {/* Speech-to-Text (Whisper) */}
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-3 mb-3">
                <StatusIcon status={config.whisper_stt.status} />
                <h2 className="text-xl font-semibold">Whisper STT (Speech-to-Text)</h2>
                <StatusBadge status={config.whisper_stt.status} />
              </div>
              <p className="text-sm text-muted-foreground">
                Used to transcribe and score your pronunciation recordings in study mode.
                Optional — study mode works without this.
              </p>
              {config.whisper_stt.error && (
                <p className="text-xs text-destructive mt-2">{config.whisper_stt.error}</p>
              )}
            </div>

            {/* Image APIs */}
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center gap-3 mb-3">
                <AlertCircle className="h-5 w-5 text-yellow-500" />
                <h2 className="text-xl font-semibold">Image APIs</h2>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                Image APIs provide contextual images for visual learning cards.
                Configure at least one for the best card generation experience.
              </p>
              <div className="flex gap-3">
                <Badge variant={config.image_apis.unsplash ? 'default' : 'secondary'}>
                  {config.image_apis.unsplash ? '✓' : '○'} Unsplash
                </Badge>
                <Badge variant={config.image_apis.pexels ? 'default' : 'secondary'}>
                  {config.image_apis.pexels ? '✓' : '○'} Pexels
                </Badge>
                <Badge variant={config.image_apis.pixabay ? 'default' : 'secondary'}>
                  {config.image_apis.pixabay ? '✓' : '○'} Pixabay
                </Badge>
              </div>
              {!config.image_apis.unsplash && !config.image_apis.pexels && !config.image_apis.pixabay && (
                <p className="text-xs text-muted-foreground mt-2">
                  Set UNSPLASH_ACCESS_KEY, PEXELS_API_KEY, or PIXABAY_API_KEY in your .env file to enable image search.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
