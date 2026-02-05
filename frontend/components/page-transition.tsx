"use client"

import { motion, AnimatePresence } from "framer-motion"
import { ReactNode } from "react"

interface PageTransitionProps {
  children: ReactNode
  className?: string
}

export function PageTransition({ children, className = "" }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{
        type: "spring",
        stiffness: 100,
        damping: 15,
        duration: 0.3
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export function FadeIn({ children, delay = 0, className = "" }: PageTransitionProps & { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay, duration: 0.5 }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export function SlideIn({
  children,
  direction = "left",
  delay = 0,
  className = ""
}: PageTransitionProps & { direction?: "left" | "right" | "up" | "down"; delay?: number }) {
  const directionOffset = {
    left: { x: -100, y: 0 },
    right: { x: 100, y: 0 },
    up: { x: 0, y: -100 },
    down: { x: 0, y: 100 }
  }

  return (
    <motion.div
      initial={{ opacity: 0, ...directionOffset[direction] }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{
        delay,
        type: "spring",
        stiffness: 100,
        damping: 15
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export function ScaleIn({ children, delay = 0, className = "" }: PageTransitionProps & { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        delay,
        type: "spring",
        stiffness: 200,
        damping: 15
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export function StaggerContainer({
  children,
  staggerDelay = 0.1,
  className = ""
}: PageTransitionProps & { staggerDelay?: number }) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        visible: {
          transition: {
            staggerChildren: staggerDelay
          }
        }
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export function StaggerItem({ children, className = "" }: PageTransitionProps) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: {
          opacity: 1,
          y: 0,
          transition: {
            type: "spring",
            stiffness: 100
          }
        }
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
