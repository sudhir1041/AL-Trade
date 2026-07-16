/**
 * AdminPage.tsx  T16.11 ✅
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Shield, Users, Server, Activity, FileText, Settings2 } from 'lucide-react'
import { api } from '@/lib/api'
import { Card, Badge, Spinner, Table, Tr, Td, Stat } from '@/components/ui'

const TABS = [
  { id: 'overview', label: 'Overview',  icon: Activity },
  { id: 'users',    label: 'Users',     icon: Users    },
  { id: 'workers',  label: 'Workers',   icon: Server   },
  { id: 'queues',   label: 'Queues',    icon: Activity },
  { id: 'logs',     label: 'Audit Logs',icon: FileText },
  { id: 'settings', label: 'Settings',  icon: Settings2 },
]

export function AdminPage() {
  const [tab, setTab] = useState('overview')

  const { data: systemData } = useQuery({ queryKey: ['admin-system'],  queryFn: () => api.get('/admin/system/'),  enabled: tab === 'overview' })
  const { data: usersData  } = useQuery({ queryKey: ['admin-users'],   queryFn: () => api.get('/admin/users/'),   enabled: tab === 'users'    })
  const { data: workersData } = useQuery({ queryKey: ['admin-workers'],queryFn: () => api.get('/admin/workers/'), enabled: tab === 'workers'  })
  const { data: queuesData  } = useQuery({ queryKey: ['admin-queues'], queryFn: () => api.get('/admin/queues/'),  enabled: tab === 'queues'   })
  const { data: logsData    } = useQuery({ queryKey: ['admin-logs'],   queryFn: () => api.get('/admin/logs/'),    enabled: tab === 'logs'     })

  const sys     = systemData?.data?.data as any
  const users   = (usersData?.data?.data  || []) as any[]
  const workers = (workersData?.data?.data?.workers || []) as any[]
  const queues  = (queuesData?.data?.data?.queues   || []) as any[]
  const logs    = (logsData?.data?.data   || []) as any[]

  return (
    <div className="p-4 md:p-6">
      <div className="flex items-center gap-2 mb-6">
        <Shield size={18} className="text-brand-400" />
        <h1 className="text-lg font-semibold text-neutral-100">Admin Panel</h1>
      </div>

      <div className="flex gap-6">
        <nav className="w-44 flex-shrink-0 space-y-0.5">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setTab(id)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${tab === id ? 'bg-brand-600/20 text-brand-400' : 'text-neutral-400 hover:text-neutral-100 hover:bg-neutral-700/50'}`}>
              <Icon size={14} />{label}
            </button>
          ))}
        </nav>

        <div className="flex-1">
          {tab === 'overview' && sys && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <Stat label="Total Users"          value={sys.total_users} />
              <Stat label="Active Users"         value={sys.active_users} />
              <Stat label="Open Positions"       value={sys.open_positions} />
              <Stat label="Open Orders"          value={sys.open_orders} />
              <Stat label="Connected Exchanges"  value={sys.connected_exchanges} />
            </div>
          )}

          {tab === 'users' && (
            <Card title="All Users">
              <Table headers={['Email', 'Username', 'Role', 'Status', 'Joined']}>
                {users.map((u: any) => (
                  <Tr key={u.id}>
                    <Td className="text-neutral-100">{u.email}</Td>
                    <Td className="text-neutral-300">{u.username}</Td>
                    <Td><Badge variant="default">{u.role}</Badge></Td>
                    <Td><Badge variant={u.is_active ? 'success' : 'danger'}>{u.is_active ? 'ACTIVE' : 'INACTIVE'}</Badge></Td>
                    <Td className="text-neutral-500 text-xs">{new Date(u.date_joined).toLocaleDateString()}</Td>
                  </Tr>
                ))}
              </Table>
            </Card>
          )}

          {tab === 'workers' && (
            <Card title="Worker Status">
              <Table headers={['Worker', 'Active Tasks', 'Reserved', 'Status']}>
                {workers.length === 0
                  ? <Tr><Td className="text-neutral-400 py-4" colSpan={4 as any}>No workers online.</Td></Tr>
                  : workers.map((w: any) => (
                      <Tr key={w.worker}>
                        <Td className="font-mono text-xs text-neutral-200">{w.worker}</Td>
                        <Td>{w.active}</Td>
                        <Td>{w.reserved}</Td>
                        <Td><Badge variant="success">{w.status}</Badge></Td>
                      </Tr>
                    ))
                }
              </Table>
            </Card>
          )}

          {tab === 'queues' && (
            <Card title="Queue Status">
              <Table headers={['Queue', 'Size']}>
                {queues.map((q: any) => (
                  <Tr key={q.queue}>
                    <Td className="font-mono text-xs text-neutral-200">{q.queue}</Td>
                    <Td><Badge variant={q.size > 100 ? 'danger' : q.size > 10 ? 'warning' : 'success'}>{q.size}</Badge></Td>
                  </Tr>
                ))}
              </Table>
            </Card>
          )}

          {tab === 'logs' && (
            <Card title="Audit Logs">
              <Table headers={['Action', 'Resource', 'User', 'IP', 'Time']}>
                {logs.map((l: any) => (
                  <Tr key={l.id}>
                    <Td className="font-mono text-xs text-brand-400">{l.action}</Td>
                    <Td className="text-neutral-400 text-xs">{l.resource_type}</Td>
                    <Td className="text-neutral-400 text-xs font-mono">{l.user_id?.slice(0,8)}…</Td>
                    <Td className="text-neutral-500 text-xs">{l.ip_address || '—'}</Td>
                    <Td className="text-neutral-500 text-xs">{new Date(l.created_at).toLocaleString()}</Td>
                  </Tr>
                ))}
              </Table>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
