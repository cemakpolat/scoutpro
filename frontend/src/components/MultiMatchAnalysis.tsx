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
  limit: 100,
};

// Extracts a plain date string from either a regular string or an Opta XML-style
// object: { "@value": "2020-07-26 16:00:00", "@attributes": { "TBC": "1" } }
const extractRawDateString = (value: unknown): string => {
  if (!value) return '';
  if (typeof value === 'object' && value !== null && '@value' in (value as Record<string, unknown>)) {
    const inner = (value as Record<string, unknown>)['@value'];
    return typeof inner === 'string' ? inner : '';
  }
  return typeof value === 'string' ? value : '';
};

const formatDate = (value: unknown): string => {
  const raw = extractRawDateString(value);
  if (!raw) return 'No date';
  const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T');
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? raw : parsed.toLocaleDateString();
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

type AnalysisEvent = Record<string, unknown> & {
  match_id?: string | number;
  matchID?: string | number;
  player_id?: string | number | null;
  team_id?: string | number | null;
  type_name?: string;
  action_type?: string;
  is_goal?: boolean;
  is_successful?: boolean;
  is_assist?: boolean;
  is_key_pass?: boolean;
  progressive_pass?: boolean;
  entered_final_third?: boolean;
  entered_box?: boolean;
  high_regain?: boolean;
  analytical_xg?: number | string;
  shot_distance?: number | string;
};

type AppliedAnalysisSnapshot = {
  matchIds: string[];
  analysisType: string;
};

type PatternCard = {
  pattern: string;
  frequency: string;
  impact: 'High' | 'Medium';
  trend: 'increasing' | 'decreasing' | 'stable';
};

type PlayerOutputRow = {
  id: string;
  uiKey: string;
  name: string;
  rank: number;
  matches: number;
  goals: number;
  shots: number;
  completedPasses: number;
  actionSuccessRate: number;
};

const toAnalysisMatchRecord = (match: any, index: number, teams: any[]): AnalysisMatchRecord | null => {
  const status = normalizeMatchStatus(match.status, match.date, match.homeScore, match.awayScore);
  const reliableLive = hasReliableLiveContext(match, teams);

  if (status === 'live' && !reliableLive) {
    return null;
  }

  return {
    id: String(match.id),
    uiKey: `${match.id || 'match'}-${index}`,
    home: resolveTeamName(match.homeTeam || match.home_team || match.home_team_name, match.homeTeamId || match.home_team_id, teams, 'Home'),
    away: resolveTeamName(match.awayTeam || match.away_team || match.away_team_name, match.awayTeamId || match.away_team_id, teams, 'Away'),
    date: formatDate(match.date),
    rawDate: extractRawDateString(match.date),
    status,
    competition: match.competition || 'Turkish Süper Lig',
    homeScore: toNumber(match.homeScore ?? match.home_score),
    awayScore: toNumber(match.awayScore ?? match.away_score),
  };
};

const mergeMatchRecords = (existing: AnalysisMatchRecord[], incoming: AnalysisMatchRecord[]): AnalysisMatchRecord[] => {
  const byId = new Map<string, AnalysisMatchRecord>();

  [...existing, ...incoming].forEach((match) => {
    byId.set(match.id, match);
  });

  return Array.from(byId.values()).sort(compareAnalysisMatches);
};

const toIdString = (value: unknown): string => (value === null || value === undefined ? '' : String(value));

const getEventMatchId = (event: AnalysisEvent): string => toIdString(event.match_id ?? event.matchID);

const getEventPlayerId = (event: AnalysisEvent): string => toIdString(event.player_id);

const isShotEvent = (event: AnalysisEvent): boolean => {
  const typeName = String(event.type_name || '').toLowerCase();
  return Boolean(
    event.analytical_xg !== undefined
      || event.shot_distance !== undefined
      || ['goal', 'miss', 'attempt_saved', 'blocked_shot', 'chance_missed', 'post'].includes(typeName)
  );
};

const average = (values: number[]): number => {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
};

const getSeriesTrend = (series: number[]): 'increasing' | 'decreasing' | 'stable' => {
  if (series.length < 2) {
    return 'stable';
  }

  const midpoint = Math.ceil(series.length / 2);
  const firstHalf = average(series.slice(0, midpoint));
  const secondHalf = average(series.slice(midpoint));

  if (secondHalf > firstHalf * 1.15) {
    return 'increasing';
  }

  if (secondHalf < firstHalf * 0.85) {
    return 'decreasing';
  }

  return 'stable';
};

const MultiMatchAnalysis: React.FC = () => {
  const [selectedMatches, setSelectedMatches] = useState<string[]>([]);
  const [analysisType, setAnalysisType] = useState('comparative');
  const [showMatchPicker, setShowMatchPicker] = useState(false);
  const [matchSearchQuery, setMatchSearchQuery] = useState('');
  const [matchPickerResults, setMatchPickerResults] = useState<AnalysisMatchRecord[]>([]);
  const [matchPickerLoading, setMatchPickerLoading] = useState(false);
  const [matchPickerError, setMatchPickerError] = useState<string | null>(null);
  const [matchCache, setMatchCache] = useState<AnalysisMatchRecord[]>([]);
  const [appliedAnalysis, setAppliedAnalysis] = useState<AppliedAnalysisSnapshot | null>(null);
  const [backendAnalysis, setBackendAnalysis] = useState<any | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const pickerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { matches, teams, players } = useData();
  const { data: analysisMatchesData, loading: analysisMatchesLoading, refetch: refetchAnalysisMatches } = useApi(
    () => apiService.getMatches(analysisMatchFilters),
    [],
  );

  const availableMatches = useMemo(
    () => {
      const matchPool = analysisMatchesData && analysisMatchesData.length > 0 ? analysisMatchesData : matches;
      const normalizedMatches = matchPool
        .map((match: any, index: number) => toAnalysisMatchRecord(match, index, teams))
        .filter(Boolean) as AnalysisMatchRecord[];

      normalizedMatches.sort(compareAnalysisMatches);
      return normalizedMatches;
    },
    [analysisMatchesData, matches, teams],
  );

  const knownMatchLookup = useMemo(() => {
    const lookup = new Map<string, AnalysisMatchRecord>();

    mergeMatchRecords(availableMatches, matchCache).forEach((match) => {
      lookup.set(match.id, match);
    });

    return lookup;
  }, [availableMatches, matchCache]);

  useEffect(() => {
    setSelectedMatches((previous) => previous.filter((matchId) => knownMatchLookup.has(matchId)));
  }, [knownMatchLookup]);

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
      setMatchPickerError(null);
    }
  }, [showMatchPicker]);

  useEffect(() => {
    if (!showMatchPicker) {
      return;
    }

    let isCancelled = false;
    const timeoutId = setTimeout(async () => {
      setMatchPickerLoading(true);
      setMatchPickerError(null);

      const response = await apiService.searchMatches(matchSearchQuery, 36);
      if (isCancelled) {
        return;
      }

      if (response.success) {
        const normalizedResults = (response.data || [])
          .map((match: any, index: number) => toAnalysisMatchRecord(match, index, teams))
          .filter(Boolean) as AnalysisMatchRecord[];

        setMatchPickerResults(normalizedResults);
        setMatchCache((previous) => mergeMatchRecords(previous, normalizedResults));
      } else {
        setMatchPickerResults([]);
        setMatchPickerError(response.error.message || 'Failed to search matches');
      }

      setMatchPickerLoading(false);
    }, matchSearchQuery.trim().length >= 2 ? 250 : 0);

    return () => {
      isCancelled = true;
      clearTimeout(timeoutId);
    };
  }, [matchSearchQuery, showMatchPicker, teams]);

  useEffect(() => {
    setAppliedAnalysis((previous) => {
      if (!previous) {
        return previous;
      }

      const validMatchIds = previous.matchIds.filter((matchId) => knownMatchLookup.has(matchId));
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
  }, [knownMatchLookup]);

  const playerLookup = useMemo(
    () => {
      const lookup = new Map<string, any>();

      players.forEach((player: any) => {
        [
          player.id,
          player.playerID,
          player.player_id,
          player.optaId,
          player.opta_uid,
          player.provider_ids?.opta,
        ]
          .filter(Boolean)
          .forEach((candidateId) => lookup.set(String(candidateId), player));
      });

      return lookup;
    },
    [players],
  );

  const selectedMatchCards = useMemo(
    () => selectedMatches
      .map((matchId) => knownMatchLookup.get(matchId))
      .filter(Boolean) as AnalysisMatchRecord[],
    [knownMatchLookup, selectedMatches],
  );

  const pickerMatches = useMemo(() => {
    const selected = matchPickerResults.filter((match) => selectedMatches.includes(match.id));
    const unselected = matchPickerResults.filter((match) => !selectedMatches.includes(match.id));
    return [...selected, ...unselected].slice(0, 50);
  }, [matchPickerResults, selectedMatches]);

  const openPicker = useCallback(() => setShowMatchPicker(true), []);
  const closePicker = useCallback(() => setShowMatchPicker(false), []);

  const appliedMatchIds = appliedAnalysis?.matchIds ?? [];

  const selectedMatchRecords = useMemo(
    () => appliedMatchIds
      .map((matchId) => knownMatchLookup.get(matchId))
      .filter(Boolean) as AnalysisMatchRecord[],
    [appliedMatchIds, knownMatchLookup],
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

  const patterns: PatternCard[] = useMemo(
    () => (backendAnalysis?.patterns ?? []).map((p: any) => ({
      pattern: p.name,
      frequency: typeof p.frequency === 'number' ? `${p.frequency} per match` : String(p.frequency),
      impact: 'Medium' as const,
      trend: 'stable' as const,
    })),
    [backendAnalysis],
  );

  const keyInsights: string[] = backendAnalysis?.key_insights ?? [];

  const playerOutput: PlayerOutputRow[] = useMemo(
    () => (backendAnalysis?.player_leaderboard ?? []).map((p: any, index: number) => ({
      id: String(p.player_id),
      uiKey: `${p.player_id}-${index}`,
      name: p.player_name || `Player ${p.player_id}`,
      rank: index + 1,
      matches: 1,
      goals: p.goals ?? 0,
      shots: p.shots ?? 0,
      completedPasses: p.completed_passes ?? 0,
      actionSuccessRate: 0,
    })),
    [backendAnalysis],
  );

  const applyAnalysis = async () => {
    if (selectedMatches.length === 0) {
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      await refetchAnalysisMatches();
      setAppliedAnalysis({ matchIds: [...selectedMatches], analysisType });

      const response = await apiService.getMultiMatchAnalytics(selectedMatches);
      if (response.success && response.data) {
        setBackendAnalysis(response.data);
        if ((response.data.matches_with_data ?? 0) === 0) {
          setAnalysisError('No event data was returned for the selected matches. Score-based summaries are still available.');
        }
      } else {
        setBackendAnalysis(null);
        setAnalysisError('Analytics service did not return results for the selected matches.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const analysisLoading = analysisMatchesLoading || isAnalyzing;

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
        <p className="text-slate-400 text-sm">Search across all competitions and seasons</p>
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
              <div className="mt-2 text-xs text-slate-400">
                Type a team, league or year. Results are loaded from the backend, so the picker scales to large match catalogs.
              </div>
            </div>

            {/* Match grid */}
            <div className="max-h-96 overflow-y-auto p-3">
              {matchPickerLoading ? (
                <div className="py-8 text-center text-sm text-slate-400">Loading matches…</div>
              ) : matchPickerError ? (
                <div className="py-8 text-center text-sm text-red-300">{matchPickerError}</div>
              ) : pickerMatches.length === 0 ? (
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
              <span className="text-xs text-slate-500">{pickerMatches.length} result{pickerMatches.length !== 1 ? 's' : ''} shown</span>
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

      {analysisError && (
        <div className="rounded-lg border border-yellow-600/30 bg-yellow-600/10 px-4 py-3 text-sm text-yellow-200">
          {analysisError}
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
                No event-driven patterns were generated for the selected matches.
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
                        <span className="font-semibold text-green-400">{player.actionSuccessRate}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
              No player event output is available for the selected match set.
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
            <h3 className="text-xl font-semibold mb-6">Generated Signals</h3>
            <div className="space-y-4">
              <div className="p-3 bg-green-600/10 border border-green-600/20 rounded">
                <div className="text-sm font-medium text-green-400 mb-1">Match Coverage</div>
                <div className="text-xs text-slate-300">{backendAnalysis?.matches_with_data ?? 0} of {selectedMatches.length} selected matches returned event data.</div>
              </div>
              <div className="p-3 bg-yellow-600/10 border border-yellow-600/20 rounded">
                <div className="text-sm font-medium text-yellow-400 mb-1">Chance Quality</div>
                <div className="text-xs text-slate-300">Avg {backendAnalysis?.kpis?.avg_shots_per_match ?? 0} shots/match — avg xG {backendAnalysis?.kpis?.avg_xg_per_match ?? 0} per match.</div>
              </div>
              <div className="p-3 bg-blue-600/10 border border-blue-600/20 rounded">
                <div className="text-sm font-medium text-blue-400 mb-1">Scoring</div>
                <div className="text-xs text-slate-300">Avg {backendAnalysis?.kpis?.avg_goals_per_match ?? 0} goals/match — {backendAnalysis?.kpis?.high_scoring_pct ?? 0}% of matches had more than 3 goals.</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiMatchAnalysis;
