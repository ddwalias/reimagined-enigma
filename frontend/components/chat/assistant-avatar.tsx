"use client"

import { cn } from "@/lib/utils"

interface AssistantAvatarProps {
  className?: string
  size?: number
}

export function AssistantAvatar({ className, size = 32 }: AssistantAvatarProps) {
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-white ring-1 ring-emerald-100 transition-colors dark:bg-stone-900 dark:ring-emerald-900/60",
        className,
      )}
      style={{
        width: size,
        height: size,
        boxShadow:
          "rgba(14, 63, 126, 0.04) 0px 0px 0px 1px, rgba(42, 51, 69, 0.04) 0px 1px 1px -0.5px, rgba(42, 51, 70, 0.04) 0px 3px 3px -1.5px, rgba(42, 51, 70, 0.04) 0px 6px 6px -3px",
      }}
      aria-hidden="true"
    >
      <img src="/optisigns-apple-touch.png" alt="" className="h-full w-full object-contain p-[8%]" />
    </div>
  )
}
