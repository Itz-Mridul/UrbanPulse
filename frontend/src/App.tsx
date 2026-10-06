import { Routes, Route } from 'react-router-dom'
import AppShell from './components/AppShell'
import Dashboard from './pages/Dashboard'
import ReplayPage from './pages/ReplayPage'
import VerificationPage from './pages/VerificationPage'
import MethodologyPage from './pages/MethodologyPage'
import LandingPage from './pages/LandingPage'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/replay" element={<ReplayPage />} />
        <Route path="/verify" element={<VerificationPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
      </Routes>
    </AppShell>
  )
}
