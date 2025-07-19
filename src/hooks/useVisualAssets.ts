import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface AssetMetadata {
  asset_id: string;
  asset_type: string;
  source_url?: string;
  local_path?: string;
  width?: number;
  height?: number;
  file_size?: number;
  format?: string;
  quality?: string;
  checksum?: string;
  download_date?: string;
  last_accessed?: string;
  cache_expires?: string;
  fallback_used: boolean;
  error_count: number;
  last_error?: string;
}

export interface AssetCollection {
  entity_id: string;
  entity_type: string;
  assets: Record<string, AssetMetadata[]>;
  primary_cover?: string;
  primary_author_photo?: string;
  created_date: string;
  updated_date: string;
}

export interface CoverImageRequest {
  book_id: string;
  title: string;
  authors: string[];
  isbn?: string;
  preferred_size?: string;
}

export interface CoverImageResponse {
  success: boolean;
  asset_metadata?: AssetMetadata;
  local_path?: string;
  fallback_used: boolean;
  error?: string;
}

export interface UseVisualAssetsReturn {
  getCoverImage: (request: CoverImageRequest) => Promise<CoverImageResponse>;
  getAssetCollection: (entityId: string, entityType: string) => Promise<AssetCollection | null>;
  saveAssetCollection: (collection: AssetCollection) => Promise<boolean>;
  getAllAssetCollections: () => Promise<AssetCollection[]>;
  cleanupUnusedAssets: () => Promise<number>;
  isLoading: boolean;
  error: string | null;
}

export const useVisualAssets = (): UseVisualAssetsReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getCoverImage = useCallback(async (request: CoverImageRequest): Promise<CoverImageResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await invoke<CoverImageResponse>('get_book_cover', { request });
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get cover image';
      setError(errorMessage);
      return {
        success: false,
        fallback_used: false,
        error: errorMessage
      };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getAssetCollection = useCallback(async (entityId: string, entityType: string): Promise<AssetCollection | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const collection = await invoke<AssetCollection | null>('get_asset_collection', {
        entityId,
        entityType
      });
      return collection;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get asset collection';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveAssetCollection = useCallback(async (collection: AssetCollection): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const success = await invoke<boolean>('save_asset_collection', { collection });
      return success;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save asset collection';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getAllAssetCollections = useCallback(async (): Promise<AssetCollection[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const collections = await invoke<AssetCollection[]>('get_all_asset_collections');
      return collections;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get asset collections';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const cleanupUnusedAssets = useCallback(async (): Promise<number> => {
    setIsLoading(true);
    setError(null);

    try {
      const cleanedCount = await invoke<number>('cleanup_unused_assets');
      return cleanedCount;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cleanup unused assets';
      setError(errorMessage);
      return 0;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    getCoverImage,
    getAssetCollection,
    saveAssetCollection,
    getAllAssetCollections,
    cleanupUnusedAssets,
    isLoading,
    error
  };
};

export interface UseBookCoverReturn {
  coverUrl: string | null;
  isLoading: boolean;
  error: string | null;
  isFallback: boolean;
  refreshCover: () => void;
}

export const useBookCover = (
  bookId: string,
  title: string,
  authors: string[],
  isbn?: string
): UseBookCoverReturn => {
  const [coverUrl, setCoverUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFallback, setIsFallback] = useState(false);

  const { getCoverImage } = useVisualAssets();

  const loadCover = useCallback(async () => {
    if (!bookId || !title) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await getCoverImage({
        book_id: bookId,
        title,
        authors,
        isbn,
        preferred_size: 'medium'
      });

      if (response.success && response.local_path) {
        // Convert local path to a data URL or file:// URL for display
        // Tauri can serve local files, but we need to convert the path
        const fileUrl = `file://${response.local_path}`;
        setCoverUrl(fileUrl);
        setIsFallback(response.fallback_used);
      } else {
        setError(response.error || 'Failed to load cover image');
        setCoverUrl(null);
        setIsFallback(false);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load cover';
      setError(errorMessage);
      setCoverUrl(null);
      setIsFallback(false);
    } finally {
      setIsLoading(false);
    }
  }, [bookId, title, authors, isbn, getCoverImage]);

  const refreshCover = useCallback(() => {
    loadCover();
  }, [loadCover]);

  useEffect(() => {
    loadCover();
  }, [loadCover]);

  return {
    coverUrl,
    isLoading,
    error,
    isFallback,
    refreshCover
  };
};

// Utility function to create a placeholder cover image data URL
export const createPlaceholderCover = (title: string, authors: string[] = []): string => {
  const canvas = document.createElement('canvas');
  canvas.width = 400;
  canvas.height = 600;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';

  // Create gradient background
  const gradient = ctx.createLinearGradient(0, 0, 400, 600);
  gradient.addColorStop(0, '#4f46e5');
  gradient.addColorStop(1, '#7c3aed');
  
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 400, 600);

  // Add border
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.lineWidth = 2;
  ctx.strokeRect(20, 20, 360, 560);

  // Add title
  ctx.fillStyle = 'white';
  ctx.font = 'bold 24px Georgia, serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  // Word wrap title
  const maxWidth = 320;
  const words = title.split(' ');
  let lines = [];
  let currentLine = words[0];

  for (let i = 1; i < words.length; i++) {
    const word = words[i];
    const width = ctx.measureText(currentLine + ' ' + word).width;
    if (width < maxWidth) {
      currentLine += ' ' + word;
    } else {
      lines.push(currentLine);
      currentLine = word;
    }
  }
  lines.push(currentLine);

  // Draw title lines
  const startY = 250 - (lines.length * 15);
  lines.forEach((line, index) => {
    ctx.fillText(line, 200, startY + (index * 30));
  });

  // Add author
  if (authors.length > 0) {
    ctx.font = '18px Arial, sans-serif';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillText(authors.join(', '), 200, 480);
  }

  // Add branding
  ctx.font = '12px Arial, sans-serif';
  ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
  ctx.fillText('Generated by Lexicon', 200, 550);

  return canvas.toDataURL('image/png');
};
