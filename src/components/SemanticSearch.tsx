import React, { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Search, Filter, Settings, Clock, BarChart3, X, Tag, BookOpen, User, FileText, TrendingUp } from 'lucide-react';

interface SearchConfig {
  semantic_model: string;
  use_semantic_similarity: boolean;
  similarity_threshold: number;
  use_fuzzy_matching: boolean;
  fuzzy_threshold: number;
  max_results: number;
  boost_exact_matches: boolean;
  boost_title_matches: number;
  boost_author_matches: number;
  enable_cache: boolean;
}

interface SearchQuery {
  text: string;
  filters: Record<string, any>;
  facets: string[];
  sort_by: string;
  sort_order: string;
  limit: number;
  offset: number;
}

interface SearchResult {
  id: string;
  title: string;
  author: string;
  content: string;
  metadata: Record<string, any>;
  relevance_score: number;
  match_type: string;
  highlighted_fields: Record<string, string>;
}

interface SearchFacet {
  name: string;
  values: [string, number][];
}

interface SearchResponse {
  results: SearchResult[];
  total_count: number;
  facets: SearchFacet[];
  query_time_ms: number;
  suggestions: string[];
}

interface SemanticSearchProps {
  onResultSelect?: (result: SearchResult) => void;
  initialQuery?: string;
  showAdvancedOptions?: boolean;
}

const DEFAULT_CONFIG: SearchConfig = {
  semantic_model: "all-MiniLM-L6-v2",
  use_semantic_similarity: true,
  similarity_threshold: 0.7,
  use_fuzzy_matching: true,
  fuzzy_threshold: 0.8,
  max_results: 50,
  boost_exact_matches: true,
  boost_title_matches: 2.0,
  boost_author_matches: 1.5,
  enable_cache: true,
};

export const SemanticSearch: React.FC<SemanticSearchProps> = ({
  onResultSelect,
  initialQuery = "",
  showAdvancedOptions = false
}) => {
  // State
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [facets, setFacets] = useState<SearchFacet[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [queryTime, setQueryTime] = useState(0);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<Record<string, any>>({});
  const [activeFacets, setActiveFacets] = useState<string[]>(['category', 'author', 'subject']);
  const [sortBy, setSortBy] = useState('relevance');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [showSettings, setShowSettings] = useState(false);
  const [config, setConfig] = useState<SearchConfig>(DEFAULT_CONFIG);
  const [statistics, setStatistics] = useState<Record<string, any>>({});

  // Initialize search engine
  useEffect(() => {
    const initializeSearch = async () => {
      try {
        setIsLoading(true);
        await invoke('initialize_semantic_search', { config });
        setIsInitialized(true);
        await loadStatistics();
      } catch (error) {
        console.error('Failed to initialize semantic search:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (!isInitialized) {
      initializeSearch();
    }
  }, [config, isInitialized]);

  // Load statistics
  const loadStatistics = useCallback(async () => {
    try {
      const stats = await invoke<Record<string, any>>('get_search_statistics');
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load search statistics:', error);
    }
  }, []);

  // Perform search
  const performSearch = useCallback(async () => {
    if (!query.trim() || !isInitialized) return;

    try {
      setIsLoading(true);
      
      const searchQuery: SearchQuery = {
        text: query,
        filters: selectedFilters,
        facets: activeFacets,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
      };

      const response = await invoke<SearchResponse>('semantic_search', { query: searchQuery });
      
      setResults(response.results);
      setFacets(response.facets);
      setTotalCount(response.total_count);
      setQueryTime(response.query_time_ms);
      setSuggestions(response.suggestions);
      
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
      setFacets([]);
      setTotalCount(0);
    } finally {
      setIsLoading(false);
    }
  }, [query, selectedFilters, activeFacets, sortBy, sortOrder, currentPage, pageSize, isInitialized]);

  // Quick search function
  const quickSearch = useCallback(async (searchText: string, limit = 10) => {
    if (!searchText.trim() || !isInitialized) return;

    try {
      setIsLoading(true);
      const response = await invoke<SearchResponse>('quick_search', { 
        query_text: searchText, 
        limit 
      });
      
      setResults(response.results);
      setTotalCount(response.total_count);
      setQueryTime(response.query_time_ms);
      
    } catch (error) {
      console.error('Quick search failed:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [isInitialized]);

  // Handle filter changes
  const handleFilterChange = (filterKey: string, value: any) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filterKey]: value
    }));
    setCurrentPage(1); // Reset to first page
  };

  // Remove filter
  const removeFilter = (filterKey: string) => {
    setSelectedFilters(prev => {
      const newFilters = { ...prev };
      delete newFilters[filterKey];
      return newFilters;
    });
  };

  // Handle search input
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    performSearch();
  };

  // Handle result selection
  const handleResultClick = (result: SearchResult) => {
    if (onResultSelect) {
      onResultSelect(result);
    }
  };

  // Get match type badge color
  const getMatchTypeBadgeColor = (matchType: string) => {
    switch (matchType.toLowerCase()) {
      case 'exact':
        return 'bg-green-100 text-green-800';
      case 'semantic':
        return 'bg-blue-100 text-blue-800';
      case 'fuzzy':
        return 'bg-yellow-100 text-yellow-800';
      case 'tfidf':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Format relevance score
  const formatRelevanceScore = (score: number) => {
    return (score * 100).toFixed(1) + '%';
  };

  // Calculate pagination
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Search className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">Semantic Search</h2>
        </div>
        <div className="flex items-center space-x-2">
          {statistics.total_documents && (
            <span className="text-sm text-gray-500">
              {statistics.total_documents} documents indexed
            </span>
          )}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Semantic Model
              </label>
              <select
                value={config.semantic_model}
                onChange={(e) => setConfig(prev => ({ ...prev, semantic_model: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (Fast)</option>
                <option value="all-mpnet-base-v2">all-mpnet-base-v2 (Accurate)</option>
                <option value="multi-qa-MiniLM-L6-cos-v1">multi-qa-MiniLM-L6-cos-v1 (Q&A)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Similarity Threshold
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={config.similarity_threshold}
                onChange={(e) => setConfig(prev => ({ ...prev, similarity_threshold: parseFloat(e.target.value) }))}
                className="w-full"
              />
              <span className="text-xs text-gray-500">{config.similarity_threshold}</span>
            </div>
          </div>
          <div className="flex items-center space-x-4 mt-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.use_semantic_similarity}
                onChange={(e) => setConfig(prev => ({ ...prev, use_semantic_similarity: e.target.checked }))}
                className="rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Semantic Similarity</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.use_fuzzy_matching}
                onChange={(e) => setConfig(prev => ({ ...prev, use_fuzzy_matching: e.target.checked }))}
                className="rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Fuzzy Matching</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enable_cache}
                onChange={(e) => setConfig(prev => ({ ...prev, enable_cache: e.target.checked }))}
                className="rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Enable Cache</span>
            </label>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="p-4 border-b border-gray-200">
        <form onSubmit={handleSearchSubmit} className="flex space-x-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search books, authors, content..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!isInitialized}
            />
          </div>
          <button
            type="submit"
            disabled={!isInitialized || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Active Filters */}
        {Object.keys(selectedFilters).length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.entries(selectedFilters).map(([key, value]) => (
              <span
                key={key}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {key}: {String(value)}
                <button
                  onClick={() => removeFilter(key)}
                  className="ml-1 hover:text-blue-600"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Query Info */}
        {totalCount > 0 && (
          <div className="flex items-center justify-between mt-3 text-sm text-gray-500">
            <div className="flex items-center space-x-4">
              <span>{totalCount} results</span>
              <span className="flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                {queryTime}ms
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="text-xs border border-gray-300 rounded px-2 py-1"
              >
                <option value="relevance">Relevance</option>
                <option value="title">Title</option>
                <option value="author">Author</option>
                <option value="date">Date</option>
              </select>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="text-xs border border-gray-300 rounded px-2 py-1"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Facets Sidebar */}
        {facets.length > 0 && (
          <div className="w-64 border-r border-gray-200 p-4 overflow-y-auto">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Filters</h3>
            {facets.map((facet) => (
              <div key={facet.name} className="mb-4">
                <h4 className="text-xs font-medium text-gray-700 mb-2 capitalize">
                  {facet.name}
                </h4>
                <div className="space-y-1">
                  {facet.values.slice(0, 5).map(([value, count]) => (
                    <label key={value} className="flex items-center text-xs">
                      <input
                        type="checkbox"
                        checked={selectedFilters[facet.name] === value}
                        onChange={(e) => {
                          if (e.target.checked) {
                            handleFilterChange(facet.name, value);
                          } else {
                            removeFilter(facet.name);
                          }
                        }}
                        className="mr-2 rounded"
                      />
                      <span className="flex-1 truncate">{value}</span>
                      <span className="text-gray-400">({count})</span>
                    </label>
                  ))}
                  {facet.values.length > 5 && (
                    <button className="text-xs text-blue-600 hover:text-blue-800">
                      Show more...
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {!isLoading && !isInitialized && (
            <div className="flex items-center justify-center h-32 text-gray-500">
              Initializing search engine...
            </div>
          )}

          {!isLoading && isInitialized && results.length === 0 && query && (
            <div className="flex flex-col items-center justify-center h-32 text-gray-500">
              <Search className="w-8 h-8 mb-2" />
              <p>No results found for "{query}"</p>
              {suggestions.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm mb-1">Did you mean:</p>
                  <div className="flex flex-wrap gap-1">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => setQuery(suggestion)}
                        className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!isLoading && results.length > 0 && (
            <div className="p-4 space-y-4">
              {results.map((result) => (
                <div
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-md cursor-pointer transition-shadow"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 hover:text-blue-600">
                        {result.highlighted_fields.title || result.title}
                      </h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          {result.highlighted_fields.author || result.author}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getMatchTypeBadgeColor(result.match_type)}`}>
                        {result.match_type}
                      </span>
                      <div className="flex items-center text-sm text-gray-500">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {formatRelevanceScore(result.relevance_score)}
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 line-clamp-3 mb-2">
                    {result.highlighted_fields.content || result.content}
                  </p>
                  
                  {Object.keys(result.metadata).length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {Object.entries(result.metadata).slice(0, 3).map(([key, value]) => (
                        <span
                          key={key}
                          className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
                        >
                          <Tag className="w-3 h-3 mr-1" />
                          {key}: {String(value)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-500">
                    Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} results
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <span className="px-3 py-1 text-sm">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SemanticSearch;
