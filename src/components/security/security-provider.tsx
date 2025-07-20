import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Shield, AlertTriangle, CheckCircle, Eye, EyeOff, Lock, Unlock } from 'lucide-react';
import { Button } from '../ui';
import { cn } from '@/lib/utils';

// Security Context for global security state
interface SecurityState {
  isAuthenticated: boolean;
  sessionTimeout: number;
  lastActivity: number;
  securityLevel: 'low' | 'medium' | 'high';
  encryptionEnabled: boolean;
  biometricEnabled: boolean;
  sessionActive: boolean;
}

interface SecurityContextType {
  state: SecurityState;
  updateSecurityLevel: (level: 'low' | 'medium' | 'high') => void;
  extendSession: () => void;
  lockSession: () => void;
  unlockSession: (password: string) => Promise<boolean>;
  enableEncryption: () => void;
  disableEncryption: () => void;
  isSecureContext: boolean;
}

const SecurityContext = createContext<SecurityContextType | null>(null);

export const useSecurity = () => {
  const context = useContext(SecurityContext);
  if (!context) {
    throw new Error('useSecurity must be used within SecurityProvider');
  }
  return context;
};

// Security Provider Component
export const SecurityProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [state, setState] = useState<SecurityState>(() => {
    const stored = localStorage.getItem('lexicon-security-preferences');
    const preferences = stored ? JSON.parse(stored) : {};
    
    return {
      isAuthenticated: false,
      sessionTimeout: preferences.sessionTimeout || 30 * 60 * 1000, // 30 minutes
      lastActivity: Date.now(),
      securityLevel: preferences.securityLevel || 'medium',
      encryptionEnabled: preferences.encryptionEnabled || false,
      biometricEnabled: preferences.biometricEnabled || false,
      sessionActive: true,
      ...preferences
    };
  });

  const isSecureContext = window.isSecureContext;

  // Session management
  useEffect(() => {
    const checkSession = () => {
      const now = Date.now();
      const timeSinceActivity = now - state.lastActivity;
      
      if (timeSinceActivity > state.sessionTimeout && state.sessionActive) {
        setState(prev => ({ ...prev, sessionActive: false }));
        console.log('🔒 Session timeout - locking application');
      }
    };

    const interval = setInterval(checkSession, 60000); // Check every minute
    
    // Activity tracking
    const updateActivity = () => {
      setState(prev => ({ ...prev, lastActivity: Date.now() }));
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });

    return () => {
      clearInterval(interval);
      events.forEach(event => {
        document.removeEventListener(event, updateActivity);
      });
    };
  }, [state.sessionTimeout, state.sessionActive]);

  // Persist security preferences
  useEffect(() => {
    const preferences = {
      sessionTimeout: state.sessionTimeout,
      securityLevel: state.securityLevel,
      encryptionEnabled: state.encryptionEnabled,
      biometricEnabled: state.biometricEnabled
    };
    localStorage.setItem('lexicon-security-preferences', JSON.stringify(preferences));
  }, [state.sessionTimeout, state.securityLevel, state.encryptionEnabled, state.biometricEnabled]);

  const updateSecurityLevel = (level: 'low' | 'medium' | 'high') => {
    const timeouts = {
      low: 60 * 60 * 1000,    // 1 hour
      medium: 30 * 60 * 1000, // 30 minutes
      high: 15 * 60 * 1000    // 15 minutes
    };
    
    setState(prev => ({
      ...prev,
      securityLevel: level,
      sessionTimeout: timeouts[level]
    }));
  };

  const extendSession = () => {
    setState(prev => ({ 
      ...prev, 
      lastActivity: Date.now(),
      sessionActive: true 
    }));
  };

  const lockSession = () => {
    setState(prev => ({ ...prev, sessionActive: false }));
  };

  const unlockSession = async (password: string): Promise<boolean> => {
    // In a real implementation, this would validate against stored credentials
    // For demo purposes, we'll simulate validation
    const isValid = password.length >= 6; // Simple validation
    
    if (isValid) {
      setState(prev => ({
        ...prev,
        sessionActive: true,
        lastActivity: Date.now(),
        isAuthenticated: true
      }));
    }
    
    return isValid;
  };

  const enableEncryption = () => {
    setState(prev => ({ ...prev, encryptionEnabled: true }));
  };

  const disableEncryption = () => {
    setState(prev => ({ ...prev, encryptionEnabled: false }));
  };

  return (
    <SecurityContext.Provider value={{
      state,
      updateSecurityLevel,
      extendSession,
      lockSession,
      unlockSession,
      enableEncryption,
      disableEncryption,
      isSecureContext
    }}>
      {children}
    </SecurityContext.Provider>
  );
};

// Secure Input Component
interface SecureInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  showToggle?: boolean;
  strength?: boolean;
  onStrengthChange?: (strength: number) => void;
}

export const SecureInput: React.FC<SecureInputProps> = ({
  showToggle = false,
  strength = false,
  onStrengthChange,
  className,
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [inputValue, setInputValue] = useState('');
  
  const calculateStrength = useCallback((password: string): number => {
    let score = 0;
    
    if (password.length >= 8) score += 25;
    if (password.length >= 12) score += 25;
    if (/[a-z]/.test(password)) score += 12.5;
    if (/[A-Z]/.test(password)) score += 12.5;
    if (/[0-9]/.test(password)) score += 12.5;
    if (/[^A-Za-z0-9]/.test(password)) score += 12.5;
    
    return Math.min(score, 100);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);
    
    if (strength && onStrengthChange) {
      const strengthScore = calculateStrength(value);
      onStrengthChange(strengthScore);
    }
    
    props.onChange?.(e);
  };

  const strengthScore = strength ? calculateStrength(inputValue) : 0;
  const strengthColor = strengthScore < 40 ? 'bg-red-500' : 
                       strengthScore < 70 ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div className="relative">
      <input
        {...props}
        type={showToggle ? (isVisible ? 'text' : 'password') : props.type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
          "text-sm ring-offset-background file:border-0 file:bg-transparent",
          "file:text-sm file:font-medium placeholder:text-muted-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          showToggle && "pr-10",
          className
        )}
        value={inputValue}
        onChange={handleChange}
      />
      
      {showToggle && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
          onClick={() => setIsVisible(!isVisible)}
          aria-label={isVisible ? 'Hide password' : 'Show password'}
        >
          {isVisible ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </Button>
      )}
      
      {strength && inputValue && (
        <div className="mt-2 space-y-1">
          <div className="flex justify-between text-xs">
            <span>Password Strength</span>
            <span className={cn(
              strengthScore < 40 ? 'text-red-600' : 
              strengthScore < 70 ? 'text-yellow-600' : 'text-green-600'
            )}>
              {strengthScore < 40 ? 'Weak' : 
               strengthScore < 70 ? 'Medium' : 'Strong'}
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div 
              className={cn("h-2 rounded-full transition-all", strengthColor)}
              style={{ width: `${strengthScore}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

// Security Dashboard Component
export const SecurityDashboard: React.FC<{ className?: string }> = ({ 
  className 
}) => {
  const { state, updateSecurityLevel, isSecureContext } = useSecurity();
  
  const securityChecks = [
    {
      id: 'https',
      label: 'HTTPS Connection',
      status: isSecureContext,
      description: 'Connection is encrypted and secure',
      severity: 'high' as const
    },
    {
      id: 'encryption',
      label: 'Data Encryption',
      status: state.encryptionEnabled,
      description: 'Local data is encrypted at rest',
      severity: 'high' as const
    },
    {
      id: 'session',
      label: 'Session Security',
      status: state.sessionActive && state.sessionTimeout > 0,
      description: 'Session timeout is configured',
      severity: 'medium' as const
    },
    {
      id: 'biometric',
      label: 'Biometric Authentication',
      status: state.biometricEnabled,
      description: 'Enhanced authentication enabled',
      severity: 'low' as const
    }
  ];

  const getStatusIcon = (status: boolean) => {
    return status ? (
      <CheckCircle className="h-5 w-5 text-green-500" />
    ) : (
      <AlertTriangle className="h-5 w-5 text-yellow-500" />
    );
  };

  const getSecurityScore = () => {
    const totalChecks = securityChecks.length;
    const passedChecks = securityChecks.filter(check => check.status).length;
    return Math.round((passedChecks / totalChecks) * 100);
  };

  const securityScore = getSecurityScore();

  return (
    <div className={cn("space-y-6 p-4", className)}>
      <div className="flex items-center space-x-2">
        <Shield className="h-6 w-6" />
        <h2 className="text-lg font-semibold">Security Dashboard</h2>
      </div>

      {/* Security Score */}
      <div className="p-4 border rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Security Score</span>
          <span className={cn(
            "text-lg font-bold",
            securityScore >= 80 ? 'text-green-600' : 
            securityScore >= 60 ? 'text-yellow-600' : 'text-red-600'
          )}>
            {securityScore}%
          </span>
        </div>
        <div className="w-full bg-muted rounded-full h-2">
          <div 
            className={cn(
              "h-2 rounded-full transition-all",
              securityScore >= 80 ? 'bg-green-500' : 
              securityScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
            )}
            style={{ width: `${securityScore}%` }}
          />
        </div>
      </div>

      {/* Security Checks */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium">Security Checks</h3>
        {securityChecks.map((check) => (
          <div key={check.id} className="flex items-start space-x-3 p-3 border rounded-lg">
            {getStatusIcon(check.status)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{check.label}</p>
                <span className={cn(
                  "text-xs px-2 py-1 rounded-full",
                  check.severity === 'high' && "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
                  check.severity === 'medium' && "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
                  check.severity === 'low' && "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
                )}>
                  {check.severity}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{check.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Security Level Settings */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium">Security Level</h3>
        <div className="grid grid-cols-3 gap-2">
          {(['low', 'medium', 'high'] as const).map((level) => (
            <Button
              key={level}
              variant={state.securityLevel === level ? 'default' : 'outline'}
              size="sm"
              onClick={() => updateSecurityLevel(level)}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </Button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Current: {state.securityLevel} 
          (Session timeout: {Math.round(state.sessionTimeout / 60000)} minutes)
        </p>
      </div>

      {/* Session Status */}
      <div className="p-3 border rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Session Status</span>
          <div className="flex items-center space-x-2">
            {state.sessionActive ? (
              <>
                <Unlock className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600">Active</span>
              </>
            ) : (
              <>
                <Lock className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-600">Locked</span>
              </>
            )}
          </div>
        </div>
        {state.sessionActive && (
          <p className="text-xs text-muted-foreground mt-1">
            Last activity: {new Date(state.lastActivity).toLocaleTimeString()}
          </p>
        )}
      </div>

      {/* Recommendations */}
      {securityScore < 100 && (
        <div className="p-3 bg-muted rounded-lg">
          <h4 className="text-sm font-medium mb-2">Security Recommendations</h4>
          <ul className="text-xs space-y-1 text-muted-foreground">
            {!isSecureContext && (
              <li>• Use HTTPS for enhanced security</li>
            )}
            {!state.encryptionEnabled && (
              <li>• Enable data encryption for sensitive information</li>
            )}
            {!state.biometricEnabled && (
              <li>• Consider enabling biometric authentication</li>
            )}
            {state.securityLevel === 'low' && (
              <li>• Increase security level for better protection</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

// Session Lock Component
interface SessionLockProps {
  onUnlock: () => void;
}

export const SessionLock: React.FC<SessionLockProps> = ({ onUnlock }) => {
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { unlockSession } = useSecurity();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const success = await unlockSession(password);
      if (success) {
        onUnlock();
      } else {
        setError('Invalid password. Please try again.');
      }
    } catch (err) {
      setError('Failed to unlock session. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="max-w-md w-full mx-4 p-6 bg-background border rounded-lg shadow-lg">
        <div className="text-center mb-6">
          <Lock className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-semibold">Session Locked</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Your session has been locked for security. Please enter your password to continue.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="unlock-password" className="text-sm font-medium">
              Password
            </label>
            <SecureInput
              id="unlock-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              showToggle
              required
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 dark:bg-red-950 p-2 rounded">
              {error}
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !password}
          >
            {isLoading ? 'Unlocking...' : 'Unlock Session'}
          </Button>
        </form>
      </div>
    </div>
  );
};
