/**
 * SettingsPage.tsx  T16.10 ✅
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Shield, Link, Bell, Palette, Key, CreditCard } from 'lucide-react'
import { authService } from '@/services/auth.service'
import { exchangeService, billingService } from '@/services'
import { Card, Button, Input, Badge, Spinner } from '@/components/ui'
import { useAuthStore } from '@/stores/authStore'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'profile',    label: 'Profile',    icon: Settings },
  { id: 'security',   label: 'Security',   icon: Shield   },
  { id: 'exchanges',  label: 'Exchanges',  icon: Link     },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'appearance', label: 'Appearance', icon: Palette  },
  { id: 'billing',    label: 'Billing',    icon: CreditCard },
]

export function SettingsPage() {
  const [tab, setTab] = useState('profile')
  const { user }      = useAuthStore()
  const qc = useQueryClient()

  const { data: exchangeRes } = useQuery({ queryKey: ['exchange-accounts'], queryFn: () => exchangeService.getAccounts() })
  const { data: subRes }      = useQuery({ queryKey: ['subscription'],      queryFn: () => billingService.getSubscription() })
  const { data: plansRes }    = useQuery({ queryKey: ['plans'],             queryFn: () => billingService.getPlans() })

  const accounts = (exchangeRes?.data?.data || []) as any[]
  const sub      = subRes?.data?.data as any
  const plans    = (plansRes?.data?.data || []) as any[]

  const disconnectMutation = useMutation({
    mutationFn: (id: string) => exchangeService.deleteAccount(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['exchange-accounts'] }); toast.success('Exchange disconnected.') },
  })

  return (
    <div className="p-4 md:p-6">
      <div className="flex items-center gap-2 mb-6">
        <Settings size={18} className="text-brand-400" />
        <h1 className="text-lg font-semibold text-neutral-100">Settings</h1>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <nav className="w-44 flex-shrink-0 space-y-0.5">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setTab(id)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${tab === id ? 'bg-brand-600/20 text-brand-400' : 'text-neutral-400 hover:text-neutral-100 hover:bg-neutral-700/50'}`}>
              <Icon size={14} />{label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="flex-1 max-w-2xl">
          {/* Profile */}
          {tab === 'profile' && (
            <Card title="Profile Information">
              <div className="p-4 space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <Input label="First name" defaultValue={user?.first_name} placeholder="First name" />
                  <Input label="Last name"  defaultValue={user?.last_name}  placeholder="Last name"  />
                </div>
                <Input label="Username" defaultValue={user?.username} />
                <Input label="Email" defaultValue={user?.email} disabled className="opacity-60" />
                <Input label="Timezone" defaultValue={user?.timezone} />
                <Button>Save Changes</Button>
              </div>
            </Card>
          )}

          {/* Security */}
          {tab === 'security' && (
            <div className="space-y-4">
              <Card title="Two-Factor Authentication">
                <div className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-200">TOTP Authenticator</p>
                    <p className="text-xs text-neutral-400 mt-0.5">Use an authenticator app for extra security.</p>
                  </div>
                  <Badge variant={user?.is_2fa_enabled ? 'success' : 'default'}>
                    {user?.is_2fa_enabled ? 'ENABLED' : 'DISABLED'}
                  </Badge>
                </div>
              </Card>
              <Card title="Change Password">
                <div className="p-4 space-y-3">
                  <Input label="Current password" type="password" placeholder="••••••••" />
                  <Input label="New password"     type="password" placeholder="••••••••" />
                  <Input label="Confirm password" type="password" placeholder="••••••••" />
                  <Button>Change Password</Button>
                </div>
              </Card>
            </div>
          )}

          {/* Exchanges */}
          {tab === 'exchanges' && (
            <Card title="Connected Exchanges">
              <div className="p-4 space-y-3">
                {accounts.length === 0
                  ? <p className="text-sm text-neutral-400">No exchanges connected.</p>
                  : accounts.map((a: any) => (
                      <div key={a.id} className="flex items-center justify-between p-3 bg-neutral-700/50 rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-neutral-100">{a.label || a.exchange_name}</p>
                          <p className="text-xs text-neutral-400">{a.exchange_name} · {a.is_testnet ? 'Testnet' : 'Live'}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={a.connection_status === 'CONNECTED' ? 'success' : 'danger'}>{a.connection_status}</Badge>
                          <Button size="sm" variant="ghost" onClick={() => disconnectMutation.mutate(a.id)}>Remove</Button>
                        </div>
                      </div>
                    ))
                }
                <Button size="sm" variant="secondary">+ Connect Exchange</Button>
              </div>
            </Card>
          )}

          {/* Billing */}
          {tab === 'billing' && (
            <div className="space-y-4">
              {sub && (
                <Card title="Current Subscription">
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-semibold text-neutral-100">{sub.plan_name}</p>
                        <p className="text-xs text-neutral-400">{sub.status} · {sub.is_yearly ? 'Yearly' : 'Monthly'}</p>
                      </div>
                      <Badge variant={sub.is_active ? 'success' : 'danger'}>{sub.status}</Badge>
                    </div>
                    {sub.current_period_end && (
                      <p className="text-xs text-neutral-500 mt-2">
                        Renews: {new Date(sub.current_period_end).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </Card>
              )}
              <Card title="Available Plans">
                <div className="p-4 space-y-3">
                  {(plans as any[]).map((p: any) => (
                    <div key={p.id} className="flex items-center justify-between p-3 bg-neutral-700/50 rounded-lg">
                      <div>
                        <p className="text-sm font-medium text-neutral-100">{p.name}</p>
                        <p className="text-xs text-neutral-400">${p.price_monthly}/mo · {p.max_exchanges} exchanges</p>
                      </div>
                      <Button size="sm" variant={sub?.plan_tier === p.tier ? 'secondary' : 'primary'}>
                        {sub?.plan_tier === p.tier ? 'Current' : 'Upgrade'}
                      </Button>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {/* Appearance */}
          {tab === 'appearance' && (
            <Card title="Appearance">
              <div className="p-4 space-y-3">
                <p className="text-sm text-neutral-300">Theme</p>
                <div className="flex gap-2">
                  {['Dark', 'Light'].map(t => (
                    <button key={t} className={`px-4 py-2 rounded-lg text-sm border transition-colors ${t === 'Dark' ? 'border-brand-500 text-brand-400' : 'border-neutral-600 text-neutral-400 hover:border-neutral-500'}`}>
                      {t}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-neutral-500">High contrast mode coming in a future update.</p>
              </div>
            </Card>
          )}

          {/* Notifications */}
          {tab === 'notifications' && (
            <Card title="Notification Channels">
              <div className="p-4 space-y-4">
                {[['Email', 'Receive trade alerts via email'],['Telegram', 'Connect Telegram bot for instant alerts'],['Discord', 'Webhook integration for Discord'],['Slack', 'Webhook integration for Slack']].map(([ch, desc]) => (
                  <div key={ch} className="flex items-center justify-between py-2 border-b border-neutral-700 last:border-0">
                    <div>
                      <p className="text-sm font-medium text-neutral-200">{ch}</p>
                      <p className="text-xs text-neutral-400">{desc}</p>
                    </div>
                    <div className="w-10 h-5 bg-brand-600 rounded-full flex items-center justify-end pr-0.5 cursor-pointer">
                      <div className="w-4 h-4 bg-white rounded-full" />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
