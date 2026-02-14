"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { createAvatar, fetchLoRAModels, uploadLoRAModel } from "@/lib/api/avatars"
import type { LoRAModel } from "@/types/lora"

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

const steps = [
  { id: 1, title: "Ficha Base" },
  { id: 2, title: "Perfil Visual" },
  { id: 3, title: "Personalidad" },
  { id: 4, title: "Narrativa" },
  { id: 5, title: "Limites" },
]

export default function AvatarsPage() {
  const [step, setStep] = useState(1)
  const [isSaving, setIsSaving] = useState(false)
  const [isUploadingLora, setIsUploadingLora] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [loras, setLoras] = useState<LoRAModel[]>([])
  const [selectedLoraId, setSelectedLoraId] = useState("")
  const [loraName, setLoraName] = useState("")
  const [loraFile, setLoraFile] = useState<File | null>(null)
  const [form, setForm] = useState({
    name: "",
    vertical: "Lifestyle / influencer",
    contentSoft: true,
    contentHard: true,
    dominantFeatures: "",
    visualType: "Natural",
    palette: "",
    variants: "",
    toneFormal: "Formal",
    toneDominant: "Dominante",
    toneProvocative: "Provocadora",
    toneAuthority: "Autoritaria",
    backstory: "",
    interests: "",
    role: "",
    limitsAllowed: "",
    limitsRed: "",
    scalePolicies: "",
    ageRange: "26-35",
    ethnicity: "diverse",
    gender: "female",
  })

  useEffect(() => {
    const loadLoras = async () => {
      try {
        const result = await fetchLoRAModels(DEMO_USER_ID)
        setLoras(result)
        if (result.length > 0 && !selectedLoraId) {
          setSelectedLoraId(result[0].id)
        }
      } catch {
        // keep page usable even if LoRA endpoint fails
      }
    }
    loadLoras()
  }, [])

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
      const updated = [newLora, ...loras]
      setLoras(updated)
      setSelectedLoraId(newLora.id)
      setLoraName("")
      setLoraFile(null)
      setMessage("LoRA subido y disponible para este avatar.")
    } catch (err: any) {
      setMessage(err?.message || "Error subiendo LoRA.")
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
          age_range: form.ageRange as "18-25" | "26-35" | "36-45" | "46+",
          ethnicity: form.ethnicity,
          aesthetic_style: form.visualType.toLowerCase(),
          gender: form.gender as "female" | "male" | "non-binary",
          custom_prompt: [
            form.dominantFeatures,
            form.palette,
            form.variants
          ].filter(Boolean).join(", ")
        }
      })
      setMessage("Avatar creado correctamente.")
    } catch (err: any) {
      setMessage(err?.message || "Error al crear avatar.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-high">Crear Avatar</h1>
        <p className="text-soft max-w-2xl">
          Sistema 1. Creas una identidad completa que luego produce contenido soft para redes y hard para venta.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <Card className="panel">
            <CardHeader>
              <CardTitle>Paso {step} de {steps.length}</CardTitle>
              <CardDescription>{steps.find(s => s.id === step)?.title}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {step === 1 && (
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-semibold">Nombre del avatar</label>
                    <Input
                      placeholder="Ej: Luna Starr"
                      className="mt-2"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Vertical comercial</label>
                    <div className="choice-group mt-2">
                      {[
                        "Lifestyle / influencer",
                        "Entretenimiento adulto",
                        "Performance / musica",
                        "Experimental"
                      ].map((val) => (
                        <label key={val} className="choice-item">
                          <input
                            type="radio"
                            name="vertical"
                            checked={form.vertical === val}
                            onChange={() => setForm({ ...form, vertical: val })}
                          />
                          {val}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Tipo de contenido (ambos)</label>
                    <div className="mt-2 flex gap-4">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={form.contentSoft}
                          onChange={(e) => setForm({ ...form, contentSoft: e.target.checked })}
                        /> Soft
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={form.contentHard}
                          onChange={(e) => setForm({ ...form, contentHard: e.target.checked })}
                        /> Hard
                      </label>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">LoRA disponible</label>
                    <select
                      className="mt-2 h-10 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 text-base text-high"
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
                  <div className="md:col-span-2 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
                    <Input
                      placeholder="Nombre del LoRA"
                      value={loraName}
                      onChange={(e) => setLoraName(e.target.value)}
                    />
                    <Input
                      type="file"
                      accept=".safetensors"
                      onChange={(e) => setLoraFile(e.target.files?.[0] || null)}
                    />
                    <Button className="btn-contrast" onClick={handleUploadLora} disabled={isUploadingLora}>
                      {isUploadingLora ? "Subiendo..." : "Subir LoRA"}
                    </Button>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Edad</label>
                    <div className="choice-group mt-2">
                      {["18-25", "26-35", "36-45", "46+"].map((val) => (
                        <label key={val} className="choice-item">
                          <input
                            type="radio"
                            name="ageRange"
                            checked={form.ageRange === val}
                            onChange={() => setForm({ ...form, ageRange: val })}
                          />
                          {val}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Genero</label>
                    <div className="choice-group mt-2">
                      {["female", "male", "non-binary"].map((val) => (
                        <label key={val} className="choice-item">
                          <input
                            type="radio"
                            name="gender"
                            checked={form.gender === val}
                            onChange={() => setForm({ ...form, gender: val })}
                          />
                          {val}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Etnia / estilo</label>
                    <Input
                      placeholder="Ej: latina, asiatica, europea"
                      className="mt-2"
                      value={form.ethnicity}
                      onChange={(e) => setForm({ ...form, ethnicity: e.target.value })}
                    />
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-semibold">Rasgos dominantes</label>
                    <Input
                      placeholder="Ej: ojos claros, piel oliva, cabello negro"
                      className="mt-2"
                      value={form.dominantFeatures}
                      onChange={(e) => setForm({ ...form, dominantFeatures: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Tipo visual</label>
                    <div className="choice-group mt-2">
                      {["Natural", "Glam", "Urbano", "Alternativo"].map((val) => (
                        <label key={val} className="choice-item">
                          <input
                            type="radio"
                            name="visualType"
                            checked={form.visualType === val}
                            onChange={() => setForm({ ...form, visualType: val })}
                          />
                          {val}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Paleta de colores</label>
                    <Input
                      placeholder="Ej: tonos calidos, rojo + negro"
                      className="mt-2"
                      value={form.palette}
                      onChange={(e) => setForm({ ...form, palette: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Variantes controladas</label>
                    <Input
                      placeholder="Ej: 3 estilos de peinado"
                      className="mt-2"
                      value={form.variants}
                      onChange={(e) => setForm({ ...form, variants: e.target.value })}
                    />
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="grid gap-4 md:grid-cols-2">
                  {[
                    { key: "toneFormal", label: "Formal / Informal", options: ["Formal", "Neutra", "Informal"] },
                    { key: "toneDominant", label: "Dominante / Cercana", options: ["Dominante", "Equilibrada", "Cercana"] },
                    { key: "toneProvocative", label: "Provocadora / Sutil", options: ["Provocadora", "Equilibrada", "Sutil"] },
                    { key: "toneAuthority", label: "Autoritaria / Accesible", options: ["Autoritaria", "Equilibrada", "Accesible"] },
                  ].map((block) => (
                    <div key={block.key}>
                      <label className="text-sm font-semibold">{block.label}</label>
                      <div className="choice-group mt-2">
                        {block.options.map((val) => (
                          <label key={val} className="choice-item">
                            <input
                              type="radio"
                              name={block.key}
                              checked={(form as any)[block.key] === val}
                              onChange={() => setForm({ ...form, [block.key]: val } as any)}
                            />
                            {val}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {step === 4 && (
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-semibold">Backstory minima viable</label>
                    <textarea
                      className="mt-2 h-28 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                      value={form.backstory}
                      onChange={(e) => setForm({ ...form, backstory: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Intereses y motivaciones</label>
                    <textarea
                      className="mt-2 h-28 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                      value={form.interests}
                      onChange={(e) => setForm({ ...form, interests: e.target.value })}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-sm font-semibold">Rol frente a la audiencia</label>
                    <textarea
                      className="mt-2 h-24 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                      value={form.role}
                      onChange={(e) => setForm({ ...form, role: e.target.value })}
                    />
                  </div>
                </div>
              )}

              {step === 5 && (
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-semibold">Tipos de contenido autorizados</label>
                    <textarea
                      className="mt-2 h-24 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                      value={form.limitsAllowed}
                      onChange={(e) => setForm({ ...form, limitsAllowed: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Lineas rojas (NO produce)</label>
                    <textarea
                      className="mt-2 h-24 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                      value={form.limitsRed}
                      onChange={(e) => setForm({ ...form, limitsRed: e.target.value })}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-sm font-semibold">Politicas de escalado</label>
                    <textarea
                      className="mt-2 h-24 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                      value={form.scalePolicies}
                      onChange={(e) => setForm({ ...form, scalePolicies: e.target.value })}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex items-center gap-3">
            <Button className="btn-contrast hover:bg-slate-700" onClick={() => setStep(Math.max(1, step - 1))}>
              Anterior
            </Button>
            <Button className="btn-contrast hover:bg-slate-700" onClick={() => setStep(Math.min(steps.length, step + 1))}>
              Siguiente
            </Button>
            <Button className="btn-contrast-primary hover:bg-emerald-500" onClick={handleCreate} disabled={isSaving}>
              {isSaving ? "Creando..." : "Crear avatar"}
            </Button>
          </div>
        </div>

        <Card className="panel">
          <CardHeader>
            <CardTitle>Resumen</CardTitle>
            <CardDescription>Vista rapida de la identidad</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <div className="text-soft">Avatar</div>
              <div className="text-high font-semibold">{form.name || "Sin nombre"}</div>
            </div>
            <div>
              <div className="text-soft">Vertical</div>
              <div className="text-high font-semibold">{form.vertical}</div>
            </div>
            <div>
              <div className="text-soft">Contenido</div>
              <div className="text-high font-semibold">
                {form.contentSoft && form.contentHard ? "Soft + Hard" : form.contentSoft ? "Soft" : "Hard"}
              </div>
            </div>
            <div>
              <div className="text-soft">LoRA</div>
              <div className="text-high font-semibold">
                {loras.find((l) => l.id === selectedLoraId)?.name || "Sin LoRA"}
              </div>
            </div>
            {message && (
              <div className="text-sm text-soft">{message}</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
