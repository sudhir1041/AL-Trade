/**
 * ReportsPage.tsx  T16.9 ✅
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { BarChart3, Plus, RefreshCw, Download, Trash2 } from 'lucide-react'
import { reportService } from '@/services'
import { Card, Badge, Button, Spinner, EmptyState, Table, Tr, Td } from '@/components/ui'
import toast from 'react-hot-toast'

const STATUS_COLORS: Record<string, 'success'|'warning'|'danger'|'default'> = {
  READY: 'success', GENERATING: 'warning', FAILED: 'danger', PENDING: 'default'
}

export function ReportsPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState('ALL')

  const { data: reportsRes, isLoading } = useQuery({
    queryKey: ['reports', tab],
    queryFn:  () => reportService.list(tab === 'ALL' ? undefined : tab),
  })

  const generateMutation = useMutation({
    mutationFn: (type: string) => reportService.generate({ report_type: type }),
    onSuccess: () => { toast.success('Report generation queued.'); qc.invalidateQueries({ queryKey: ['reports'] }) },
    onError:   () => toast.error('Failed to generate report.'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => reportService.delete(id),
    onSuccess: () => { toast.success('Deleted.'); qc.invalidateQueries({ queryKey: ['reports'] }) },
  })

  const reports  = (reportsRes?.data?.data || []) as any[]
  const TABS = ['ALL','DAILY','WEEKLY','MONTHLY','TRADE_JOURNAL','STRATEGY','TAX']

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 size={18} className="text-brand-400" />
          <h1 className="text-lg font-semibold text-neutral-100">Reports & Analytics</h1>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => qc.invalidateQueries({ queryKey: ['reports'] })}><RefreshCw size={13} /></Button>
          <Button size="sm" loading={generateMutation.isPending} onClick={() => generateMutation.mutate('DAILY')}>
            <Plus size={13} /> Daily Report
          </Button>
        </div>
      </div>

      {/* Quick generate */}
      <div className="flex flex-wrap gap-2">
        {['WEEKLY','MONTHLY','TRADE_JOURNAL','TAX'].map(type => (
          <Button key={type} size="sm" variant="secondary" loading={generateMutation.isPending} onClick={() => generateMutation.mutate(type)}>
            <Plus size={11} /> {type.replace('_', ' ')}
          </Button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 flex-wrap">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${tab === t ? 'bg-brand-600 text-white' : 'bg-neutral-800 text-neutral-400 hover:text-neutral-100 border border-neutral-700'}`}>
            {t}
          </button>
        ))}
      </div>

      <Card>
        {isLoading
          ? <div className="flex justify-center py-12"><Spinner /></div>
          : reports.length === 0
            ? <EmptyState icon={<BarChart3 size={28} />} title="No reports" message="Generate a report to see your trading analytics." />
            : <Table headers={['Title', 'Type', 'Status', 'Generated', 'Actions']}>
                {reports.map((r: any) => (
                  <Tr key={r.id}>
                    <Td className="font-medium text-neutral-100">{r.title}</Td>
                    <Td><Badge variant="default">{r.report_type}</Badge></Td>
                    <Td><Badge variant={STATUS_COLORS[r.status]}>{r.status}</Badge></Td>
                    <Td className="text-neutral-400 text-xs">{r.generated_at ? new Date(r.generated_at).toLocaleString() : '—'}</Td>
                    <Td>
                      <div className="flex gap-1">
                        {r.status === 'READY' && (
                          <Button size="sm" variant="secondary" onClick={() => toast('Download not yet wired to file export.')}>
                            <Download size={11} />
                          </Button>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => { if (confirm('Delete report?')) deleteMutation.mutate(r.id) }}>
                          <Trash2 size={11} className="text-danger" />
                        </Button>
                      </div>
                    </Td>
                  </Tr>
                ))}
              </Table>
        }
      </Card>

      {/* Summary data for READY reports */}
      {reports.filter((r: any) => r.status === 'READY' && r.data?.net_pnl !== undefined).slice(0,1).map((r: any) => (
        <Card key={r.id} title={r.title}>
          <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {[
              ['Total Trades',  r.data.total_trades],
              ['Win Rate',      `${r.data.win_rate_pct}%`],
              ['Net PnL',       `$${r.data.net_pnl}`],
              ['Profit Factor', r.data.profit_factor],
              ['Sharpe Ratio',  r.data.sharpe_ratio],
              ['Max Drawdown',  `${r.data.max_drawdown_pct}%`],
            ].map(([label, val]) => (
              <div key={label as string}>
                <p className="text-xs text-neutral-400">{label}</p>
                <p className="font-semibold text-neutral-100 font-mono">{val}</p>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  )
}
