import { useState, useCallback } from "react"

interface Toast {
  id: string
  title?: string
  description?: string
  variant?: "default" | "destructive"
}

interface ToastState {
  toasts: Toast[]
}

const initialState: ToastState = {
  toasts: []
}

let state = initialState
let listeners: Array<(state: ToastState) => void> = []

function dispatch(action: any) {
  // Simple toast management
  listeners.forEach((listener) => listener(state))
}

export function useToast() {
  const [, forceUpdate] = useState({})

  const toast = useCallback((props: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(2)
    const newToast: Toast = { id, ...props }
    
    state.toasts.push(newToast)
    dispatch(state)
    
    // Auto remove after 5 seconds
    setTimeout(() => {
      state.toasts = state.toasts.filter(t => t.id !== id)
      dispatch(state)
    }, 5000)
    
    return newToast
  }, [])

  const dismiss = useCallback((toastId: string) => {
    state.toasts = state.toasts.filter(t => t.id !== toastId)
    dispatch(state)
  }, [])

  return {
    toast,
    dismiss,
    toasts: state.toasts
  }
}
