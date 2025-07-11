/**
 * Skip Navigation Component
 * 
 * Provides keyboard users with a way to skip navigation and jump to main content
 */

import React from 'react';
import { Button } from '../ui/button';
import { useSkipToContent } from '../../lib/accessibility';

export const SkipNavigation: React.FC = () => {
  const { skipToMain } = useSkipToContent();

  return (
    <div className="sr-only focus-within:not-sr-only">
      <Button
        variant="outline"
        size="sm"
        onFocus={(e) => {
          // Make visible when focused
          e.currentTarget.parentElement?.classList.remove('sr-only');
        }}
        onBlur={(e) => {
          // Hide again when unfocused
          e.currentTarget.parentElement?.classList.add('sr-only');
        }}
        onClick={skipToMain}
        className="absolute top-4 left-4 z-50 bg-background border-2 border-primary focus:bg-primary focus:text-primary-foreground"
      >
        Skip to main content
      </Button>
    </div>
  );
};

export default SkipNavigation;
