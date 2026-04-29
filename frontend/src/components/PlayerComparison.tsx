import React, { useState, useEffect } from 'react';
import {
  Users,
  X,
  Plus,
  TrendingUp,
  TrendingDown,
  Minus,
  Download,
  Save,
  Search,
  ArrowLeftRight,
  Target,
  Activity,
  Award,
  Shield,
  Zap,
} from 'lucide-react';
import { comparisonService } from '../services/comparisonService';
import { exportService } from '../services/exportService';
import { ComparisonCategory, SimilarPlayer } from '../types/comparison';
import { useData } from '../context/DataContext';
import apiService from '../services/api';

const PlayerComparison: React.FC = () => {
  const [selectedPlayers, setSelectedPlayers] = useState<any[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonCategory[]>([]);
  const [showPlayerSelect, setShowPlayerSelect] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [similarPlayers, setSimilarPlayers] = useState<SimilarPlayer[]>([]);
  const [showSimilar, setShowSimilar] = useState(false);
  const [apiComparisonData, setApiComparisonData] = useState<any>(null);
  const [radarAttributes, setRadarAttributes] = useState<string[]>([
    'passing',
    'dribbling',
    'shooting',
    'speed',
    'stamina',
    'tackling',
  ]);

  // Use real player data from context
  const { players } = useData();

  // Map real players for selection
  const availablePlayers = players.map((p: any) => ({
    id: String(p.id),
    name: p.name,
    position: p.position,
    age: p.age,
    club: p.club,
    nationality: p.nationality,
    image: p.photo || p.image || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.name)}&size=100&background=334155&color=fff`,
  }));

  const filteredPlayers = availablePlayers.filter(
    p =>
      !selectedPlayers.find(sp => sp.id === p.id) &&
      (p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.club.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  useEffect(() => {
    if (selectedPlayers.length >= 2) {
      // Use local comparison service
      const data = comparisonService.comparePlayers(selectedPlayers);
      setComparisonData(data);
      
      // Also fetch API comparison data
      const ids = selectedPlayers.map(p => p.id);
      apiService.comparePlayers(ids).then(res => {
        if (res.success && res.data) {
          setApiComparisonData(res.data);
        }
      }).catch(() => {});
    }
  }, [selectedPlayers]);

  const handleAddPlayer = (player: any) => {
    if (selectedPlayers.length < 6) {
      setSelectedPlayers([...selectedPlayers, player]);
      setSearchQuery('');
      if (selectedPlayers.length === 0) {
        setShowPlayerSelect(true);
      }
    }
  };

  const handleRemovePlayer = (playerId: string) => {
    setSelectedPlayers(selectedPlayers.filter(p => p.id !== playerId));
  };

  const handleFindSimilar = async (playerId: string) => {
    try {
      const similar = await comparisonService.findSimilarPlayers({
        playerId,
        limit: 10,
        minSimilarity: 60,
      });
      setSimilarPlayers(similar);
      setShowSimilar(true);
    } catch (error) {
      console.error('Error finding similar players:', error);
    }
  };

  const handleExport = async () => {
    if (selectedPlayers.length < 2) {
      alert('Please select at least 2 players to export comparison');
      return;
    }

    try {
      // Flatten comparison data for export
      const exportData: any[] = [];

      comparisonData.forEach(category => {
        category.metrics.forEach(metric => {
          const row: any = {
            Category: category.name,
            Attribute: metric.name,
          };

          // Add columns for each player dynamically
          selectedPlayers.forEach((player, idx) => {
            const value = idx === 0 ? metric.player1Value : metric.player2Value;
            row[player.name] = typeof value === 'number' ? Math.round(value) : value;
          });

          if (selectedPlayers.length === 2) {
            row.Difference = metric.difference ? metric.difference.toFixed(1) : '-';
            row.Winner = metric.winner === 'player1' ? selectedPlayers[0].name :
                        metric.winner === 'player2' ? selectedPlayers[1].name : 'Tie';
          }

          exportData.push(row);
        });
      });

      const playerNames = selectedPlayers.map(p => p.name).join(' vs ');

      await exportService.export({
        format: 'pdf',
        fileName: `player_comparison_${selectedPlayers.map(p => p.name.replace(/\s+/g, '_')).join('_vs_')}.pdf`,
        data: exportData,
        header: `Player Comparison: ${playerNames}`,
        branding: {
          companyName: 'ScoutPro',
          colors: {
            primary: '#10b981',
          },
        },
      });

      alert('Comparison exported to PDF successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  const getMetricIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'physical':
        return Activity;
      case 'technical':
        return Target;
      case 'mental':
        return Zap;
      case 'defensive':
        return Shield;
      case 'performance':
        return Award;
      default:
        return TrendingUp;
    }
  };

  const getCategoryColor = (category: string): string => {
    switch (category.toLowerCase()) {
      case 'physical':
        return 'text-blue-400';
      case 'technical':
        return 'text-green-400';
      case 'mental':
        return 'text-purple-400';
      case 'defensive':
        return 'text-red-400';
      case 'performance':
        return 'text-yellow-400';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Player Comparison</h1>
        <p className="text-slate-400">
          Compare up to 6 players side-by-side across multiple attributes
        </p>
      </div>

      {/* Player Selection Bar */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center space-x-4 overflow-x-auto pb-2">
          {selectedPlayers.map((player, index) => (
            <div
              key={player.id}
              className="flex-shrink-0 bg-slate-700 rounded-lg p-3 min-w-[200px] relative group"
            >
              <button
                onClick={() => handleRemovePlayer(player.id)}
                className="absolute -top-2 -right-2 p-1 bg-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="h-3 w-3 text-white" />
              </button>

              <div className="flex items-center space-x-3">
                {player.image ? (
                  <img
                    src={player.image}
                    alt={player.name}
                    className="w-12 h-12 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-slate-600 flex items-center justify-center">
                    <Users className="h-6 w-6 text-slate-400" />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <h3 className="text-white font-medium text-sm truncate">{player.name}</h3>
                  <p className="text-xs text-slate-400">{player.club}</p>
                  <p className="text-xs text-slate-500">{player.position} • {player.age}y</p>
                </div>
              </div>

              <button
                onClick={() => handleFindSimilar(player.id)}
                className="mt-2 w-full text-xs text-green-400 hover:text-green-300 flex items-center justify-center space-x-1"
              >
                <Target className="h-3 w-3" />
                <span>Find Similar</span>
              </button>
            </div>
          ))}

          {selectedPlayers.length < 6 && (
            <button
              onClick={() => setShowPlayerSelect(!showPlayerSelect)}
              className="flex-shrink-0 min-w-[200px] h-[120px] border-2 border-dashed border-slate-600 rounded-lg flex flex-col items-center justify-center space-y-2 hover:border-green-500 hover:bg-slate-700/30 transition-all group"
            >
              <Plus className="h-8 w-8 text-slate-600 group-hover:text-green-500" />
              <span className="text-sm text-slate-600 group-hover:text-green-500">
                Add Player
              </span>
            </button>
          )}
        </div>

        {/* Player Search */}
        {showPlayerSelect && (
          <div className="mt-4 pt-4 border-t border-slate-700">
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search players..."
                className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                autoFocus
              />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-[300px] overflow-y-auto">
              {filteredPlayers.map(player => (
                <button
                  key={player.id}
                  onClick={() => handleAddPlayer(player)}
                  className="p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-left transition-colors"
                >
                  <p className="text-white text-sm font-medium truncate">{player.name}</p>
                  <p className="text-xs text-slate-400">{player.club}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      {selectedPlayers.length >= 2 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Comparing {selectedPlayers.length} players across {comparisonData.length} categories
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center space-x-2 transition-colors"
            >
              <Download className="h-4 w-4" />
              <span className="text-sm">Export</span>
            </button>
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center space-x-2 transition-colors">
              <Save className="h-4 w-4" />
              <span className="text-sm">Save Comparison</span>
            </button>
          </div>
        </div>
      )}

      {/* Comparison Table */}
      {selectedPlayers.length >= 2 && comparisonData.length > 0 && (
        <div className="space-y-6">
          {comparisonData.map((category, idx) => {
            const Icon = getMetricIcon(category.name);
            const colorClass = getCategoryColor(category.name);

            return (
              <div key={idx} className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-slate-700/50 border-b border-slate-700 flex items-center space-x-2">
                  <Icon className={`h-5 w-5 ${colorClass}`} />
                  <h3 className="text-lg font-semibold text-white">{category.name}</h3>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="px-4 py-3 text-left text-sm font-medium text-slate-400 sticky left-0 bg-slate-800">
                          Attribute
                        </th>
                        {selectedPlayers.map((player, pIdx) => (
                          <th
                            key={pIdx}
                            className="px-4 py-3 text-center text-sm font-medium text-white min-w-[120px]"
                          >
                            {player.name.split(' ')[0]}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {category.metrics.map((metric, mIdx) => (
                        <tr key={mIdx} className="border-b border-slate-700 hover:bg-slate-700/30">
                          <td className="px-4 py-3 text-sm text-slate-300 font-medium sticky left-0 bg-slate-800">
                            {metric.name}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="flex flex-col items-center">
                              <span
                                className={`text-sm font-semibold ${
                                  metric.winner === 'player1' ? 'text-green-400' : 'text-white'
                                }`}
                              >
                                {typeof metric.player1Value === 'number'
                                  ? Math.round(metric.player1Value)
                                  : metric.player1Value}
                                {metric.unit && <span className="text-xs ml-0.5">{metric.unit}</span>}
                              </span>
                              {metric.winner === 'player1' && (
                                <TrendingUp className="h-3 w-3 text-green-400 mt-0.5" />
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="flex flex-col items-center">
                              <span
                                className={`text-sm font-semibold ${
                                  metric.winner === 'player2' ? 'text-green-400' : 'text-white'
                                }`}
                              >
                                {typeof metric.player2Value === 'number'
                                  ? Math.round(metric.player2Value)
                                  : metric.player2Value}
                                {metric.unit && <span className="text-xs ml-0.5">{metric.unit}</span>}
                              </span>
                              {metric.winner === 'player2' && (
                                <TrendingUp className="h-3 w-3 text-green-400 mt-0.5" />
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty State */}
      {selectedPlayers.length < 2 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
          <ArrowLeftRight className="h-16 w-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Players Selected</h3>
          <p className="text-slate-400 mb-6">
            Add at least 2 players to start comparing their attributes
          </p>
          <button
            onClick={() => setShowPlayerSelect(true)}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
          >
            Select Players
          </button>
        </div>
      )}

      {/* Similar Players Modal */}
      {showSimilar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between sticky top-0 bg-slate-800">
              <h3 className="text-lg font-semibold text-white">Similar Players</h3>
              <button
                onClick={() => setShowSimilar(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              {similarPlayers.map(player => (
                <div
                  key={player.id}
                  className="bg-slate-700 rounded-lg p-4 hover:bg-slate-600 transition-colors cursor-pointer"
                  onClick={() => {
                    handleAddPlayer(player);
                    setShowSimilar(false);
                  }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="text-white font-medium">{player.name}</h4>
                      <p className="text-sm text-slate-400">{player.club}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-green-400 font-semibold">
                        {player.similarityScore}%
                      </div>
                      <div className="text-xs text-slate-500">Match</div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1">
                    {player.matchingAttributes.slice(0, 5).map((attr, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-slate-800 text-xs text-slate-300 rounded"
                      >
                        {attr}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerComparison;
