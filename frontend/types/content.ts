/**
 * Content Generation Type Definitions
 */

export type ContentStatus = "pending" | "generating" | "completed" | "failed"

export type ContentTier = "capa1" | "capa2" | "capa3"

export interface ContentPiece {
  id: string
  avatar_id: string
  prompt_used: string
  image_url: string
  tier: ContentTier
  status: ContentStatus
  generation_time_seconds: number | null
  cost_usd: number | null
  created_at: string
  meta_data: Record<string, any>
  explicitness_level?: number
  price_usd?: number
}

export interface Template {
  id: string
  name: string
  category: string
  tier: ContentTier
  prompt_template: string
  negative_prompt: string
  style_modifiers: string[]
}

export interface ContentGenerationRequest {
  avatar_id: string
  template_id?: string
  custom_prompt?: string
  tier?: ContentTier
}

export interface BatchGenerationRequest {
  avatar_id: string
  num_pieces: number
  platform: string
  tier_distribution?: {
    capa1: number
    capa2: number
    capa3: number
  }
  include_hooks?: boolean
  safety_check?: boolean
  upload_to_storage?: boolean
  custom_prompts?: string[]
  custom_tiers?: Array<"capa1" | "capa2" | "capa3">
  generation_config?: Record<string, any>
}

export interface BatchGenerationResponse {
  task_id: string
  status: string
  message: string
  estimated_duration_minutes: number
  estimated_cost_usd: number
}

/**
 * Content Batch Status
 */
export type BatchStatus = "queued" | "processing" | "completed" | "failed"

export interface ContentBatch {
  id: string
  avatar_id: string
  model_name: string
  template: string
  total_pieces: number
  completed: number
  failed: number
  status: BatchStatus
  created_at: string
  estimated_cost: number
  task_id?: string
}

/**
 * Content Stats per Avatar
 */
export interface ContentStats {
  avatar_id: string
  total_content: number
  tier_distribution: {
    capa1: number
    capa2: number
    capa3: number
  }
  safety_distribution: {
    safe: number
    suggestive: number
    borderline: number
  }
  has_lora_weights: boolean
}

/**
 * Template List Response
 */
export interface TemplateListResponse {
  templates: Template[]
  total: number
  categories: string[]
}

/**
 * Hook Generation
 */
export interface HookGenerationRequest {
  avatar_id: string
  content_type: string
  platform: "instagram" | "tiktok" | "x" | "facebook"
  num_variations?: number
}

export interface HookGenerationResponse {
  hooks: string[]
  platform: string
  content_type: string
}

/**
 * Safety Check
 */
export interface SafetyCheckRequest {
  image_url: string
  prompt?: string
}

export interface SafetyCheckResponse {
  is_safe: boolean
  safety_score: number
  flags: string[]
  recommendation: "approve" | "review" | "reject"
}
