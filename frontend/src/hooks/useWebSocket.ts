import { useEffect, useRef } from 'react'
import useAlertStore, { Alert } from '../store/alertStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts'

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const { addAlert, updateAlertStatus } = useAlertStore()

  useEffect(() => {
    const connect = () => {
      try {
        wsRef.current = new WebSocket(WS_URL)

        wsRef.current.onopen = () => {
          console.log('[WS] Connected to CascadeIQ alert stream')
          // Heartbeat
          const heartbeat = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send('ping')
            } else {
              clearInterval(heartbeat)
            }
          }, 30_000)
        }

        wsRef.current.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'ALERT') {
              addAlert(msg.data as Alert)
            } else if (msg.type === 'ALERT_STATUS_CHANGED') {
              updateAlertStatus(msg.data.alert_id, msg.data.status)
            }
          } catch (e) {
            // ignore non-JSON (e.g., pong)
          }
        }

        wsRef.current.onclose = () => {
          console.log('[WS] Disconnected — reconnecting in 5s…')
          setTimeout(connect, 5_000)
        }

        wsRef.current.onerror = (e) => {
          console.warn('[WS] Error', e)
          wsRef.current?.close()
        }
      } catch (e) {
        console.warn('[WS] Connection failed, retrying in 5s', e)
        setTimeout(connect, 5_000)
      }
    }

    connect()
    return () => { wsRef.current?.close() }
  }, [addAlert, updateAlertStatus])

  return wsRef
}
