"use client"

import React from "react"
import { AlertTriangle } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { formatErrorMessage } from "@/lib/errors"

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Error Boundary Component
 * Catches React errors and displays user-friendly message
 */
export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="p-8">
          <Alert variant="destructive" className="border-red-500/50 bg-red-500/10">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription>
              {formatErrorMessage(this.state.error)}
            </AlertDescription>
          </Alert>
          <Button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4"
          >
            Try again
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}

/**
 * Error Display Component
 * For displaying inline errors in components
 */
export function ErrorDisplay({ error }: { error: unknown }) {
  return (
    <Alert variant="destructive" className="border-red-500/50 bg-red-500/10">
      <AlertTriangle className="h-4 w-4 text-red-500" />
      <AlertTitle className="text-red-500">Error</AlertTitle>
      <AlertDescription className="text-red-400">
        {formatErrorMessage(error)}
      </AlertDescription>
    </Alert>
  )
}
