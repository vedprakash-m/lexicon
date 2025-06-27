/**
 * Tabs Component
 * 
 * A tab navigation component using Headless UI for accessibility.
 */

import React, { Fragment } from 'react';
import { Tab as HeadlessTab } from '@headlessui/react';
import { cn } from '../../lib/utils';

export interface TabsProps {
  defaultIndex?: number;
  selectedIndex?: number;
  onChange?: (index: number) => void;
  children: React.ReactNode;
  className?: string;
}

export interface TabListProps {
  children: React.ReactNode;
  className?: string;
}

export interface TabProps {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}

export interface TabPanelsProps {
  children: React.ReactNode;
  className?: string;
}

export interface TabPanelProps {
  children: React.ReactNode;
  className?: string;
}

const Tabs: React.FC<TabsProps> = ({ 
  defaultIndex, 
  selectedIndex, 
  onChange, 
  children, 
  className 
}) => {
  return (
    <HeadlessTab.Group
      defaultIndex={defaultIndex}
      selectedIndex={selectedIndex}
      onChange={onChange}
      as="div"
      className={className}
    >
      {children}
    </HeadlessTab.Group>
  );
};

const TabList: React.FC<TabListProps> = ({ children, className }) => {
  return (
    <HeadlessTab.List
      className={cn(
        'flex space-x-1 rounded-lg bg-muted p-1',
        className
      )}
    >
      {children}
    </HeadlessTab.List>
  );
};

const Tab: React.FC<TabProps> = ({ children, className, disabled }) => {
  return (
    <HeadlessTab as={Fragment}>
      {({ selected }) => (
        <button
          disabled={disabled}
          className={cn(
            'w-full rounded-md py-2.5 px-3 text-sm font-medium leading-5 transition-all',
            'ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            selected
              ? 'bg-background text-foreground shadow'
              : 'text-muted-foreground hover:bg-background/50 hover:text-foreground',
            disabled && 'cursor-not-allowed opacity-50',
            className
          )}
        >
          {children}
        </button>
      )}
    </HeadlessTab>
  );
};

const TabPanels: React.FC<TabPanelsProps> = ({ children, className }) => {
  return (
    <HeadlessTab.Panels className={cn('mt-4', className)}>
      {children}
    </HeadlessTab.Panels>
  );
};

const TabPanel: React.FC<TabPanelProps> = ({ children, className }) => {
  return (
    <HeadlessTab.Panel
      className={cn(
        'rounded-lg bg-background p-4 ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        className
      )}
    >
      {children}
    </HeadlessTab.Panel>
  );
};

export { Tabs, TabList, Tab, TabPanels, TabPanel };
