import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  BarChart3,
  Users,
  Target,
  Zap,
  RefreshCw,
  Loader2,
  Plus,
  Search,
  X,
  ChevronDown,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import type { MatchFilters } from '../types';
import { hasReliableLiveContext, normalizeMatchStatus, resolveTeamName } from '../utils/dataTransformers';

const toNumber = (value: unknown): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const analysisMatchFilters: MatchFilters & { limit: number } = {
  status: ['finished'],
  limit: 200,
};

const formatDate = (value?: string): string => {
  if (!value) {
    return 'No date';
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString();
};

const compareAnalysisMatches = (
  left: { status: string; homeScore: number; awayScore: number; home: string; away: string; rawDate: string },
  right: { status: string; homeScore: number; awayScore: number; home: string; away: string; rawDate: string },
): number => {
  const leftHasGoals = left.homeScore + left.awayScore > 0;
  const rightHasGoals = right.homeScore + right.awayScore > 0;
  if (leftHasGoals !== rightHasGoals) {
    return Number(rightHasGoals) - Number(leftHasGoals);
  }

  const statusPriority = (status: string): number => {
    if (status === 'finished') return 2;
    if (status === 'live' || status === 'in_progress') return 1;
    return 0;
  };

  const statusDiff = statusPriority(right.status) - statusPriority(left.status);
  if (statusDiff !== 0) {
    return statusDiff;
  }

  const hasResolvedTeams = (home: string, away: string): boolean => {
    const placeholderPattern = /^team\s+\d+$/i;
    return !placeholderPattern.test(home) && !placeholderPattern.test(away);
  };

  const teamDiff = Number(hasResolvedTeams(right.home, right.away)) - Number(hasResolvedTeams(left.home, left.away));
  if (teamDiff !== 0) {
    return teamDiff;
  }

  const leftTimestamp = new Date(left.rawDate).getTime();
  const rightTimestamp = new Date(right.rawDate).getTime();

  return (Number.isFinite(rightTimestamp) ? rightTimestamp : 0) - (Number.isFinite(leftTimestamp) ? leftTimestamp : 0);
};

type AnalysisMatchRecord = {
  id: string;
  uiKey: string;
  home: string;
  away: string;
  date: string;
  rawDate: string;
  status: string;
  competition: string;
  homeScore: number;
  awayScore: number;
};

const MultiMatchAnalysis: React.FC = () => {
  const [selectedMatches, setSelectedMatches] = useState<string[]>([]);
  const [analysisType, setAnalysisType] = useState('comparative');
  const [showMatchPicker, setShowMatchPicker] = useState(false);
  const [matchSearchQuery, setMatchSearchQuery] = useState('');
  const [appliedAnalysis, setAppliedAnalysis] = useState<{ matchIds: string[]; analysisType: string } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const pickerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { matches, teams } = useData();
  const { data: analysisMatchesData, loading: analysisMatchesLoading, refetch: refetchAnalysisMatches } = useApi(
    () => apiService.getMatches(analysisMatchFilters),
    [],
  );
  const { data: overviewData, loading: overviewLoading, refetch: refetchOverview } = useApi(
    () => apiService.getDashboardOverview(),
    [],
  );
  const { data: trendData, loading: trendsLoading, refetch: refetchTrends } = useApi(
    () => apiService.getLeagueTrends(),
    [],
  );

  const availableMatches = useMemo(
    () => {
      const matchPool = analysisMatchesData && analysisMatchesData.length > 0 ? analysisMatchesData : matches;
      const normalizedMatches = matchPool
        .map((match: any, index: number) => {
          const status = normalizeMatchStatus(match.status, match.date, match.homeScore, match.awayScore);
          const reliableLive = hasReliableLiveContext(match, teams);

          if (status === 'live' && !reliableLive) {
            return null;
          }

          return {
            id: String(match.id),
            uiKey: `${match.id || 'match'}-${index}`,
            home: resolveTeamName(match.homeTeam || match.home_team, match.homeTeamId || match.home_team_id, teams, 'Home'),
            away: resolveTeamName(match.awayTeam || match.away_team, match.awayTeamId || match.away_team_id, teams, 'Away'),
            date: formatDate(match.date),
            rawDate: match.date,
            status,
            competition: match.competition || 'Turkish Süper Lig',
            homeScore: toNumber(match.homeScore),
            awayScore: toNumber(match.awayScore),
          };
        })
        .filter(Boolean) as AnalysisMatchRecord[];

      normalizedMatches.sort(compareAnalysisMatches);
      return normalizedMatches;
    },
    [analysisMatchesData, matches, teams],
  );

  useEffect(() => {
    setSelectedMatches((previous) => previous.filter((matchId) => availableMatches.some((match) => match.id === matchId)));
  }, [availableMatches]);

  // Close picker when clicking outside
  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        setShowMatchPicker(false);
      }
    };
    if (showMatchPicker) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [showMatchPicker]);

  // Focus search when picker opens
  useEffect(() => {
    if (showMatchPicker) {
      setTimeout(() => searchInputRef.current?.focus(), 50);
    } else {
      setMatchSearchQuery('');
    }
  }, [showMatchPicker]);

  useEffect(() => {
    setAppliedAnalysis((previous) => {
      if (!previous) {
        return previous;
      }

      const validMatchIds = previous.matchIds.filter((matchId) => availableMatches.some((match) => match.id === matchId));
      if (validMatchIds.length === 0) {
        return null;
      }

      if (validMatchIds.length === previous.matchIds.length) {
        return previous;
      }

      return {
        ...previous,
        matchIds: validMatchIds,
      };
    });
  }, [availableMatches]);

  const availableMatchLookup = useMemo(
    () => new Map(availableMatches.map((match) => [match.id, match])),
    [availableMatches],
  );

  const selectedMatchCards = useMemo(
    () => selectedMatches
      .map((matchId) => availableMatchLookup.get(matchId))
      .filter(Boolean) as AnalysisMatchRecord[],
    [availableMatchLookup, selectedMatches],
  );

  const pickerMatches = useMemo(() => {
    const normalizedQuery = matchSearchQuery.trim().toLowerCase();
    // Search across ALL available matches — no year/league pre-filter
    const pool = normalizedQuery.length === 0
      ? availableMatches
      : availableMatches.filter((match) => {
        const text = `${match.home} ${match.away} ${match.competition} ${match.date} ${match.rawDate ?? ''}`.toLowerCase();
        return text.includes(normalizedQuery);
      });
    // Put already-selected ones first so they're easy to deselect
    const selected = pool.filter((m) => selectedMatches.includes(m.id));
    const unselected = pool.filter((m) => !selectedMatches.includes(m.id));
    return [...selected, ...unselected].slice(0, 50);
  }, [availableMatches, matchSearchQuery, selectedMatches]);

  const openPicker = useCallback(() => setShowMatchPicker(true), []);
  const closePicker = useCallback(() => setShowMatchPicker(false), []);

  const appliedMatchIds = appliedAnalysis?.matchIds ?? [];
  const appliedAnalysisType = appliedAnalysis?.analysisType ?? analysisType;

  const summary = overviewData?.summary || overviewData?.data || {};
  const predictionSummary = overviewData?.predictions || {};
  const selectedMatchRecords = useMemo(
    () => appliedMatchIds
      .map((matchId) => availableMatchLookup.get(matchId))
      .filter(Boolean) as AnalysisMatchRecord[],
    [appliedMatchIds, availableMatchLookup],
  );
  const averageGoals = selectedMatchRecords.length > 0
    ? selectedMatchRecords.reduce((sum, match) => sum + match.homeScore + match.awayScore, 0) / selectedMatchRecords.length
    : 0;
  const averageGoalMargin = selectedMatchRecords.length > 0
    ? selectedMatchRecords.reduce((sum, match) => sum + Math.abs(match.homeScore - match.awayScore), 0) / selectedMatchRecords.length
    : 0;
  const homeWins = selectedMatchRecords.filter((match) => match.homeScore > match.awayScore).length;
  const draws = selectedMatchRecords.filter((match) => match.homeScore === match.awayScore).length;
  const highScoringMatches = selectedMatchRecords.filter((match) => match.homeScore + match.awayScore >= 3).length;
  const liveSelections = selectedMatchRecords.filter((match) => ['live', 'in_progress'].includes(String(match.status).toLowerCase())).length;

  const patterns = useMemo(() => {
    const baseline = toNumber(summary.avgGoalsPerMatch);

    return ((trendData?.trends || []) as any[]).slice(-4).map((trend) => ({
      pattern: `${trend.name} scoring trend`,
      frequency: `${toNumber(trend.matchCount)} matches`,
      impact: toNumber(trend.avgGoals) >= baseline ? 'High' : 'Medium',
      trend: toNumber(trend.avgGoals) > baseline ? 'increasing' : toNumber(trend.avgGoals) < baseline ? 'decreasing' : 'stable',
    }));
  }, [summary.avgGoalsPerMatch, trendData]);

  const keyInsights = useMemo(() => {
    if (selectedMatchRecords.length === 0) {
      return [];
    }

    const baseline = toNumber(summary.avgGoalsPerMatch);
    const homeWinRate = selectedMatchRecords.length > 0 ? Math.round((homeWins / selectedMatchRecords.length) * 100) : 0;
    const drawRate = selectedMatchRecords.length > 0 ? Math.round((draws / selectedMatchRecords.length) * 100) : 0;

    return [
      `${selectedMatchRecords.length} selected matches average ${averageGoals.toFixed(2)} goals per game.`,
      `Home sides won ${homeWinRate}% of the sample, with draws in ${drawRate}% of fixtures.`,
      baseline > 0
        ? `This ${appliedAnalysisType} view is ${averageGoals >= baseline ? 'above' : 'below'} the league baseline of ${baseline.toFixed(2)} goals per match.`
        : 'League baseline metrics are still loading from analytics-service.',
      liveSelections > 0
        ? `${liveSelections} selected fixtures are currently live or in progress.`
        : 'No selected fixtures are currently live.',
    ];
  }, [appliedAnalysisType, averageGoals, draws, homeWins, liveSelections, selectedMatchRecords, summary.avgGoalsPerMatch]);

  const playerOutput = useMemo(
    () => ((overviewData?.topPlayers || []) as any[]).slice(0, 6).map((player, index) => ({
      id: String(player.playerID || ''),
      uiKey: `${player.playerID || player.player_name || 'player'}-${index}`,
      name: player.player_name || `Player #${player.playerID}`,
      rank: player.rank || '—',
      matches: Array.isArray(player.matchIDs) ? player.matchIDs.length : 0,
      goals: toNumber(player.goals),
      shots: toNumber(player.shots),
      completedPasses: toNumber(player.passes_completed),
      duelWinRate: player.duels ? Math.round((toNumber(player.duels_won) / Math.max(toNumber(player.duels), 1)) * 100) : 0,
    })),
    [overviewData],
  );

  const applyAnalysis = async () => {
    if (selectedMatches.length === 0) {
      return;
    }

    setIsAnalyzing(true);
    try {
      await Promise.all([refetchAnalysisMatches(), refetchOverview(), refetchTrends()]);
      setAppliedAnalysis({
        matchIds: [...selectedMatches],
        analysisType,
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const analysisLoading = analysisMatchesLoading || overviewLoading || trendsLoading || isAnalyzing;

  const toggleMatchSelection = useCallback((matchId: string) => {
    setSelectedMatches((previous) => (
      previous.includes(matchId)
        ? previous.filter((id) => id !== matchId)
        : [...previous, matchId]
    ));
  }, []);

  const hasAppliedSelection = selectedMatchRecords.length > 0;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <BarChart3 className="h-8 w-8 mr-3 text-blue-500" />
          Multi-Match Analysis
        </h1>
        <p className="text-slate-400 text-sm">{availableMatches.length} matches available</p>
      </div>

      {/* ── Match Selection Bar (mirrors PlayerComparison layout) ─────────── */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4" ref={pickerRef}>

        {/* Chip row — scrollable horizontally, never overflows vertically */}
        <div className="flex items-center gap-3 flex-wrap">
          {selectedMatchCards.map((match) => (
            <div
              key={match.uiKey}
              className="flex-shrink-0 bg-slate-700 rounded-lg px-3 py-2 min-w-[170px] max-w-[220px] relative group"
            >
              <button
                onClick={() => toggleMatchSelection(match.id)}
                className="absolute -top-1.5 -right-1.5 p-0.5 bg-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="h-3 w-3 text-white" />
              </button>
              <div className="text-xs text-slate-400 truncate">{match.competition}</div>
              <div className="text-sm font-semibold text-white leading-tight mt-0.5 truncate">
                {match.home} <span className="text-slate-400">vs</span> {match.away}
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-slate-400">{match.date}</span>
                <span className="text-sm font-bold text-green-400">{match.homeScore}–{match.awayScore}</span>
              </div>
            </div>
          ))}

          {/* Add Match button — no relative wrapper, no absolute child */}
          <button
            onClick={showMatchPicker ? closePicker : openPicker}
            className="flex-shrink-0 min-w-[120px] h-[76px] border-2 border-dashed border-slate-600 rounded-lg flex flex-col items-center justify-center space-y-1 hover:border-blue-500 hover:bg-slate-700/30 transition-all group"
          >
            <Plus className="h-6 w-6 text-slate-600 group-hover:text-blue-400" />
            <span className="text-xs text-slate-600 group-hover:text-blue-400">Add Match</span>
          </button>

          {selectedMatchCards.length > 0 && (
            <button
              onClick={() => setSelectedMatches([])}
              className="flex-shrink-0 text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded"
            >
              Clear all
            </button>
          )}
        </div>

        {/* Full-width picker panel — rendered as a normal block below the chip row */}
        {showMatchPicker && (
          <div className="mt-4 rounded-xl border border-slate-600 bg-slate-900/60">
            {/* Search bar — spans full card width */}
            <div className="p-3 border-b border-slate-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={matchSearchQuery}
                  onChange={(e) => setMatchSearchQuery(e.target.value)}
                  placeholder="Search team, league, year…"
                  className="w-full rounded-lg border border-slate-600 bg-slate-700 py-2.5 pl-9 pr-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Match grid */}
            <div className="max-h-96 overflow-y-auto p-3">
              {pickerMatches.length === 0 ? (
                <div className="py-8 text-center text-sm text-slate-400">No matches found</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {pickerMatches.map((match) => {
                    const isSelected = selectedMatches.includes(match.id);
                    return (
                      <button
                        key={match.uiKey}
                        onClick={() => toggleMatchSelection(match.id)}
                        className={`flex items-center justify-between rounded-lg px-3 py-2.5 text-left transition-colors border ${
                          isSelected
                            ? 'border-blue-500 bg-blue-500/15'
                            : 'border-slate-700 bg-slate-800 hover:bg-slate-700'
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="text-sm font-medium text-white truncate">
                              {match.home} <span className="text-slate-400">vs</span> {match.away}
                            </span>
                            {isSelected && (
                              <span className="flex-shrink-0 px-1.5 py-0.5 text-xs bg-blue-500 text-white rounded">✓</span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5 mt-0.5 text-xs text-slate-400 truncate">
                            <span className="truncate">{match.competition}</span>
                            <span>·</span>
                            <span className="flex-shrink-0">{match.date}</span>
                          </div>
                        </div>
                        <span className="ml-2 flex-shrink-0 text-sm font-bold text-green-400">
                          {match.homeScore}–{match.awayScore}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="px-4 py-2 border-t border-slate-700 flex items-center justify-between">
              <span className="text-xs text-slate-500">{pickerMatches.length} shown · {availableMatches.length} total</span>
              <button onClick={closePicker} className="text-xs text-slate-400 hover:text-white transition-colors">Done</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Analysis Type + Apply ─────────────────────────────────────────── */}
      {selectedMatchCards.length > 0 && (
        <div className="flex items-center justify-between bg-slate-800 border border-slate-700 rounded-lg px-5 py-4">
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-slate-300 whitespace-nowrap">Analysis type</label>
            <div className="relative">
              <select
                value={analysisType}
                onChange={(e) => setAnalysisType(e.target.value)}
                className="appearance-none pl-3 pr-8 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="comparative">Comparative</option>
                <option value="trend">Trend</option>
                <option value="pattern">Pattern Recognition</option>
                <option value="predictive">Predictive</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            </div>
            <span className="text-sm text-slate-400">{selectedMatchCards.length} match{selectedMatchCards.length !== 1 ? 'es' : ''} selected</span>
          </div>
          <button
            onClick={applyAnalysis}
            disabled={analysisLoading}
            className="flex items-center space-x-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 rounded-lg transition-colors text-sm font-medium"
          >
            {analysisLoading ? (
              <><Loader2 className="h-4 w-4 animate-spin" /><span>Applying…</span></>
            ) : (
              <><RefreshCw className="h-4 w-4" /><span>Apply Analysis</span></>
            )}
          </button>
        </div>
      )}



      {!hasAppliedSelection && (
        <div className="rounded-xl border border-slate-700 bg-slate-800 px-6 py-8 text-center text-slate-300">
          Select matches, choose an analysis type, then click Apply Analysis to generate results.
        </div>
      )}

      {hasAppliedSelection && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <Target className="h-6 w-6 mr-2 text-purple-400" />
              Pattern Recognition
            </h3>
            {patterns.length > 0 ? (
              <div className="space-y-4">
                {patterns.map((pattern, index) => (
                  <div key={index} className="p-4 bg-slate-700 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">{pattern.pattern}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          pattern.impact === 'High' ? 'bg-red-600 text-red-100' : 'bg-yellow-600 text-yellow-100'
                        }`}>
                          {pattern.impact}
                        </span>
                        <span className={`text-sm ${
                          pattern.trend === 'increasing' ? 'text-green-400' : pattern.trend === 'decreasing' ? 'text-red-400' : 'text-slate-400'
                        }`}>
                          {pattern.trend === 'increasing' ? '↗' : pattern.trend === 'decreasing' ? '↘' : '→'}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-sm">Frequency</span>
                      <span className="font-bold text-blue-400">{pattern.frequency}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                Trend-based pattern data is not available from analytics-service yet.
              </div>
            )}
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <Zap className="h-6 w-6 mr-2 text-yellow-400" />
              Key Insights
            </h3>
            <div className="space-y-4">
              {keyInsights.map((insight, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-yellow-600 rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>
                    <p className="text-sm text-slate-300 flex-1">{insight}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {hasAppliedSelection && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Users className="h-6 w-6 mr-2 text-green-400" />
            Cross-Match Player Output
          </h3>
          {playerOutput.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-2">Player</th>
                    <th className="text-left py-3 px-2">Rank</th>
                    <th className="text-left py-3 px-2">Matches</th>
                    <th className="text-left py-3 px-2">Goals</th>
                    <th className="text-left py-3 px-2">Shots</th>
                    <th className="text-left py-3 px-2">Completed Passes</th>
                    <th className="text-left py-3 px-2">Duel Win %</th>
                  </tr>
                </thead>
                <tbody>
                  {playerOutput.map((player) => (
                    <tr key={player.uiKey} className="border-b border-slate-700 hover:bg-slate-700">
                      <td className="py-3 px-2 font-semibold">{player.name}</td>
                      <td className="py-3 px-2 text-blue-400">#{player.rank}</td>
                      <td className="py-3 px-2">{player.matches}</td>
                      <td className="py-3 px-2">{player.goals}</td>
                      <td className="py-3 px-2">{player.shots}</td>
                      <td className="py-3 px-2">{player.completedPasses}</td>
                      <td className="py-3 px-2">
                        <span className="font-semibold text-green-400">{player.duelWinRate}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
              Player output rankings are not available from the backend yet.
            </div>
          )}
        </div>
      )}

      {hasAppliedSelection && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Tactical Evolution</h3>
            <div className="space-y-4">
              <div className="p-3 bg-slate-700 rounded">
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Average Goals</span>
                  <span className="text-green-400 font-bold">{averageGoals.toFixed(2)}</span>
                </div>
                <div className="text-xs text-slate-400">Across the selected backend match sample</div>
              </div>
              <div className="p-3 bg-slate-700 rounded">
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Home Win Rate</span>
                  <span className="text-blue-400 font-bold">{selectedMatchRecords.length > 0 ? Math.round((homeWins / selectedMatchRecords.length) * 100) : 0}%</span>
                </div>
                <div className="text-xs text-slate-400">Home-side success rate in the chosen window</div>
              </div>
              <div className="p-3 bg-slate-700 rounded">
                <div className="flex justify-between mb-1">
                  <span className="text-sm">High-Scoring Share</span>
                  <span className="text-yellow-400 font-bold">{selectedMatchRecords.length > 0 ? Math.round((highScoringMatches / selectedMatchRecords.length) * 100) : 0}%</span>
                </div>
                <div className="text-xs text-slate-400">Matches with 3+ total goals</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Match Momentum</h3>
            <div className="space-y-4">
              <div className="p-3 bg-slate-700 rounded">
                <div className="text-sm font-medium mb-2">Goal Margin</div>
                <div className="text-xs text-slate-400 mb-2">Average score differential</div>
                <div className="text-2xl font-bold text-red-400">{averageGoalMargin.toFixed(2)}</div>
              </div>
              <div className="p-3 bg-slate-700 rounded">
                <div className="text-sm font-medium mb-2">Draw Rate</div>
                <div className="text-xs text-slate-400 mb-2">Share of level scorelines</div>
                <div className="text-2xl font-bold text-purple-400">{selectedMatchRecords.length > 0 ? Math.round((draws / selectedMatchRecords.length) * 100) : 0}%</div>
              </div>
              <div className="p-3 bg-slate-700 rounded">
                <div className="text-sm font-medium mb-2">Live Fixtures</div>
                <div className="text-xs text-slate-400 mb-2">Currently active in this selection</div>
                <div className="text-2xl font-bold text-green-400">{liveSelections}</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Predictive Insights</h3>
            <div className="space-y-4">
              <div className="p-3 bg-green-600/10 border border-green-600/20 rounded">
                <div className="text-sm font-medium text-green-400 mb-1">Prediction Volume</div>
                <div className="text-xs text-slate-300">{predictionSummary.total || summary.transferPredictions || 0} active prediction records available in the backend snapshot.</div>
              </div>
              <div className="p-3 bg-yellow-600/10 border border-yellow-600/20 rounded">
                <div className="text-sm font-medium text-yellow-400 mb-1">Accuracy Score</div>
                <div className="text-xs text-slate-300">Current model accuracy reading: {predictionSummary.accuracy || summary.modelAccuracy || '—'}.</div>
              </div>
              <div className="p-3 bg-blue-600/10 border border-blue-600/20 rounded">
                <div className="text-sm font-medium text-blue-400 mb-1">Trend Alert</div>
                <div className="text-xs text-slate-300">Competition baseline sits at {toNumber(summary.avgGoalsPerMatch).toFixed(2)} goals per match across {summary.totalMatches || 0} fixtures.</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiMatchAnalysis;
