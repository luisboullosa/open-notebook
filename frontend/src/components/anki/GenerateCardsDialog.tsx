'use client'

import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Plus, X } from 'lucide-react'
import { useSources } from '@/lib/hooks/use-sources'
import { useNotebooks } from '@/lib/hooks/use-notebooks'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import ankiApi from '@/lib/api/anki'
import type { AnkiPromptPreset } from '@/lib/api/anki'
import { useCreateCard } from '@/lib/hooks/use-anki'

interface GenerateCardsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  deckId: string
}

const RATING_LABELS: Record<number, string> = {
  1: 'Poor',
  2: 'Needs work',
  3: 'Okay',
  4: 'Good',
  5: 'Excellent',
}

export function GenerateCardsDialog({ open, onOpenChange, deckId }: GenerateCardsDialogProps) {
  const [selectedNotebook, setSelectedNotebook] = useState<string>('')
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [selectedModel, setSelectedModel] = useState('qwen2.5:3b')
  const [promptPresets, setPromptPresets] = useState<AnkiPromptPreset[]>([])
  const [selectedPromptPreset, setSelectedPromptPreset] = useState<string>('default-general')
  const [userPrompt, setUserPrompt] = useState('')
  const [numCards, setNumCards] = useState(1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedCards, setGeneratedCards] = useState<any[]>([])
  const [isAddingCards, setIsAddingCards] = useState(false)
  const [qualityRating, setQualityRating] = useState<number>(0)
  const [feedbackText, setFeedbackText] = useState('')
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false)
  const [acceptedCardsCount, setAcceptedCardsCount] = useState(0)
  const [generationContext, setGenerationContext] = useState<{
    sourceIds: string[]
    modelId: string
    promptTemplateKey?: string
    userPrompt: string
    numCards: number
  } | null>(null)

  const { data: notebooks } = useNotebooks()
  const { data: sources } = useSources(selectedNotebook)
  const createCard = useCreateCard()

  useEffect(() => {
    if (!open) {
      return
    }

    const loadPresets = async () => {
      try {
        const presets = await ankiApi.promptPresets.list()
        setPromptPresets(presets)

        const defaultPreset = presets.find((preset) => preset.key === 'default-general') || presets[0]
        if (defaultPreset) {
          setSelectedPromptPreset(defaultPreset.key)
          setUserPrompt(defaultPreset.instructions)
        }
      } catch (error) {
        toast.error('Failed to load prompt presets')
      }
    }

    void loadPresets()
  }, [open])

  const handleSelectPromptPreset = (presetKey: string) => {
    setSelectedPromptPreset(presetKey)
    const preset = promptPresets.find((item) => item.key === presetKey)
    if (!preset) {
      return
    }
    setUserPrompt(preset.instructions)
  }

  const handleToggleSource = (sourceId: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    )
  }

  const handleGenerate = async () => {
    if (selectedSources.length === 0) {
      toast.error('Please select at least one source')
      return
    }
    if (!userPrompt.trim()) {
      toast.error('Please provide instructions for card generation')
      return
    }

    setIsGenerating(true)
    try {
      const result = await ankiApi.generateCards(deckId, {
        source_ids: selectedSources,
        user_prompt: userPrompt,
        prompt_template_key: selectedPromptPreset,
        model_id: selectedModel,
        num_cards: numCards
      })

      setGeneratedCards(result.cards)
      setAcceptedCardsCount(0)
      setQualityRating(0)
      setFeedbackText('')
      setGenerationContext({
        sourceIds: selectedSources,
        modelId: selectedModel,
        promptTemplateKey: selectedPromptPreset,
        userPrompt,
        numCards,
      })
      toast.success(`Generated ${result.cards.length} card${result.cards.length > 1 ? 's' : ''}`)
    } catch (error: any) {
      console.error('Error generating cards:', error)
      toast.error(error?.response?.data?.detail || 'Failed to generate cards')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleAddCard = async (card: any, index: number) => {
    setIsAddingCards(true)
    try {
      await createCard.mutateAsync({
        front: card.front,
        back: card.back,
        notes: card.notes,
        tags: card.suggested_tags || [],
        deck_id: deckId
      })

      setAcceptedCardsCount((count) => count + 1)

      // Remove card from generated list
      setGeneratedCards(prev => prev.filter((_, i) => i !== index))
      toast.success('Card added to deck')
    } catch (error) {
      toast.error('Failed to add card')
    } finally {
      setIsAddingCards(false)
    }
  }

  const handleAddAllCards = async () => {
    setIsAddingCards(true)
    try {
      const cardsToAdd = generatedCards.length
      for (const card of generatedCards) {
        await createCard.mutateAsync({
          front: card.front,
          back: card.back,
          notes: card.notes,
          tags: card.suggested_tags || [],
          deck_id: deckId
        })
      }
      setAcceptedCardsCount((count) => count + cardsToAdd)
      toast.success(`Added ${generatedCards.length} cards to deck`)
      setGeneratedCards([])
      onOpenChange(false)
    } catch (error) {
      toast.error('Failed to add all cards')
    } finally {
      setIsAddingCards(false)
    }
  }

  const handleSubmitFeedback = async () => {
    if (!generationContext) {
      toast.error('Generate cards first before submitting feedback')
      return
    }
    if (qualityRating === 0) {
      toast.error('Please rate the quality from 1 to 5')
      return
    }

    setIsSubmittingFeedback(true)
    try {
      await ankiApi.feedback.submitGeneration({
        rating: qualityRating,
        feedback_text: feedbackText.trim() || undefined,
        prompt_template_key: generationContext.promptTemplateKey,
        user_prompt: generationContext.userPrompt,
        model_id: generationContext.modelId,
        source_ids: generationContext.sourceIds,
        num_cards: generationContext.numCards,
        generated_cards_count: generatedCards.length + acceptedCardsCount,
        accepted_cards_count: acceptedCardsCount,
      })
      toast.success('Feedback saved. Future generations will use this quality signal.')
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to save feedback')
    } finally {
      setIsSubmittingFeedback(false)
    }
  }

  const handleClose = () => {
    setSelectedNotebook('')
    setSelectedSources([])
    setUserPrompt('')
    setNumCards(1)
    setGeneratedCards([])
    setQualityRating(0)
    setFeedbackText('')
    setAcceptedCardsCount(0)
    setGenerationContext(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Generate Cards from Sources</DialogTitle>
          <DialogDescription>
            Select sources and provide instructions to generate flashcards with AI
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Notebook Selection */}
          <div className="space-y-2">
            <Label>Notebook</Label>
            <Select value={selectedNotebook} onValueChange={setSelectedNotebook}>
              <SelectTrigger>
                <SelectValue placeholder="Select a notebook" />
              </SelectTrigger>
              <SelectContent>
                {notebooks?.map(notebook => (
                  <SelectItem key={notebook.id} value={notebook.id}>
                    {notebook.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Source Selection */}
          {selectedNotebook && sources && sources.length > 0 && (
            <div className="space-y-2">
              <Label>Sources ({selectedSources.length} selected)</Label>
              <ScrollArea className="h-40 border rounded-md p-4">
                <div className="space-y-2">
                  {sources.map(source => (
                    <div key={source.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={source.id}
                        checked={selectedSources.includes(source.id)}
                        onCheckedChange={() => handleToggleSource(source.id)}
                      />
                      <label htmlFor={source.id} className="text-sm cursor-pointer flex-1">
                        {source.title}
                      </label>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}

          {/* Model Selection */}
          <div className="space-y-2">
            <Label>Prompt Preset</Label>
            <Select value={selectedPromptPreset} onValueChange={handleSelectPromptPreset}>
              <SelectTrigger>
                <SelectValue placeholder="Select a prompt preset" />
              </SelectTrigger>
              <SelectContent>
                {promptPresets.map((preset) => (
                  <SelectItem key={preset.key} value={preset.key}>
                    {preset.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {promptPresets.find((preset) => preset.key === selectedPromptPreset)?.description && (
              <p className="text-xs text-muted-foreground">
                {promptPresets.find((preset) => preset.key === selectedPromptPreset)?.description}
              </p>
            )}
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <Label>AI Model</Label>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="qwen2.5:3b">qwen2.5:3b (Fast, 1.9GB)</SelectItem>
                <SelectItem value="qwen2.5:7b">qwen2.5:7b (Better quality, 4.7GB - may fail on low memory)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* User Prompt */}
          <div className="space-y-2">
            <Label>Instructions</Label>
            <Textarea
              placeholder="E.g., Generate vocabulary cards for advanced Dutch learners, focusing on formal language..."
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              rows={4}
            />
          </div>

          {/* Number of Cards */}
          <div className="space-y-2">
            <Label>Number of Cards</Label>
            <Input
              type="number"
              min={1}
              max={10}
              value={numCards}
              onChange={(e) => setNumCards(parseInt(e.target.value) || 1)}
            />
          </div>

          {/* Generate Button */}
          <Button 
            onClick={handleGenerate} 
            disabled={isGenerating || selectedSources.length === 0 || !userPrompt.trim()}
            className="w-full"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate Cards'
            )}
          </Button>

          {/* Generated Cards Preview */}
          {generatedCards.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Generated Cards</h3>
                <Button onClick={handleAddAllCards} disabled={isAddingCards} size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Add All
                </Button>
              </div>
              
              <div className="space-y-4">
                {generatedCards.map((card, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div>
                      <Label className="text-xs text-muted-foreground">Front</Label>
                      <p className="mt-1">{card.front}</p>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Back</Label>
                      <p className="mt-1">{card.back}</p>
                    </div>
                    {card.notes && (
                      <div>
                        <Label className="text-xs text-muted-foreground">Notes</Label>
                        <p className="mt-1 text-sm text-muted-foreground">{card.notes}</p>
                      </div>
                    )}
                    {card.suggested_tags && card.suggested_tags.length > 0 && (
                      <div className="flex gap-2">
                        {card.suggested_tags.map((tag: string) => (
                          <Badge key={tag} variant="secondary">{tag}</Badge>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        onClick={() => handleAddCard(card, index)}
                        disabled={isAddingCards}
                      >
                        <Plus className="mr-2 h-3 w-3" />
                        Add to Deck
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost"
                        onClick={() => setGeneratedCards(prev => prev.filter((_, i) => i !== index))}
                      >
                        <X className="mr-2 h-3 w-3" />
                        Dismiss
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="rounded-lg border p-4 space-y-3">
                <h4 className="font-medium">Rate this generation</h4>
                <div className="grid grid-cols-5 gap-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <Button
                      key={rating}
                      type="button"
                      variant={qualityRating === rating ? 'default' : 'outline'}
                      onClick={() => setQualityRating(rating)}
                    >
                      {rating} · {RATING_LABELS[rating]}
                    </Button>
                  ))}
                </div>
                <Textarea
                  placeholder="What should we improve in the generated cards? (e.g., too verbose, missing examples, wrong level)"
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  This feedback is saved and reused to improve future card-generation prompts.
                </p>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleSubmitFeedback}
                  disabled={isSubmittingFeedback || qualityRating === 0}
                >
                  {isSubmittingFeedback ? 'Saving feedback...' : 'Save Feedback'}
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
