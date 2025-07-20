/**
 * Validated Form Components
 * 
 * Form components with built-in validation using the form validation framework
 */

import React from 'react';
import { Input, Textarea, Button } from '../ui';
import { useFormValidation, ValidationRule, ValidationRules } from '../../utils/formValidation';
import { cn } from '../../lib/utils';

interface ValidatedInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  name: string;
  label?: string;
  rules?: ValidationRule[];
  showError?: boolean;
  helpText?: string;
  onValidation?: (isValid: boolean, errors: string[]) => void;
}

export const ValidatedInput: React.FC<ValidatedInputProps> = ({
  name,
  label,
  rules = [],
  showError = true,
  helpText,
  className,
  onValidation,
  onChange,
  onBlur,
  ...props
}) => {
  const { setValue, getFieldError, hasFieldError, handleBlur, addFieldRules } = useFormValidation();

  React.useEffect(() => {
    if (rules.length > 0) {
      addFieldRules(name, rules);
    }
  }, [name, rules, addFieldRules]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setValue(name, value);
    
    if (onChange) {
      onChange(e);
    }

    if (onValidation) {
      // Delay validation callback to allow state to update
      setTimeout(() => {
        const error = getFieldError(name);
        onValidation(!hasFieldError(name), error ? [error] : []);
      }, 0);
    }
  };

  const handleFieldBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    handleBlur(name);
    if (onBlur) {
      onBlur(e);
    }
  };

  const error = showError ? getFieldError(name) : undefined;
  const isInvalid = hasFieldError(name);

  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={name} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          {label}
          {rules.some(rule => rule.type === 'required') && <span className="text-destructive ml-1">*</span>}
        </label>
      )}
      
      <Input
        id={name}
        name={name}
        className={cn(
          className,
          isInvalid && "border-destructive focus-visible:ring-destructive"
        )}
        aria-invalid={isInvalid}
        onChange={handleChange}
        onBlur={handleFieldBlur}
        {...props}
      />
      
      {helpText && !error && (
        <p className="text-sm text-muted-foreground">
          {helpText}
        </p>
      )}
      
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

interface ValidatedTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  name: string;
  label?: string;
  rules?: ValidationRule[];
  showError?: boolean;
  helpText?: string;
  onValidation?: (isValid: boolean, errors: string[]) => void;
}

export const ValidatedTextarea: React.FC<ValidatedTextareaProps> = ({
  name,
  label,
  rules = [],
  showError = true,
  helpText,
  className,
  onValidation,
  onChange,
  onBlur,
  ...props
}) => {
  const { setValue, getFieldError, hasFieldError, handleBlur, addFieldRules } = useFormValidation();

  React.useEffect(() => {
    if (rules.length > 0) {
      addFieldRules(name, rules);
    }
  }, [name, rules, addFieldRules]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setValue(name, value);
    
    if (onChange) {
      onChange(e);
    }

    if (onValidation) {
      setTimeout(() => {
        const error = getFieldError(name);
        onValidation(!hasFieldError(name), error ? [error] : []);
      }, 0);
    }
  };

  const handleFieldBlur = (e: React.FocusEvent<HTMLTextAreaElement>) => {
    handleBlur(name);
    if (onBlur) {
      onBlur(e);
    }
  };

  const error = showError ? getFieldError(name) : undefined;
  const isInvalid = hasFieldError(name);

  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={name} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
          {label}
          {rules.some(rule => rule.type === 'required') && <span className="text-destructive ml-1">*</span>}
        </label>
      )}
      
      <Textarea
        id={name}
        name={name}
        className={cn(
          className,
          isInvalid && "border-destructive focus-visible:ring-destructive"
        )}
        aria-invalid={isInvalid}
        onChange={handleChange}
        onBlur={handleFieldBlur}
        {...props}
      />
      
      {helpText && !error && (
        <p className="text-sm text-muted-foreground">
          {helpText}
        </p>
      )}
      
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

interface ValidatedFormProps {
  children: React.ReactNode;
  onSubmit: (values: Record<string, any>, isValid: boolean) => void;
  className?: string;
  showErrorSummary?: boolean;
}

export const ValidatedForm: React.FC<ValidatedFormProps> = ({
  children,
  onSubmit,
  className,
  showErrorSummary = false
}) => {
  const { validateForm, isValid, validation, values } = useFormValidation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validationResult = validateForm();
    onSubmit(values, validationResult.isValid);
  };

  return (
    <form onSubmit={handleSubmit} className={className}>
      {showErrorSummary && !isValid && validation.errors.length > 0 && (
        <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
          <h4 className="text-sm font-medium text-destructive mb-2">Please fix the following errors:</h4>
          <ul className="text-sm text-destructive space-y-1">
            {validation.errors.map((error, index) => (
              <li key={index}>• {error}</li>
            ))}
          </ul>
        </div>
      )}
      
      {children}
    </form>
  );
};

// Validation rule presets for common use cases
export const CommonValidationRules = {
  email: [
    ValidationRules.required('Email is required'),
    ValidationRules.email('Please enter a valid email address')
  ],
  
  password: [
    ValidationRules.required('Password is required'),
    ValidationRules.minLength(8, 'Password must be at least 8 characters'),
    ValidationRules.pattern(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      'Password must contain at least one lowercase letter, one uppercase letter, and one number'
    )
  ],
  
  url: [
    ValidationRules.required('URL is required'),
    ValidationRules.url('Please enter a valid URL')
  ],
  
  requiredText: [
    ValidationRules.required('This field is required'),
    ValidationRules.minLength(1, 'This field cannot be empty')
  ],
  
  fileName: [
    ValidationRules.required('File name is required'),
    ValidationRules.pattern(
      /^[^<>:"/\\|?*]+$/,
      'File name contains invalid characters'
    )
  ],
  
  positiveNumber: [
    ValidationRules.required('This field is required'),
    ValidationRules.number('Must be a valid number'),
    ValidationRules.custom(
      (value) => Number(value) > 0,
      'Must be a positive number'
    )
  ]
};
