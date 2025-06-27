/**
 * Loading Spinner Component
 * 
 * A customizable loading spinner with different sizes and variants.
 */

import React from 'react';
import { cn } from '../../lib/utils';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'secondary' | 'muted';
  className?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ 
  size = 'md', 
  variant = 'default', 
  className 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  const variantClasses = {
    default: 'text-primary',
    secondary: 'text-secondary-foreground',
    muted: 'text-muted-foreground',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-transparent border-t-current',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export { Spinner };
