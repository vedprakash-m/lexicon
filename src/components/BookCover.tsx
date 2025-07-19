import React, { useState, useCallback } from 'react';
import { BookOpen, RefreshCw, AlertCircle } from 'lucide-react';
import { useBookCover, createPlaceholderCover } from '../hooks/useVisualAssets';
import { cn } from '../lib/utils';

interface BookCoverProps {
  bookId: string;
  title: string;
  authors: string[];
  isbn?: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
  showRefreshButton?: boolean;
  fallbackType?: 'icon' | 'placeholder' | 'generated';
}

const sizeClasses = {
  small: 'w-16 h-24',
  medium: 'w-32 h-48',
  large: 'w-48 h-72'
};

const BookCover: React.FC<BookCoverProps> = ({
  bookId,
  title,
  authors,
  isbn,
  size = 'medium',
  className,
  showRefreshButton = false,
  fallbackType = 'generated'
}) => {
  const { coverUrl, isLoading, error, isFallback, refreshCover } = useBookCover(
    bookId,
    title,
    authors,
    isbn
  );
  
  const [imageError, setImageError] = useState(false);
  const [generatedPlaceholder, setGeneratedPlaceholder] = useState<string | null>(null);

  const handleImageError = useCallback(() => {
    setImageError(true);
    if (fallbackType === 'generated' && !generatedPlaceholder) {
      const placeholder = createPlaceholderCover(title, authors);
      setGeneratedPlaceholder(placeholder);
    }
  }, [fallbackType, generatedPlaceholder, title, authors]);

  const handleRefresh = useCallback(() => {
    setImageError(false);
    setGeneratedPlaceholder(null);
    refreshCover();
  }, [refreshCover]);

  const renderFallback = () => {
    if (fallbackType === 'icon') {
      return (
        <div className={cn(
          'flex items-center justify-center bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg',
          sizeClasses[size]
        )}>
          <BookOpen className="w-8 h-8 text-gray-400" />
        </div>
      );
    }

    if (fallbackType === 'generated' && generatedPlaceholder) {
      return (
        <img
          src={generatedPlaceholder}
          alt={`Generated cover for ${title}`}
          className={cn(
            'object-cover rounded-lg shadow-md',
            sizeClasses[size]
          )}
        />
      );
    }

    // Default placeholder
    return (
      <div className={cn(
        'flex flex-col items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg shadow-md p-2',
        sizeClasses[size]
      )}>
        <BookOpen className="w-6 h-6 mb-1" />
        <span className="text-xs text-center font-medium line-clamp-2">
          {title}
        </span>
        {authors.length > 0 && (
          <span className="text-xs opacity-80 text-center mt-1">
            {authors[0]}
          </span>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className={cn(
        'flex items-center justify-center bg-gray-100 rounded-lg animate-pulse',
        sizeClasses[size],
        className
      )}>
        <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (error && !coverUrl) {
    return (
      <div className={cn(
        'flex flex-col items-center justify-center bg-red-50 border border-red-200 rounded-lg p-2',
        sizeClasses[size],
        className
      )}>
        <AlertCircle className="w-6 h-6 text-red-500 mb-1" />
        <span className="text-xs text-red-600 text-center">
          Cover Error
        </span>
        {showRefreshButton && (
          <button
            onClick={handleRefresh}
            className="mt-1 text-xs text-red-600 hover:text-red-800 underline"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (!coverUrl || imageError) {
    return (
      <div className={cn('relative group', className)}>
        {renderFallback()}
        {showRefreshButton && (
          <button
            onClick={handleRefresh}
            className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white rounded-full p-1 shadow-md"
            title="Refresh cover"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={cn('relative group', className)}>
      <img
        src={coverUrl}
        alt={`Cover for ${title}`}
        className={cn(
          'object-cover rounded-lg shadow-md transition-transform duration-300 group-hover:scale-105',
          sizeClasses[size],
          isFallback && 'opacity-90'
        )}
        onError={handleImageError}
      />
      
      {isFallback && (
        <div className="absolute bottom-1 right-1 bg-black bg-opacity-50 text-white text-xs px-1 py-0.5 rounded">
          Generated
        </div>
      )}
      
      {showRefreshButton && (
        <button
          onClick={handleRefresh}
          className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white rounded-full p-1 shadow-md"
          title="Refresh cover"
        >
          <RefreshCw className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};

export default BookCover;
