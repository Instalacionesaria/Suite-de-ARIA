import { useState, useEffect } from 'react'
import { API_URL } from '@/config'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'

const CHANNEL_TABS = [
  { key: 'email', label: 'Correo Electrónico', icon: '✉️' },
  { key: 'whatsapp', label: 'WhatsApp', icon: '💬' },
] as const

type Channel = (typeof CHANNEL_TABS)[number]['key']

interface OutreachLead {
  id: number
  name: string
  email: string
  phone: string
  source: 'maps' | 'linkedin' | 'facebook'
  location: string
}

const SOURCE_ICONS: Record<string, string> = {
  maps: '🗺️',
  linkedin: '💼',
  facebook: '📘',
}

export default function OutreachPage() {
  const [activeChannel, setActiveChannel] = useState<Channel>('email')
  const [leads, setLeads] = useState<OutreachLead[]>([])

  useEffect(() => {
    const raw = localStorage.getItem('aria_outreach_leads')
    if (raw) {
      try {
        setLeads(JSON.parse(raw))
      } catch { /* ignore */ }
    }
  }, [])

  const sourceCounts = leads.reduce<Record<string, number>>((acc, l) => {
    acc[l.source] = (acc[l.source] || 0) + 1
    return acc
  }, {})

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Outreach</h1>
        <p className="text-sm text-gray-500 mt-1">
          Envía mensajes a tus leads via <span className="font-medium text-indigo-600">LeadConnector (HighLevel)</span>.
        </p>
      </div>

      {/* Leads selected indicator */}
      <div className="mb-5 flex items-center gap-3 px-4 py-3 bg-indigo-50 border border-indigo-100 rounded-xl">
        <span className="text-indigo-600 text-lg">📋</span>
        <div className="flex-1">
          {leads.length > 0 ? (
            <>
              <p className="text-sm font-medium text-indigo-900">{leads.length} lead{leads.length !== 1 ? 's' : ''} seleccionado{leads.length !== 1 ? 's' : ''} para outreach</p>
              <p className="text-xs text-indigo-500">Selecciona más desde la página de Mis Leads</p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-indigo-900">No hay leads seleccionados</p>
              <p className="text-xs text-indigo-500">Ve a Mis Leads, selecciona los leads y haz click en "Enviar a Outreach"</p>
            </>
          )}
        </div>
        {leads.length > 0 && (
          <Badge variant="secondary" className="text-xs">
            {Object.entries(sourceCounts).map(([source, count]) => (
              <span key={source} className="mr-2">{SOURCE_ICONS[source] || ''} {count}</span>
            ))}
          </Badge>
        )}
      </div>

      {/* Channel tabs */}
      <div className="flex gap-2 mb-6">
        {CHANNEL_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveChannel(tab.key)}
            className={`relative flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer border ${
              activeChannel === tab.key
                ? 'bg-white border-gray-200 text-gray-900 shadow-sm'
                : 'bg-transparent border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/60'
            }`}
          >
            {activeChannel === tab.key && (
              <motion.div
                layoutId="outreach-tab-bg"
                className="absolute inset-0 bg-white rounded-xl border border-gray-200 shadow-sm"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative text-base">{tab.icon}</span>
            <span className="relative">{tab.label}</span>
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {activeChannel === 'email' && <EmailLCForm key="email" leads={leads} />}
        {activeChannel === 'whatsapp' && <WhatsAppForm key="whatsapp" />}
      </AnimatePresence>
    </div>
  )
}

const formAnimation = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.2 } },
}

function EmailLCForm({ leads }: { leads: OutreachLead[] }) {
  const [asunto, setAsunto] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [emailFrom, setEmailFrom] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    const raw = localStorage.getItem('aria_onboarding_data')
    if (raw) {
      try {
        const data = JSON.parse(raw)
        if (data.mensaje_outreach) setMensaje(data.mensaje_outreach)
      } catch { /* ignore */ }
    }
  }, [])

  const leadsConEmail = leads.filter((l) => l.email)

  const handleSend = async () => {
    const pitToken = localStorage.getItem('aria_hl_pit_token') || ''
    const locationId = localStorage.getItem('aria_hl_location_id') || ''

    if (!pitToken.trim() || !locationId.trim()) {
      setStatus({ type: 'error', message: 'Configura tu PIT Token y Location ID en el panel derecho de HighLevel.' })
      return
    }
    if (!asunto.trim() || !mensaje.trim()) {
      setStatus({ type: 'error', message: 'El asunto y el mensaje son obligatorios.' })
      return
    }
    if (leadsConEmail.length === 0) {
      setStatus({ type: 'error', message: 'No hay leads con email para enviar. Selecciona leads desde Mis Leads.' })
      return
    }

    setIsLoading(true)
    setStatus(null)

    try {
      const destinatarios = leadsConEmail.map((l) => ({
        email: l.email,
        nombre: l.name,
        telefono: l.phone || '',
        empresa: l.name,
      }))

      const res = await fetch(`${API_URL}/send-email-highlevel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pit_token: pitToken.trim(),
          location_id: locationId.trim(),
          asunto,
          mensaje,
          destinatarios,
          email_from: emailFrom || '',
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setStatus({ type: 'error', message: data.detail?.message || data.detail || 'Error al enviar correos.' })
      } else {
        setStatus({ type: 'success', message: data.message })
      }
    } catch {
      setStatus({ type: 'error', message: 'No se pudo conectar al servidor.' })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <motion.div {...formAnimation} className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-xl">✉️</span>
        <h2 className="text-lg font-semibold text-gray-900">Envío de Correos</h2>
        <Badge className="bg-orange-50 text-orange-600 border-orange-200 text-[10px]">LeadConnector</Badge>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3">
        <p className="text-xs text-gray-500">
          Las credenciales de HighLevel (PIT Token y Location ID) se configuran en el <strong>panel derecho</strong>.
        </p>
      </div>

      <div className="space-y-1.5">
        <Label className="text-sm text-gray-600">Remitente (opcional)</Label>
        <Input
          value={emailFrom}
          onChange={(e) => setEmailFrom(e.target.value)}
          placeholder="Ej: Juan Pérez <juan@empresa.com>"
          className="h-10"
        />
        <p className="text-[10px] text-gray-400">Si lo dejas vacío, se usará el remitente configurado en HighLevel.</p>
      </div>

      <div className="space-y-1.5">
        <Label className="text-sm text-gray-600">Asunto</Label>
        <Input
          value={asunto}
          onChange={(e) => setAsunto(e.target.value)}
          placeholder="Ej: Una propuesta para tu negocio"
          className="h-10"
        />
      </div>

      <div className="space-y-1.5">
        <Label className="text-sm text-gray-600">Mensaje</Label>
        <Textarea
          value={mensaje}
          onChange={(e) => setMensaje(e.target.value)}
          placeholder="Escribe tu mensaje aquí... El onboarding puede generarlo automáticamente."
          className="min-h-[160px] resize-y"
        />
      </div>

      {status && (
        <div className={`px-4 py-3 rounded-xl text-sm ${
          status.type === 'success'
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {status.message}
        </div>
      )}

      <div className="flex items-center gap-3">
        <Button
          onClick={handleSend}
          disabled={isLoading || leadsConEmail.length === 0}
          className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm cursor-pointer disabled:opacity-50"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Enviando...
            </span>
          ) : (
            `✉️ Enviar a ${leadsConEmail.length} lead${leadsConEmail.length !== 1 ? 's' : ''}`
          )}
        </Button>
        <p className="text-xs text-gray-400">
          Los leads se crearán como contactos en tu CRM de HighLevel automáticamente.
        </p>
      </div>
    </motion.div>
  )
}

function WhatsAppForm() {
  return (
    <motion.div {...formAnimation} className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-xl">💬</span>
        <h2 className="text-lg font-semibold text-gray-900">Enviar WhatsApps</h2>
        <Badge className="bg-green-50 text-green-600 border-green-200 text-[10px]">WhatsApp</Badge>
      </div>

      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-4xl mb-3">🚧</span>
        <p className="text-sm text-gray-500">Próximamente disponible</p>
        <p className="text-xs text-gray-400 mt-1">Estamos trabajando en la integración de WhatsApp via LeadConnector.</p>
      </div>
    </motion.div>
  )
}
