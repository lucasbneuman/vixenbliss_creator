"use client"

import { useState } from "react"
import { MetricCard } from "@/components/metric-card"
import { HealthIndicator, HealthStats } from "@/components/health-indicator"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  Send,
  Calendar,
  CheckCircle2,
  XCircle,
  Eye
} from "lucide-react"
import { cn } from "@/lib/utils"

interface SocialAccount {
  id: string
  platform: "tiktok" | "instagram" | "facebook" | "twitter"
  model_name: string
  username: string
  followers: number
  health: "healthy" | "warning" | "critical"
  last_post: string
  engagement_rate: number
  posts_this_week: number
  shadowban_risk: number
}

export default function DistributionHubPage() {
  const [selectedPlatform, setSelectedPlatform] = useState<string>("all")

  const accounts: SocialAccount[] = [
    {
      id: "1",
      platform: "tiktok",
      model_name: "Luna Starr",
      username: "@lunastarr_fit",
      followers: 45200,
      health: "healthy",
      last_post: "2 hours ago",
      engagement_rate: 8.2,
      posts_this_week: 14,
      shadowban_risk: 5
    },
    {
      id: "2",
      platform: "instagram",
      model_name: "Luna Starr",
      username: "@lunastarr.fit",
      followers: 32800,
      health: "healthy",
      last_post: "4 hours ago",
      engagement_rate: 6.4,
      posts_this_week: 12,
      shadowban_risk: 8
    },
    {
      id: "3",
      platform: "tiktok",
      model_name: "Aria Nova",
      username: "@arianova_life",
      followers: 28900,
      health: "warning",
      last_post: "1 day ago",
      engagement_rate: 4.2,
      posts_this_week: 8,
      shadowban_risk: 35
    },
    {
      id: "4",
      platform: "instagram",
      model_name: "Maya Eclipse",
      username: "@maya.eclipse",
      followers: 18500,
      health: "critical",
      last_post: "3 days ago",
      engagement_rate: 1.8,
      posts_this_week: 2,
      shadowban_risk: 85
    }
  ]

  const filteredAccounts = selectedPlatform === "all"
    ? accounts
    : accounts.filter(a => a.platform === selectedPlatform)

  const totalPosts = 342
  const postsToday = 48
  const healthyAccounts = accounts.filter(a => a.health === "healthy").length
  const warningAccounts = accounts.filter(a => a.health === "warning").length
  const criticalAccounts = accounts.filter(a => a.health === "critical").length
  const totalAccounts = accounts.length

  const avgEngagement = accounts.reduce((sum, a) => sum + a.engagement_rate, 0) / accounts.length

  const getPlatformIcon = (platform: string) => {
    const icons: Record<string, string> = {
      tiktok: "TT",
      instagram: "IG",
      facebook: "FB",
      twitter: "X"
    }
    return icons[platform] || "SOC"
  }

  const getPlatformColor = (platform: string) => {
    const colors: Record<string, string> = {
      tiktok: "bg-pink-500/20 text-pink-300 border-pink-500/30",
      instagram: "bg-purple-500/20 text-purple-300 border-purple-500/30",
      facebook: "bg-blue-500/20 text-blue-300 border-blue-500/30",
      twitter: "bg-sky-500/20 text-sky-300 border-sky-500/30"
    }
    return colors[platform] || "bg-white/10 text-soft border-white/10"
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="section-head">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-high">Distribution Hub</h1>
          <p className="text-soft mt-1">
            Multi-platform automated publishing control center
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="gap-2">
            <Calendar className="h-4 w-4" />
            Schedule Posts
          </Button>
          <Button variant="success" className="gap-2">
            <Send className="h-4 w-4" />
            Publish Now
          </Button>
        </div>
      </div>
      <div className="divider" />

      {/* Shadowban Alerts */}
      {criticalAccounts > 0 && (
        <Alert className="border-red-500/30 bg-red-500/15">
          <AlertTriangle className="h-4 w-4 text-red-300" />
          <AlertTitle className="text-red-200">
            {criticalAccounts} Account{criticalAccounts > 1 ? 's' : ''} at High Shadowban Risk
          </AlertTitle>
          <AlertDescription className="text-red-100/90">
            Immediate action required. Reduce posting frequency and review content patterns.
          </AlertDescription>
        </Alert>
      )}

      {/* Distribution Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Posts Today"
          value={postsToday}
          format="number"
          variant="success"
          icon={<Send className="h-5 w-5" />}
          deltaLabel="Across all platforms"
          sparkline={[32, 38, 42, 45, 41, 46, 48]}
        />
        <MetricCard
          title="Active This Week"
          value={totalPosts}
          format="number"
          icon={<Activity className="h-5 w-5" />}
          deltaLabel="Total publications"
        />
        <MetricCard
          title="Avg Engagement"
          value={`${avgEngagement.toFixed(1)}%`}
          icon={<TrendingUp className="h-5 w-5" />}
          deltaLabel="Across all accounts"
        />
        <Card className="panel">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-soft">
              Account Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <HealthStats
              healthy={healthyAccounts}
              warning={warningAccounts}
              critical={criticalAccounts}
              total={totalAccounts}
            />
          </CardContent>
        </Card>
      </div>

      {/* Platform Filter */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Platform Filter</h2>
          <p className="text-soft text-sm">Slice performance by channel</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant={selectedPlatform === "all" ? "default" : "outline"}
          onClick={() => setSelectedPlatform("all")}
          className={cn(
            "gap-2",
            selectedPlatform === "all" && "bg-white/15 text-high border-white/10"
          )}
        >
          All Platforms
        </Button>
        <Button
          variant={selectedPlatform === "tiktok" ? "default" : "outline"}
          onClick={() => setSelectedPlatform("tiktok")}
          className={cn(
            "gap-2",
            selectedPlatform === "tiktok" && "bg-pink-500/20 text-high border-pink-500/30"
          )}
        >
          {getPlatformIcon("tiktok")} TikTok
        </Button>
        <Button
          variant={selectedPlatform === "instagram" ? "default" : "outline"}
          onClick={() => setSelectedPlatform("instagram")}
          className={cn(
            "gap-2",
            selectedPlatform === "instagram" && "bg-purple-500/20 text-high border-purple-500/30"
          )}
        >
          {getPlatformIcon("instagram")} Instagram
        </Button>
        <Button
          variant={selectedPlatform === "facebook" ? "default" : "outline"}
          onClick={() => setSelectedPlatform("facebook")}
          className={cn(
            "gap-2",
            selectedPlatform === "facebook" && "bg-blue-500/20 text-high border-blue-500/30"
          )}
        >
          {getPlatformIcon("facebook")} Facebook
        </Button>
        <Button
          variant={selectedPlatform === "twitter" ? "default" : "outline"}
          onClick={() => setSelectedPlatform("twitter")}
          className={cn(
            "gap-2",
            selectedPlatform === "twitter" && "bg-sky-500/20 text-high border-sky-500/30"
          )}
        >
          {getPlatformIcon("twitter")} X (Twitter)
        </Button>
      </div>

      {/* Accounts Table */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Social Media Accounts</h2>
          <p className="text-soft text-sm">Health, engagement, and risk overview</p>
        </div>
      </div>
      <Card className="panel">
        <CardHeader>
          <CardTitle>Social Media Accounts</CardTitle>
          <CardDescription>
            Showing {filteredAccounts.length} of {accounts.length} accounts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-white/10">
                <TableHead>Platform</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Username</TableHead>
                <TableHead className="text-right">Followers</TableHead>
                <TableHead>Health</TableHead>
                <TableHead className="text-right">Engagement</TableHead>
                <TableHead className="text-right">Posts/Week</TableHead>
                <TableHead className="text-right">Shadowban Risk</TableHead>
                <TableHead className="text-right">Last Post</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAccounts.map((account) => (
                <TableRow key={account.id} className="border-white/10 hover:bg-white/5">
                  <TableCell>
                    <Badge className={cn("border", getPlatformColor(account.platform))}>
                      {getPlatformIcon(account.platform)} {account.platform}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium">{account.model_name}</TableCell>
                  <TableCell className="text-soft">{account.username}</TableCell>
                  <TableCell className="text-right font-semibold">
                    {account.followers.toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <HealthIndicator status={account.health} showBadge />
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={cn(
                      "font-semibold",
                      account.engagement_rate >= 6 ? "text-green-500" :
                      account.engagement_rate >= 4 ? "text-yellow-500" :
                      "text-red-500"
                    )}>
                      {account.engagement_rate.toFixed(1)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right">{account.posts_this_week}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            "h-full transition-all",
                            account.shadowban_risk < 30 ? "bg-green-500" :
                            account.shadowban_risk < 60 ? "bg-yellow-500" :
                            "bg-red-500"
                          )}
                          style={{ width: `${account.shadowban_risk}%` }}
                        />
                      </div>
                      <span className={cn(
                        "text-xs font-semibold w-10 text-right",
                        account.shadowban_risk < 30 ? "text-green-500" :
                        account.shadowban_risk < 60 ? "text-yellow-500" :
                        "text-red-500"
                      )}>
                        {account.shadowban_risk}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right text-soft text-sm">
                    {account.last_post}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Platform Performance */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Platform Performance</h2>
          <p className="text-soft text-sm">Comparative stats by network</p>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="panel-amber bg-pink-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-pink-500">
              {getPlatformIcon("tiktok")} TikTok
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Accounts</span>
                <span className="font-semibold">24</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Avg Engagement</span>
                <span className="font-semibold text-green-500">7.2%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Posts This Week</span>
                <span className="font-semibold">168</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="panel-sky bg-purple-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-500">
              {getPlatformIcon("instagram")} Instagram
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Accounts</span>
                <span className="font-semibold">24</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Avg Engagement</span>
                <span className="font-semibold text-yellow-500">5.8%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Posts This Week</span>
                <span className="font-semibold">144</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="panel-sky bg-blue-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-500">
              {getPlatformIcon("facebook")} Facebook
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Accounts</span>
                <span className="font-semibold">18</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Avg Engagement</span>
                <span className="font-semibold text-yellow-500">4.2%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Posts This Week</span>
                <span className="font-semibold">108</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="panel-emerald bg-sky-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sky-500">
              {getPlatformIcon("twitter")} X (Twitter)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Accounts</span>
                <span className="font-semibold">12</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Avg Engagement</span>
                <span className="font-semibold text-red-500">3.1%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-soft">Posts This Week</span>
                <span className="font-semibold">84</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Posting Schedule Preview */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Upcoming Schedule</h2>
          <p className="text-soft text-sm">Next 24 hours of automation</p>
        </div>
      </div>
      <Card className="panel">
        <CardHeader>
          <CardTitle>Next 24 Hours Schedule</CardTitle>
          <CardDescription>Upcoming automated publications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { time: "14:00", model: "Luna Starr", platform: "tiktok", content: "Gym Workout Video" },
              { time: "15:30", model: "Aria Nova", platform: "instagram", content: "Morning Routine Reel" },
              { time: "17:00", model: "Maya Eclipse", platform: "facebook", content: "Fashion Photoshoot" },
              { time: "18:30", model: "Luna Starr", platform: "instagram", content: "Fitness Tips Story" },
              { time: "20:00", model: "Aria Nova", platform: "tiktok", content: "Lifestyle Vlog" }
            ].map((post, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 border border-white/10 rounded-xl"
              >
                <div className="flex items-center gap-4">
                  <div className="text-center min-w-[60px]">
                    <div className="text-sm font-semibold">{post.time}</div>
                    <div className="text-xs text-soft">Today</div>
                  </div>
                  <Badge className={cn("border", getPlatformColor(post.platform))}>
                    {getPlatformIcon(post.platform)}
                  </Badge>
                  <div>
                    <p className="font-medium">{post.model}</p>
                    <p className="text-sm text-soft">{post.content}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  Edit
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
