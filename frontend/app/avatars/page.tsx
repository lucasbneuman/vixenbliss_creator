"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Users,
  Plus,
  Image,
  Calendar,
  TrendingUp,
  Settings,
  Sparkles
} from "lucide-react"

export default function AvatarsPage() {
  const [avatars] = useState([
    // Placeholder - en producción vendría de la API
  ])

  return (
    <div className="space-y-8">
      <div className="section-head">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-high">Avatares</h2>
          <p className="text-soft">
            Gestiona tus identidades AI y sus características
          </p>
        </div>
        <Button variant="success" className="gap-2">
          <Plus className="h-4 w-4" />
          Crear Avatar
        </Button>
      </div>
      <div className="divider" />

      {avatars.length === 0 ? (
        <Card className="panel border-dashed border-white/20">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="rounded-full bg-violet-500/10 p-6 mb-4">
              <Users className="h-12 w-12 text-violet-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No tienes avatares todavía</h3>
            <p className="text-soft text-center mb-6 max-w-md">
              Crea tu primer avatar AI para comenzar a generar contenido personalizado.
              Cada avatar incluye:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-2xl mb-6">
              <div className="flex flex-col items-center text-center p-4 border border-white/10 rounded-xl bg-white/5">
                <Image className="h-8 w-8 text-pink-500 mb-2" />
                <p className="font-medium">50 Imágenes</p>
                <p className="text-xs text-soft">Dataset facial único</p>
              </div>
              <div className="flex flex-col items-center text-center p-4 border border-white/10 rounded-xl bg-white/5">
                <Sparkles className="h-8 w-8 text-yellow-500 mb-2" />
                <p className="font-medium">LoRA Model</p>
                <p className="text-xs text-soft">Entrenamiento personalizado</p>
              </div>
              <div className="flex flex-col items-center text-center p-4 border border-white/10 rounded-xl bg-white/5">
                <Settings className="h-8 w-8 text-blue-500 mb-2" />
                <p className="font-medium">Metadata</p>
                <p className="text-xs text-soft">Bio, intereses, personalidad</p>
              </div>
            </div>
            <Button size="lg" variant="success" className="gap-2">
              <Plus className="h-4 w-4" />
              Crear Primer Avatar
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Avatar cards aquí cuando haya datos */}
        </div>
      )}

      {/* Info Cards */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Getting Started</h2>
          <p className="text-soft text-sm">Setup flow, features, and requirements</p>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="panel">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Proceso de Creación</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-violet-500 text-white flex items-center justify-center text-xs font-bold">
                  1
                </div>
                <p className="text-sm">Genera 50 fotos faciales únicas</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-violet-500 text-white flex items-center justify-center text-xs font-bold">
                  2
                </div>
                <p className="text-sm">Entrena modelo LoRA personalizado</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-violet-500 text-white flex items-center justify-center text-xs font-bold">
                  3
                </div>
                <p className="text-sm">Genera bio y personalidad con LLM</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-violet-500 text-white flex items-center justify-center text-xs font-bold">
                  4
                </div>
                <p className="text-sm">Configura ubicación e intereses</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Características</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-yellow-500" />
                <span>Generación facial realista</span>
              </li>
              <li className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-blue-500" />
                <span>Edad y etnia personalizables</span>
              </li>
              <li className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span>Auto-bio generator con LLM</span>
              </li>
              <li className="flex items-center gap-2">
                <Settings className="h-4 w-4 text-soft" />
                <span>Tracking de costos por avatar</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">APIs Necesarias</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Replicate</span>
                <Badge variant="outline" className="text-yellow-500 border-yellow-500">
                  Requerida
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">OpenAI/Anthropic</span>
                <Badge variant="outline" className="text-yellow-500 border-yellow-500">
                  Requerida
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Cloudflare R2</span>
                <Badge variant="outline" className="text-blue-500 border-blue-500">
                  Recomendada
                </Badge>
              </div>
              <p className="text-xs text-soft mt-4">
                Configura las API keys en Settings para comenzar
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
