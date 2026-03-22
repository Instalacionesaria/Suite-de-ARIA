import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import HighLevelPanel from '@/components/HighLevelPanel'
import { API_URL } from '@/config'

const NAV_ITEMS = [
  {
    label: 'Onboarding',
    to: '/dashboard/onboarding',
    icon: '🤖',
    description: 'Asistente IA',
  },
  {
    label: 'Scraper',
    to: '/dashboard/scraper',
    icon: '🔍',
    description: 'Búsqueda de leads',
  },
  {
    label: 'Mis Leads',
    to: '/dashboard/leads',
    icon: '📋',
    description: 'Pool unificado',
  },
  {
    label: 'Outreach',
    to: '/dashboard/outreach',
    icon: '📨',
    description: 'Email y WhatsApp',
  },
  {
    label: 'Recarga de Leads',
    to: '/dashboard/recarga',
    icon: '⚡',
    description: 'Planes y créditos',
  },
  {
    label: 'Acceso MCP HighLevel',
    to: '/dashboard/highlevel',
    icon: '🔗',
    description: 'Subcuenta HighLevel',
  },
]

export default function DashboardLayout() {
  const navigate = useNavigate()
  const [leadsScraped, setLeadsScraped] = useState(0)
  const [leadsRemaining, setLeadsRemaining] = useState(0)

  const fetchLeads = useCallback(async () => {
    const email = localStorage.getItem('aria_user_email')
    if (!email) return
    try {
      const res = await fetch(`${API_URL}/user-leads?email=${encodeURIComponent(email)}`)
      if (res.ok) {
        const data = await res.json()
        setLeadsScraped(data.numero_leads_scrapeados)
        setLeadsRemaining(data.leads_disponibles_en_total)
      }
    } catch {
      // silently ignore
    }
  }, [])

  useEffect(() => {
    fetchLeads()
    const interval = setInterval(fetchLeads, 30000)
    return () => clearInterval(interval)
  }, [fetchLeads])

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* ── Left Sidebar ── */}
      <aside className="w-64 bg-[#1a1d2e] text-white flex flex-col shrink-0 fixed inset-y-0 left-0 z-30">
        {/* Logo */}
        <div className="px-5 pt-6 pb-4 flex flex-col items-center">
          <div className="w-14 h-14 rounded-xl bg-gray-800 flex items-center justify-center mb-3 shadow-lg">
            <svg viewBox="0 0 40 40" fill="none" className="w-8 h-8" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 6L8 32h5.5l2.5-6h8l2.5 6H32L20 6zm-2.3 16 2.3-5.5 2.3 5.5h-4.6z" fill="white" />
            </svg>
          </div>
          <h2 className="font-bold text-sm tracking-wider">ARIA SCRAPER</h2>
          <p className="text-[11px] text-gray-400 tracking-[0.2em]">SUITE</p>
        </div>

        <Separator className="bg-white/10 mx-4" />

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group ${
                  isActive
                    ? 'bg-indigo-600/20 text-white'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute left-0 w-[3px] h-8 bg-indigo-500 rounded-r-full"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className="text-lg">{item.icon}</span>
                  <div>
                    <p className="font-medium leading-tight">{item.label}</p>
                    <p className="text-[10px] text-gray-500 group-hover:text-gray-400 transition-colors">
                      {item.description}
                    </p>
                  </div>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <Separator className="bg-white/10 mx-4" />

        {/* Leads counter */}
        <div className="px-5 py-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Leads Scrapeados</span>
            <span className="font-bold text-white">{leadsScraped}</span>
          </div>
          <Progress value={leadsScraped + leadsRemaining > 0 ? (leadsScraped / (leadsScraped + leadsRemaining)) * 100 : 0} className="h-1.5 bg-gray-700" />
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">Leads Restantes</span>
            <span className="font-bold text-emerald-400">{leadsRemaining}</span>
          </div>

          <button
            onClick={() => {
              localStorage.removeItem('aria_user')
              localStorage.removeItem('aria_user_email')
              localStorage.removeItem('aria_user_id')
              localStorage.removeItem('aria_onboarding_data')
              navigate('/')
            }}
            className="w-full mt-2 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-red-500/30 text-red-400 text-sm font-medium hover:bg-red-500/10 transition-all duration-200 cursor-pointer"
          >
            ← Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="flex-1 ml-64 mr-72 overflow-y-auto">
        <Outlet />
      </main>

      {/* ── Right Sidebar: HighLevel ── */}
      <div className="fixed inset-y-0 right-0 z-20">
        <HighLevelPanel />
      </div>
    </div>
  )
}
