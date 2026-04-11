import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

const N8N_WEBHOOK_URL = 'https://n8n.ariaia.com/webhook/SubirGHL'

const SOURCE_CONFIG: Record<string, { icon: string; label: string }> = {
  maps: { icon: '🗺️', label: 'Google Maps' },
  facebook: { icon: '📘', label: 'Facebook' },
  linkedin: { icon: '💼', label: 'LinkedIn' },
}

interface StoredLead {
  source?: string
  name?: string
  email?: string
  phone?: string
  website?: string
  location?: string
  category?: string
  raw_data?: Record<string, unknown>
}

export default function HighLevelPanel() {
  const [pitToken, setPitToken] = useState(() => localStorage.getItem('aria_hl_pit_token') || '')
  const [locationId, setLocationId] = useState(() => localStorage.getItem('aria_hl_location_id') || '')
  const [etiqueta, setEtiqueta] = useState(() => localStorage.getItem('aria_hl_etiqueta') || '')

  const [sourceCounts, setSourceCounts] = useState<{ source: string; count: number }[]>([])
  const [totalPending, setTotalPending] = useState(0)
  const [isSending, setIsSending] = useState(false)
  const [sendResult, setSendResult] = useState<{ ok: boolean; msg: string } | null>(null)

  useEffect(() => {
    const update = () => {
      const raw = localStorage.getItem('aria_outreach_leads')
      if (!raw) { setSourceCounts([]); setTotalPending(0); return }
      try {
        const leads: { source?: string }[] = JSON.parse(raw)
        const counts: Record<string, number> = {}
        leads.forEach((l) => { const s = l.source || 'maps'; counts[s] = (counts[s] || 0) + 1 })
        const entries = Object.entries(counts).map(([source, count]) => ({ source, count }))
        setSourceCounts(entries)
        setTotalPending(leads.length)
      } catch { setSourceCounts([]); setTotalPending(0) }
    }
    update()
    window.addEventListener('storage', update)
    const interval = setInterval(update, 1000)
    return () => { window.removeEventListener('storage', update); clearInterval(interval) }
  }, [])

  useEffect(() => { localStorage.setItem('aria_hl_pit_token', pitToken) }, [pitToken])
  useEffect(() => { localStorage.setItem('aria_hl_location_id', locationId) }, [locationId])
  useEffect(() => { localStorage.setItem('aria_hl_etiqueta', etiqueta) }, [etiqueta])

  const handleSendToHighLevel = async () => {
    if (!pitToken.trim() || !locationId.trim()) {
      setSendResult({ ok: false, msg: 'Ingresa el API Token y Location ID.' })
      return
    }

    const raw = localStorage.getItem('aria_outreach_leads')
    if (!raw) return
    const storedLeads: StoredLead[] = JSON.parse(raw)

    // Mapear leads al formato que espera n8n/HighLevel
    const leads = storedLeads.map((l) => {
      const rd = l.raw_data || {}
      return {
        title: rd.title || l.name || null,
        categoryName: rd.categoryName || l.category || null,
        address: rd.address || l.location || null,
        street: rd.street || null,
        website: rd.website || l.website || null,
        phone: rd.phone || l.phone || null,
        phoneUnformatted: rd.phoneUnformatted || l.phone || null,
        fullName: rd.fullName || null,
        jobTitle: rd.jobTitle || null,
        email: rd.email || l.email || null,
        emails: rd.emails || null,
        linkedinProfile: rd.linkedinProfile || null,
        mobileNumber: rd.mobileNumber || null,
        companyName: rd.companyName || null,
        companyWebsite: rd.companyWebsite || null,
        companyLinkedin: rd.companyLinkedin || null,
        companyPhoneNumber: rd.companyPhoneNumber || null,
        companySize: rd.companySize || null,
        industry: rd.industry || null,
        city: rd.city || null,
        businessModel: rd.businessModel || null,
      }
    })

    setIsSending(true)
    setSendResult(null)

    try {
      const res = await fetch(N8N_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiToken: pitToken.trim(),
          etiqueta: etiqueta.trim() || 'ARIA Suite',
          locationId: locationId.trim(),
          leads,
        }),
      })

      if (res.ok) {
        setSendResult({ ok: true, msg: `${leads.length} leads enviados a High Level.` })
      } else {
        setSendResult({ ok: false, msg: `Error ${res.status}: ${res.statusText}` })
      }
    } catch (err) {
      setSendResult({ ok: false, msg: `Error de conexión: ${err}` })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <aside className="w-72 h-full shrink-0 bg-white border-l border-gray-200 p-5 overflow-y-auto flex flex-col gap-5">
      {/* Leads pending summary */}
      <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-3 space-y-2.5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold text-indigo-900">Leads para enviar</p>
          <span className="text-xs font-bold text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded-full">
            {totalPending}
          </span>
        </div>

        <div className="space-y-1.5">
          {sourceCounts.length > 0 ? sourceCounts.map((item) => {
            const cfg = SOURCE_CONFIG[item.source] || { icon: '📋', label: item.source }
            return (
              <div
                key={item.source}
                className="flex items-center justify-between text-xs bg-white rounded-lg px-2.5 py-1.5 border border-indigo-100/60"
              >
                <span className="text-gray-700">
                  {cfg.icon} {cfg.label}
                </span>
                <span className="font-semibold text-gray-900">{item.count}</span>
              </div>
            )
          }) : (
            <p className="text-[10px] text-gray-400 text-center py-1">Sin leads seleccionados</p>
          )}
        </div>

        <p className="text-[10px] text-indigo-500">
          Selecciona leads desde <span className="font-semibold">Mis Leads</span> para modificar
        </p>
      </div>

      <Separator />

      {/* API Token */}
      <div className="space-y-1.5">
        <Label className="text-sm font-semibold text-gray-900">API Token de High Level</Label>
        <p className="text-[11px] text-gray-500">Ingresa tu API token de High Level</p>
        <Input
          type="password"
          value={pitToken}
          onChange={(e) => setPitToken(e.target.value)}
          placeholder="Ingresa tu API token de High Level"
          className="h-9 text-sm border-purple-200 focus-visible:ring-purple-500/30 focus-visible:border-purple-400"
        />
        <p className="text-[10px] text-gray-400">
          Encuentra tu API token en tu cuenta de High Level → Settings → API
        </p>
      </div>

      <Separator />

      {/* Location ID */}
      <div className="space-y-1.5">
        <Label className="text-sm font-semibold text-gray-900">Location ID</Label>
        <Input
          value={locationId}
          onChange={(e) => setLocationId(e.target.value)}
          placeholder="Ingresa tu Location ID de High Level"
          className="h-9 text-sm border-purple-200 focus-visible:ring-purple-500/30 focus-visible:border-purple-400"
        />
        <p className="text-[10px] text-gray-400">
          Encuentra tu Location ID en tu cuenta de High Level → Settings → Business Profile
        </p>
      </div>

      <Separator />

      {/* Etiqueta */}
      <div className="space-y-1.5">
        <Label className="text-sm font-semibold text-gray-900">Etiqueta para High Level</Label>
        <Input
          value={etiqueta}
          onChange={(e) => setEtiqueta(e.target.value)}
          placeholder="Ej: Leads Peluquerías Lima - Enero"
          className="h-9 text-sm border-purple-200 focus-visible:ring-purple-500/30 focus-visible:border-purple-400"
        />
        <p className="text-[10px] text-gray-400">
          Esta etiqueta te ayudará a identificar y organizar tus leads en High Level (máx. 30 caracteres)
        </p>
      </div>

      <Separator />

      {/* Submit */}
      <div className="mt-auto space-y-3">
        <Button
          disabled={totalPending === 0 || isSending || !pitToken.trim() || !locationId.trim()}
          onClick={handleSendToHighLevel}
          className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-sm cursor-pointer text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSending ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Enviando...
            </span>
          ) : (
            `⚡ Enviar ${totalPending} leads a High Level`
          )}
        </Button>

        {sendResult && (
          <div className={`flex items-start gap-2 px-3 py-2 rounded-lg border ${sendResult.ok ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}`}>
            <span className={`text-sm shrink-0 ${sendResult.ok ? 'text-emerald-500' : 'text-red-500'}`}>
              {sendResult.ok ? '✅' : '❌'}
            </span>
            <p className={`text-[10px] leading-relaxed ${sendResult.ok ? 'text-emerald-600' : 'text-red-600'}`}>
              {sendResult.msg}
            </p>
          </div>
        )}

        {!sendResult && (
          <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-100">
            <span className="text-amber-500 text-sm shrink-0">⚠️</span>
            <p className="text-[10px] text-amber-600 leading-relaxed">
              Esta opción solo se habilita una vez que se termine el scrapeo de los Leads
            </p>
          </div>
        )}
      </div>
    </aside>
  )
}
