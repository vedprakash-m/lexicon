/**
 * Toast Component
 * 
 * A toast notification system for displaying temporary messages.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { Transition } from '@headlessui/react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  title: string;
  description?: string;
  type: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast = { ...toast, id };
    
    setToasts((prev) => [...prev, newToast]);

    // Auto-remove after duration (default 5 seconds)
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed bottom-0 right-0 z-50 w-full max-w-sm p-4 space-y-4">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getBorderColor = () => {
    switch (toast.type) {
      case 'success':
        return 'border-l-green-500';
      case 'error':
        return 'border-l-red-500';
      case 'warning':
        return 'border-l-yellow-500';
      case 'info':
        return 'border-l-blue-500';
    }
  };

  return (
    <Transition
      appear
      show={true}
      enter="transition-all duration-150"
      enterFrom="opacity-0 translate-x-full"
      enterTo="opacity-100 translate-x-0"
      leave="transition-all duration-150"
      leaveFrom="opacity-100 translate-x-0"
      leaveTo="opacity-0 translate-x-full"
    >
      <div
        className={cn(
          'relative w-full rounded-lg border border-border bg-card p-4 shadow-lg border-l-4',
          getBorderColor()
        )}
      >
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">{getIcon()}</div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-card-foreground">
              {toast.title}
            </div>
            {toast.description && (
              <div className="mt-1 text-sm text-muted-foreground">
                {toast.description}
              </div>
            )}
            {toast.action && (
              <div className="mt-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    toast.action!.onClick();
                    onClose();
                  }}
                >
                  {toast.action.label}
                </Button>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 flex-shrink-0"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Transition>
  );
}

// Convenience hooks for different toast types
export function useToastActions() {
  const { addToast } = useToast();

  return {
    success: (title: string, description?: string) =>
      addToast({ title, description, type: 'success' }),
    error: (title: string, description?: string) =>
      addToast({ title, description, type: 'error' }),
    warning: (title: string, description?: string) =>
      addToast({ title, description, type: 'warning' }),
    info: (title: string, description?: string) =>
      addToast({ title, description, type: 'info' }),
  };
}
