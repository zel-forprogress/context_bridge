import { useEffect } from 'react'

// 简单的事件系统，用于配置同步
type ConfigSyncListener = () => void

const listeners: Set<ConfigSyncListener> = new Set()

export function notifyConfigChanged() {
  listeners.forEach((listener) => listener())
}

export function useConfigSync(onConfigChanged: () => void) {
  useEffect(() => {
    listeners.add(onConfigChanged)
    return () => {
      listeners.delete(onConfigChanged)
    }
  }, [onConfigChanged])
}
