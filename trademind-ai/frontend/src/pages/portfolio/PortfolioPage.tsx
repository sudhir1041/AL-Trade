/**
 * PortfolioPage.tsx  T16.6 ✅
 */
import { useQuery } from '@tanstack/react-query'
import { Briefcase, TrendingUp, TrendingDown } from 'lucide-react'
import { portfolioService, orderService } from '@/services'
import { Card, Stat, Badge, Table, Tr, Td, Spinner, EmptyState } from '@/components/ui'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend } from 'recharts'
import { clsx } from 'clsx'

const COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316']

export function PortfolioPage() {
  const { data: portRes,  isLoading } = useQuery({ queryKey: ['portfolio'], queryFn: () => portfolioService.get(), refetchInterval: 30_000 })
  const { data: perfRes  } = useQuery({ queryKey: ['pnl-history'], queryFn: () => portfolioService.performance(30) })
  const { data: pnlRes   } = useQuery({ queryKey: ['pnl-totals'],  queryFn: () => portfolioService.pnl() })
  const { data: tradesRes } = useQuery({ queryKey: ['trade-history'], queryFn: () => orderService.getTradeHistory() })

  const portfolios  = portRes?.data?.data  || []
  const perfHistory = perfRes?.data?.data  || []
  const pnlSummary  = pnlRes?.data?.data   as any
  const trades      = tradesRes?.data?.data || []

  const totalBalance = portfolios.reduce((s: number, p: any) => s + parseFloat(p.total_balance || 0), 0)
  const allAssets    = portfolios.flatMap((p: any) => p.assets || [])
  const assetMap: Record<string, number> = {}
  allAssets.forEach((a: any) => { assetMap[a.asset] = (assetMap[a.asset] || 0) + parseFloat(a.value_usdt || 0) })
  const pieData = Object.entries(assetMap).map(([name, value]) => ({ name, value: +value.toFixed(2) }))

  const chartData = (perfHistory as any[]).map((d: any) => ({
    date:  d.date,
    value: parseFloat(d.portfolio_value || 0),
    pnl:   parseFloat(d.daily_pnl || 0),
  }))

  if (isLoading) return <div className="flex items-center justify-center h-40"><Spinner /></div>

  return (
    <div className="p-4 md:p-6 space-y-5">
      <div className="flex items-center gap-2">
        <Briefcase size={18} className="text-brand-400" />
        <h1 className="text-lg font-semibold text-neutral-100">Portfolio</h1>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Total Balance" value={`$${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} mono />
        <Stat label="Total PnL"     value={pnlSummary?.total_realized_pnl || '0.00'} mono />
        <Stat label="Win Rate"      value={`${pnlSummary?.overall_win_rate || 0}%`} />
        <Stat label="Total Trades"  value={pnlSummary?.total_trades || 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Performance chart */}
        <Card title="Portfolio Value (30d)" className="lg:col-span-2">
          <div className="p-4 h-48">
            {chartData.length === 0
              ? <EmptyState icon={<TrendingUp size={24} />} title="No history yet" message="Portfolio snapshots recorded daily." />
              : <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"   stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%"  stopColor="#3b82f6" stopOpacity={0}   />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                    <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#grad)" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
            }
          </div>
        </Card>

        {/* Allocation pie */}
        <Card title="Asset Allocation">
          <div className="p-4 h-48">
            {pieData.length === 0
              ? <EmptyState icon={<Briefcase size={24} />} title="No assets" message="Connect an exchange." />
              : <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" paddingAngle={2}>
                      {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} />
                    <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
            }
          </div>
        </Card>
      </div>

      {/* Trade history */}
      <Card title="Trade History">
        {trades.length === 0
          ? <EmptyState icon={<Briefcase size={24} />} title="No trades yet" message="Completed trades will appear here." />
          : <Table headers={['Symbol', 'Side', 'Qty', 'Fill Price', 'Exchange', 'Date']}>
              {(trades as any[]).slice(0, 20).map((t: any) => (
                <Tr key={t.id}>
                  <Td className="font-medium text-neutral-100">{t.symbol}</Td>
                  <Td><Badge variant={t.side === 'BUY' ? 'buy' : 'sell'}>{t.side}</Badge></Td>
                  <Td className="trading-value">{t.filled_quantity}</Td>
                  <Td className="trading-value">{t.average_fill_price ? parseFloat(t.average_fill_price).toFixed(4) : '—'}</Td>
                  <Td className="text-neutral-400">{t.exchange_name}</Td>
                  <Td className="text-neutral-500 text-xs">{t.filled_at ? new Date(t.filled_at).toLocaleDateString() : '—'}</Td>
                </Tr>
              ))}
            </Table>
        }
      </Card>
    </div>
  )
}
