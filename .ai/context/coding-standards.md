# Coding Standards - VixenBliss Creator

## General Principles
1. **Explicit over implicit** - Type hints, clear naming
2. **Simple over complex** - No over-engineering
3. **Tested over untested** - Tests requeridos (>80% coverage)
4. **Documented over undocumented** - Docs para APIs públicas

## Python (Backend + LLM Service)

### Style Guide
- **PEP 8** compliance
- **Type hints** obligatorios
- **Pydantic** para validaciones
- **Async/await** para I/O operations

### Good Examples
```python
# ✅ Good: Type hints, async, Pydantic
from pydantic import BaseModel, Field
from typing import List, Optional

class AvatarCreate(BaseModel):
    avatar_name: str = Field(..., min_length=3, max_length=50)
    nicho: str = Field(..., min_length=3)
    aesthetic_style: Optional[str] = None

async def create_avatar(data: AvatarCreate) -> Avatar:
    """Create new avatar with validations."""
    avatar = await avatar_service.create(data)
    return avatar

# ✅ Good: Error handling
async def get_avatar(avatar_id: UUID) -> Avatar:
    avatar = await db.fetch_one(
        "SELECT * FROM avatars WHERE id = :id",
        {"id": avatar_id}
    )
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return Avatar(**avatar)
```

### Bad Examples
```python
# ❌ Bad: No type hints
def create_avatar(data):
    return avatar_service.create(data)

# ❌ Bad: No validation
@app.post("/avatars")
async def create_avatar(request: Request):
    data = await request.json()
    avatar = await db.insert("avatars", data)  # No validation!
    return avatar

# ❌ Bad: Synchronous I/O
def get_avatar(avatar_id):
    return db.query("SELECT * FROM avatars WHERE id = ?", avatar_id)
```

### Testing Standards
```python
# ✅ Good: Fixtures, async tests
import pytest

@pytest.fixture
async def avatar_service():
    return AvatarService()

@pytest.mark.asyncio
async def test_create_avatar_success(avatar_service):
    data = AvatarCreate(avatar_name="Test", nicho="fitness")
    avatar = await avatar_service.create(data)

    assert avatar.id is not None
    assert avatar.avatar_name == "Test"
    assert avatar.status == "active"

@pytest.mark.asyncio
async def test_create_avatar_duplicate(avatar_service):
    data = AvatarCreate(avatar_name="Test", nicho="fitness")
    await avatar_service.create(data)

    with pytest.raises(DuplicateAvatarError):
        await avatar_service.create(data)
```

## TypeScript (Frontend)

### Style Guide
- **TypeScript strict mode** enabled
- **Server Components** por defecto
- **Client Components** solo cuando necesario
- **shadcn/ui** para UI components

### Good Examples
```typescript
// ✅ Good: Server Component, typed
import { Avatar } from "@/types"

export default async function AvatarList() {
  const avatars: Avatar[] = await fetchAvatars()

  return (
    <div className="grid gap-4">
      {avatars.map((avatar) => (
        <AvatarCard key={avatar.id} avatar={avatar} />
      ))}
    </div>
  )
}

// ✅ Good: Client Component only when needed
"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"

interface InteractiveChartProps {
  data: ChartData[]
}

export function InteractiveChart({ data }: InteractiveChartProps) {
  const [filter, setFilter] = useState<string>("all")

  return (
    <div>
      <Button onClick={() => setFilter("winners")}>Winners</Button>
      <Chart data={data} filter={filter} />
    </div>
  )
}

// ✅ Good: Type-safe API calls
async function fetchAvatars(): Promise<Avatar[]> {
  const response = await fetch("/api/v1/avatars")
  if (!response.ok) {
    throw new Error("Failed to fetch avatars")
  }
  return response.json()
}
```

### Bad Examples
```typescript
// ❌ Bad: Client Component when not needed
"use client"

export default function AvatarList() {
  const avatars = getAvatars()  // No async!
  return <div>{avatars.map(...)}</div>
}

// ❌ Bad: No types
export default function AvatarCard({ avatar }) {  // any type!
  return <div>{avatar.name}</div>
}

// ❌ Bad: Inline styles
<div style={{ color: "red", fontSize: 16 }}>Text</div>
// Use Tailwind: <div className="text-red-500 text-base">Text</div>
```

### Testing Standards
```typescript
// ✅ Good: Component tests
import { render, screen } from '@testing-library/react'
import { AvatarCard } from '@/components/AvatarCard'

describe('AvatarCard', () => {
  it('renders avatar name and status', () => {
    render(<AvatarCard name="Test" status="active" />)

    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('shows performance score if provided', () => {
    render(<AvatarCard name="Test" status="active" score={85.5} />)

    expect(screen.getByText('85.5')).toBeInTheDocument()
  })
})
```

## SQL (Database)

### Schema Standards
```sql
-- ✅ Good: Explicit types, indexes, relations
CREATE TABLE avatars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_name VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'active',
    performance_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_avatars_status ON avatars(status);
CREATE INDEX idx_avatars_name ON avatars(avatar_name);
CREATE INDEX idx_avatars_metadata ON avatars USING GIN (metadata);

-- ✅ Good: Reversible migrations
-- migrations/001_create_avatars.up.sql
CREATE TABLE avatars (...);

-- migrations/001_create_avatars.down.sql
DROP TABLE avatars;
```

### Bad Examples
```sql
-- ❌ Bad: No types, no indexes
CREATE TABLE avatars (
    id TEXT,  -- Should be UUID
    name TEXT,  -- No length limit
    data TEXT  -- Should be JSONB
);

-- ❌ Bad: Irreversible migration
DROP TABLE avatars;
CREATE TABLE avatars (...);  -- Data loss!
```

## LLM/Prompts

### Prompt Standards
```python
# ✅ Good: Versioned, documented, separated
# prompts/avatar_bio_v1.txt
"""
Version: 1.0
Tokens: ~200
Model: gpt-4o-mini
Cost per call: ~$0.001
Last updated: 2024-01-15

You are generating a bio for {avatar_name}, a {niche} content creator.
Style: {aesthetic_style}
Keep it under 150 characters.

Example:
Avatar: "Luna", fitness, aesthetic
Bio: "Fitness enthusiast 💪 | Helping you get fit | DM for custom plans"
"""

# ✅ Good: Cost optimization
from langchain.chat_models import ChatOpenAI

cheap_llm = ChatOpenAI(model="gpt-4o-mini")  # For classification
expensive_llm = ChatOpenAI(model="gpt-4o")    # For generation

intent = await cheap_llm.invoke("Classify: {message}")
if intent.requires_creative:
    response = await expensive_llm.invoke(prompt)
```

## File Naming

### Python
- `snake_case.py` para archivos
- `PascalCase` para classes
- `snake_case` para functions/variables

### TypeScript
- `kebab-case.tsx` para components
- `PascalCase` para React components
- `camelCase` para functions/variables

### SQL
- `001_create_avatars.up.sql` para migrations (numbered)
- `snake_case` para tablas/columnas

## Comments

### When to Comment
```python
# ✅ Good: Complex business logic
def calculate_roi(revenue: float, cost: float) -> float:
    """
    Calculate ROI for avatar performance.

    ROI = (Revenue - Cost) / Cost * 100

    Winner: ROI > 500%
    Loser: ROI < 100%
    """
    return (revenue - cost) / cost * 100
```

### When NOT to Comment
```python
# ❌ Bad: Obvious code
# Get avatar by ID
avatar = await get_avatar(avatar_id)

# ❌ Bad: Commented code
# old_function()  # Delete this!
# if False:
#     legacy_code()
```

## Imports

### Python
```python
# ✅ Good: Organized imports
from typing import List, Optional
import asyncio

from fastapi import HTTPException
from pydantic import BaseModel

from app.services.avatar_service import AvatarService
from app.models.avatar import Avatar
```

### TypeScript
```typescript
// ✅ Good: Organized imports
import { useState } from "react"
import { Avatar } from "@/types"
import { Button } from "@/components/ui/button"
import { fetchAvatars } from "@/lib/api"
```

## Error Handling

### Python
```python
# ✅ Good: Specific exceptions
try:
    avatar = await avatar_service.create(data)
except DuplicateAvatarError as e:
    raise HTTPException(status_code=409, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### TypeScript
```typescript
// ✅ Good: Error boundaries
async function fetchAvatars(): Promise<Avatar[]> {
  try {
    const response = await fetch("/api/v1/avatars")
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    return response.json()
  } catch (error) {
    console.error("Failed to fetch avatars:", error)
    throw error
  }
}
```

## Cleanup Before Commit
- [ ] No console.log() o print() de debug
- [ ] No código comentado
- [ ] No archivos temporales
- [ ] Tests passing
- [ ] Type checks passing
- [ ] Linter passing
