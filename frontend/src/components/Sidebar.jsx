import { NavLink } from 'react-router-dom'
import {
  Inbox, Bot, BarChart3, Zap, Activity, FlaskConical
} from 'lucide-react'

const navItems = [
  { to: '/',            icon: Inbox,         label: 'Email Queue' },
  { to: '/simulation',  icon: Bot,           label: 'Agent Simulation' },
  { to: '/evaluation',  icon: BarChart3,     label: 'Evaluation' },
  { to: '/live',        icon: FlaskConical,  label: 'Live Triage' },
]

export default function Sidebar({ health }) {
  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-full fixed top-0 left-0 z-20">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <p className="font-semibold text-white text-sm leading-tight">Email Triage</p>
            <p className="text-xs text-gray-500 leading-tight">OpenEnv AI</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-3">
          Main Menu
        </p>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Status Footer */}
      <div className="px-4 py-4 border-t border-gray-800">
        <div className="flex items-center gap-2 px-2">
          <Activity size={13} className={health ? 'text-emerald-400' : 'text-red-400'} />
          <span className="text-xs text-gray-500">
            API {health ? (
              <span className="text-emerald-400 font-medium">Online</span>
            ) : (
              <span className="text-red-400 font-medium">Offline</span>
            )}
          </span>
        </div>
        <p className="text-xs text-gray-600 mt-2 px-2">v1.0.0 · OpenEnv Spec</p>
      </div>
    </aside>
  )
}
