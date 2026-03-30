import { useState, useRef, useEffect } from 'react'
import { API_URL } from '@/config'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

const AVAILABLE_MODELS = [
  { value: 'gpt-4.1', label: 'GPT-4.1' },
  { value: 'gpt-5.1', label: 'GPT-5.1' },
  { value: 'gpt-5.2', label: 'GPT-5.2' },
]

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content:
    '¡Hola! 👋 Soy el asistente de onboarding de ARIA Suite. Voy a ayudarte a configurar tu cuenta conociendo un poco sobre tu negocio.\n\nCuéntame, ¿a qué se dedica tu negocio?',
  timestamp: new Date(),
}

const QUICK_ACTIONS = [
  'Tengo una peluquería',
  'Soy dueño de un restaurante',
  'Tengo una agencia de marketing',
  'Vendo productos online',
]

export default function OnboardingPage() {
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem('aria_onboarding_messages')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        return parsed.map((m: Message) => ({ ...m, timestamp: new Date(m.timestamp) }))
      } catch { /* ignore */ }
    }
    return [WELCOME_MESSAGE]
  })
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('aria_openai_api_key') || '')
  const [model, setModel] = useState(() => localStorage.getItem('aria_openai_model') || 'gpt-4.1')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    localStorage.setItem('aria_onboarding_messages', JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    localStorage.setItem('aria_openai_api_key', apiKey)
  }, [apiKey])

  useEffect(() => {
    localStorage.setItem('aria_openai_model', model)
  }, [model])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setInput('')
    setIsLoading(true)

    try {
      // Construir historial sin el welcome message ni el mensaje actual
      const history = updatedMessages
        .filter((m) => m.id !== 'welcome')
        .slice(0, -1) // excluir el mensaje actual (va en "message")
        .map((m) => ({ role: m.role, content: m.content }))

      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content.trim(),
          history,
          model: model || undefined,
          api_key: apiKey || undefined,
        }),
      })

      const data = await res.json()

      // Si el agente extrajo datos, guardarlos en localStorage
      if (data.extracted_data) {
        const existing = JSON.parse(localStorage.getItem('aria_onboarding_data') || '{}')
        const merged = { ...existing, ...data.extracted_data }
        localStorage.setItem('aria_onboarding_data', JSON.stringify(merged))
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'No pude conectarme al servidor. Verifica que el backend esté corriendo.',
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const showApiKeyModal = !apiKey

  return (
    <div className="flex flex-col h-screen">
      {/* Modal API Key */}
      <AnimatePresence>
        {showApiKeyModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 max-w-md w-full mx-4"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                  <span className="text-white text-lg">🔑</span>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">API Key requerida</h2>
                  <p className="text-xs text-gray-500">Para usar el asistente de onboarding</p>
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-4">
                El asistente de onboarding usa inteligencia artificial para configurar tu cuenta automáticamente.
                Necesitas una <strong>API Key de OpenAI</strong> para activarlo.
              </p>

              <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-5">
                <p className="text-xs text-amber-700">
                  <strong>Sin onboarding</strong> puedes usar los scrapers normalmente, pero el mensaje de
                  Outreach no se generará automáticamente y tendrás que escribirlo manualmente.
                </p>
              </div>

              <div className="space-y-3">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-gray-700">OpenAI API Key</label>
                  <Input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="h-10"
                  />
                  <p className="text-[10px] text-gray-400">
                    Consíguela en platform.openai.com/api-keys. El costo de tokens corre por tu cuenta.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-gray-700">Modelo</label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full h-10 px-3 text-sm border border-gray-200 rounded-md bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {AVAILABLE_MODELS.map((m) => (
                      <option key={m.value} value={m.value}>
                        {m.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <Button
                onClick={() => {}}
                disabled={!apiKey}
                className="w-full mt-5 h-11 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white shadow-sm disabled:opacity-50 cursor-pointer"
              >
                Activar Onboarding
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="shrink-0 border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center shadow-sm">
            <span className="text-white text-sm">🤖</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Onboarding</h1>
            <p className="text-xs text-gray-500">Asistente IA para configurar tu cuenta</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="OpenAI API Key"
              className="h-8 w-48 text-xs"
            />
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="h-8 px-2 text-xs border border-gray-200 rounded-md bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {AVAILABLE_MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-100">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-medium text-emerald-600">En línea</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4 bg-gray-50/50">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex gap-2.5 max-w-[75%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-sm shadow-sm ${
                    msg.role === 'assistant'
                      ? 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {msg.role === 'assistant' ? '🤖' : '👤'}
                </div>

                {/* Bubble */}
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === 'assistant'
                      ? 'bg-white border border-gray-200 text-gray-800 shadow-sm'
                      : 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md'
                  }`}
                >
                  {msg.content.split('\n').map((line, i) => (
                    <p key={i} className={i > 0 ? 'mt-2' : ''}>
                      {line}
                    </p>
                  ))}
                  <p
                    className={`text-[10px] mt-2 ${
                      msg.role === 'assistant' ? 'text-gray-400' : 'text-white/60'
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2.5"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-sm shadow-sm">
              🤖
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick actions */}
      {messages.length <= 1 && (
        <div className="shrink-0 px-6 py-3 bg-white border-t border-gray-100">
          <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wider mb-2">
            Preguntas sugeridas
          </p>
          <div className="flex flex-wrap gap-2">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action}
                onClick={() => sendMessage(action)}
                className="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-600 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-600 transition-all duration-200 cursor-pointer"
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-t border-gray-200 bg-white px-6 py-4"
      >
        <div className="flex gap-3 items-end">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu mensaje..."
            className="min-h-[44px] max-h-[120px] resize-none text-sm flex-1"
            rows={1}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="h-11 px-5 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white shadow-sm disabled:opacity-50 cursor-pointer shrink-0"
          >
            Enviar
          </Button>
        </div>
        <p className="text-[10px] text-gray-400 mt-2">
          Presiona Enter para enviar, Shift+Enter para nueva línea
        </p>
      </form>
    </div>
  )
}
