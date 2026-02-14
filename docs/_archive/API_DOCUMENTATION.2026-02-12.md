# ARCHIVED

Archivo archivado el 2026-02-12 durante consolidacion de documentacion API.
Fuente original: docs/API_DOCUMENTATION.md

---
# API Documentation - VixenBliss Creator

## Base URLs
- **Development**: `http://localhost:8000`
- **Staging**: `https://api-staging.vixenbliss.com`
- **Production**: `https://api.vixenbliss.com`

## Authentication
All API endpoints require JWT authentication unless specified otherwise.

### Headers
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

---

## Avatars API

### Create Avatar
**Endpoint**: `POST /api/v1/avatars`

**Request Body**:
```json
{
  "avatar_name": "Luna",
  "nicho": "fitness",
  "aesthetic_style": "athletic",
  "metadata": {
    "age_range": "25-30",
    "location": "Miami, FL"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "avatar_name": "Luna",
  "nicho": "fitness",
  "aesthetic_style": "athletic",
  "status": "active",
  "performance_score": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Avatars
**Endpoint**: `GET /api/v1/avatars`

**Query Parameters**:
- `status` (optional): `active`, `paused`, `archived`
- `limit` (optional): default 20, max 100
- `offset` (optional): pagination

**Response** (200 OK):
```json
{
  "avatars": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "avatar_name": "Luna",
      "status": "active",
      "performance_score": 85.5
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### Get Avatar
**Endpoint**: `GET /api/v1/avatars/{avatar_id}`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "avatar_name": "Luna",
  "nicho": "fitness",
  "status": "active",
  "bio": "Fitness enthusiast ðŸ’ª | Helping you get fit",
  "identity_components": [
    {
      "component_type": "interests",
      "component_data": {"interests": ["yoga", "nutrition", "wellness"]}
    }
  ],
  "stats": {
    "total_content": 50,
    "total_followers": 15000,
    "total_subscribers": 450,
    "total_revenue": 6750.00
  }
}
```

---

## Content API

### List Content Pieces
**Endpoint**: `GET /api/v1/content`

**Query Parameters**:
- `avatar_id` (required): UUID of avatar
- `status` (optional): `draft`, `ready`, `published`

**Response** (200 OK):
```json
{
  "content_pieces": [
    {
      "id": "content-uuid-1",
      "avatar_id": "avatar-uuid",
      "template_name": "workout-pose-1",
      "hook": "Try this simple morning routine! ðŸ”¥",
      "image_url": "https://cdn.vixenbliss.com/avatars/luna/content-1.jpg",
      "status": "ready",
      "engagement_score": 0,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Generate Content Batch
**Endpoint**: `POST /api/v1/content/generate`

**Request Body**:
```json
{
  "avatar_id": "550e8400-e29b-41d4-a716-446655440000",
  "count": 50,
  "templates": ["workout-pose-1", "workout-pose-2", ...]
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "celery-task-uuid",
  "status": "processing",
  "estimated_completion": "2024-01-15T11:00:00Z"
}
```

### AI Provider Routing (Backend)
The backend supports provider-agnostic routing for image generation and LoRA inference.

Runtime configuration (environment variables):
- `AI_IMAGE_PROVIDER`: primary provider for LoRA/content image inference.
- `AI_IMAGE_PROVIDER_FALLBACKS`: comma-separated fallback chain.
- `AI_PROVIDER_ENDPOINT_URL`: generic HTTP serverless endpoint (Modal-compatible).
- `AI_PROVIDER_API_TOKEN`: token for generic HTTP provider auth.
- `AI_PROVIDER_AUTH_HEADER`, `AI_PROVIDER_AUTH_SCHEME`: auth header customization.
- `FACE_PROVIDER_ORDER`: provider order for facial generation in Sistema 1.

Backward compatibility:
- `LORA_PROVIDER`, `MODAL_ENDPOINT_URL`, `MODAL_API_TOKEN`, `MODAL_API_KEY` are still supported.

Supported provider keys and aliases:
- LoRA/content inference: `replicate`, `comfyui`, `modal_sdxl_lora`, `serverless_http`
- Facial generation: `replicate_sdxl` (`replicate`), `leonardo`, `dall_e_3` (`openai`)

---

## Scheduling API

### Schedule Post
**Endpoint**: `POST /api/v1/scheduling/schedule`

**Request Body**:
```json
{
  "content_id": "content-uuid",
  "platform": "instagram",
  "scheduled_time": "2024-01-16T09:00:00Z",
  "caption": "Morning vibes! ðŸŒ…"
}
```

**Response** (201 Created):
```json
{
  "id": "scheduled-post-uuid",
  "content_id": "content-uuid",
  "platform": "instagram",
  "scheduled_time": "2024-01-16T09:00:00Z",
  "status": "scheduled"
}
```

---

## Subscriptions API

### Create Subscription
**Endpoint**: `POST /api/v1/subscriptions`

**Request Body**:
```json
{
  "avatar_id": "avatar-uuid",
  "tier": "basic",
  "stripe_customer_id": "cus_...",
  "stripe_subscription_id": "sub_..."
}
```

**Response** (201 Created):
```json
{
  "id": "subscription-uuid",
  "avatar_id": "avatar-uuid",
  "tier": "basic",
  "amount": 9.99,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Analytics API

### Avatar Performance
**Endpoint**: `GET /api/v1/analytics/avatar/{avatar_id}`

**Response** (200 OK):
```json
{
  "avatar_id": "avatar-uuid",
  "avatar_name": "Luna",
  "metrics": {
    "followers": 15000,
    "subscribers": 450,
    "conversion_rate": 3.0,
    "total_revenue": 6750.00,
    "llm_cost": 450.00,
    "roi": 15.0,
    "status": "winner"
  },
  "content_stats": {
    "total_pieces": 50,
    "avg_engagement": 5.2,
    "top_performing": [
      {
        "content_id": "content-uuid-1",
        "engagement_score": 8.5,
        "views": 50000
      }
    ]
  }
}
```

---

## Webhooks

### Stripe Webhook
**Endpoint**: `POST /webhooks/stripe`

**Events Handled**:
- `checkout.session.completed` - New subscription
- `invoice.payment_succeeded` - Recurring payment
- `customer.subscription.deleted` - Cancellation

### Instagram Webhook
**Endpoint**: `POST /webhooks/instagram`

**Events Handled**:
- `messages` - New DM (trigger chatbot)
- `comments` - New comment
- `mentions` - Avatar mentioned

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error: avatar_name must be at least 3 characters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 404 Not Found
```json
{
  "detail": "Avatar not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limits
- **Authenticated requests**: 100 requests/minute
- **Webhook endpoints**: No limit
- **Content generation**: 10 batches/hour per avatar

---

## Pagination
All list endpoints support pagination:
- `limit`: Number of items (default 20, max 100)
- `offset`: Starting position (default 0)

**Example**:
```
GET /api/v1/avatars?limit=20&offset=40
```

---

## Status Codes
- `200 OK` - Successful GET request
- `201 Created` - Successful POST request
- `202 Accepted` - Background job started
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

*This documentation will be expanded as endpoints are implemented.*
