/**
 * Accessible Form Field Component
 * 
 * A comprehensive form field wrapper with proper labeling and error handling
 */

import React from 'react';
import { cn } from '../../lib/utils';
import { useId } from '../../lib/accessibility';

interface FormFieldProps {
  children: React.ReactElement;
  label?: string;
  description?: string;
  error?: string;
  required?: boolean;
  className?: string;
  hideLabel?: boolean;
}

export const FormField: React.FC<FormFieldProps> = ({
  children,
  label,
  description,
  error,
  required = false,
  className,
  hideLabel = false,
}) => {
  const fieldId = useId('field');
  const errorId = error ? `${fieldId}-error` : undefined;
  const descriptionId = description ? `${fieldId}-description` : undefined;
  
  const describedBy = [descriptionId, errorId].filter(Boolean).join(' ') || undefined;

  // Clone the child element and add accessibility props
  const enhancedChild = React.cloneElement(children, {
    id: fieldId,
    'aria-describedby': describedBy,
    'aria-invalid': error ? 'true' : 'false',
    'aria-required': required,
    ...children.props,
  });

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <label
          htmlFor={fieldId}
          className={cn(
            'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
            hideLabel && 'sr-only'
          )}
        >
          {label}
          {required && <span className="text-destructive ml-1" aria-label="required">*</span>}
        </label>
      )}
      
      {enhancedChild}
      
      {description && (
        <p id={descriptionId} className="text-sm text-muted-foreground">
          {description}
        </p>
      )}
      
      {error && (
        <p id={errorId} className="text-sm text-destructive" role="alert" aria-live="polite">
          {error}
        </p>
      )}
    </div>
  );
};

export default FormField;
