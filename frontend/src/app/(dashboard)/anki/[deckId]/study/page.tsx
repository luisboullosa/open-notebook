'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ArrowLeft, RotateCcw, Volume2 } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { useDeck, useDeckCards, useRateCard, useRecordStudy } from '@/lib/hooks/use-anki'
import type { AnkiCard } from '@/lib/api/anki'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

const RATING_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: 'Again', color: 'bg-red-500 hover:bg-red-600' },
  2: { label: 'Hard', color: 'bg-orange-500 hover:bg-orange-600' },
  3: { label: 'Good', color: 'bg-yellow-500 hover:bg-yellow-600' },
  4: { label: 'Easy', color: 'bg-green-500 hover:bg-green-600' },
  5: { label: 'Perfect', color: 'bg-emerald-500 hover:bg-emerald-600' },
}

export default function StudyPage() {
  const params = useParams()
  const router = useRouter()
  const deckId = decodeURIComponent(params.deckId as string)

  const { data: deck, isLoading: isDeckLoading } = useDeck(deckId)
  const { data: cards, isLoading: isCardsLoading } = useDeckCards(deckId)
  const rateCard = useRateCard()
  const recordStudy = useRecordStudy()

  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [studiedCards, setStudiedCards] = useState<Set<string>>(new Set())
  const [sessionComplete, setSessionComplete] = useState(false)

  const studyCards: AnkiCard[] = cards || []
  const currentCard = studyCards[currentIndex]
  const progress = studyCards.length > 0
    ? Math.round((studiedCards.size / studyCards.length) * 100)
    : 0

  const handleFlip = useCallback(() => {
    if (!isFlipped && currentCard) {
      recordStudy.mutate(currentCard.id)
      setStudiedCards(prev => new Set([...prev, currentCard.id]))
    }
    setIsFlipped(prev => !prev)
  }, [isFlipped, currentCard, recordStudy])

  const handleRate = useCallback(async (rating: number) => {
    if (!currentCard) return

    await rateCard.mutateAsync({ cardId: currentCard.id, rating })

    // Move to next card
    if (currentIndex + 1 >= studyCards.length) {
      setSessionComplete(true)
    } else {
      setCurrentIndex(prev => prev + 1)
      setIsFlipped(false)
    }
  }, [currentCard, currentIndex, studyCards.length, rateCard])

  const handlePlayAudio = useCallback(() => {
    if (currentCard?.audio_metadata?.reference_mp3) {
      const audio = new Audio(currentCard.audio_metadata.reference_mp3)
      audio.play()
    }
  }, [currentCard])

  const handleRestart = useCallback(() => {
    setCurrentIndex(0)
    setIsFlipped(false)
    setStudiedCards(new Set())
    setSessionComplete(false)
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !isFlipped) {
        e.preventDefault()
        handleFlip()
      } else if (isFlipped) {
        if (e.key === '1') handleRate(1)
        else if (e.key === '2') handleRate(2)
        else if (e.key === '3') handleRate(3)
        else if (e.key === '4') handleRate(4)
        else if (e.key === '5') handleRate(5)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isFlipped, handleFlip, handleRate])

  if (isDeckLoading || isCardsLoading) {
    return (
      <AppShell>
        <div className="container mx-auto py-8 px-4 max-w-2xl">
          <Skeleton className="h-8 w-64 mb-4" />
          <Skeleton className="h-64 w-full" />
        </div>
      </AppShell>
    )
  }

  if (!deck) {
    return (
      <AppShell>
        <div className="container mx-auto py-8 px-4 text-center">
          <p className="text-muted-foreground">Deck not found</p>
          <Button className="mt-4" onClick={() => router.push('/anki')}>Back to Decks</Button>
        </div>
      </AppShell>
    )
  }

  if (studyCards.length === 0) {
    return (
      <AppShell>
        <div className="container mx-auto py-8 px-4 max-w-2xl text-center">
          <h1 className="text-2xl font-bold mb-4">{deck.name}</h1>
          <p className="text-muted-foreground mb-6">No cards to study in this deck yet.</p>
          <Button onClick={() => router.push(`/anki/${encodeURIComponent(deckId)}`)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Deck
          </Button>
        </div>
      </AppShell>
    )
  }

  if (sessionComplete) {
    return (
      <AppShell>
        <div className="container mx-auto py-8 px-4 max-w-2xl text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-3xl font-bold mb-2">Session Complete!</h1>
          <p className="text-muted-foreground mb-6">
            You studied {studyCards.length} card{studyCards.length !== 1 ? 's' : ''} from{' '}
            <strong>{deck.name}</strong>.
          </p>
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={handleRestart}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Study Again
            </Button>
            <Button onClick={() => router.push(`/anki/${encodeURIComponent(deckId)}`)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Deck
            </Button>
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="container mx-auto py-8 px-4 max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/anki/${encodeURIComponent(deckId)}`)}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            {deck.name}
          </Button>
          <span className="text-sm text-muted-foreground">
            {currentIndex + 1} / {studyCards.length}
          </span>
        </div>

        {/* Progress bar */}
        <Progress value={progress} className="mb-6 h-2" />

        {/* Card */}
        <div
          className="relative cursor-pointer select-none"
          onClick={handleFlip}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.code === 'Space' && handleFlip()}
          aria-label={isFlipped ? 'Card back (click to flip)' : 'Card front (click to see answer)'}
        >
          <div
            className={`
              min-h-[280px] rounded-xl border bg-card shadow-lg p-8 transition-all duration-300
              flex flex-col items-center justify-center text-center gap-4
              ${isFlipped ? 'border-primary/50 bg-primary/5' : 'hover:border-primary/30'}
            `}
          >
            {/* Card type badge */}
            {currentCard.card_type && (
              <Badge variant="secondary" className="text-xs">
                {currentCard.card_type}
              </Badge>
            )}

            {/* CEFR badge */}
            {currentCard.cefr_level && (
              <Badge variant="outline" className="text-xs">
                {currentCard.cefr_level}
              </Badge>
            )}

            {/* Front / Back content */}
            {!isFlipped ? (
              <div>
                <p className="text-2xl font-semibold">{currentCard.front}</p>
                <p className="text-sm text-muted-foreground mt-4">
                  Press <kbd className="bg-muted px-1 rounded text-xs">Space</kbd> or click to reveal
                </p>
              </div>
            ) : (
              <div className="w-full">
                <p className="text-lg text-muted-foreground mb-2">{currentCard.front}</p>
                <hr className="my-3" />
                <p className="text-2xl font-semibold">{currentCard.back}</p>
                {currentCard.notes && (
                  <p className="text-sm text-muted-foreground mt-3 italic">{currentCard.notes}</p>
                )}
                {currentCard.audio_metadata?.ipa_transcriptions?.[0] && (
                  <p className="text-sm font-mono text-muted-foreground mt-2">
                    /{currentCard.audio_metadata.ipa_transcriptions[0]}/
                  </p>
                )}
              </div>
            )}

            {/* Image */}
            {isFlipped && currentCard.image_metadata?.cached_path && (
              <img
                src={`/uploads/${currentCard.image_metadata.cached_path.replace(/^.*\/uploads\//, '')}`}
                alt={currentCard.front}
                className="max-h-32 rounded-lg object-contain mt-2"
              />
            )}
          </div>
        </div>

        {/* Audio button */}
        {currentCard.audio_metadata?.reference_mp3 && (
          <div className="flex justify-center mt-3">
            <Button variant="ghost" size="sm" onClick={handlePlayAudio}>
              <Volume2 className="mr-2 h-4 w-4" />
              Play Audio
            </Button>
          </div>
        )}

        {/* Rating buttons (only shown after flip) */}
        {isFlipped && (
          <div className="mt-6">
            <p className="text-center text-sm text-muted-foreground mb-3">
              How well did you know this?{' '}
              <span className="text-xs">(or press 1–5)</span>
            </p>
            <div className="grid grid-cols-5 gap-2">
              {[1, 2, 3, 4, 5].map((rating) => (
                <Button
                  key={rating}
                  className={`text-white ${RATING_LABELS[rating].color}`}
                  onClick={() => handleRate(rating)}
                  disabled={rateCard.isPending}
                >
                  <span className="hidden sm:inline">{RATING_LABELS[rating].label}</span>
                  <span className="sm:hidden">{rating}</span>
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {currentCard.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 justify-center mt-4">
            {currentCard.tags.map(tag => (
              <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
