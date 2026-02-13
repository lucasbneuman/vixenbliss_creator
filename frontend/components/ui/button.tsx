import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-emerald-600 text-white hover:bg-emerald-500 shadow-[0_10px_30px_rgba(16,185,129,0.2)]",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        outline: "border border-white/25 bg-slate-900/80 hover:bg-slate-800 text-white shadow-[0_10px_25px_rgba(0,0,0,0.25)]",
        secondary: "bg-slate-800/90 text-white hover:bg-slate-700 border border-white/10",
        ghost: "hover:bg-white/10 hover:text-slate-100",
        link: "text-slate-100 underline-offset-4 hover:underline",
        success: "bg-emerald-600 text-white hover:bg-emerald-500 shadow-[0_10px_30px_rgba(16,185,129,0.2)]",
        warning: "bg-amber-600 text-white hover:bg-amber-500",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
