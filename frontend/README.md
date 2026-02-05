# VixenBliss Creator - Industrial Frontend

**Industrial monetization control system designed for 1000-model scale operations.**

---

## Quick Start

```bash
npm install
npm run dev
```

Visit **http://localhost:3000**

---

## Pages

| Route | Page | Purpose |
|-------|------|---------|
| `/` | CEO Dashboard | Executive control center with revenue metrics |
| `/models` | Models Management | Portfolio of 48+ digital models |
| `/factory` | Content Factory | Production pipeline (1000 pieces/day) |
| `/distribution` | Distribution Hub | Multi-platform publishing (TikTok, IG, FB, X) |
| `/revenue` | Revenue Analytics | Financial breakdown by subscription layer |

---

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode)
- **UI**: shadcn/ui + TailwindCSS
- **Charts**: Recharts
- **State**: React Server Components (default)
- **Theme**: Dark Industrial (Bloomberg Terminal inspired)

---

## Key Features

### Data-First Design
- Large prominent numbers (MRR, ARPU, LTV/CAC)
- Real-time metrics with delta indicators
- Sparklines for trend visualization

### Action-Oriented
- Clone/Kill/Pause buttons visible in tables
- Confirmation dialogs for destructive actions
- Quick actions from dashboard

### Industrial Aesthetics
- Dark color palette (#0f172a background)
- Professional typography
- Color coding: Green (revenue), Red (alerts), Yellow (warnings), Blue (info)

### Responsive
- Mobile: Single column stacking
- Tablet: 2-column grids
- Desktop: 3-4 column grids

---

## Components

### Core Components

**MetricCard**
```tsx
<MetricCard
  title="MRR Total"
  value={156800}
  format="currency"
  delta={34.2}
  trend="up"
  variant="success"
  sparkline={[45000, 52000, 68000, ...]}
/>
```

**ModelTable**
```tsx
<ModelTable
  models={models}
  onClone={handleClone}
  onKill={handleKill}
  onPause={handlePause}
  onActivate={handleActivate}
/>
```

**RevenueChart**
```tsx
<RevenueChart
  data={revenueData}
  chartType="area"
  title="Revenue Breakdown"
/>
```

**HealthIndicator**
```tsx
<HealthIndicator
  status="healthy"
  showBadge
/>
```

**ActionButton**
```tsx
<QuickActionButton
  action="clone"
  onAction={handleClone}
  itemName="Luna Starr"
/>
```

---

## Development

### Install Dependencies
```bash
npm install
```

### Run Dev Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

### Start Production Server
```bash
npm run start
```

### Type Check
```bash
npm run type-check
```

### Lint
```bash
npm run lint
```

---

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # CEO Dashboard
│   ├── models/page.tsx       # Models Management
│   ├── factory/page.tsx      # Content Factory
│   ├── distribution/page.tsx # Distribution Hub
│   ├── revenue/page.tsx      # Revenue Analytics
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   ├── metric-card.tsx
│   ├── model-table.tsx
│   ├── revenue-chart.tsx
│   ├── health-indicator.tsx
│   ├── action-button.tsx
│   ├── sidebar.tsx
│   └── ui/                   # shadcn/ui primitives
└── lib/
    └── utils.ts
```

---

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_POLLING_INTERVAL=30000
```

---

## Color System

```css
/* Success / Revenue */
--green-500: #10b981

/* Danger / Alerts */
--red-500: #ef4444

/* Warning */
--yellow-500: #eab308

/* Info */
--blue-500: #3b82f6

/* Background */
--slate-950: #0f172a
--slate-800: #1e293b
--slate-700: #334155
```

---

## Next Steps

### Phase 1: API Integration
- [ ] Connect to backend endpoints
- [ ] Replace mock data
- [ ] Implement error handling
- [ ] Add loading states

### Phase 2: Real-Time Features
- [ ] WebSocket connection
- [ ] Live MRR counter
- [ ] Push notifications

### Phase 3: Advanced Features
- [ ] Model detail page
- [ ] Analytics deep-dive
- [ ] Settings page
- [ ] Export reports

---

## Documentation

- **[INDUSTRIAL_UI.md](./INDUSTRIAL_UI.md)**: Complete UI system documentation
- **[QUICK_START.md](./QUICK_START.md)**: Developer quick start guide
- **[../DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)**: Deployment checklist
- **[../EXECUTIVE_SUMMARY.md](../EXECUTIVE_SUMMARY.md)**: Executive summary

---

## Build Status

```
✓ Compiled successfully
✓ Generating static pages (10/10)

Route (app)              Size     First Load JS
┌ /                      4.32 kB         231 kB
├ /distribution          6.8 kB          102 kB
├ /factory               6.98 kB         102 kB
├ /models                3.96 kB         129 kB
└ /revenue               6.03 kB         202 kB
```

---

## Support

For issues or questions, see:
- Technical docs: `INDUSTRIAL_UI.md`
- API integration: `DEPLOYMENT_CHECKLIST.md`
- Quick start: `QUICK_START.md`

---

**Version**: 1.0.0
**Status**: ✅ Ready for API Integration
**Last Updated**: 2026-01-06
