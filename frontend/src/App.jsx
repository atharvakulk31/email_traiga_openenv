import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import EmailQueue from './pages/EmailQueue'
import EmailDetail from './pages/EmailDetail'
import AgentSimulation from './pages/AgentSimulation'
import EvaluationDashboard from './pages/EvaluationDashboard'
import LiveTriage from './pages/LiveTriage'
import { envApi } from './api/client'

function Layout({ health }) {
  const location = useLocation()

  const PAGE_TITLES = {
    '/':           'Email Queue',
    '/simulation': 'Agent Simulation',
    '/evaluation': 'Evaluation',
    '/live':       'Live Triage',
  }

  useEffect(() => {
    const base = 'Email Triage AI'
    const title = Object.entries(PAGE_TITLES).find(([path]) =>
      path === '/' ? location.pathname === '/' : location.pathname.startsWith(path)
    )
    document.title = title ? `${title[1]} — ${base}` : base
  }, [location.pathname])

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar health={health} />

      {/* Main Content */}
      <main className="flex-1 ml-64 overflow-y-auto">
        <div className="min-h-full p-6 lg:p-8">
          <Routes>
            <Route path="/"              element={<EmailQueue />} />
            <Route path="/email/:id"     element={<EmailDetail />} />
            <Route path="/simulation"    element={<AgentSimulation />} />
            <Route path="/evaluation"    element={<EvaluationDashboard />} />
            <Route path="/live"          element={<LiveTriage />} />
            <Route path="*"             element={<NotFound />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <p className="text-6xl font-bold text-gray-800 mb-4">404</p>
      <p className="text-gray-400 font-medium mb-1">Page not found</p>
      <p className="text-gray-600 text-sm">The page you're looking for doesn't exist.</p>
    </div>
  )
}

export default function App() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    envApi.health()
      .then(() => setHealth(true))
      .catch(() => setHealth(false))

    // Re-check every 30s
    const interval = setInterval(() => {
      envApi.health()
        .then(() => setHealth(true))
        .catch(() => setHealth(false))
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  return (
    <BrowserRouter>
      <Layout health={health} />
    </BrowserRouter>
  )
}
