/**
 * DashboardLayout.tsx  T16.3 ✅
 * Full trading terminal layout: sidebar + header + main content.
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Radar, LineChart, Briefcase,
  Settings, Brain, BarChart3, Shield, LogOut,
  Bell, ChevronDown, Cpu, FileText
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { authService }  from '@/services/auth.service'
import { clsx }         from 'clsx'
import { useState }     from 'react'

const NAV = [
  { path: '/dashboard',  label: 'Dashboard',   icon: LayoutDashboard },
  { path: '/scanner',    label: 'Scanner',      icon: Radar },
  { path: '/terminal',   label: 'Terminal',     icon: LineChart },
  { path: '/portfolio',  label: 'Portfolio',    icon: Briefcase },
  { path: '/strategies', label: 'Strategies',   icon: Cpu },
  { path: '/ai',         label: 'AI Insights',  icon: Brain },
  { path: '/reports',    label: 'Reports',      icon: BarChart3 },
]

export function DashboardLayout() {
  const { user, refreshToken, logout } = useAuthStore()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  const handleLogout = async () => {
    try { if (refreshToken) await authService.logout(refreshToken) } catch {}
    logout()
  }

  return (
    <div className="flex h-screen bg-neutral-900 overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside className={clsx(
        'flex flex-col bg-neutral-800 border-r border-neutral-700 transition-all duration-200',
        collapsed ? 'w-16' : 'w-56'
      )}>
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 py-4 border-b border-neutral-700 h-14">
          <div className="w-7 h-7 rounded-md bg-brand-600 flex-shrink-0 flex items-center justify-center">
            <span className="text-white font-bold text-xs">T</span>
          </div>
          {!collapsed && <span className="font-bold text-neutral-100 text-sm">TradeMind AI</span>}
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {NAV.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                clsx('nav-item', isActive && 'active', collapsed && 'justify-center px-2')
              }
            >
              <Icon size={16} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Bottom actions */}
        <div className="p-2 border-t border-neutral-700 space-y-0.5">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              clsx('nav-item', isActive && 'active', collapsed && 'justify-center px-2')
            }
          >
            <Settings size={16} className="flex-shrink-0" />
            {!collapsed && <span>Settings</span>}
          </NavLink>

          {user?.role && ['ADMIN', 'SUPER_ADMIN'].includes(user.role) && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                clsx('nav-item', isActive && 'active', collapsed && 'justify-center px-2')
              }
            >
              <Shield size={16} className="flex-shrink-0" />
              {!collapsed && <span>Admin</span>}
            </NavLink>
          )}

          <button
            onClick={handleLogout}
            className={clsx(
              'nav-item w-full text-danger hover:bg-danger/10 hover:text-danger',
              collapsed && 'justify-center px-2'
            )}
          >
            <LogOut size={16} className="flex-shrink-0" />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* ── Main area ───────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-neutral-800 border-b border-neutral-700 flex items-center justify-between px-4 flex-shrink-0">
          <button
            onClick={() => setCollapsed(c => !c)}
            className="text-neutral-400 hover:text-neutral-100 transition-colors"
          >
            <LayoutDashboard size={18} />
          </button>

          <div className="flex items-center gap-3">
            {/* Notifications bell */}
            <button className="relative text-neutral-400 hover:text-neutral-100 transition-colors">
              <Bell size={18} />
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-brand-600 rounded-full text-[10px] flex items-center justify-center text-white">3</span>
            </button>

            {/* User menu */}
            <button className="flex items-center gap-2 text-sm text-neutral-300 hover:text-neutral-100 transition-colors">
              <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-xs font-semibold text-white">
                {user?.first_name?.[0] || user?.username?.[0] || 'U'}
              </div>
              <span className="hidden md:block">{user?.username}</span>
              <ChevronDown size={14} />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
