'use client'
import { useEffect, useRef, useState, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Send, Plus, Trash2, Zap, User, Paperclip,
  MessageSquare, ChevronRight, Loader2, Copy, Check
} from 'lucide-react'
import toast from 'react-hot-toast'
import { AppShell } from '@/components/layout/AppShell'
import { chatApi } from '@/lib/api'
import { useChatStore, useAuthStore } from '@/store'
import { formatRelativeTime, SUGGESTED_PROMPTS, cn } from '@/lib/utils'
import type { ChatMessage } from '@/types'

function TypingIndicator() {
  return (
    <div className="flex gap-3 items-start animate-fade-in">
      <div className="w-8 h-8 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
        <Zap className="w-4 h-4 text-brand-400" />
      </div>
      <div className="chat-message-ai rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1 items-center h-5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage & { isStreaming?: boolean; streamContent?: string } }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'
  const content = message.isStreaming ? message.streamContent || '' : message.content

  const copyContent = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('flex gap-3 items-start', isUser && 'flex-row-reverse')}
    >
      <div className={cn(
        'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
        isUser
          ? 'bg-brand-500/20 border border-brand-500/30'
          : 'bg-brand-500/10 border border-brand-500/20'
      )}>
        {isUser
          ? <User className="w-4 h-4 text-brand-400" />
          : <Zap className="w-4 h-4 text-brand-400" />
        }
      </div>

      <div className={cn(
        'group relative max-w-2xl rounded-2xl px-4 py-3',
        isUser
          ? 'chat-message-user rounded-tr-sm'
          : 'chat-message-ai rounded-tl-sm'
      )}>
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        ) : (
          <div className="prose-chat text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            {message.isStreaming && (
              <span className="inline-block w-0.5 h-4 bg-brand-400 ml-0.5 animate-pulse" />
            )}
          </div>
        )}
        {!message.isStreaming && (
          <button
            onClick={copyContent}
            className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-background border border-white/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          >
            {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3 text-muted-foreground" />}
          </button>
        )}
        <div className={cn(
          'text-[10px] text-muted-foreground mt-1',
          isUser ? 'text-right' : ''
        )}>
          {formatRelativeTime(message.created_at)}
          {message.rag_context_used && (
            <span className="ml-2 text-brand-400/60">· knowledge base</span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default function ChatPage() {
  const searchParams = useSearchParams()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const {
    sessions, setSessions, activeSessionId, setActiveSession,
    messages, setMessages, addMessage, isStreaming, streamingContent,
    setStreaming, clearStreaming, appendStreamChunk, removeSession,
    addSession, updateSessionTitle,
  } = useChatStore()
  const { user } = useAuthStore()

  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(sessions.length === 0)
  // Mutable ref always holds the latest streamed content — fixes stale closure
  const streamRef = useRef('')

  // Keep ref in sync with Zustand store
  useEffect(() => { streamRef.current = streamingContent }, [streamingContent])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, streamingContent])

  // Load sessions on mount
  useEffect(() => {
    if (!user) return
    chatApi.listSessions()
      .then(setSessions)
      .catch(console.error)
      .finally(() => setLoadingSessions(false))
  }, [user, setSessions])

  // Handle initial query from URL params
  useEffect(() => {
    const q = searchParams.get('q')
    if (q) {
      setInput(q)
      setTimeout(() => handleSend(q), 800)
    }
  }, [])

  // Load messages when session changes
  useEffect(() => {
    if (!activeSessionId) return
    chatApi.getMessages(activeSessionId)
      .then(setMessages)
      .catch(console.error)
  }, [activeSessionId])

  const handleSend = async (overrideContent?: string) => {
    const content = overrideContent || input.trim()
    if (!content || isStreaming || isLoading) return

    setInput('')
    setIsLoading(true)

    const tempId = `temp-${Date.now()}`
    const userMsg: ChatMessage = {
      id: tempId,
      session_id: activeSessionId || '',
      role: 'user',
      content,
      rag_context_used: false,
      created_at: new Date().toISOString(),
    }
    addMessage(userMsg)
    setStreaming(true)
    
    // Accumulate streamed content locally in a closure to avoid React async scheduler race conditions
    let accumulatedContent = ''
    streamRef.current = ''

    let currentSessionId = activeSessionId

    await chatApi.streamChat(
      content,
      currentSessionId,
      [],
      (chunk) => {
        accumulatedContent += chunk
        appendStreamChunk(chunk)
      },
      (newSessionId) => {
        currentSessionId = newSessionId
        setActiveSession(newSessionId)
        if (!activeSessionId) {
          addSession({
            id: newSessionId,
            title: 'New Chat',
            message_count: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        }
      },
      (sessionId) => {
        const aiMsg: ChatMessage = {
          id: `ai-${Date.now()}`,
          session_id: sessionId,
          role: 'assistant',
          content: accumulatedContent,
          rag_context_used: false,
          created_at: new Date().toISOString(),
        }
        clearStreaming()
        streamRef.current = ''
        addMessage(aiMsg)
        setIsLoading(false)
        chatApi.listSessions().then(setSessions).catch(console.error)
      },
      (err) => {
        toast.error(err || 'AI error. Please try again.')
        clearStreaming()
        streamRef.current = ''
        setIsLoading(false)
      }
    )
    setIsLoading(false)
  }

  const handleNewChat = () => {
    setActiveSession(null)
    setMessages([])
    clearStreaming()
    streamRef.current = ''
    inputRef.current?.focus()
  }

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    await chatApi.deleteSession(id)
    removeSession(id)
    if (activeSessionId === id) handleNewChat()
    toast.success('Chat deleted')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <AppShell>
      <div className="flex h-screen">
        {/* Sessions sidebar */}
        <div className="w-64 border-r border-white/5 flex flex-col bg-background/50">
          <div className="p-4 border-b border-white/5">
            <button
              onClick={handleNewChat}
              className="w-full flex items-center gap-2 bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/20 text-brand-400 px-3 py-2 rounded-lg text-sm font-medium transition-all"
            >
              <Plus className="w-4 h-4" />
              New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {loadingSessions ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="skeleton h-12 rounded-lg" />
                ))}
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-30" />
                No chats yet
              </div>
            ) : (
              <div className="space-y-1">
                {sessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => setActiveSession(session.id)}
                    className={cn(
                      'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all group flex items-center justify-between',
                      activeSessionId === session.id
                        ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                        : 'hover:bg-white/5 text-muted-foreground hover:text-foreground'
                    )}
                  >
                    <span className="truncate flex-1">{session.title}</span>
                    <button
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-400 transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            {!activeSessionId && messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto">
                <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
                  <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mx-auto mb-6">
                    <Zap className="w-8 h-8 text-brand-400" />
                  </div>
                  <h2 className="font-display font-bold text-2xl text-center mb-2">Ask Maffa anything</h2>
                  <p className="text-muted-foreground text-center mb-8 text-sm">
                    Your intelligent AI Tax Assistant powered by the premium Maffa Core optimization engine
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {SUGGESTED_PROMPTS.slice(0, 6).map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => handleSend(prompt)}
                        className="glass p-3 rounded-xl text-left text-sm hover:bg-white/[0.06] transition-all group"
                      >
                        <ChevronRight className="w-3.5 h-3.5 text-brand-400 mb-1.5" />
                        <span className="text-muted-foreground group-hover:text-foreground transition-colors leading-relaxed">
                          {prompt}
                        </span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              </div>
            ) : (
              <div className="max-w-3xl mx-auto space-y-6">
                <AnimatePresence initial={false}>
                  {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                  ))}
                  {isStreaming && streamingContent && (
                    <motion.div key="streaming" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3 items-start">
                      <div className="w-8 h-8 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
                        <Zap className="w-4 h-4 text-brand-400" />
                      </div>
                      <div className="chat-message-ai rounded-2xl rounded-tl-sm px-4 py-3 max-w-2xl">
                        <div className="prose-chat text-sm">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
                          <span className="inline-block w-0.5 h-4 bg-brand-400 ml-0.5 animate-pulse" />
                        </div>
                      </div>
                    </motion.div>
                  )}
                  {isStreaming && !streamingContent && <TypingIndicator key="typing" />}
                </AnimatePresence>
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
 
          {/* Input area */}
          <div className="p-4 border-t border-white/5">
            <div className="max-w-3xl mx-auto">
              <div className="glass-strong rounded-2xl border border-white/10 p-3 flex items-end gap-3 focus-within:border-brand-500/40 transition-all">
                <button className="p-2 rounded-lg hover:bg-white/10 text-muted-foreground hover:text-foreground transition-all flex-shrink-0">
                  <Paperclip className="w-4 h-4" />
                </button>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about taxes, deductions, regimes..."
                  rows={1}
                  className="flex-1 bg-transparent text-sm resize-none outline-none placeholder:text-muted-foreground max-h-32 overflow-y-auto"
                  style={{ minHeight: '24px' }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement
                    target.style.height = 'auto'
                    target.style.height = target.scrollHeight + 'px'
                  }}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || isStreaming}
                  className="p-2 rounded-lg bg-brand-500 hover:bg-brand-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex-shrink-0"
                >
                  {isStreaming ? (
                    <Loader2 className="w-4 h-4 text-white animate-spin" />
                  ) : (
                    <Send className="w-4 h-4 text-white" />
                  )}
                </button>
              </div>
              <p className="text-[11px] text-muted-foreground text-center mt-2">
                Maffa is powered by the Maffa Core optimization engine. For complex matters, consult a Chartered Accountant.
              </p>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
