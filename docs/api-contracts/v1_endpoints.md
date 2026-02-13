# API Contract Freeze v1

Last updated: 2026-02-12
Source of truth: `backend/app/main.py` and `backend/app/api/*.py`

This document captures current behavior as implemented in code. It does not assume intended behavior.

## Mounted today (contracted)

Mounted in `backend/app/main.py` today and included in v1 freeze:
- `identities.router` (`/api/v1/identities`)
- `content.router` (`/api/v1/content`)
- `loras.router` (`/api/v1/loras`)
- `costs.router` (`/api/v1/identities/costs`)

## Present in code but not mounted (not contracted)

Defined in `backend/app/api/` but not mounted in `backend/app/main.py` today.
These routes are intentionally outside the v1 contract freeze:
- `distribution.router` (`/api/v1/distribution`)
- `conversations.router` (`/api/v1/conversations`)
- `premium.router` (`/api/v1/premium`)
- `video.router` (`/api/v1/video`)
- `webhooks.router` (`/api/v1/webhooks`)

Notes:
- `storage.py` exposes `/storage/*` routes (non-v1), so it is outside this v1 inventory.
- No explicit auth dependency (`Depends(get_current_user)` or similar) is present in these routers.
- Several routes require `user_id` (query/form param) as input; this is not auth middleware.
- FastAPI validation errors may return `422` even when not raised explicitly by handler code.

## `/api/v1/identities` (mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed | Auth | Side effects |
|---|---|---|---|---|---|---|
| POST | `/api/v1/identities/components/generate` | Body: `FacialGenerationRequest` | `FacialGenerationResponse` | 200, 500, 422 | None | Calls AI generation service |
| POST | `/api/v1/identities/avatars` | Body: `AvatarCreateRequest`; query: `user_id` (UUID) | `FacialGenerationResponse` | 200, 500, 422 | None (`user_id` required) | Generates face, uploads, writes avatar/components |
| POST | `/api/v1/identities/avatars/with-lora` | Body: `AvatarCreateWithLoRARequest`; query: `user_id` (UUID) | `AvatarResponse` | 200, 500, 422 | None (`user_id` required) | Writes avatar with LoRA metadata |
| GET | `/api/v1/identities/avatars/{avatar_id}` | Path: `avatar_id` (UUID) | `AvatarResponse` | 200, 404, 422 | None | DB read |
| GET | `/api/v1/identities/avatars` | Query: `user_id` (UUID), `skip`, `limit` | `List[AvatarResponse]` | 200, 422 | None (`user_id` required) | DB read |
| PATCH | `/api/v1/identities/avatars/{avatar_id}/stage` | Path: `avatar_id` (UUID); query: `new_stage` | `{success, avatar_id, new_stage}` | 200, 404, 422 | None | DB update |

## `/api/v1/content` (mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed | Auth | Side effects |
|---|---|---|---|---|---|---|
| POST | `/api/v1/content/generate` | Body: `ContentGenerationRequest` | `ContentPieceResponse` | 200, 400, 404, 502, 422 | None | Generates image, writes `ContentPiece` |
| POST | `/api/v1/content/batch` | Body: `BatchGenerationRequest` | Dict with `success`, `message`, `task_id`, `avatar_id`, estimates | 200, 400, 404, 422 | None | Queues Celery task |
| POST | `/api/v1/content/batch/sync` | Body: `BatchGenerationRequest` | `BatchGenerationResponse` | 200, 400, 404, 422 | None | Runs sync batch processor |
| GET | `/api/v1/content/templates` | Query: `category`, `tier`, `avatar_id` | `TemplateListResponse` (`templates`, `total`, `categories`) | 200, 400, 404, 422 | None | Template lookup; optional avatar DB read |
| GET | `/api/v1/content/templates/{template_id}` | Path: `template_id` | Template object | 200, 404, 422 | None | In-memory template lookup |
| POST | `/api/v1/content/hooks` | Body: `HookGenerationRequest` | `HookGenerationResponse` (`hooks`, `platform`, `content_type`) | 200, 400, 404, 422 | None | Generates hooks |
| POST | `/api/v1/content/safety-check` | Body: `SafetyCheckRequest` | `SafetyCheckResponse` | 200, 422 | None | Calls safety service |
| POST | `/api/v1/content/upload-batch` | Query/body params: `avatar_id`, `content_ids: List[str]` | Dict with `avatar_id`, `total_uploaded`, `total_failed`, `results` | 200, 404, 422 | None | Downloads from URLs, uploads to storage, DB updates |
| GET | `/api/v1/content/avatar/{avatar_id}/content` | Path: `avatar_id`; query: `tier`, `limit`, `offset` | `List[ContentPieceResponse]` | 200, 422 | None | DB read |
| GET | `/api/v1/content/stats/{avatar_id}` | Path: `avatar_id` | Dict with `avatar_id`, `total_content`, tier/safety distributions, `has_lora_weights` | 200, 404, 422 | None | DB read/aggregation |

## `/api/v1/loras` (mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed | Auth | Side effects |
|---|---|---|---|---|---|---|
| GET | `/api/v1/loras/models` | Query: `user_id` (UUID), `include_inactive` | `list[LoRAModelResponse]` | 200, 422 | None (`user_id` required) | DB read |
| POST | `/api/v1/loras/models` | Body: `LoRAModelCreateRequest`; query: `user_id` (UUID) | `LoRAModelResponse` | 200, 422 | None (`user_id` required) | DB insert |
| POST | `/api/v1/loras/models/upload` | Multipart: `user_id`, `name`, optional metadata + `lora_file` | `LoRAModelResponse` | 200, 400, 500, 422 | None (`user_id` form field) | Uploads file to storage, DB insert |
| DELETE | `/api/v1/loras/models/{lora_model_id}` | Path: `lora_model_id`; query: `user_id` | `{success, lora_model_id}` | 200, 404, 422 | None (`user_id` required) | Soft-delete (`is_active=False`) |
| POST | `/api/v1/loras/dataset/generate` | Body: `DatasetGenerationRequest` | `DatasetGenerationResponse` | 200, 404, 500, 422 | None | Dataset generation workflow |
| POST | `/api/v1/loras/training/start` | Body: `LoRATrainingRequest` | `LoRATrainingResponse` | 200, 500, 422 | None | Queues training task |
| GET | `/api/v1/loras/training/status/{training_job_id}` | Path: `training_job_id` | `LoRATrainingStatus` | 200, 422 | None | Reads Celery task state |

## `/api/v1/identities/costs` (mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed | Auth | Side effects |
|---|---|---|---|---|---|---|
| GET | `/api/v1/identities/costs/{avatar_id}` | Path: `avatar_id` (UUID) | Cost breakdown dict from service | 200, 404, 422 | None | DB read |
| GET | `/api/v1/identities/costs/batch/{batch_id}` | Path: `batch_id` | Batch cost dict from service | 200, 422 | None | DB read |
| GET | `/api/v1/identities/costs/summary` | Query: optional `user_id`, `days` | Summary dict from service | 200, 422 | None | DB aggregation |
| GET | `/api/v1/identities/costs/estimate` | None | Estimate dict from service | 200, 422 | None | Pure service call |

## Not contracted endpoint inventory (present in code, not mounted)

## `/api/v1/distribution` (defined, not mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed in router | Auth | Side effects |
|---|---|---|---|---|---|---|
| GET | `/api/v1/distribution/auth/{platform}/url` | Path: `platform`; query: `redirect_uri`, `state` | `{authorization_url, platform, redirect_uri}` | 200, 400, 422 | None | Calls social provider OAuth URL service |
| POST | `/api/v1/distribution/auth/{platform}/callback` | Path: `platform`; query/form-style params: `code`, `redirect_uri`, `user_id`, optional `avatar_id` | `{success, account_id, platform, username, status}` | 200, 400, 422 | None | Exchanges tokens; writes/updates social account |
| GET | `/api/v1/distribution/accounts` | Query: `user_id`, optional `platform` | `List[Dict[str, Any]]` account summaries | 200, 422 | None | DB read |
| DELETE | `/api/v1/distribution/accounts/{account_id}` | Path: `account_id` | `{success, message}` | 200, 404, 422 | None | DB update (disconnect) |
| POST | `/api/v1/distribution/health/check/{account_id}` | Path: `account_id` | Health check result dict | 200, 404, 422 | None | Health service call + DB updates |
| POST | `/api/v1/distribution/health/check-all` | Query: `user_id` | `{total_accounts, results}` | 200, 422 | None | Iterative health checks |
| GET | `/api/v1/distribution/health/dashboard/{user_id}` | Path: `user_id` | Dashboard dict | 200, 422 | None | Aggregation read |
| POST | `/api/v1/distribution/publish` | Params: `account_id`, `content_piece_id`, optional `caption`, `hashtags` | `{success, post_id, platform_url, published_at}` | 200, 400, 404, 500, 422 | None | Publishes to external platform; DB update |
| POST | `/api/v1/distribution/schedule` | Params: `account_id`, `content_piece_ids`, optional flags | `{success, total_scheduled, scheduled_posts[]}` | 200, 400, 404, 422 | None | Creates scheduled posts |
| GET | `/api/v1/distribution/scheduled-posts` | Query: optional `account_id`, `status`, `limit` | `{total, posts[]}` | 200, 422 | None | DB read |
| DELETE | `/api/v1/distribution/scheduled-posts/{post_id}` | Path: `post_id` | `{success, message}` | 200, 400, 404, 422 | None | DB update (cancel) |
| GET | `/api/v1/distribution/analytics/optimal-times/{account_id}` | Path: `account_id`; query: `days_back` | Analysis dict | 200, 404, 422 | None | Analytics computation |

## `/api/v1/conversations` (defined, not mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed in router | Auth | Side effects |
|---|---|---|---|---|---|---|
| GET | `/api/v1/conversations` | Query filters: `user_id`, `avatar_id`, `funnel_stage`, `qualification`, `min_lead_score`, `is_converted`, `limit`, `offset` | `{total, conversations[]}` | 200, 422 | None | DB query |
| GET | `/api/v1/conversations/{conversation_id}` | Path: `conversation_id` | Conversation detail dict | 200, 404, 422 | None | DB read |
| GET | `/api/v1/conversations/{conversation_id}/messages` | Path: `conversation_id`; query: `limit`, `offset` | `{conversation_id, total, messages[]}` | 200, 404, 422 | None | DB read |
| POST | `/api/v1/conversations/{conversation_id}/send-message` | Path: `conversation_id`; param: `message_text` | `{success, bot_response, lead_score, funnel_stage, intent?, sentiment?}` | 200, 500, 422 | None | Processes DM pipeline |
| POST | `/api/v1/conversations/{conversation_id}/rescore` | Path: `conversation_id` | `{conversation_id, ...score_data}` | 200, 404, 422 | None | Recomputes and updates score |
| GET | `/api/v1/conversations/analytics/overview` | Query: optional `avatar_id`, `days_back` | Analytics dict | 200, 422 | None | Aggregation read |
| POST | `/api/v1/conversations/upsell-events` | Params: `conversation_id`, `offer_type`, optional `offer_price`, `ab_test_variant_id`, `pricing_strategy` | Upsell event summary dict | 200, 500, 422 | None | DB insert |
| PUT | `/api/v1/conversations/upsell-events/{upsell_event_id}/response` | Path: `upsell_event_id`; params: `user_response`, optional `rejection_reason`, `negotiated_price` | Updated upsell event fields | 200, 500, 422 | None | DB update |
| POST | `/api/v1/conversations/upsell-events/{upsell_event_id}/convert` | Path: `upsell_event_id`; optional `revenue_generated` | Conversion result dict | 200, 500, 422 | None | DB update/revenue tracking |
| POST | `/api/v1/conversations/ab-tests` | Params: `test_name`, `element_type`, `variants`, optional `description` | `{test_name, element_type, variants[]}` | 200, 500, 422 | None | Creates AB test |
| GET | `/api/v1/conversations/ab-tests/{test_name}/results` | Path: `test_name` | AB test results dict | 200, 500, 422 | None | Read/compute results |
| POST | `/api/v1/conversations/ab-tests/{test_name}/end` | Path: `test_name`; optional `deploy_winner` | End-test result dict | 200, 500, 422 | None | Finalizes AB test |

## `/api/v1/premium` (defined, not mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed in router | Auth | Side effects |
|---|---|---|---|---|---|---|
| GET | `/api/v1/premium/packs` | Query: `avatar_id` | `{avatar_id, available_packs}` | 200, 500, 422 | None | Service read |
| POST | `/api/v1/premium/packs/create` | Params: `avatar_id`, optional `pack_type`, `custom_piece_count`, `custom_price`, `custom_explicitness` | Service result dict | 200, 500, 422 | None | Creates premium pack |
| GET | `/api/v1/premium/packs/stats/{avatar_id}` | Path: `avatar_id` | `{avatar_id, ...stats}` | 200, 500, 422 | None | Aggregation read |
| POST | `/api/v1/premium/conversions/tier-upgrade` | Params: `conversation_id`, `from_tier`, `to_tier`, `upgrade_price` | `{success, upgrade_event_id, ...}` | 200, 404, 500, 422 | None | Writes upgrade + conversion records |
| GET | `/api/v1/premium/conversions/tier-upgrade/stats` | Query: optional `avatar_id`, `days_back` | Upgrade metrics dict | 200, 422 | None | Aggregation read |
| GET | `/api/v1/premium/metrics/revenue-per-subscriber` | Query: optional `avatar_id`, `tier`, `days_back` | Revenue metrics dict | 200, 422 | None | Aggregation read |
| GET | `/api/v1/premium/metrics/dashboard` | Query: optional `avatar_id`, `days_back` | Composite dashboard dict | 200, 422 | None | Aggregation + composed service calls |

## `/api/v1/video` (defined, not mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed in router | Auth | Side effects |
|---|---|---|---|---|---|---|
| POST | `/api/v1/video/generate` | Params: `avatar_id`, `prompt`, optional `duration`, `aspect_ratio`, `style`, `image_url`, `provider`, `enable_fallback` | `{success, content_piece_id, video_url, provider, duration, cost, fallback_count, created_at}` | 200, 404, 500, 422 | None | Generates video, uploads storage, writes content/cost |
| POST | `/api/v1/video/voice/generate` | Params: `avatar_id`, `text`, optional `voice_id`, `language`, `provider` | `{success, audio_url, provider, audio_format, char_count, cost, voice_id, language}` | 200, 404, 500, 422 | None | Generates TTS, uploads storage, tracks cost |
| POST | `/api/v1/video/distribution/schedule` | Params: `content_piece_id`, `platforms`, optional `scheduled_time` | `{success, content_piece_id, platforms, scheduled_time, platform_metadata, warnings}` | 200, 400, 404, 500, 422 | None | Updates distribution metadata |
| GET | `/api/v1/video/costs/{avatar_id}` | Path: `avatar_id` | Cost dict from service | 200, 500, 422 | None | Read costs |
| GET | `/api/v1/video/costs/user/{user_id}` | Path: `user_id`; query: `days_back` | User video cost summary dict | 200, 500, 422 | None | Aggregation read |
| POST | `/api/v1/video/costs/estimate` | Params: `provider`, `duration`, optional `quantity` | `{provider, duration, quantity, estimated_cost, cost_per_video}` | 200, 500, 422 | None | Cost estimate only |

## `/api/v1/webhooks` (defined, not mounted)

| Method | Path | Request schema / params | Response shape (high-level) | Status codes observed in router | Auth | Side effects |
|---|---|---|---|---|---|---|
| GET | `/api/v1/webhooks/instagram/verify` | Query aliases: `hub.mode`, `hub.challenge`, `hub.verify_token` | Integer challenge on success | 200, 403, 422 | No auth dependency; token check via query/env | Verification only |
| POST | `/api/v1/webhooks/instagram/callback` | Raw webhook payload in request body | `{status: "received"}` or `{status: "ignored", reason}` | 200, 401, 422 | Signature check (header) | Background task dispatch |
| GET | `/api/v1/webhooks/tiktok/verify` | Query: `challenge`, `timestamp`, `signature` | `{challenge}` | 200, 403, 422 | Signature/hash check via query/env | Verification only |
| POST | `/api/v1/webhooks/tiktok/callback` | Raw webhook payload in request body | `{status: "received"}` | 200, 401, 422 | Signature check (header) | Background task dispatch |
| POST | `/api/v1/webhooks/manual/send-message` | Params: `conversation_id`, `message_text` | `{success, bot_response, lead_score, funnel_stage}` | 200, 500, 422 | None | Runs manual DM processing |

---

## Complemento Operativo (Legacy, No Contractual)

Esta seccion resume informacion util proveniente de `docs/API_DOCUMENTATION.md`.
No reemplaza el freeze contractual; solo agrega contexto operativo.

### Base URLs (referenciales)

- Development: `http://localhost:8000`
- Staging: `https://api-staging.vixenbliss.com`
- Production: `https://api.vixenbliss.com`

### Headers comunes

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Status codes comunes

- `200`, `201`, `202`
- `400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`

### Notas

- Si hay conflicto entre esta seccion y los contratos de arriba, prevalece el contrato freeze.
- Historial anterior: `docs/_archive/API_DOCUMENTATION.2026-02-12.md`.
