import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const PLANS = [
  // --- Recargas rápidas (precio $0.015/lead) ---
  // TODO: reemplazar url:'' por el link de pago real de cada recarga.
  {
    name: 'Recarga 500',
    price: '7.50',
    leads: '500',
    popular: false,
    features: ['Scraping de Google Maps', 'Leads con teléfono y email', 'Exportación CSV'],
    gradient: 'from-emerald-500 to-teal-500',
    btnClass: 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white',
    ringClass: 'border-gray-200 hover:border-emerald-300',
    url: '',
  },
  {
    name: 'Recarga 1,000',
    price: '15',
    leads: '1,000',
    popular: false,
    features: ['Scraping de Google Maps', 'Leads con teléfono y email', 'Exportación CSV'],
    gradient: 'from-cyan-500 to-blue-500',
    btnClass: 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white',
    ringClass: 'border-gray-200 hover:border-cyan-300',
    url: '',
  },
  {
    name: 'Recarga 1,500',
    price: '22.50',
    leads: '1,500',
    popular: false,
    features: ['Scraping de Google Maps', 'Leads con teléfono y email', 'Exportación CSV'],
    gradient: 'from-violet-500 to-purple-500',
    btnClass: 'bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white',
    ringClass: 'border-gray-200 hover:border-violet-300',
    url: '',
  },
  {
    name: 'Recarga 2,000',
    price: '30',
    leads: '2,000',
    popular: false,
    features: ['Scraping de Google Maps', 'Leads con teléfono y email', 'Exportación CSV'],
    gradient: 'from-amber-500 to-orange-500',
    btnClass: 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white',
    ringClass: 'border-gray-200 hover:border-amber-300',
    url: '',
  },
  // --- Planes ---
  {
    name: 'Básico',
    price: '37.50',
    leads: '2,500',
    popular: false,
    features: ['Scraping de Google Maps', 'Exportación CSV', 'Soporte por email'],
    gradient: 'from-gray-800 to-gray-900',
    btnClass: 'bg-gray-900 hover:bg-gray-800 text-white',
    ringClass: 'border-gray-200 hover:border-gray-300',
    url: 'https://app.sistema-ia.com/v2/preview/x16WvgS1ah6f4cfQrMQ5?notrack=true',
  },
  {
    name: 'Profesional',
    price: '75',
    leads: '5,000',
    popular: true,
    features: ['Todo del Básico', 'Scraping LinkedIn & Facebook', 'Datos Premium', 'Envío de correos y WhatsApp'],
    gradient: 'from-blue-600 to-indigo-600',
    btnClass: 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg shadow-blue-200/50',
    ringClass: 'border-blue-400 ring-2 ring-blue-100',
    url: 'https://app.sistema-ia.com/v2/preview/zQUMLhmYxodJJ2AfPyxm?notrack=true',
  },
  {
    name: 'Empresarial',
    price: '150',
    leads: '10,000',
    popular: false,
    features: ['Todo del Profesional', 'API access ilimitado', 'Soporte prioritario', 'Cuentas múltiples'],
    gradient: 'from-purple-600 to-pink-500',
    btnClass: 'bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 text-white',
    ringClass: 'border-gray-200 hover:border-purple-300',
    url: 'https://app.sistema-ia.com/v2/preview/oSy7kaUA0HOFWNRgodxI',
  },
]

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] as const },
  }),
}

export default function RecargaPage() {
  return (
    <motion.div
      className="p-6 lg:p-8 max-w-6xl mx-auto"
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={fadeUp} custom={0} className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 text-xs font-medium mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
          Planes disponibles
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          ⚡ Recarga de Leads
        </h1>
        <p className="text-sm text-gray-500 max-w-md mx-auto leading-relaxed">
          Amplía tu capacidad de generación de leads con nuestros planes flexibles. Obtén más datos.
        </p>
      </motion.div>

      {/* Plans */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 items-start">
        {PLANS.map((plan, i) => (
          <motion.div
            key={plan.name}
            variants={fadeUp}
            custom={2 + i}
            whileHover={{ y: -6 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className={`relative bg-white rounded-2xl border p-6 flex flex-col text-center shadow-sm transition-shadow duration-300 hover:shadow-xl ${plan.ringClass}`}
          >
            {plan.popular && (
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[10px] px-4 py-1 border-0 shadow-md">
                ✨ Más Popular
              </Badge>
            )}

            {/* Plan icon */}
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center mx-auto mb-3 mt-1 shadow-sm`}>
              <span className="text-white text-lg font-bold">
                {plan.name.charAt(0)}
              </span>
            </div>

            <p className="text-sm font-semibold text-gray-500 mb-1">{plan.name}</p>

            <div className="flex items-baseline justify-center gap-0.5 mb-1">
              <span className="text-sm text-gray-400 font-medium">$</span>
              <span className="text-4xl font-extrabold text-gray-900">{plan.price}</span>
            </div>

            <p className="text-sm text-blue-600 font-semibold mb-4">
              {plan.leads} leads incluidos
            </p>

            {/* Features */}
            <ul className="text-left space-y-2 mb-6 flex-1">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-xs text-gray-600">
                  <span className="text-emerald-500 mt-0.5 shrink-0">✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            {plan.url ? (
              <a href={plan.url} target="_blank" rel="noopener noreferrer">
                <Button
                  className={`w-full cursor-pointer transition-all duration-300 hover:scale-[1.03] active:scale-[0.97] ${plan.btnClass}`}
                >
                  🚀 Seleccionar Plan
                </Button>
              </a>
            ) : (
              <Button
                disabled
                className="w-full bg-gray-100 text-gray-400 cursor-not-allowed hover:bg-gray-100"
              >
                Disponible pronto
              </Button>
            )}
          </motion.div>
        ))}
      </div>

      {/* Footer note */}
      <motion.p
        variants={fadeUp}
        custom={6}
        className="text-center text-xs text-gray-400 mt-8"
      >
        Todos los planes incluyen acceso a ARIA CRM, comunidad y coaching en vivo.
      </motion.p>
    </motion.div>
  )
}
