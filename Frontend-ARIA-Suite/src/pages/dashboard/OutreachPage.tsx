import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'

const CHANNEL_TABS = [
  { key: 'email', label: 'Correo Electrónico', icon: '✉️', color: 'bg-emerald-600' },
  { key: 'whatsapp', label: 'WhatsApp', icon: '💬', color: 'bg-green-600' },
] as const

type Channel = (typeof CHANNEL_TABS)[number]['key']

export default function OutreachPage() {
  const [activeChannel, setActiveChannel] = useState<Channel>('email')

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Outreach</h1>
        <p className="text-sm text-gray-500 mt-1">
          Contacta a tus leads por email o WhatsApp. Funciona con los leads de{' '}
          <span className="font-medium text-indigo-600">cualquier fuente</span>.
        </p>
      </div>

      {/* Leads selected indicator */}
      <div className="mb-5 flex items-center gap-3 px-4 py-3 bg-indigo-50 border border-indigo-100 rounded-xl">
        <span className="text-indigo-600 text-lg">📋</span>
        <div className="flex-1">
          <p className="text-sm font-medium text-indigo-900">3 leads seleccionados para outreach</p>
          <p className="text-xs text-indigo-500">Selecciona más desde la página de Mis Leads</p>
        </div>
        <Badge variant="secondary" className="text-xs">
          🗺️ 1 &nbsp; 💼 1 &nbsp; 📘 1
        </Badge>
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
        {activeChannel === 'email' && <EmailForm key="email" />}
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

function EmailForm() {
  return (
    <motion.div {...formAnimation} className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-xl">✉️</span>
        <h2 className="text-lg font-semibold text-gray-900">Envío de Correos</h2>
        <Badge className="bg-emerald-50 text-emerald-600 border-emerald-200 text-[10px]">Email</Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label className="text-sm text-gray-600">Correo del remitente</Label>
          <Input placeholder="tu-correo@gmail.com" className="h-10" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-sm text-gray-600">Password de la Aplicación</Label>
          <Input type="password" placeholder="Contraseña de aplicación" className="h-10" />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label className="text-sm text-gray-600">Nombre del Enviador</Label>
        <Input placeholder="Ej: Juan Pérez - Empresa XYZ" className="h-10" />
      </div>

      <div className="space-y-1.5">
        <Label className="text-sm text-gray-600">Mensaje</Label>
        <Textarea
          placeholder="Escribe tu mensaje aquí... Puedes incluir emojis 😊"
          className="min-h-[120px] resize-y"
        />
      </div>

      <Button className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm cursor-pointer">
        ✉️ Enviar Correos
      </Button>
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

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label className="text-sm text-gray-600">Número de WhatsApp</Label>
          <Input placeholder="Ej: +51999888777" className="h-10" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-sm text-gray-600">Nombre del Enviador</Label>
          <Input placeholder="Ej: Juan Perez - Empresa XYZ" className="h-10" />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label className="text-sm text-gray-600">Mensaje</Label>
        <Textarea
          placeholder="Escribe tu mensaje de WhatsApp aquí... Puedes incluir emojis 😊"
          className="min-h-[120px] resize-y"
        />
      </div>

      <Button className="bg-green-600 hover:bg-green-700 text-white shadow-sm cursor-pointer">
        💬 Enviar WhatsApps
      </Button>
    </motion.div>
  )
}
