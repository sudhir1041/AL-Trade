/**
 * AIInsightsPage.tsx  T16.8 ✅
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Brain, Zap } from 'lucide-react'
import { aiService, scannerService } from '@/services'
import { Card, Badge, DirectionBadge, ConfidenceBar, Spinner, EmptyState, Table, Tr, Td, Input } from '@/components/ui'

export function AIInsightsPage() {
  const [selected, setSelected] = useState<any>(null)
  const [search, setSearch] = useState('')

  const { data: histData, isLoading } = useQuery({
    queryKey: ['ai-history-full'],
    queryFn:  () => aiService.getHistory(undefined, 100),
    refetchInterval: 300_000,
  })

  const scores = (histData?.data?.data || []) as any[]
  const filtered = scores.filter((s: any) => !search || s.symbol?.includes(search.toUpperCase()))
  const tradeable = filtered.filter((s: any) => ['BUY','SELL'].includes(s.direction) && parseFloat(s.confidence_score) >= 75)

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={18} className="text-brand-400" />
          <div>
            <h1 className="text-lg font-semibold text-neutral-100">AI Insights</h1>
            <p className="text-xs text-neutral-400">{tradeable.length} high-confidence opportunities</p>
          </div>
        </div>
        <Input placeholder="Search symbol..." value={search} onChange={e => setSearch(e.target.value)} className="w-40" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Score list */}
        <div className="lg:col-span-2">
          <Card>
            {isLoading
              ? <div className="flex justify-center py-12"><Spinner /></div>
              : filtered.length === 0
                ? <EmptyState icon={<Brain size={28} />} title="No AI scores" message="Scores update every 5 minutes." />
                : <Table headers={['Symbol', 'Direction', 'Confidence', 'Risk', 'Regime', 'Strategies', 'Time']}>
                    {filtered.slice(0, 50).map((s: any) => (
                      <Tr key={s.id} onClick={() => setSelected(s)} className={selected?.id === s.id ? '!bg-brand-600/10' : ''}>
                        <Td className="font-medium text-neutral-100">{s.symbol}</Td>
                        <Td><DirectionBadge direction={s.direction} /></Td>
                        <Td className="w-32"><ConfidenceBar value={parseFloat(s.confidence_score)} /></Td>
                        <Td><Badge variant={s.risk_level === 'LOW' ? 'success' : s.risk_level === 'HIGH' ? 'danger' : 'warning'}>{s.risk_level}</Badge></Td>
                        <Td className="text-neutral-400 text-xs">{s.market_regime || '—'}</Td>
                        <Td className="text-neutral-400 text-xs">{(s.compatible_strategies || []).join(', ') || '—'}</Td>
                        <Td className="text-neutral-500 text-xs">{new Date(s.created_at).toLocaleTimeString()}</Td>
                      </Tr>
                    ))}
                  </Table>
            }
          </Card>
        </div>

        {/* Detail panel */}
        <div>
          {selected
            ? <Card title={`${selected.symbol} — AI Analysis`}>
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <DirectionBadge direction={selected.direction} />
                    <Badge variant={selected.risk_level === 'LOW' ? 'success' : selected.risk_level === 'HIGH' ? 'danger' : 'warning'}>
                      {selected.risk_level}
                    </Badge>
                  </div>

                  <div>
                    <p className="text-xs text-neutral-400 mb-1">Confidence Score</p>
                    <ConfidenceBar value={parseFloat(selected.confidence_score)} />
                  </div>

                  {selected.entry_zone_low && (
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="widget">
                        <p className="text-neutral-400">Entry Zone</p>
                        <p className="font-mono text-neutral-100">{parseFloat(selected.entry_zone_low).toFixed(4)}</p>
                      </div>
                      <div className="widget">
                        <p className="text-neutral-400">Stop Loss</p>
                        <p className="font-mono text-danger">{parseFloat(selected.stop_loss_suggest || 0).toFixed(4)}</p>
                      </div>
                      <div className="widget">
                        <p className="text-neutral-400">TP1</p>
                        <p className="font-mono text-success">{parseFloat(selected.tp1_suggest || 0).toFixed(4)}</p>
                      </div>
                      <div className="widget">
                        <p className="text-neutral-400">R/R Ratio</p>
                        <p className="font-mono text-neutral-100">{parseFloat(selected.risk_reward_ratio || 0).toFixed(2)}</p>
                      </div>
                    </div>
                  )}

                  <div>
                    <p className="text-xs text-neutral-400 mb-1">Supporting Factors</p>
                    <div className="flex flex-wrap gap-1">
                      {(selected.supporting_factors || []).map((f: string) => (
                        <Badge key={f} variant="success" className="text-[10px]">{f.replace(/_/g,' ')}</Badge>
                      ))}
                    </div>
                  </div>

                  {selected.conflicting_factors?.length > 0 && (
                    <div>
                      <p className="text-xs text-neutral-400 mb-1">Concerns</p>
                      <div className="flex flex-wrap gap-1">
                        {selected.conflicting_factors.map((f: string) => (
                          <Badge key={f} variant="warning" className="text-[10px]">{f.replace(/_/g,' ')}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <p className="text-xs text-neutral-400 mb-1">Reasoning</p>
                    <p className="text-xs text-neutral-300 leading-relaxed">{selected.reasoning}</p>
                  </div>

                  {Object.keys(selected.mtf_alignment || {}).length > 0 && (
                    <div>
                      <p className="text-xs text-neutral-400 mb-1">Multi-Timeframe</p>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(selected.mtf_alignment).map(([tf, trend]: any) => (
                          <Badge key={tf} variant={trend === 'BULLISH' ? 'success' : trend === 'BEARISH' ? 'danger' : 'default'} className="text-[10px]">
                            {tf}: {trend}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            : <Card>
                <EmptyState icon={<Zap size={24} />} title="Select a symbol" message="Click any row to see the full AI analysis." />
              </Card>
          }
        </div>
      </div>
    </div>
  )
}
