import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] },
  }),
}

const scaleIn = {
  hidden: { opacity: 0, scale: 0.85 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] },
  },
}

const MODULES = [
  {
    key: 'scraper',
    icon: '🔍',
    title: 'Scrapea',
    tagline: 'Encuentra leads al instante',
    description:
      'Coloca el tipo de negocio y la localización para obtener leads cualificados en segundos.',
    gradient: 'from-indigo-500/40 via-blue-400/40 to-cyan-400/40',
  },
  {
    key: 'prospector',
    icon: '🎯',
    title: 'Prospecta',
    tagline: 'Conecta con los correctos',
    description:
      'Gestiona, califica y prioriza tus prospectos para maximizar cada oportunidad de venta.',
    gradient: 'from-purple-500/40 via-pink-400/40 to-rose-400/40',
  },
  {
    key: 'scheduler',
    icon: '📅',
    title: 'Agenda',
    tagline: 'Cierra más reuniones',
    description:
      'Programa citas automáticamente con tus prospectos y sincroniza todo con tu calendario.',
    gradient: 'from-amber-500/40 via-orange-400/40 to-yellow-400/40',
  },
]

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [activeModule, setActiveModule] = useState(0)
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen flex overflow-hidden">
      {/* ── Left Panel ── */}
      <div className="flex flex-col justify-center items-center w-full lg:w-1/2 px-8 py-12 bg-white relative">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-20 -left-20 w-72 h-72 bg-indigo-100/60 rounded-full blur-3xl animate-[drift_8s_ease-in-out_infinite]" />
          <div className="absolute -bottom-16 -right-16 w-64 h-64 bg-purple-100/50 rounded-full blur-3xl animate-[drift_10s_ease-in-out_infinite_reverse]" />
        </div>

        <motion.div
          className="w-full max-w-sm relative z-10"
          initial="hidden"
          animate="visible"
        >
          <motion.h1
            variants={fadeUp}
            custom={0}
            className="text-3xl font-bold text-center text-gray-900 mb-2 leading-tight"
          >
            ¡Bienvenido a la{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-[length:200%_auto] animate-[shimmer-text_3s_linear_infinite]">
              SUITE DE ARIA
            </span>
            !
          </motion.h1>

          <motion.p
            variants={fadeUp}
            custom={1}
            className="text-center text-gray-500 text-sm mb-8"
          >
            Scrapea, prospecta y agenda — todo en{' '}
            <span className="text-indigo-500 font-medium">un solo lugar</span>.
          </motion.p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <motion.div variants={fadeUp} custom={2} className="space-y-1.5">
              <Label
                htmlFor="email"
                className="text-sm font-medium text-gray-700 flex items-center gap-1.5"
              >
                <span className="text-gray-400">✉</span> Correo Electrónico
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="border-gray-200 focus-visible:ring-indigo-500/30 focus-visible:border-indigo-400 h-11 transition-all duration-300 hover:border-indigo-300 hover:shadow-sm"
                required
              />
            </motion.div>

            <motion.div variants={fadeUp} custom={3} className="space-y-1.5">
              <Label
                htmlFor="code"
                className="text-sm font-medium text-gray-700 flex items-center gap-1.5"
              >
                <span>🔑</span> Ingresa tu código de ARIA Suite
              </Label>
              <Input
                id="code"
                type="text"
                placeholder="Ingresa tu código"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="border-gray-200 focus-visible:ring-indigo-500/30 focus-visible:border-indigo-400 h-11 transition-all duration-300 hover:border-indigo-300 hover:shadow-sm"
                required
              />
              <p className="text-xs text-gray-500 leading-relaxed">
                <span className="font-semibold text-gray-600">🔵 Nota</span>: Recuerda que tu
                código fue enviado a tu correo electrónico con el cual te registraste en ARIA IA.
                El asunto por el cual lo puedes buscar es{' '}
                <span className="font-semibold text-indigo-600">
                  "Este es tu Acceso para ARIA Suite"
                </span>
                .
              </p>
            </motion.div>

            <motion.div variants={fadeUp} custom={4}>
              <Button
                type="submit"
                className="w-full h-11 relative overflow-hidden bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white font-semibold shadow-lg shadow-indigo-200/60 border-0 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-300/40 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
              >
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-[btn-shimmer_2.5s_ease-in-out_infinite]" />
                <span className="relative">🚀 Iniciar Sesión</span>
              </Button>
            </motion.div>
          </form>

          <motion.div
            variants={fadeUp}
            custom={5}
            className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-center transition-all duration-300 hover:border-amber-300 hover:shadow-sm"
          >
            <p className="text-sm font-semibold text-amber-700 mb-0.5">🔒 Acceso restringido</p>
            <p className="text-xs text-amber-600 leading-relaxed">
              Solo usuarios <span className="font-semibold">activos</span> con{' '}
              <span className="font-semibold text-indigo-600">código de acceso válido</span> pueden
              ingresar al sistema.
            </p>
          </motion.div>

          <motion.div variants={fadeUp} custom={6} className="flex justify-center gap-1.5 mt-6">
            {MODULES.map((_, i) => (
              <button
                key={i}
                onClick={() => setActiveModule(i)}
                className={`w-2 h-2 rounded-full transition-all duration-300 cursor-pointer ${
                  i === activeModule
                    ? 'bg-indigo-500 scale-125 animate-pulse'
                    : 'bg-gray-200 hover:bg-gray-300'
                }`}
              />
            ))}
          </motion.div>
        </motion.div>
      </div>

      {/* ── Right Panel ── */}
      <div
        className="hidden lg:flex flex-col justify-center items-center w-1/2 relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #1a0a3e 0%, #3b1a7e 40%, #7c3aed 100%)',
        }}
      >
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-purple-500/30 rounded-full blur-[100px] animate-[aurora_6s_ease-in-out_infinite]" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-[120px] animate-[aurora_8s_ease-in-out_infinite_reverse]" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-pink-500/15 rounded-full blur-[80px] animate-[aurora_7s_ease-in-out_2s_infinite]" />
        </div>

        {PARTICLES.map((p) => (
          <span
            key={p.id}
            className="absolute rounded-full bg-white"
            style={{
              width: p.size,
              height: p.size,
              top: p.top,
              left: p.left,
              opacity: p.opacity,
              animation: `float ${p.duration}s ease-in-out ${p.delay}s infinite`,
            }}
          />
        ))}

        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.3) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        <motion.div
          className="relative z-10 flex flex-col items-center text-center px-10 max-w-md"
          initial="hidden"
          animate="visible"
        >
          {/* Logo */}
          <motion.div
            variants={scaleIn}
            className="w-20 h-20 rounded-2xl bg-gray-900 flex items-center justify-center mb-5 shadow-2xl shadow-black/40 relative group"
          >
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/30 to-purple-500/30 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-500 opacity-20 blur-sm animate-pulse" />
            <svg
              viewBox="0 0 40 40"
              fill="none"
              className="w-10 h-10 relative z-10"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M20 6L8 32h5.5l2.5-6h8l2.5 6H32L20 6zm-2.3 16 2.3-5.5 2.3 5.5h-4.6z"
                fill="white"
              />
            </svg>
          </motion.div>

          {/* Brand */}
          <motion.h2
            variants={fadeUp}
            custom={1}
            className="text-3xl font-bold text-white tracking-wider mb-1"
          >
            ARIA
          </motion.h2>
          <motion.p
            variants={fadeUp}
            custom={2}
            className="text-purple-300 font-semibold tracking-[0.3em] text-sm mb-8"
          >
            SUITE
          </motion.p>

          {/* Module selector tabs */}
          <motion.div
            variants={fadeUp}
            custom={3}
            className="flex gap-2 mb-5 w-full"
          >
            {MODULES.map((mod, i) => (
              <button
                key={mod.key}
                onClick={() => setActiveModule(i)}
                className={`flex-1 py-2 px-2 rounded-xl text-xs font-medium transition-all duration-300 cursor-pointer border ${
                  i === activeModule
                    ? 'bg-white/15 border-white/25 text-white shadow-lg shadow-purple-900/20'
                    : 'bg-white/5 border-white/10 text-purple-300 hover:bg-white/10 hover:text-white'
                }`}
              >
                <span className="text-base">{mod.icon}</span>
                <span className="block mt-0.5">{mod.title}</span>
              </button>
            ))}
          </motion.div>

          {/* Active module card */}
          <motion.div
            variants={fadeUp}
            custom={4}
            className="w-full rounded-2xl relative p-[1px] mb-6 group"
          >
            <div
              className={`absolute inset-0 rounded-2xl bg-gradient-to-r ${MODULES[activeModule].gradient} animate-[border-spin_4s_linear_infinite] bg-[length:300%_300%]`}
            />
            <div className="relative rounded-2xl bg-white/10 backdrop-blur-md px-6 py-5 transition-all duration-500 group-hover:bg-white/[0.14] min-h-[130px] flex flex-col justify-center">
              <AnimatePresence mode="wait">
                <motion.div
                  key={MODULES[activeModule].key}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.3 }}
                >
                  <p className="text-white font-semibold text-lg mb-1">
                    {MODULES[activeModule].icon} {MODULES[activeModule].tagline}
                  </p>
                  <p className="text-purple-200 text-sm leading-relaxed">
                    {MODULES[activeModule].description}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Powered by HighLevel badge */}
          <motion.div
            variants={fadeUp}
            custom={5}
            className="flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm mb-5"
          >
            <span className="text-[10px] text-purple-400 uppercase tracking-wider font-medium">
              Potenciado por
            </span>
            <span className="text-white font-bold text-sm tracking-wide">HighLevel</span>
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          </motion.div>

          {/* Tags */}
          <motion.div
            variants={fadeUp}
            custom={6}
            className="flex items-center gap-4 text-purple-300 text-sm"
          >
            {['Scrapear', 'Prospectar', 'Agendar'].map((tag, i) => (
              <motion.span
                key={tag}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full border backdrop-blur-sm transition-all duration-300 cursor-pointer ${
                  i === activeModule
                    ? 'border-white/25 bg-white/15 text-white'
                    : 'border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20'
                }`}
                onClick={() => setActiveModule(i)}
                whileHover={{ scale: 1.08, y: -2 }}
                transition={{ type: 'spring', stiffness: 400, damping: 17 }}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${
                  i === activeModule ? 'bg-white animate-pulse' : 'bg-purple-400'
                }`} />
                {tag}
              </motion.span>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}

const PARTICLES = [
  { id: 1, size: 3, top: '8%', left: '15%', opacity: 0.4, duration: 5, delay: 0 },
  { id: 2, size: 2, top: '18%', left: '78%', opacity: 0.6, duration: 4, delay: 1.2 },
  { id: 3, size: 4, top: '32%', left: '6%', opacity: 0.25, duration: 6, delay: 0.5 },
  { id: 4, size: 2, top: '45%', left: '88%', opacity: 0.5, duration: 5, delay: 2 },
  { id: 5, size: 3, top: '60%', left: '22%', opacity: 0.35, duration: 7, delay: 1 },
  { id: 6, size: 2, top: '72%', left: '65%', opacity: 0.45, duration: 4.5, delay: 0.8 },
  { id: 7, size: 5, top: '85%', left: '40%', opacity: 0.2, duration: 8, delay: 1.5 },
  { id: 8, size: 2, top: '12%', left: '52%', opacity: 0.5, duration: 5.5, delay: 0.3 },
  { id: 9, size: 3, top: '55%', left: '45%', opacity: 0.3, duration: 6.5, delay: 2.2 },
  { id: 10, size: 2, top: '78%', left: '12%', opacity: 0.55, duration: 4, delay: 1.8 },
  { id: 11, size: 3, top: '25%', left: '35%', opacity: 0.3, duration: 5, delay: 0.7 },
  { id: 12, size: 2, top: '90%', left: '80%', opacity: 0.4, duration: 6, delay: 1.1 },
]
