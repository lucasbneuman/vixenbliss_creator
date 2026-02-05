/**
 * Custom React Hooks for API calls
 * Handles loading, error states, and data fetching
 */

import { useState, useEffect, useCallback } from "react"
import { ApiClientError } from "@/lib/api/client"

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

/**
 * Hook for fetching data with loading/error states
 */
export function useApi<T>(
  apiFunction: () => Promise<T>,
  dependencies: any[] = []
): UseApiState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
  })

  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const data = await apiFunction()
      setState({ data, loading: false, error: null })
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error : new Error("Unknown error"),
      })
    }
  }, dependencies)

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    ...state,
    refetch: fetchData,
  }
}

/**
 * Hook for API mutations (POST, PUT, DELETE)
 */
export function useApiMutation<TData, TVariables = void>() {
  const [state, setState] = useState<{
    loading: boolean
    error: Error | null
  }>({
    loading: false,
    error: null,
  })

  const mutate = useCallback(
    async (
      apiFunction: (variables: TVariables) => Promise<TData>,
      variables: TVariables
    ): Promise<TData | null> => {
      setState({ loading: true, error: null })

      try {
        const data = await apiFunction(variables)
        setState({ loading: false, error: null })
        return data
      } catch (error) {
        const errorObj =
          error instanceof Error ? error : new Error("Unknown error")
        setState({ loading: false, error: errorObj })
        throw errorObj
      }
    },
    []
  )

  return {
    ...state,
    mutate,
  }
}

/**
 * Hook for managing async actions with toast notifications
 */
export function useAsyncAction() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const execute = useCallback(async <T,>(
    action: () => Promise<T>,
    options?: {
      onSuccess?: (data: T) => void
      onError?: (error: Error) => void
      successMessage?: string
      errorMessage?: string
    }
  ): Promise<T | null> => {
    setLoading(true)
    setError(null)

    try {
      const result = await action()
      setLoading(false)

      if (options?.onSuccess) {
        options.onSuccess(result)
      }

      return result
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Unknown error")
      setLoading(false)
      setError(error)

      if (options?.onError) {
        options.onError(error)
      }

      return null
    }
  }, [])

  return {
    loading,
    error,
    execute,
  }
}
