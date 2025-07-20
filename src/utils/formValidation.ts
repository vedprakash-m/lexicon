/**
 * Form Validation Framework
 * 
 * A comprehensive validation system for consistent form validation across components
 */

export interface ValidationRule {
  type: 'required' | 'minLength' | 'maxLength' | 'pattern' | 'email' | 'url' | 'number' | 'custom';
  message: string;
  value?: any;
  validator?: (value: any) => boolean;
}

export interface FieldValidation {
  isValid: boolean;
  errors: string[];
}

export interface FormValidation {
  isValid: boolean;
  fields: Record<string, FieldValidation>;
  errors: string[];
}

export class FormValidator {
  private rules: Record<string, ValidationRule[]> = {};
  private values: Record<string, any> = {};

  constructor(rules: Record<string, ValidationRule[]> = {}) {
    this.rules = rules;
  }

  // Add validation rules for a field
  addFieldRules(fieldName: string, rules: ValidationRule[]): void {
    this.rules[fieldName] = rules;
  }

  // Set field value
  setValue(fieldName: string, value: any): void {
    this.values[fieldName] = value;
  }

  // Set multiple values
  setValues(values: Record<string, any>): void {
    this.values = { ...this.values, ...values };
  }

  // Validate a single field
  validateField(fieldName: string, value?: any): FieldValidation {
    const fieldValue = value !== undefined ? value : this.values[fieldName];
    const fieldRules = this.rules[fieldName] || [];
    const errors: string[] = [];

    for (const rule of fieldRules) {
      if (!this.validateRule(fieldValue, rule)) {
        errors.push(rule.message);
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Validate all fields
  validateAll(): FormValidation {
    const fields: Record<string, FieldValidation> = {};
    const allErrors: string[] = [];

    for (const fieldName of Object.keys(this.rules)) {
      const fieldValidation = this.validateField(fieldName);
      fields[fieldName] = fieldValidation;
      
      if (!fieldValidation.isValid) {
        allErrors.push(...fieldValidation.errors);
      }
    }

    return {
      isValid: allErrors.length === 0,
      fields,
      errors: allErrors
    };
  }

  // Validate only specified fields
  validateFields(fieldNames: string[]): FormValidation {
    const fields: Record<string, FieldValidation> = {};
    const allErrors: string[] = [];

    for (const fieldName of fieldNames) {
      if (this.rules[fieldName]) {
        const fieldValidation = this.validateField(fieldName);
        fields[fieldName] = fieldValidation;
        
        if (!fieldValidation.isValid) {
          allErrors.push(...fieldValidation.errors);
        }
      }
    }

    return {
      isValid: allErrors.length === 0,
      fields,
      errors: allErrors
    };
  }

  // Check if form is valid without returning detailed results
  isValid(): boolean {
    return this.validateAll().isValid;
  }

  // Get validation errors for a specific field
  getFieldErrors(fieldName: string): string[] {
    return this.validateField(fieldName).errors;
  }

  // Clear validation rules
  clearRules(): void {
    this.rules = {};
  }

  // Clear values
  clearValues(): void {
    this.values = {};
  }

  // Private method to validate individual rules
  private validateRule(value: any, rule: ValidationRule): boolean {
    switch (rule.type) {
      case 'required':
        return this.validateRequired(value);
      
      case 'minLength':
        return this.validateMinLength(value, rule.value);
      
      case 'maxLength':
        return this.validateMaxLength(value, rule.value);
      
      case 'pattern':
        return this.validatePattern(value, rule.value);
      
      case 'email':
        return this.validateEmail(value);
      
      case 'url':
        return this.validateUrl(value);
      
      case 'number':
        return this.validateNumber(value);
      
      case 'custom':
        return rule.validator ? rule.validator(value) : true;
      
      default:
        return true;
    }
  }

  private validateRequired(value: any): boolean {
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    if (Array.isArray(value)) return value.length > 0;
    return true;
  }

  private validateMinLength(value: any, minLength: number): boolean {
    if (value === null || value === undefined) return true;
    const str = String(value);
    return str.length >= minLength;
  }

  private validateMaxLength(value: any, maxLength: number): boolean {
    if (value === null || value === undefined) return true;
    const str = String(value);
    return str.length <= maxLength;
  }

  private validatePattern(value: any, pattern: string | RegExp): boolean {
    if (value === null || value === undefined) return true;
    const str = String(value);
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
    return regex.test(str);
  }

  private validateEmail(value: any): boolean {
    if (value === null || value === undefined) return true;
    const str = String(value);
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(str);
  }

  private validateUrl(value: any): boolean {
    if (value === null || value === undefined) return true;
    const str = String(value);
    try {
      new URL(str);
      return true;
    } catch {
      return false;
    }
  }

  private validateNumber(value: any): boolean {
    if (value === null || value === undefined) return true;
    return !isNaN(Number(value)) && isFinite(Number(value));
  }
}

// Common validation rule factories
export const ValidationRules = {
  required: (message = 'This field is required'): ValidationRule => ({
    type: 'required',
    message
  }),

  minLength: (length: number, message?: string): ValidationRule => ({
    type: 'minLength',
    value: length,
    message: message || `Must be at least ${length} characters`
  }),

  maxLength: (length: number, message?: string): ValidationRule => ({
    type: 'maxLength',
    value: length,
    message: message || `Must be no more than ${length} characters`
  }),

  email: (message = 'Must be a valid email address'): ValidationRule => ({
    type: 'email',
    message
  }),

  url: (message = 'Must be a valid URL'): ValidationRule => ({
    type: 'url',
    message
  }),

  pattern: (pattern: string | RegExp, message = 'Invalid format'): ValidationRule => ({
    type: 'pattern',
    value: pattern,
    message
  }),

  number: (message = 'Must be a valid number'): ValidationRule => ({
    type: 'number',
    message
  }),

  custom: (validator: (value: any) => boolean, message = 'Invalid value'): ValidationRule => ({
    type: 'custom',
    validator,
    message
  })
};

// React hook for form validation
import { useState, useCallback, useEffect } from 'react';

export interface UseFormValidationOptions {
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  debounceMs?: number;
}

export function useFormValidation(
  initialRules: Record<string, ValidationRule[]> = {},
  options: UseFormValidationOptions = {}
) {
  const [validator] = useState(() => new FormValidator(initialRules));
  const [validation, setValidation] = useState<FormValidation>({ isValid: true, fields: {}, errors: [] });
  const [formValues, setFormValues] = useState<Record<string, any>>({});

  const {
    validateOnChange = true,
    validateOnBlur = true,
    debounceMs = 300
  } = options;

  // Debounce validation
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  const validateForm = useCallback(() => {
    const result = validator.validateAll();
    setValidation(result);
    return result;
  }, [validator]);

  const validateField = useCallback((fieldName: string) => {
    const result = validator.validateField(fieldName);
    setValidation(prev => ({
      ...prev,
      fields: {
        ...prev.fields,
        [fieldName]: result
      },
      isValid: Object.values({ ...prev.fields, [fieldName]: result }).every(f => f.isValid)
    }));
    return result;
  }, [validator]);

  const setValue = useCallback((fieldName: string, value: any) => {
    validator.setValue(fieldName, value);
    setFormValues(prev => ({ ...prev, [fieldName]: value }));

    if (validateOnChange) {
      if (debounceMs > 0) {
        if (debounceTimer) clearTimeout(debounceTimer);
        setDebounceTimer(setTimeout(() => validateField(fieldName), debounceMs));
      } else {
        validateField(fieldName);
      }
    }
  }, [validator, validateOnChange, validateField, debounceMs, debounceTimer]);

  const setValues = useCallback((newValues: Record<string, any>) => {
    validator.setValues(newValues);
    setFormValues(prev => ({ ...prev, ...newValues }));

    if (validateOnChange) {
      if (debounceMs > 0) {
        if (debounceTimer) clearTimeout(debounceTimer);
        setDebounceTimer(setTimeout(() => validateForm(), debounceMs));
      } else {
        validateForm();
      }
    }
  }, [validator, validateOnChange, validateForm, debounceMs, debounceTimer]);

  const handleBlur = useCallback((fieldName: string) => {
    if (validateOnBlur) {
      validateField(fieldName);
    }
  }, [validateOnBlur, validateField]);

  const addFieldRules = useCallback((fieldName: string, rules: ValidationRule[]) => {
    validator.addFieldRules(fieldName, rules);
  }, [validator]);

  const getFieldError = useCallback((fieldName: string): string | undefined => {
    const fieldValidation = validation.fields[fieldName];
    return fieldValidation && !fieldValidation.isValid ? fieldValidation.errors[0] : undefined;
  }, [validation]);

  const hasFieldError = useCallback((fieldName: string): boolean => {
    const fieldValidation = validation.fields[fieldName];
    return fieldValidation ? !fieldValidation.isValid : false;
  }, [validation]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer) clearTimeout(debounceTimer);
    };
  }, [debounceTimer]);

  return {
    validation,
    values: formValues,
    setValue,
    setValues,
    validateForm,
    validateField,
    handleBlur,
    addFieldRules,
    getFieldError,
    hasFieldError,
    isValid: validation.isValid
  };
}
