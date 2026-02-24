import apiClient from './client'

// ============================================================================
// Type Definitions
// ============================================================================

export interface AnkiCard {
  id: string
  front: string
  back: string
  notes?: string
  card_type?: string
  deck_id: string
  export_session_id?: string
  source_citation?: SourceCitation
  cefr_level?: string
  cefr_confidence?: number
  cefr_votes?: CEFRVote[]
  image_metadata?: ImageMetadata
  audio_metadata?: AudioMetadata
  tags: string[]
  metadata?: Record<string, unknown>
  user_rating?: number
  study_count?: number
  created_at?: string
  updated_at?: string
}

export interface AnkiDeck {
  id: string
  name: string
  description?: string
  tags: string[]
  metadata?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface AnkiExportSession {
  id: string
  name: string
  export_format: string
  include_audio: boolean
  include_images: boolean
  status: 'draft' | 'processing' | 'completed' | 'failed'
  export_file_path?: string
  created_at?: string
  updated_at?: string
}

export interface SourceCitation {
  source_id: string
  page?: number
  context?: string
  timestamp?: string
}

export interface CEFRVote {
  model_id: string
  level: string
  confidence: number
  reasoning?: string
}

export interface ImageMetadata {
  url?: string
  source: string
  license?: string
  attribution_text?: string
  cached_path?: string
  cache_expiry?: string
}

export interface AudioMetadata {
  reference_mp3?: string
  audio_expires_at?: string
  user_recordings: string[]
  phonetic_scores: number[]
  ipa_transcriptions: string[]
}

export interface DutchWordFrequency {
  word: string
  frequency: number
  rank: number
}

// Request types
export interface CardCreateRequest {
  front: string
  back: string
  notes?: string
  deck_id: string
  tags?: string[]
  card_type?: string
}

export interface CardUpdateRequest {
  front?: string
  back?: string
  notes?: string
  tags?: string[]
  card_type?: string
}

export const CARD_TYPES = [
  { value: 'translation', label: 'Translation' },
  { value: 'fill-in-the-blank', label: 'Fill in the Blank' },
  { value: 'grammar', label: 'Grammar Focus' },
  { value: 'phrase', label: 'Phrase / Expression' },
  { value: 'visual-context', label: 'Visual Context' },
  { value: 'word-family', label: 'Word Family' },
  { value: 'conversation', label: 'Conversation' },
  { value: 'collocations', label: 'Collocations' },
  { value: 'false-friends', label: 'False Friends' },
  { value: 'synonyms', label: 'Synonyms / Register' },
  { value: 'homonyms', label: 'Homonyms / Confusables' },
] as const

export interface DeckCreateRequest {
  name: string
  description?: string
  tags?: string[]
}

export interface CEFRClassifyRequest {
  text: string
}

export interface CEFRClassifyResponse {
  level: string
  confidence: number
  votes: CEFRVote[]
}

export interface ImageSearchRequest {
  query: string
  context?: string
}

export interface ExportSessionCreateRequest {
  deck_ids: string[]
  export_format?: string
  include_audio?: boolean
  include_images?: boolean
}

export interface AudioGenerateRequest {
  text: string
  language?: string
}

export interface AudioTranscribeResponse {
  success: boolean
  transcribed_text: string
  ipa_transcription: string
  phonetic_score: number
}

// ============================================================================
// API Client
// ============================================================================

export const ankiApi = {
  // ============================================================================
  // Card Endpoints
  // ============================================================================

  cards: {
    create: async (data: CardCreateRequest) => {
      const response = await apiClient.post<AnkiCard>('/anki/cards', data)
      return response.data
    },

    get: async (cardId: string) => {
      const response = await apiClient.get<AnkiCard>(`/anki/cards/${cardId}`)
      return response.data
    },

    update: async (cardId: string, data: CardUpdateRequest) => {
      const response = await apiClient.put<AnkiCard>(`/anki/cards/${cardId}`, data)
      return response.data
    },

    delete: async (cardId: string) => {
      await apiClient.delete(`/anki/cards/${cardId}`)
    },

    listByDeck: async (deckId: string, params?: { skip?: number; limit?: number }) => {
      const response = await apiClient.get<AnkiCard[]>(`/anki/decks/${deckId}/cards`, { params })
      return response.data
    },

    rate: async (cardId: string, rating: number) => {
      const response = await apiClient.put<AnkiCard>(`/anki/cards/${cardId}/rating`, { rating })
      return response.data
    },

    recordStudy: async (cardId: string) => {
      const response = await apiClient.post<{ success: boolean; study_count: number }>(
        `/anki/cards/${cardId}/study`
      )
      return response.data
    },
  },

  // ============================================================================
  // Deck Endpoints
  // ============================================================================

  decks: {
    create: async (data: DeckCreateRequest) => {
      const response = await apiClient.post<AnkiDeck>('/anki/decks', data)
      return response.data
    },

    list: async () => {
      const response = await apiClient.get<AnkiDeck[]>('/anki/decks')
      return response.data
    },

    get: async (deckId: string) => {
      const response = await apiClient.get<AnkiDeck>(`/anki/decks/${deckId}`)
      return response.data
    },

    delete: async (deckId: string, deleteCards: boolean = false) => {
      await apiClient.delete(`/anki/decks/${deckId}`, {
        params: { delete_cards: deleteCards },
      })
    },

    exportApkg: async (deckId: string, includeAudio: boolean = true) => {
      const response = await apiClient.get(
        `/anki/decks/${encodeURIComponent(deckId)}/export`,
        { params: { include_audio: includeAudio }, responseType: 'blob' }
      )
      return response
    },
  },

  // ============================================================================
  // CEFR Classification Endpoints
  // ============================================================================

  cefr: {
    classify: async (data: CEFRClassifyRequest) => {
      const response = await apiClient.post<CEFRClassifyResponse>('/anki/cefr/classify', data)
      return response.data
    },

    setCardCEFR: async (cardId: string, text: string) => {
      const response = await apiClient.post<CEFRClassifyResponse>(
        `/anki/cards/${cardId}/cefr`,
        { text }
      )
      return response.data
    },
  },

  // ============================================================================
  // Image Endpoints
  // ============================================================================

  images: {
    search: async (data: ImageSearchRequest) => {
      const response = await apiClient.post<ImageMetadata>('/anki/images/search', data)
      return response.data
    },

    upload: async (cardId: string, file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post<{ success: boolean; image_metadata: ImageMetadata }>(
        `/anki/cards/${cardId}/image/upload`,
        formData
      )
      return response.data
    },
  },

  // ============================================================================
  // Audio Endpoints
  // ============================================================================

  audio: {
    generate: async (cardId: string, text: string, language: string = 'nl') => {
      const response = await apiClient.post<{ success: boolean; audio_metadata: AudioMetadata }>(
        `/anki/cards/${cardId}/audio/generate`,
        null,
        {
          params: { text, language },
        }
      )
      return response.data
    },

    transcribe: async (cardId: string, file: File, referenceText: string) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post<AudioTranscribeResponse>(
        `/anki/cards/${cardId}/audio/transcribe`,
        formData,
        {
          params: { reference_text: referenceText },
        }
      )
      return response.data
    },
  },

  // ============================================================================
  // Export Session Endpoints
  // ============================================================================

  exportSessions: {
    create: async (data: ExportSessionCreateRequest) => {
      const response = await apiClient.post<AnkiExportSession>('/anki/export-sessions', data)
      return response.data
    },

    get: async (sessionId: string) => {
      const response = await apiClient.get<AnkiExportSession>(`/anki/export-sessions/${sessionId}`)
      return response.data
    },
  },

  // ============================================================================
  // AI Card Generation
  // ============================================================================

  generateCards: async (deckId: string, data: {
    source_ids: string[]
    user_prompt: string
    model_id?: string
    num_cards?: number
  }) => {
    const response = await apiClient.post<{
      cards: {
        front: string
        back: string
        notes?: string
        suggested_tags: string[]
        source_references: string[]
      }[]
      model_used: string
    }>(`/anki/decks/${encodeURIComponent(deckId)}/generate-cards`, data)
    return response.data
  },

  // Get Anki card insights from transformations
  getSourceAnkiInsights: async (sourceId: string) => {
    const response = await apiClient.get<{
      source_id: string
      insights: Array<{
        insight_id: string
        insight_type: string
        created: string | null
        cards: Array<{
          front: string
          back: string
          notes?: string
          suggested_tags: string[]
        }>
        card_count: number
      }>
      total_cards: number
    }>(`/anki/sources/${encodeURIComponent(sourceId)}/anki-insights`)
    return response.data
  },

  getNotebookAnkiInsights: async (notebookId: string) => {
    const response = await apiClient.get<{
      notebook_id: string
      sources: Array<{
        source_id: string
        insights: Array<{
          insight_id: string
          insight_type: string
          created: string | null
          cards: Array<{
            front: string
            back: string
            notes?: string
            suggested_tags: string[]
          }>
          card_count: number
        }>
        card_count: number
      }>
      total_cards: number
    }>(`/anki/notebooks/${encodeURIComponent(notebookId)}/anki-insights`)
    return response.data
  },

  createCardsFromInsight: async (deckId: string, insightId: string, cardIndices?: number[]) => {
    const response = await apiClient.post<{
      success: boolean
      cards_created: number
      cards: Array<{ id: string; front: string }>
    }>(`/anki/decks/${encodeURIComponent(deckId)}/insights/${encodeURIComponent(insightId)}/create-cards`, {
      card_indices: cardIndices
    })
    return response.data
  },

  // ============================================================================
  // Config Check
  // ============================================================================

  checkConfig: async () => {
    const response = await apiClient.get<{
      ollama: {
        status: string
        models: string[]
        error: string | null
        required_installed?: string[]
        required_missing?: string[]
        recommended_installed?: string[]
        recommended_missing?: string[]
      }
      piper_tts: { status: string; error: string | null }
      whisper_stt: { status: string; error: string | null }
      image_apis: { unsplash: boolean; pexels: boolean; pixabay: boolean }
      recommended_models: {
        description: string
        required: string[]
        recommended: string[]
      }
    }>('/anki/config/check')
    return response.data
  },
}

export default ankiApi
