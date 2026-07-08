/**
 * hooks/useTicker.ts
 * T4.2 ✅  Live ticker via WebSocket with REST fallback.
 */
import { useState, useEffect } from 'react'
import { useWebSocket }  from './useWebSocket'
import { marketService } from '@/services'
import type { Ticker }   from '@/types'

export function useTicker(symbol: string) {
  const [ticker, setTicker] = useState<Ticker | null>(null)

  // Initial REST fetch
  useEffect(() => {
    if (!symbol) return
    marketService.getTicker(symbol)
      .then(r => setTicker(r.data.data))
      .catch(() => {})
  }, [symbol])

  // Live WS updates
  useWebSocket(`/ws/market/ticker/${symbol}/`, {
    requireAuth: false,
    onMessage: (data: any) => {
      if (data?.event === 'market.ticker' && data.symbol === symbol) {
        setTicker(prev => ({ ...prev, ...data.payload }))
      }
    },
  })

  return ticker
}
