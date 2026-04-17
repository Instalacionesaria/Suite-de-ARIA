import { useState, useEffect } from 'react'
import { API_URL } from '@/config'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'

const SCRAPER_TABS = [
  { key: 'maps', label: 'Google Maps', icon: '🗺️', color: 'bg-blue-500' },
  { key: 'facebook', label: 'Facebook', icon: '📘', color: 'bg-indigo-600' },
  { key: 'linkedin', label: 'LinkedIn', icon: '💼', color: 'bg-sky-600' },
] as const

type ScraperTab = (typeof SCRAPER_TABS)[number]['key']

export default function ScraperPage() {
  const [activeTab, setActiveTab] = useState<ScraperTab>('maps')
  const hasOnboardingData = !!localStorage.getItem('aria_onboarding_data')

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Scraper</h1>
        <p className="text-sm text-gray-500 mt-1">
          Selecciona una fuente y extrae leads. Los resultados irán a{' '}
          <span className="font-medium text-indigo-600">Mis Leads</span>.
        </p>
      </div>

      {!hasOnboardingData && (
        <div className="mb-5 flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl">
          <span className="text-amber-500 text-lg mt-0.5">⚠️</span>
          <div>
            <p className="text-sm font-medium text-amber-800">No completaste el Onboarding</p>
            <p className="text-xs text-amber-600 mt-0.5">
              Puedes usar los scrapers manualmente, pero el mensaje de <strong>Outreach</strong> no se generará
              automáticamente. Ve a <strong>Onboarding</strong> para que el asistente IA configure todo por ti.
            </p>
          </div>
        </div>
      )}

      {/* Source tabs */}
      <div className="flex gap-2 mb-6">
        {SCRAPER_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`relative flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer border ${
              activeTab === tab.key
                ? 'bg-white border-gray-200 text-gray-900 shadow-sm'
                : 'bg-transparent border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/60'
            }`}
          >
            {activeTab === tab.key && (
              <motion.div
                layoutId="scraper-tab-bg"
                className="absolute inset-0 bg-white rounded-xl border border-gray-200 shadow-sm"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative text-base">{tab.icon}</span>
            <span className="relative">{tab.label}</span>
            {activeTab === tab.key && (
              <Badge variant="secondary" className="relative text-[10px] px-1.5 py-0">
                Activo
              </Badge>
            )}
          </button>
        ))}
      </div>

      {/* Scraper forms */}
      <AnimatePresence mode="wait">
        {activeTab === 'maps' && <MapsForm key="maps" />}
        {activeTab === 'linkedin' && <LinkedInForm key="linkedin" />}
        {activeTab === 'facebook' && <FacebookForm key="facebook" />}
      </AnimatePresence>
    </div>
  )
}

const formAnimation = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.2 } },
}

interface Lead {
  title?: string
  categoryName?: string
  address?: string
  phone?: string
  website?: string
  email?: string
  [key: string]: unknown
}

function MapsForm() {
  const [businessType, setBusinessType] = useState('')
  const [location, setLocation] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'polling'; message: string } | null>(null)
  const [results, setResults] = useState<Lead[]>([])

  useEffect(() => {
    const raw = localStorage.getItem('aria_onboarding_data')
    if (raw) {
      try {
        const data = JSON.parse(raw)
        if (data.tipo_negocio) setBusinessType(data.tipo_negocio)
        if (data.localizacion) setLocation(data.localizacion)
      } catch { /* ignore */ }
    }
  }, [])

  const pollJobStatus = async (jobId: string) => {
    setIsPolling(true)
    setStatus({ type: 'polling', message: 'Scrapeando leads... Esto puede tomar unos minutos.' })

    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/job/${jobId}`)
        const data = await res.json()

        if (data.status === 'COMPLETED') {
          setIsPolling(false)
          setIsLoading(false)
          const leads = data.results?.data || []
          setResults(leads)
          setStatus({ type: 'success', message: `Scraping completado. ${leads.length} leads encontrados.` })
          return
        }

        if (data.status === 'FAILED') {
          setIsPolling(false)
          setIsLoading(false)
          setStatus({ type: 'error', message: 'El scraping falló. Intenta de nuevo.' })
          return
        }

        if (data.status === 'CANCELLED') {
          setIsPolling(false)
          setIsLoading(false)
          setStatus({ type: 'error', message: 'El scraping fue cancelado.' })
          return
        }

        // Seguir haciendo polling
        setTimeout(poll, 5000)
      } catch {
        setIsPolling(false)
        setIsLoading(false)
        setStatus({ type: 'error', message: 'Error al consultar el estado del scraping.' })
      }
    }

    poll()
  }

  const handleStartScraping = async () => {
    if (!businessType.trim() || !location.trim()) {
      setStatus({ type: 'error', message: 'Completa el tipo de negocio y la localización.' })
      return
    }

    // Validar mínimo 3 partes en la localización (ej: distrito, ciudad, país)
    const locationParts = location.split(',').map((p) => p.trim()).filter(Boolean)
    if (locationParts.length < 3) {
      setStatus({
        type: 'error',
        message: 'La localización debe tener al menos 3 partes separadas por coma. Ej: "Cayma, Arequipa, Perú" (distrito, ciudad, país). Esto evita que el scraper consuma demasiados leads de zonas amplias.',
      })
      return
    }

    setIsLoading(true)
    setStatus(null)
    setResults([])

    try {
      const res = await fetch(`${API_URL}/start-scraping`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          businessType: businessType.trim(),
          location: location.trim(),
          getEmails: true,
          getBusinessModel: false,
          timestamp: new Date().toISOString(),
          userId: localStorage.getItem('aria_user_id') || '',
          correo_electronico: localStorage.getItem('aria_user_email') || '',
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setStatus({ type: 'error', message: data.detail || 'Error al iniciar el scraping.' })
        setIsLoading(false)
        return
      }

      // Iniciar polling
      pollJobStatus(data.jobId)
    } catch {
      setStatus({ type: 'error', message: 'No se pudo conectar al servidor. Verifica que el backend esté corriendo.' })
      setIsLoading(false)
    }
  }

  return (
    <motion.div {...formAnimation} className="space-y-5">
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-5">
          <span className="text-xl">🗺️</span>
          <h2 className="text-lg font-semibold text-gray-900">Google Maps</h2>
          <Badge className="bg-blue-50 text-blue-600 border-blue-200 text-[10px]">Scraper</Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div className="space-y-1.5">
            <Label htmlFor="business-type" className="text-sm text-gray-600">Tipo de Negocio</Label>
            <Input id="business-type" placeholder="Ej: Peluquería" className="h-10" value={businessType} onChange={(e) => setBusinessType(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="location" className="text-sm text-gray-600">Localización</Label>
            <Input id="location" placeholder="Ej: Cayma, Arequipa, Perú" className="h-10" value={location} onChange={(e) => setLocation(e.target.value)} />
            <p className="text-[11px] text-amber-600">
              ⚠️ Mínimo 3 partes separadas por coma (ej: distrito, ciudad, país). Evita zonas demasiado amplias.
            </p>
          </div>
        </div>


        {status && (
          <div className={`mb-4 px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${
            status.type === 'success'
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : status.type === 'polling'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {status.type === 'polling' && (
              <span className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin shrink-0" />
            )}
            {status.message}
          </div>
        )}

        <Button
          onClick={handleStartScraping}
          disabled={isLoading || isPolling}
          className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm cursor-pointer disabled:opacity-50"
        >
          {isPolling ? 'Scrapeando...' : isLoading ? 'Iniciando...' : '🚀 Iniciar Scraping'}
        </Button>
      </div>

      {/* Tabla de resultados */}
      {results.length > 0 && <LeadsTable leads={results} />}
    </motion.div>
  )
}

const COLUMN_LABELS: Record<string, string> = {
  title: 'Nombre',
  categoryName: 'Categoria',
  address: 'Direccion',
  neighborhood: 'Barrio',
  street: 'Calle',
  website: 'Sitio Web',
  phone: 'Telefono',
  phoneUnformatted: 'Tel. sin formato',
  fullName: 'Nombre Completo',
  jobTitle: 'Cargo',
  email: 'Email',
  emails: 'Emails',
  linkedinProfile: 'LinkedIn',
  mobileNumber: 'Celular',
  companyName: 'Empresa',
  companyWebsite: 'Web Empresa',
  companyLinkedin: 'LinkedIn Empresa',
  companyPhoneNumber: 'Tel. Empresa',
  companySize: 'Tamaño Empresa',
  industry: 'Industria',
  city: 'Ciudad',
  businessModel: 'Modelo de Negocio',
}

function LeadsTable({ leads }: { leads: Lead[] }) {
  // Obtener columnas que tengan al menos un valor no nulo
  const columns = Object.keys(leads[0] || {}).filter((key) =>
    leads.some((lead) => lead[key] != null && lead[key] !== '')
  )

  const renderCell = (value: unknown, key: string) => {
    if (value == null || value === '') return <span className="text-gray-300">-</span>

    const str = Array.isArray(value) ? value.join(', ') : String(value)

    // Renderizar links para URLs y emails
    if (key === 'website' || key === 'companyWebsite' || key === 'companyLinkedin' || key === 'linkedinProfile') {
      return (
        <a href={str} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline truncate block max-w-[180px]">
          {str.replace(/^https?:\/\//, '')}
        </a>
      )
    }

    if (key === 'email' || key === 'emails') {
      return <span className="text-indigo-600">{str}</span>
    }

    return <span className="truncate block max-w-[200px]">{str}</span>
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Resultados ({leads.length} leads)</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-medium text-gray-600 sticky left-0 bg-gray-50">#</th>
              {columns.map((col) => (
                <th key={col} className="text-left px-4 py-3 font-medium text-gray-600 whitespace-nowrap">
                  {COLUMN_LABELS[col] || col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {leads.map((lead, i) => (
              <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400 sticky left-0 bg-white">{i + 1}</td>
                {columns.map((col) => (
                  <td key={col} className="px-4 py-3 text-gray-600 whitespace-nowrap">
                    {renderCell(lead[col], col)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function LinkedInForm() {
  const [jobTitle, setJobTitle] = useState('')
  const [country, setCountry] = useState('')
  const [state, setState] = useState('')
  const [numberOfLeads, setNumberOfLeads] = useState(100)
  const [isLoading, setIsLoading] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'polling'; message: string } | null>(null)
  const [results, setResults] = useState<Lead[]>([])

  const pollJobStatus = async (jobId: string) => {
    setIsPolling(true)
    setStatus({ type: 'polling', message: 'Scrapeando leads de LinkedIn... Esto puede tomar varios minutos.' })

    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/job/${jobId}`)
        const data = await res.json()

        if (data.status === 'COMPLETED') {
          setIsPolling(false)
          setIsLoading(false)
          const leads = data.results?.data || []
          setResults(leads)
          setStatus({ type: 'success', message: `Scraping completado. ${leads.length} leads encontrados.` })
          return
        }
        if (data.status === 'FAILED' || data.status === 'CANCELLED') {
          setIsPolling(false)
          setIsLoading(false)
          setStatus({ type: 'error', message: `El scraping ${data.status === 'FAILED' ? 'falló' : 'fue cancelado'}.` })
          return
        }
        setTimeout(poll, 5000)
      } catch {
        setIsPolling(false)
        setIsLoading(false)
        setStatus({ type: 'error', message: 'Error al consultar el estado del scraping.' })
      }
    }
    poll()
  }

  const handleStartScraping = async () => {
    if (!jobTitle.trim() || !country.trim()) {
      setStatus({ type: 'error', message: 'Job Title y País son obligatorios.' })
      return
    }
    if (numberOfLeads < 100 || numberOfLeads > 30000) {
      setStatus({ type: 'error', message: 'Number of Leads debe estar entre 100 y 30000.' })
      return
    }

    setIsLoading(true)
    setStatus(null)
    setResults([])

    try {
      const res = await fetch(`${API_URL}/start-linkedin-scraping`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_title: jobTitle.trim(),
          country: country.trim(),
          state: state.trim(),
          number_of_leads: numberOfLeads,
          userId: localStorage.getItem('aria_user_id') || '',
          correo_electronico: localStorage.getItem('aria_user_email') || '',
          timestamp: new Date().toISOString(),
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setStatus({ type: 'error', message: data.detail || 'Error al iniciar el scraping.' })
        setIsLoading(false)
        return
      }
      pollJobStatus(data.jobId)
    } catch {
      setStatus({ type: 'error', message: 'No se pudo conectar al servidor.' })
      setIsLoading(false)
    }
  }

  return (
    <motion.div {...formAnimation} className="space-y-5">
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-5">
          <span className="text-xl">💼</span>
          <h2 className="text-lg font-semibold text-gray-900">LinkedIn (vía Apollo)</h2>
          <Badge className="bg-sky-50 text-sky-600 border-sky-200 text-[10px]">Scraper</Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div className="space-y-1.5">
            <Label htmlFor="li-job-title" className="text-sm text-gray-600">Job Title</Label>
            <Input
              id="li-job-title"
              placeholder="Ej: Real Estate Agent, CEO, Marketing Manager"
              className="h-10"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="li-country" className="text-sm text-gray-600">Country</Label>
            <Input
              id="li-country"
              placeholder="Ej: United States, Peru, Mexico"
              className="h-10"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            />
            <p className="text-[11px] text-amber-600">
              ⚠️ Es preferible escribir el nombre del país en inglés para evitar errores en la búsqueda.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
          <div className="space-y-1.5">
            <Label htmlFor="li-state" className="text-sm text-gray-600">State / Región (opcional)</Label>
            <Input
              id="li-state"
              placeholder="Ej: California, Lima, Ucayali, Madre de Dios"
              className="h-10"
              value={state}
              onChange={(e) => setState(e.target.value)}
            />
            <p className="text-[11px] text-gray-400">
              El estado puede ir en español si no tiene traducción común al inglés.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="li-number" className="text-sm text-gray-600">Number of Leads (100 - 30000)</Label>
            <Input
              id="li-number"
              type="number"
              min={100}
              max={30000}
              step={100}
              className="h-10"
              value={numberOfLeads}
              onChange={(e) => setNumberOfLeads(Number(e.target.value))}
            />
          </div>
        </div>

        {status && (
          <div className={`mb-4 px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${
            status.type === 'success'
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : status.type === 'polling'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {status.type === 'polling' && (
              <span className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin shrink-0" />
            )}
            {status.message}
          </div>
        )}

        <Button
          onClick={handleStartScraping}
          disabled={isLoading || isPolling}
          className="bg-sky-600 hover:bg-sky-700 text-white shadow-sm cursor-pointer disabled:opacity-50"
        >
          {isPolling ? 'Scrapeando...' : isLoading ? 'Iniciando...' : '💼 Scrape Leads'}
        </Button>
      </div>

      {results.length > 0 && <LeadsTable leads={results} />}
    </motion.div>
  )
}

function FacebookForm() {
  const [adsUrl, setAdsUrl] = useState('')
  const [adsLoading, setAdsLoading] = useState(false)
  const [adsPolling, setAdsPolling] = useState(false)
  const [adsStatus, setAdsStatus] = useState<{ type: 'success' | 'error' | 'polling'; message: string } | null>(null)
  const [adsResults, setAdsResults] = useState<Lead[]>([])

  const [pagesLoading, setPagesLoading] = useState(false)
  const [pagesPolling, setPagesPolling] = useState(false)
  const [pagesStatus, setPagesStatus] = useState<{ type: 'success' | 'error' | 'polling'; message: string } | null>(null)
  const [pagesResults, setPagesResults] = useState<Lead[]>([])

  const pollJob = async (
    jobId: string,
    setPolling: (v: boolean) => void,
    setLoading: (v: boolean) => void,
    setStatus: (v: { type: 'success' | 'error' | 'polling'; message: string }) => void,
    setResults: (v: Lead[]) => void,
    label: string,
  ) => {
    setPolling(true)
    setStatus({ type: 'polling', message: `Scrapeando ${label}... Esto puede tomar unos minutos.` })

    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/job/${jobId}`)
        const data = await res.json()

        if (data.status === 'COMPLETED') {
          setPolling(false)
          setLoading(false)
          const leads = data.results?.data || []
          setResults(leads)
          setStatus({ type: 'success', message: `Completado. ${leads.length} resultados encontrados.` })
          return
        }
        if (data.status === 'FAILED' || data.status === 'CANCELLED') {
          setPolling(false)
          setLoading(false)
          setStatus({ type: 'error', message: `El scraping ${data.status === 'FAILED' ? 'falló' : 'fue cancelado'}.` })
          return
        }
        setTimeout(poll, 5000)
      } catch {
        setPolling(false)
        setLoading(false)
        setStatus({ type: 'error', message: 'Error al consultar el estado del scraping.' })
      }
    }
    poll()
  }

  const handleAdsStart = async () => {
    if (!adsUrl.trim()) {
      setAdsStatus({ type: 'error', message: 'Ingresa la URL de la biblioteca de anuncios.' })
      return
    }
    setAdsLoading(true)
    setAdsStatus(null)
    setAdsResults([])

    try {
      const res = await fetch(`${API_URL}/start-facebook-ads-scraping`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: adsUrl.trim(),
          userId: localStorage.getItem('aria_user_id') || '',
          correo_electronico: localStorage.getItem('aria_user_email') || '',
          timestamp: new Date().toISOString(),
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setAdsStatus({ type: 'error', message: data.detail || 'Error al iniciar el scraping.' })
        setAdsLoading(false)
        return
      }
      pollJob(data.jobId, setAdsPolling, setAdsLoading, setAdsStatus, setAdsResults, 'Facebook Ads')
    } catch {
      setAdsStatus({ type: 'error', message: 'No se pudo conectar al servidor.' })
      setAdsLoading(false)
    }
  }

  const handlePagesStart = async () => {
    if (adsResults.length === 0) {
      setPagesStatus({ type: 'error', message: 'Primero completa el scraping de la biblioteca de anuncios.' })
      return
    }
    setPagesLoading(true)
    setPagesStatus(null)
    setPagesResults([])

    const pages = adsResults.map((ad) => ({
      page_name: (ad.page_name as string) || '',
      page_profile_uri: (ad.page_profile_uri as string) || '',
      page_id: (ad.page_id as string) || '',
    }))

    try {
      const res = await fetch(`${API_URL}/start-facebook-pages-scraping`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pages,
          userId: localStorage.getItem('aria_user_id') || '',
          correo_electronico: localStorage.getItem('aria_user_email') || '',
          timestamp: new Date().toISOString(),
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setPagesStatus({ type: 'error', message: data.detail || 'Error al iniciar el scraping.' })
        setPagesLoading(false)
        return
      }
      pollJob(data.jobId || data.job_id, setPagesPolling, setPagesLoading, setPagesStatus, setPagesResults, 'Facebook Pages')
    } catch {
      setPagesStatus({ type: 'error', message: 'No se pudo conectar al servidor.' })
      setPagesLoading(false)
    }
  }

  const StatusBanner = ({ status: s }: { status: { type: string; message: string } | null }) => {
    if (!s) return null
    return (
      <div className={`mb-4 px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${
        s.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
          : s.type === 'polling' ? 'bg-blue-50 text-blue-700 border border-blue-200'
          : 'bg-red-50 text-red-700 border border-red-200'
      }`}>
        {s.type === 'polling' && <span className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin shrink-0" />}
        {s.message}
      </div>
    )
  }

  return (
    <motion.div {...formAnimation} className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {/* Step 1: Biblioteca de Anuncios */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-base font-semibold text-gray-900">Ingresa la URL de la biblioteca de anuncios</h2>
          </div>

          <div className="space-y-1.5 mb-5 mt-3">
            <Label htmlFor="fb-ads-url" className="text-sm text-gray-600">
              URL de la biblioteca de anuncios de Facebook
            </Label>
            <Input
              id="fb-ads-url"
              placeholder="https://www.facebook.com/ads/library/..."
              className="h-10"
              value={adsUrl}
              onChange={(e) => setAdsUrl(e.target.value)}
            />
          </div>

          <StatusBanner status={adsStatus} />

          <Button
            onClick={handleAdsStart}
            disabled={adsLoading || adsPolling}
            className="bg-gray-500 hover:bg-gray-600 text-white shadow-sm cursor-pointer mt-auto w-full disabled:opacity-50"
          >
            {adsPolling ? 'Scrapeando...' : adsLoading ? 'Iniciando...' : '🔍 Iniciar scraping de esta biblioteca de anuncios'}
          </Button>
        </div>

        {/* Step 2: Scraper de Página */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-base font-semibold text-gray-900">Scraper de Pagina de Facebook</h2>
          </div>

          <div className="mt-3 mb-5 flex-1 flex items-center">
            {adsResults.length > 0 ? (
              <div className="w-full rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
                <p className="text-sm text-emerald-700 leading-relaxed">
                  {adsResults.length} paginas listas para scrapear. Haz clic para obtener datos detallados.
                </p>
              </div>
            ) : (
              <div className="w-full rounded-xl border border-blue-200 bg-blue-50 px-4 py-3">
                <p className="text-sm text-blue-700 leading-relaxed">
                  Primero completa el scraping de la biblioteca de anuncios para obtener las paginas a procesar.
                </p>
              </div>
            )}
          </div>

          <StatusBanner status={pagesStatus} />

          <Button
            onClick={handlePagesStart}
            disabled={pagesLoading || pagesPolling || adsResults.length === 0}
            className="bg-blue-500 hover:bg-blue-600 text-white shadow-sm cursor-pointer w-full disabled:opacity-50"
          >
            {pagesPolling ? 'Scrapeando...' : pagesLoading ? 'Iniciando...' : '🔍 Iniciar scraping'}
          </Button>
        </div>
      </div>

      {/* Tabla de resultados de Ads */}
      {adsResults.length > 0 && !pagesResults.length && <LeadsTable leads={adsResults} />}

      {/* Tabla de resultados de Pages (reemplaza la de Ads) */}
      {pagesResults.length > 0 && <LeadsTable leads={pagesResults} />}
    </motion.div>
  )
}
