import React, { useState, useEffect } from 'react';
import {
  Star,
  Clock,
  Trash2,
  Search,
  Edit2,
  Check,
  X,
} from 'lucide-react';
import { searchService } from '../../services/searchService';
import { SavedSearch, SearchHistory, SearchFilters } from '../../types/search';

interface SavedSearchesProps {
  onSearchSelect?: (query: string, filters?: SearchFilters) => void;
}

const SavedSearches: React.FC<SavedSearchesProps> = ({ onSearchSelect }) => {
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);
  const [activeTab, setActiveTab] = useState<'saved' | 'history'>('saved');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  // Load saved searches and history
  useEffect(() => {
    void loadData();
  }, []);

  const loadData = async () => {
    try {
      const [saved, history] = await Promise.all([
        searchService.getSavedSearches(),
        searchService.getRecentSearches(),
      ]);
      setSavedSearches(saved);
      setSearchHistory(history);
    } catch (error) {
      console.error('Failed to load saved searches', error);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await searchService.deleteSavedSearch(id);
      await loadData();
    } catch (error) {
      console.error('Failed to delete saved search', error);
    }
  };

  const handleClearHistory = async () => {
    if (confirm('Are you sure you want to clear your search history?')) {
      try {
        await searchService.clearHistory();
        await loadData();
      } catch (error) {
        console.error('Failed to clear search history', error);
      }
    }
  };

  const handleEditStart = (search: SavedSearch) => {
    setEditingId(search.id);
    setEditName(search.name);
  };

  const handleEditSave = async (search: SavedSearch) => {
    if (!editName.trim()) {
      return;
    }

    try {
      await searchService.updateSavedSearch(search.id, { name: editName.trim() });
      setEditingId(null);
      await loadData();
    } catch (error) {
      console.error('Failed to update saved search', error);
    }
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditName('');
  };

  const handleSearchClick = (query: string, filters?: SearchFilters) => {
    if (onSearchSelect) {
      onSearchSelect(query, filters);
    }
  };

  const formatRelativeTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getFilterSummary = (filters: SearchFilters): string => {
    const parts: string[] = [];

    if (filters.position && filters.position.length > 0) {
      parts.push(`${filters.position.length} position${filters.position.length > 1 ? 's' : ''}`);
    }
    if (filters.league && filters.league.length > 0) {
      parts.push(`${filters.league.length} league${filters.league.length > 1 ? 's' : ''}`);
    }
    if (filters.nationality && filters.nationality.length > 0) {
      parts.push(`${filters.nationality.length} nationalit${filters.nationality.length > 1 ? 'ies' : 'y'}`);
    }
    if (filters.ageMin || filters.ageMax) {
      parts.push(`age ${filters.ageMin || '16'}-${filters.ageMax || '45'}`);
    }

    return parts.length > 0 ? parts.join(', ') : 'No filters';
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg">
      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        <button
          onClick={() => setActiveTab('saved')}
          className={`flex-1 px-4 py-3 flex items-center justify-center space-x-2 transition-colors ${
            activeTab === 'saved'
              ? 'bg-slate-700 text-white border-b-2 border-green-500'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <Star className="h-4 w-4" />
          <span className="text-sm font-medium">Saved</span>
          {savedSearches.length > 0 && (
            <span className="px-1.5 py-0.5 bg-slate-600 text-xs rounded-full">
              {savedSearches.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex-1 px-4 py-3 flex items-center justify-center space-x-2 transition-colors ${
            activeTab === 'history'
              ? 'bg-slate-700 text-white border-b-2 border-green-500'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <Clock className="h-4 w-4" />
          <span className="text-sm font-medium">History</span>
          {searchHistory.length > 0 && (
            <span className="px-1.5 py-0.5 bg-slate-600 text-xs rounded-full">
              {searchHistory.length}
            </span>
          )}
        </button>
      </div>

      {/* Content */}
      <div className="max-h-[500px] overflow-y-auto">
        {activeTab === 'saved' && (
          <div>
            {savedSearches.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <Star className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400 text-sm mb-1">No saved searches yet</p>
                <p className="text-slate-500 text-xs">
                  Save your frequently used searches for quick access
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-700">
                {savedSearches.map(search => (
                  <div
                    key={search.id}
                    className="px-4 py-3 hover:bg-slate-700/30 transition-colors group"
                  >
                    {editingId === search.id ? (
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={editName}
                          onChange={e => setEditName(e.target.value)}
                          className="flex-1 px-3 py-1.5 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          autoFocus
                        />
                        <button
                          onClick={() => handleEditSave(search)}
                          className="p-1.5 text-green-400 hover:text-green-300 transition-colors"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                        <button
                          onClick={handleEditCancel}
                          className="p-1.5 text-slate-400 hover:text-white transition-colors"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-start justify-between">
                          <button
                            onClick={() => handleSearchClick(search.query, search.filters)}
                            className="flex-1 text-left"
                          >
                            <div className="flex items-center space-x-2 mb-1">
                              <Star className="h-4 w-4 text-yellow-400 flex-shrink-0" />
                              <span className="text-sm font-medium text-white">{search.name}</span>
                              <span className="text-xs text-slate-500 capitalize">{search.type}</span>
                            </div>
                            <p className="text-xs text-slate-400 mb-1">{search.query}</p>
                            <p className="text-xs text-slate-500">{getFilterSummary(search.filters)}</p>
                          </button>

                          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleEditStart(search)}
                              className="p-1.5 text-slate-400 hover:text-white transition-colors"
                              title="Edit name"
                            >
                              <Edit2 className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => handleDelete(search.id)}
                              className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-slate-500">
                          Saved {formatRelativeTime(search.createdAt)}
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            {searchHistory.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <Clock className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400 text-sm mb-1">No search history</p>
                <p className="text-slate-500 text-xs">Your recent searches will appear here</p>
              </div>
            ) : (
              <>
                <div className="px-4 py-2 border-b border-slate-700 flex items-center justify-between">
                  <span className="text-xs text-slate-400">Recent searches</span>
                  <button
                    onClick={handleClearHistory}
                    className="text-xs text-slate-400 hover:text-red-400 transition-colors"
                  >
                    Clear all
                  </button>
                </div>
                <div className="divide-y divide-slate-700">
                  {searchHistory.map(item => (
                    <button
                      key={item.id}
                      onClick={() => handleSearchClick(item.query, item.filters)}
                      className="w-full px-4 py-3 hover:bg-slate-700/30 transition-colors text-left group"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <Clock className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                            <span className="text-sm text-white truncate">{item.query}</span>
                          </div>
                          <div className="flex items-center space-x-2 text-xs text-slate-500">
                            <span>{formatRelativeTime(item.timestamp)}</span>
                            <span>•</span>
                            <span>{item.resultCount} result{item.resultCount !== 1 ? 's' : ''}</span>
                            {item.filters && Object.keys(item.filters).length > 0 && (
                              <>
                                <span>•</span>
                                <span className="capitalize">{item.type}</span>
                              </>
                            )}
                          </div>
                        </div>
                        <Search className="h-4 w-4 text-slate-600 group-hover:text-slate-400 transition-colors flex-shrink-0 ml-2" />
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SavedSearches;
