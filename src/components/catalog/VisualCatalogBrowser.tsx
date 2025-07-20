import React, { useState, useEffect, useMemo } from 'react';
import { Search, Grid, List, Filter, Sort, Eye, Edit, Download } from 'lucide-react';

interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl?: string;
  metadata: {
    publisher?: string;
    publishedDate?: string;
    pageCount?: number;
    categories?: string[];
    rating?: number;
    description?: string;
  };
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  chapterCount?: number;
  wordCount?: number;
  lastProcessed?: Date;
}

interface VisualCatalogBrowserProps {
  books: Book[];
  onBookSelect: (book: Book) => void;
  onBookEdit: (book: Book) => void;
  onBookProcess: (book: Book) => void;
  onBookExport: (book: Book) => void;
}

type ViewMode = 'grid' | 'list';
type SortField = 'title' | 'author' | 'publishedDate' | 'rating' | 'lastProcessed';
type SortOrder = 'asc' | 'desc';

export const VisualCatalogBrowser: React.FC<VisualCatalogBrowserProps> = ({
  books,
  onBookSelect,
  onBookEdit,
  onBookProcess,
  onBookExport,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('title');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [selectedBooks, setSelectedBooks] = useState<Set<string>>(new Set());

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set<string>();
    books.forEach(book => {
      book.metadata.categories?.forEach(cat => cats.add(cat));
    });
    return Array.from(cats).sort();
  }, [books]);

  // Filter and sort books
  const filteredAndSortedBooks = useMemo(() => {
    let filtered = books.filter(book => {
      // Search filter
      const matchesSearch = searchQuery === '' || 
        book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        book.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
        book.metadata.description?.toLowerCase().includes(searchQuery.toLowerCase());

      // Category filter
      const matchesCategory = selectedCategory === 'all' ||
        book.metadata.categories?.includes(selectedCategory);

      return matchesSearch && matchesCategory;
    });

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortField) {
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'author':
          aValue = a.author.toLowerCase();
          bValue = b.author.toLowerCase();
          break;
        case 'publishedDate':
          aValue = a.metadata.publishedDate || '';
          bValue = b.metadata.publishedDate || '';
          break;
        case 'rating':
          aValue = a.metadata.rating || 0;
          bValue = b.metadata.rating || 0;
          break;
        case 'lastProcessed':
          aValue = a.lastProcessed?.getTime() || 0;
          bValue = b.lastProcessed?.getTime() || 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [books, searchQuery, selectedCategory, sortField, sortOrder]);

  const handleBookClick = (book: Book) => {
    onBookSelect(book);
  };

  const handleBookSelection = (bookId: string, selected: boolean) => {
    const newSelection = new Set(selectedBooks);
    if (selected) {
      newSelection.add(bookId);
    } else {
      newSelection.delete(bookId);
    }
    setSelectedBooks(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedBooks.size === filteredAndSortedBooks.length) {
      setSelectedBooks(new Set());
    } else {
      setSelectedBooks(new Set(filteredAndSortedBooks.map(book => book.id)));
    }
  };

  const getStatusColor = (status: Book['processingStatus']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const BookCard: React.FC<{ book: Book }> = ({ book }) => (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden">
      <div className="relative">
        {book.coverUrl ? (
          <img
            src={book.coverUrl}
            alt={`Cover of ${book.title}`}
            className="w-full h-48 object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/placeholder-book-cover.png';
            }}
          />
        ) : (
          <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
            <span className="text-gray-500 text-sm">No Cover</span>
          </div>
        )}
        
        <div className="absolute top-2 right-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(book.processingStatus)}`}>
            {book.processingStatus}
          </span>
        </div>

        <div className="absolute top-2 left-2">
          <input
            type="checkbox"
            checked={selectedBooks.has(book.id)}
            onChange={(e) => handleBookSelection(book.id, e.target.checked)}
            className="rounded border-gray-300"
          />
        </div>
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-lg mb-1 line-clamp-2" title={book.title}>
          {book.title}
        </h3>
        <p className="text-gray-600 mb-2" title={book.author}>
          {book.author}
        </p>

        {book.metadata.rating && (
          <div className="flex items-center mb-2">
            <div className="flex text-yellow-400">
              {[...Array(5)].map((_, i) => (
                <span key={i} className={i < Math.floor(book.metadata.rating!) ? 'text-yellow-400' : 'text-gray-300'}>
                  ★
                </span>
              ))}
            </div>
            <span className="ml-1 text-sm text-gray-600">
              {book.metadata.rating.toFixed(1)}
            </span>
          </div>
        )}

        <div className="text-sm text-gray-500 mb-3">
          {book.metadata.publishedDate && (
            <div>Published: {book.metadata.publishedDate}</div>
          )}
          {book.metadata.pageCount && (
            <div>{book.metadata.pageCount} pages</div>
          )}
          {book.chapterCount && (
            <div>{book.chapterCount} chapters</div>
          )}
        </div>

        <div className="flex flex-wrap gap-1 mb-3">
          {book.metadata.categories?.slice(0, 3).map(category => (
            <span
              key={category}
              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
            >
              {category}
            </span>
          ))}
          {book.metadata.categories && book.metadata.categories.length > 3 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              +{book.metadata.categories.length - 3}
            </span>
          )}
        </div>

        <div className="flex justify-between items-center">
          <button
            onClick={() => handleBookClick(book)}
            className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
          >
            <Eye size={14} />
            View
          </button>
          
          <div className="flex gap-1">
            <button
              onClick={() => onBookEdit(book)}
              className="p-1 text-gray-600 hover:text-blue-600"
              title="Edit metadata"
            >
              <Edit size={16} />
            </button>
            <button
              onClick={() => onBookExport(book)}
              className="p-1 text-gray-600 hover:text-green-600"
              title="Export"
            >
              <Download size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const BookListItem: React.FC<{ book: Book }> = ({ book }) => (
    <div className="bg-white border-b border-gray-200 hover:bg-gray-50 transition-colors duration-150">
      <div className="flex items-center p-4 gap-4">
        <input
          type="checkbox"
          checked={selectedBooks.has(book.id)}
          onChange={(e) => handleBookSelection(book.id, e.target.checked)}
          className="rounded border-gray-300"
        />

        <div className="w-12 h-16 flex-shrink-0">
          {book.coverUrl ? (
            <img
              src={book.coverUrl}
              alt={`Cover of ${book.title}`}
              className="w-full h-full object-cover rounded"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder-book-cover.png';
              }}
            />
          ) : (
            <div className="w-full h-full bg-gray-200 rounded flex items-center justify-center">
              <span className="text-gray-500 text-xs">No Cover</span>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg mb-1 truncate" title={book.title}>
            {book.title}
          </h3>
          <p className="text-gray-600 mb-1" title={book.author}>
            {book.author}
          </p>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            {book.metadata.publishedDate && (
              <span>{book.metadata.publishedDate}</span>
            )}
            {book.metadata.pageCount && (
              <span>{book.metadata.pageCount} pages</span>
            )}
            {book.chapterCount && (
              <span>{book.chapterCount} chapters</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {book.metadata.rating && (
            <div className="flex items-center">
              <span className="text-yellow-400">★</span>
              <span className="ml-1 text-sm text-gray-600">
                {book.metadata.rating.toFixed(1)}
              </span>
            </div>
          )}

          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(book.processingStatus)}`}>
            {book.processingStatus}
          </span>

          <div className="flex gap-1">
            <button
              onClick={() => handleBookClick(book)}
              className="p-2 text-gray-600 hover:text-blue-600"
              title="View details"
            >
              <Eye size={16} />
            </button>
            <button
              onClick={() => onBookEdit(book)}
              className="p-2 text-gray-600 hover:text-blue-600"
              title="Edit metadata"
            >
              <Edit size={16} />
            </button>
            <button
              onClick={() => onBookExport(book)}
              className="p-2 text-gray-600 hover:text-green-600"
              title="Export"
            >
              <Download size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Library Catalog</h2>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <Grid size={20} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <List size={20} />
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search books, authors, descriptions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <select
            value={`${sortField}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortField(field as SortField);
              setSortOrder(order as SortOrder);
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="title-asc">Title A-Z</option>
            <option value="title-desc">Title Z-A</option>
            <option value="author-asc">Author A-Z</option>
            <option value="author-desc">Author Z-A</option>
            <option value="publishedDate-desc">Newest First</option>
            <option value="publishedDate-asc">Oldest First</option>
            <option value="rating-desc">Highest Rated</option>
            <option value="lastProcessed-desc">Recently Processed</option>
          </select>
        </div>

        {/* Selection Actions */}
        {selectedBooks.size > 0 && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg flex items-center justify-between">
            <span className="text-blue-800">
              {selectedBooks.size} book{selectedBooks.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  selectedBooks.forEach(bookId => {
                    const book = books.find(b => b.id === bookId);
                    if (book) onBookProcess(book);
                  });
                }}
                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              >
                Process Selected
              </button>
              <button
                onClick={() => {
                  selectedBooks.forEach(bookId => {
                    const book = books.find(b => b.id === bookId);
                    if (book) onBookExport(book);
                  });
                }}
                className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
              >
                Export Selected
              </button>
              <button
                onClick={() => setSelectedBooks(new Set())}
                className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
              >
                Clear Selection
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {filteredAndSortedBooks.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-gray-500 text-lg mb-2">No books found</p>
              <p className="text-gray-400">Try adjusting your search or filters</p>
            </div>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {filteredAndSortedBooks.map(book => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            <div className="bg-gray-50 p-4 flex items-center">
              <input
                type="checkbox"
                checked={selectedBooks.size === filteredAndSortedBooks.length && filteredAndSortedBooks.length > 0}
                onChange={handleSelectAll}
                className="rounded border-gray-300 mr-4"
              />
              <span className="text-sm font-medium text-gray-700">
                Select All ({filteredAndSortedBooks.length})
              </span>
            </div>
            {filteredAndSortedBooks.map(book => (
              <BookListItem key={book.id} book={book} />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Showing {filteredAndSortedBooks.length} of {books.length} books
          </span>
          {selectedBooks.size > 0 && (
            <span>
              {selectedBooks.size} selected
            </span>
          )}
        </div>
      </div>
    </div>
  );
};