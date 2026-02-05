# VixenBliss Creator - Quick Start Guide

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

Visit: **http://localhost:3000**

## Pages Available

### 1. CEO Dashboard - `/`
- Revenue metrics prominently displayed
- Top/Bottom performers tables
- Critical alerts
- Financial health overview

### 2. Models - `/models`
- Full portfolio management
- Clone/Kill/Pause actions
- Performance distribution
- Advanced filtering

### 3. Content Factory - `/factory`
- Production pipeline visualization
- Real-time batch monitoring
- Cost tracking
- Template analytics

### 4. Distribution Hub - `/distribution`
- Multi-platform overview (TikTok, IG, FB, X)
- Account health monitoring
- Shadowban risk tracking
- 24h schedule preview

### 5. Revenue - `/revenue`
- Revenue by layer breakdown
- Conversion funnel
- Top subscribers (whales)
- 90-day projection to $1M

## Key Components

### MetricCard
```tsx
<MetricCard
  title="MRR Total"
  value={156800}
  format="currency"
  delta={34.2}
  trend="up"
  variant="success"
  icon={<DollarSign />}
  sparkline={[45000, 52000, 68000, ...]}
/>
```

### ModelTable
```tsx
<ModelTable
  models={models}
  onClone={(model) => console.log("Clone", model)}
  onKill={(model) => console.log("Kill", model)}
  onPause={(model) => console.log("Pause", model)}
  onActivate={(model) => console.log("Activate", model)}
/>
```

### RevenueChart
```tsx
<RevenueChart
  data={revenueData}
  chartType="area"
  title="Revenue Breakdown"
/>
```

## Theme

Dark industrial theme by default:
- Background: `#0f172a`
- Card: `#1e293b`
- Success: `#10b981` (green)
- Danger: `#ef4444` (red)
- Warning: `#eab308` (yellow)

## Build

```bash
npm run build
```

Production build in `.next` folder.

## Deployment

```bash
npm run start
```

Or deploy to Vercel:
```bash
vercel deploy
```

## Environment Variables

Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Next Steps

1. Connect to backend API endpoints
2. Replace mock data with real API calls
3. Implement authentication
4. Add error handling
5. Add loading states

## Troubleshooting

### Build fails
```bash
rm -rf .next
npm run build
```

### Types issues
```bash
npm run type-check
```

### Port already in use
```bash
# Change port
npm run dev -- -p 3001
```

## Support

See **INDUSTRIAL_UI.md** for complete documentation.

---

**Status**: Ready for development
**Last Updated**: 2026-01-06
