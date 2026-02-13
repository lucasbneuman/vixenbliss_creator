"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { createAvatar, fetchLoRAModels, uploadLoRAModel } from "@/lib/api/avatars"
import type { LoRAModel } from "@/types/lora"

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

type AvatarFormState = {
  name: string
  vertical: string
  dominantFeatures: string
  visualType: "Natural" | "Glam" | "Urbano" | "Alternativo"
  palette: string
  variants: string
  ageRange: "18-25" | "26-35" | "36-45" | "46+"
  ethnicity: string
  gender: "female" | "male" | "non-binary"
}

const initialForm: AvatarFormState = {
  name: "",
  vertical: "Lifestyle / influencer",
  dominantFeatures: "",
  visualType: "Natural",
  palette: "",
  variants: "",
  ageRange: "26-35",
  ethnicity: "diverse",
  gender: "female",
}

export default function AvatarsPage() {
  const [isSaving, setIsSaving] = useState(false)
  const [isUploadingLora, setIsUploadingLora] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [loras, setLoras] = useState<LoRAModel[]>([])
  const [selectedLoraId, setSelectedLoraId] = useState("")
  const [loraName, setLoraName] = useState("")
  const [loraFile, setLoraFile] = useState<File | null>(null)
  const [form, setForm] = useState<AvatarFormState>(initialForm)

  useEffect(() => {
    const loadLoras = async () => {
      try {
        const result = await fetchLoRAModels(DEMO_USER_ID)
        setLoras(result)
        if (result.length > 0 && !selectedLoraId) {
          setSelectedLoraId(result[0].id)
        }
      } catch {
        // Keep page usable if LoRA catalog is unavailable.
      }
    }

    loadLoras()
  }, [selectedLoraId])

  const handleUploadLora = async () => {
    if (!loraName.trim() || !loraFile) {
      setMessage("Ingresa nombre y archivo .safetensors para subir el LoRA.")
      return
    }

    setIsUploadingLora(true)
    setMessage(null)

    try {
      const newLora = await uploadLoRAModel({
        userId: DEMO_USER_ID,
        name: loraName.trim(),
        file: loraFile,
      })
      setLoras((prev) => [newLora, ...prev])
      setSelectedLoraId(newLora.id)
      setLoraName("")
      setLoraFile(null)
      setMessage("LoRA subido correctamente.")
    } catch (err) {
      if (err instanceof Error) {
        setMessage(err.message)
      } else {
        setMessage("Error subiendo LoRA.")
      }
    } finally {
      setIsUploadingLora(false)
    }
  }

  const handleCreate = async () => {
    setIsSaving(true)
    setMessage(null)

    try {
      await createAvatar(DEMO_USER_ID, {
        name: form.name || "Sin nombre",
        niche: form.vertical,
        aesthetic_style: form.visualType.toLowerCase(),
        lora_model_id: selectedLoraId || undefined,
        facial_generation: {
          age_range: form.ageRange,
          ethnicity: form.ethnicity,
          aesthetic_style: form.visualType.toLowerCase(),
          gender: form.gender,
          custom_prompt: [form.dominantFeatures, form.palette, form.variants].filter(Boolean).join(", "),
        },
      })

      setMessage("Avatar creado correctamente.")
      setForm(initialForm)
    } catch (err) {
      if (err instanceof Error) {
        setMessage(err.message)
      } else {
        setMessage("Error creando avatar.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-high">Sistema 1: Avatares</h1>
        <p className="text-soft max-w-2xl">
          Define la identidad base del avatar y vincula un LoRA para habilitar produccion consistente.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <Card className="panel">
          <CardHeader>
            <CardTitle>Ficha base</CardTitle>
            <CardDescription>Datos minimos para activar generacion</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-semibold">Nombre</label>
                <Input
                  placeholder="Ej: Luna Starr"
                  className="mt-2"
                  value={form.name}
                  onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-sm font-semibold">Vertical comercial</label>
                <div className="choice-group mt-2">
                  {["Lifestyle / influencer", "Entretenimiento adulto", "Performance / musica", "Experimental"].map((val) => (
                    <label key={val} className="choice-item">
                      <input
                        type="radio"
                        name="vertical"
                        checked={form.vertical === val}
                        onChange={() => setForm((prev) => ({ ...prev, vertical: val }))}
                      />
                      {val}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold">LoRA</label>
                <select
                  className="mt-2 h-10 w-full rounded-lg border px-3 text-base"
                  value={selectedLoraId}
                  onChange={(e) => setSelectedLoraId(e.target.value)}
                >
                  <option value="">Sin LoRA</option>
                  {loras.map((lora) => (
                    <option key={lora.id} value={lora.id}>
                      {lora.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-semibold">Edad</label>
                <div className="choice-group mt-2">
                  {(["18-25", "26-35", "36-45", "46+"] as const).map((val) => (
                    <label key={val} className="choice-item">
                      <input
                        type="radio"
                        name="ageRange"
                        checked={form.ageRange === val}
                        onChange={() => setForm((prev) => ({ ...prev, ageRange: val }))}
                      />
                      {val}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold">Genero</label>
                <div className="choice-group mt-2">
                  {(["female", "male", "non-binary"] as const).map((val) => (
                    <label key={val} className="choice-item">
                      <input
                        type="radio"
                        name="gender"
                        checked={form.gender === val}
                        onChange={() => setForm((prev) => ({ ...prev, gender: val }))}
                      />
                      {val}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold">Etnia o estilo</label>
                <Input
                  className="mt-2"
                  value={form.ethnicity}
                  onChange={(e) => setForm((prev) => ({ ...prev, ethnicity: e.target.value }))}
                  placeholder="Ej: latina, asiatica, europea"
                />
              </div>
              <div>
                <label className="text-sm font-semibold">Rasgos dominantes</label>
                <Input
                  className="mt-2"
                  value={form.dominantFeatures}
                  onChange={(e) => setForm((prev) => ({ ...prev, dominantFeatures: e.target.value }))}
                  placeholder="Ojos, piel, cabello"
                />
              </div>
              <div>
                <label className="text-sm font-semibold">Tipo visual</label>
                <div className="choice-group mt-2">
                  {(["Natural", "Glam", "Urbano", "Alternativo"] as const).map((val) => (
                    <label key={val} className="choice-item">
                      <input
                        type="radio"
                        name="visualType"
                        checked={form.visualType === val}
                        onChange={() => setForm((prev) => ({ ...prev, visualType: val }))}
                      />
                      {val}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold">Paleta</label>
                <Input
                  className="mt-2"
                  value={form.palette}
                  onChange={(e) => setForm((prev) => ({ ...prev, palette: e.target.value }))}
                  placeholder="Ej: tonos frios, borgona"
                />
              </div>
              <div>
                <label className="text-sm font-semibold">Variantes</label>
                <Input
                  className="mt-2"
                  value={form.variants}
                  onChange={(e) => setForm((prev) => ({ ...prev, variants: e.target.value }))}
                  placeholder="Ej: peinado A/B/C"
                />
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
              <Input
                placeholder="Nombre del LoRA"
                value={loraName}
                onChange={(e) => setLoraName(e.target.value)}
              />
              <Input type="file" accept=".safetensors" onChange={(e) => setLoraFile(e.target.files?.[0] || null)} />
              <Button variant="outline" onClick={handleUploadLora} disabled={isUploadingLora}>
                {isUploadingLora ? "Subiendo..." : "Subir LoRA"}
              </Button>
            </div>

            <div className="flex items-center gap-3">
              <Button className="btn-contrast-primary" onClick={handleCreate} disabled={isSaving}>
                {isSaving ? "Creando..." : "Crear avatar"}
              </Button>
              {message && <span className="text-sm text-soft">{message}</span>}
            </div>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <CardTitle>Resumen</CardTitle>
            <CardDescription>Previsualizacion rapida</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <div className="text-soft">Avatar</div>
              <div className="font-semibold text-high">{form.name || "Sin nombre"}</div>
            </div>
            <div>
              <div className="text-soft">Vertical</div>
              <div className="font-semibold text-high">{form.vertical}</div>
            </div>
            <div>
              <div className="text-soft">LoRA</div>
              <div className="font-semibold text-high">{loras.find((item) => item.id === selectedLoraId)?.name || "Sin LoRA"}</div>
            </div>
            <div>
              <div className="text-soft">Genero/edad</div>
              <div className="font-semibold text-high">{form.gender} · {form.ageRange}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
