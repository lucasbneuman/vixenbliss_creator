"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"

interface ActionButtonProps {
  children: React.ReactNode
  onClick: () => void | Promise<void>
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  size?: "default" | "sm" | "lg" | "icon"
  icon?: React.ReactNode
  confirmTitle?: string
  confirmDescription?: string
  requireConfirm?: boolean
  disabled?: boolean
  className?: string
}

export function ActionButton({
  children,
  onClick,
  variant = "default",
  size = "default",
  icon,
  confirmTitle,
  confirmDescription,
  requireConfirm = false,
  disabled = false,
  className
}: ActionButtonProps) {
  const [showDialog, setShowDialog] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleClick = async () => {
    if (requireConfirm) {
      setShowDialog(true)
      return
    }

    await executeAction()
  }

  const executeAction = async () => {
    setIsLoading(true)
    try {
      await onClick()
    } finally {
      setIsLoading(false)
      setShowDialog(false)
    }
  }

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={handleClick}
        disabled={disabled || isLoading}
        className={cn("gap-2", className)}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          icon
        )}
        {children}
      </Button>

      {requireConfirm && (
        <Dialog open={showDialog} onOpenChange={setShowDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{confirmTitle || "Confirm Action"}</DialogTitle>
              <DialogDescription>
                {confirmDescription || "Are you sure you want to proceed with this action?"}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowDialog(false)}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button
                variant={variant}
                onClick={executeAction}
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                Confirm
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}

interface QuickActionButtonProps {
  action: "clone" | "kill" | "pause" | "activate"
  onAction: () => void | Promise<void>
  itemName?: string
  size?: "default" | "sm" | "lg" | "icon"
  disabled?: boolean
}

export function QuickActionButton({
  action,
  onAction,
  itemName = "this item",
  size = "sm",
  disabled = false
}: QuickActionButtonProps) {
  const configs = {
    clone: {
      label: "Clone",
      variant: "default" as const,
      confirmTitle: "Clone Model",
      confirmDescription: `Create a duplicate of ${itemName} with the same identity parameters and settings.`,
      className: "bg-sky-600 text-slate-100 hover:bg-sky-500"
    },
    kill: {
      label: "Kill",
      variant: "destructive" as const,
      confirmTitle: "Kill Model",
      confirmDescription: `This will permanently archive ${itemName} and stop all content generation. This action cannot be undone.`,
      className: ""
    },
    pause: {
      label: "Pause",
      variant: "outline" as const,
      confirmTitle: "Pause Model",
      confirmDescription: `Temporarily pause ${itemName}. Content generation and distribution will stop until reactivated.`,
      className: "border-yellow-400 text-yellow-200 hover:bg-yellow-500/10"
    },
    activate: {
      label: "Activate",
      variant: "default" as const,
      confirmTitle: "Activate Model",
      confirmDescription: `Resume content generation and distribution for ${itemName}.`,
      className: "bg-emerald-600 text-slate-100 hover:bg-emerald-500"
    }
  }

  const config = configs[action]

  return (
    <ActionButton
      onClick={onAction}
      variant={config.variant}
      size={size}
      requireConfirm={action === "kill"}
      confirmTitle={config.confirmTitle}
      confirmDescription={config.confirmDescription}
      disabled={disabled}
      className={config.className}
    >
      {config.label}
    </ActionButton>
  )
}
