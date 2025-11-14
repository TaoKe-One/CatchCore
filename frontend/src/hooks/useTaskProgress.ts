/**
 * Custom hook for real-time task progress tracking via WebSocket
 */

import { useEffect, useState, useCallback, useRef } from 'react'

export interface TaskLog {
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  message: string
}

export interface TaskProgress {
  progress: number
  step?: string
}

export interface TaskResult {
  [key: string]: any
}

export interface TaskStatus {
  task_id: number
  name: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress: number
  current_step?: string
  total_steps?: number
  started_at?: string
  completed_at?: string
}

export interface WebSocketMessage {
  type: 'status' | 'progress' | 'log' | 'result' | 'error' | 'complete' | 'logs' | 'pong'
  timestamp: string
  data: any
}

export const useTaskProgress = (taskId: number, autoConnect: boolean = true) => {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [status, setStatus] = useState<TaskStatus | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [logs, setLogs] = useState<TaskLog[]>([])
  const [results, setResults] = useState<TaskResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isCompleted, setIsCompleted] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (reconnectAttempts.current >= maxReconnectAttempts) {
      setError('Failed to connect after multiple attempts')
      return
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/task/${taskId}`

      const socket = new WebSocket(wsUrl)

      socket.onopen = () => {
        console.log(`WebSocket connected for task ${taskId}`)
        setIsConnected(true)
        setError(null)
        reconnectAttempts.current = 0
        wsRef.current = socket
        setWs(socket)
      }

      socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      socket.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection error')
      }

      socket.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        wsRef.current = null

        // Attempt to reconnect
        if (status?.status === 'running' || status?.status === 'paused') {
          reconnectAttempts.current += 1
          const backoffMs = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
          setTimeout(connect, backoffMs)
        }
      }
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }
  }, [taskId, status?.status])

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'status':
        setStatus(message.data as TaskStatus)
        if (message.data.status === 'completed' || message.data.status === 'failed' || message.data.status === 'cancelled') {
          setIsCompleted(true)
        }
        break

      case 'progress': {
        const progressData = message.data as TaskProgress
        setProgress(progressData.progress)
        // Update status with current step if available
        setStatus((prev) =>
          prev ? { ...prev, progress: progressData.progress, current_step: progressData.step } : null
        )
        break
      }

      case 'log': {
        const logData = message.data as TaskLog
        setLogs((prev) => [...prev, logData])
        break
      }

      case 'logs': {
        // Initial logs load
        const logsArray = Array.isArray(message.data) ? message.data : [message.data]
        setLogs(logsArray)
        break
      }

      case 'result': {
        const resultData = message.data as TaskResult
        setResults((prev) => [...prev, resultData])
        break
      }

      case 'error': {
        const errorData = message.data as { error: string }
        setError(errorData.error)
        break
      }

      case 'complete': {
        const completeData = message.data as { status: string }
        setIsCompleted(true)
        setStatus((prev) =>
          prev ? { ...prev, status: completeData.status as any, progress: 100 } : null
        )
        break
      }

      case 'pong':
        // Health check response, do nothing
        break

      default:
        console.warn(`Unknown message type: ${message.type}`)
    }
  }

  const sendMessage = useCallback((message: string | object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message)
      wsRef.current.send(data)
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const healthCheck = useCallback(() => {
    sendMessage('ping')
  }, [sendMessage])

  const requestStatus = useCallback(() => {
    sendMessage('status')
  }, [sendMessage])

  const requestLogs = useCallback(() => {
    sendMessage('logs')
  }, [sendMessage])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setWs(null)
      setIsConnected(false)
    }
  }, [])

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect && !isConnected) {
      connect()
    }

    return () => {
      // Don't auto-disconnect on unmount to allow component remount
    }
  }, [autoConnect, taskId])

  // Periodic health check
  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(() => {
      healthCheck()
    }, 30000) // Every 30 seconds

    return () => clearInterval(interval)
  }, [isConnected, healthCheck])

  return {
    isConnected,
    status,
    progress,
    logs,
    results,
    error,
    isCompleted,
    ws,
    connect,
    disconnect,
    sendMessage,
    healthCheck,
    requestStatus,
    requestLogs,
  }
}
