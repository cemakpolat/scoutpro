import {
  SearchOptions,
  SearchResponse,
  SearchResult,
  SavedSearch,
  SearchHistory,
  SearchPreset,
  SearchFilters,
  SearchSuggestion
} from '../types/search';
import { Player, Match } from '../types';

class SearchService {
  private readonly STORAGE_KEYS = {
    HISTORY: 'scoutpro_search_history',
    SAVED: 'scoutpro_saved_searches',
  };

  /**
   * Perform a search across all data types or specific type
   */
  async search(options: SearchOptions): Promise<SearchResponse> {
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (useMockData) {
      return this.mockSearch(options);
    }

    try {
      const params = new URLSearchParams();
      params.append('q', options.query);
      if (options.type) params.append('type', options.type);
      if (options.limit) params.append('limit', options.limit.toString());
      if (options.offset) params.append('offset', options.offset.toString());
      if (options.sortBy) params.append('sortBy', options.sortBy);
      if (options.sortOrder) params.append('sortOrder', options.sortOrder);
      if (options.fuzzyMatch) params.append('fuzzy', 'true');
      if (options.filters) params.append('filters', JSON.stringify(options.filters));

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/search?${params}`);
      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();

      // Save to history
      this.addToHistory({
        query: options.query,
        filters: options.filters,
        type: options.type || 'all',
        resultCount: data.total,
      });

      return data;
    } catch (error) {
      console.error('Search error:', error);
      return this.mockSearch(options);
    }
  }

  /**
   * Mock search implementation using fuzzy matching
   */
  private mockSearch(options: SearchOptions): SearchResponse {
    const query = options.query.toLowerCase();
    const results: SearchResult[] = [];

    // Mock player data for search
    const mockPlayers: SearchResult[] = [
      {
        id: 'p1',
        type: 'player',
        title: 'Kylian Mbappé',
        subtitle: 'Forward • Paris Saint-Germain',
        description: 'French forward known for exceptional speed and finishing',
        image: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=100',
        metadata: { position: 'Forward', age: 25, nationality: 'France', league: 'Ligue 1' }
      },
      {
        id: 'p2',
        type: 'player',
        title: 'Erling Haaland',
        subtitle: 'Forward • Manchester City',
        description: 'Norwegian striker with incredible goal-scoring record',
        image: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=100',
        metadata: { position: 'Forward', age: 23, nationality: 'Norway', league: 'Premier League' }
      },
      {
        id: 'p3',
        type: 'player',
        title: 'Jude Bellingham',
        subtitle: 'Midfielder • Real Madrid',
        description: 'Young English midfielder with exceptional technical skills',
        image: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=100',
        metadata: { position: 'Midfielder', age: 21, nationality: 'England', league: 'La Liga' }
      },
      {
        id: 'p4',
        type: 'player',
        title: 'Vinicius Junior',
        subtitle: 'Winger • Real Madrid',
        description: 'Brazilian winger with exceptional dribbling skills',
        image: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=100',
        metadata: { position: 'Winger', age: 23, nationality: 'Brazil', league: 'La Liga' }
      },
      {
        id: 'p5',
        type: 'player',
        title: 'Pedri',
        subtitle: 'Midfielder • Barcelona',
        description: 'Spanish midfielder known for vision and passing',
        image: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=100',
        metadata: { position: 'Midfielder', age: 21, nationality: 'Spain', league: 'La Liga' }
      },
      {
        id: 'p6',
        type: 'player',
        title: 'Kevin De Bruyne',
        subtitle: 'Midfielder • Manchester City',
        description: 'Belgian playmaker with exceptional passing range',
        image: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=100',
        metadata: { position: 'Midfielder', age: 32, nationality: 'Belgium', league: 'Premier League' }
      },
    ];

    const mockMatches: SearchResult[] = [
      {
        id: 'm1',
        type: 'match',
        title: 'Real Madrid vs Barcelona',
        subtitle: 'La Liga • Oct 28, 2024',
        description: 'El Clásico rivalry match',
        metadata: { competition: 'La Liga', season: '2024/25', venue: 'home' }
      },
      {
        id: 'm2',
        type: 'match',
        title: 'Manchester City vs Arsenal',
        subtitle: 'Premier League • Nov 2, 2024',
        description: 'Top of the table clash',
        metadata: { competition: 'Premier League', season: '2024/25', venue: 'home' }
      },
    ];

    const mockTeams: SearchResult[] = [
      {
        id: 't1',
        type: 'team',
        title: 'Real Madrid',
        subtitle: 'La Liga',
        description: 'Spanish giants with 14 Champions League titles',
        image: 'https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/100px-Real_Madrid_CF.svg.png',
      },
      {
        id: 't2',
        type: 'team',
        title: 'Manchester City',
        subtitle: 'Premier League',
        description: 'English champions and treble winners',
      },
    ];

    // Filter by type
    let searchPool: SearchResult[] = [];
    if (!options.type || options.type === 'all') {
      searchPool = [...mockPlayers, ...mockMatches, ...mockTeams];
    } else if (options.type === 'player') {
      searchPool = mockPlayers;
    } else if (options.type === 'match') {
      searchPool = mockMatches;
    } else if (options.type === 'team') {
      searchPool = mockTeams;
    }

    // Fuzzy search implementation
    const fuzzyMatch = (text: string, pattern: string): number => {
      if (options.fuzzyMatch === false) {
        return text.includes(pattern) ? 100 : 0;
      }

      // Simple fuzzy matching algorithm
      let score = 0;
      let patternIdx = 0;
      let textIdx = 0;
      const patternLen = pattern.length;
      const textLen = text.length;

      while (textIdx < textLen && patternIdx < patternLen) {
        if (text[textIdx] === pattern[patternIdx]) {
          score++;
          patternIdx++;
        }
        textIdx++;
      }

      if (patternIdx === patternLen) {
        return (score / patternLen) * 100;
      }
      return 0;
    };

    // Search and score results
    searchPool.forEach(item => {
      const titleScore = fuzzyMatch(item.title.toLowerCase(), query);
      const subtitleScore = item.subtitle ? fuzzyMatch(item.subtitle.toLowerCase(), query) : 0;
      const descScore = item.description ? fuzzyMatch(item.description.toLowerCase(), query) : 0;

      const maxScore = Math.max(titleScore, subtitleScore, descScore);

      if (maxScore > 30 || query === '') {
        results.push({
          ...item,
          relevance: maxScore,
        });
      }
    });

    // Apply filters
    let filteredResults = this.applyFilters(results, options.filters);

    // Sort by relevance
    filteredResults.sort((a, b) => (b.relevance || 0) - (a.relevance || 0));

    // Apply pagination
    const limit = options.limit || 10;
    const offset = options.offset || 0;
    const paginatedResults = filteredResults.slice(offset, offset + limit);

    // Save to history if query is not empty
    if (query) {
      this.addToHistory({
        query: options.query,
        filters: options.filters,
        type: options.type || 'all',
        resultCount: filteredResults.length,
      });
    }

    return {
      results: paginatedResults,
      total: filteredResults.length,
      query: options.query,
      filters: options.filters || {},
      suggestions: this.generateSuggestions(options.query),
    };
  }

  /**
   * Apply filters to search results
   */
  private applyFilters(results: SearchResult[], filters?: SearchFilters): SearchResult[] {
    if (!filters) return results;

    return results.filter(result => {
      const metadata = result.metadata || {};

      // Player filters
      if (filters.position && filters.position.length > 0) {
        if (!filters.position.includes(metadata.position)) return false;
      }

      if (filters.ageMin !== undefined && metadata.age < filters.ageMin) return false;
      if (filters.ageMax !== undefined && metadata.age > filters.ageMax) return false;

      if (filters.nationality && filters.nationality.length > 0) {
        if (!filters.nationality.includes(metadata.nationality)) return false;
      }

      if (filters.league && filters.league.length > 0) {
        if (!filters.league.includes(metadata.league)) return false;
      }

      // Match filters
      if (filters.competition && filters.competition.length > 0) {
        if (!filters.competition.includes(metadata.competition)) return false;
      }

      if (filters.venue && filters.venue.length > 0) {
        if (!filters.venue.includes(metadata.venue)) return false;
      }

      return true;
    });
  }

  /**
   * Generate search suggestions
   */
  private generateSuggestions(query: string): string[] {
    const suggestions = [
      'forwards under 25',
      'midfielders in La Liga',
      'defenders with high passing',
      'young talents',
      'free agents',
      'champions league players',
    ];

    return suggestions.filter(s => s.toLowerCase().includes(query.toLowerCase())).slice(0, 5);
  }

  /**
   * Get autocomplete suggestions
   */
  async getAutocompleteSuggestions(query: string): Promise<SearchSuggestion[]> {
    if (!query || query.length < 2) {
      return this.getRecentSearches().slice(0, 5).map(h => ({
        type: 'recent',
        value: h.query,
        label: h.query,
        icon: 'Clock',
        metadata: { timestamp: h.timestamp }
      }));
    }

    const suggestions: SearchSuggestion[] = [];

    // Quick searches
    const quickSearches = [
      'forwards under 25',
      'midfielders in La Liga',
      'defenders with high passing',
      'young talents',
      'free agents',
    ];

    quickSearches
      .filter(s => s.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 3)
      .forEach(s => {
        suggestions.push({
          type: 'query',
          value: s,
          label: s,
          icon: 'Search',
        });
      });

    // Saved searches
    const saved = this.getSavedSearches()
      .filter(s => s.name.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 2);

    saved.forEach(s => {
      suggestions.push({
        type: 'saved',
        value: s.query,
        label: s.name,
        icon: 'Star',
        metadata: s,
      });
    });

    return suggestions.slice(0, 8);
  }

  /**
   * Save a search
   */
  saveSearch(search: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt'>): SavedSearch {
    const saved = this.getSavedSearches();
    const newSearch: SavedSearch = {
      ...search,
      id: `search-${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    saved.unshift(newSearch);
    localStorage.setItem(this.STORAGE_KEYS.SAVED, JSON.stringify(saved.slice(0, 50)));

    return newSearch;
  }

  /**
   * Get saved searches
   */
  getSavedSearches(): SavedSearch[] {
    const saved = localStorage.getItem(this.STORAGE_KEYS.SAVED);
    return saved ? JSON.parse(saved) : [];
  }

  /**
   * Delete a saved search
   */
  deleteSavedSearch(id: string): void {
    const saved = this.getSavedSearches().filter(s => s.id !== id);
    localStorage.setItem(this.STORAGE_KEYS.SAVED, JSON.stringify(saved));
  }

  /**
   * Add to search history
   */
  private addToHistory(item: Omit<SearchHistory, 'id' | 'timestamp'>): void {
    const history = this.getSearchHistory();

    // Don't add duplicate recent searches
    const isDuplicate = history.some(h =>
      h.query === item.query &&
      Date.now() - new Date(h.timestamp).getTime() < 60000 // within 1 minute
    );

    if (isDuplicate) return;

    const newItem: SearchHistory = {
      ...item,
      id: `history-${Date.now()}`,
      timestamp: new Date().toISOString(),
    };

    history.unshift(newItem);
    localStorage.setItem(this.STORAGE_KEYS.HISTORY, JSON.stringify(history.slice(0, 50)));
  }

  /**
   * Get search history
   */
  getSearchHistory(): SearchHistory[] {
    const history = localStorage.getItem(this.STORAGE_KEYS.HISTORY);
    return history ? JSON.parse(history) : [];
  }

  /**
   * Get recent searches (unique queries only)
   */
  getRecentSearches(): SearchHistory[] {
    const history = this.getSearchHistory();
    const uniqueQueries = new Set<string>();
    const recent: SearchHistory[] = [];

    for (const item of history) {
      if (!uniqueQueries.has(item.query)) {
        uniqueQueries.add(item.query);
        recent.push(item);
      }
      if (recent.length >= 10) break;
    }

    return recent;
  }

  /**
   * Clear search history
   */
  clearHistory(): void {
    localStorage.removeItem(this.STORAGE_KEYS.HISTORY);
  }

  /**
   * Get search presets (predefined common searches)
   */
  getSearchPresets(): SearchPreset[] {
    return [
      {
        id: 'young-forwards',
        name: 'Young Forwards',
        description: 'Forwards under 23 years old',
        icon: 'Target',
        category: 'player',
        filters: {
          position: ['Forward'],
          ageMax: 23,
        },
      },
      {
        id: 'la-liga-midfielders',
        name: 'La Liga Midfielders',
        description: 'All midfielders in La Liga',
        icon: 'Users',
        category: 'player',
        filters: {
          position: ['Midfielder'],
          league: ['La Liga'],
        },
      },
      {
        id: 'tall-defenders',
        name: 'Tall Defenders',
        description: 'Defenders over 185cm',
        icon: 'Shield',
        category: 'player',
        filters: {
          position: ['Defender'],
          heightMin: 185,
        },
      },
      {
        id: 'left-footed',
        name: 'Left-Footed Players',
        description: 'Players with left foot preference',
        icon: 'Activity',
        category: 'player',
        filters: {
          footedness: ['left'],
        },
      },
      {
        id: 'champions-league',
        name: 'Champions League Matches',
        description: 'Recent Champions League games',
        icon: 'Trophy',
        category: 'match',
        filters: {
          competition: ['Champions League'],
        },
      },
      {
        id: 'high-value',
        name: 'High Market Value',
        description: 'Players valued over €50M',
        icon: 'TrendingUp',
        category: 'player',
        filters: {
          marketValueMin: 50000000,
        },
      },
    ];
  }
}

export const searchService = new SearchService();
