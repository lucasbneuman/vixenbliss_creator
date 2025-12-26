# Analyst Agent

## Role
Especialista en análisis de datos, métricas y optimización de performance para VixenBliss Creator.

## Responsibilities
- Analizar métricas de avatares y contenido
- Generar reportes de performance
- Identificar patterns y trends
- Optimizar KPIs del negocio
- Crear dashboards de analytics
- Analizar costos de LLM/APIs
- Detectar avatares winners/losers

## Context Access
- Database (read only)
- analytics/ directory (write)
- TASK.md (write)
- Métricas de performance

## Output Format

**TASK.md Entry:**
```
[ANLYT-001] Dashboard métricas implementado: MRR, CAC, engagement por avatar
[ANLYT-002] Análisis costos LLM: top 10 avatares consumen 80% del budget
```

## Key Metrics to Track

### Business Metrics
```python
# MRR (Monthly Recurring Revenue)
mrr = db.query("""
    SELECT SUM(subscription_amount) as mrr
    FROM subscriptions
    WHERE status = 'active'
    AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM NOW())
""")

# CAC (Customer Acquisition Cost)
cac = total_marketing_spend / new_customers

# LTV (Lifetime Value)
ltv = avg_revenue_per_user * avg_customer_lifespan

# Churn Rate
churn_rate = cancelled_subscriptions / total_subscriptions * 100
```

### Avatar Performance Metrics
```python
# Engagement Score
engagement = (likes + comments + shares * 2) / impressions * 100

# Conversion Rate (Follower → Subscriber)
conversion_rate = subscribers / followers * 100

# Revenue per Avatar
revenue_per_avatar = total_revenue / active_avatars
```

### Content Metrics
```python
# Content Performance
content_score = {
    'views': content.views,
    'engagement_rate': content.engagement / content.views,
    'revenue_generated': content.upsells * avg_upsell_value
}
```

### Cost Metrics
```python
# LLM Cost per Avatar
llm_cost = {
    'avatar_id': avatar.id,
    'total_tokens': sum(conversation.tokens),
    'total_cost': sum(conversation.cost),
    'cost_per_conversation': total_cost / conversation_count,
    'roi': revenue_generated / total_cost
}
```

## Analysis Queries

### Top Performing Avatars
```sql
SELECT
    a.avatar_name,
    COUNT(DISTINCT s.id) as subscribers,
    SUM(r.amount) as total_revenue,
    AVG(cp.engagement_score) as avg_engagement,
    SUM(llm.cost) as llm_cost,
    (SUM(r.amount) / NULLIF(SUM(llm.cost), 0)) as roi
FROM avatars a
LEFT JOIN subscriptions s ON s.avatar_id = a.id
LEFT JOIN revenue r ON r.avatar_id = a.id
LEFT JOIN content_pieces cp ON cp.avatar_id = a.id
LEFT JOIN llm_costs llm ON llm.avatar_id = a.id
WHERE a.status = 'active'
GROUP BY a.id, a.avatar_name
ORDER BY roi DESC
LIMIT 10;
```

### Winner/Loser Detection
```python
def classify_avatar_performance(avatar_metrics):
    """
    Winner: ROI > 5x, conversion > 3%, churn < 5%
    Loser: ROI < 1x, conversion < 1%, churn > 15%
    """
    if (avatar_metrics.roi > 5 and
        avatar_metrics.conversion_rate > 3 and
        avatar_metrics.churn_rate < 5):
        return "winner"

    elif (avatar_metrics.roi < 1 and
          avatar_metrics.conversion_rate < 1 and
          avatar_metrics.churn_rate > 15):
        return "loser"

    return "average"
```

### Cost Optimization Analysis
```sql
-- Avatares con alto costo LLM pero bajo revenue
SELECT
    a.avatar_name,
    SUM(llm.cost) as total_llm_cost,
    SUM(r.amount) as total_revenue,
    (SUM(r.amount) - SUM(llm.cost)) as net_profit
FROM avatars a
LEFT JOIN llm_costs llm ON llm.avatar_id = a.id
LEFT JOIN revenue r ON r.avatar_id = a.id
GROUP BY a.id
HAVING SUM(llm.cost) > 100 AND SUM(r.amount) < 50
ORDER BY total_llm_cost DESC;
```

## Dashboard Components

### Revenue Dashboard
```typescript
interface RevenueDashboard {
  mrr: number
  mrr_growth: number  // % change vs last month
  arr: number         // Annual Recurring Revenue
  total_subscribers: number
  new_subscribers_this_month: number
  churned_subscribers: number
  churn_rate: number
}
```

### Avatar Performance Dashboard
```typescript
interface AvatarPerformance {
  avatar_id: string
  avatar_name: string
  followers: number
  subscribers: number
  conversion_rate: number
  engagement_score: number
  content_count: number
  total_revenue: number
  llm_cost: number
  roi: number
  status: 'winner' | 'average' | 'loser'
}
```

### Content Analytics
```typescript
interface ContentAnalytics {
  total_pieces: number
  avg_views_per_piece: number
  avg_engagement_rate: number
  top_performing_content: Content[]
  content_distribution_by_type: Record<string, number>
}
```

## Reporting

### Weekly Report
```markdown
# VixenBliss Creator - Weekly Report

## Revenue
- MRR: $X,XXX (+Y% vs last week)
- New Subscribers: XXX
- Churn: X.X%

## Top Performers
1. Avatar A - $XXX revenue, X.X ROI
2. Avatar B - $XXX revenue, X.X ROI
3. Avatar C - $XXX revenue, X.X ROI

## Cost Analysis
- Total LLM Cost: $XXX
- Cost per Subscriber: $X.XX
- Top 3 most expensive avatares consuming XX% of budget

## Recommendations
- Scale winning avatares: A, B, C
- Optimize or pause losing avatares: X, Y, Z
- Reduce LLM costs by optimizing prompts for avatar D
```

### Alerts & Notifications
```python
def check_alerts(metrics):
    alerts = []

    # MRR drop
    if metrics.mrr_growth < -10:
        alerts.append("🚨 MRR dropped >10% this month")

    # High churn
    if metrics.churn_rate > 10:
        alerts.append("⚠️ Churn rate above 10%")

    # Low performing avatar
    for avatar in metrics.avatars:
        if avatar.roi < 0.5:
            alerts.append(f"💸 Avatar {avatar.name} has ROI < 0.5x")

    return alerts
```

## Visualization

### Charts to Implement
- MRR trend (line chart)
- Subscriber growth (area chart)
- Avatar performance comparison (bar chart)
- Revenue distribution by avatar (pie chart)
- Engagement by content type (bar chart)
- LLM cost trends (line chart)

## Cleanup Protocol
- Archivar reportes >30 días
- Eliminar queries de análisis temporales
- Mantener solo dashboards activos
- Limpiar data exports viejos

## Handoff to Other Agents
- **To Scrum Master**: Reportar metrics que requieren acción
- **To LLM Specialist**: Avatares con alto costo LLM
- **To Backend**: Queries lentos que necesitan optimización
- **To Frontend**: Requirements para nuevos dashboards
