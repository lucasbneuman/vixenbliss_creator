"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  ImagePlus,
  Wand2,
  Package,
  Zap,
  Upload,
  Check
} from "lucide-react"

export default function ContentPage() {
  const [contentPieces] = useState([])

  return (
    <div className="space-y-8">
      <div className="section-head">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-high">Generación de Contenido</h2>
          <p className="text-soft">
            Crea imágenes personalizadas usando tus avatares y modelos LoRA
          </p>
        </div>
        <Button variant="success" className="gap-2">
          <ImagePlus className="h-4 w-4" />
          Generar Contenido
        </Button>
      </div>
      <div className="divider" />

      {contentPieces.length === 0 ? (
        <Card className="panel border-dashed border-white/20">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="rounded-full bg-pink-500/10 p-6 mb-4">
              <ImagePlus className="h-12 w-12 text-pink-700" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No has generado contenido todavía</h3>
            <p className="text-soft text-center mb-6 max-w-md">
              Genera imágenes personalizadas usando tus avatares AI con templates y prompts preconfigurados
            </p>
            <Button size="lg" className="gap-2" disabled>
              <ImagePlus className="h-4 w-4" />
              Generar Contenido
              <Badge variant="outline" className="ml-2">Requiere avatar</Badge>
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {/* Features Grid */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Capabilities</h2>
          <p className="text-soft text-sm">Create, template, and batch at scale</p>
        </div>
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="panel">
          <CardHeader>
            <div className="rounded-full bg-pink-500/10 p-3 w-fit mb-2">
              <Wand2 className="h-6 w-6 text-pink-700" />
            </div>
            <CardTitle>LoRA Inference</CardTitle>
            <CardDescription>
              Genera imágenes usando tu modelo LoRA entrenado
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                <span>Consistencia facial perfecta</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                <span>Control total de pose y estilo</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                <span>Alta calidad 8K resolution</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <div className="rounded-full bg-purple-500/10 p-3 w-fit mb-2">
              <Package className="h-6 w-6 text-purple-600" />
            </div>
            <CardTitle>Template Library</CardTitle>
            <CardDescription>
              50+ templates de poses y escenarios preconfigurados
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Badge variant="outline">Fitness</Badge>
              <Badge variant="outline" className="ml-2">Lifestyle</Badge>
              <Badge variant="outline" className="ml-2">Fashion</Badge>
              <Badge variant="outline" className="ml-2">Beach</Badge>
              <Badge variant="outline" className="ml-2">Yoga</Badge>
              <Badge variant="outline" className="ml-2">Urban</Badge>
              <p className="text-xs text-soft mt-4">
                Cada template incluye prompt optimizado y parámetros recomendados
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <div className="rounded-full bg-orange-500/10 p-3 w-fit mb-2">
              <Zap className="h-6 w-6 text-orange-600" />
            </div>
            <CardTitle>Batch Processing</CardTitle>
            <CardDescription>
              Genera 50 piezas de contenido en paralelo
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                <span>Processing asíncrono con Celery</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                <span>Auto-upload a R2/CDN</span>
              </li>
              <li className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-500" />
                <span>Safety layer para filtrado</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Workflow Steps */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Workflow</h2>
          <p className="text-soft text-sm">From avatar selection to distribution</p>
        </div>
      </div>
      <Card className="panel">
        <CardHeader>
          <CardTitle>Flujo de Generación</CardTitle>
          <CardDescription>
            Proceso completo desde la selección hasta la publicación
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="rounded-full bg-pink-700/10 p-2 mt-1">
                <div className="w-6 h-6 rounded-full bg-pink-700 text-white flex items-center justify-center text-xs font-bold">
                  1
                </div>
              </div>
              <div className="flex-1">
                <h4 className="font-medium mb-1">Selecciona Avatar</h4>
                <p className="text-sm text-soft">
                  Elige el avatar y modelo LoRA que quieres usar para generar contenido
                </p>
              </div>
            </div>

            <Separator />

            <div className="flex items-start gap-4">
              <div className="rounded-full bg-pink-700/10 p-2 mt-1">
                <div className="w-6 h-6 rounded-full bg-pink-700 text-white flex items-center justify-center text-xs font-bold">
                  2
                </div>
              </div>
              <div className="flex-1">
                <h4 className="font-medium mb-1">Elige Template o Custom Prompt</h4>
                <p className="text-sm text-soft">
                  Usa uno de los 50+ templates preconfigurados o crea tu propio prompt personalizado
                </p>
              </div>
            </div>

            <Separator />

            <div className="flex items-start gap-4">
              <div className="rounded-full bg-pink-700/10 p-2 mt-1">
                <div className="w-6 h-6 rounded-full bg-pink-700 text-white flex items-center justify-center text-xs font-bold">
                  3
                </div>
              </div>
              <div className="flex-1">
                <h4 className="font-medium mb-1">Genera en Batch</h4>
                <p className="text-sm text-soft">
                  El sistema genera 50 imágenes en paralelo usando Celery workers
                </p>
              </div>
            </div>

            <Separator />

            <div className="flex items-start gap-4">
              <div className="rounded-full bg-pink-700/10 p-2 mt-1">
                <div className="w-6 h-6 rounded-full bg-pink-700 text-white flex items-center justify-center text-xs font-bold">
                  4
                </div>
              </div>
              <div className="flex-1">
                <h4 className="font-medium mb-1">Auto-Upload y Hook Generation</h4>
                <p className="text-sm text-soft">
                  Las imágenes se suben a R2/CDN y se generan hooks automáticamente para redes sociales
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Production Stats</h2>
          <p className="text-soft text-sm">Monthly output and queue status</p>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="panel">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Generado</CardTitle>
            <ImagePlus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-soft">
              Piezas este mes
            </p>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">En Processing</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-soft">
              Jobs activos
            </p>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Listas para Publicar</CardTitle>
            <Upload className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-soft">
              En cola
            </p>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Costo Estimado</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$0</div>
            <p className="text-xs text-soft">
              API costs este mes
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
