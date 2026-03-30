import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

const PENDING_LEADS = [
  { source: 'maps' as const, icon: '🗺️', label: 'Google Maps', count: 28 },
  { source: 'facebook' as const, icon: '📘', label: 'Facebook', count: 12 },
]

const TOTAL_PENDING = PENDING_LEADS.reduce((s, l) => s + l.count, 0)

export default function HighLevelPanel() {
  const [pitToken, setPitToken] = useState(() => localStorage.getItem('aria_hl_pit_token') || '')
  const [locationId, setLocationId] = useState(() => localStorage.getItem('aria_hl_location_id') || '')
  const [etiqueta, setEtiqueta] = useState(() => localStorage.getItem('aria_hl_etiqueta') || '')

  useEffect(() => { localStorage.setItem('aria_hl_pit_token', pitToken) }, [pitToken])
  useEffect(() => { localStorage.setItem('aria_hl_location_id', locationId) }, [locationId])
  useEffect(() => { localStorage.setItem('aria_hl_etiqueta', etiqueta) }, [etiqueta])

  return (
    <aside className="w-72 h-full shrink-0 bg-white border-l border-gray-200 p-5 overflow-y-auto flex flex-col gap-5">
      {/* Leads pending summary */}
      <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-3 space-y-2.5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold text-indigo-900">Leads para enviar</p>
          <span className="text-xs font-bold text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded-full">
            {TOTAL_PENDING}
          </span>
        </div>

        <div className="space-y-1.5">
          {PENDING_LEADS.map((item) => (
            <div
              key={item.source}
              className="flex items-center justify-between text-xs bg-white rounded-lg px-2.5 py-1.5 border border-indigo-100/60"
            >
              <span className="text-gray-700">
                {item.icon} {item.label}
              </span>
              <span className="font-semibold text-gray-900">{item.count}</span>
            </div>
          ))}
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
          placeholder="Ej: Leads Peluquerías Lima - Enero 2025"
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
          disabled={TOTAL_PENDING === 0}
          className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-sm cursor-pointer text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ⚡ Enviar {TOTAL_PENDING} leads a High Level
        </Button>

        <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-100">
          <span className="text-amber-500 text-sm shrink-0">⚠️</span>
          <p className="text-[10px] text-amber-600 leading-relaxed">
            Esta opción solo se habilita una vez que se termine el scrapeo de los Leads
          </p>
        </div>
      </div>
    </aside>
  )
}
