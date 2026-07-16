import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { authService } from '@/services/auth.service'

export function ForgotPasswordPage() {
  const [email, setEmail]   = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent]     = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authService.forgotPassword(email)
      setSent(true)
    } catch {
      setSent(true) // always show success to prevent email enumeration
    } finally { setLoading(false) }
  }

  if (sent) return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center mx-auto mb-3">
        <span className="text-success text-xl">✓</span>
      </div>
      <h2 className="text-lg font-semibold text-neutral-100 mb-2">Check your email</h2>
      <p className="text-neutral-400 text-sm mb-4">If an account exists, a reset link has been sent.</p>
      <Link to="/login" className="text-brand-400 hover:text-brand-300 text-sm">Back to login</Link>
    </div>
  )

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-100 mb-1">Forgot password</h1>
      <p className="text-neutral-400 text-sm mb-6">We'll send a reset link to your email.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1">Email</label>
          <input
            type="email" value={email} onChange={e => setEmail(e.target.value)} required
            className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-brand-500"
            placeholder="you@example.com"
          />
        </div>
        <button type="submit" disabled={loading}
          className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 text-white text-sm font-semibold rounded-lg flex items-center justify-center gap-2">
          {loading && <Loader2 size={14} className="animate-spin" />}
          Send reset link
        </button>
      </form>
      <p className="text-center text-neutral-400 text-sm mt-4">
        <Link to="/login" className="text-brand-400 hover:text-brand-300">Back to login</Link>
      </p>
    </div>
  )
}
