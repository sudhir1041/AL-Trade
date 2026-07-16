/**
 * hooks/useWebSocket.ts
 * T4.2 ✅  Generic WebSocket hook with auto-reconnect.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { createWebSocket } from '@/lib/api'

interface Options {
  onMessage?: (data: unknown) => void
  onOpen?:    () => void
  onClose?:   () => void
  requireAuth?: boolean
  reconnectMs?: number
}

export function useWebSocket(path: string, options: Options = {}) {
  const { accessToken } = useAuthStore()
  const wsRef           = useRef<WebSocket | null>(null)
  const timerRef        = useRef<ReturnType<typeof setTimeout>>()
  const [connected, setConnected] = useState(false)
  const { onMessage, onOpen, onClose, requireAuth = true, reconnectMs = 3000 } = options

  const connect = useCallback(() => {
    if (requireAuth && !accessToken) return
    const ws = createWebSocket(path, requireAuth ? accessToken! : undefined)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      onOpen?.()
    }
    ws.onmessage = (e) => {
      try { onMessage?.(JSON.parse(e.data)) } catch {}
    }
    ws.onclose = () => {
      setConnected(false)
      onClose?.()
      // Auto-reconnect
      timerRef.current = setTimeout(connect, reconnectMs)
    }
    ws.onerror = () => ws.close()
  }, [path, accessToken, requireAuth, reconnectMs, onMessage, onOpen, onClose])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(timerRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { connected, send }
}
