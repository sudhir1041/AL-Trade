/**
 * LoginPage.tsx  T16.2 ✅
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/stores/authStore'

const schema = z.object({
  email:     z.string().email('Valid email required'),
  password:  z.string().min(1, 'Password required'),
  totp_code: z.string().optional(),
})

type FormData = z.infer<typeof schema>

export function LoginPage() {
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const [needs2FA, setNeeds2FA]         = useState(false)
  const [loading, setLoading]           = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      const res = await authService.login(data.email, data.password, data.totp_code)
      const { access_token, refresh_token, user } = res.data.data
      setTokens(access_token, refresh_token)
      setUser(user as any)
      toast.success('Welcome back!')
      navigate('/dashboard')
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Login failed.'
      if (msg.toLowerCase().includes('two-factor') || msg.toLowerCase().includes('2fa')) {
        setNeeds2FA(true)
        toast('Please enter your 2FA code.', { icon: '🔐' })
      } else {
        toast.error(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-100 mb-1">Sign in</h1>
      <p className="text-neutral-400 text-sm mb-6">Welcome back to TradeMind AI</p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1">Email</label>
          <input
            {...register('email')}
            type="email"
            autoComplete="email"
            className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-brand-500 transition-colors"
            placeholder="you@example.com"
          />
          {errors.email && <p className="text-danger text-xs mt-1">{errors.email.message}</p>}
        </div>

        {/* Password */}
        <div>
          <div className="flex justify-between mb-1">
            <label className="text-sm font-medium text-neutral-300">Password</label>
            <Link to="/forgot-password" className="text-xs text-brand-400 hover:text-brand-300">
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              className="w-full px-3 py-2 pr-10 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-brand-500 transition-colors"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(s => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-200"
            >
              {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
          {errors.password && <p className="text-danger text-xs mt-1">{errors.password.message}</p>}
        </div>

        {/* 2FA code (shown only when needed) */}
        {needs2FA && (
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1">2FA Code</label>
            <input
              {...register('totp_code')}
              type="text"
              maxLength={6}
              inputMode="numeric"
              className="w-full px-3 py-2 bg-neutral-700 border border-brand-500 rounded-lg text-sm text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-brand-400 tracking-widest text-center"
              placeholder="000000"
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {loading && <Loader2 size={14} className="animate-spin" />}
          Sign in
        </button>
      </form>

      <p className="text-center text-neutral-400 text-sm mt-4">
        Don't have an account?{' '}
        <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">
          Create account
        </Link>
      </p>
    </div>
  )
}
