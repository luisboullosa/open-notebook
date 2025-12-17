'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { sourceChatApi } from '@/lib/api/source-chat'
import {
  SourceChatSession,
  SourceChatMessage,
  SourceChatContextIndicator,
  CreateSourceChatSessionRequest,
  UpdateSourceChatSessionRequest
} from '@/lib/types/api'
export function useSourceChat(sourceId: string) {
  const queryClient = useQueryClient()
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<SourceChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [contextIndicators, setContextIndicators] = useState<SourceChatContextIndicator | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const { data: sessions = [], isLoading: loadingSessions, refetch: refetchSessions } = useQuery<SourceChatSession[]>({
    queryKey: ['sourceChatSessions', sourceId],
    queryFn: () => sourceChatApi.listSessions(sourceId),
    enabled: !!sourceId
  })

  const { data: currentSession, refetch: refetchCurrentSession } = useQuery({
    queryKey: ['sourceChatSession', sourceId, currentSessionId],
    queryFn: () => sourceChatApi.getSession(sourceId, currentSessionId!),
    enabled: !!sourceId && !!currentSessionId
  })

  useEffect(() => {
    if (currentSession?.messages) setMessages(currentSession.messages)
  }, [currentSession])

  useEffect(() => {
    if (sessions.length > 0 && !currentSessionId) setCurrentSessionId(sessions[0].id)
  }, [sessions, currentSessionId])

  const createSessionMutation = useMutation({
    mutationFn: (data: Omit<CreateSourceChatSessionRequest, 'source_id'>) => sourceChatApi.createSession(sourceId, data),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['sourceChatSessions', sourceId] })
      setCurrentSessionId(newSession.id)
      toast.success('Chat session created')
    },
    onError: () => toast.error('Failed to create chat session')
  })

  const updateSessionMutation = useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: UpdateSourceChatSessionRequest }) =>
      sourceChatApi.updateSession(sourceId, sessionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sourceChatSessions', sourceId] })
      queryClient.invalidateQueries({ queryKey: ['sourceChatSession', sourceId, currentSessionId] })
      toast.success('Session updated')
    },
    onError: () => toast.error('Failed to update session')
  })

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => sourceChatApi.deleteSession(sourceId, sessionId),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['sourceChatSessions', sourceId] })
      if (currentSessionId === deletedId) {
        setCurrentSessionId(null)
        setMessages([])
      }
      toast.success('Session deleted')
    },
    onError: () => toast.error('Failed to delete session')
  })

  const sendMessage = useCallback(
    async (message: string, modelOverride?: string) => {
      let sessionId = currentSessionId

      if (!sessionId) {
        try {
          const defaultTitle = message.length > 30 ? `${message.substring(0, 30)}...` : message
          const newSession = await sourceChatApi.createSession(sourceId, { title: defaultTitle })
          sessionId = newSession.id
          setCurrentSessionId(sessionId)
          queryClient.invalidateQueries({ queryKey: ['sourceChatSessions', sourceId] })
        } catch (err) {
          console.error('Failed to create chat session:', err)
          toast.error('Failed to create chat session')
          return
        }
      }

      const tempId = `temp-${Date.now()}`
      const userMessage: SourceChatMessage = { id: tempId, type: 'human', content: message, timestamp: new Date().toISOString() }
      setMessages(prev => [...prev, userMessage])
      setIsStreaming(true)

      try {
        const response = await sourceChatApi.sendMessage(sourceId, sessionId, { message, model_override: modelOverride })
        if (!response) throw new Error('No response body')

        const reader = response.getReader()
        const decoder = new TextDecoder()
        let aiMessage: SourceChatMessage | null = null

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const text = decoder.decode(value)
          const lines = text.split('\n')

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'ai_message') {
                if (!aiMessage) {
                  aiMessage = { id: `ai-${Date.now()}`, type: 'ai', content: data.content || '', timestamp: new Date().toISOString() }
                  setMessages(prev => [...prev, aiMessage!])
                } else {
                  aiMessage.content += data.content || ''
                  setMessages(prev => prev.map(msg => (msg.id === aiMessage!.id ? { ...msg, content: aiMessage!.content } : msg)))
                }
              } else if (data.type === 'context_indicators') {
                setContextIndicators(data.data)
              } else if (data.type === 'error') {
                throw new Error(data.message || 'Stream error')
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      } catch (error: unknown) {
        console.error('Error sending message:', error)

        let errorMessage = 'Unknown error'
        if (typeof error === 'object' && error !== null) {
          const e = error as { response?: { data?: { detail?: string } }; message?: string }
          errorMessage = e.response?.data?.detail || e.message || errorMessage
        }

        if (errorMessage.includes('not found') && errorMessage.includes('model')) {
          const modelMatch = errorMessage.match(/model ['"]?([^'\"]+)['\"]? not found/)
          const modelName = modelMatch ? modelMatch[1] : 'required model'
          toast.error(`Model not available: ${modelName}`, { description: 'The AI model is being downloaded. Please wait a few minutes and try again.', duration: 10000 })
        } else if (errorMessage.includes('embeddings') || errorMessage.includes('mxbai-embed-large')) {
          toast.error('Embedding model not ready', { description: 'The embedding model is being downloaded. Chat will work in a few minutes.', duration: 10000 })
        } else {
          toast.error('Failed to send message', { description: errorMessage.length > 100 ? 'Check console for details' : errorMessage })
        }

        setMessages(prev => prev.filter(msg => !msg.id.startsWith('temp-')))
      } finally {
        setIsStreaming(false)
        refetchCurrentSession()
      }
    },
    [sourceId, currentSessionId, refetchCurrentSession, queryClient]
  )

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsStreaming(false)
    }
  }, [])

  const switchSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId)
    setContextIndicators(null)
  }, [])

  const createSession = useCallback((data: Omit<CreateSourceChatSessionRequest, 'source_id'>) => createSessionMutation.mutate(data), [createSessionMutation])

  const updateSession = useCallback((sessionId: string, data: UpdateSourceChatSessionRequest) => updateSessionMutation.mutate({ sessionId, data }), [updateSessionMutation])

  const deleteSession = useCallback((sessionId: string) => deleteSessionMutation.mutate(sessionId), [deleteSessionMutation])

  return {
    sessions,
    currentSession: sessions.find(s => s.id === currentSessionId),
    currentSessionId,
    messages,
    isStreaming,
    contextIndicators,
    loadingSessions,
    createSession,
    updateSession,
    deleteSession,
    switchSession,
    sendMessage,
    cancelStreaming,
    refetchSessions
  }
}
                toast.error('Embedding model not ready', { description: 'The embedding model is being downloaded. Chat will work in a few minutes.', duration: 10000 })
