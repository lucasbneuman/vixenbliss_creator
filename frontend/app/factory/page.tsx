"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  ImagePlus,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  RefreshCw
} from "lucide-react"
import {
  fetchTemplates,
  fetchCostSummary,
  fetchAvatars,
  type Template,
  type ContentBatch,
  type CostSummary,
} from "@/lib/api"
import { LoadingSpinner } from "@/components/loading-state"
import { ErrorDisplay } from "@/components/error-boundary"
import { BatchGenerationDialog } from "@/components/batch-generation-dialog"
import type { Avatar } from "@/types/avatar"

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

const getMockBatches = (): ContentBatch[] => [
  {
    id: "batch-001",
    avatar_id: "1",
    model_name: "Luna Starr",
    template: "Fitness - Gym Workout",
    total_pieces: 50,
    completed: 45,
    failed: 2,
    status: "processing",
    created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    estimated_cost: 12.50
  },
  {
    id: "batch-002",
    avatar_id: "2",
    model_name: "Aria Nova",
    template: "Lifestyle - Morning Routine",
    total_pieces: 50,
    completed: 50,
    failed: 0,
    status: "completed",
    created_at: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    estimated_cost: 12.50
  },
  {
    id: "batch-003",
    avatar_id: "3",
    model_name: "Maya Eclipse",
    template: "Fashion - Street Style",
    total_pieces: 50,
    completed: 0,
    failed: 0,
    status: "queued",
    created_at: new Date().toISOString(),
    estimated_cost: 12.50
  }
]

export default function ContentFactoryPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [costSummary, setCostSummary] = useState<CostSummary | null>(null)
  const [batches, setBatches] = useState<ContentBatch[]>(getMockBatches())
  const [avatars, setAvatars] = useState<Avatar[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [showBatchDialog, setShowBatchDialog] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [templatesData, costsData, avatarsData] = await Promise.all([
        fetchTemplates(),
        fetchCostSummary(DEMO_USER_ID, 30),
        fetchAvatars(DEMO_USER_ID)
      ])

      setTemplates(templatesData)
      setCostSummary(costsData)
      setAvatars(avatarsData)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to load factory data"))
      setTemplates(getMockTemplates())
      setCostSummary(getMockCostSummary())
    } finally {
      setLoading(false)
    }
  }

  const getMockTemplates = (): Template[] => [
    {
      id: "t1",
      name: "Fitness - Gym Workout",
      category: "fitness",
      tier: "capa1",
      prompt_template: "fitness workout at gym",
      negative_prompt: "",
      style_modifiers: []
    },
    {
      id: "t2",
      name: "Lifestyle - Morning Routine",
      category: "lifestyle",
      tier: "capa1",
      prompt_template: "morning routine lifestyle",
      negative_prompt: "",
      style_modifiers: []
    },
  ]

  const getMockCostSummary = (): CostSummary => ({
    total_cost: 1035.40,
    by_operation: {
      lora_inference: 892.40,
      hook_generation: 124.80,
      storage: 18.20
    },
    by_provider: {
      replicate: 892.40,
      openai: 124.80,
      cloudflare_r2: 18.20
    },
    count: 847
  })

  const totalProducedToday = batches.reduce((sum, b) => sum + b.completed, 0)

  const getStatusIcon = (status: ContentBatch["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-brand-100" />
      case "processing":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case "queued":
        return <Clock className="h-4 w-4 text-yellow-500" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />
    }
  }

  const getStatusBadge = (status: ContentBatch["status"]) => {
    const configs = {
      completed: { variant: "default" as const, className: "bg-[hsl(var(--brand-1))]/85 text-slate-100" },
      processing: { variant: "default" as const, className: "bg-sky-600/80 text-slate-100" },
      queued: { variant: "default" as const, className: "bg-yellow-600 text-slate-100" },
      failed: { variant: "destructive" as const, className: "" }
    }

    const config = configs[status]

    return (
      <Badge variant={config.variant} className={config.className}>
        {status}
      </Badge>
    )
  }

  if (loading && !costSummary) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-semibold text-high">Sistema 2: Fabrica de Contenido</h1>
          <p className="text-soft mt-1">Cargando datos...</p>
        </div>
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-high">Sistema 2: Fabrica de Contenido</h1>
        <p className="text-soft max-w-2xl">
          Selecciona un avatar, define prompts y produce lotes sin romper contratos API v1.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="success"
          className="gap-2"
          onClick={() => setShowBatchDialog(true)}
          disabled={avatars.length === 0}
        >
          <ImagePlus className="h-4 w-4" />
          Crear lote de contenido
        </Button>
        <Button variant="outline" onClick={loadData} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
        <Button variant="outline" asChild>
          <Link href="/avatars">Ver avatares</Link>
        </Button>
      </div>

      {error && (
        <ErrorDisplay error={error} />
      )}

      {avatars.length === 0 && (
        <Card className="panel border-dashed border-white/20">
          <CardContent className="py-8">
            <div className="font-semibold">Primero crea un avatar</div>
            <p className="text-sm text-soft mt-1">
              Para generar contenido necesitas al menos un avatar listo.
            </p>
            <Button variant="outline" className="mt-3" asChild>
              <Link href="/avatars">Ir a crear avatar</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Avatares disponibles</CardTitle>
            <CardDescription>Listos para usar</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {avatars.length}
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Plantillas</CardTitle>
            <CardDescription>Para crear contenido</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {templates.length}
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Piezas hoy</CardTitle>
            <CardDescription>Producción completada</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {totalProducedToday}
          </CardContent>
        </Card>
      </div>

      <Card className="panel">
        <CardHeader>
          <CardTitle>Lotes recientes</CardTitle>
          <CardDescription>Estado de producción</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {batches.map((batch) => {
              const progress = (batch.completed / batch.total_pieces) * 100

              return (
                <div
                  key={batch.id}
                  className="border border-white/10 rounded-xl p-4 hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        {getStatusIcon(batch.status)}
                        <h3 className="font-semibold">{batch.model_name}</h3>
                        {getStatusBadge(batch.status)}
                      </div>
                      <p className="text-sm text-soft">{batch.template}</p>
                      <p className="text-xs text-soft mt-1">
                        Lote: {batch.id} · Inicio: {new Date(batch.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">
                        {batch.completed}/{batch.total_pieces}
                      </div>
                      <div className="text-xs text-soft">
                        {batch.failed > 0 && (
                          <span className="text-red-500">{batch.failed} fallidos</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <Progress value={progress} className="h-2 mb-2" />

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-soft">
                      {progress.toFixed(1)}% completado
                    </span>
                    <span className="text-soft">
                      Costo estimado: ${batch.estimated_cost.toFixed(2)}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="panel">
        <CardHeader>
          <CardTitle>Costos (últimos 30 días)</CardTitle>
          <CardDescription>Resumen simple de gastos</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Generación de imágenes</p>
                <p className="text-sm text-soft">Replicate</p>
              </div>
              <div className="text-right">
                <div className="font-semibold">
                  ${costSummary?.by_provider?.replicate?.toFixed(2) || "0.00"}
                </div>
                <div className="text-xs text-soft">este mes</div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Texto y hooks</p>
                <p className="text-sm text-soft">OpenAI</p>
              </div>
              <div className="text-right">
                <div className="font-semibold">
                  ${costSummary?.by_provider?.openai?.toFixed(2) || "0.00"}
                </div>
                <div className="text-xs text-soft">este mes</div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Storage</p>
                <p className="text-sm text-soft">Cloudflare R2</p>
              </div>
              <div className="text-right">
                <div className="font-semibold">
                  ${costSummary?.by_provider?.cloudflare_r2?.toFixed(2) || "0.00"}
                </div>
                <div className="text-xs text-soft">este mes</div>
              </div>
            </div>

            <div className="border-t border-white/10 pt-4 mt-4">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-lg">Total</p>
                <div className="text-right">
                  <div className="text-2xl font-bold text-brand-100">
                    ${costSummary?.total_cost?.toFixed(2) || "0.00"}
                  </div>
                  <div className="text-xs text-soft">últimos 30 días</div>
                </div>
              </div>
              <div className="mt-2 text-sm text-soft">
                Costo promedio por pieza: ${costSummary?.total_cost && costSummary.count ? (costSummary.total_cost / costSummary.count).toFixed(2) : "0.00"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="panel">
        <CardHeader>
          <CardTitle>Plantillas disponibles</CardTitle>
          <CardDescription>
            {templates.length > 0 ? `${templates.length} plantillas disponibles` : "Aún no hay plantillas"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {templates.length === 0 ? (
            <div className="text-sm text-soft">Crea o carga una plantilla para empezar.</div>
          ) : (
            <div className="space-y-3">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="flex items-center justify-between p-3 border border-white/10 rounded-xl"
                >
                  <div className="flex-1">
                    <p className="font-medium">{template.name}</p>
                    <p className="text-sm text-soft">{template.category}</p>
                  </div>
                  <Badge variant="secondary">{template.tier}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <BatchGenerationDialog
        open={showBatchDialog}
        onOpenChange={setShowBatchDialog}
        avatars={avatars}
        templates={templates}
        onSuccess={() => {
          loadData()
        }}
      />
    </div>
  )
}

