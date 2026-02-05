"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Loader2, Sparkles } from "lucide-react"
import { generateBatch, type Template } from "@/lib/api"
import type { Avatar } from "@/types/avatar"

interface BatchGenerationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  avatars: Avatar[]
  templates: Template[]
  onSuccess?: () => void
}

export function BatchGenerationDialog({
  open,
  onOpenChange,
  avatars,
  templates,
  onSuccess,
}: BatchGenerationDialogProps) {
  const [selectedAvatarId, setSelectedAvatarId] = useState<string>("")
  const [numPieces, setNumPieces] = useState<number>(50)
  const [platform, setPlatform] = useState<string>("instagram")
  const [tierDistribution, setTierDistribution] = useState({
    capa1: 60,
    capa2: 30,
    capa3: 10,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!selectedAvatarId) {
      setError("Please select an avatar")
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await generateBatch({
        avatar_id: selectedAvatarId,
        num_pieces: numPieces,
        platform,
        tier_distribution: tierDistribution,
        include_hooks: true,
        safety_check: true,
        upload_to_storage: true,
      })

      // Success - close dialog and notify parent
      onOpenChange(false)
      if (onSuccess) onSuccess()

      // Reset form
      setSelectedAvatarId("")
      setNumPieces(50)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start batch generation")
    } finally {
      setLoading(false)
    }
  }

  const estimatedCost = (numPieces * 0.25).toFixed(2)
  const estimatedTime = Math.ceil((numPieces * 8) / 60 / 5) // 5 concurrent workers

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px] bg-slate-950/90 border-white/10">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-emerald-300" />
            New Batch Generation
          </DialogTitle>
          <DialogDescription>
            Generate {numPieces} content pieces with LoRA + hooks
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Avatar Selection */}
          <div className="grid gap-2">
            <Label htmlFor="avatar">Select Avatar</Label>
            <Select value={selectedAvatarId} onValueChange={setSelectedAvatarId}>
              <SelectTrigger id="avatar">
                <SelectValue placeholder="Choose an avatar..." />
              </SelectTrigger>
              <SelectContent>
                {avatars
                  .filter((a) => a.lora_weights_url) // Only avatars with trained LoRAs
                  .map((avatar) => (
                    <SelectItem key={avatar.id} value={avatar.id}>
                      {avatar.name}
                      {!avatar.lora_weights_url && (
                        <Badge variant="outline" className="ml-2 text-xs">
                          No LoRA
                        </Badge>
                      )}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-soft">
              Only avatars with trained LoRA weights can generate content
            </p>
          </div>

          {/* Number of Pieces */}
          <div className="grid gap-2">
            <Label htmlFor="num-pieces">Number of Pieces</Label>
            <Input
              id="num-pieces"
              type="number"
              min={1}
              max={100}
              value={numPieces}
              onChange={(e) => setNumPieces(parseInt(e.target.value) || 50)}
            />
            <p className="text-xs text-soft">Recommended: 50 pieces per batch</p>
          </div>

          {/* Platform */}
          <div className="grid gap-2">
            <Label htmlFor="platform">Target Platform</Label>
            <Select value={platform} onValueChange={setPlatform}>
              <SelectTrigger id="platform">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="instagram">Instagram</SelectItem>
                <SelectItem value="tiktok">TikTok</SelectItem>
                <SelectItem value="x">X (Twitter)</SelectItem>
                <SelectItem value="facebook">Facebook</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tier Distribution */}
          <div className="grid gap-2">
            <Label>Tier Distribution</Label>
            <div className="flex gap-2">
              <div className="flex-1">
                <Label className="text-xs text-soft">Layer 1</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={tierDistribution.capa1}
                  onChange={(e) =>
                    setTierDistribution({
                      ...tierDistribution,
                      capa1: parseInt(e.target.value) || 0,
                    })
                  }
                  className="text-sm"
                />
              </div>
              <div className="flex-1">
                <Label className="text-xs text-soft">Layer 2</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={tierDistribution.capa2}
                  onChange={(e) =>
                    setTierDistribution({
                      ...tierDistribution,
                      capa2: parseInt(e.target.value) || 0,
                    })
                  }
                  className="text-sm"
                />
              </div>
              <div className="flex-1">
                <Label className="text-xs text-soft">Layer 3</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={tierDistribution.capa3}
                  onChange={(e) =>
                    setTierDistribution({
                      ...tierDistribution,
                      capa3: parseInt(e.target.value) || 0,
                    })
                  }
                  className="text-sm"
                />
              </div>
            </div>
            <p className="text-xs text-soft">Percentages (must sum to 100%)</p>
          </div>

          {/* Estimates */}
          <div className="border border-white/10 rounded-xl p-3 space-y-2 bg-white/5">
            <div className="flex justify-between text-sm">
              <span className="text-soft">Estimated Cost</span>
              <span className="font-semibold text-emerald-300">${estimatedCost}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-soft">Estimated Time</span>
              <span className="font-semibold">{estimatedTime} minutes</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-soft">Workers</span>
              <span className="font-semibold">5 concurrent</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3">
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleGenerate}
            disabled={loading || !selectedAvatarId}
            variant="success"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Batch
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
