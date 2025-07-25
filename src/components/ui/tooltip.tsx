import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { cn } from "@/lib/utils";

const TooltipProvider = TooltipPrimitive.Provider;

const Tooltip = TooltipPrimitive.Root;

const TooltipTrigger = TooltipPrimitive.Trigger;

const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Content
    ref={ref}
    sideOffset={sideOffset}
    className={cn(
      "z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className
    )}
    {...props}
  />
));
TooltipContent.displayName = TooltipPrimitive.Content.displayName;

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };

// Enhanced tooltip with shortcut display
interface TooltipWithShortcutProps {
  children: React.ReactNode;
  content: string;
  shortcut?: string;
  side?: "top" | "bottom" | "left" | "right";
  disabled?: boolean;
}

export function TooltipWithShortcut({ 
  children, 
  content, 
  shortcut, 
  side = "top",
  disabled = false 
}: TooltipWithShortcutProps) {
  if (disabled) {
    return <>{children}</>;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {children}
      </TooltipTrigger>
      <TooltipContent side={side} className="flex flex-col items-center space-y-1">
        <span>{content}</span>
        {shortcut && (
          <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded font-mono">
            {shortcut}
          </span>
        )}
      </TooltipContent>
    </Tooltip>
  );
}

// Quick tooltip for simple use cases
interface QuickTooltipProps {
  content: string;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  disabled?: boolean;
}

export function QuickTooltip({ 
  content, 
  children, 
  side = "top",
  disabled = false 
}: QuickTooltipProps) {
  if (disabled) {
    return <>{children}</>;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {children}
      </TooltipTrigger>
      <TooltipContent side={side}>
        {content}
      </TooltipContent>
    </Tooltip>
  );
}
