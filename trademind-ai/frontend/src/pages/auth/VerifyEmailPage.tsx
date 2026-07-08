import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Loader2, CheckCircle, XCircle } from 'lucide-react'
import { authService } from '@/services/auth.service'

export function VerifyEmailPage() {
  const [params]  = useSearchParams()
  const navigate  = useNavigate()
  const token     = params.get('token') || ''
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [msg, setMsg]       = useState('')

  useEffect(() => {
    if (!token) { setStatus('error'); setMsg('No verification token found.'); return }
    authService.verifyEmail(token)
      .then(() => { setStatus('success'); setMsg('Email verified! Redirecting...'); setTimeout(() => navigate('/login'), 2000) })
      .catch(e  => { setStatus('error');  setMsg(e.response?.data?.error?.message || 'Verification failed.') })
  }, [token])

  return (
    <div className="text-center py-4">
      {status === 'loading' && <><Loader2 size={32} className="animate-spin text-brand-400 mx-auto mb-3" /><p className="text-neutral-300">Verifying your email...</p></>}
      {status === 'success' && <><CheckCircle size={32} className="text-success mx-auto mb-3" /><h2 className="text-lg font-semibold text-neutral-100 mb-1">Email verified!</h2><p className="text-neutral-400 text-sm">{msg}</p></>}
      {status === 'error'   && <><XCircle size={32} className="text-danger mx-auto mb-3" /><h2 className="text-lg font-semibold text-neutral-100 mb-1">Verification failed</h2><p className="text-neutral-400 text-sm">{msg}</p></>}
    </div>
  )
}
