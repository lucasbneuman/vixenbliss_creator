"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { fetchAvatars } from "@/lib/api/avatars"
import { generateBatch, generateVideo } from "@/lib/api/content"
import type { Avatar } from "@/types/avatar"

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

const steps = [
  { id: 1, title: "Seleccion" },
  { id: 2, title: "Prompts y Hooks" },
  { id: 3, title: "Microvariaciones" },
  { id: 4, title: "Volumen y Duracion" },
]

export default function ContentFactoryPage() {
  const [step, setStep] = useState(1)
  const [avatars, setAvatars] = useState<Avatar[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [form, setForm] = useState({
    avatarId: "",
    contentKind: "Imagen + Video",
    softOutputs: 80,
    hardOutputs: 40,
    promptBase: "",
    hookA: "",
    hookB: "",
    hookC: "",
    outputsPerHook: 20,
    duration: "15s",
    microGestures: true,
    microFraming: true,
    microText: true,
    microHooks: true,
    microCtas: true,
    microPoses: true,
  })

  useEffect(() => {
    const load = async () => {
      try {
        const result = await fetchAvatars(DEMO_USER_ID)
        setAvatars(result)
        if (result[0]?.id) {
          setForm((prev) => ({ ...prev, avatarId: result[0].id }))
        }
      } catch (err: any) {
        setMessage(err?.message || "Error cargando avatares.")
      }
    }
    load()
  }, [])

  const buildPrompts = () => {
    const hooks = [form.hookA, form.hookB, form.hookC].filter(Boolean)
    const hooksToUse = hooks.length > 0 ? hooks : [""]
    const prompts: string[] = []
    hooksToUse.forEach((hook) => {
      for (let i = 0; i < form.outputsPerHook; i += 1) {
        const full = hook
          ? `${form.promptBase}, ${hook}`.trim()
          : `${form.promptBase}`.trim()
        prompts.push(full)
      }
    })
    return prompts
  }

  const buildTiers = (total: number) => {
    const soft = Math.max(0, Math.min(form.softOutputs, total))
    const hard = Math.max(0, Math.min(form.hardOutputs, total - soft))
    const tiers: Array<"capa1" | "capa2" | "capa3"> = []
    for (let i = 0; i < soft; i += 1) tiers.push("capa1")
    for (let i = 0; i < hard; i += 1) tiers.push("capa3")
    while (tiers.length < total) tiers.push("capa2")
    return tiers
  }

  const handleGenerate = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const prompts = buildPrompts()
      const tiers = buildTiers(prompts.length)
      const numPieces = prompts.length

      if (!form.avatarId || numPieces === 0) {
        setMessage("Selecciona un avatar y completa el prompt.")
        return
      }

      await generateBatch({
        avatar_id: form.avatarId,
        num_pieces: numPieces,
        platform: "instagram",
        include_hooks: true,
        safety_check: true,
        upload_to_storage: true,
        custom_prompts: prompts,
        custom_tiers: tiers,
        generation_config: {
          enhance_prompts: true,
          micro: {
            gestures: form.microGestures,
            framing: form.microFraming,
            text: form.microText,
            hooks: form.microHooks,
            ctas: form.microCtas,
            poses: form.microPoses
          }
        }
      })

      if (form.contentKind.includes("Video")) {
        const duration = parseInt(form.duration.replace("s", ""), 10)
        const hooks = [form.hookA, form.hookB, form.hookC].filter(Boolean)
        const hooksToUse = hooks.length > 0 ? hooks : [""]
        for (const hook of hooksToUse) {
          const videoPrompt = hook
            ? `${form.promptBase}, ${hook}`.trim()
            : `${form.promptBase}`.trim()
          await generateVideo({
            avatar_id: form.avatarId,
            prompt: videoPrompt,
            duration
          })
        }
      }

      setMessage("Lote generado correctamente.")
    } catch (err: any) {
      setMessage(err?.message || "Error al generar lote.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-high">Crear Contenido</h1>
        <p className="text-soft max-w-2xl">
          Sistema 2. Produccion masiva: prompt base + hooks + microvariaciones. El algoritmo decide que funciona.
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
                    <label className="text-sm font-semibold">Avatar</label>
                    <div className="choice-group mt-2">
                      {avatars.map((av) => (
                        <label key={av.id} className="choice-item">
                          <input
                            type="radio"
                            name="avatar"
                            checked={form.avatarId === av.id}
                            onChange={() => setForm({ ...form, avatarId: av.id })}
                          />
                          {av.name}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Contenido</label>
                    <div className="choice-group mt-2">
                      {["Imagen + Video", "Solo imagen", "Solo video"].map((val) => (
                        <label key={val} className="choice-item">
                          <input
                            type="radio"
                            name="contentKind"
                            checked={form.contentKind === val}
                            onChange={() => setForm({ ...form, contentKind: val })}
                          />
                          {val}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Soft outputs</label>
                    <Input
                      type="number"
                      placeholder="Ej: 80"
                      className="mt-2"
                      value={form.softOutputs}
                      onChange={(e) => setForm({ ...form, softOutputs: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Hard outputs</label>
                    <Input
                      type="number"
                      placeholder="Ej: 40"
                      className="mt-2"
                      value={form.hardOutputs}
                      onChange={(e) => setForm({ ...form, hardOutputs: Number(e.target.value) })}
                    />
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-semibold">Prompt base</label>
                    <textarea
                      className="mt-2 h-24 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                      value={form.promptBase}
                      onChange={(e) => setForm({ ...form, promptBase: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-4 md:grid-cols-3">
                    {["hookA", "hookB", "hookC"].map((key, idx) => (
                      <div key={key}>
                        <label className="text-sm font-semibold">Hook {String.fromCharCode(65 + idx)}</label>
                        <textarea
                          className="mt-2 h-24 w-full rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-base text-high"
                          value={(form as any)[key]}
                          onChange={(e) => setForm({ ...form, [key]: e.target.value } as any)}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="grid gap-3 md:grid-cols-2">
                  {[
                    ["microGestures", "Gestos y expresiones faciales"],
                    ["microFraming", "Encuadres y planos"],
                    ["microText", "Textos superpuestos (copy)"],
                    ["microHooks", "Hooks iniciales (primeros 3s)"],
                    ["microCtas", "CTAs (llamadas a la accion)"],
                    ["microPoses", "Variar expresiones y poses"],
                  ].map(([key, label]) => (
                    <label key={key} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={(form as any)[key]}
                        onChange={(e) => setForm({ ...form, [key]: e.target.checked } as any)}
                      /> {label}
                    </label>
                  ))}
                </div>
              )}

              {step === 4 && (
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="text-sm font-semibold">Outputs por hook</label>
                    <Input
                      type="number"
                      placeholder="20 - 50"
                      className="mt-2"
                      value={form.outputsPerHook}
                      onChange={(e) => setForm({ ...form, outputsPerHook: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Duracion video</label>
                    <div className="choice-group mt-2">
                      {["7s", "15s", "30s", "60s"].map((val) => (
                        <label key={val} className="choice-item">
                          <input
                            type="radio"
                            name="duration"
                            checked={form.duration === val}
                            onChange={() => setForm({ ...form, duration: val })}
                          />
                          {val}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-semibold">Cantidad total</label>
                    <Input
                      type="number"
                      placeholder="Ej: 150"
                      className="mt-2"
                      value={form.outputsPerHook * 3}
                      onChange={() => {}}
                      disabled
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
            <Button className="btn-contrast-primary hover:bg-emerald-500" onClick={handleGenerate} disabled={loading}>
              {loading ? "Generando..." : "Generar lote"}
            </Button>
          </div>
        </div>

        <Card className="panel">
          <CardHeader>
            <CardTitle>Resumen del lote</CardTitle>
            <CardDescription>Datos de produccion</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <div className="text-soft">Avatar</div>
              <div className="text-high font-semibold">
                {avatars.find(a => a.id === form.avatarId)?.name || "Sin seleccionar"}
              </div>
            </div>
            <div>
              <div className="text-soft">Contenido</div>
              <div className="text-high font-semibold">{form.contentKind}</div>
            </div>
            <div>
              <div className="text-soft">Soft / Hard</div>
              <div className="text-high font-semibold">{form.softOutputs} / {form.hardOutputs}</div>
            </div>
            <div>
              <div className="text-soft">Duracion video</div>
              <div className="text-high font-semibold">{form.duration}</div>
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
