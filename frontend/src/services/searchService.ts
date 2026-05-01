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
import { API_BASE_URL } from '../config/api';

class SearchService {
  private readonly baseUrl = API_BASE_URL;

  private async requestJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.message || errorData?.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  /**
   * Perform a search across all data types or specific type
   */
  async search(options: SearchOptions): Promise<SearchResponse> {
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

      const baseUrl = API_BASE_URL;
      const response = await fetch(`${baseUrl}/search?${params}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.message || errorData?.error || 'Search failed');
      }

      const data = await response.json();
      const results = this.normalizeGatewayResults(data);
      const filteredResults = this.applyFilters(results, options.filters);
      filteredResults.sort((a, b) => (b.relevance || 0) - (a.relevance || 0));

      const limit = options.limit || 10;
      const offset = options.offset || 0;
      const paginatedResults = filteredResults.slice(offset, offset + limit);

      try {
        await this.addToHistory({
          query: options.query,
          filters: options.filters,
          type: options.type || 'all',
          resultCount: filteredResults.length,
        });
      } catch (historyError) {
        console.error('Search history persistence error:', historyError);
      }

      return {
        results: paginatedResults,
        total: filteredResults.length,
        query: options.query,
        filters: options.filters || {},
        suggestions: this.generateSuggestions(options.query),
      };
    } catch (error) {
      console.error('Search error:', error);
      throw error instanceof Error ? error : new Error('Search failed');
    }
  }

  private normalizeGatewayResults(data: any): SearchResult[] {
    const results: SearchResult[] = [];

    (Array.isArray(data?.players) ? data.players : []).forEach((player: any) => {
      results.push({
        id: String(player.id || player.uID || ''),
        type: 'player',
        title: player.name || 'Unknown Player',
        subtitle: [player.position, player.club].filter(Boolean).join(' • '),
        description: player.nationality ? `${player.nationality} player` : undefined,
        image: player.photo || player.image,
        relevance: 100,
        metadata: {
          position: player.position,
          age: player.age,
          nationality: player.nationality,
          league: player.league,
          club: player.teamName || player.club,
          goals: player.goals,
          assists: player.assists,
          passAccuracy: player.passAccuracy,
          rating: player.rating,
        },
      });
    });

    (Array.isArray(data?.teams) ? data.teams : []).forEach((team: any) => {
      results.push({
        id: String(team.id || team.uID || ''),
        type: 'team',
        title: team.name || 'Unknown Team',
        subtitle: [team.league, team.country].filter(Boolean).join(' • '),
        description: team.manager ? `Managed by ${team.manager}` : undefined,
        image: team.logo,
        relevance: 100,
        metadata: {
          league: team.league,
          country: team.country,
        },
      });
    });

    (Array.isArray(data?.matches) ? data.matches : []).forEach((match: any) => {
      const homeTeam = match.homeTeam || match.home_team || match.home_team_id || 'Home';
      const awayTeam = match.awayTeam || match.away_team || match.away_team_id || 'Away';

      results.push({
        id: String(match.id || match.uID || ''),
        type: 'match',
        title: `${homeTeam} vs ${awayTeam}`,
        subtitle: [match.competition, match.date].filter(Boolean).join(' • '),
        description: match.venue ? `Venue: ${match.venue}` : undefined,
        relevance: 100,
        metadata: {
          competition: match.competition,
          venue: match.venue,
          status: match.status,
        },
      });
    });

    return results;
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
    let recentSearches: SearchHistory[] = [];
    let savedSearches: SavedSearch[] = [];

    try {
      [recentSearches, savedSearches] = await Promise.all([
        this.getRecentSearches(),
        this.getSavedSearches(),
      ]);
    } catch (error) {
      console.error('Autocomplete persistence error:', error);
    }

    if (!query || query.length < 2) {
      return recentSearches.slice(0, 5).map(h => ({
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
    const saved = savedSearches
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
  async saveSearch(search: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt'>): Promise<SavedSearch> {
    return this.requestJson<SavedSearch>('/search/saved', {
      method: 'POST',
      body: JSON.stringify(search),
    });
  }

  async updateSavedSearch(id: string, updates: Partial<SavedSearch>): Promise<SavedSearch> {
    return this.requestJson<SavedSearch>(`/search/saved/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Get saved searches
   */
  async getSavedSearches(): Promise<SavedSearch[]> {
    return this.requestJson<SavedSearch[]>('/search/saved');
  }

  /**
   * Delete a saved search
   */
  async deleteSavedSearch(id: string): Promise<void> {
    await this.requestJson(`/search/saved/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * Add to search history
   */
  private async addToHistory(item: Omit<SearchHistory, 'id' | 'timestamp'>): Promise<void> {
    await this.requestJson('/search/history', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  /**
   * Get search history
   */
  async getSearchHistory(): Promise<SearchHistory[]> {
    return this.requestJson<SearchHistory[]>('/search/history');
  }

  /**
   * Get recent searches (unique queries only)
   */
  async getRecentSearches(): Promise<SearchHistory[]> {
    const history = await this.getSearchHistory();
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
  async clearHistory(): Promise<void> {
    await this.requestJson('/search/history', {
      method: 'DELETE',
    });
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
