import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Shield, Link, Bell, Palette, Key, LogOut } from 'lucide-react'
import { api } from '@/lib/api'
import { Card, Button, Input, Badge, Spinner } from '@/components/ui'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'profile',    label: 'Profile',    icon: Settings },
  { id: 'security',   label: 'Security',   icon: Shield   },
  { id: 'exchanges',  label: 'Exchanges',  icon: Link     },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'appearance', label: 'Appearance', icon: Palette  },
  { id: 'billing',    label: 'Billing',    icon: Key      },
]

export function SettingsPage() {
  const [tab, setTab] = useState('profile')
  const queryClient = useQueryClient()

  // Queries
  const { data: profileData } = useQuery({ queryKey: ['profile'], queryFn: () => api.get('/auth/me/') })
  const { data: accountsData } = useQuery({ queryKey: ['exchange-accounts'], queryFn: () => api.get('/exchanges/accounts/') })
  const { data: subData } = useQuery({ queryKey: ['subscription'], queryFn: () => api.get('/billing/subscription/') })

  const user = profileData?.data?.data
  const accounts = (accountsData?.data?.data || []) as any[]
  const sub = subData?.data?.data

  // Custom mock state for Mudrex integration
  const [mudrexSecret, setMudrexSecret] = useState('')
  const [mudrexConnected, setMudrexConnected] = useState(false)

  // Mutations
  const updateProfile = useMutation({
    mutationFn: (data: any) => api.patch('/auth/me/', data),
    onSuccess: () => {
      toast.success('Profile updated successfully')
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    }
  })

  const disconnectMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/exchanges/accounts/${id}/`),
    onSuccess: () => {
      toast.success('Exchange disconnected')
      queryClient.invalidateQueries({ queryKey: ['exchange-accounts'] })
    }
  })

  if (!user) return <div className="p-8 flex justify-center"><Spinner /></div>

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-neutral-100">Settings</h1>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Navigation Sidebar */}
        <nav className="w-full md:w-56 flex-shrink-0 space-y-1">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
                tab === id
                  ? 'bg-brand-600/20 text-brand-400 font-medium'
                  : 'text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800'
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
          <div className="pt-4 mt-4 border-t border-neutral-800">
            <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-red-400 hover:bg-red-500/10 transition-colors">
              <LogOut size={16} />
              Sign Out
            </button>
          </div>
        </nav>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          {/* Profile */}
          {tab === 'profile' && (
            <div className="space-y-6">
              <Card title="Personal Information">
                <form className="p-4 space-y-4" onSubmit={(e) => { e.preventDefault(); updateProfile.mutate({ first_name: (e.target as any).first_name.value }) }}>
                  <div className="grid grid-cols-2 gap-4">
                    <Input label="First Name" name="first_name" defaultValue={user.first_name} />
                    <Input label="Last Name" name="last_name" defaultValue={user.last_name} />
                  </div>
                  <Input label="Email Address" type="email" value={user.email} disabled />
                  <Input label="Timezone" defaultValue="UTC" disabled />
                  <div className="flex justify-end pt-2">
                    <Button type="submit" disabled={updateProfile.isPending}>
                      {updateProfile.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </div>
                </form>
              </Card>
            </div>
          )}

          {/* Exchanges */}
          {tab === 'exchanges' && (
            <div className="space-y-4">
              <Card title="Connected Exchanges">
                <div className="p-4 space-y-3">
                  {accounts.length === 0 && !mudrexConnected
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
                  {mudrexConnected && (
                    <div className="flex items-center justify-between p-3 bg-neutral-700/50 rounded-lg border border-brand-500/30">
                        <div>
                          <p className="text-sm font-medium text-neutral-100">Mudrex Integration (Live)</p>
                          <p className="text-xs text-brand-400 mt-1 flex items-center gap-1">
                             <Shield size={12} /> All Premium Features Enabled
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="success">CONNECTED</Badge>
                          <Button size="sm" variant="ghost" onClick={() => {
                              setMudrexConnected(false);
                              setMudrexSecret('');
                              toast.success('Mudrex integration disconnected');
                          }}>Remove</Button>
                        </div>
                    </div>
                  )}
                  {!mudrexConnected && (
                    <div className="mt-4 pt-4 border-t border-neutral-700">
                      <h3 className="text-sm font-medium mb-3">Add Mudrex Integration</h3>
                      <div className="flex gap-2 items-end">
                        <div className="flex-1">
                           <Input
                              label="Mudrex API Secret (X-Authentication)"
                              type="password"
                              placeholder="Enter your Mudrex API Secret..."
                              value={mudrexSecret}
                              onChange={(e) => setMudrexSecret(e.target.value)}
                           />
                        </div>
                        <Button
                            onClick={() => {
                                if(mudrexSecret.length > 5) {
                                    setMudrexConnected(true);
                                    toast.success('Mudrex successfully connected! All features activated.');
                                } else {
                                    toast.error('Invalid API Secret');
                                }
                            }}
                        >Connect Mudrex</Button>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Billing */}
          {tab === 'billing' && (
            <div className="space-y-4">
              {sub && (
                <Card title="Current Subscription">
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-lg font-bold text-neutral-100">{sub.plan.name}</p>
                        <p className="text-sm text-neutral-400">
                          {sub.status === 'active' ? 'Renews on' : 'Expires on'} {new Date(sub.current_period_end).toLocaleDateString()}
                        </p>
                      </div>
                      <Badge variant={sub.status === 'active' ? 'success' : 'warning'}>
                        {sub.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* Notifications */}
          {tab === 'notifications' && (
            <Card title="Notification Preferences">
              <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-100">Trade Executions</p>
                    <p className="text-xs text-neutral-400">Receive alerts when orders are filled.</p>
                  </div>
                  <Badge variant="success">Enabled</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-100">Risk Alerts</p>
                    <p className="text-xs text-neutral-400">Alerts for liquidations or high margin usage.</p>
                  </div>
                  <Badge variant="success">Enabled</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-100">System Errors</p>
                    <p className="text-xs text-neutral-400">Important system or connection errors.</p>
                  </div>
                  <Badge variant="success">Enabled</Badge>
                </div>
              </div>
            </Card>
          )}

        </div>
      </div>
    </div>
  )
}
