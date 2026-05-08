import { useState, useEffect, useCallback, useRef } from 'react'
import i18n from '../i18n'

export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = [], enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const load = useCallback(async () => {
    if (!enabled) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await fetcherRef.current()
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : i18n.t('error.unknown'))
    } finally {
      setLoading(false)
    }
  }, [enabled, ...deps])

  useEffect(() => {
    load()
  }, [load])

  return { data, loading, error, reload: load }
}
