# Security Guidelines - VixenBliss Creator

## Principios Generales
1. **Never trust user input** - Validar y sanitizar todo
2. **Principle of least privilege** - Mínimos permisos necesarios
3. **Defense in depth** - Múltiples capas de seguridad
4. **Secrets never in code** - Environment variables o secrets manager

## Secrets Management

### ✅ Good Practices
```bash
# .env (NOT in git, in .gitignore)
DATABASE_URL=postgresql://user:pass@localhost/dbname
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
NOTION_API_KEY=ntn_...

# .env.example (committed to git)
DATABASE_URL=postgresql://user:pass@localhost/dbname
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_test_...
NOTION_API_KEY=ntn_...
```

```python
# ✅ Good: Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")
```

### ❌ Bad Practices
```python
# ❌ NEVER: Hardcoded secrets
OPENAI_API_KEY = "sk-proj-abc123..."  # FORBIDDEN!
STRIPE_KEY = "sk_live_xyz789..."      # FORBIDDEN!

# ❌ NEVER: Secrets in logs
logger.info(f"Using API key: {OPENAI_API_KEY}")  # FORBIDDEN!

# ❌ NEVER: Secrets in error messages
raise Exception(f"Failed with key {api_key}")  # FORBIDDEN!
```

## Authentication & Authorization

### Backend (FastAPI)
```python
# ✅ Good: JWT authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await get_user_by_id(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Good: Protected endpoint
@app.get("/api/v1/avatars")
async def list_avatars(current_user: User = Depends(get_current_user)):
    return await avatar_service.get_by_user(current_user.id)
```

### Frontend (Next.js)
```typescript
// ✅ Good: Server-side session
import { getServerSession } from "next-auth"

export default async function AvatarPage() {
  const session = await getServerSession()

  if (!session) {
    redirect("/login")
  }

  const avatars = await fetchAvatars(session.accessToken)
  return <AvatarList avatars={avatars} />
}
```

## Input Validation

### Backend
```python
# ✅ Good: Pydantic validation
from pydantic import BaseModel, Field, validator

class AvatarCreate(BaseModel):
    avatar_name: str = Field(..., min_length=3, max_length=50)
    nicho: str = Field(..., min_length=3, max_length=100)

    @validator("avatar_name")
    def validate_avatar_name(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError("Only alphanumeric and underscore allowed")
        return v

# ✅ Good: SQL injection prevention (use parameters)
async def get_avatar(avatar_id: UUID):
    # Good: Parameterized query
    return await db.fetch_one(
        "SELECT * FROM avatars WHERE id = :id",
        {"id": avatar_id}
    )

# ❌ Bad: SQL injection vulnerability
async def get_avatar(avatar_name: str):
    # FORBIDDEN: String interpolation
    return await db.fetch_one(
        f"SELECT * FROM avatars WHERE name = '{avatar_name}'"
    )
```

### Frontend
```typescript
// ✅ Good: XSS prevention (React escapes by default)
export function AvatarCard({ name }: { name: string }) {
  return <div>{name}</div>  // React auto-escapes
}

// ❌ Bad: XSS vulnerability
export function AvatarCard({ name }: { name: string }) {
  return <div dangerouslySetInnerHTML={{ __html: name }} />  // DANGEROUS!
}
```

## API Security

### Rate Limiting
```python
# ✅ Good: Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/avatars")
@limiter.limit("10/minute")
async def create_avatar(request: Request, data: AvatarCreate):
    return await avatar_service.create(data)
```

### CORS
```python
# ✅ Good: Restricted CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vixenbliss.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ❌ Bad: Open CORS
allow_origins=["*"]  # FORBIDDEN in production!
```

## Content Security

### LLM Output Moderation
```python
# ✅ Good: Content moderation
from openai import OpenAI

client = OpenAI()

async def check_safety(content: str) -> bool:
    """Verify content meets policies."""
    moderation = await client.moderations.create(input=content)

    if moderation.results[0].flagged:
        logger.warning(f"Content flagged: {moderation.results[0].categories}")
        return False

    return True

# ✅ Good: Apply to generated content
async def generate_response(prompt: str) -> str:
    response = await llm.invoke(prompt)

    if not await check_safety(response):
        return "I can't help with that."

    return response
```

## Database Security

### Connection Security
```python
# ✅ Good: SSL connection
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"

# ✅ Good: Connection pooling limits
async def create_db_pool():
    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=5,
        max_size=20,
        command_timeout=60,
    )
```

### Data Encryption
```python
# ✅ Good: Hash passwords
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ❌ Bad: Plain text passwords
password = "user_password_123"  # FORBIDDEN!
```

## Third-Party API Security

### Webhook Verification
```python
# ✅ Good: Verify Stripe webhooks
import stripe

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Process verified event
    return {"status": "success"}
```

## Logging Security

### ✅ Good Logging
```python
# Log events without sensitive data
logger.info(f"User {user_id} created avatar {avatar_id}")
logger.warning(f"Failed login attempt for user {user_id}")
logger.error(f"API call failed: {endpoint}")
```

### ❌ Bad Logging
```python
# FORBIDDEN: Logging secrets
logger.info(f"Using API key: {api_key}")  # FORBIDDEN!
logger.debug(f"Password attempt: {password}")  # FORBIDDEN!
logger.info(f"JWT token: {token}")  # FORBIDDEN!
```

## Security Checklist

### Before Deployment
- [ ] No secrets hardcoded
- [ ] Environment variables configured
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (React default + no dangerouslySetInnerHTML)
- [ ] Authentication on protected endpoints
- [ ] Content moderation for LLM outputs
- [ ] Webhook signature verification
- [ ] Error messages don't leak sensitive info
- [ ] Logs don't contain secrets

### Regular Security Tasks
- [ ] Update dependencies monthly
- [ ] Review access logs weekly
- [ ] Rotate API keys quarterly
- [ ] Security audit annually
- [ ] Backup database daily
- [ ] Test disaster recovery quarterly
