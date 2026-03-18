import { NavLink } from 'react-router-dom'
import clsx from 'clsx'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/transactions', label: 'Transacciones', icon: '📋' },
  { to: '/monthly', label: 'Vista Mensual', icon: '📅' },
  { to: '/comparison', label: 'Comparativo', icon: '📈' },
  { to: '/budget', label: 'Presupuesto', icon: '🎯' },
  { to: '/accounts', label: 'Cuentas', icon: '🏦' },
  { to: '/upload', label: 'Cargar Cartola', icon: '⬆️' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
      <div className="px-5 py-6 border-b border-gray-100">
        <h1 className="text-lg font-bold text-gray-900">💰 Finanzas</h1>
        <p className="text-xs text-gray-500 mt-0.5">Control personal</p>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }: { isActive: boolean }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            <span>{link.icon}</span>
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
