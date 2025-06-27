/**
 * Dialog Component
 * 
 * A modal dialog component using Headless UI for accessibility.
 */

import React, { Fragment } from 'react';
import { Dialog as HeadlessDialog, Transition } from '@headlessui/react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from './button';

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

export interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
}

export interface DialogHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
}

export interface DialogDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export interface DialogFooterProps {
  children: React.ReactNode;
  className?: string;
}

const Dialog: React.FC<DialogProps> = ({ open, onClose, children, className }) => {
  return (
    <Transition appear show={open} as={Fragment}>
      <HeadlessDialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <HeadlessDialog.Panel
                className={cn(
                  'w-full max-w-md transform overflow-hidden rounded-lg bg-card p-6 text-left align-middle shadow-xl transition-all',
                  className
                )}
              >
                {children}
              </HeadlessDialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </HeadlessDialog>
    </Transition>
  );
};

const DialogContent: React.FC<DialogContentProps> = ({ children, className }) => (
  <div className={cn('relative', className)}>
    {children}
  </div>
);

const DialogHeader: React.FC<DialogHeaderProps> = ({ children, className }) => (
  <div className={cn('flex flex-col space-y-1.5 text-center sm:text-left', className)}>
    {children}
  </div>
);

const DialogTitle: React.FC<DialogTitleProps> = ({ children, className }) => (
  <HeadlessDialog.Title
    as="h3"
    className={cn('text-lg font-medium leading-6 text-card-foreground', className)}
  >
    {children}
  </HeadlessDialog.Title>
);

const DialogDescription: React.FC<DialogDescriptionProps> = ({ children, className }) => (
  <HeadlessDialog.Description
    className={cn('text-sm text-muted-foreground', className)}
  >
    {children}
  </HeadlessDialog.Description>
);

const DialogFooter: React.FC<DialogFooterProps> = ({ children, className }) => (
  <div className={cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-6', className)}>
    {children}
  </div>
);

const DialogClose: React.FC<{ onClose: () => void; className?: string }> = ({ onClose, className }) => (
  <Button
    variant="ghost"
    size="icon"
    className={cn('absolute right-4 top-4', className)}
    onClick={onClose}
  >
    <X className="h-4 w-4" />
    <span className="sr-only">Close</span>
  </Button>
);

export {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
};
