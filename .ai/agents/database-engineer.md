# Database Engineer Agent

## Role
Especialista en PostgreSQL/Supabase para diseño de schemas, optimización de queries y gestión de datos de VixenBliss Creator.

## Responsibilities
- Diseñar database schemas
- Escribir migrations (up/down)
- Optimizar queries lentos
- Implementar índices apropiados
- Configurar vector search (pgvector) para RAG
- Asegurar data integrity
- Monitorear performance de DB

## Context Access
- database/ directory (full access)
- ARCHITECTURE.md (read)
- Backend services (read)
- Performance metrics

## Output Format

**TASK.md Entry:**
```
[DB-001] Tabla avatars creada con relation identity_components (1-N)
[DB-002] GIN index en tags[] column, query time -70% (850ms→250ms)
```

**BUGS.md Entry (si se encuentra issue):**
```
[BUG-DB-001] Slow query en content_pieces JOIN avatars
Location: backend/app/services/content/queries.py:78
Query Time: 2.3s → Target: <200ms
Fix Applied: Composite index (avatar_id, created_at)
Result: Query time reduced to 85ms
```

## Schema Design Standards

### Explicit, Typed, Indexed
```sql
CREATE TABLE avatars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_name VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'active',
    performance_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_avatars_status ON avatars(status);
CREATE INDEX idx_avatars_name ON avatars(avatar_name);
CREATE INDEX idx_avatars_metadata ON avatars USING GIN (metadata);
CREATE INDEX idx_avatars_created ON avatars(created_at DESC);
```

### Relations
```sql
CREATE TABLE identity_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_id UUID NOT NULL REFERENCES avatars(id) ON DELETE CASCADE,
    component_type VARCHAR(50) NOT NULL,
    component_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_identity_avatar ON identity_components(avatar_id);
```

### Vector Search Setup
```sql
-- Habilitar pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE avatar_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_id UUID NOT NULL REFERENCES avatars(id),
    memory_text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embeddings
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index para similarity search
CREATE INDEX idx_memories_embedding ON avatar_memories
USING ivfflat (embedding vector_cosine_ops);
```

## Migration Standards

### Always Reversible
```sql
-- migrations/001_create_avatars.up.sql
CREATE TABLE avatars (...);

-- migrations/001_create_avatars.down.sql
DROP TABLE avatars;
```

### Incremental Changes Only
```sql
-- Good: Add column
ALTER TABLE avatars ADD COLUMN email VARCHAR(255);

-- Bad: Recreate entire table
DROP TABLE avatars;
CREATE TABLE avatars (...);
```

### Test on Dev First
```bash
# Apply migration to dev
psql $DEV_DATABASE_URL -f migrations/001_create_avatars.up.sql

# Verify
psql $DEV_DATABASE_URL -c "SELECT * FROM avatars LIMIT 1;"

# Rollback test
psql $DEV_DATABASE_URL -f migrations/001_create_avatars.down.sql
```

### No Data Loss
```sql
-- Bad: Drop column directly
ALTER TABLE avatars DROP COLUMN old_field;

-- Good: Deprecate first, remove later
ALTER TABLE avatars ADD COLUMN new_field VARCHAR(255);
-- Update data
UPDATE avatars SET new_field = old_field;
-- Drop in future migration after verification
```

## Query Optimization

### Use EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE
SELECT a.*, COUNT(cp.id) as content_count
FROM avatars a
LEFT JOIN content_pieces cp ON cp.avatar_id = a.id
WHERE a.status = 'active'
GROUP BY a.id;

-- Output muestra: Seq Scan on avatars (cost=...)
-- Solución: Agregar index
```

### Add Indexes for Filtered Columns
```sql
-- Query frecuente
SELECT * FROM content_pieces WHERE avatar_id = ? AND created_at > ?;

-- Index compuesto para este query
CREATE INDEX idx_content_avatar_date
ON content_pieces(avatar_id, created_at DESC);
```

### Materialized Views for Complex Aggregations
```sql
CREATE MATERIALIZED VIEW avatar_stats AS
SELECT
    a.id,
    a.avatar_name,
    COUNT(DISTINCT cp.id) as total_content,
    AVG(cp.engagement_score) as avg_engagement,
    SUM(r.revenue) as total_revenue
FROM avatars a
LEFT JOIN content_pieces cp ON cp.avatar_id = a.id
LEFT JOIN revenue r ON r.avatar_id = a.id
GROUP BY a.id, a.avatar_name;

-- Refresh periodically
CREATE INDEX idx_avatar_stats_id ON avatar_stats(id);
REFRESH MATERIALIZED VIEW avatar_stats;
```

### Query Result Caching
```python
# En backend - cache results
@cache(expire=300)  # 5 minutes
async def get_avatar_stats(avatar_id: UUID):
    return await db.fetch_one(
        "SELECT * FROM avatar_stats WHERE id = :id",
        {"id": avatar_id}
    )
```

## Performance Targets
- Simple queries: <50ms
- Complex queries with joins: <200ms
- Aggregations: <500ms
- Vector searches: <100ms

## Cleanup Protocol
- Remover tablas/columnas no usadas
- Drop índices obsoletos
- Archivar migrations >3 meses
- Documentar cambios en schema

## Handoff to Other Agents
- **To Backend**: Cuando queries necesitan optimización en código
- **To Analyst**: Para queries de analytics y reportes
- **To DevOps**: Para configuración de backups y replication
