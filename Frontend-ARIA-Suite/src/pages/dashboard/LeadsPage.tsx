import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_URL } from '@/config'
import { motion } from 'framer-motion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'

type LeadSource = 'all' | 'maps' | 'linkedin' | 'facebook'

interface Lead {
  id: string
  name: string
  email: string
  phone: string
  source: 'maps' | 'linkedin' | 'facebook'
  location: string
  category?: string
  website?: string
  raw_data?: Record<string, unknown>
  created_at: string
}

const SOURCE_CONFIG = {
  maps: { label: 'Maps', icon: '🗺️', badgeClass: 'bg-blue-50 text-blue-600 border-blue-200' },
  linkedin: { label: 'LinkedIn', icon: '💼', badgeClass: 'bg-sky-50 text-sky-600 border-sky-200' },
  facebook: { label: 'Facebook', icon: '📘', badgeClass: 'bg-indigo-50 text-indigo-600 border-indigo-200' },
}

const FILTER_TABS: { key: LeadSource; label: string }[] = [
  { key: 'all', label: 'Todos' },
  { key: 'maps', label: '🗺️ Maps' },
  { key: 'linkedin', label: '💼 LinkedIn' },
  { key: 'facebook', label: '📘 Facebook' },
]

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return iso
  }
}

function downloadCSV(leads: Lead[]) {
  if (leads.length === 0) return
  const headers = ['Nombre', 'Email', 'Teléfono', 'Fuente', 'Ubicación', 'Fecha']
  const escape = (v: string) => `"${(v || '').replace(/"/g, '""')}"`
  const rows = leads.map((l) => [
    escape(l.name),
    escape(l.email),
    escape(l.phone),
    escape(l.source),
    escape(l.location),
    escape(formatDate(l.created_at)),
  ].join(','))
  const csv = [headers.join(','), ...rows].join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `leads_aria_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function LeadsPage() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState<LeadSource>('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const email = localStorage.getItem('aria_user_email')
    if (!email) {
      setLoading(false)
      setError('Inicia sesión para ver tus leads.')
      return
    }

    fetch(`${API_URL}/mis-leads?email=${encodeURIComponent(email)}`)
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(data.detail || 'Error al cargar leads.')
        }
        return res.json()
      })
      .then((data: Lead[]) => {
        setLeads(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const filtered = leads.filter((lead) => {
    const matchesSource = filter === 'all' || lead.source === filter
    const matchesSearch =
      search === '' ||
      lead.name.toLowerCase().includes(search.toLowerCase()) ||
      lead.email.toLowerCase().includes(search.toLowerCase())
    return matchesSource && matchesSearch
  })

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (selected.size === filtered.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(filtered.map((l) => l.id)))
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mis Leads</h1>
          <p className="text-sm text-gray-500 mt-1">
            Todos tus leads en un solo lugar. Selecciona y envía a{' '}
            <span className="font-medium text-indigo-600">Outreach</span>.
          </p>
        </div>
        {selected.size > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2"
          >
            <Badge variant="secondary" className="text-sm">
              {selected.size} seleccionado{selected.size > 1 ? 's' : ''}
            </Badge>
            <Button
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer"
              onClick={() => {
                const leadsParaOutreach = leads.filter((l) => selected.has(l.id))
                localStorage.setItem('aria_outreach_leads', JSON.stringify(leadsParaOutreach))
                navigate('/dashboard/outreach')
              }}
            >
              📨 Enviar a Outreach
            </Button>
          </motion.div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="flex gap-1.5">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer border ${
                filter === tab.key
                  ? 'bg-white border-gray-200 text-gray-900 shadow-sm'
                  : 'bg-transparent border-transparent text-gray-500 hover:bg-white/80 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <Input
          placeholder="Buscar por nombre o email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 text-sm max-w-xs"
        />
        <Button
          size="sm"
          variant="outline"
          disabled={filtered.length === 0}
          onClick={() => downloadCSV(filtered)}
          className="h-8 text-xs cursor-pointer gap-1.5 ml-auto"
        >
          Descargar CSV
        </Button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-400">
            <span className="w-5 h-5 border-2 border-gray-300 border-t-transparent rounded-full animate-spin inline-block mb-2" />
            <p className="text-sm">Cargando leads...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center text-red-500 text-sm">{error}</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/50">
                <th className="text-left p-3 w-10">
                  <Checkbox
                    checked={selected.size === filtered.length && filtered.length > 0}
                    onCheckedChange={toggleAll}
                  />
                </th>
                <th className="text-left p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Nombre</th>
                <th className="text-left p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                <th className="text-left p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">Teléfono</th>
                <th className="text-left p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Fuente</th>
                <th className="text-left p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">Ubicación</th>
                <th className="text-left p-3 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((lead) => {
                const src = SOURCE_CONFIG[lead.source] || SOURCE_CONFIG.maps
                return (
                  <motion.tr
                    key={lead.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className={`border-b border-gray-50 transition-colors duration-150 ${
                      selected.has(lead.id) ? 'bg-indigo-50/50' : 'hover:bg-gray-50'
                    }`}
                  >
                    <td className="p-3">
                      <Checkbox
                        checked={selected.has(lead.id)}
                        onCheckedChange={() => toggleSelect(lead.id)}
                      />
                    </td>
                    <td className="p-3 font-medium text-gray-900">{lead.name}</td>
                    <td className="p-3 text-gray-600">{lead.email}</td>
                    <td className="p-3 text-gray-600 hidden md:table-cell">{lead.phone}</td>
                    <td className="p-3">
                      <Badge className={`${src.badgeClass} text-[10px]`}>
                        {src.icon} {src.label}
                      </Badge>
                    </td>
                    <td className="p-3 text-gray-500 hidden lg:table-cell">{lead.location}</td>
                    <td className="p-3 text-gray-400 text-xs hidden lg:table-cell">{formatDate(lead.created_at)}</td>
                  </motion.tr>
                )
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-12 text-center text-gray-400">
                    {leads.length === 0
                      ? 'Aún no tienes leads. Ejecuta un scraper para comenzar.'
                      : 'No se encontraron leads con ese filtro.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
