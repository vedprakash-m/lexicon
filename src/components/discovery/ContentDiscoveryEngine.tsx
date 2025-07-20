import React, { useState, useEffect, useMemo } from 'react';
import { Network, BookOpen, Users, Tag, TrendingUp, Filter, Search } from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  author: string;
  type: 'book' | 'article' | 'document';
  categories: string[];
  keywords: string[];
  metadata: {
    publishedDate?: string;
    pageCount?: number;
    rating?: number;
    description?: string;
  };
  relationships: ContentRelationship[];
  similarityScore?: number;
}

interface ContentRelationship {
  targetId: string;
  type: 'author' | 'series' | 'translation' | 'edition' | 'similar' | 'references';
  strength: number; // 0-1
  metadata?: {
    commonAuthors?: string[];
    sharedKeywords?: string[];
    topicSimilarity?: number;
  };
}

interface RecommendationEngine {
  getRecommendations: (itemId: string, limit?: number) => ContentItem[];
  getSimilarContent: (item: ContentItem, limit?: number) => ContentItem[];
  getRelatedByAuthor: (authorName: string, limit?: number) => ContentItem[];
  getRelatedByCategory: (category: string, limit?: number) => ContentItem[];
  getTrendingContent: (timeframe?: 'week' | 'month' | 'year') => ContentItem[];
}

interface ContentDiscoveryEngineProps {
  content: ContentItem[];
  selectedItem?: ContentItem;
  onItemSelect: (item: ContentItem) => void;
  onRelationshipExplore: (relationship: ContentRelationship) => void;
}

export const ContentDiscoveryEngine: React.FC<ContentDiscoveryEngineProps> = ({
  content,
  selectedItem,
  onItemSelect,
  onRelationshipExplore,
}) => {
  const [activeTab, setActiveTab] = useState<'recommendations' | 'similar' | 'relationships' | 'trending'>('recommendations');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [relationshipFilter, setRelationshipFilter] = useState<string>('all');

  // Create recommendation engine
  const recommendationEngine: RecommendationEngine = useMemo(() => ({
    getRecommendations: (itemId: string, limit = 10) => {
      const item = content.find(c => c.id === itemId);
      if (!item) return [];

      // Score content based on multiple factors
      const scored = content
        .filter(c => c.id !== itemId)
        .map(c => ({
          ...c,
          similarityScore: calculateSimilarityScore(item, c)
        }))
        .sort((a, b) => (b.similarityScore || 0) - (a.similarityScore || 0))
        .slice(0, limit);

      return scored;
    },

    getSimilarContent: (item: ContentItem, limit = 10) => {
      return content
        .filter(c => c.id !== item.id)
        .map(c => ({
          ...c,
          similarityScore: calculateContentSimilarity(item, c)
        }))
        .sort((a, b) => (b.similarityScore || 0) - (a.similarityScore || 0))
        .slice(0, limit);
    },

    getRelatedByAuthor: (authorName: string, limit = 10) => {
      return content
        .filter(c => c.author.toLowerCase().includes(authorName.toLowerCase()))
        .slice(0, limit);
    },

    getRelatedByCategory: (category: string, limit = 10) => {
      return content
        .filter(c => c.categories.includes(category))
        .slice(0, limit);
    },

    getTrendingContent: (timeframe = 'month') => {
      // Mock trending algorithm - in real implementation would use engagement metrics
      return content
        .filter(c => c.metadata.rating && c.metadata.rating > 4.0)
        .sort((a, b) => (b.metadata.rating || 0) - (a.metadata.rating || 0))
        .slice(0, 10);
    }
  }), [content]);

  // Calculate similarity between two content items
  const calculateSimilarityScore = (item1: ContentItem, item2: ContentItem): number => {
    let score = 0;

    // Author similarity
    if (item1.author === item2.author) {
      score += 0.4;
    }

    // Category overlap
    const categoryOverlap = item1.categories.filter(cat => item2.categories.includes(cat)).length;
    const categoryUnion = new Set([...item1.categories, ...item2.categories]).size;
    if (categoryUnion > 0) {
      score += (categoryOverlap / categoryUnion) * 0.3;
    }

    // Keyword similarity
    const keywordOverlap = item1.keywords.filter(kw => item2.keywords.includes(kw)).length;
    const keywordUnion = new Set([...item1.keywords, ...item2.keywords]).size;
    if (keywordUnion > 0) {
      score += (keywordOverlap / keywordUnion) * 0.2;
    }

    // Existing relationship bonus
    const hasRelationship = item1.relationships.some(rel => rel.targetId === item2.id);
    if (hasRelationship) {
      score += 0.1;
    }

    return Math.min(score, 1.0);
  };

  const calculateContentSimilarity = (item1: ContentItem, item2: ContentItem): number => {
    // More sophisticated similarity calculation
    let score = 0;

    // Title similarity (simple word overlap)
    const title1Words = new Set(item1.title.toLowerCase().split(/\s+/));
    const title2Words = new Set(item2.title.toLowerCase().split(/\s+/));
    const titleOverlap = [...title1Words].filter(word => title2Words.has(word)).length;
    const titleUnion = new Set([...title1Words, ...title2Words]).size;
    if (titleUnion > 0) {
      score += (titleOverlap / titleUnion) * 0.2;
    }

    // Description similarity
    if (item1.metadata.description && item2.metadata.description) {
      const desc1Words = new Set(item1.metadata.description.toLowerCase().split(/\s+/));
      const desc2Words = new Set(item2.metadata.description.toLowerCase().split(/\s+/));
      const descOverlap = [...desc1Words].filter(word => desc2Words.has(word)).length;
      const descUnion = new Set([...desc1Words, ...desc2Words]).size;
      if (descUnion > 0) {
        score += (descOverlap / descUnion) * 0.3;
      }
    }

    // Add base similarity score
    score += calculateSimilarityScore(item1, item2) * 0.5;

    return Math.min(score, 1.0);
  };

  // Get current recommendations based on active tab
  const getCurrentRecommendations = (): ContentItem[] => {
    if (!selectedItem) return [];

    switch (activeTab) {
      case 'recommendations':
        return recommendationEngine.getRecommendations(selectedItem.id);
      case 'similar':
        return recommendationEngine.getSimilarContent(selectedItem);
      case 'trending':
        return recommendationEngine.getTrendingContent();
      default:
        return [];
    }
  };

  // Filter recommendations based on search and categories
  const filteredRecommendations = useMemo(() => {
    let recommendations = getCurrentRecommendations();

    // Apply search filter
    if (searchQuery) {
      recommendations = recommendations.filter(item =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.metadata.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply category filter
    if (selectedCategories.length > 0) {
      recommendations = recommendations.filter(item =>
        item.categories.some(cat => selectedCategories.includes(cat))
      );
    }

    return recommendations;
  }, [activeTab, selectedItem, searchQuery, selectedCategories, content]);

  // Get all unique categories
  const allCategories = useMemo(() => {
    const categories = new Set<string>();
    content.forEach(item => {
      item.categories.forEach(cat => categories.add(cat));
    });
    return Array.from(categories).sort();
  }, [content]);

  // Get relationships for selected item
  const getRelationships = (): ContentRelationship[] => {
    if (!selectedItem) return [];
    
    let relationships = selectedItem.relationships;
    
    if (relationshipFilter !== 'all') {
      relationships = relationships.filter(rel => rel.type === relationshipFilter);
    }
    
    return relationships.sort((a, b) => b.strength - a.strength);
  };

  const RelationshipVisualization: React.FC<{ relationships: ContentRelationship[] }> = ({ relationships }) => (
    <div className="space-y-4">
      {relationships.map((relationship, index) => {
        const relatedItem = content.find(c => c.id === relationship.targetId);
        if (!relatedItem) return null;

        return (
          <div
            key={index}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
            onClick={() => onRelationshipExplore(relationship)}
          >
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${getRelationshipColor(relationship.type)}`} />
              <div>
                <h4 className="font-medium text-gray-900">{relatedItem.title}</h4>
                <p className="text-sm text-gray-600">{relatedItem.author}</p>
                <p className="text-xs text-gray-500 capitalize">{relationship.type} relationship</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">
                {Math.round(relationship.strength * 100)}%
              </div>
              <div className="w-16 h-2 bg-gray-200 rounded-full mt-1">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${relationship.strength * 100}%` }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );

  const getRelationshipColor = (type: string): string => {
    const colors = {
      author: 'bg-blue-500',
      series: 'bg-green-500',
      translation: 'bg-purple-500',
      edition: 'bg-orange-500',
      similar: 'bg-pink-500',
      references: 'bg-indigo-500',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500';
  };

  const ContentCard: React.FC<{ item: ContentItem; showSimilarity?: boolean }> = ({ 
    item, 
    showSimilarity = false 
  }) => (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onItemSelect(item)}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-gray-900 line-clamp-2">{item.title}</h3>
        {showSimilarity && item.similarityScore && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full ml-2">
            {Math.round(item.similarityScore * 100)}%
          </span>
        )}
      </div>
      
      <p className="text-gray-600 text-sm mb-2">{item.author}</p>
      
      <div className="flex flex-wrap gap-1 mb-2">
        {item.categories.slice(0, 3).map(category => (
          <span
            key={category}
            className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full"
          >
            {category}
          </span>
        ))}
        {item.categories.length > 3 && (
          <span className="text-xs text-gray-500">+{item.categories.length - 3}</span>
        )}
      </div>
      
      {item.metadata.description && (
        <p className="text-sm text-gray-600 line-clamp-2">
          {item.metadata.description}
        </p>
      )}
      
      <div className="flex justify-between items-center mt-3 text-xs text-gray-500">
        <span>{item.type}</span>
        {item.metadata.rating && (
          <div className="flex items-center">
            <span className="text-yellow-400">★</span>
            <span className="ml-1">{item.metadata.rating.toFixed(1)}</span>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Content Discovery</h2>
        
        {selectedItem && (
          <div className="bg-blue-50 p-3 rounded-lg mb-4">
            <h3 className="font-medium text-blue-900">Exploring: {selectedItem.title}</h3>
            <p className="text-blue-700 text-sm">by {selectedItem.author}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          {[
            { id: 'recommendations', label: 'Recommendations', icon: TrendingUp },
            { id: 'similar', label: 'Similar Content', icon: BookOpen },
            { id: 'relationships', label: 'Relationships', icon: Network },
            { id: 'trending', label: 'Trending', icon: TrendingUp },
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Filters */}
      {activeTab !== 'relationships' && (
        <div className="border-b border-gray-200 p-4 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search recommendations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {allCategories.slice(0, 8).map(category => (
              <button
                key={category}
                onClick={() => {
                  setSelectedCategories(prev =>
                    prev.includes(category)
                      ? prev.filter(c => c !== category)
                      : [...prev, category]
                  );
                }}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  selectedCategories.includes(category)
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Relationship Filters */}
      {activeTab === 'relationships' && (
        <div className="border-b border-gray-200 p-4">
          <select
            value={relationshipFilter}
            onChange={(e) => setRelationshipFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Relationships</option>
            <option value="author">Same Author</option>
            <option value="series">Series</option>
            <option value="translation">Translations</option>
            <option value="edition">Editions</option>
            <option value="similar">Similar Content</option>
            <option value="references">References</option>
          </select>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {!selectedItem ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <BookOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select Content to Explore</h3>
              <p className="text-gray-600">Choose a book or document to discover related content and relationships</p>
            </div>
          </div>
        ) : activeTab === 'relationships' ? (
          <RelationshipVisualization relationships={getRelationships()} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRecommendations.map(item => (
              <ContentCard
                key={item.id}
                item={item}
                showSimilarity={activeTab === 'similar' || activeTab === 'recommendations'}
              />
            ))}
          </div>
        )}

        {selectedItem && activeTab !== 'relationships' && filteredRecommendations.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <p className="text-gray-500">No recommendations found</p>
              <p className="text-gray-400 text-sm">Try adjusting your filters</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};