import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowLeftRight,
  Award,
  Brain,
  Download,
  Plus,
  RefreshCw,
  Search,
  Shield,
  Target,
  Users,
  X,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { exportService } from '../services/exportService';
import { SimilarPlayer } from '../types/comparison';
import { useData } from '../context/DataContext';
import { usePlayerSequenceCoverage } from '../hooks/usePlayerSequenceCoverage';
import apiService from '../services/api';
import SequenceCoverageBadge from './SequenceCoverageBadge';

type ComparisonRow = {
  name: string;
  values: Array<number | string | null>;
  unit?: string;
  highlightBest?: boolean;
};

type ComparisonSection = {
  name: string;
  metrics: ComparisonRow[];
};

function firstDefinedValue<T>(...values: Array<T | null | undefined | ''>): T | null {
  for (const value of values) {
    if (value !== null && value !== undefined && value !== '') {
      return value as T;
    }
  }

  return null;
}

function unwrapNestedData<T>(payload: unknown): T | null {
  if (payload && typeof payload === 'object' && 'data' in (payload as Record<string, unknown>)) {
    return ((payload as Record<string, unknown>).data ?? null) as T | null;
  }

  return (payload ?? null) as T | null;
}

function buildFallbackSummary(player: any) {
  return {
    goals: toNumericValue(firstDefinedValue(player?.goals, player?.stats?.goals)) || 0,
    assists: toNumericValue(firstDefinedValue(player?.assists, player?.stats?.assists)) || 0,
    appearances: toNumericValue(
      firstDefinedValue(player?.appearances, player?.stats?.appearances, player?.matches_played, player?.matchesPlayed)
    ) || 0,
    passes: toNumericValue(firstDefinedValue(player?.passes, player?.stats?.passes, player?.total_passes)) || 0,
    successfulPasses: toNumericValue(
      firstDefinedValue(
        player?.successful_passes,
        player?.successfulPasses,
        player?.stats?.successful_passes,
        player?.stats?.successfulPasses,
        player?.completed_passes,
        player?.stats?.completed_passes,
      )
    ) || 0,
    passAccuracy: toNumericValue(
      firstDefinedValue(player?.passAccuracy, player?.pass_accuracy, player?.stats?.passAccuracy, player?.stats?.pass_accuracy)
    ) || 0,
    shots: toNumericValue(firstDefinedValue(player?.shots, player?.stats?.shots, player?.total_shots)) || 0,
    rating: toNumericValue(firstDefinedValue(player?.rating, player?.stats?.rating, player?.avg_rating, player?.average_rating)) || 0,
  };
}

function toNumericValue(value: number | string | null | undefined): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function formatMetricValue(value: number | string | null, unit?: string): string {
  if (value === null || value === undefined || value === '') {
    return '-';
  }

  if (typeof value === 'number') {
    const formatted = unit === '%' ? value.toFixed(1) : Number.isInteger(value) ? value.toString() : value.toFixed(1);
    return unit ? `${formatted}${unit}` : formatted;
  }

  return unit && value !== '-' ? `${value}${unit}` : String(value);
}

function getWinningIndexes(values: Array<number | string | null>, highlightBest?: boolean): number[] {
  if (!highlightBest) {
    return [];
  }

  const numericValues = values.map(toNumericValue);
  const validValues = numericValues.filter((value): value is number => value !== null);

  if (validValues.length < 2) {
    return [];
  }

  const bestValue = Math.max(...validValues);
  const worstValue = Math.min(...validValues);
  if (bestValue === worstValue) {
    return [];
  }

  return numericValues.reduce<number[]>((indexes, value, index) => {
    if (value === bestValue) {
      indexes.push(index);
    }
    return indexes;
  }, []);
}

function buildSimilarityProfile(player: any) {
  return {
    id: String(player.id),
    player_id: String(player.id),
    name: player.name,
    position: player.position,
    age: typeof player.age === 'number' ? player.age : toNumericValue(player.age),
    club: player.club,
    nationality: player.nationality,
    goals: toNumericValue(player.goals) || 0,
    assists: toNumericValue(player.assists) || 0,
    appearances: toNumericValue(player.appearances) || 0,
    passAccuracy: toNumericValue(player.passAccuracy) || 0,
    rating: toNumericValue(player.rating) || 0,
    minutesPlayed: toNumericValue(player.minutesPlayed) || 0,
  };
}

function buildComparisonSections(payload: any): ComparisonSection[] {
  const playerEntries = Array.isArray(payload?.players) ? payload.players : [];
  if (playerEntries.length === 0) {
    return [];
  }

  const metricLookup = new Map(
    (Array.isArray(payload?.metrics) ? payload.metrics : []).map((metric: any) => [metric.metric, metric.values || []])
  );

  const profileSection: ComparisonSection = {
    name: 'Profile',
    metrics: [
      {
        name: 'Club',
        values: playerEntries.map((entry: any) => entry.summary?.club || entry.player?.club || '-'),
      },
      {
        name: 'Position',
        values: playerEntries.map((entry: any) => entry.summary?.position || entry.player?.position || '-'),
      },
      {
        name: 'Age',
        values: playerEntries.map((entry: any) => entry.summary?.age ?? entry.player?.age ?? '-'),
      },
      {
        name: 'Appearances',
        values: playerEntries.map((entry: any) => entry.summary?.appearances ?? '-'),
        highlightBest: true,
      },
    ],
  };

  const performanceSection: ComparisonSection = {
    name: 'Performance',
    metrics: [
      {
        name: 'Goals',
        values: metricLookup.get('goals') || playerEntries.map((entry: any) => entry.summary?.goals ?? 0),
        highlightBest: true,
      },
      {
        name: 'Assists',
        values: metricLookup.get('assists') || playerEntries.map((entry: any) => entry.summary?.assists ?? 0),
        highlightBest: true,
      },
    ],
  };

  const distributionSection: ComparisonSection = {
    name: 'Distribution',
    metrics: [
      {
        name: 'Pass Accuracy',
        values: metricLookup.get('passAccuracy') || playerEntries.map((entry: any) => entry.summary?.passAccuracy ?? 0),
        unit: '%',
        highlightBest: true,
      },
    ],
  };

  const sequenceSection: ComparisonSection = {
    name: 'Sequence Play',
    metrics: [
      {
        name: 'Sequences Involved',
        values: metricLookup.get('totalSequences') || playerEntries.map((entry: any) => entry.summary?.totalSequences ?? null),
        highlightBest: true,
      },
      {
        name: 'Direct Attacks',
        values: metricLookup.get('directAttacks') || playerEntries.map((entry: any) => entry.summary?.directAttacks ?? null),
        highlightBest: true,
      },
      {
        name: 'Box Entries',
        values: metricLookup.get('boxEntries') || playerEntries.map((entry: any) => entry.summary?.boxEntries ?? null),
        highlightBest: true,
      },
      {
        name: 'Shot-Ending Sequences',
        values: metricLookup.get('shotEndings') || playerEntries.map((entry: any) => entry.summary?.shotEndings ?? null),
        highlightBest: true,
      },
    ],
  };

  const overallSection: ComparisonSection = {
    name: 'Overall',
    metrics: [
      {
        name: 'Rating',
        values: metricLookup.get('rating') || playerEntries.map((entry: any) => entry.summary?.rating ?? 0),
        highlightBest: true,
      },
    ],
  };

  return [profileSection, performanceSection, distributionSection, sequenceSection, overallSection].filter((section) =>
    section.metrics.some((metric) => metric.values.some((value) => value !== null && value !== undefined && value !== ''))
  );
}

function mapSimilarPlayer(result: any): SimilarPlayer {
  const stats = result?.stats || {};
  const playerId = String(result?.player_id || stats.player_id || stats.id || '');
  const normalizedScore = toNumericValue(result?.similarity_score);
  const similarityScore = normalizedScore === null ? 0 : normalizedScore <= 1 ? Math.round(normalizedScore * 100) : Math.round(normalizedScore);

  return {
    id: playerId,
    name: stats.name || 'Unknown Player',
    position: stats.position || 'Unknown',
    age: toNumericValue(stats.age) || 0,
    club: stats.club || 'Unknown Club',
    nationality: stats.nationality || '',
    similarityScore,
    matchingAttributes: Array.isArray(result?.matching_attributes) ? result.matching_attributes : [],
    image: `https://ui-avatars.com/api/?name=${encodeURIComponent(stats.name || 'ScoutPro Player')}&size=100&background=334155&color=fff`,
  };
}

const PlayerComparison: React.FC = () => {
  const [selectedPlayers, setSelectedPlayers] = useState<any[]>([]);
  const [comparisonPayload, setComparisonPayload] = useState<any>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [showPlayerSelect, setShowPlayerSelect] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [similarPlayers, setSimilarPlayers] = useState<SimilarPlayer[]>([]);
  const [showSimilar, setShowSimilar] = useState(false);

  const { players } = useData();

  const availablePlayers = players.map((p: any) => ({
    id: String(p.id),
    name: p.name,
    position: p.position,
    age: p.age,
    club: p.club,
    nationality: p.nationality,
    ...buildFallbackSummary(p),
    image: p.photo || p.image || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.name)}&size=100&background=334155&color=fff`,
  }));

  const playerLookup = useMemo(
    () => new Map(players.map((player: any) => [String(player.id), player])),
    [players],
  );

  const playerCardLookup = useMemo(
    () => new Map(availablePlayers.map((player) => [player.id, player])),
    [availablePlayers],
  );

  const filteredPlayers = availablePlayers.filter(
    p =>
      !selectedPlayers.find(sp => sp.id === p.id) &&
      (p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.club.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const comparisonCoverageIds = useMemo(
    () => Array.from(new Set([
      ...selectedPlayers.map((player) => String(player.id)),
      ...filteredPlayers.slice(0, 100).map((player) => String(player.id)),
    ])),
    [filteredPlayers, selectedPlayers],
  );

  const { coverageByPlayerId } = usePlayerSequenceCoverage(comparisonCoverageIds);

  const comparedPlayers = useMemo(() => {
    const payloadPlayers = Array.isArray(comparisonPayload?.players) ? comparisonPayload.players : [];
    if (payloadPlayers.length === 0) {
      return selectedPlayers;
    }

    return payloadPlayers.map((entry: any) => {
      const playerId = String(entry.player_id || entry.player?.id || '');
      const fallbackPlayer = playerCardLookup.get(playerId);

      return {
        id: playerId,
        name: entry.player?.name || fallbackPlayer?.name || 'Unknown Player',
        club: entry.summary?.club || entry.player?.club || fallbackPlayer?.club || '-',
        position: entry.summary?.position || entry.player?.position || fallbackPlayer?.position || '-',
        age: entry.summary?.age ?? entry.player?.age ?? fallbackPlayer?.age ?? '-',
        image: fallbackPlayer?.image || `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.player?.name || 'ScoutPro Player')}&size=100&background=334155&color=fff`,
      };
    });
  }, [comparisonPayload, playerCardLookup, selectedPlayers]);

  const comparisonSections = useMemo(
    () => buildComparisonSections(comparisonPayload),
    [comparisonPayload],
  );

  const loadComparison = async (playerIds: string[]) => {
    setComparisonLoading(true);
    setComparisonError(null);

    try {
      const comparisonTargets = playerIds.map((id) => {
        const sourcePlayer = playerLookup.get(id);
        const playerCard = playerCardLookup.get(id) || selectedPlayers.find((player) => String(player.id) === id);

        return {
          comparisonId: id,
          sourcePlayer,
          playerCard,
        };
      });

      const comparisonResponse = await apiService.comparePlayers(playerIds);
      const playerSequencePromises = comparisonTargets.map((target) => apiService.getPlayerSequenceInsights(target.comparisonId));
      const sequenceResponses = await Promise.allSettled(playerSequencePromises);
      const comparisonData = comparisonResponse.success ? comparisonResponse.data : null;
      const payloadPlayers = Array.isArray(comparisonData?.players) ? comparisonData.players : [];
      const metricLookup = new Map(
        (Array.isArray(comparisonData?.metrics) ? comparisonData.metrics : []).map((metric: any) => [metric.metric, metric.values || []])
      );
      
      // Build comparison payload from real data
      const players = comparisonTargets.map((target, idx) => {
        const comparisonEntry = payloadPlayers.find(
          (entry: any) => String(entry.player_id || entry.player?.id || '') === target.comparisonId
        );
        const sequenceResponse = sequenceResponses[idx];
        const sequenceData = sequenceResponse.status === 'fulfilled' && sequenceResponse.value.success
          ? unwrapNestedData<Record<string, any>>(sequenceResponse.value.data)
          : null;
        const sequenceSummary = sequenceData?.summary || null;
        const comparisonSummary = comparisonEntry?.summary || {};
        const fallbackSummary = buildFallbackSummary(target.sourcePlayer || target.playerCard);
        const goals = toNumericValue(firstDefinedValue(comparisonSummary.goals, fallbackSummary.goals)) || 0;
        const assists = toNumericValue(firstDefinedValue(comparisonSummary.assists, fallbackSummary.assists)) || 0;
        const appearances = toNumericValue(
          firstDefinedValue(comparisonSummary.appearances, comparisonSummary.matches_played, fallbackSummary.appearances)
        ) || 0;
        const passes = toNumericValue(firstDefinedValue(comparisonSummary.passes, comparisonSummary.total_passes, fallbackSummary.passes)) || 0;
        const successfulPasses = toNumericValue(
          firstDefinedValue(
            comparisonSummary.successful_passes,
            comparisonSummary.successfulPasses,
            comparisonSummary.completed_passes,
            comparisonSummary.completedPasses,
            fallbackSummary.successfulPasses,
          )
        ) || 0;
        const passAccuracy = toNumericValue(
          firstDefinedValue(comparisonSummary.passAccuracy, comparisonSummary.pass_accuracy, fallbackSummary.passAccuracy)
        );
        const shots = toNumericValue(firstDefinedValue(comparisonSummary.shots, comparisonSummary.total_shots, fallbackSummary.shots)) || 0;
        const rating = toNumericValue(firstDefinedValue(comparisonSummary.rating, comparisonSummary.avg_rating, fallbackSummary.rating)) || 0;
        const hasSequenceData = Number(sequenceSummary?.matchesAnalyzed || 0) > 0;
        const playerCard = target.playerCard;
        
        return {
          player_id: target.comparisonId,
          player: {
            id: target.comparisonId,
            name: comparisonEntry?.player?.name || playerCard?.name || 'Unknown',
            club: comparisonEntry?.player?.club || playerCard?.club || 'Unknown',
            position: comparisonEntry?.player?.position || playerCard?.position || 'Unknown',
            age: comparisonEntry?.player?.age ?? playerCard?.age ?? 0,
          },
          summary: {
            goals,
            assists,
            appearances,
            passes,
            successful_passes: successfulPasses,
            passAccuracy: passAccuracy ?? (passes > 0 ? Math.round((successfulPasses / passes) * 100) : 0),
            shots,
            rating,
            club: comparisonSummary.club || playerCard?.club || 'Unknown',
            position: comparisonSummary.position || playerCard?.position || 'Unknown',
            age: comparisonSummary.age ?? playerCard?.age ?? 0,
            totalSequences: hasSequenceData ? sequenceSummary?.totalSequences ?? 0 : null,
            directAttacks: hasSequenceData ? sequenceSummary?.directAttacks ?? 0 : null,
            boxEntries: hasSequenceData ? sequenceSummary?.boxEntries ?? 0 : null,
            shotEndings: hasSequenceData ? sequenceSummary?.shotEndings ?? 0 : null,
          }
        };
      });

      // Build metrics for comparison
      const metrics = [
        {
          metric: 'goals',
          values: metricLookup.get('goals') || players.map(p => p.summary.goals),
        },
        {
          metric: 'assists',
          values: metricLookup.get('assists') || players.map(p => p.summary.assists),
        },
        {
          metric: 'passAccuracy',
          values: metricLookup.get('passAccuracy') || players.map(p => p.summary.passAccuracy),
        },
        {
          metric: 'shots',
          values: players.map(p => p.summary.shots),
        },
        {
          metric: 'rating',
          values: metricLookup.get('rating') || players.map(p => p.summary.rating),
        },
        {
          metric: 'totalSequences',
          values: players.map(p => p.summary.totalSequences),
        },
        {
          metric: 'directAttacks',
          values: players.map(p => p.summary.directAttacks),
        },
        {
          metric: 'boxEntries',
          values: players.map(p => p.summary.boxEntries),
        },
        {
          metric: 'shotEndings',
          values: players.map(p => p.summary.shotEndings),
        },
      ];

      setComparisonPayload({ players, metrics });
    } catch (error) {
      console.error('Failed to load comparison:', error);
      setComparisonPayload(null);
      setComparisonError(error instanceof Error ? error.message : 'Failed to load player comparison');
    } finally {
      setComparisonLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPlayers.length < 2) {
      setComparisonPayload(null);
      setComparisonError(null);
      return;
    }

    const ids = selectedPlayers.map((player) => player.id);
    void loadComparison(ids);
  }, [playerCardLookup, playerLookup, selectedPlayers]);

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

  const handleFindSimilar = async (playerId: string, advanced: boolean = false) => {
    try {
      const targetPlayer = playerLookup.get(playerId);
      if (!targetPlayer) {
        throw new Error('Target player not found in loaded dataset');
      }

      const candidatePlayers = players
        .filter((player: any) => String(player.id) !== playerId && !selectedPlayers.some((selected) => selected.id === String(player.id)))
        .map(buildSimilarityProfile);

      const response = await apiService.findSimilarPlayers(
        buildSimilarityProfile(targetPlayer),
        candidatePlayers,
        10,
        advanced
      );

      if (!response.success) {
        throw new Error(response.error.message);
      }

      setSimilarPlayers((response.data || []).map(mapSimilarPlayer));
      setShowSimilar(true);
    } catch (error) {
      console.error('Error finding similar players:', error);
      alert(error instanceof Error ? error.message : 'Failed to find similar players');
    }
  };

  const handleExport = async () => {
    if (selectedPlayers.length < 2) {
      alert('Please select at least 2 players to export comparison');
      return;
    }

    try {
      const exportData: any[] = [];

      const comparisonSections = buildComparisonSections(comparisonPayload);

      comparisonSections.forEach(category => {
        category.metrics.forEach(metric => {
          const row: any = {
            Category: category.name,
            Attribute: metric.name,
          };

          selectedPlayers.forEach((player, index) => {
            const value = metric.values[index];
            row[player.name] = typeof value === 'number' ? Number(value.toFixed(1)) : value;
          });

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
      case 'profile':
        return Users;
      case 'performance':
        return Award;
      case 'distribution':
        return Activity;
      case 'overall':
        return Shield;
      default:
        return TrendingUp;
    }
  };

  const getCategoryColor = (category: string): string => {
    switch (category.toLowerCase()) {
      case 'profile':
        return 'text-blue-400';
      case 'performance':
        return 'text-green-400';
      case 'distribution':
        return 'text-purple-400';
      case 'overall':
        return 'text-red-400';
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
                  <div className="mt-2">
                    <SequenceCoverageBadge coverage={coverageByPlayerId[String(player.id)]} compact />
                  </div>
                </div>
              </div>

              <div className="flex space-x-2 mt-2">
                <button
                  onClick={() => handleFindSimilar(player.id)}
                  title="Standard Similarity"
                  className="w-full text-xs text-green-400 hover:bg-slate-700/50 p-1 rounded transition flex items-center justify-center space-x-1"
                >
                  <Target className="h-3 w-3" />
                  <span>Similar</span>
                </button>
                <button
                  onClick={() => handleFindSimilar(player.id, true)}
                  title="Advanced ML (KNN)"
                  className="w-full text-xs text-purple-400 hover:bg-slate-700/50 p-1 rounded transition flex items-center justify-center space-x-1"
                >
                  <Brain className="h-3 w-3" />
                  <span>ML KNN</span>
                </button>
              </div>
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
                  <div className="mt-2 inline-block">
                    <SequenceCoverageBadge coverage={coverageByPlayerId[String(player.id)]} compact />
                  </div>
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
            {comparisonLoading
              ? 'Refreshing backend comparison...'
              : `Comparing ${comparedPlayers.length} players across ${comparisonSections.length} backend sections`}
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleExport}
              disabled={comparisonLoading || comparisonSections.length === 0}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center space-x-2 transition-colors"
            >
              <Download className="h-4 w-4" />
              <span className="text-sm">Export</span>
            </button>
            <button
              onClick={() => void loadComparison(selectedPlayers.map((player) => player.id))}
              disabled={comparisonLoading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white rounded-lg flex items-center space-x-2 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${comparisonLoading ? 'animate-spin' : ''}`} />
              <span className="text-sm">Refresh Comparison</span>
            </button>
          </div>
        </div>
      )}

      {comparisonError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-sm text-red-300">
          {comparisonError}
        </div>
      )}

      {/* Comparison Table */}
      {selectedPlayers.length >= 2 && comparisonSections.length > 0 && (
        <div className="space-y-6">
          {comparisonSections.map((category, idx) => {
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
                        {comparedPlayers.map((player, pIdx) => (
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
                      {category.metrics.map((metric, mIdx) => {
                        const winningIndexes = getWinningIndexes(metric.values, metric.highlightBest);

                        return (
                          <tr key={mIdx} className="border-b border-slate-700 hover:bg-slate-700/30">
                            <td className="px-4 py-3 text-sm text-slate-300 font-medium sticky left-0 bg-slate-800">
                              {metric.name}
                            </td>
                            {metric.values.map((value, valueIndex) => {
                              const isWinner = winningIndexes.includes(valueIndex);

                              return (
                                <td key={`${metric.name}-${valueIndex}`} className="px-4 py-3 text-center">
                                  <div className="flex flex-col items-center">
                                    <span className={`text-sm font-semibold ${isWinner ? 'text-green-400' : 'text-white'}`}>
                                      {formatMetricValue(value, metric.unit)}
                                    </span>
                                    {isWinner && <TrendingUp className="h-3 w-3 text-green-400 mt-0.5" />}
                                  </div>
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
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
