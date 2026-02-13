/**
 * Avatar & Model Type Definitions
 * Based on backend SQLAlchemy models
 */

export type AvatarStage = "draft" | "generating_face" | "training_lora" | "ready" | "active" | "paused" | "archived"

export type AvatarHealth = "healthy" | "warning" | "critical"

export interface Avatar {
  id: string
  user_id: string
  name: string
  stage: AvatarStage
  base_image_url: string | null
  lora_model_id: string | null
  lora_weights_url: string | null
  niche: string | null
  aesthetic_style: string | null
  created_at: string
  updated_at: string
  meta_data: Record<string, any>
}

/**
 * Extended Model interface for dashboard display
 * Combines Avatar + performance metrics
 */
export interface Model {
  id: string
  name: string
  niche: string
  status: "active" | "paused" | "archived"
  mrr: number
  arpu: number
  subscribers: number
  engagement_rate: number
  content_generated: number
  health: AvatarHealth
  created_at: string
  performance_delta?: number
}

export interface AvatarCreateRequest {
  name: string
  niche: string
  aesthetic_style: string
  lora_model_id?: string
  facial_generation: {
    age_range: "18-25" | "26-35" | "36-45" | "46+"
    ethnicity?: string
    aesthetic_style: string
    gender: "female" | "male" | "non-binary"
    custom_prompt?: string
  }
}

export interface AvatarUpdateRequest {
  name?: string
  stage?: AvatarStage
  niche?: string
  aesthetic_style?: string
  meta_data?: Record<string, any>
}
