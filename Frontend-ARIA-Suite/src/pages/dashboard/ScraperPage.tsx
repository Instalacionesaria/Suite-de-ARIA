import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'

const SCRAPER_TABS = [
  { key: 'maps', label: 'Google Maps', icon: '🗺️', color: 'bg-blue-500' },
  { key: 'linkedin', label: 'LinkedIn', icon: '💼', color: 'bg-sky-600' },
  { key: 'facebook', label: 'Facebook', icon: '📘', color: 'bg-indigo-600' },
] as const

type ScraperTab = (typeof SCRAPER_TABS)[number]['key']

export default function ScraperPage() {
  const [activeTab, setActiveTab] = useState<ScraperTab>('maps')

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Scraper</h1>
        <p className="text-sm text-gray-500 mt-1">
          Selecciona una fuente y extrae leads. Los resultados irán a{' '}
          <span className="font-medium text-indigo-600">Mis Leads</span>.
        </p>
      </div>

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

function MapsForm() {
  const [enrichPremium, setEnrichPremium] = useState(false)

  return (
    <motion.div {...formAnimation} className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-xl">🗺️</span>
        <h2 className="text-lg font-semibold text-gray-900">Google Maps</h2>
        <Badge className="bg-blue-50 text-blue-600 border-blue-200 text-[10px]">Scraper</Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div className="space-y-1.5">
          <Label htmlFor="business-type" className="text-sm text-gray-600">Tipo de Negocio</Label>
          <Input id="business-type" placeholder="Ej: Peluquería" className="h-10" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="location" className="text-sm text-gray-600">Localización</Label>
          <Input id="location" placeholder="Ej: Miraflores, Lima" className="h-10" />
        </div>
      </div>

      <div className="flex items-center gap-2 mb-5">
        <Checkbox
          id="enrich"
          checked={enrichPremium}
          onCheckedChange={(v) => setEnrichPremium(v === true)}
        />
        <Label htmlFor="enrich" className="text-sm text-gray-600 cursor-pointer">
          Enriquecer con Datos Premium (Ejm: Emails, Perfil LinkedIn, etc)
        </Label>
      </div>

      <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm cursor-pointer">
        🚀 Iniciar Scraping
      </Button>
    </motion.div>
  )
}

function LinkedInForm() {
  return (
    <motion.div {...formAnimation} className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-xl">💼</span>
        <h2 className="text-lg font-semibold text-gray-900">LinkedIn</h2>
        <Badge className="bg-sky-50 text-sky-600 border-sky-200 text-[10px]">Scraper</Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div className="space-y-1.5">
          <Label htmlFor="li-keyword" className="text-sm text-gray-600">Palabra clave / Cargo</Label>
          <Input id="li-keyword" placeholder="Ej: CEO, Marketing Manager" className="h-10" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="li-location" className="text-sm text-gray-600">Ubicación</Label>
          <Input id="li-location" placeholder="Ej: Lima, Perú" className="h-10" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
        <div className="space-y-1.5">
          <Label htmlFor="li-industry" className="text-sm text-gray-600">Industria</Label>
          <Input id="li-industry" placeholder="Ej: Tecnología" className="h-10" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="li-company" className="text-sm text-gray-600">Empresa (opcional)</Label>
          <Input id="li-company" placeholder="Ej: Google, Meta" className="h-10" />
        </div>
      </div>

      <Button className="bg-sky-600 hover:bg-sky-700 text-white shadow-sm cursor-pointer">
        💼 Buscar en LinkedIn
      </Button>
    </motion.div>
  )
}

function FacebookForm() {
  return (
    <motion.div {...formAnimation} className="grid grid-cols-1 sm:grid-cols-2 gap-5">
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
          />
        </div>

        <Button className="bg-gray-500 hover:bg-gray-600 text-white shadow-sm cursor-pointer mt-auto w-full">
          🔍 Iniciar scraping de esta biblioteca de anuncios
        </Button>
      </div>

      {/* Step 2: Scraper de Página */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col">
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-base font-semibold text-gray-900">Scraper de Página de Facebook</h2>
        </div>

        <div className="mt-3 mb-5 flex-1 flex items-center">
          <div className="w-full rounded-xl border border-blue-200 bg-blue-50 px-4 py-3">
            <p className="text-sm text-blue-700 leading-relaxed">
              Primero completa el scraping de la biblioteca de anuncios para obtener las páginas a procesar.
            </p>
          </div>
        </div>

        <Button className="bg-blue-500 hover:bg-blue-600 text-white shadow-sm cursor-pointer w-full">
          🔍 Iniciar scraping
        </Button>
      </div>
    </motion.div>
  )
}
