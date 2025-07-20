import React, { useState } from 'react';
import { Plus, FileText, FolderPlus, Upload, BookOpen } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, Button } from '../ui';
import { useNavigate } from 'react-router-dom';

interface NewProjectDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const newProjectOptions = [
  {
    id: 'book',
    title: 'Add New Book',
    description: 'Upload and process a book (PDF, EPUB, MOBI, TXT)',
    icon: BookOpen,
    color: 'text-blue-500',
    action: '/library'
  },
  {
    id: 'project',
    title: 'Create Project',
    description: 'Start a new knowledge organization project',
    icon: FolderPlus,
    color: 'text-green-500',
    action: '/projects'
  },
  {
    id: 'batch',
    title: 'Batch Upload',
    description: 'Upload multiple files for processing',
    icon: Upload,
    color: 'text-purple-500',
    action: '/batch'
  },
  {
    id: 'document',
    title: 'New Document',
    description: 'Create a new text document',
    icon: FileText,
    color: 'text-orange-500',
    action: '/library'
  }
];

export function NewProjectDialog({ isOpen, onClose }: NewProjectDialogProps) {
  const navigate = useNavigate();

  const handleOptionClick = (option: typeof newProjectOptions[0]) => {
    onClose();
    navigate(option.action);
    
    // Trigger specific actions based on the option
    if (option.id === 'book') {
      // This would trigger file upload dialog in the library
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('lexicon:open-file-upload'));
      }, 100);
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            What would you like to create?
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          {newProjectOptions.map((option) => {
            const Icon = option.icon;
            return (
              <button
                key={option.id}
                onClick={() => handleOptionClick(option)}
                className="w-full p-4 text-left rounded-lg border border-border hover:bg-accent/50 transition-colors group"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg bg-background border ${option.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-sm group-hover:text-primary transition-colors">
                      {option.title}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      {option.description}
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
