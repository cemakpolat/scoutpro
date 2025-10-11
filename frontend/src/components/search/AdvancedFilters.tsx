import React, { useState } from 'react';
import {
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal,
  Users,
  MapPin,
  Calendar,
  Target,
  DollarSign,
  TrendingUp,
  Shield,
} from 'lucide-react';
import { SearchFilters } from '../../types/search';

interface AdvancedFiltersProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  onClose?: () => void;
  type?: 'player' | 'match' | 'team' | 'all';
}

const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  onClose,
  type = 'all',
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['position', 'age', 'location'])
  );

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const toggleArrayFilter = (key: keyof SearchFilters, value: string) => {
    const currentArray = (filters[key] as string[]) || [];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(v => v !== value)
      : [...currentArray, value];
    updateFilter(key, newArray.length > 0 ? newArray : undefined);
  };

  const clearAllFilters = () => {
    onFiltersChange({});
  };

  const getActiveFilterCount = (): number => {
    return Object.values(filters).filter(v => v !== undefined && v !== null && (Array.isArray(v) ? v.length > 0 : true)).length;
  };

  // Position options
  const positions = ['Forward', 'Winger', 'Midfielder', 'Defender', 'Goalkeeper'];

  // League options
  const leagues = [
    'Premier League',
    'La Liga',
    'Serie A',
    'Bundesliga',
    'Ligue 1',
    'Champions League',
    'Europa League',
  ];

  // Nationality options (top football nations)
  const nationalities = [
    'England',
    'Spain',
    'Germany',
    'France',
    'Italy',
    'Brazil',
    'Argentina',
    'Portugal',
    'Netherlands',
    'Belgium',
  ];

  // Footedness options
  const footednessOptions = [
    { value: 'left', label: 'Left' },
    { value: 'right', label: 'Right' },
    { value: 'both', label: 'Both' },
  ];

  // Competition options for matches
  const competitions = [
    'Premier League',
    'La Liga',
    'Serie A',
    'Bundesliga',
    'Ligue 1',
    'Champions League',
    'Europa League',
    'World Cup',
    'European Championship',
  ];

  // Season options
  const seasons = ['2024/25', '2023/24', '2022/23', '2021/22'];

  // Venue options
  const venueOptions = [
    { value: 'home', label: 'Home' },
    { value: 'away', label: 'Away' },
    { value: 'neutral', label: 'Neutral' },
  ];

  const FilterSection: React.FC<{ title: string; icon: any; id: string; children: React.ReactNode }> = ({
    title,
    icon: Icon,
    id,
    children,
  }) => {
    const isExpanded = expandedSections.has(id);

    return (
      <div className="border-b border-slate-700 last:border-b-0">
        <button
          onClick={() => toggleSection(id)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
        >
          <div className="flex items-center space-x-2">
            <Icon className="h-4 w-4 text-green-400" />
            <span className="text-sm font-medium text-white">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
        </button>

        {isExpanded && <div className="px-4 pb-4">{children}</div>}
      </div>
    );
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Filter className="h-5 w-5 text-green-400" />
          <h3 className="text-lg font-semibold text-white">Advanced Filters</h3>
          {getActiveFilterCount() > 0 && (
            <span className="px-2 py-0.5 bg-green-600 text-white text-xs rounded-full">
              {getActiveFilterCount()}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {getActiveFilterCount() > 0 && (
            <button
              onClick={clearAllFilters}
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              Clear all
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Sections */}
      <div className="max-h-[600px] overflow-y-auto">
        {/* Player Filters */}
        {(type === 'player' || type === 'all') && (
          <>
            {/* Position */}
            <FilterSection title="Position" icon={Target} id="position">
              <div className="grid grid-cols-2 gap-2">
                {positions.map(pos => (
                  <button
                    key={pos}
                    onClick={() => toggleArrayFilter('position', pos)}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      (filters.position || []).includes(pos)
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {pos}
                  </button>
                ))}
              </div>
            </FilterSection>

            {/* Age Range */}
            <FilterSection title="Age Range" icon={Calendar} id="age">
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Min Age</label>
                  <input
                    type="number"
                    min="16"
                    max="45"
                    value={filters.ageMin || ''}
                    onChange={e =>
                      updateFilter('ageMin', e.target.value ? parseInt(e.target.value) : undefined)
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="16"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Max Age</label>
                  <input
                    type="number"
                    min="16"
                    max="45"
                    value={filters.ageMax || ''}
                    onChange={e =>
                      updateFilter('ageMax', e.target.value ? parseInt(e.target.value) : undefined)
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="45"
                  />
                </div>
              </div>
            </FilterSection>

            {/* League */}
            <FilterSection title="League" icon={Shield} id="league">
              <div className="space-y-2">
                {leagues.map(league => (
                  <label
                    key={league}
                    className="flex items-center space-x-2 cursor-pointer hover:bg-slate-700/30 px-2 py-1 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={(filters.league || []).includes(league)}
                      onChange={() => toggleArrayFilter('league', league)}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-green-600 focus:ring-green-500 focus:ring-offset-slate-800"
                    />
                    <span className="text-sm text-slate-300">{league}</span>
                  </label>
                ))}
              </div>
            </FilterSection>

            {/* Nationality */}
            <FilterSection title="Nationality" icon={MapPin} id="nationality">
              <div className="space-y-2">
                {nationalities.map(nation => (
                  <label
                    key={nation}
                    className="flex items-center space-x-2 cursor-pointer hover:bg-slate-700/30 px-2 py-1 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={(filters.nationality || []).includes(nation)}
                      onChange={() => toggleArrayFilter('nationality', nation)}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-green-600 focus:ring-green-500 focus:ring-offset-slate-800"
                    />
                    <span className="text-sm text-slate-300">{nation}</span>
                  </label>
                ))}
              </div>
            </FilterSection>

            {/* Height Range */}
            <FilterSection title="Height (cm)" icon={TrendingUp} id="height">
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Min Height</label>
                  <input
                    type="number"
                    min="150"
                    max="210"
                    value={filters.heightMin || ''}
                    onChange={e =>
                      updateFilter('heightMin', e.target.value ? parseInt(e.target.value) : undefined)
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="150"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Max Height</label>
                  <input
                    type="number"
                    min="150"
                    max="210"
                    value={filters.heightMax || ''}
                    onChange={e =>
                      updateFilter('heightMax', e.target.value ? parseInt(e.target.value) : undefined)
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="210"
                  />
                </div>
              </div>
            </FilterSection>

            {/* Footedness */}
            <FilterSection title="Preferred Foot" icon={Target} id="footedness">
              <div className="grid grid-cols-3 gap-2">
                {footednessOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => toggleArrayFilter('footedness', option.value)}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      (filters.footedness || []).includes(option.value as any)
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </FilterSection>

            {/* Market Value */}
            <FilterSection title="Market Value (€)" icon={DollarSign} id="marketValue">
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Min Value (millions)</label>
                  <input
                    type="number"
                    min="0"
                    value={filters.marketValueMin ? filters.marketValueMin / 1000000 : ''}
                    onChange={e =>
                      updateFilter(
                        'marketValueMin',
                        e.target.value ? parseInt(e.target.value) * 1000000 : undefined
                      )
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Max Value (millions)</label>
                  <input
                    type="number"
                    min="0"
                    value={filters.marketValueMax ? filters.marketValueMax / 1000000 : ''}
                    onChange={e =>
                      updateFilter(
                        'marketValueMax',
                        e.target.value ? parseInt(e.target.value) * 1000000 : undefined
                      )
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="200"
                  />
                </div>
              </div>
            </FilterSection>
          </>
        )}

        {/* Match Filters */}
        {(type === 'match' || type === 'all') && (
          <>
            {/* Competition */}
            <FilterSection title="Competition" icon={Shield} id="competition">
              <div className="space-y-2">
                {competitions.map(comp => (
                  <label
                    key={comp}
                    className="flex items-center space-x-2 cursor-pointer hover:bg-slate-700/30 px-2 py-1 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={(filters.competition || []).includes(comp)}
                      onChange={() => toggleArrayFilter('competition', comp)}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-green-600 focus:ring-green-500 focus:ring-offset-slate-800"
                    />
                    <span className="text-sm text-slate-300">{comp}</span>
                  </label>
                ))}
              </div>
            </FilterSection>

            {/* Season */}
            <FilterSection title="Season" icon={Calendar} id="season">
              <div className="grid grid-cols-2 gap-2">
                {seasons.map(season => (
                  <button
                    key={season}
                    onClick={() => toggleArrayFilter('season', season)}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      (filters.season || []).includes(season)
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {season}
                  </button>
                ))}
              </div>
            </FilterSection>

            {/* Venue */}
            <FilterSection title="Venue" icon={MapPin} id="venue">
              <div className="grid grid-cols-3 gap-2">
                {venueOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => toggleArrayFilter('venue', option.value)}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      (filters.venue || []).includes(option.value as any)
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </FilterSection>

            {/* Date Range */}
            <FilterSection title="Date Range" icon={Calendar} id="dateRange">
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">From</label>
                  <input
                    type="date"
                    value={filters.dateFrom || ''}
                    onChange={e => updateFilter('dateFrom', e.target.value || undefined)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">To</label>
                  <input
                    type="date"
                    value={filters.dateTo || ''}
                    onChange={e => updateFilter('dateTo', e.target.value || undefined)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>
            </FilterSection>
          </>
        )}
      </div>
    </div>
  );
};

export default AdvancedFilters;
