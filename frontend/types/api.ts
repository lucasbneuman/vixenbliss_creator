/**
 * API Response & Error Type Definitions
 */

export interface ApiResponse<T> {
  data: T
  status: number
}

export interface ApiError {
  message: string
  status: number
  detail?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

export interface HealthCheckResponse {
  status: "healthy" | "unhealthy"
  database: "connected" | "disconnected"
  version?: string
  error?: string
}

/**
 * Cost tracking types
 */
export interface CostEntry {
  id: string
  avatar_id: string
  user_id: string
  operation_type: string
  provider: string
  cost_usd: number
  metadata: Record<string, any>
  created_at: string
}

export interface CostSummary {
  total_cost: number
  by_operation: Record<string, number>
  by_provider: Record<string, number>
  count: number
}

/**
 * Revenue metrics types
 */
export interface RevenueData {
  date: string
  layer1: number
  layer2: number
  layer3: number
  total: number
}

export interface ConversionData {
  stage: string
  count: number
  conversionRate: number
}

export interface MetricsDashboard {
  mrr_total: number
  daily_revenue: number
  arpu: number
  active_models: number
  total_subscribers: number
  churn_rate: number
  conversion_rate: number
}
