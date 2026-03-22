import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import LoginPage from '@/pages/LoginPage'
import DashboardLayout from '@/layouts/DashboardLayout'
import RecargaPage from '@/pages/dashboard/RecargaPage'
import ScraperPage from '@/pages/dashboard/ScraperPage'
import LeadsPage from '@/pages/dashboard/LeadsPage'
import OutreachPage from '@/pages/dashboard/OutreachPage'
import OnboardingPage from '@/pages/dashboard/OnboardingPage'
import HighLevelMCPPage from '@/pages/dashboard/HighLevelMCPPage'

export default function App() {
  return (
    <TooltipProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<Navigate to="onboarding" replace />} />
            <Route path="recarga" element={<RecargaPage />} />
            <Route path="scraper" element={<ScraperPage />} />
            <Route path="leads" element={<LeadsPage />} />
            <Route path="outreach" element={<OutreachPage />} />
            <Route path="onboarding" element={<OnboardingPage />} />
            <Route path="highlevel" element={<HighLevelMCPPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  )
}
