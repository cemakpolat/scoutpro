import React from 'react';
import { Search, Filter, Star, TrendingUp, Users, Target, Brain, AlertCircle } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import { Player, AIInsight } from '../types';
import { deriveAge } from '../utils/dataTransformers';

interface ScoutingDashboardProps {
  onPlayerSelect?: (player: Player) => void;
}

const ScoutingDashboard: React.FC<ScoutingDashboardProps> = ({ onPlayerSelect }) => {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedPosition, setSelectedPosition] = React.useState<string>('all');
  const [ageRange, setAgeRange] = React.useState({ min: 16, max: 35 });

  const { data: targetPlayers, loading: targetsLoading } = useApi(
    () => apiService.getPlayers({
      position: selectedPosition !== 'all' ? [selectedPosition] : undefined,
      ageMin: ageRange.min,
      ageMax: ageRange.max
    }, {
      search: searchTerm.trim() || undefined,
    }),
    [selectedPosition, ageRange, searchTerm]
  );

  // Get player statistics for scouting recommendations
  const { data: playerStats, loading: statsLoading } = useApi(
    () => apiService.getPlayerStatisticsRealtime(10, 0, 'goals'),
    []
  );

  // Transform stats into AI recommendations
  const aiRecommendations = (playerStats?.data || []).map((p: any, idx: number) => ({
    id: `stat-${idx}`,
    title: `${p.player_name} - High Performer`,
    description: `${p.goals} goals, ${p.shots} shots, ${p.passes} passes - ${p.pass_accuracy}% accuracy`,
    priority: p.goals > 0 ? 'high' : 'medium',
    confidence: p.goals > 0 ? 0.86 : 0.68,
  }));
  const aiLoading = statsLoading;

  const positions = ['all', 'GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST'];
  const shortlistCount = Math.min(targetPlayers?.length || 0, 12);
  const recentActivity = (aiRecommendations || []).slice(0, 3).map((insight: AIInsight) => ({
    id: insight.id,
    message: insight.title,
    detail: insight.description,
  }));

  const handlePlayerClick = (player: Player) => {
    if (onPlayerSelect) {
      onPlayerSelect(player);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Scouting Dashboard</h1>
          <p className="text-slate-400 mt-1">Discover and analyze potential transfer targets</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
            <Target className="w-4 h-4" />
            <span>Add Target</span>
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search players..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-400"
            />
          </div>

          {/* Position Filter */}
          <select
            value={selectedPosition}
            onChange={(e) => setSelectedPosition(e.target.value)}
            className="px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {positions.map(position => (
              <option key={position} value={position}>
                {position === 'all' ? 'All Positions' : position}
              </option>
            ))}
          </select>

          {/* Age Range */}
          <div className="flex items-center space-x-2">
            <input
              type="number"
              placeholder="Min age"
              value={ageRange.min}
              onChange={(e) => setAgeRange(prev => ({ ...prev, min: parseInt(e.target.value) || 16 }))}
              className="w-20 px-3 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-400"
            />
            <span className="text-slate-400">-</span>
            <input
              type="number"
              placeholder="Max age"
              value={ageRange.max}
              onChange={(e) => setAgeRange(prev => ({ ...prev, max: parseInt(e.target.value) || 35 }))}
              className="w-20 px-3 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-400"
            />
          </div>

          {/* Advanced Filters */}
          <button className="flex items-center justify-center space-x-2 px-4 py-2 border border-slate-600 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors">
            <Filter className="w-4 h-4" />
            <span>More Filters</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Recommendations */}
        <div className="lg:col-span-2">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center space-x-2">
                <Brain className="w-5 h-5 text-purple-600" />
                <h2 className="text-xl font-semibold text-white">AI Recommendations</h2>
              </div>
            </div>
            <div className="p-6">
              {aiLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-slate-700 rounded-full"></div>
                        <div className="flex-1">
                          <div className="h-4 bg-slate-700 rounded w-1/3 mb-2"></div>
                          <div className="h-3 bg-slate-700 rounded w-2/3"></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : aiRecommendations && aiRecommendations.length > 0 ? (
                <div className="space-y-4">
                  {aiRecommendations.slice(0, 5).map((insight: AIInsight) => (
                    <div key={insight.id} className="flex items-start space-x-4 p-4 bg-purple-900/20 rounded-lg border border-purple-800/30">
                      <div className="w-2 h-2 bg-purple-600 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <h3 className="font-medium text-white">{insight.title}</h3>
                        <p className="text-sm text-slate-400 mt-1">{insight.description}</p>
                        <div className="flex items-center space-x-2 mt-2">
                          <span className="text-xs bg-purple-900/40 text-purple-300 px-2 py-1 rounded">
                            {Math.round(insight.confidence * 100)}% confidence
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">No AI recommendations available</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="space-y-6">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Scouting Overview</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Active Targets</span>
                <span className="font-semibold text-blue-400">
                  {targetsLoading ? '...' : targetPlayers?.length || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Reports This Week</span>
                <span className="font-semibold text-green-400">
                  {aiRecommendations.length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Shortlisted</span>
                <span className="font-semibold text-orange-400">{shortlistCount}</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
            {recentActivity.length > 0 ? (
              <div className="space-y-3">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-3">
                    <div className="mt-2 h-2 w-2 rounded-full bg-green-500"></div>
                    <div>
                      <div className="text-sm text-slate-200">{activity.message}</div>
                      <div className="text-xs text-slate-400">{activity.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-400">No scouting activity is available from the backend right now.</div>
            )}
          </div>
        </div>
      </div>

      {/* Player Results */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700">
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Search Results</h2>
            <span className="text-sm text-slate-400">
              {targetsLoading ? 'Loading...' : `${targetPlayers?.length || 0} players found`}
            </span>
          </div>
        </div>
        <div className="p-6">
          {targetsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="animate-pulse">
                  <div className="border border-slate-700 rounded-lg p-4">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-slate-700 rounded-full"></div>
                      <div className="flex-1">
                        <div className="h-4 bg-slate-700 rounded w-2/3 mb-2"></div>
                        <div className="h-3 bg-slate-700 rounded w-1/2"></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : targetPlayers && targetPlayers.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {targetPlayers.map((player: Player) => (
                <div
                  key={player.id}
                  onClick={() => handlePlayerClick(player)}
                  className="border border-slate-700 rounded-lg p-4 hover:shadow-md hover:border-slate-600 transition-all cursor-pointer bg-slate-900/50"
                >
                  <div className="flex items-center space-x-4">
                    <img
                      src={player.photo || `https://images.pexels.com/photos/274506/pexels-photo-274506.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop`}
                      alt={player.name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                    <div className="flex-1">
                      <h3 className="font-medium text-white">{player.name}</h3>
                      <p className="text-sm text-slate-400">{player.position || (player as any).detailed_position || 'Unknown'} • {player.club || (player as any).team || (player as any).team_name || 'Unknown club'}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-xs bg-blue-900/40 text-blue-300 px-2 py-1 rounded">
                          {deriveAge((player as any).age, (player as any).birth_date || (player as any).birthDate) ?? 'Age unavailable'}
                          {typeof deriveAge((player as any).age, (player as any).birth_date || (player as any).birthDate) === 'number' ? ' years' : ''}
                        </span>
                        <span className="text-xs text-slate-400">
                          €{typeof player.marketValue === 'number'
                            ? (player.marketValue / 1000000).toFixed(1)
                            : parseFloat(String(player.marketValue || '0').replace(/[€M,]/g, '')) || '—'}M
                        </span>
                      </div>
                    </div>
                    <Star className="w-4 h-4 text-slate-600 hover:text-yellow-500" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">No players found</h3>
              <p className="text-slate-400">Try adjusting your search criteria</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScoutingDashboard;