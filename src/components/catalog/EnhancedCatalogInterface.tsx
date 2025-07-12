import React, { useState, useEffect, useMemo } from 'react';
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
  Info
} from 'lucide-react';

// Enhanced catalog interface with rich metadata display
const EnhancedCatalogInterface = () => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    author: '',
    language: '',
    yearRange: [1000, 2025],
    hasTranslations: false,
    hasCover: false
  });
  const [sortBy, setSortBy] = useState('title');
  const [selectedBook, setSelectedBook] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Empty books array for new installation
  const mockBooks = [];

  useEffect(() => {
    // Return empty result for new installation
    setBooks([]);
    setLoading(false);
  }, []);

  // Filter and search logic
  const filteredBooks = useMemo(() => {
    let result = books;

    // Search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(book => 
        book.title.toLowerCase().includes(query) ||
        book.subtitle?.toLowerCase().includes(query) ||
        book.authors?.some(author => author.name.toLowerCase().includes(query)) ||
        book.description?.toLowerCase().includes(query) ||
        book.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Category filter
    if (filters.category) {
      result = result.filter(book => 
        book.categories.includes(filters.category)
      );
    }

    // Author filter
    if (filters.author) {
      result = result.filter(book => 
        book.authors?.some(author => 
          author.name.toLowerCase().includes(filters.author.toLowerCase())
        )
      );
    }

    // Language filter
    if (filters.language) {
      result = result.filter(book => book.language === filters.language);
    }

    // Year range filter
    result = result.filter(book => 
      book.publication_year >= filters.yearRange[0] && 
      book.publication_year <= filters.yearRange[1]
    );

    // Has translations filter
    if (filters.hasTranslations) {
      result = result.filter(book => book.translations && book.translations.length > 0);
    }

    // Has cover filter
    if (filters.hasCover) {
      result = result.filter(book => book.cover_image);
    }

    // Sort
    result.sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'author':
          return (a.authors?.[0]?.name || '').localeCompare(b.authors?.[0]?.name || '');
        case 'year':
          return (b.publication_year || 0) - (a.publication_year || 0);
        case 'rating':
          return (b.rating || 0) - (a.rating || 0);
        case 'popularity':
          return (b.downloads || 0) - (a.downloads || 0);
        default:
          return 0;
      }
    });

    return result;
  }, [books, searchQuery, filters, sortBy]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (books.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto max-w-md">
          <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No books found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filters
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="border-b border-gray-200 pb-5 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Enhanced Book Catalog</h1>
            <p className="mt-1 text-sm text-gray-500">
              {filteredBooks.length} {filteredBooks.length === 1 ? 'book' : 'books'} found
            </p>
          </div>
          
          {/* View Toggle */}
          <div className="flex items-center space-x-2">
            <div className="bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded ${viewMode === 'grid' ? 'bg-white shadow' : ''}`}
              >
                <Grid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-white shadow' : ''}`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search books, authors, subjects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap gap-4 items-center">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Filter className="h-4 w-4" />
            <span>Filters</span>
            <ChevronDown className={`h-4 w-4 transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="title">Sort by Title</option>
            <option value="author">Sort by Author</option>
            <option value="year">Sort by Year</option>
            <option value="rating">Sort by Rating</option>
            <option value="popularity">Sort by Popularity</option>
          </select>
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="bg-gray-50 p-4 rounded-lg space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-1.5 border border-gray-300 rounded-lg"
                >
                  <option value="">All Categories</option>
                  <option value="Philosophy">Philosophy</option>
                  <option value="Religion">Religion</option>
                  <option value="Spirituality">Spirituality</option>
                  <option value="Literature">Literature</option>
                </select>
              </div>

              {/* Language Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language
                </label>
                <select
                  value={filters.language}
                  onChange={(e) => setFilters(prev => ({ ...prev, language: e.target.value }))}
                  className="w-full px-3 py-1.5 border border-gray-300 rounded-lg"
                >
                  <option value="">All Languages</option>
                  <option value="English">English</option>
                  <option value="Sanskrit">Sanskrit</option>
                  <option value="Hindi">Hindi</option>
                </select>
              </div>

              {/* Author Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Author
                </label>
                <input
                  type="text"
                  placeholder="Filter by author..."
                  value={filters.author}
                  onChange={(e) => setFilters(prev => ({ ...prev, author: e.target.value }))}
                  className="w-full px-3 py-1.5 border border-gray-300 rounded-lg"
                />
              </div>
            </div>

            {/* Boolean Filters */}
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.hasTranslations}
                  onChange={(e) => setFilters(prev => ({ ...prev, hasTranslations: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Has Translations</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.hasCover}
                  onChange={(e) => setFilters(prev => ({ ...prev, hasCover: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Has Cover Image</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Results Display */}
      <div className="text-center py-12">
        <div className="mx-auto max-w-md">
          <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No books available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Add books to your collection to see them here
          </p>
        </div>
      </div>
    </div>
  );
};

export default EnhancedCatalogInterface;
