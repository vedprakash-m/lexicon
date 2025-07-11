import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface BookMetadata {
  id: string;
  title: string;
  subtitle?: string;
  authors: Array<{
    name: string;
    role?: string;
    photo?: string;
  }>;
  publisher?: {
    name: string;
    logo?: string;
  };
  publication_year: number;
  language: string;
  original_language?: string;
  pages?: number;
  isbn?: string;
  categories: string[];
  subjects: string[];
  description: string;
  cover_image?: string;
  rating?: number;
  quality_score?: number;
  translations?: string[];
  related_books?: string[];
  series?: string;
  series_number?: number;
  enrichment_sources?: string[];
  relationships?: Array<{
    type: string;
    book_id: string;
    confidence: number;
  }>;
}

export interface CatalogFilters {
  category?: string;
  author?: string;
  language?: string;
  yearRange?: [number, number];
  hasTranslations?: boolean;
  hasCover?: boolean;
  minQuality?: number;
  minRating?: number;
}

export interface CatalogSearchParams {
  query?: string;
  filters?: CatalogFilters;
  sortBy?: 'title' | 'author' | 'year' | 'rating' | 'quality';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface CatalogStats {
  totalBooks: number;
  totalAuthors: number;
  categoriesCount: number;
  languagesCount: number;
  averageQuality: number;
  booksWithCovers: number;
  booksWithTranslations: number;
  recentlyAdded: number;
}

export interface EnrichmentResult {
  bookId: string;
  success: boolean;
  addedFields: string[];
  errors?: string[];
}

export interface UseCatalogManagerReturn {
  books: BookMetadata[];
  stats: CatalogStats | null;
  isLoading: boolean;
  error: string | null;
  searchBooks: (params: CatalogSearchParams) => Promise<BookMetadata[]>;
  getBookById: (id: string) => Promise<BookMetadata | null>;
  enrichBook: (bookId: string, sources?: string[]) => Promise<EnrichmentResult>;
  exportCatalog: (format: string, books?: string[]) => Promise<string>;
  getRelatedBooks: (bookId: string) => Promise<BookMetadata[]>;
  refreshCatalog: () => Promise<void>;
  generateCatalogReport: () => Promise<string>;
}

export const useCatalogManager = (): UseCatalogManagerReturn => {
  const [books, setBooks] = useState<BookMetadata[]>([]);
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchBooks = useCallback(async (params: CatalogSearchParams): Promise<BookMetadata[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await invoke<BookMetadata[]>('search_catalog', {
        query: params.query || '',
        filters: params.filters || {},
        sortBy: params.sortBy || 'title',
        sortOrder: params.sortOrder || 'asc',
        page: params.page || 1,
        limit: params.limit || 50
      });
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to search catalog';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getBookById = useCallback(async (id: string): Promise<BookMetadata | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await invoke<BookMetadata>('get_book_by_id', { bookId: id });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get book';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const enrichBook = useCallback(async (bookId: string, sources?: string[]): Promise<EnrichmentResult> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await invoke<EnrichmentResult>('enrich_book_metadata', {
        bookId,
        sources: sources || ['google_books', 'openlibrary']
      });
      
      // Refresh the book data after enrichment
      await refreshCatalog();
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to enrich book';
      setError(errorMessage);
      return {
        bookId,
        success: false,
        addedFields: [],
        errors: [errorMessage]
      };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const exportCatalog = useCallback(async (format: string, bookIds?: string[]): Promise<string> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await invoke<string>('export_catalog', {
        format,
        bookIds: bookIds || []
      });
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export catalog';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getRelatedBooks = useCallback(async (bookId: string): Promise<BookMetadata[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await invoke<BookMetadata[]>('get_related_books', { bookId });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get related books';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshCatalog = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load all books
      const allBooks = await invoke<BookMetadata[]>('get_all_books');
      setBooks(allBooks);
      
      // Load catalog statistics
      const catalogStats = await invoke<CatalogStats>('get_catalog_stats');
      setStats(catalogStats);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh catalog';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const generateCatalogReport = useCallback(async (): Promise<string> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await invoke<string>('generate_catalog_report');
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate catalog report';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load initial catalog data
  useEffect(() => {
    refreshCatalog();
  }, [refreshCatalog]);

  return {
    books,
    stats,
    isLoading,
    error,
    searchBooks,
    getBookById,
    enrichBook,
    exportCatalog,
    getRelatedBooks,
    refreshCatalog,
    generateCatalogReport
  };
};
