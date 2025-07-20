/**
 * Input Component
 * 
 * A styled input component with consistent theming and accessibility.
 * Enhanced with ARIA attributes and validation support.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useId } from '../../lib/accessibility';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
  showLabel?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    type, 
    label, 
    error, 
    helpText, 
    showLabel = true,
    id: providedId,
    ...props 
  }, ref) => {
    const generatedId = useId('input');
    const inputId = providedId || generatedId;
    const errorId = error ? `${inputId}-error` : undefined;
    const helpId = helpText ? `${inputId}-help` : undefined;
    
    const describedBy = [errorId, helpId].filter(Boolean).join(' ') || undefined;

    const inputElement = (
      <input
        id={inputId}
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          error && 'border-destructive focus-visible:ring-destructive',
          className
        )}
        ref={ref}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={describedBy}
        {...props}
      />
    );

    if (!label) {
      return inputElement;
    }

    return (
      <div className="space-y-2">
        <label 
          htmlFor={inputId}
          className={cn(
            'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
            !showLabel && 'sr-only'
          )}
        >
          {label}
          {props.required && <span className="text-destructive ml-1">*</span>}
        </label>
        {inputElement}
        {helpText && (
          <p id={helpId} className="text-sm text-muted-foreground">
            {helpText}
          </p>
        )}
        {error && (
          <p id={errorId} className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

export { Input };
