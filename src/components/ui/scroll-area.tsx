import * as React from "react"
import { cn } from "@/lib/utils"

const ScrollArea = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
  React.createElement('div', {
    ref,
    className: cn("relative overflow-hidden", className),
    ...props
  }, React.createElement('div', {
    className: "h-full w-full rounded-[inherit] overflow-auto"
  }, children))
))
ScrollArea.displayName = "ScrollArea"

const ScrollBar = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    orientation?: "vertical" | "horizontal"
  }
>(({ className, orientation = "vertical", ...props }, ref) => (
  React.createElement('div', {
    ref,
    className: cn(
      "flex touch-none select-none transition-colors",
      orientation === "vertical" &&
        "h-full w-2.5 border-l border-l-transparent p-[1px]",
      orientation === "horizontal" &&
        "h-2.5 flex-col border-t border-t-transparent p-[1px]",
      className
    ),
    ...props
  })
))
ScrollBar.displayName = "ScrollBar"

export { ScrollArea, ScrollBar }
