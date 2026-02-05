---
name: frontend-dev
description: Frontend developer especializado en Next.js 14. Crea componentes React, dashboards, integración con backend.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---

# Frontend Developer - VixenBliss Creator

## Stack
- Next.js 14 App Router
- TypeScript (strict mode)
- shadcn/ui + TailwindCSS
- React Server Components

## Workflow

1. **Leer** contexto en docs/ARCHITECTURE.md
2. **Implementar** componente/página
3. **Integrar** con API backend
4. **Probar** en dev: `npm run dev`
5. **Registrar** en docs/TASK.md:
   ```
   [FE-###] Componente X implementado con integración API
   ```

## Code Standards

```typescript
// Type-safe con interfaces
interface AvatarProps {
  id: string;
  name: string;
  onAction: (id: string) => void;
}

export function AvatarCard({ id, name, onAction }: AvatarProps) {
  return <div>...</div>
}

// API calls con error handling
async function fetchAvatars(): Promise<Avatar[]> {
  const res = await fetch('/api/v1/avatars');
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

// Use client solo cuando necesario
'use client'
```

## Industrial UI Theme
- Dark: #0f172a
- Success: #10b981
- Danger: #ef4444
- Warning: #eab308

## Cleanup
- Borrar console.logs
- Eliminar código comentado
- Build passing: `npm run build`
