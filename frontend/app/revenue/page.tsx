"use client"

import { MetricCard } from "@/components/metric-card"
import { RevenueChart, ConversionFunnel } from "@/components/revenue-chart"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DollarSign,
  TrendingUp,
  Users,
  CreditCard,
  Target,
  ArrowUpRight,
  Crown
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function RevenuePage() {
  const revenueData = [
    { date: "Jan 1", layer1: 2400, layer2: 1800, layer3: 900, total: 5100 },
    { date: "Jan 2", layer1: 2600, layer2: 2100, layer3: 1200, total: 5900 },
    { date: "Jan 3", layer1: 2800, layer2: 2400, layer3: 1400, total: 6600 },
    { date: "Jan 4", layer1: 3200, layer2: 2700, layer3: 1600, total: 7500 },
    { date: "Jan 5", layer1: 3600, layer2: 3100, layer3: 1900, total: 8600 },
    { date: "Jan 6", layer1: 4100, layer2: 3600, layer3: 2300, total: 10000 },
    { date: "Jan 7", layer1: 4500, layer2: 4200, layer3: 2800, total: 11500 },
  ]

  const conversionData = [
    { stage: "Free (Social Media)", count: 50000, conversionRate: 100 },
    { stage: "Layer 1 ($9-19)", count: 2500, conversionRate: 5.0 },
    { stage: "Layer 2 ($29-99)", count: 500, conversionRate: 20.0 },
    { stage: "Layer 3 (VIP)", count: 50, conversionRate: 10.0 },
  ]

  const topSubscribers = [
    {
      id: "1",
      username: "whale_001",
      model: "Luna Starr",
      tier: "Layer 3 (VIP)",
      mrr: 299,
      ltv: 3588,
      subscribed_since: "2023-09-15",
      engagement_score: 95
    },
    {
      id: "2",
      username: "premium_fan_42",
      model: "Aria Nova",
      tier: "Layer 3 (VIP)",
      mrr: 199,
      ltv: 2388,
      subscribed_since: "2023-10-22",
      engagement_score: 88
    },
    {
      id: "3",
      username: "superfan_luna",
      model: "Luna Starr",
      tier: "Layer 2 ($29-99)",
      mrr: 99,
      ltv: 1188,
      subscribed_since: "2023-08-10",
      engagement_score: 92
    }
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="section-head">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-high">Revenue & Monetization</h1>
          <p className="text-soft mt-1">
            Multi-layer subscription revenue analytics
          </p>
        </div>
        <Button variant="success" className="gap-2">
          <CreditCard className="h-4 w-4" />
          Configure Pricing
        </Button>
      </div>
      <div className="divider" />

      {/* Top-Line Revenue Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="MRR Total"
          value={156800}
          delta={34.2}
          deltaLabel="vs last month"
          format="currency"
          variant="success"
          icon={<DollarSign className="h-5 w-5" />}
          trend="up"
          sparkline={[45000, 52000, 68000, 89000, 112000, 134000, 156800]}
        />
        <MetricCard
          title="ARR Projection"
          value={1881600}
          deltaLabel="Annualized MRR"
          format="currency"
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <MetricCard
          title="Global ARPU"
          value={42}
          delta={8.5}
          deltaLabel="Per subscriber/month"
          format="currency"
          icon={<Users className="h-5 w-5" />}
          trend="up"
        />
        <MetricCard
          title="LTV/CAC Ratio"
          value={4.2}
          delta={15.3}
          deltaLabel="Target: >3.0"
          format="number"
          variant="success"
          icon={<Target className="h-5 w-5" />}
          trend="up"
        />
      </div>

      {/* Revenue by Layer */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="text-2xl font-bold">Revenue by Subscription Layer</h2>
            <p className="text-soft text-sm">Tier performance and growth momentum</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="panel-emerald bg-emerald-500/5">
            <CardHeader>
              <CardTitle className="text-emerald-300">Layer 1 ($9-19)</CardTitle>
              <CardDescription>Base subscription tier</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-3xl font-bold text-emerald-300">$62,700</div>
                  <p className="text-sm text-soft mt-1">MRR</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xl font-semibold">1,487</div>
                    <p className="text-xs text-soft">Subscribers</p>
                  </div>
                  <div>
                    <div className="text-xl font-semibold">$42</div>
                    <p className="text-xs text-soft">ARPU</p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-sm text-emerald-300">
                  <TrendingUp className="h-4 w-4" />
                  <span>+28.4% vs last month</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="panel-sky bg-sky-500/5">
            <CardHeader>
              <CardTitle className="text-sky-300">Layer 2 ($29-99)</CardTitle>
              <CardDescription>Premium content tier</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-3xl font-bold text-sky-300">$71,200</div>
                  <p className="text-sm text-soft mt-1">MRR</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xl font-semibold">892</div>
                    <p className="text-xs text-soft">Subscribers</p>
                  </div>
                  <div>
                    <div className="text-xl font-semibold">$80</div>
                    <p className="text-xs text-soft">ARPU</p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-sm text-sky-300">
                  <TrendingUp className="h-4 w-4" />
                  <span>+42.1% vs last month</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="panel-amber bg-amber-500/5">
            <CardHeader>
              <CardTitle className="text-amber-300 flex items-center gap-2">
                <Crown className="h-5 w-5" />
                Layer 3 (VIP)
              </CardTitle>
              <CardDescription>Personalized whale tier</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-3xl font-bold text-amber-300">$22,900</div>
                  <p className="text-sm text-soft mt-1">MRR</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xl font-semibold">78</div>
                    <p className="text-xs text-soft">Whales</p>
                  </div>
                  <div>
                    <div className="text-xl font-semibold">$294</div>
                    <p className="text-xs text-soft">ARPU</p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-sm text-amber-300">
                  <TrendingUp className="h-4 w-4" />
                  <span>+51.8% vs last month</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Charts Row */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="text-2xl font-bold">Revenue Trends</h2>
            <p className="text-soft text-sm">Layer composition and conversion flow</p>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <RevenueChart data={revenueData} chartType="area" />
          <ConversionFunnel data={conversionData} />
        </div>
      </div>

      {/* Key Financial Metrics */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="text-2xl font-bold">Financial Health</h2>
            <p className="text-soft text-sm">Churn, expansion, and LTV</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Churn Rate"
            value="3.2%"
            deltaLabel="Target: <5%"
            variant="success"
            icon={<Users className="h-5 w-5" />}
          />
          <MetricCard
            title="New MRR This Month"
            value={34500}
            format="currency"
            variant="success"
            icon={<ArrowUpRight className="h-5 w-5" />}
            deltaLabel="From new subscribers"
          />
          <MetricCard
            title="Expansion MRR"
            value={12800}
            format="currency"
            variant="success"
            icon={<TrendingUp className="h-5 w-5" />}
            deltaLabel="From tier upgrades"
          />
          <MetricCard
            title="Avg LTV"
            value={1680}
            format="currency"
            icon={<Target className="h-5 w-5" />}
            deltaLabel="Per subscriber"
          />
        </div>
      </div>

      {/* Top Subscribers (Whales) */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-2xl font-bold">VIP Subscribers</h2>
          <p className="text-soft text-sm">Highest LTV and engagement</p>
        </div>
      </div>
      <Card className="panel">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Crown className="h-5 w-5 text-purple-500" />
                Top Subscribers (Whales)
              </CardTitle>
              <CardDescription>Highest LTV customers</CardDescription>
            </div>
            <Badge variant="outline" className="text-purple-500 border-purple-500">
              {topSubscribers.length} VIP
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-white/10">
                <TableHead>Username</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead className="text-right">MRR</TableHead>
                <TableHead className="text-right">LTV</TableHead>
                <TableHead>Subscribed Since</TableHead>
                <TableHead className="text-right">Engagement</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {topSubscribers.map((sub) => (
                <TableRow key={sub.id} className="border-white/10 hover:bg-white/5">
                  <TableCell className="font-medium">{sub.username}</TableCell>
                  <TableCell>{sub.model}</TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn(
                        sub.tier.includes("Layer 3") ? "text-purple-500 border-purple-500" :
                        sub.tier.includes("Layer 2") ? "text-blue-500 border-blue-500" :
                        "text-green-500 border-green-500"
                      )}
                    >
                      {sub.tier}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-semibold text-green-500">
                    ${sub.mrr}
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    ${sub.ltv.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-soft text-sm">
                    {new Date(sub.subscribed_since).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-500 transition-all"
                          style={{ width: `${sub.engagement_score}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-purple-500 w-8">
                        {sub.engagement_score}
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pricing Tiers Configuration */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-2xl font-bold">Active Pricing Tiers</h2>
          <p className="text-soft text-sm">Current subscription configuration</p>
        </div>
      </div>
      <Card className="panel">
        <CardHeader>
          <CardTitle>Active Pricing Tiers</CardTitle>
          <CardDescription>Current subscription configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="border border-emerald-500/30 rounded-xl p-4 bg-emerald-500/5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-green-500">Layer 1</h3>
                  <Badge className="bg-emerald-500/30 text-emerald-200 border border-emerald-400/40">Active</Badge>
                </div>
                <div className="text-2xl font-bold mb-2">$9 - $19</div>
                <p className="text-sm text-soft mb-4">
                  Standard content library access
                </p>
                <ul className="space-y-1 text-sm text-soft">
                  <li>• Daily photo updates</li>
                  <li>• Basic chat access</li>
                  <li>• Community content</li>
                </ul>
              </div>

              <div className="border border-blue-500/30 rounded-lg p-4 bg-blue-500/5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-blue-500">Layer 2</h3>
                  <Badge className="bg-sky-500/30 text-sky-200 border border-sky-400/40">Active</Badge>
                </div>
                <div className="text-2xl font-bold mb-2">$29 - $99</div>
                <p className="text-sm text-soft mb-4">
                  Premium exclusive content
                </p>
                <ul className="space-y-1 text-sm text-soft">
                  <li>• Everything in Layer 1</li>
                  <li>• Premium photo sets</li>
                  <li>• Priority chat response</li>
                  <li>• Custom request queue</li>
                </ul>
              </div>

              <div className="border border-purple-500/30 rounded-lg p-4 bg-purple-500/5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-purple-500 flex items-center gap-1">
                    <Crown className="h-4 w-4" />
                    Layer 3 (VIP)
                  </h3>
                  <Badge className="bg-amber-500/30 text-amber-200 border border-amber-400/40">Active</Badge>
                </div>
                <div className="text-2xl font-bold mb-2">Custom</div>
                <p className="text-sm text-soft mb-4">
                  Personalized whale experience
                </p>
                <ul className="space-y-1 text-sm text-soft">
                  <li>• Everything in Layer 2</li>
                  <li>• Custom content requests</li>
                  <li>• 1-on-1 video calls</li>
                  <li>• Personalized interactions</li>
                  <li>• Direct phone number</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Revenue Forecasting */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-2xl font-bold">Revenue Forecasting</h2>
          <p className="text-soft text-sm">90-day runway to $1M target</p>
        </div>
      </div>
      <Card className="panel border-emerald-400/20 bg-emerald-500/5">
        <CardHeader>
          <CardTitle className="text-emerald-300">90-Day Revenue Projection</CardTitle>
          <CardDescription>Path to $1M target</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <div className="text-sm text-soft mb-1">Current MRR</div>
                <div className="text-2xl font-bold text-emerald-300">$156,800</div>
              </div>
              <div>
                <div className="text-sm text-soft mb-1">Projected 90-Day MRR</div>
                <div className="text-2xl font-bold">$425,000</div>
              </div>
              <div>
                <div className="text-sm text-soft mb-1">Target Gap</div>
                <div className="text-2xl font-bold text-yellow-500">$575,000</div>
              </div>
            </div>

            <div className="h-3 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-400 transition-all"
                style={{ width: "42.5%" }}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="border border-white/10 rounded-xl p-4">
                <h4 className="font-semibold mb-2">To Reach $1M MRR:</h4>
                <ul className="space-y-1 text-sm text-soft">
                  <li>• Need 843,200 additional MRR</li>
                  <li>• ~20,080 new Layer 1 subscribers</li>
                  <li>• OR ~10,540 new Layer 2 subscribers</li>
                  <li>• OR ~2,870 new VIP whales</li>
                  <li>• OR mixed combination (recommended)</li>
                </ul>
              </div>

              <div className="border border-white/10 rounded-xl p-4">
                <h4 className="font-semibold mb-2">Growth Levers:</h4>
                <ul className="space-y-1 text-sm text-soft">
                  <li>• Scale to 1000 active models</li>
                  <li>• Increase Layer 1 → Layer 2 conversion</li>
                  <li>• Optimize DM automation for upsells</li>
                  <li>• Launch VIP recruitment campaigns</li>
                  <li>• Reduce churn with engagement AI</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
