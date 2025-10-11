import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  X,
  Clock,
  Star,
  TrendingUp,
  Filter,
  Loader,
  User,
  Activity,
  FileText,
  Users as UsersIcon,
} from 'lucide-react';
import { searchService } from '../../services/searchService';
import { SearchResult, SearchSuggestion } from '../../types/search';

interface GlobalSearchProps {
  onResultSelect?: (result: SearchResult) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

const GlobalSearch: React.FC<GlobalSearchProps> = ({
  onResultSelect,
  placeholder = 'Search players, matches, teams...',
  autoFocus = false,
}) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Handle clicks outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Auto-focus input if requested
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  // Perform search with debouncing
  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      const recentSuggestions = await searchService.getAutocompleteSuggestions('');
      setSuggestions(recentSuggestions);
      setResults([]);
      return;
    }

    setIsLoading(true);

    try {
      // Get autocomplete suggestions
      const autocompleteSuggestions = await searchService.getAutocompleteSuggestions(searchQuery);
      setSuggestions(autocompleteSuggestions);

      // Perform full search
      const response = await searchService.search({
        query: searchQuery,
        limit: 10,
        fuzzyMatch: true,
      });

      setResults(response.results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle input change with debouncing
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setIsOpen(true);
    setSelectedIndex(0);

    // Clear existing timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer
    debounceTimer.current = setTimeout(() => {
      performSearch(value);
    }, 300);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const totalItems = suggestions.length + results.length;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev < totalItems - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : totalItems - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex < suggestions.length) {
        // Select suggestion
        const suggestion = suggestions[selectedIndex];
        handleSuggestionClick(suggestion);
      } else {
        // Select result
        const result = results[selectedIndex - suggestions.length];
        if (result) {
          handleResultClick(result);
        }
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.value);
    performSearch(suggestion.value);
    setSelectedIndex(0);
  };

  // Handle result click
  const handleResultClick = (result: SearchResult) => {
    setIsOpen(false);
    setQuery('');
    if (onResultSelect) {
      onResultSelect(result);
    }
  };

  // Clear search
  const handleClear = () => {
    setQuery('');
    setResults([]);
    setSuggestions([]);
    setSelectedIndex(0);
    inputRef.current?.focus();
    performSearch('');
  };

  // Get icon for result type
  const getResultIcon = (type: string) => {
    switch (type) {
      case 'player':
        return User;
      case 'match':
        return Activity;
      case 'team':
        return UsersIcon;
      case 'report':
        return FileText;
      default:
        return Search;
    }
  };

  // Get icon for suggestion type
  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'recent':
        return Clock;
      case 'saved':
        return Star;
      case 'filter':
        return Filter;
      default:
        return Search;
    }
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            setIsOpen(true);
            if (!query) performSearch('');
          }}
          placeholder={placeholder}
          className="w-full pl-12 pr-12 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
        />

        {/* Loading or Clear Button */}
        <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
          {isLoading ? (
            <Loader className="h-5 w-5 text-slate-400 animate-spin" />
          ) : query ? (
            <button
              onClick={handleClear}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          ) : null}
        </div>
      </div>

      {/* Dropdown Results */}
      {isOpen && (suggestions.length > 0 || results.length > 0 || query) && (
        <div className="absolute z-50 w-full mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl max-h-[500px] overflow-y-auto">
          {/* Suggestions Section */}
          {suggestions.length > 0 && (
            <div className="border-b border-slate-700">
              <div className="px-4 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {query ? 'Suggestions' : 'Recent Searches'}
              </div>
              {suggestions.map((suggestion, index) => {
                const Icon = getSuggestionIcon(suggestion.type);
                const isSelected = index === selectedIndex;

                return (
                  <button
                    key={`suggestion-${index}`}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className={`w-full px-4 py-3 flex items-center space-x-3 transition-colors ${
                      isSelected
                        ? 'bg-slate-700 text-white'
                        : 'text-slate-300 hover:bg-slate-700/50'
                    }`}
                  >
                    <Icon className="h-4 w-4 flex-shrink-0 text-slate-400" />
                    <span className="text-sm">{suggestion.label}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Results Section */}
          {results.length > 0 && (
            <div>
              <div className="px-4 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Results ({results.length})
              </div>
              {results.map((result, index) => {
                const Icon = getResultIcon(result.type);
                const globalIndex = suggestions.length + index;
                const isSelected = globalIndex === selectedIndex;

                return (
                  <button
                    key={result.id}
                    onClick={() => handleResultClick(result)}
                    className={`w-full px-4 py-3 flex items-start space-x-3 transition-colors ${
                      isSelected
                        ? 'bg-slate-700 text-white'
                        : 'text-slate-300 hover:bg-slate-700/50'
                    }`}
                  >
                    {result.image ? (
                      <img
                        src={result.image}
                        alt={result.title}
                        className="w-10 h-10 rounded-lg object-cover flex-shrink-0"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                        <Icon className="h-5 w-5 text-slate-400" />
                      </div>
                    )}

                    <div className="flex-1 text-left min-w-0">
                      <div className="font-medium text-sm truncate">{result.title}</div>
                      {result.subtitle && (
                        <div className="text-xs text-slate-400 truncate">{result.subtitle}</div>
                      )}
                      {result.description && (
                        <div className="text-xs text-slate-500 truncate mt-0.5">
                          {result.description}
                        </div>
                      )}
                    </div>

                    {result.relevance && result.relevance > 0 && (
                      <div className="flex-shrink-0 text-xs text-slate-500">
                        {Math.round(result.relevance)}%
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* No Results */}
          {query && results.length === 0 && suggestions.length === 0 && !isLoading && (
            <div className="px-4 py-8 text-center text-slate-400">
              <Search className="h-8 w-8 mx-auto mb-2 text-slate-600" />
              <p className="text-sm">No results found for "{query}"</p>
              <p className="text-xs text-slate-500 mt-1">Try adjusting your search terms</p>
            </div>
          )}

          {/* Keyboard Shortcuts Help */}
          <div className="border-t border-slate-700 px-4 py-2 flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center space-x-4">
              <span>
                <kbd className="px-1.5 py-0.5 bg-slate-700 rounded">↑↓</kbd> Navigate
              </span>
              <span>
                <kbd className="px-1.5 py-0.5 bg-slate-700 rounded">↵</kbd> Select
              </span>
              <span>
                <kbd className="px-1.5 py-0.5 bg-slate-700 rounded">Esc</kbd> Close
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GlobalSearch;
