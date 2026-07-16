import { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { authService } from '@/services/auth.service'

export function ResetPasswordPage() {
  const [params]  = useSearchParams()
  const navigate  = useNavigate()
  const token     = params.get('token') || ''
  const [pwd, setPwd]       = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (pwd !== confirm) { toast.error('Passwords do not match.'); return }
    setLoading(true)
    try {
      await authService.resetPassword(token, pwd, confirm)
      toast.success('Password reset! You can now sign in.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || 'Reset failed.')
    } finally { setLoading(false) }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-100 mb-1">Reset password</h1>
      <p className="text-neutral-400 text-sm mb-6">Choose a new password for your account.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        {[['New password', pwd, setPwd], ['Confirm password', confirm, setConfirm]].map(([label, val, setter]) => (
          <div key={label as string}>
            <label className="block text-sm font-medium text-neutral-300 mb-1">{label as string}</label>
            <input type="password" value={val as string} onChange={e => (setter as any)(e.target.value)} required minLength={10}
              className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-brand-500"
              placeholder="••••••••••" />
          </div>
        ))}
        <button type="submit" disabled={loading || !token}
          className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 text-white text-sm font-semibold rounded-lg flex items-center justify-center gap-2">
          {loading && <Loader2 size={14} className="animate-spin" />}
          Reset password
        </button>
      </form>
      <p className="text-center mt-4"><Link to="/login" className="text-brand-400 hover:text-brand-300 text-sm">Back to login</Link></p>
    </div>
  )
}
