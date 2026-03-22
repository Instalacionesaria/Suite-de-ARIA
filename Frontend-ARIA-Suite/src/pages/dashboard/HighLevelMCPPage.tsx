import { useState, useRef, useEffect } from 'react'
import { API_URL } from '@/config'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function HighLevelMCPPage() {
  const [pitToken, setPitToken] = useState('')
  const [locationId, setLocationId] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return
    if (!pitToken.trim() || !locationId.trim()) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const res = await fetch(`${API_URL}/highlevel-mcp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pit_token: pitToken,
          location_id: locationId,
          orden: content.trim(),
        }),
      })

      const data = await res.json()

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.respuesta || data.detail || 'Sin respuesta del agente.',
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'No pude conectarme al servidor. Verifica que el backend este corriendo.',
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

  const credentialsReady = pitToken.trim() && locationId.trim()

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="shrink-0 border-b border-gray-200 bg-white px-6 py-4">
        <h1 className="text-lg font-bold text-gray-900">Acceso a MCP High Level</h1>
      </div>

      {/* Credentials Section */}
      <div className="shrink-0 px-6 py-5 bg-white border-b border-gray-200">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: Credentials */}
          <div className="border border-gray-200 rounded-xl p-5 space-y-4">
            <h2 className="text-base font-semibold text-gray-900">Conectar con Credenciales</h2>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700">Token de la Cuenta</label>
              <Input
                value={pitToken}
                onChange={(e) => setPitToken(e.target.value)}
                placeholder="Ingresa tu token de High Level"
                className="text-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700">Location ID</label>
              <Input
                value={locationId}
                onChange={(e) => setLocationId(e.target.value)}
                placeholder="Ingresa tu Location ID"
                className="text-sm"
              />
            </div>
          </div>

          {/* Right: Direct Connection (coming soon) */}
          <div className="border border-gray-200 rounded-xl p-5 flex flex-col items-center justify-center text-center space-y-3">
            <h2 className="text-base font-semibold text-gray-900">Conexion Directa</h2>
            <Button
              disabled
              className="bg-gray-300 text-gray-500 cursor-not-allowed hover:bg-gray-300"
            >
              Conectar con HighLevel
            </Button>
            <p className="text-sm text-gray-400">Esta opcion sera habilitada pronto</p>
          </div>
        </div>
      </div>

      {/* Chat Section */}
      <div className="shrink-0 px-6 pt-5 pb-2">
        <h2 className="text-base font-semibold text-gray-900">Chat con Agente MCP de HighLevel</h2>
        <p className="text-sm text-gray-500">Conversa con el agente IA para ejecutar acciones en tu cuenta</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-3 bg-gray-50/50 border border-gray-200 mx-6 rounded-xl">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-gray-400">Escribe tu primera orden o consulta para comenzar</p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex mb-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex gap-2.5 max-w-[75%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div
                  className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-sm shadow-sm ${
                    msg.role === 'assistant'
                      ? 'bg-gradient-to-br from-indigo-500 to-purple-500 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {msg.role === 'assistant' ? '🤖' : '👤'}
                </div>
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

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2.5 mb-3"
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

      {/* Input */}
      <form onSubmit={handleSubmit} className="shrink-0 px-6 py-4">
        <div className="flex gap-3 items-end">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              credentialsReady
                ? "Escribe tu orden... Ej: 'Crear un contacto con nombre Juan Perez' o 'Listar oportunidades abiertas'"
                : 'Ingresa tus credenciales arriba para comenzar'
            }
            disabled={!credentialsReady}
            className="min-h-[44px] max-h-[120px] resize-none text-sm flex-1"
            rows={1}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading || !credentialsReady}
            className="h-11 px-5 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white shadow-sm disabled:opacity-50 cursor-pointer shrink-0"
          >
            Enviar
          </Button>
        </div>
      </form>
    </div>
  )
}
