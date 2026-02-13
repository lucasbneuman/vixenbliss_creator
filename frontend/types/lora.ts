export interface LoRAModel {
  id: string
  user_id: string
  name: string
  description?: string | null
  base_model?: string | null
  lora_weights_url: string
  preview_image_url?: string | null
  tags: string[]
  is_active: boolean
  meta_data: Record<string, any>
  created_at: string
  updated_at: string
}
