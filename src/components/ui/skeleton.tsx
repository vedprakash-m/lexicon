/**
 * Skeleton Component
 * 
 * Provides skeleton loading placeholders for better perceived performance
 * while components are loading dynamically.
 */

import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'card' | 'text' | 'circle' | 'button';
  pulse?: boolean;
  lines?: number;
}

const Skeleton = ({ 
  className, 
  variant = 'default',
  pulse = true,
  lines = 1,
  ...props 
}: SkeletonProps) => {
  const baseClasses = cn(
    "bg-gray-200 dark:bg-gray-800 rounded-md",
    pulse && "animate-pulse",
    className
  );

  const variants = {
    default: "h-4 w-full",
    card: "h-48 w-full rounded-lg",
    text: "h-4 w-full",
    circle: "h-12 w-12 rounded-full",
    button: "h-10 w-24 rounded-md"
  };

  if (variant === 'text' && lines > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={cn(
              baseClasses,
              variants[variant],
              index === lines - 1 && "w-3/4" // Last line shorter
            )}
            {...props}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(baseClasses, variants[variant])}
      {...props}
    />
  );
};

// Specialized skeleton components for common use cases
const SkeletonCard = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border rounded-lg space-y-3", className)} {...props}>
    <Skeleton variant="text" />
    <Skeleton variant="text" lines={2} />
    <div className="flex space-x-2">
      <Skeleton variant="button" />
      <Skeleton variant="button" />
    </div>
  </div>
);

const SkeletonTable = ({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) => (
  <div className="space-y-3">
    <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={`header-${i}`} className="h-8" />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={`row-${rowIndex}`} className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, colIndex) => (
          <Skeleton key={`cell-${rowIndex}-${colIndex}`} className="h-6" />
        ))}
      </div>
    ))}
  </div>
);

const SkeletonList = ({ items = 5 }: { items?: number }) => (
  <div className="space-y-4">
    {Array.from({ length: items }).map((_, index) => (
      <div key={index} className="flex space-x-3">
        <Skeleton variant="circle" className="h-10 w-10" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      </div>
    ))}
  </div>
);

export { Skeleton, SkeletonCard, SkeletonTable, SkeletonList };
export type { SkeletonProps };
