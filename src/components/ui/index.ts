/**
 * UI Component Library Index
 * 
 * Central export file for all Lexicon UI components.
 * This file provides a clean API for importing components throughout the application.
 */

// Core Components
export { Button } from './button';
export type { ButtonProps } from './button';

export { Input } from './input';
export type { InputProps } from './input';

export { Label } from './label';
export type { LabelProps } from './label';

export { Switch } from './switch';
export type { SwitchProps } from './switch';

export { Textarea } from './textarea';
export type { TextareaProps } from './textarea';

export { Select } from './select';
export type { SelectProps, SelectOption } from './select';

// Layout Components
export { Card } from './card';
export { Skeleton, SkeletonCard, SkeletonTable, SkeletonList } from './skeleton';
export type { SkeletonProps } from './skeleton';

export { Badge } from './badge';
export { Progress } from './progress';

// Navigation Components
export { Sidebar } from './sidebar';
export type { SidebarProps, SidebarItem } from './sidebar';

export { Header } from './header';
export type { HeaderProps } from './header';

export { Tabs, TabList, Tab, TabPanels, TabPanel } from './tabs';
export type { TabsProps, TabListProps, TabProps, TabPanelsProps, TabPanelProps } from './tabs';

// Export aliases for common naming conventions
export { TabList as TabsList, Tab as TabsTrigger, TabPanel as TabsContent } from './tabs';

// Modal Components
export {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from './dialog';
export type {
  DialogProps,
  DialogContentProps,
  DialogHeaderProps,
  DialogTitleProps,
  DialogDescriptionProps,
  DialogFooterProps,
} from './dialog';

// Feedback Components
export { ToastProvider, useToast, useToastActions } from './toast';
export type { Toast, ToastType } from './toast';

export { Spinner } from './spinner';
export type { SpinnerProps } from './spinner';

// Theme Components
export { ThemeProvider, useTheme } from './theme-provider';
export { ThemeToggle } from './theme-toggle';

// Advanced UI Components
export { 
  Tooltip, 
  TooltipTrigger, 
  TooltipContent, 
  TooltipProvider,
  TooltipWithShortcut,
  QuickTooltip 
} from './tooltip';

export { 
  KeyboardShortcutsProvider, 
  useShortcut, 
  useKeyboardShortcuts,
  formatShortcut,
  KeyboardShortcutsHelp,
  KeyboardShortcut 
} from './keyboard-shortcuts';

export { CommandPalette } from './command-palette';
export { HelpSystem } from './help-system';
export { SimpleHelpSystem, SimpleHelpButton } from './simple-help-system';

// Accessibility components
export * from '../accessibility';
