/**
 * AuthLayout.tsx  T16.2 ✅
 */
import { Outlet } from 'react-router-dom'

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-neutral-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">T</span>
            </div>
            <span className="text-xl font-bold text-neutral-100">TradeMind AI</span>
          </div>
          <p className="text-neutral-400 text-sm">AI-powered cryptocurrency trading</p>
        </div>

        {/* Page content */}
        <div className="card p-6">
          <Outlet />
        </div>

        <p className="text-center text-neutral-500 text-xs mt-6">
          Trading involves substantial financial risk. Past performance does not guarantee future results.
        </p>
      </div>
    </div>
  )
}
