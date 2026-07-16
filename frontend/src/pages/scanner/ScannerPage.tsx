/**
 * ScannerPage.tsx  T16.4 ✅
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Radar, Play, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { scannerService } from '@/services'
import { Button, Badge, Card, ConfidenceBar, Spinner, EmptyState, Input, Select, Table, Tr, Td } from '@/components/ui'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

const TREND_ICONS: Record<string, React.ReactNode> = {
  BULLISH:  <TrendingUp  size={12} className="text-success" />,
  BEARISH:  <TrendingDown size={12} className="text-danger"  />,
  SIDEWAYS: <Minus        size={12} className="text-neutral-400" />,
}

export function ScannerPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [minConf, setMinConf] = useState('0')
  const [trend,   setTrend]   = useState('ALL')

  const { data: resData, isLoading } = useQuery({
    queryKey: ['scanner-results'],
    queryFn:  () => scannerService.getResults(100),
    refetchInterval: 60_000,
  })
  const { data: statusData } = useQuery({
    queryKey: ['scanner-status'],
    queryFn:  () => scannerService.getStatus(),
    refetchInterval: 30_000,
  })

  const runMutation = useMutation({
    mutationFn: () => scannerService.run(),
    onSuccess:  () => { toast.success('Scan triggered!'); setTimeout(() => qc.invalidateQueries({ queryKey: ['scanner-results'] }), 5000) },
    onError:    () => toast.error('Failed to trigger scan.'),
  })

  const results = (resData?.data?.data || []) as any[]
  const status  = statusData?.data?.data as any

  const filtered = results.filter(r => {
    if (search && !r.symbol?.includes(search.toUpperCase())) return false
    if (parseFloat(r.confidence_score) < parseFloat(minConf)) return false
    if (trend !== 'ALL' && r.trend_direction !== trend) return false
    return true
  })

  return (
    <div className="p-4 md:p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radar size={18} className="text-brand-400" />
          <div>
            <h1 className="text-lg font-semibold text-neutral-100">Market Scanner</h1>
            <p className="text-xs text-neutral-400">
              {status?.status === 'COMPLETED'
                ? `${status.pairs_scanned} pairs scanned — ${status.candidates_found} candidates`
                : 'Scanning...'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => qc.invalidateQueries({ queryKey: ['scanner-results'] })}>
            <RefreshCw size={13} />
          </Button>
          <Button size="sm" loading={runMutation.isPending} onClick={() => runMutation.mutate()}>
            <Play size={13} /> Run Scan
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="p-3 flex flex-wrap gap-3">
          <Input placeholder="Search symbol..." value={search} onChange={e => setSearch(e.target.value)} className="w-40" />
          <Input type="number" placeholder="Min score" value={minConf} onChange={e => setMinConf(e.target.value)} className="w-28" />
          <Select
            value={trend}
            onChange={e => setTrend(e.target.value)}
            options={[
              { value: 'ALL',      label: 'All Trends' },
              { value: 'BULLISH',  label: 'Bullish'    },
              { value: 'BEARISH',  label: 'Bearish'    },
              { value: 'SIDEWAYS', label: 'Sideways'   },
            ]}
            className="w-36"
          />
          <span className="text-xs text-neutral-400 self-center">{filtered.length} results</span>
        </div>
      </Card>

      {/* Results table */}
      <Card>
        {isLoading
          ? <div className="flex justify-center py-12"><Spinner /></div>
          : filtered.length === 0
            ? <EmptyState icon={<Radar size={28} />} title="No results" message="Run a scan or adjust your filters." />
            : <Table headers={['Symbol', 'Exchange', 'Confidence', 'Risk', 'Trend', 'Volume', 'Volume Spike', 'Status']}>
                {filtered.map((r: any) => (
                  <Tr key={r.id}>
                    <Td><span className="font-medium text-neutral-100">{r.symbol}</span></Td>
                    <Td className="text-neutral-400">{r.exchange_name}</Td>
                    <Td className="w-36"><ConfidenceBar value={parseFloat(r.confidence_score)} /></Td>
                    <Td>
                      <Badge variant={parseFloat(r.risk_score) < 30 ? 'success' : parseFloat(r.risk_score) < 60 ? 'warning' : 'danger'}>
                        {parseFloat(r.risk_score).toFixed(0)}
                      </Badge>
                    </Td>
                    <Td>
                      <div className="flex items-center gap-1">
                        {TREND_ICONS[r.trend_direction]}
                        <span className={clsx('text-xs', r.trend_direction === 'BULLISH' ? 'text-success' : r.trend_direction === 'BEARISH' ? 'text-danger' : 'text-neutral-400')}>
                          {r.trend_direction}
                        </span>
                      </div>
                    </Td>
                    <Td className="trading-value text-neutral-300">${parseFloat(r.volume_24h_usdt || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}</Td>
                    <Td>{r.volume_spike ? <Badge variant="warning">SPIKE</Badge> : <span className="text-neutral-500 text-xs">—</span>}</Td>
                    <Td>{r.is_candidate ? <Badge variant="success">CANDIDATE</Badge> : <Badge variant="default">FILTERED</Badge>}</Td>
                  </Tr>
                ))}
              </Table>
        }
      </Card>
    </div>
  )
}
