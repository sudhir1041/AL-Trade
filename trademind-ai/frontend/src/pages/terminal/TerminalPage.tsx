/**
 * TerminalPage.tsx  T16.5 ✅
 * Trading terminal with chart, order entry, positions, and AI overlay.
 */
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { LineChart, Zap, ShieldAlert } from 'lucide-react'
import { marketService, aiService, orderService } from '@/services'
import { Button, Badge, Card, DirectionBadge, ConfidenceBar, Spinner, Select, Input } from '@/components/ui'
import { useTicker } from '@/hooks/useTicker'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

const TIMEFRAMES = ['1m','5m','15m','1h','4h','1d'].map(v => ({ value: v, label: v }))

export function TerminalPage() {
  const { symbol: paramSymbol } = useParams()
  const qc = useQueryClient()

  const [symbol,    setSymbol]    = useState(paramSymbol || 'BTCUSDT')
  const [timeframe, setTimeframe] = useState('1h')
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY')
  const [orderType, setOrderType] = useState('MARKET')
  const [quantity,  setQuantity]  = useState('')
  const [price,     setPrice]     = useState('')
  const [sl,        setSL]        = useState('')
  const [tp,        setTP]        = useState('')

  const ticker = useTicker(symbol)

  const { data: aiData } = useQuery({
    queryKey: ['ai-score', symbol],
    queryFn:  () => aiService.getScore(symbol),
    refetchInterval: 300_000,
  })
  const { data: posData } = useQuery({
    queryKey: ['positions'],
    queryFn:  () => orderService.getPositions(),
    refetchInterval: 15_000,
  })

  const ai        = aiData?.data?.data as any
  const positions = (posData?.data?.data || []) as any[]
  const openPos   = positions.filter((p: any) => p.symbol === symbol)

  const orderMutation = useMutation({
    mutationFn: (d: any) => orderService.create(d),
    onSuccess: () => {
      toast.success(`${orderSide} order placed for ${symbol}`)
      qc.invalidateQueries({ queryKey: ['positions'] })
      setQuantity(''); setPrice(''); setSL(''); setTP('')
    },
    onError: (e: any) => toast.error(e.response?.data?.error?.message || 'Order failed.'),
  })

  const placeOrder = () => {
    if (!quantity) { toast.error('Enter quantity.'); return }
    orderMutation.mutate({
      trading_pair: symbol,
      side:         orderSide,
      order_type:   orderType,
      quantity:     parseFloat(quantity),
      price:        price     ? parseFloat(price) : undefined,
      stop_loss_price:   sl ? parseFloat(sl) : undefined,
      take_profit_price: tp ? parseFloat(tp) : undefined,
      is_paper_trade: true,
    })
  }

  return (
    <div className="h-full flex flex-col">
      {/* Top bar */}
      <div className="flex items-center gap-4 px-4 py-2 bg-neutral-800 border-b border-neutral-700">
        <div className="flex items-center gap-2">
          <LineChart size={16} className="text-brand-400" />
          <Input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} className="w-32 !py-1 uppercase" />
        </div>
        {ticker && (
          <div className="flex items-center gap-4 text-sm">
            <span className="font-mono font-semibold text-neutral-100">{parseFloat(ticker.price).toLocaleString()}</span>
            <span className={clsx('text-xs', parseFloat(ticker.change_24h_pct) >= 0 ? 'text-success' : 'text-danger')}>
              {parseFloat(ticker.change_24h_pct) >= 0 ? '+' : ''}{parseFloat(ticker.change_24h_pct).toFixed(2)}%
            </span>
            <span className="text-xs text-neutral-400">Vol: ${parseFloat(ticker.volume_24h || '0').toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
            <span className="text-xs text-neutral-400">H: {parseFloat(ticker.high_24h || '0').toLocaleString()}</span>
            <span className="text-xs text-neutral-400">L: {parseFloat(ticker.low_24h  || '0').toLocaleString()}</span>
          </div>
        )}
        <Select value={timeframe} onChange={e => setTimeframe(e.target.value)} options={TIMEFRAMES} className="ml-auto w-20 !py-1" />
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Chart area */}
        <div className="flex-1 bg-neutral-900 flex items-center justify-center border-r border-neutral-700">
          <div className="text-center text-neutral-500">
            <LineChart size={40} className="mx-auto mb-2 opacity-30" />
            <p className="text-sm">TradingView chart — integrate <code className="text-xs bg-neutral-800 px-1 rounded">lightweight-charts</code></p>
            <p className="text-xs mt-1 opacity-60">{symbol} · {timeframe}</p>
          </div>
        </div>

        {/* Right panel */}
        <div className="w-72 flex flex-col overflow-y-auto">
          {/* AI Recommendation */}
          {ai && (
            <Card title="AI Signal" className="m-3 rounded-widget">
              <div className="p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <DirectionBadge direction={ai.direction} />
                  <Badge variant={ai.risk_level === 'LOW' ? 'success' : ai.risk_level === 'HIGH' ? 'danger' : 'warning'}>
                    {ai.risk_level} risk
                  </Badge>
                </div>
                <ConfidenceBar value={parseFloat(ai.confidence_score)} />
                {ai.stop_loss_suggest && <div className="text-xs text-neutral-400">SL: <span className="text-danger font-mono">{parseFloat(ai.stop_loss_suggest).toFixed(4)}</span></div>}
                {ai.tp1_suggest       && <div className="text-xs text-neutral-400">TP1: <span className="text-success font-mono">{parseFloat(ai.tp1_suggest).toFixed(4)}</span></div>}
                {ai.reasoning && <p className="text-xs text-neutral-400 leading-relaxed border-t border-neutral-700 pt-2 mt-2">{ai.reasoning}</p>}
              </div>
            </Card>
          )}

          {/* Order entry */}
          <Card title="Place Order" className="m-3 rounded-widget">
            <div className="p-3 space-y-3">
              {/* BUY/SELL toggle */}
              <div className="flex rounded-lg overflow-hidden border border-neutral-600">
                <button onClick={() => setOrderSide('BUY')}
                  className={clsx('flex-1 py-1.5 text-xs font-semibold transition-colors',
                    orderSide === 'BUY' ? 'bg-success text-white' : 'text-neutral-400 hover:bg-neutral-700')}>
                  BUY / LONG
                </button>
                <button onClick={() => setOrderSide('SELL')}
                  className={clsx('flex-1 py-1.5 text-xs font-semibold transition-colors',
                    orderSide === 'SELL' ? 'bg-danger text-white' : 'text-neutral-400 hover:bg-neutral-700')}>
                  SELL / SHORT
                </button>
              </div>
              <Select value={orderType} onChange={e => setOrderType(e.target.value)}
                options={[{ value:'MARKET',label:'Market'},{value:'LIMIT',label:'Limit'},{value:'STOP_LIMIT',label:'Stop Limit'}]} />
              <Input label="Quantity" type="number" placeholder="0.001" value={quantity} onChange={e => setQuantity(e.target.value)} />
              {orderType !== 'MARKET' && <Input label="Price" type="number" placeholder="0.00" value={price} onChange={e => setPrice(e.target.value)} />}
              <Input label="Stop Loss" type="number" placeholder="0.00" value={sl} onChange={e => setSL(e.target.value)} />
              <Input label="Take Profit" type="number" placeholder="0.00" value={tp} onChange={e => setTP(e.target.value)} />
              <Button variant={orderSide === 'BUY' ? 'buy' : 'sell'} className="w-full" loading={orderMutation.isPending} onClick={placeOrder}>
                {orderSide} {symbol} (Paper)
              </Button>
            </div>
          </Card>

          {/* Open positions for this symbol */}
          {openPos.length > 0 && (
            <Card title={`Positions (${openPos.length})`} className="m-3 rounded-widget">
              <div className="p-3 space-y-2">
                {openPos.map((p: any) => (
                  <div key={p.id} className="text-xs border border-neutral-700 rounded-lg p-2 space-y-1">
                    <div className="flex items-center justify-between">
                      <Badge variant={p.side === 'LONG' ? 'buy' : 'sell'}>{p.side}</Badge>
                      <span className={clsx('font-mono', p.pnl_pct >= 0 ? 'text-success' : 'text-danger')}>
                        {p.pnl_pct >= 0 ? '+' : ''}{p.pnl_pct.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-neutral-400">
                      <span>Qty: {p.quantity}</span>
                      <span>Entry: {parseFloat(p.entry_price).toFixed(4)}</span>
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
