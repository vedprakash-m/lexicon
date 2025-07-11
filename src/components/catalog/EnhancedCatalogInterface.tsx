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
  const [loading, setLoading] = useState(true);
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

  // Mock data - in real app, this would come from the backend
  const mockBooks = [
    {
      id: 'bhagavad_gita_en',
      title: 'Bhagavad Gita As It Is',
      subtitle: 'With Original Sanskrit Text',
      authors: [
        {
          name: 'A.C. Bhaktivedanta Swami Prabhupada',
          role: 'Author & Translator',
          photo: '/api/assets/author_bhaktivedanta_photo.jpg'
        }
      ],
      publisher: {
        name: 'The Bhaktivedanta Book Trust',
        logo: '/api/assets/publisher_bbt_logo.jpg'
      },
      publication_year: 1972,
      language: 'English',
      original_language: 'Sanskrit',
      pages: 944,
      isbn: '978-0-89213-268-3',
      categories: ['Philosophy', 'Religion', 'Spirituality'],
      subjects: ['Hindu Philosophy', 'Yoga', 'Meditation', 'Bhakti'],
      description: 'The largest-selling edition of the Gita in the Western world, Bhagavad-gita As It Is is more than a book. It is alive with knowledge and devotion; thus it has the power to change your life.',
      cover_image: '/api/assets/bhagavad_gita_cover.jpg',
      rating: 4.8,
      quality_score: 0.92,
      translations: ['Spanish', 'French', 'German', 'Italian'],
      related_books: ['srimad_bhagavatam_1', 'sri_isopanisad'],
      series: null,
      enrichment_sources: ['google_books', 'openlibrary'],
      relationships: [
        { type: 'translation', book_id: 'bhagavad_gita_es', confidence: 1.0 },
        { type: 'same_author', book_id: 'srimad_bhagavatam_1', confidence: 0.95 },
        { type: 'thematic_similarity', book_id: 'tao_te_ching', confidence: 0.72 }
      ]
    },
    {
      id: 'srimad_bhagavatam_1',
      title: 'Srimad Bhagavatam Canto 1',
      subtitle: 'Creation',
      authors: [
        {
          name: 'A.C. Bhaktivedanta Swami Prabhupada',
          role: 'Translator & Commentator',
          photo: '/api/assets/author_bhaktivedanta_photo.jpg'
        }
      ],
      publisher: {
        name: 'The Bhaktivedanta Book Trust',
        logo: '/api/assets/publisher_bbt_logo.jpg'
      },
      publication_year: 1974,
      language: 'English',
      original_language: 'Sanskrit',
      pages: 756,
      series: 'Srimad Bhagavatam',
      series_number: 1,
      categories: ['Philosophy', 'Religion', 'Spirituality', 'Literature'],
      subjects: ['Hindu Philosophy', 'Stories', 'Devotion', 'Bhakti', 'Vedic Literature'],
      description: 'First Canto of the great Vedic literature, containing the essence of all Vedic knowledge.',
      cover_image: '/api/assets/srimad_bhagavatam_1_cover.jpg',
      rating: 4.9,
      quality_score: 0.89,
      relationships: [
        { type: 'same_author', book_id: 'bhagavad_gita_en', confidence: 0.95 },
        { type: 'sequel', book_id: 'srimad_bhagavatam_2', confidence: 0.9 }
      ]
    },
    {
      id: 'thinking_fast_slow',
      title: 'Thinking, Fast and Slow',
      authors: [
        {
          name: 'Daniel Kahneman',
          role: 'Author',
          photo: '/api/assets/author_kahneman_photo.jpg'
        }
      ],
      publisher: {
        name: 'Farrar, Straus and Giroux',
        logo: '/api/assets/publisher_fsg_logo.jpg'
      },
      publication_year: 2011,
      language: 'English',
      pages: 511,
      isbn: '978-0-374-27563-1',
      categories: ['Psychology', 'Science', 'Behavioral Economics'],
      subjects: ['Cognitive Psychology', 'Decision Making', 'Behavioral Science'],
      description: 'A revolutionary book about how the mind makes decisions.',
      cover_image: '/api/assets/thinking_fast_slow_cover.jpg',
      rating: 4.6,
      quality_score: 0.94,
      translations: ['Spanish', 'French', 'German'],
      relationships: []
    },
    {
      id: 'art_of_war',
      title: 'The Art of War',
      authors: [
        {
          name: 'Sun Tzu',
          role: 'Author'
        }
      ],
      publication_year: -500, // BCE
      language: 'English',
      original_language: 'Chinese',
      pages: 273,
      categories: ['Strategy', 'Military', 'Philosophy'],
      subjects: ['War', 'Strategy', 'Leadership', 'Tactics'],
      description: 'Ancient Chinese military strategy and philosophy.',
      cover_image: '/api/assets/art_of_war_cover.jpg',
      rating: 4.5,
      quality_score: 0.78,
      translations: ['Spanish', 'French', 'German', 'Italian', 'Japanese'],
      relationships: []
    }
  ];

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      setBooks(mockBooks);
      setLoading(false);
    }, 1000);
  }, []);

  // Filter and search logic
  const filteredBooks = useMemo(() => {
    let result = books;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(book => 
        book.title.toLowerCase().includes(query) ||
        book.authors.some(author => author.name.toLowerCase().includes(query)) ||
        book.description.toLowerCase().includes(query) ||
        book.subjects.some(subject => subject.toLowerCase().includes(query))
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
        book.authors.some(author => 
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
          return a.authors[0]?.name.localeCompare(b.authors[0]?.name) || 0;
        case 'year':
          return b.publication_year - a.publication_year;
        case 'rating':
          return (b.rating || 0) - (a.rating || 0);
        case 'quality':
          return (b.quality_score || 0) - (a.quality_score || 0);
        default:
          return 0;
      }
    });

    return result;
  }, [books, searchQuery, filters, sortBy]);

  // Get unique values for filter options
  const filterOptions = useMemo(() => {
    const categories = new Set();
    const authors = new Set();
    const languages = new Set();

    books.forEach(book => {
      book.categories.forEach(cat => categories.add(cat));
      book.authors.forEach(author => authors.add(author.name));
      languages.add(book.language);
    });

    return {
      categories: Array.from(categories).sort(),
      authors: Array.from(authors).sort(),
      languages: Array.from(languages).sort()
    };
  }, [books]);

  const BookCard = ({ book }) => (
    <div 
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 cursor-pointer overflow-hidden"
      onClick={() => setSelectedBook(book)}
    >
      {/* Cover Image */}
      <div className="relative h-64 bg-gray-200 overflow-hidden">
        {book.cover_image ? (
          <img 
            src={book.cover_image} 
            alt={book.title}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              e.target.src = '/api/placeholder-cover.jpg';
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <BookOpen size={48} />
          </div>
        )}
        
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
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-bold text-lg mb-1 line-clamp-2">{book.title}</h3>
        {book.subtitle && (
          <p className="text-gray-600 text-sm mb-2">{book.subtitle}</p>
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

  const BookListItem = ({ book }) => (
    <div 
      className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-300 cursor-pointer p-4 flex"
      onClick={() => setSelectedBook(book)}
    >
      {/* Cover Thumbnail */}
      <div className="w-16 h-20 bg-gray-200 rounded mr-4 flex-shrink-0 overflow-hidden">
        {book.cover_image ? (
          <img 
            src={book.cover_image} 
            alt={book.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.src = '/api/placeholder-cover.jpg';
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <BookOpen size={20} />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1">
        <div className="flex justify-between items-start mb-2">
          <div>
            <h3 className="font-bold text-lg">{book.title}</h3>
            {book.subtitle && (
              <p className="text-gray-600 text-sm">{book.subtitle}</p>
            )}
          </div>
          <div className="flex items-center space-x-2">
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
          <div className="flex items-center">
            <BookOpen size={14} className="mr-1" />
            <span>{book.pages} pages</span>
          </div>
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

  const BookDetailModal = ({ book, onClose }) => {
    if (!book) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
              <h2 className="text-2xl font-bold">{book.title}</h2>
              <button 
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Cover and basic info */}
              <div>
                <div className="w-full h-80 bg-gray-200 rounded mb-4 overflow-hidden">
                  {book.cover_image ? (
                    <img 
                      src={book.cover_image} 
                      alt={book.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                      <BookOpen size={64} />
                    </div>
                  )}
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

              {/* Details */}
              <div className="md:col-span-2">
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
                          const relatedBook = books.find(b => b.id === rel.book_id);
                          return (
                            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                              <div>
                                <div className="font-medium">{relatedBook?.title || 'Unknown Book'}</div>
                                <div className="text-sm text-gray-600 capitalize">
                                  {rel.type.replace('_', ' ')} • {Math.round(rel.confidence * 100)}% confidence
                                </div>
                              </div>
                              <button className="text-blue-600 hover:text-blue-800 text-sm">
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

  if (loading) {
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
              <div className="text-sm text-gray-600">
                {filteredBooks.length} of {books.length} books
              </div>
            </div>
          </div>
        </div>
      </div>

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
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white shadow-sm' : ''}`}
              >
                <Grid size={20} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-white shadow-sm' : ''}`}
              >
                <List size={20} />
              </button>
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
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
                    value={filters.category}
                    onChange={(e) => setFilters({...filters, category: e.target.value})}
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
                    value={filters.author}
                    onChange={(e) => setFilters({...filters, author: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Language Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                  <select
                    value={filters.language}
                    onChange={(e) => setFilters({...filters, language: e.target.value})}
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
                        checked={filters.hasTranslations}
                        onChange={(e) => setFilters({...filters, hasTranslations: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-sm">Has Translations</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.hasCover}
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

        {/* Results */}
        {filteredBooks.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen size={48} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No books found</h3>
            <p className="text-gray-600">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className={
            viewMode === 'grid' 
              ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
              : "space-y-4"
          }>
            {filteredBooks.map(book => (
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
      </div>
    </div>
  );
};

export default EnhancedCatalogInterface;
