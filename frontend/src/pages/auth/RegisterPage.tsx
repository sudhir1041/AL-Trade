/**
 * RegisterPage.tsx  T16.2 ✅
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { authService } from '@/services/auth.service'

const schema = z.object({
  email:            z.string().email('Valid email required'),
  username:         z.string().min(3).max(30),
  first_name:       z.string().optional(),
  last_name:        z.string().optional(),
  password:         z.string().min(10, 'Min 10 characters'),
  confirm_password: z.string(),
}).refine(d => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path:    ['confirm_password'],
})

type FormData = z.infer<typeof schema>

export function RegisterPage() {
  const navigate  = useNavigate()
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      await authService.register(data)
      toast.success('Account created! Please check your email to verify.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  const field = (name: keyof FormData, label: string, type = 'text', placeholder = '') => (
    <div>
      <label className="block text-sm font-medium text-neutral-300 mb-1">{label}</label>
      <input
        {...register(name)}
        type={type}
        placeholder={placeholder}
        className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-brand-500 transition-colors"
      />
      {errors[name] && <p className="text-danger text-xs mt-1">{errors[name]?.message as string}</p>}
    </div>
  )

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-100 mb-1">Create account</h1>
      <p className="text-neutral-400 text-sm mb-6">Join TradeMind AI</p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        {field('email',    'Email',    'email',    'you@example.com')}
        {field('username', 'Username', 'text',     'tradername')}
        <div className="grid grid-cols-2 gap-3">
          {field('first_name', 'First name')}
          {field('last_name',  'Last name')}
        </div>
        {field('password',         'Password',         'password', '10+ characters')}
        {field('confirm_password', 'Confirm password', 'password', '••••••••')}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 mt-1 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {loading && <Loader2 size={14} className="animate-spin" />}
          Create account
        </button>
      </form>

      <p className="text-center text-neutral-400 text-sm mt-4">
        Already have an account?{' '}
        <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">Sign in</Link>
      </p>
    </div>
  )
}
