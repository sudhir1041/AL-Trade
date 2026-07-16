/**
 * App.tsx
 * T16 ✅  Root router — public + protected routes.
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

// Layouts
import { AuthLayout }      from '@/components/layout/AuthLayout'
import { DashboardLayout } from '@/components/layout/DashboardLayout'

// Auth pages
import { LoginPage }          from '@/pages/auth/LoginPage'
import { RegisterPage }        from '@/pages/auth/RegisterPage'
import { ForgotPasswordPage }  from '@/pages/auth/ForgotPasswordPage'
import { ResetPasswordPage }   from '@/pages/auth/ResetPasswordPage'
import { VerifyEmailPage }     from '@/pages/auth/VerifyEmailPage'

// App pages
import { DashboardPage }   from '@/pages/dashboard/DashboardPage'
import { ScannerPage }     from '@/pages/scanner/ScannerPage'
import { TerminalPage }    from '@/pages/terminal/TerminalPage'
import { PortfolioPage }   from '@/pages/portfolio/PortfolioPage'
import { StrategiesPage }  from '@/pages/strategies/StrategiesPage'
import { AIInsightsPage }  from '@/pages/ai/AIInsightsPage'
import { ReportsPage }     from '@/pages/reports/ReportsPage'
import { SettingsPage }    from '@/pages/settings/SettingsPage'
import { AdminPage }       from '@/pages/admin/AdminPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>
}

export default function App() {
  return (
    <Routes>
      {/* Public / Auth routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login"           element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register"        element={<PublicRoute><RegisterPage /></PublicRoute>} />
        <Route path="/forgot-password" element={<PublicRoute><ForgotPasswordPage /></PublicRoute>} />
        <Route path="/reset-password"  element={<PublicRoute><ResetPasswordPage /></PublicRoute>} />
        <Route path="/verify-email"    element={<VerifyEmailPage />} />
      </Route>

      {/* Protected app routes */}
      <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route index                    element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard"        element={<DashboardPage />} />
        <Route path="/scanner"          element={<ScannerPage />} />
        <Route path="/terminal"         element={<TerminalPage />} />
        <Route path="/terminal/:symbol" element={<TerminalPage />} />
        <Route path="/portfolio"        element={<PortfolioPage />} />
        <Route path="/strategies"       element={<StrategiesPage />} />
        <Route path="/ai"               element={<AIInsightsPage />} />
        <Route path="/reports"          element={<ReportsPage />} />
        <Route path="/settings"         element={<SettingsPage />} />
        <Route path="/settings/:tab"    element={<SettingsPage />} />
        <Route path="/admin"            element={<AdminPage />} />
        <Route path="/admin/:tab"       element={<AdminPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
