import { useState } from 'react'
import { motion } from 'framer-motion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'

type LeadSource = 'all' | 'maps' | 'linkedin' | 'facebook'

interface Lead {
  id: number
  name: string
  email: string
  phone: string
  source: 'maps' | 'linkedin' | 'facebook'
  location: string
  date: string
}

const DEMO_LEADS: Lead[] = [
  { id: 1, name: 'Peluquería Glamour', email: 'contacto@glamour.com', phone: '+51 999 111 222', source: 'maps', location: 'Miraflores, Lima', date: '15 Mar 2026' },
  { id: 2, name: 'Carlos Rodríguez', email: 'carlos@techcorp.io', phone: '+51 998 333 444', source: 'linkedin', location: 'San Isidro, Lima', date: '15 Mar 2026' },
  { id: 3, name: 'Gym PowerFit', email: 'info@powerfit.pe', phone: '+51 997 555 666', source: 'facebook', location: 'Surco, Lima', date: '14 Mar 2026' },
  { id: 4, name: 'Clínica Dental Sonrisa', email: 'admin@sonrisa.com', phone: '+51 996 777 888', source: 'maps', location: 'Barranco, Lima', date: '14 Mar 2026' },
  { id: 5, name: 'Ana López - CEO', email: 'ana@startupxyz.com', phone: '+51 995 999 000', source: 'linkedin', location: 'Lima, Perú', date: '13 Mar 2026' },
  { id: 6, name: 'Restaurante El Sabor', email: 'reservas@elsabor.pe', phone: '+51 994 111 333', source: 'facebook', location: 'Magdalena, Lima', date: '13 Mar 2026' },
]

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

export default function LeadsPage() {
  const [filter, setFilter] = useState<LeadSource>('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Set<number>>(new Set())

  const filtered = DEMO_LEADS.filter((lead) => {
    const matchesSource = filter === 'all' || lead.source === filter
    const matchesSearch =
      search === '' ||
      lead.name.toLowerCase().includes(search.toLowerCase()) ||
      lead.email.toLowerCase().includes(search.toLowerCase())
    return matchesSource && matchesSearch
  })

  const toggleSelect = (id: number) => {
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
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer">
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
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
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
              const src = SOURCE_CONFIG[lead.source]
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
                  <td className="p-3 text-gray-400 text-xs hidden lg:table-cell">{lead.date}</td>
                </motion.tr>
              )
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="p-12 text-center text-gray-400">
                  No se encontraron leads con ese filtro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
