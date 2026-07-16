/**
 * DashboardPage.tsx  T16.3 ✅
 */
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, Activity, Shield, Zap, AlertTriangle } from 'lucide-react'
import { portfolioService, orderService, riskService, scannerService, aiService } from '@/services'
import { Card, Stat, Badge, DirectionBadge, ConfidenceBar, Skeleton, EmptyState, Table, Tr, Td } from '@/components/ui'
import { clsx } from 'clsx'

export function DashboardPage() {
  const { data: portfolioRes, isLoading: pLoad } = useQuery({
    queryKey: ['portfolio'],
    queryFn:  () => portfolioService.get(),
    refetchInterval: 30_000,
  })
  const { data: positionsRes } = useQuery({
    queryKey: ['positions'],
    queryFn:  () => orderService.getPositions(),
    refetchInterval: 15_000,
  })
  const { data: riskRes }    = useQuery({ queryKey: ['risk-limits'],   queryFn: () => riskService.getLimits() })
  const { data: candidatesRes } = useQuery({ queryKey: ['candidates'], queryFn: () => scannerService.getCandidates(), refetchInterval: 60_000 })
  const { data: aiHistoryRes }  = useQuery({ queryKey: ['ai-history'], queryFn: () => aiService.getHistory(undefined, 10), refetchInterval: 60_000 })

  const portfolios  = portfolioRes?.data?.data  || []
  const positions   = positionsRes?.data?.data  || []
  const candidates  = candidatesRes?.data?.data || []
  const aiScores    = aiHistoryRes?.data?.data  || []
  const risk        = riskRes?.data?.data

  const totalBalance = portfolios.reduce((s: number, p: any) => s + parseFloat(p.total_balance || 0), 0)
  const totalPnL     = portfolios.reduce((s: number, p: any) => s + parseFloat(p.unrealized_pnl || 0), 0)

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-neutral-100">Dashboard</h1>
          <p className="text-xs text-neutral-400">Live portfolio overview</p>
        </div>
        <Badge variant={totalPnL >= 0 ? 'success' : 'danger'}>
          {totalPnL >= 0 ? <TrendingUp size={10} className="mr-1" /> : <TrendingDown size={10} className="mr-1" />}
          {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)} USDT
        </Badge>
      </div>

      {/* ── Stats row ──────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {pLoad ? Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-20" />) : <>
          <Stat label="Total Balance"    value={`$${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} mono />
          <Stat label="Unrealized PnL"   value={`${totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}`} change={totalBalance > 0 ? (totalPnL / totalBalance * 100) : 0} mono />
          <Stat label="Open Positions"   value={positions.length} />
          <Stat label="Scanner Candidates" value={candidates.length} />
        </>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* ── Open Positions ───────────────────────────── */}
        <Card title="Open Positions" className="lg:col-span-2">
          {positions.length === 0
            ? <EmptyState icon={<Activity size={24} />} title="No open positions" message="Your active positions will appear here." />
            : <Table headers={['Symbol', 'Side', 'Entry', 'Current', 'PnL', 'PnL%']}>
                {positions.slice(0, 8).map((p: any) => {
                  const pnl    = parseFloat(p.unrealized_pnl)
                  const pnlPct = p.pnl_pct
                  return (
                    <Tr key={p.id}>
                      <Td><span className="font-medium text-neutral-100">{p.symbol}</span></Td>
                      <Td><Badge variant={p.side === 'LONG' ? 'buy' : 'sell'}>{p.side}</Badge></Td>
                      <Td className="trading-value">{parseFloat(p.entry_price).toFixed(4)}</Td>
                      <Td className="trading-value">{parseFloat(p.current_price).toFixed(4)}</Td>
                      <Td className={clsx('trading-value', pnl >= 0 ? 'text-success' : 'text-danger')}>
                        {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
                      </Td>
                      <Td className={clsx('trading-value', pnlPct >= 0 ? 'text-success' : 'text-danger')}>
                        {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
                      </Td>
                    </Tr>
                  )
                })}
              </Table>
          }
        </Card>

        {/* ── AI Top Opportunities ─────────────────────── */}
        <Card title="AI Opportunities">
          {aiScores.length === 0
            ? <EmptyState icon={<Zap size={24} />} title="No signals yet" message="AI scores update every 5 minutes." />
            : <div className="p-3 space-y-3">
                {aiScores.filter((s: any) => ['BUY','SELL'].includes(s.direction)).slice(0, 6).map((s: any) => (
                  <div key={s.id} className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-neutral-100">{s.symbol}</span>
                        <DirectionBadge direction={s.direction} />
                      </div>
                      <ConfidenceBar value={parseFloat(s.confidence_score)} />
                    </div>
                    <Badge variant={s.risk_level === 'LOW' ? 'success' : s.risk_level === 'HIGH' ? 'danger' : 'warning'}>
                      {s.risk_level}
                    </Badge>
                  </div>
                ))}
              </div>
          }
        </Card>
      </div>

      {/* ── Risk Status ───────────────────────────────────── */}
      {risk && (
        <Card title="Risk Status">
          <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-neutral-400 mb-1">Daily Loss Limit</p>
              <p className="text-sm font-semibold text-neutral-100">{risk.limits?.max_daily_loss_pct}%</p>
              {risk.current_usage?.daily_limit_reached && <Badge variant="danger" className="mt-1">LIMIT REACHED</Badge>}
            </div>
            <div>
              <p className="text-xs text-neutral-400 mb-1">Trades Today</p>
              <p className="text-sm font-semibold text-neutral-100">{risk.current_usage?.trades_today || 0}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400 mb-1">Max Open Positions</p>
              <p className="text-sm font-semibold text-neutral-100">{positions.length} / {risk.limits?.max_open_positions}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400 mb-1">Max Drawdown</p>
              <p className="text-sm font-semibold text-neutral-100">{risk.limits?.max_drawdown_pct}%</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
