/**
 * Accessible Loading Spinner Component
 * 
 * A loading spinner with proper ARIA attributes and screen reader support
 */

import React from 'react';
import { cn } from '../../lib/utils';
import { Loader2 } from 'lucide-react';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
  description?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  label = 'Loading',
  description,
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label}
      className={cn('flex items-center justify-center', className)}
    >
      <Loader2 
        className={cn('animate-spin', sizeClasses[size])}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
      {description && (
        <span className="sr-only">{description}</span>
      )}
    </div>
  );
};

export default LoadingSpinner;
