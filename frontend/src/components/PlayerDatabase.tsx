import React, { useState } from 'react';
import { Search, Filter, Download, Plus, X } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import { exportService } from '../services/exportService';
import { PlayerFilters, QueryParams } from '../types';
import PlayerCard from './PlayerCard';
import PlayerDetail from './PlayerDetail';

const PlayerDatabase: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [positionFilter, setPositionFilter] = useState('all');
  const [filters, setFilters] = useState<PlayerFilters>({});
  const [queryParams, setQueryParams] = useState<QueryParams>({
    page: 1,
    limit: 20,
    sortBy: 'rating',
    sortOrder: 'desc'
  });

  // Add Player modal state
  const [showAddPlayer, setShowAddPlayer] = useState(false);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [newPlayerPosition, setNewPlayerPosition] = useState('ST');
  const [newPlayerAge, setNewPlayerAge] = useState('');
  const [newPlayerNationality, setNewPlayerNationality] = useState('');
  const [newPlayerClub, setNewPlayerClub] = useState('');
  const [newPlayerHeight, setNewPlayerHeight] = useState('');
  const [newPlayerFoot, setNewPlayerFoot] = useState('Right');

  // Advanced filters state
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  const { players, loading, errors, addPlayer } = useData();

  // Fetch players with filters
  const { data: playersData, loading: playersLoading, refetch } = useApi(
    () => apiService.getPlayers(filters, { ...queryParams, search: searchTerm }),
    [filters, queryParams, searchTerm]
  );

  const handleFilterChange = (newFilters: Partial<PlayerFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const handlePositionFilter = (position: string) => {
    setPositionFilter(position);
    if (position === 'all') {
      handleFilterChange({ position: undefined });
    } else {
      handleFilterChange({ position: [position] });
    }
  };

  const displayPlayers = playersData || players;

  const handleExport = async () => {
    if (!displayPlayers || displayPlayers.length === 0) {
      alert('No players to export');
      return;
    }

    try {
      const exportData = displayPlayers.map((player: any) => ({
        Name: player.name,
        Position: player.position,
        Age: player.age,
        Nationality: player.nationality,
        Club: player.club,
        'Market Value': player.marketValue || '-',
        Height: player.height ? `${player.height}cm` : '-',
        Foot: player.foot || '-',
      }));

      await exportService.export({
        format: 'pdf',
        fileName: `players_database_${Date.now()}.pdf`,
        data: exportData,
        header: 'Player Database Export',
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });

      alert('Player database exported to PDF successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  const handleAddPlayer = () => {
    const newPlayer = {
      id: `player_${Date.now()}`,
      name: newPlayerName,
      position: newPlayerPosition,
      age: parseInt(newPlayerAge) || 0,
      nationality: newPlayerNationality,
      club: newPlayerClub,
      height: parseInt(newPlayerHeight) || 0,
      foot: newPlayerFoot,
      rating: 0,
      marketValue: 'TBD',
      stats: {}
    };

    // For now, show success message (backend integration will replace this)
    alert(`✅ Player "${newPlayerName}" added successfully!\n\n(Note: This will be saved to database once backend is connected)`);

    // Reset form
    setNewPlayerName('');
    setNewPlayerPosition('ST');
    setNewPlayerAge('');
    setNewPlayerNationality('');
    setNewPlayerClub('');
    setNewPlayerHeight('');
    setNewPlayerFoot('Right');
    setShowAddPlayer(false);

    // Trigger refetch to show updated list (when backend is ready)
    refetch?.();
  };

  if (selectedPlayer) {
    return <PlayerDetail player={selectedPlayer} onBack={() => setSelectedPlayer(null)} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Player Database</h1>
        <button
          onClick={() => setShowAddPlayer(true)}
          className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add Player</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col lg:flex-row space-y-4 lg:space-y-0 lg:space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search players, clubs, or leagues..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>
        
        <select
          value={positionFilter}
          onChange={(e) => handlePositionFilter(e.target.value)}
          className="px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-green-500"
        >
          <option value="all">All Positions</option>
          <option value="GK">Goalkeeper</option>
          <option value="CB">Center Back</option>
          <option value="LB">Left Back</option>
          <option value="RB">Right Back</option>
          <option value="CM">Central Midfielder</option>
          <option value="CDM">Defensive Midfielder</option>
          <option value="CAM">Attacking Midfielder</option>
          <option value="LW">Left Winger</option>
          <option value="RW">Right Winger</option>
          <option value="ST">Striker</option>
        </select>

        <button
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className={`flex items-center space-x-2 px-4 py-3 border rounded-lg transition-colors ${
            showAdvancedFilters
              ? 'bg-blue-600 border-blue-600 hover:bg-blue-700'
              : 'bg-slate-800 border-slate-700 hover:bg-slate-700'
          }`}
        >
          <Filter className="h-4 w-4" />
          <span>More Filters</span>
        </button>

        <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
          <Download className="h-4 w-4" />
          <span>Export</span>
        </button>
      </div>

      {/* Advanced Filters Panel */}
      {showAdvancedFilters && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Advanced Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Age Range</label>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                  onChange={(e) => handleFilterChange({ ageMin: parseInt(e.target.value) })}
                />
                <span>-</span>
                <input
                  type="number"
                  placeholder="Max"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                  onChange={(e) => handleFilterChange({ ageMax: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Nationality</label>
              <input
                type="text"
                placeholder="e.g., England, Brazil"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                onChange={(e) => handleFilterChange({ nationality: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Current Club</label>
              <input
                type="text"
                placeholder="e.g., Manchester United"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                onChange={(e) => handleFilterChange({ club: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Preferred Foot</label>
              <select
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                onChange={(e) => handleFilterChange({ foot: e.target.value !== 'all' ? e.target.value : undefined })}
              >
                <option value="all">All</option>
                <option value="Right">Right</option>
                <option value="Left">Left</option>
                <option value="Both">Both</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Height (cm)</label>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                  onChange={(e) => handleFilterChange({ heightMin: parseInt(e.target.value) })}
                />
                <span>-</span>
                <input
                  type="number"
                  placeholder="Max"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                  onChange={(e) => handleFilterChange({ heightMax: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Contract Status</label>
              <select
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                onChange={(e) => handleFilterChange({ contractStatus: e.target.value !== 'all' ? e.target.value : undefined })}
              >
                <option value="all">All</option>
                <option value="active">Active</option>
                <option value="expiring">Expiring Soon</option>
                <option value="free">Free Agent</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-3 mt-4">
            <button
              onClick={() => {
                setFilters({});
                setPositionFilter('all');
              }}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              Clear All Filters
            </button>
            <button
              onClick={() => setShowAdvancedFilters(false)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}

      {/* Results Summary */}
      <div className="text-slate-400">
        Showing {displayPlayers.length} players
        {playersLoading && <span className="ml-2">Loading...</span>}
        {errors.players && <span className="ml-2 text-red-400">Error: {errors.players}</span>}
      </div>

      {/* Player Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {displayPlayers.map((player) => (
          <PlayerCard
            key={player.id}
            player={player}
            onClick={() => setSelectedPlayer(player)}
          />
        ))}
      </div>

      {/* Add Player Modal */}
      {showAddPlayer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Add New Player</h2>
              <button
                onClick={() => setShowAddPlayer(false)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Player Name *</label>
                  <input
                    type="text"
                    value={newPlayerName}
                    onChange={(e) => setNewPlayerName(e.target.value)}
                    placeholder="e.g., Erling Haaland"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Position *</label>
                  <select
                    value={newPlayerPosition}
                    onChange={(e) => setNewPlayerPosition(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="GK">Goalkeeper</option>
                    <option value="CB">Center Back</option>
                    <option value="LB">Left Back</option>
                    <option value="RB">Right Back</option>
                    <option value="CM">Central Midfielder</option>
                    <option value="CDM">Defensive Midfielder</option>
                    <option value="CAM">Attacking Midfielder</option>
                    <option value="LW">Left Winger</option>
                    <option value="RW">Right Winger</option>
                    <option value="ST">Striker</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Age *</label>
                  <input
                    type="number"
                    value={newPlayerAge}
                    onChange={(e) => setNewPlayerAge(e.target.value)}
                    placeholder="e.g., 23"
                    min="15"
                    max="45"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Nationality *</label>
                  <input
                    type="text"
                    value={newPlayerNationality}
                    onChange={(e) => setNewPlayerNationality(e.target.value)}
                    placeholder="e.g., Norway"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Current Club *</label>
                  <input
                    type="text"
                    value={newPlayerClub}
                    onChange={(e) => setNewPlayerClub(e.target.value)}
                    placeholder="e.g., Manchester City"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Height (cm)</label>
                  <input
                    type="number"
                    value={newPlayerHeight}
                    onChange={(e) => setNewPlayerHeight(e.target.value)}
                    placeholder="e.g., 194"
                    min="150"
                    max="220"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Preferred Foot</label>
                  <select
                    value={newPlayerFoot}
                    onChange={(e) => setNewPlayerFoot(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="Right">Right</option>
                    <option value="Left">Left</option>
                    <option value="Both">Both</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center space-x-3 pt-4">
                <button
                  onClick={handleAddPlayer}
                  disabled={!newPlayerName.trim() || !newPlayerAge || !newPlayerNationality.trim() || !newPlayerClub.trim()}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Add Player
                </button>
                <button
                  onClick={() => setShowAddPlayer(false)}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
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

export default PlayerDatabase;