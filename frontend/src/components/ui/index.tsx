/**
 * components/ui/index.tsx
 * T16.1 ✅  Reusable UI component library.
 */
import { clsx } from 'clsx'
import { Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import React from 'react'

// ── Button ────────────────────────────────────────────────────────────────────
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'buy' | 'sell'
  size?:    'sm' | 'md' | 'lg'
  loading?: boolean
}
export function Button({ variant = 'primary', size = 'md', loading, children, className, disabled, ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary:   'bg-brand-600 hover:bg-brand-500 text-white',
    secondary: 'bg-neutral-700 hover:bg-neutral-600 text-neutral-100 border border-neutral-600',
    danger:    'bg-danger hover:bg-red-600 text-white',
    ghost:     'hover:bg-neutral-700/50 text-neutral-300 hover:text-neutral-100',
    buy:       'bg-success hover:bg-green-500 text-white',
    sell:      'bg-danger hover:bg-red-500 text-white',
  }
  const sizes = { sm: 'px-3 py-1.5 text-xs', md: 'px-4 py-2 text-sm', lg: 'px-5 py-2.5 text-sm' }
  return (
    <button className={clsx(base, variants[variant], sizes[size], className)} disabled={disabled || loading} {...props}>
      {loading && <Loader2 size={14} className="animate-spin" />}
      {children}
    </button>
  )
}

// ── Badge ─────────────────────────────────────────────────────────────────────
interface BadgeProps { children: React.ReactNode; variant?: 'default' | 'buy' | 'sell' | 'hold' | 'success' | 'warning' | 'danger'; className?: string }
export function Badge({ children, variant = 'default', className }: BadgeProps) {
  const variants = {
    default: 'bg-neutral-700 text-neutral-300',
    buy:     'bg-success/20 text-success',
    sell:    'bg-danger/20 text-danger',
    hold:    'bg-warning/20 text-warning',
    success: 'bg-success/20 text-success',
    warning: 'bg-warning/20 text-warning',
    danger:  'bg-danger/20 text-danger',
  }
  return <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-badge text-xs font-semibold', variants[variant], className)}>{children}</span>
}

// ── Card ──────────────────────────────────────────────────────────────────────
interface CardProps { children: React.ReactNode; className?: string; title?: string; action?: React.ReactNode }
export function Card({ children, className, title, action }: CardProps) {
  return (
    <div className={clsx('card', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700">
          {title && <h3 className="text-sm font-semibold text-neutral-200">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

// ── Stat widget ───────────────────────────────────────────────────────────────
interface StatProps { label: string; value: string | number; change?: number; prefix?: string; suffix?: string; mono?: boolean }
export function Stat({ label, value, change, prefix, suffix, mono }: StatProps) {
  return (
    <div className="widget">
      <p className="text-xs text-neutral-400 mb-1">{label}</p>
      <p className={clsx('text-lg font-semibold text-neutral-100', mono && 'font-mono')}>
        {prefix}{value}{suffix}
      </p>
      {change !== undefined && (
        <div className={clsx('flex items-center gap-1 text-xs mt-1', change >= 0 ? 'text-success' : 'text-danger')}>
          {change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </div>
      )}
    </div>
  )
}

// ── PnL display ───────────────────────────────────────────────────────────────
export function PnL({ value, showSign = true, className }: { value: number; showSign?: boolean; className?: string }) {
  const pos = value >= 0
  return (
    <span className={clsx('font-mono', pos ? 'text-success' : 'text-danger', className)}>
      {showSign && (pos ? '+' : '')}{value.toFixed(2)}
    </span>
  )
}

// ── Direction badge ───────────────────────────────────────────────────────────
export function DirectionBadge({ direction }: { direction: string }) {
  const map: Record<string, 'buy' | 'sell' | 'hold' | 'default'> = {
    BUY: 'buy', SELL: 'sell', HOLD: 'hold', IGNORE: 'default',
  }
  return <Badge variant={map[direction] || 'default'}>{direction}</Badge>
}

// ── Confidence bar ────────────────────────────────────────────────────────────
export function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 90 ? 'bg-success' : value >= 75 ? 'bg-brand-500' : value >= 50 ? 'bg-warning' : 'bg-neutral-600'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-neutral-700 rounded-full h-1.5">
        <div className={clsx('h-1.5 rounded-full transition-all', color)} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-neutral-400 w-8 text-right">{value.toFixed(0)}</span>
    </div>
  )
}

// ── Loading spinner ───────────────────────────────────────────────────────────
export function Spinner({ size = 20 }: { size?: number }) {
  return <Loader2 size={size} className="animate-spin text-brand-400" />
}

// ── Empty state ───────────────────────────────────────────────────────────────
export function EmptyState({ icon, title, message, action }: { icon?: React.ReactNode; title: string; message: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="text-neutral-500 mb-3">{icon}</div>}
      <h3 className="text-sm font-medium text-neutral-300 mb-1">{title}</h3>
      <p className="text-xs text-neutral-500 mb-4 max-w-xs">{message}</p>
      {action}
    </div>
  )
}

// ── Table ─────────────────────────────────────────────────────────────────────
export function Table({ headers, children, className }: { headers: string[]; children: React.ReactNode; className?: string }) {
  return (
    <div className={clsx('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-neutral-700">
            {headers.map(h => <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-neutral-400">{h}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-700/50">{children}</tbody>
      </table>
    </div>
  )
}

export function Tr({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) {
  return <tr onClick={onClick} className={clsx('hover:bg-neutral-700/30 transition-colors', onClick && 'cursor-pointer', className)}>{children}</tr>
}

export function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={clsx('px-4 py-2.5 text-neutral-300', className)}>{children}</td>
}

// ── Skeleton loader ───────────────────────────────────────────────────────────
export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse bg-neutral-700 rounded', className)} />
}

// ── Input ─────────────────────────────────────────────────────────────────────
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> { label?: string; error?: string }
export function Input({ label, error, className, ...props }: InputProps) {
  return (
    <div>
      {label && <label className="block text-xs font-medium text-neutral-400 mb-1">{label}</label>}
      <input
        className={clsx(
          'w-full px-3 py-2 bg-neutral-700 border rounded-lg text-sm text-neutral-100 placeholder-neutral-500 focus:outline-none transition-colors',
          error ? 'border-danger focus:border-danger' : 'border-neutral-600 focus:border-brand-500',
          className
        )}
        {...props}
      />
      {error && <p className="text-danger text-xs mt-1">{error}</p>}
    </div>
  )
}

// ── Select ────────────────────────────────────────────────────────────────────
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> { label?: string; options: { value: string; label: string }[] }
export function Select({ label, options, className, ...props }: SelectProps) {
  return (
    <div>
      {label && <label className="block text-xs font-medium text-neutral-400 mb-1">{label}</label>}
      <select
        className={clsx('w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-lg text-sm text-neutral-100 focus:outline-none focus:border-brand-500 transition-colors', className)}
        {...props}
      >
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}
