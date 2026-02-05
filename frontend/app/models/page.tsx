"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ModelTable } from "@/components/model-table"
import { Model } from "@/types/avatar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Plus,
  Search,
  RefreshCw
} from "lucide-react"
import { fetchAvatars, deleteAvatar, pauseAvatar, activateAvatar, cloneAvatar } from "@/lib/api"
import { transformAvatarToModel } from "@/lib/transformers"
import { LoadingSpinner } from "@/components/loading-state"
import { ErrorDisplay } from "@/components/error-boundary"

// Hardcoded user ID for demo - will come from auth context
const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

export default function ModelsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "paused" | "archived">("all")
  const [allModels, setAllModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // Fetch models from API
  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    setLoading(true)
    setError(null)

    try {
      const avatars = await fetchAvatars(DEMO_USER_ID)
      const models = avatars.map(transformAvatarToModel)
      setAllModels(models)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to load models"))
      // Fallback to mock data for demo
      setAllModels(getMockModels())
    } finally {
      setLoading(false)
    }
  }

  // Mock data fallback - En producción vendría de la API
function getMockModels(): Model[] {
  return [
    {
      id: "1",
      name: "Luna Starr",
      niche: "Fitness",
      status: "active",
      mrr: 12400,
      arpu: 48,
      subscribers: 258,
      engagement_rate: 8.2,
      content_generated: 156,
      health: "healthy",
      created_at: "2024-01-01",
      performance_delta: 24.5
    },
    {
      id: "2",
      name: "Aria Nova",
      niche: "Lifestyle",
      status: "active",
      mrr: 9800,
      arpu: 42,
      subscribers: 233,
      engagement_rate: 6.8,
      content_generated: 142,
      health: "healthy",
      created_at: "2024-01-02",
      performance_delta: 18.3
    },
    {
      id: "3",
      name: "Maya Eclipse",
      niche: "Fashion",
      status: "active",
      mrr: 8200,
      arpu: 39,
      subscribers: 210,
      engagement_rate: 5.4,
      content_generated: 128,
      health: "warning",
      created_at: "2024-01-03",
      performance_delta: 12.1
    },
    {
      id: "4",
      name: "Jade Phoenix",
      niche: "Yoga",
      status: "active",
      mrr: 1200,
      arpu: 18,
      subscribers: 67,
      engagement_rate: 2.1,
      content_generated: 45,
      health: "critical",
      created_at: "2024-01-04",
      performance_delta: -8.4
    },
    {
      id: "5",
      name: "Nova Sky",
      niche: "Travel",
      status: "paused",
      mrr: 0,
      arpu: 0,
      subscribers: 0,
      engagement_rate: 0,
      content_generated: 89,
      health: "warning",
      created_at: "2024-01-05",
      performance_delta: 0
    },
  ]
}

  const filteredModels = allModels.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         model.niche.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === "all" || model.status === statusFilter

    return matchesSearch && matchesStatus
  })

  const handleClone = async (model: Model) => {
    try {
      await cloneAvatar(model.id)
      await loadModels() // Refresh list
    } catch (err) {
      console.error("Failed to clone model:", err)
    }
  }

  const handleKill = async (model: Model) => {
    if (!confirm(`Are you sure you want to kill "${model.name}"? This action cannot be undone.`)) {
      return
    }

    try {
      await deleteAvatar(model.id)
      await loadModels() // Refresh list
    } catch (err) {
      console.error("Failed to kill model:", err)
    }
  }

  const handlePause = async (model: Model) => {
    try {
      await pauseAvatar(model.id)
      await loadModels() // Refresh list
    } catch (err) {
      console.error("Failed to pause model:", err)
    }
  }

  const handleActivate = async (model: Model) => {
    try {
      await activateAvatar(model.id)
      await loadModels() // Refresh list
    } catch (err) {
      console.error("Failed to activate model:", err)
    }
  }

  const handleView = (model: Model) => {
    console.log("View model:", model)
    // TODO: Navigate to model detail page /models/[id]
  }

  // Show loading state
  if (loading && allModels.length === 0) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-high">Models</h1>
          <p className="text-soft mt-1">Loading your digital assets...</p>
        </div>
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-high">Modelos (Avatares)</h1>
        <p className="text-soft max-w-2xl">
          Aquí creas y administras avatares. Luego usas esos avatares para generar contenido.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button asChild variant="success" className="gap-2">
          <Link href="/avatars">
            <Plus className="h-4 w-4" />
            Crear avatar
          </Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/factory">Crear contenido</Link>
        </Button>
        <Button
          variant="outline"
          className="gap-2"
          onClick={loadModels}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <ErrorDisplay error={error} />
      )}

      <Card className="panel">
        <CardHeader>
          <CardTitle>Cómo funciona</CardTitle>
          <CardDescription>Tres pasos simples</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-white/10 p-3">
            <div className="font-semibold">1. Crear avatar</div>
            <div className="text-sm text-soft">Define identidad, estilo y dataset.</div>
          </div>
          <div className="rounded-lg border border-white/10 p-3">
            <div className="font-semibold">2. Generar contenido</div>
            <div className="text-sm text-soft">Usa plantillas para producir lotes.</div>
          </div>
          <div className="rounded-lg border border-white/10 p-3">
            <div className="font-semibold">3. Distribuir</div>
            <div className="text-sm text-soft">Publica y mide resultados.</div>
          </div>
        </CardContent>
      </Card>

      <Card className="panel">
        <CardHeader>
          <CardTitle>Buscar y filtrar</CardTitle>
          <CardDescription>Encuentra un avatar rápido</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-soft" />
            <Input
              placeholder="Buscar por nombre o nicho..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant={statusFilter === "all" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setStatusFilter("all")}
            >
              Todos
            </Button>
            <Button
              variant={statusFilter === "active" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setStatusFilter("active")}
            >
              Activos
            </Button>
            <Button
              variant={statusFilter === "paused" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setStatusFilter("paused")}
            >
              Pausados
            </Button>
            <Button
              variant={statusFilter === "archived" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setStatusFilter("archived")}
            >
              Archivados
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Models Table */}
      <div>
        <p className="text-sm text-soft mb-3">
          Mostrando {filteredModels.length} de {allModels.length} avatares
        </p>

        <ModelTable
          models={filteredModels}
          onClone={handleClone}
          onKill={handleKill}
          onPause={handlePause}
          onActivate={handleActivate}
          onView={handleView}
        />
      </div>
    </div>
  )
}
