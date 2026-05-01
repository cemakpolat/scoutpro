import React, { useState, useEffect } from 'react';
import {
  Search as SearchIcon,
  Filter,
  Star,
  Clock,
  Zap,
  SlidersHorizontal,
  Grid,
  List,
  Download,
  Bookmark,
  X,
} from 'lucide-react';
import GlobalSearch from './search/GlobalSearch';
import AdvancedFilters from './search/AdvancedFilters';
import SavedSearches from './search/SavedSearches';
import PlayerDetail from './PlayerDetail';
import SequenceCoverageBadge from './SequenceCoverageBadge';
import { searchService } from '../services/searchService';
import { exportService } from '../services/exportService';
import apiService from '../services/api';
import { SearchResult, SearchFilters, SearchPreset } from '../types/search';

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState<any>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showSaved, setShowSaved] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [presets, setPresets] = useState<SearchPreset[]>([]);
  const [total, setTotal] = useState(0);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [playerCoverageById, setPlayerCoverageById] = useState<Record<string, any>>({});
  const [coverageLoading, setCoverageLoading] = useState(false);

  useEffect(() => {
    setPresets(searchService.getSearchPresets());
  }, []);

  useEffect(() => {
    const playerIds = results.filter((result) => result.type === 'player').map((result) => String(result.id)).filter(Boolean);
    let active = true;

    if (playerIds.length === 0) {
      setPlayerCoverageById({});
      setCoverageLoading(false);
      return () => {
        active = false;
      };
    }

    setCoverageLoading(true);
    setPlayerCoverageById({});

    void apiService.getPlayerSequenceCoverage(playerIds).then((response) => {
      if (!active) {
        return;
      }

      const items = response.success ? response.data?.items || [] : [];
      const nextCoverageByPlayerId: Record<string, any> = {};
      items.forEach((item: any) => {
        if (item?.player_id) {
          nextCoverageByPlayerId[String(item.player_id)] = item;
        }
      });
      setPlayerCoverageById(nextCoverageByPlayerId);
    }).finally(() => {
      if (active) {
        setCoverageLoading(false);
      }
    });

    return () => {
      active = false;
    };
  }, [results]);

  const performSearch = async (searchQuery: string, searchFilters?: SearchFilters) => {
    const hasQuery = searchQuery && searchQuery.trim();
    const hasFilters = searchFilters && Object.keys(searchFilters).length > 0;

    if (!hasQuery && !hasFilters) return;

    setIsLoading(true);
    setQuery(searchQuery); // Update the query state

    try {
      const response = await searchService.search({
        query: searchQuery || '',
        filters: searchFilters || filters,
        limit: 50,
        fuzzyMatch: true,
      });

      setResults(response.results);
      setTotal(response.total);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResultSelect = (result: SearchResult) => {
    if (result.type === 'player') {
      // Map SearchResult to Player format
      setSelectedPlayer({
        id: result.id,
        name: result.title,
        position: result.metadata?.position || 'Unknown',
        club: result.metadata?.club,
        age: result.metadata?.age || 0,
        nationality: result.metadata?.nationality || 'Unknown',
        marketValue: '€0M',
        goals: result.metadata?.goals || 0,
        assists: result.metadata?.assists || 0,
        rating: result.metadata?.rating || 0,
        passAccuracy: result.metadata?.passAccuracy || 0,
        image: result.image
      });
      return;
    }
    setQuery(result.title);
    performSearch(result.title, filters);
  };

  const handlePresetClick = (preset: SearchPreset) => {
    setFilters(preset.filters);
    setQuery(preset.name);
    performSearch(preset.name, preset.filters);
    setShowFilters(false);
  };

  const handleSaveSearch = async () => {
    if (!saveName.trim()) return;

    try {
      await searchService.saveSearch({
        name: saveName,
        query,
        filters,
        type: 'all',
      });

      setSaveName('');
      setShowSaveModal(false);
      alert('Search saved successfully!');
    } catch (error) {
      console.error('Failed to save search', error);
      alert('Failed to save search. Please try again.');
    }
  };

  const handleSearchSelect = (searchQuery: string, searchFilters?: SearchFilters) => {
    setQuery(searchQuery);
    setFilters(searchFilters || {});
    performSearch(searchQuery, searchFilters);
    setShowSaved(false);
  };

  const getActiveFilterCount = (): number => {
    return Object.values(filters).filter(v =>
      v !== undefined && v !== null && (Array.isArray(v) ? v.length > 0 : true)
    ).length;
  };

  const handleExportResults = async (format: 'pdf' | 'csv' = 'pdf') => {
    if (results.length === 0) {
      alert('No results to export');
      return;
    }

    try {
      // Prepare data for export
      const exportData = results.map(result => ({
        Type: result.type,
        Title: result.title,
        Subtitle: result.subtitle || '-',
        Description: result.description || '-',
        Relevance: result.relevance ? `${Math.round(result.relevance)}%` : '-',
      }));

      if (format === 'pdf') {
        await exportService.export({
          format: 'pdf',
          fileName: `search_results_${query || 'all'}_${Date.now()}.pdf`,
          data: exportData,
          header: `Search Results${query ? `: "${query}"` : ''}`,
          branding: {
            companyName: 'ScoutPro',
            colors: {
              primary: '#10b981',
            },
          },
        });
      } else {
        await exportService.exportSearchResults(results, 'csv');
      }

      alert(`Export to ${format.toUpperCase()} completed! Your file will download shortly.`);
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  const ResultCard: React.FC<{ result: SearchResult }> = ({ result }) => {
    const Icon = result.type === 'player' ? SearchIcon : SearchIcon;
    const coverage = result.type === 'player' ? playerCoverageById[String(result.id)] : null;

    return (
      <div
        onClick={() => handleResultSelect(result)}
        className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-green-500 transition-all cursor-pointer group"
      >
        <div className="flex items-start space-x-3">
          {result.image ? (
            <img
              src={result.image}
              alt={result.title}
              className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
            />
          ) : (
            <div className="w-16 h-16 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
              <Icon className="h-8 w-8 text-slate-500" />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-1">
              <h3 className="text-white font-semibold group-hover:text-green-400 transition-colors">
                {result.title}
              </h3>
              <div className="flex flex-col items-end gap-2 ml-2">
                <span className="text-xs text-slate-500 capitalize flex-shrink-0">
                  {result.type}
                </span>
                {coverage && <SequenceCoverageBadge coverage={coverage} compact />}
              </div>
            </div>

            {result.subtitle && (
              <p className="text-sm text-slate-400 mb-2">{result.subtitle}</p>
            )}

            {result.description && (
              <p className="text-sm text-slate-500 line-clamp-2">{result.description}</p>
            )}

            {result.metadata && (
              <div className="flex flex-wrap gap-2 mt-3">
                {Object.entries(result.metadata).slice(0, 4).map(([key, value]) => (
                  <span
                    key={key}
                    className="px-2 py-1 bg-slate-700 text-xs text-slate-300 rounded"
                  >
                    {String(value)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const ResultListItem: React.FC<{ result: SearchResult }> = ({ result }) => {
    const coverage = result.type === 'player' ? playerCoverageById[String(result.id)] : null;

    return (
      <div
        onClick={() => handleResultSelect(result)}
        className="bg-slate-800 border-l-4 border-slate-700 hover:border-green-500 px-4 py-3 hover:bg-slate-700/30 transition-all cursor-pointer"
      >
        <div className="flex items-center space-x-4">
          {result.image ? (
            <img
              src={result.image}
              alt={result.title}
              className="w-12 h-12 rounded object-cover flex-shrink-0"
            />
          ) : (
            <div className="w-12 h-12 rounded bg-slate-700 flex items-center justify-center flex-shrink-0">
              <SearchIcon className="h-6 w-6 text-slate-500" />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className="text-white font-medium">{result.title}</h3>
              <span className="text-xs text-slate-500 capitalize">• {result.type}</span>
            </div>
            {result.subtitle && (
              <p className="text-sm text-slate-400">{result.subtitle}</p>
            )}
            {coverage && (
              <div className="mt-2 inline-block">
                <SequenceCoverageBadge coverage={coverage} compact />
              </div>
            )}
          </div>

          {result.relevance && result.relevance > 0 && (
            <div className="flex-shrink-0 text-sm text-slate-500">
              {Math.round(result.relevance)}% match
            </div>
          )}
        </div>
      </div>
    );
  };

  if (selectedPlayer) {
    return <PlayerDetail player={selectedPlayer} onBack={() => setSelectedPlayer(null)} />;
  }

  const sequenceReadyCount = Object.values(playerCoverageById).filter((coverage: any) => coverage?.hasCoverage === true).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Advanced Search</h1>
        <p className="text-slate-400">
          Search across players, matches, teams, and reports with powerful filters
        </p>
      </div>

      {/* Search Bar and Controls */}
      <div className="space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <GlobalSearch
              onResultSelect={handleResultSelect}
              placeholder="Search players, matches, teams, reports..."
              autoFocus
            />
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-3 rounded-lg flex items-center space-x-2 transition-colors ${
                showFilters
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <Filter className="h-5 w-5" />
              <span className="text-sm font-medium">Filters</span>
              {getActiveFilterCount() > 0 && (
                <span className="px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {getActiveFilterCount()}
                </span>
              )}
            </button>

            <button
              onClick={() => setShowSaved(!showSaved)}
              className={`px-4 py-3 rounded-lg flex items-center space-x-2 transition-colors ${
                showSaved
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <Star className="h-5 w-5" />
              <span className="text-sm font-medium hidden lg:inline">Saved</span>
            </button>

            {query && (
              <button
                onClick={() => setShowSaveModal(true)}
                className="px-4 py-3 rounded-lg flex items-center space-x-2 bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 transition-colors"
                title="Save this search"
              >
                <Bookmark className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>

        {/* Quick Presets */}
        {!showFilters && !showSaved && (
          <div className="flex flex-wrap gap-2">
            <div className="flex items-center space-x-2 text-sm text-slate-400">
              <Zap className="h-4 w-4" />
              <span>Quick searches:</span>
            </div>
            {presets.slice(0, 6).map(preset => (
              <button
                key={preset.id}
                onClick={() => handlePresetClick(preset)}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 hover:border-green-500 hover:text-white transition-colors"
              >
                {preset.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="lg:max-w-md">
          <AdvancedFilters
            filters={filters}
            onFiltersChange={setFilters}
            onClose={() => setShowFilters(false)}
          />
          <div className="mt-4 flex space-x-3">
            <button
              onClick={() => performSearch(query, filters)}
              className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
            >
              Apply Filters
            </button>
            <button
              onClick={() => {
                setFilters({});
                setShowFilters(false);
              }}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Saved Searches Panel */}
      {showSaved && (
        <div className="lg:max-w-md">
          <SavedSearches onSearchSelect={handleSearchSelect} />
        </div>
      )}

      {/* Results Section */}
      {results.length > 0 && (
        <div>
          {/* Results Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm text-slate-400">
              {total} result{total !== 1 ? 's' : ''} found
              {query && ` for "${query}"`}
              {coverageLoading && <span className="ml-2">• checking player coverage...</span>}
              {!coverageLoading && sequenceReadyCount > 0 && <span className="ml-2">• {sequenceReadyCount} sequence-ready players</span>}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Grid view"
              >
                <Grid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded transition-colors ${
                  viewMode === 'list'
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="List view"
              >
                <List className="h-4 w-4" />
              </button>

              <button
                onClick={() => handleExportResults('pdf')}
                className="p-2 text-slate-400 hover:text-white rounded transition-colors"
                title="Export to PDF"
              >
                <Download className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Results Grid/List */}
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.map(result => (
                <ResultCard key={result.id} result={result} />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {results.map(result => (
                <ResultListItem key={result.id} result={result} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && results.length === 0 && query && (
        <div className="text-center py-12">
          <SearchIcon className="h-16 w-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No results found</h3>
          <p className="text-slate-400 mb-6">
            Try adjusting your search terms or filters
          </p>
          <button
            onClick={() => {
              setQuery('');
              setFilters({});
              setResults([]);
            }}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            Clear search
          </button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-slate-400">Searching...</p>
        </div>
      )}

      {/* Save Search Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Save Search</h3>
              <button
                onClick={() => setShowSaveModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Search name</label>
                <input
                  type="text"
                  value={saveName}
                  onChange={e => setSaveName(e.target.value)}
                  placeholder="e.g., Young Forwards in La Liga"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Query:</p>
                <p className="text-sm text-white">{query || '(empty)'}</p>
                {getActiveFilterCount() > 0 && (
                  <>
                    <p className="text-xs text-slate-400 mt-2 mb-1">Filters:</p>
                    <p className="text-sm text-white">{getActiveFilterCount()} active</p>
                  </>
                )}
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleSaveSearch}
                  disabled={!saveName.trim()}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                >
                  Save
                </button>
                <button
                  onClick={() => setShowSaveModal(false)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchPage;
