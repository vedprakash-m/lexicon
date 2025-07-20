import React, { useState, useEffect, useMemo } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  Star, 
  BookOpen, 
  User, 
  Calendar, 
  Tag, 
  Globe,
  Heart,
  Eye,
  ChevronDown,
  ChevronRight,
  Info,
  Download,
  RefreshCw,
  Sparkles,
  FileText,
  Plus,
  Trash2
} from 'lucide-react';
import { useCatalogManager, BookMetadata, CatalogFilters } from '../../hooks/useCatalogManager';
import { Button } from '../ui';
import { cn } from '../../lib/utils';
import { FileUploadDialog } from './FileUploadDialog';
import { useToast, useToastActions } from '../ui/toast';
import BookCover from '../BookCover';

// Integrated Enhanced Catalog Interface with backend integration
const IntegratedCatalogInterface = () => {
  const { addToast } = useToast();
  const toast = useToastActions();
  
  const { 
    books: allBooks, 
    stats, 
    isLoading: catalogLoading, 
    error: catalogError,
    searchBooks,
    enrichBook,
    exportCatalog,
    getRelatedBooks,
    refreshCatalog,
    generateCatalogReport,
    deleteBook
  } = useCatalogManager();

  const [books, setBooks] = useState<BookMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<CatalogFilters>({
    yearRange: [1000, 2025],
    hasTranslations: false,
    hasCover: false
  });
  const [sortBy, setSortBy] = useState<'title' | 'author' | 'year' | 'rating' | 'quality'>('title');
  const [selectedBook, setSelectedBook] = useState<BookMetadata | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [enriching, setEnriching] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [deleting, setDeleting] = useState<Set<string>>(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<BookMetadata | null>(null);

  // Update books when catalog data changes
  useEffect(() => {
    if (allBooks.length > 0) {
      setBooks(allBooks);
      setLoading(false);
    }
  }, [allBooks]);

  // Handle search and filtering
  useEffect(() => {
    const performSearch = async () => {
      if (catalogLoading) return;
      
      // For now, just use local filtering to avoid continuous API calls
      if (!searchQuery.trim() && Object.keys(filters).length === 0) {
        setBooks(allBooks);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        // Simple local filtering for now
        let results = allBooks;
        
        if (searchQuery.trim()) {
          const query = searchQuery.toLowerCase();
          results = results.filter(book => 
            book.title.toLowerCase().includes(query) ||
            book.authors.some(author => author.name.toLowerCase().includes(query))
          );
        }
        
        setBooks(results);
      } catch (err) {
        console.error('Search failed:', err);
        setBooks(allBooks);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(performSearch, 500);
    return () => clearTimeout(debounceTimer);
  }, [searchQuery, allBooks, catalogLoading]);

  // Global event listener for file upload
  useEffect(() => {
    const handleOpenFileUpload = () => setShowUploadDialog(true);
    
    window.addEventListener('lexicon:open-file-upload', handleOpenFileUpload);
    
    return () => {
      window.removeEventListener('lexicon:open-file-upload', handleOpenFileUpload);
    };
  }, []);

  // Get unique values for filter options
  const filterOptions = useMemo(() => {
    const categories = new Set<string>();
    const authors = new Set<string>();
    const languages = new Set<string>();

    allBooks.forEach(book => {
      book.categories.forEach(cat => categories.add(cat));
      book.authors.forEach(author => authors.add(author.name));
      languages.add(book.language);
    });

    return {
      categories: Array.from(categories).sort(),
      authors: Array.from(authors).sort(),
      languages: Array.from(languages).sort()
    };
  }, [allBooks]);

  const handleEnrichBook = async (bookId: string) => {
    setEnriching(prev => new Set(prev).add(bookId));
    try {
      const result = await enrichBook(bookId);
      if (result.success) {
        // Refresh the specific book data
        await refreshCatalog();
      }
    } catch (err) {
      console.error('Enrichment failed:', err);
    } finally {
      setEnriching(prev => {
        const next = new Set(prev);
        next.delete(bookId);
        return next;
      });
    }
  };

    const handleExportCatalog = async (format: string) => {
    setExporting(true);
    try {
      const result = await exportCatalog(format);
      // Trigger download
      const blob = new Blob([result], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `catalog.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success('Export Complete', 'Catalog exported successfully');
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Export Failed', `Export failed: ${err}`);
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteBook = async (book: BookMetadata) => {
    setDeleting(prev => new Set(prev).add(book.id));
    try {
      const result = await deleteBook(book.id);
      if (result.success) {
        toast.success('Book Deleted', `Successfully deleted "${book.title}"`);
        setShowDeleteConfirm(null);
      } else {
        toast.error('Delete Failed', `Failed to delete book: ${result.message}`);
      }
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Delete Failed', `Delete failed: ${err}`);
    } finally {
      setDeleting(prev => {
        const next = new Set(prev);
        next.delete(book.id);
        return next;
      });
    }
  };

  // Enhanced file upload handler with retry mechanism and better error handling  
  const handleFileUpload = async (files: File[], retryAttempt = 0) => {
    const maxRetries = 2;
    const isRetry = retryAttempt > 0;
    
    console.log(`${isRetry ? 'Retrying' : 'Starting'} upload of ${files.length} file(s)${isRetry ? ` (attempt ${retryAttempt + 1}/${maxRetries + 1})` : ''}`);
    
    if (!isRetry) {
      setLoading(true);
    }
    
    try {
      // Convert File objects to base64 and save them using Tauri's file system
      const uploadPromises = files.map(async (file) => {
        // Read file as ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        
        // Convert to base64 for Tauri transfer
        const base64Data = btoa(String.fromCharCode(...uint8Array));
        
        // Create a file path for the uploaded file
        const fileName = file.name;
        const filePath = `uploads/${fileName}`;
        
        // Save the file using Tauri's write_file command
        await invoke('write_file', {
          request: {
            path: filePath,
            data: base64Data,
            is_binary: true,
          }
        });
        
        // Now create the source text entry
        return invoke('upload_book_from_file', {
          uploadRequest: {
            file_name: fileName,
            file_path: filePath,
            file_size: file.size,
            title: null, // Will be extracted from filename
            author: null, // Can be filled later
          }
        });
      });
      
      const results = await Promise.all(uploadPromises);
      const successCount = results.filter((result: any) => result.success).length;
      const failedCount = files.length - successCount;
      
      if (successCount > 0) {
        // Refresh the catalog to show new books
        await refreshCatalog();
        
        if (failedCount > 0) {
          toast.warning(
            'Partial Upload Success',
            `${successCount} of ${files.length} books uploaded successfully. ${failedCount} failed.`
          );
        } else {
          toast.success(
            'Upload Complete',
            `Successfully added ${successCount} book${successCount > 1 ? 's' : ''} to your catalog!`
          );
        }
      } else {
        // All uploads failed - offer retry if not already retrying at max attempts
        if (retryAttempt < maxRetries) {
          addToast({
            title: 'Upload Failed',
            description: 'Failed to upload books. Click Retry to try again.',
            type: 'error',
            action: {
              label: 'Retry Upload',
              onClick: () => handleFileUpload(files, retryAttempt + 1)
            }
          });
        } else {
          toast.error(
            'Upload Failed',
            'Failed to add books after multiple attempts. Please check the console for details.'
          );
          console.error('Upload results after retries:', results);
        }
      }
      
    } catch (error) {
      console.error(`Upload failed${isRetry ? ` on retry ${retryAttempt + 1}` : ''}:`, error);
      
      if (retryAttempt < maxRetries) {
        addToast({
          title: 'Upload Error',
          description: `Upload failed: ${error}. Click Retry to try again.`,
          type: 'error',
          action: {
            label: 'Retry Upload',
            onClick: () => handleFileUpload(files, retryAttempt + 1)
          }
        });
      } else {
        toast.error(
          'Upload Error',
          `Failed to upload books after multiple attempts: ${error}`
        );
      }
    } finally {
      if (!isRetry) {
        setLoading(false);
      }
    }
  };

  const BookCard = ({ book }: { book: BookMetadata }) => (
    <div 
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 cursor-pointer overflow-hidden group"
      onClick={() => setSelectedBook(book)}
    >
      {/* Cover Image */}
      <div className="relative h-64 bg-gray-200 overflow-hidden">
        <BookCover
          bookId={book.id}
          title={book.title}
          authors={book.authors.map(a => a.name)}
          isbn={book.isbn}
          size="medium"
          className="w-full h-full"
          showRefreshButton={false}
          fallbackType="placeholder"
        />
        
        {/* Quality Badge */}
        {book.quality_score && (
          <div className="absolute top-2 right-2 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-semibold">
            {Math.round(book.quality_score * 100)}%
          </div>
        )}

        {/* Rating */}
        {book.rating && (
          <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded flex items-center text-xs">
            <Star size={12} className="mr-1 fill-current" />
            {book.rating}
          </div>
        )}

        {/* Action Buttons */}
        <div className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex space-x-1">
          <Button
            size="sm"
            variant="secondary"
            className="h-8 w-8 p-0"
            onClick={(e) => {
              e.stopPropagation();
              handleEnrichBook(book.id);
            }}
            disabled={enriching.has(book.id)}
          >
            {enriching.has(book.id) ? (
              <RefreshCw size={14} className="animate-spin" />
            ) : (
              <Sparkles size={14} />
            )}
          </Button>
          <Button
            size="sm"
            variant="destructive"
            className="h-8 w-8 p-0"
            onClick={(e) => {
              e.stopPropagation();
              setShowDeleteConfirm(book);
            }}
            disabled={deleting.has(book.id)}
          >
            {deleting.has(book.id) ? (
              <RefreshCw size={14} className="animate-spin" />
            ) : (
              <Trash2 size={14} />
            )}
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-bold text-lg mb-1 line-clamp-2">{book.title}</h3>
        {book.subtitle && (
          <p className="text-gray-600 text-sm mb-2 line-clamp-1">{book.subtitle}</p>
        )}
        
        <div className="flex items-center mb-2 text-sm text-gray-600">
          <User size={14} className="mr-1" />
          <span className="line-clamp-1">{book.authors[0]?.name}</span>
        </div>

        <div className="flex items-center mb-2 text-sm text-gray-600">
          <Calendar size={14} className="mr-1" />
          <span>{book.publication_year > 0 ? book.publication_year : `${Math.abs(book.publication_year)} BCE`}</span>
        </div>

        {/* Categories */}
        <div className="flex flex-wrap gap-1 mb-3">
          {book.categories.slice(0, 3).map((category, index) => (
            <span 
              key={index}
              className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs"
            >
              {category}
            </span>
          ))}
          {book.categories.length > 3 && (
            <span className="text-gray-500 text-xs">+{book.categories.length - 3} more</span>
          )}
        </div>

        {/* Language and Translations */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center">
            <Globe size={12} className="mr-1" />
            <span>{book.language}</span>
          </div>
          {book.translations && book.translations.length > 0 && (
            <span>{book.translations.length} translations</span>
          )}
        </div>

        {/* Relationships indicator */}
        {book.relationships && book.relationships.length > 0 && (
          <div className="mt-2 text-xs text-purple-600">
            <Heart size={12} className="inline mr-1" />
            {book.relationships.length} related books
          </div>
        )}
      </div>
    </div>
  );

  const BookListItem = ({ book }: { book: BookMetadata }) => (
    <div 
      className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-300 cursor-pointer p-4 flex group"
      onClick={() => setSelectedBook(book)}
    >
      {/* Cover Thumbnail */}
      <div className="w-16 h-20 bg-gray-200 rounded mr-4 flex-shrink-0 overflow-hidden">
        <BookCover
          bookId={book.id}
          title={book.title}
          authors={book.authors.map(a => a.name)}
          isbn={book.isbn}
          size="small"
          className="w-full h-full"
          showRefreshButton={false}
          fallbackType="icon"
        />
      </div>

      {/* Content */}
      <div className="flex-1">
        <div className="flex justify-between items-start mb-2">
          <div className="flex-1">
            <h3 className="font-bold text-lg">{book.title}</h3>
            {book.subtitle && (
              <p className="text-gray-600 text-sm">{book.subtitle}</p>
            )}
          </div>
          <div className="flex items-center space-x-2 ml-4">
            {book.rating && (
              <div className="flex items-center text-sm">
                <Star size={14} className="mr-1 fill-current text-yellow-400" />
                <span>{book.rating}</span>
              </div>
            )}
            {book.quality_score && (
              <div className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                {Math.round(book.quality_score * 100)}% quality
              </div>
            )}
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => {
                e.stopPropagation();
                handleEnrichBook(book.id);
              }}
              disabled={enriching.has(book.id)}
            >
              {enriching.has(book.id) ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <Sparkles size={14} />
              )}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-red-600 hover:text-red-700"
              onClick={(e) => {
                e.stopPropagation();
                setShowDeleteConfirm(book);
              }}
              disabled={deleting.has(book.id)}
            >
              {deleting.has(book.id) ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <Trash2 size={14} />
              )}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
          <div className="flex items-center">
            <User size={14} className="mr-1" />
            <span className="truncate">{book.authors[0]?.name}</span>
          </div>
          <div className="flex items-center">
            <Calendar size={14} className="mr-1" />
            <span>{book.publication_year > 0 ? book.publication_year : `${Math.abs(book.publication_year)} BCE`}</span>
          </div>
          <div className="flex items-center">
            <Globe size={14} className="mr-1" />
            <span>{book.language}</span>
          </div>
          {book.pages && (
            <div className="flex items-center">
              <BookOpen size={14} className="mr-1" />
              <span>{book.pages} pages</span>
            </div>
          )}
        </div>

        <p className="text-gray-700 text-sm mb-3 line-clamp-2">{book.description}</p>

        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-1">
            {book.categories.slice(0, 4).map((category, index) => (
              <span 
                key={index}
                className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs"
              >
                {category}
              </span>
            ))}
          </div>
          
          <div className="flex items-center space-x-4 text-xs text-gray-500">
            {book.translations && book.translations.length > 0 && (
              <span>{book.translations.length} translations</span>
            )}
            {book.relationships && book.relationships.length > 0 && (
              <span className="text-purple-600">
                <Heart size={12} className="inline mr-1" />
                {book.relationships.length} related
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const BookDetailModal = ({ book, onClose }: { book: BookMetadata; onClose: () => void }) => {
    if (!book) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
              <h2 className="text-2xl font-bold">{book.title}</h2>
              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEnrichBook(book.id)}
                  disabled={enriching.has(book.id)}
                >
                  {enriching.has(book.id) ? (
                    <RefreshCw size={16} className="animate-spin mr-2" />
                  ) : (
                    <Sparkles size={16} className="mr-2" />
                  )}
                  Enrich
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => setShowDeleteConfirm(book)}
                  disabled={deleting.has(book.id)}
                >
                  {deleting.has(book.id) ? (
                    <RefreshCw size={16} className="animate-spin mr-2" />
                  ) : (
                    <Trash2 size={16} className="mr-2" />
                  )}
                  Delete
                </Button>
                <button 
                  onClick={onClose}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Cover and basic info */}
              <div>
                <div className="w-full h-80 bg-gray-200 rounded mb-4 overflow-hidden">
                  <BookCover
                    bookId={book.id}
                    title={book.title}
                    authors={book.authors.map(a => a.name)}
                    isbn={book.isbn}
                    size="large"
                    className="w-full h-full"
                    showRefreshButton={true}
                    fallbackType="placeholder"
                  />
                </div>

                {/* Metrics */}
                <div className="space-y-2">
                  {book.rating && (
                    <div className="flex items-center justify-between">
                      <span>Rating:</span>
                      <div className="flex items-center">
                        <Star size={16} className="mr-1 fill-current text-yellow-400" />
                        <span>{book.rating}</span>
                      </div>
                    </div>
                  )}
                  {book.quality_score && (
                    <div className="flex items-center justify-between">
                      <span>Quality Score:</span>
                      <span className="font-semibold">{Math.round(book.quality_score * 100)}%</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Details - same as original component but with real data */}
              <div className="md:col-span-2">
                {/* Rest of the detail modal content - same as original */}
                <div className="space-y-4">
                  {/* Authors */}
                  <div>
                    <h3 className="font-semibold mb-2">Authors</h3>
                    {book.authors.map((author, index) => (
                      <div key={index} className="flex items-center mb-2">
                        {author.photo && (
                          <img 
                            src={author.photo} 
                            alt={author.name}
                            className="w-8 h-8 rounded-full mr-2"
                          />
                        )}
                        <div>
                          <div className="font-medium">{author.name}</div>
                          {author.role && (
                            <div className="text-sm text-gray-600">{author.role}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Publication details */}
                  <div>
                    <h3 className="font-semibold mb-2">Publication Details</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Year:</span> {book.publication_year > 0 ? book.publication_year : `${Math.abs(book.publication_year)} BCE`}
                      </div>
                      <div>
                        <span className="text-gray-600">Language:</span> {book.language}
                      </div>
                      {book.pages && (
                        <div>
                          <span className="text-gray-600">Pages:</span> {book.pages}
                        </div>
                      )}
                      {book.isbn && (
                        <div>
                          <span className="text-gray-600">ISBN:</span> {book.isbn}
                        </div>
                      )}
                      {book.publisher && (
                        <div className="col-span-2">
                          <span className="text-gray-600">Publisher:</span> {book.publisher.name}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <h3 className="font-semibold mb-2">Description</h3>
                    <p className="text-gray-700">{book.description}</p>
                  </div>

                  {/* Categories and Subjects */}
                  <div>
                    <h3 className="font-semibold mb-2">Categories & Subjects</h3>
                    <div className="mb-2">
                      <span className="text-sm text-gray-600">Categories:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {book.categories.map((category, index) => (
                          <span 
                            key={index}
                            className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs"
                          >
                            {category}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Subjects:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {book.subjects.map((subject, index) => (
                          <span 
                            key={index}
                            className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs"
                          >
                            {subject}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Translations */}
                  {book.translations && book.translations.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2">Available Translations</h3>
                      <div className="flex flex-wrap gap-1">
                        {book.translations.map((translation, index) => (
                          <span 
                            key={index}
                            className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs"
                          >
                            {translation}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Relationships */}
                  {book.relationships && book.relationships.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2">Related Books</h3>
                      <div className="space-y-2">
                        {book.relationships.map((rel, index) => {
                          const relatedBook = allBooks.find(b => b.id === rel.book_id);
                          return (
                            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                              <div>
                                <div className="font-medium">{relatedBook?.title || 'Unknown Book'}</div>
                                <div className="text-sm text-gray-600 capitalize">
                                  {rel.type.replace('_', ' ')} • {Math.round(rel.confidence * 100)}% confidence
                                </div>
                              </div>
                              <button 
                                className="text-blue-600 hover:text-blue-800 text-sm"
                                onClick={() => {
                                  if (relatedBook) {
                                    setSelectedBook(relatedBook);
                                  }
                                }}
                              >
                                View →
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Enrichment Sources */}
                  {book.enrichment_sources && (
                    <div>
                      <h3 className="font-semibold mb-2">Data Sources</h3>
                      <div className="flex gap-2">
                        {book.enrichment_sources.map((source, index) => (
                          <span 
                            key={index}
                            className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs"
                          >
                            {source.replace('_', ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (catalogLoading && !allBooks.length) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="space-y-4">
                <div className="h-64 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <BookOpen className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Enhanced Book Catalog</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => setShowUploadDialog(true)}
                className="bg-primary hover:bg-primary/90"
              >
                <Plus size={16} className="mr-2" />
                Add Books
              </Button>
              {stats && (
                <div className="text-sm text-gray-600">
                  {books.length} of {stats.totalBooks} books
                </div>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleExportCatalog('json')}
                disabled={exporting}
              >
                {exporting ? (
                  <RefreshCw size={16} className="animate-spin mr-2" />
                ) : (
                  <Download size={16} className="mr-2" />
                )}
                Export
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={refreshCatalog}
                disabled={catalogLoading}
              >
                {catalogLoading ? (
                  <RefreshCw size={16} className="animate-spin mr-2" />
                ) : (
                  <RefreshCw size={16} className="mr-2" />
                )}
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {catalogError && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">
              <strong>Error:</strong> {catalogError}
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search and Controls */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Search books, authors, subjects..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  "p-2 rounded",
                  viewMode === 'grid' ? 'bg-white shadow-sm' : ''
                )}
              >
                <Grid size={20} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  "p-2 rounded",
                  viewMode === 'list' ? 'bg-white shadow-sm' : ''
                )}
              >
                <List size={20} />
              </button>
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="title">Sort by Title</option>
              <option value="author">Sort by Author</option>
              <option value="year">Sort by Year</option>
              <option value="rating">Sort by Rating</option>
              <option value="quality">Sort by Quality</option>
            </select>

            {/* Filters Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Filter size={20} className="mr-2" />
              Filters
              {showFilters ? <ChevronDown size={16} className="ml-2" /> : <ChevronRight size={16} className="ml-2" />}
            </button>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Category Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    value={filters.category || ''}
                    onChange={(e) => setFilters({...filters, category: e.target.value || undefined})}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Categories</option>
                    {filterOptions.categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>

                {/* Author Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Author</label>
                  <input
                    type="text"
                    placeholder="Filter by author"
                    value={filters.author || ''}
                    onChange={(e) => setFilters({...filters, author: e.target.value || undefined})}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Language Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                  <select
                    value={filters.language || ''}
                    onChange={(e) => setFilters({...filters, language: e.target.value || undefined})}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Languages</option>
                    {filterOptions.languages.map(language => (
                      <option key={language} value={language}>{language}</option>
                    ))}
                  </select>
                </div>

                {/* Special Filters */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Special Filters</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.hasTranslations || false}
                        onChange={(e) => setFilters({...filters, hasTranslations: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-sm">Has Translations</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.hasCover || false}
                        onChange={(e) => setFilters({...filters, hasCover: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-sm">Has Cover Image</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <RefreshCw size={48} className="mx-auto text-gray-400 mb-4 animate-spin" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Loading books...</h3>
          </div>
        )}

        {/* Results */}
        {!loading && books.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen size={48} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No books found</h3>
            <p className="text-gray-600">Try adjusting your search or filters</p>
          </div>
        ) : !loading && (
          <div className={
            viewMode === 'grid' 
              ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
              : "space-y-4"
          }>
            {books.map(book => (
              <div key={book.id}>
                {viewMode === 'grid' ? (
                  <BookCard book={book} />
                ) : (
                  <BookListItem book={book} />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Book Detail Modal */}
        {selectedBook && (
          <BookDetailModal 
            book={selectedBook} 
            onClose={() => setSelectedBook(null)} 
          />
        )}

        {/* File Upload Dialog */}
        <FileUploadDialog
          isOpen={showUploadDialog}
          onClose={() => setShowUploadDialog(false)}
          onUpload={handleFileUpload}
        />

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Book</h3>
                <p className="text-gray-600">
                  Are you sure you want to delete "{showDeleteConfirm.title}"? This action cannot be undone and will remove all associated files.
                </p>
              </div>
              <div className="flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowDeleteConfirm(null)}
                  disabled={deleting.has(showDeleteConfirm.id)}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleDeleteBook(showDeleteConfirm)}
                  disabled={deleting.has(showDeleteConfirm.id)}
                >
                  {deleting.has(showDeleteConfirm.id) ? (
                    <>
                      <RefreshCw size={16} className="animate-spin mr-2" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 size={16} className="mr-2" />
                      Delete
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegratedCatalogInterface;
