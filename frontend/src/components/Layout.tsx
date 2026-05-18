import { BarChart2, List, PieChart, Settings } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', icon: BarChart2 },
  { to: '/watchlist', label: 'Watchlist', icon: List },
  { to: '/portfolio', label: 'Portfolio', icon: PieChart },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <aside className="w-52 shrink-0 border-r border-gray-800 flex flex-col">
        <div className="px-5 py-4 border-b border-gray-800">
          <span className="text-sm font-bold text-indigo-400 tracking-wide">STOCK REVERSAL</span>
        </div>
        <nav className="flex-1 py-4 space-y-1 px-2">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
