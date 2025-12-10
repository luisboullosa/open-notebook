'use client'

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Plus, Play } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { AnkiCard, CreateCardDialog } from '@/components/anki'
import { useDeck, useDeckCards, useDeleteCard } from '@/lib/hooks/use-anki'
import type { AnkiCard as AnkiCardType } from '@/lib/api/anki'
import { Skeleton } from '@/components/ui/skeleton'

export default function DeckDetailPage() {
  const params = useParams()
  const router = useRouter()
  const deckId = params.deckId as string
  
  const [createCardOpen, setCreateCardOpen] = useState(false)
  const [selectedCard, setSelectedCard] = useState<AnkiCardType | null>(null)
  
  const { data: deck, isLoading: isDeckLoading } = useDeck(deckId)
  const { data: cards, isLoading: isCardsLoading } = useDeckCards(deckId)
  const deleteCard = useDeleteCard()

  const handleEditCard = (card: AnkiCardType) => {
    setSelectedCard(card)
    setCreateCardOpen(true)
  }

  const handleDeleteCard = async (cardId: string) => {
    if (confirm('Are you sure you want to delete this card?')) {
      await deleteCard.mutateAsync(cardId)
    }
  }

  const handlePlayAudio = (card: AnkiCardType) => {
    if (card.audio_metadata?.reference_mp3) {
      const audio = new Audio(card.audio_metadata.reference_mp3)
      audio.play()
    }
  }

  const handleStartStudy = () => {
    router.push(`/anki/${deckId}/study`)
  }

  if (isDeckLoading) {
    return (
      <AppShell>
        <div className="container mx-auto py-8 px-4">
          <Skeleton className="h-8 w-64 mb-4" />
          <Skeleton className="h-4 w-96 mb-8" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        </div>
      </AppShell>
    )
  }

  if (!deck) {
    return (
      <AppShell>
        <div className="container mx-auto py-8 px-4">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Deck Not Found</h1>
            <Button onClick={() => router.push('/anki')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Decks
            </Button>
          </div>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/anki')}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Decks
          </Button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">{deck.name}</h1>
              {deck.description && (
                <p className="text-muted-foreground mt-1">{deck.description}</p>
              )}
              <p className="text-sm text-muted-foreground mt-2">
                {cards?.length || 0} cards
              </p>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleStartStudy} disabled={!cards || cards.length === 0}>
                <Play className="mr-2 h-4 w-4" />
                Start Study
              </Button>
              <Button onClick={() => setCreateCardOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                New Card
              </Button>
            </div>
          </div>
        </div>

        {/* Cards Grid */}
        {isCardsLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : cards && cards.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cards.map((card) => (
              <AnkiCard
                key={card.id}
                card={card}
                onEdit={handleEditCard}
                onDelete={handleDeleteCard}
                onPlayAudio={handlePlayAudio}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No cards in this deck yet</p>
            <Button onClick={() => setCreateCardOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Card
            </Button>
          </div>
        )}

        {/* Create/Edit Card Dialog */}
        <CreateCardDialog
          open={createCardOpen}
          onOpenChange={(open) => {
            setCreateCardOpen(open)
            if (!open) setSelectedCard(null)
          }}
          deckId={deckId}
          card={selectedCard || undefined}
        />
      </div>
    </AppShell>
  )
}
