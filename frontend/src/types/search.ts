// Search-related types and interfaces

export interface SearchResult {
  id: string;
  type: 'player' | 'match' | 'team' | 'report';
  title: string;
  subtitle?: string;
  description?: string;
  image?: string;
  relevance?: number;
  metadata?: Record<string, any>;
}

export interface SearchFilters {
  // Player filters
  position?: string[];
  ageMin?: number;
  ageMax?: number;
  nationality?: string[];
  league?: string[];
  club?: string[];
  footedness?: ('left' | 'right' | 'both')[];
  heightMin?: number;
  heightMax?: number;
  marketValueMin?: number;
  marketValueMax?: number;

  // Match filters
  competition?: string[];
  season?: string[];
  dateFrom?: string;
  dateTo?: string;
  venue?: ('home' | 'away' | 'neutral')[];

  // General filters
  status?: string[];
  tags?: string[];
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  type: 'player' | 'match' | 'team' | 'report' | 'all';
  createdAt: string;
  updatedAt: string;
}

export interface SearchHistory {
  id: string;
  query: string;
  filters?: SearchFilters;
  type: 'player' | 'match' | 'team' | 'report' | 'all';
  timestamp: string;
  resultCount: number;
}

export interface SearchPreset {
  id: string;
  name: string;
  description: string;
  icon?: string;
  filters: SearchFilters;
  category: 'player' | 'match' | 'scouting';
}

export interface SearchSuggestion {
  type: 'query' | 'filter' | 'recent' | 'saved';
  value: string;
  label: string;
  icon?: string;
  metadata?: any;
}

export interface SearchOptions {
  query: string;
  filters?: SearchFilters;
  type?: 'player' | 'match' | 'team' | 'report' | 'all';
  limit?: number;
  offset?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  fuzzyMatch?: boolean;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  filters: SearchFilters;
  suggestions?: string[];
  facets?: Record<string, Array<{ value: string; count: number }>>;
}
