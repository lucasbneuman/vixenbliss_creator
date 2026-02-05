# VixenBliss Creator - Industrial UI System

## Overview

Rediseño completo de la interfaz como **sistema industrial de monetización**. La UI refleja la verdadera naturaleza del proyecto: una infraestructura automatizada end-to-end para generar revenue a escala.

## Design Philosophy

### Inspiración
- Bloomberg Terminal (datos financieros prominentes)
- Stripe Dashboard (métricas de negocio claras)
- Datadog (monitoring operacional)
- AWS Console (control industrial)

### Principios
1. **Data-First**: Números grandes y prominentes
2. **Action-Oriented**: Botones de acción visibles (Clone, Kill, Pause, Scale)
3. **Industrial Aesthetics**: Terminal profesional, no "creativo"
4. **Real-Time**: Indicadores de actualización en vivo
5. **Color Coding**:
   - Verde = Revenue, Performance positiva
   - Rojo = Alertas, Underperformers, Costos críticos
   - Amarillo = Warnings, Optimización necesaria
   - Azul = Información, Métricas neutras

## Estructura de Páginas

### 1. CEO Dashboard (`/`)
**Propósito**: Centro de control ejecutivo con métricas críticas

**Componentes principales**:
- Revenue Metrics (MRR, Daily Revenue, ARPU, LTV/CAC)
- Revenue by Layer (Layer 1, 2, 3 breakdown)
- Revenue Chart (7-day trend)
- Conversion Funnel (Free → VIP)
- Operational Metrics (Content, Accounts, Response Time)
- Financial Health (Cashflow, Burn Rate, Runway)
- Top Performers Table
- Underperformers Table (kill candidates)

**Alertas**:
- Critical: Modelos underperforming
- Warning: Cuentas en riesgo de shadowban

### 2. Models Page (`/models`)
**Propósito**: Gestión del portfolio de modelos digitales

**Features**:
- Aggregate Metrics (Total MRR, Avg ARPU, Total Subs, Avg Engagement)
- Search & Filters (por status, health, niche)
- Advanced Table con sorting (MRR, ARPU, Engagement, Subscribers)
- Bulk Actions (Clone winner, Kill underperformer, Pause, Activate)
- Performance Distribution (Top/Mid/Under performers)

**Acciones disponibles**:
- Clone Model (duplicar winners)
- Kill Model (archivar underperformers)
- Pause/Activate Model
- View Details
- Export CSV

### 3. Content Factory (`/factory`)
**Propósito**: Pipeline de producción masiva de contenido

**Features**:
- Production Metrics (Produced Today, In Progress, Queued, Cost)
- Pipeline Visualization (estado real-time de batches)
- Performance Stats (Velocity, Hit Rate, Processing Time)
- Cost Analytics (breakdown por servicio: Replicate, OpenAI, R2)
- Template Performance (templates más usados y engagement)

**Monitoreo**:
- Batches en cola/processing/completados
- Progress bars en tiempo real
- Safety filter rejections
- API costs tracking

### 4. Distribution Hub (`/distribution`)
**Propósito**: Control de publicación multi-plataforma

**Features**:
- Distribution Metrics (Posts Today, Active This Week, Avg Engagement)
- Account Health Dashboard (Healthy/Warning/Critical)
- Platform Filters (TikTok, Instagram, Facebook, X)
- Accounts Table con health monitoring
- Shadowban Risk Indicators
- Platform Performance Cards
- Next 24h Schedule Preview

**Health Monitoring**:
- Shadowban risk percentage
- Last post timing
- Engagement rate por account
- Posts per week tracking

### 5. Revenue Page (`/revenue`)
**Propósito**: Analytics financiero detallado

**Features**:
- Top-Line Metrics (MRR Total, ARR, Global ARPU, LTV/CAC)
- Revenue by Layer (Layer 1, 2, 3 deep dive)
- Revenue Chart + Conversion Funnel
- Key Financial Metrics (Churn, New MRR, Expansion MRR, Avg LTV)
- Top Subscribers Table (Whales con mayor LTV)
- Pricing Tiers Configuration
- 90-Day Revenue Projection (path to $1M)

**Análisis**:
- Tier upgrade conversions
- Whale identification
- Growth levers
- Break-even analysis

## Componentes Reutilizables

### MetricCard
Tarjeta de métrica con:
- Valor grande prominente
- Delta con trend indicator
- Formato (currency, number, percentage)
- Sparkline opcional
- Variantes de color (success, danger, warning)

### ModelTable
Tabla avanzada con:
- Sorting por múltiples campos
- Health indicators
- Performance deltas
- Actions dropdown
- Responsive design

### RevenueChart
Gráfico de revenue con:
- Area/Bar chart modes
- Breakdown por layers
- Custom tooltips
- Responsive

### ConversionFunnel
Funnel visual de conversión:
- Free → Layer 1 → Layer 2 → Layer 3
- Conversion rates
- User counts
- Width proporcional

### HealthIndicator
Indicador de salud:
- Healthy (verde)
- Warning (amarillo)
- Critical (rojo)
- Badge/Icon modes

### ActionButton
Botón de acción crítica:
- Confirmación opcional
- Loading states
- Variantes (Clone, Kill, Pause, Activate)

## Color System

### Background
- Primary: `#0f172a` (slate-950)
- Card: `#1e293b` (slate-800)
- Border: `#334155` (slate-700)

### Status Colors
- Success/Revenue: `#10b981` (green-500)
- Danger/Alert: `#ef4444` (red-500)
- Warning: `#eab308` (yellow-500)
- Info: `#3b82f6` (blue-500)

### Text
- Primary: `#f1f5f9` (slate-100)
- Secondary: `#cbd5e1` (slate-300)
- Muted: `#94a3b8` (slate-400)

## Typography

### Headings
- H1: `text-4xl font-bold tracking-tight`
- H2: `text-2xl font-bold`
- H3: `text-xl font-semibold`

### Metrics
- Large Numbers: `text-3xl font-bold`
- Delta: `text-xs font-semibold`
- Labels: `text-sm text-gray-400`

## Responsive Design

### Breakpoints
- Mobile: `< 768px` - Stack all grids
- Tablet: `768px - 1024px` - 2 column grids
- Desktop: `> 1024px` - 3-4 column grids

### Sidebar
- Hidden on mobile
- Fixed on desktop (72px width)
- Contains key metrics widget

## Data Flow (Futuro)

### API Integration Points
```typescript
// CEO Dashboard
GET /api/v1/analytics/ceo-dashboard
→ Revenue metrics, top/bottom performers, operational stats

// Models
GET /api/v1/avatars?sort=mrr&order=desc
→ Full model list with performance metrics

// Content Factory
GET /api/v1/content/batches?status=processing
→ Real-time batch status

// Distribution Hub
GET /api/v1/distribution/accounts
→ Social account health + metrics

// Revenue
GET /api/v1/premium/metrics/dashboard
→ Revenue breakdown + subscriber analytics
```

### Real-Time Updates
- Polling every 30s for critical metrics (MRR, Daily Revenue)
- WebSockets para batch processing status (futuro)
- Optimistic UI updates para actions

## Performance Optimizations

### Current
- Server Components por defecto
- Client Components solo para interactividad
- Mock data para desarrollo

### Future
- React Query para data fetching
- SWR para real-time metrics
- Virtual scrolling para large tables
- Memoization de charts

## Testing Strategy

### Component Tests
```bash
npm test components/metric-card.test.tsx
npm test components/model-table.test.tsx
```

### Integration Tests
- Dashboard rendering con mock data
- Table sorting/filtering
- Action button confirmations

### E2E Tests (Futuro)
- Clone model flow
- Kill model flow
- Revenue drill-down

## Development Commands

```bash
# Desarrollo
npm run dev

# Build
npm run build

# Lint
npm run lint

# Type check
npm run type-check
```

## File Structure

```
frontend/
├── app/
│   ├── page.tsx              # CEO Dashboard
│   ├── models/page.tsx       # Models Management
│   ├── factory/page.tsx      # Content Factory
│   ├── distribution/page.tsx # Distribution Hub
│   ├── revenue/page.tsx      # Revenue Analytics
│   └── layout.tsx            # Root layout con dark theme
├── components/
│   ├── metric-card.tsx       # MetricCard component
│   ├── model-table.tsx       # ModelTable component
│   ├── revenue-chart.tsx     # RevenueChart + ConversionFunnel
│   ├── health-indicator.tsx  # HealthIndicator component
│   ├── action-button.tsx     # ActionButton component
│   ├── sidebar.tsx           # Industrial sidebar
│   └── ui/                   # shadcn/ui primitives
└── lib/
    └── utils.ts              # Utilities
```

## Next Steps

### Phase 1: API Integration
- [ ] Connect to backend endpoints
- [ ] Replace mock data with real API calls
- [ ] Implement error handling
- [ ] Add loading states

### Phase 2: Real-Time Features
- [ ] WebSocket connection para batch updates
- [ ] Live MRR counter
- [ ] Push notifications para critical alerts

### Phase 3: Advanced Features
- [ ] Model detail page con full analytics
- [ ] A/B test results visualization
- [ ] Predictive analytics dashboard
- [ ] Export reports (PDF, CSV)

### Phase 4: Mobile
- [ ] Mobile-responsive sidebar
- [ ] Touch-optimized tables
- [ ] Mobile dashboard layout

## Credits

Diseñado y desarrollado para VixenBliss Creator como sistema industrial de monetización at scale.

**Stack**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui, Recharts
**Theme**: Dark Industrial (Bloomberg Terminal inspired)
**Focus**: Data-first, Action-oriented, Revenue-driven
