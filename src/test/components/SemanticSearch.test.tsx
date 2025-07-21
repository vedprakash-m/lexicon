import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { invoke } from '@tauri-apps/api/core';
import SemanticSearch from '../../components/SemanticSearch';

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

const mockInvoke = vi.mocked(invoke);

describe('SemanticSearch Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize search engine on mount', async () => {
    mockInvoke.mockResolvedValueOnce(undefined); // initialize_semantic_search
    mockInvoke.mockResolvedValueOnce({ // get_search_statistics
      total_documents: 0,
      total_searches: 0,
      cache_hit_rate: 0.0
    });

    render(<SemanticSearch />);

    await waitFor(() => {
      expect(mockInvoke).toHaveBeenCalledWith('initialize_semantic_search', {
        config: expect.objectContaining({
          semantic_model: 'all-MiniLM-L6-v2',
          use_semantic_similarity: true,
          similarity_threshold: 0.7
        })
      });
    });
  });

  it('should perform search when form is submitted', async () => {
    const mockSearchResponse = {
      results: [
        {
          id: 'doc1',
          title: 'Test Document',
          author: 'Test Author',
          content: 'Test content',
          metadata: {},
          relevance_score: 0.95,
          match_type: 'exact',
          highlighted_fields: {}
        }
      ],
      total_count: 1,
      facets: [],
      query_time_ms: 50,
      suggestions: []
    };

    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}) // get_search_statistics
      .mockResolvedValueOnce(mockSearchResponse); // semantic_search

    render(<SemanticSearch />);

    // Wait for initialization
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    // Enter search query
    const searchInput = screen.getByPlaceholderText(/search books/i);
    fireEvent.change(searchInput, { target: { value: 'test query' } });

    // Submit search
    const searchButton = screen.getByText('Search');
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(mockInvoke).toHaveBeenCalledWith('semantic_search', {
        query: expect.objectContaining({
          text: 'test query',
          filters: {},
          facets: ['category', 'author', 'subject'],
          sort_by: 'relevance',
          sort_order: 'desc',
          limit: 20,
          offset: 0
        })
      });
    });

    // Check if results are displayed
    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
      expect(screen.getByText('Test Author')).toBeInTheDocument();
    });
  });

  it('should handle search errors gracefully', async () => {
    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}) // get_search_statistics
      .mockRejectedValueOnce(new Error('Search failed')); // semantic_search

    render(<SemanticSearch />);

    // Wait for initialization
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    // Enter search query and submit
    const searchInput = screen.getByPlaceholderText(/search books/i);
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(screen.getByText('Search'));

    // Should show no results without crashing
    await waitFor(() => {
      expect(screen.queryByText('Test Document')).not.toBeInTheDocument();
    });
  });

  it('should apply filters correctly', async () => {
    const mockSearchResponse = {
      results: [],
      total_count: 0,
      facets: [
        {
          name: 'category',
          values: [['technology', 5], ['science', 3]]
        }
      ],
      query_time_ms: 25,
      suggestions: []
    };

    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}) // get_search_statistics
      .mockResolvedValueOnce(mockSearchResponse); // semantic_search

    render(<SemanticSearch />);

    // Wait for initialization and perform search to get facets
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    const searchInput = screen.getByPlaceholderText(/search books/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    // Wait for facets to appear
    await waitFor(() => {
      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    // Should show category filter
    expect(screen.getByText('category')).toBeInTheDocument();
    expect(screen.getByText('technology')).toBeInTheDocument();
  });

  it('should handle configuration changes', async () => {
    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}); // get_search_statistics

    render(<SemanticSearch showAdvancedOptions={true} />);

    // Wait for initialization
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    // Open settings (find the button that contains the Settings icon)
    const buttons = screen.getAllByRole('button');
    const settingsButton = buttons.find(button => 
      button.querySelector('.lucide-settings') || 
      button.innerHTML.includes('Settings')
    );
    expect(settingsButton).toBeTruthy();
    fireEvent.click(settingsButton!);

    // Should show settings panel
    expect(screen.getByText('Semantic Model')).toBeInTheDocument();
    expect(screen.getByText('Similarity Threshold')).toBeInTheDocument();
  });

  it('should show query statistics', async () => {
    const mockSearchResponse = {
      results: [
        {
          id: 'doc1',
          title: 'Test Document',
          author: 'Test Author',
          content: 'Test content',
          metadata: {},
          relevance_score: 0.95,
          match_type: 'exact',
          highlighted_fields: {}
        }
      ],
      total_count: 15,
      facets: [],
      query_time_ms: 125,
      suggestions: []
    };

    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}) // get_search_statistics
      .mockResolvedValueOnce(mockSearchResponse); // semantic_search

    render(<SemanticSearch />);

    // Wait for initialization and search
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    const searchInput = screen.getByPlaceholderText(/search books/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    // Check for statistics display
    await waitFor(() => {
      expect(screen.getByText('15 results')).toBeInTheDocument();
      expect(screen.getByText('125ms')).toBeInTheDocument();
    });
  });

  it('should handle pagination', async () => {
    const mockSearchResponse = {
      results: Array.from({ length: 20 }, (_, i) => ({
        id: `doc${i}`,
        title: `Document ${i}`,
        author: 'Test Author',
        content: 'Test content',
        metadata: {},
        relevance_score: 0.9 - (i * 0.01),
        match_type: 'exact',
        highlighted_fields: {}
      })),
      total_count: 50,
      facets: [],
      query_time_ms: 75,
      suggestions: []
    };

    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}) // get_search_statistics
      .mockResolvedValueOnce(mockSearchResponse); // semantic_search

    render(<SemanticSearch />);

    // Wait for initialization and search
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    const searchInput = screen.getByPlaceholderText(/search books/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    // Check pagination
    await waitFor(() => {
      expect(screen.getByText(/Showing 1 to 20 of 50 results/)).toBeInTheDocument();
      expect(screen.getByText(/Page 1 of 3/)).toBeInTheDocument();
    });
  });

  it('should call onResultSelect when result is clicked', async () => {
    const mockOnResultSelect = vi.fn();
    const mockSearchResponse = {
      results: [
        {
          id: 'doc1',
          title: 'Clickable Document',
          author: 'Test Author',
          content: 'Test content',
          metadata: {},
          relevance_score: 0.95,
          match_type: 'exact',
          highlighted_fields: {}
        }
      ],
      total_count: 1,
      facets: [],
      query_time_ms: 50,
      suggestions: []
    };

    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}) // get_search_statistics
      .mockResolvedValueOnce(mockSearchResponse); // semantic_search

    render(<SemanticSearch onResultSelect={mockOnResultSelect} />);

    // Wait for initialization and search
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    const searchInput = screen.getByPlaceholderText(/search books/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.click(screen.getByText('Search'));

    // Click on result
    await waitFor(() => {
      const resultElement = screen.getByText('Clickable Document');
      fireEvent.click(resultElement);
    });

    expect(mockOnResultSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'doc1',
        title: 'Clickable Document'
      })
    );
  });

  it('should display suggestions when no results found', async () => {
    const mockSearchResponse = {
      results: [],
      total_count: 0,
      facets: [],
      query_time_ms: 30,
      suggestions: ['suggested query', 'another suggestion']
    };

    mockInvoke
      .mockResolvedValueOnce(undefined) // initialize_semantic_search
      .mockResolvedValueOnce({}) // get_search_statistics
      .mockResolvedValueOnce(mockSearchResponse); // semantic_search

    render(<SemanticSearch />);

    // Wait for initialization and search
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).not.toBeDisabled();
    });

    const searchInput = screen.getByPlaceholderText(/search books/i);
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    fireEvent.click(screen.getByText('Search'));

    // Check for suggestions
    await waitFor(() => {
      expect(screen.getByText('Did you mean:')).toBeInTheDocument();
      expect(screen.getByText('suggested query')).toBeInTheDocument();
      expect(screen.getByText('another suggestion')).toBeInTheDocument();
    });
  });
});
