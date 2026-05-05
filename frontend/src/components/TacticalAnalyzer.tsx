import React, { useState, useEffect, useMemo } from 'react';
import { 
  Layers, Zap, Target, Activity, Eye, Loader2
} from 'lucide-react';
import apiService from '../services/api';
import { useApi } from '../hooks/useApi';
import { buildMatchCatalog, filterMatchCatalog, formatMatchLabel, getAvailableLeagues, getAvailableYears } from '../utils/matchFilters';

const FORMATION_LAYOUTS: Record<string, Array<{ role: string; left: string; top: string; tone: string }>> = {
  '4-3-3': [
    { role: 'GK', left: '50%', top: '87%', tone: 'bg-blue-500' },
    { role: 'LB', left: '22%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '40%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '60%', top: '72%', tone: 'bg-blue-400' },
    { role: 'RB', left: '78%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CM', left: '32%', top: '52%', tone: 'bg-green-400' },
    { role: 'DM', left: '50%', top: '58%', tone: 'bg-green-400' },
    { role: 'CM', left: '68%', top: '52%', tone: 'bg-green-400' },
    { role: 'LW', left: '24%', top: '28%', tone: 'bg-red-400' },
    { role: 'ST', left: '50%', top: '24%', tone: 'bg-red-400' },
    { role: 'RW', left: '76%', top: '28%', tone: 'bg-red-400' }
  ],
  '4-2-3-1': [
    { role: 'GK', left: '50%', top: '87%', tone: 'bg-blue-500' },
    { role: 'LB', left: '22%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '40%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '60%', top: '72%', tone: 'bg-blue-400' },
    { role: 'RB', left: '78%', top: '72%', tone: 'bg-blue-400' },
    { role: 'DM', left: '38%', top: '57%', tone: 'bg-green-400' },
    { role: 'DM', left: '62%', top: '57%', tone: 'bg-green-400' },
    { role: 'LW', left: '24%', top: '36%', tone: 'bg-yellow-400' },
    { role: 'AM', left: '50%', top: '40%', tone: 'bg-yellow-400' },
    { role: 'RW', left: '76%', top: '36%', tone: 'bg-yellow-400' },
    { role: 'ST', left: '50%', top: '22%', tone: 'bg-red-400' }
  ],
  '3-5-2': [
    { role: 'GK', left: '50%', top: '87%', tone: 'bg-blue-500' },
    { role: 'LCB', left: '32%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '50%', top: '74%', tone: 'bg-blue-400' },
    { role: 'RCB', left: '68%', top: '72%', tone: 'bg-blue-400' },
    { role: 'LWB', left: '18%', top: '52%', tone: 'bg-green-400' },
    { role: 'CM', left: '38%', top: '50%', tone: 'bg-green-400' },
    { role: 'DM', left: '50%', top: '58%', tone: 'bg-green-400' },
    { role: 'CM', left: '62%', top: '50%', tone: 'bg-green-400' },
    { role: 'RWB', left: '82%', top: '52%', tone: 'bg-green-400' },
    { role: 'ST', left: '40%', top: '24%', tone: 'bg-red-400' },
    { role: 'ST', left: '60%', top: '24%', tone: 'bg-red-400' }
  ],
  '4-4-2': [
    { role: 'GK', left: '50%', top: '87%', tone: 'bg-blue-500' },
    { role: 'LB', left: '22%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '40%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '60%', top: '72%', tone: 'bg-blue-400' },
    { role: 'RB', left: '78%', top: '72%', tone: 'bg-blue-400' },
    { role: 'LM', left: '18%', top: '48%', tone: 'bg-green-400' },
    { role: 'CM', left: '40%', top: '52%', tone: 'bg-green-400' },
    { role: 'CM', left: '60%', top: '52%', tone: 'bg-green-400' },
    { role: 'RM', left: '82%', top: '48%', tone: 'bg-green-400' },
    { role: 'ST', left: '40%', top: '24%', tone: 'bg-red-400' },
    { role: 'ST', left: '60%', top: '24%', tone: 'bg-red-400' }
  ],
  '3-4-3': [
    { role: 'GK', left: '50%', top: '87%', tone: 'bg-blue-500' },
    { role: 'LCB', left: '32%', top: '72%', tone: 'bg-blue-400' },
    { role: 'CB', left: '50%', top: '74%', tone: 'bg-blue-400' },
    { role: 'RCB', left: '68%', top: '72%', tone: 'bg-blue-400' },
    { role: 'LM', left: '20%', top: '50%', tone: 'bg-green-400' },
    { role: 'CM', left: '42%', top: '54%', tone: 'bg-green-400' },
    { role: 'CM', left: '58%', top: '54%', tone: 'bg-green-400' },
    { role: 'RM', left: '80%', top: '50%', tone: 'bg-green-400' },
    { role: 'LW', left: '24%', top: '24%', tone: 'bg-red-400' },
    { role: 'ST', left: '50%', top: '22%', tone: 'bg-red-400' },
    { role: 'RW', left: '76%', top: '24%', tone: 'bg-red-400' }
  ]
};

const normalizePercent = (value: unknown, multiplier = 1): number => {
  const numericValue = Number(value) || 0;
  if (numericValue <= 1) {
    return Math.round(numericValue * 100 * multiplier);
  }

  return Math.round(numericValue * multiplier);
};

const resolveLiveMatchLabel = (match: any): string => {
  const homeTeamId = String(match?.homeTeamId || match?.home_team_id || '').trim();
  const awayTeamId = String(match?.awayTeamId || match?.away_team_id || '').trim();
  const homeTeam = match?.homeTeam || match?.home_team || (homeTeamId && homeTeamId !== '0' ? `Team ${homeTeamId}` : 'Home');
  const awayTeam = match?.awayTeam || match?.away_team || (awayTeamId && awayTeamId !== '0' ? `Team ${awayTeamId}` : 'Away');
  return `${homeTeam} vs ${awayTeam}`;
};

const hasConcreteTeamContext = (match: any): boolean => {
  const homeTeamId = String(match?.homeTeamId || match?.home_team_id || '').trim();
  const awayTeamId = String(match?.awayTeamId || match?.away_team_id || '').trim();
  return Boolean(homeTeamId && awayTeamId && homeTeamId !== '0' && awayTeamId !== '0');
};

const createLocalResponse = <T,>(data: T) => ({
  success: true as const,
  data,
  meta: { timestamp: new Date().toISOString(), source: 'client' },
});

const TacticalAnalyzer: React.FC = () => {
  const [selectedFormation, setSelectedFormation] = useState('4-3-3');
  const [analysisMode, setAnalysisMode] = useState('live');
  const [selectedPhase, setSelectedPhase] = useState('attack');
  const [selectedMatchId, setSelectedMatchId] = useState('');
  const [selectedYear, setSelectedYear] = useState('all');
  const [selectedLeague, setSelectedLeague] = useState('all');
  
  const { data: enrichedMatches } = useApi(() => apiService.getMatches({ limit: 100 }), []);
  const {
    data: matchEventsData,
    loading: eventsLoading,
    error: eventsError,
  } = useApi(
    () => selectedMatchId ? apiService.getMatchEvents(selectedMatchId) : Promise.resolve(createLocalResponse<any[]>([])),
    [selectedMatchId]
  );
  const {
    data: tacticalOverviewData,
    loading: overviewLoading,
    error: overviewError,
  } = useApi(
    () => selectedMatchId ? apiService.getTacticalOverview(selectedFormation, selectedPhase, selectedMatchId) : Promise.resolve(createLocalResponse<any>(null)),
    [selectedFormation, selectedPhase, selectedMatchId]
  );

  const matchOptions = Array.isArray(enrichedMatches) ? enrichedMatches : [];
  const matchCatalog = useMemo(() => buildMatchCatalog(matchOptions), [matchOptions]);
  const availableYears = useMemo(() => getAvailableYears(matchCatalog), [matchCatalog]);
  const availableLeagues = useMemo(
    () => getAvailableLeagues(matchCatalog, selectedYear),
    [matchCatalog, selectedYear],
  );
  const filteredMatchOptions = useMemo(
    () => filterMatchCatalog(matchCatalog, { year: selectedYear, league: selectedLeague }).map((entry) => entry.source),
    [matchCatalog, selectedYear, selectedLeague],
  );
  const matchEvents = Array.isArray(matchEventsData) ? matchEventsData : [];
  const tacticalOverview = tacticalOverviewData && typeof tacticalOverviewData === 'object' ? tacticalOverviewData : null;
  const loading = eventsLoading || overviewLoading;
  const tacticalError = eventsError || overviewError || '';

  useEffect(() => {
    if (selectedYear !== 'all' && !availableYears.includes(selectedYear)) {
      setSelectedYear('all');
    }
  }, [availableYears, selectedYear]);

  useEffect(() => {
    if (selectedLeague !== 'all' && !availableLeagues.includes(selectedLeague)) {
      setSelectedLeague('all');
    }
  }, [availableLeagues, selectedLeague]);

  useEffect(() => {
    if (!selectedMatchId && filteredMatchOptions.length > 0) {
      setSelectedMatchId(String(filteredMatchOptions[0].id || filteredMatchOptions[0].matchId));
      return;
    }

    if (selectedMatchId && !filteredMatchOptions.some((match: any) => String(match.id || match.matchId) === String(selectedMatchId))) {
      setSelectedMatchId(filteredMatchOptions.length > 0 ? String(filteredMatchOptions[0].id || filteredMatchOptions[0].matchId) : '');
    }
  }, [filteredMatchOptions, selectedMatchId]);

  const filteredMatchEvents = selectedPhase === 'attack'
    ? matchEvents.filter((event: any) => ['shot', 'pass', 'duel'].includes(event.type_name))
    : selectedPhase === 'defense'
      ? matchEvents.filter((event: any) => ['tackle', 'interception', 'clearance', 'ball_control'].includes(event.type_name))
      : matchEvents.filter((event: any) => ['pass', 'duel', 'ball_control', 'take_on', 'carries'].includes(event.type_name));

  // Build tactical data from match events
  const tacticalPatterns = filteredMatchEvents.reduce((acc: any[], event: any) => {
    const type = event.type_name || 'unknown';
    const existing = acc.find(p => p.name === type);
    if (existing) {
      existing.frequency += 1;
      existing.success += event.is_successful ? 1 : 0;
    } else {
      acc.push({ name: type, frequency: 1, success: event.is_successful ? 1 : 0 });
    }
    return acc;
  }, []).map((pattern: any) => ({
    name: pattern.name.charAt(0).toUpperCase() + pattern.name.slice(1),
    frequency: Math.round((pattern.frequency / Math.max(filteredMatchEvents.length, 1)) * 100),
    success: pattern.frequency > 0 ? Math.round((pattern.success / pattern.frequency) * 100) : 0,
    zones: ['Mid Field', 'Attack', 'Defense'],
    impact: (pattern.frequency / Math.max(filteredMatchEvents.length, 1)) > 0.2 ? 'High' : 'Medium',
    trend: 'stable'
  })).slice(0, 4);

  // Formation options with static scouting benchmarks
  const FORMATION_STATS: Record<string, { effectiveness: number; popularity: number }> = {
    '4-3-3':   { effectiveness: 72, popularity: 38 },
    '4-2-3-1': { effectiveness: 75, popularity: 31 },
    '3-5-2':   { effectiveness: 63, popularity: 15 },
    '4-4-2':   { effectiveness: 68, popularity: 12 },
    '3-4-3':   { effectiveness: 65, popularity: 4  },
  };
  const fallbackFormations = Object.keys(FORMATION_LAYOUTS).map((id) => ({
    id,
    name: id,
    ...(FORMATION_STATS[id] || { effectiveness: 65, popularity: 10 }),
  }));
  const formations = Array.isArray(tacticalOverview?.formations) && tacticalOverview.formations.length > 0
    ? tacticalOverview.formations
    : fallbackFormations;

  // Prefer actual event end locations now that the event store carries them.
  const playerMovements = filteredMatchEvents
    .filter((event: any) => event.location?.x != null && event.location?.y != null)
    .map((event: any, index: number, events: any[]) => {
      const fallbackTarget = events[index + 1]?.location;
      const targetLocation = event.end_location?.x != null && event.end_location?.y != null
        ? event.end_location
        : fallbackTarget;

      if (!targetLocation?.x && targetLocation?.x !== 0) {
        return null;
      }

      return {
        id: event.event_id || index,
        from: [event.location.x, event.location.y],
        to: [targetLocation.x, targetLocation.y],
        type: event.type_name || 'pass',
        success: Boolean(event.is_successful),
      };
    })
    .filter(Boolean)
    .slice(0, 8);

  // Zone-based heatmap aggregation (Defensive / Middle / Attacking thirds)
  const PITCH_ZONES = [
    { zone: 'Defensive Third',  xMin: 0,  xMax: 33  },
    { zone: 'Middle Third',     xMin: 33, xMax: 67  },
    { zone: 'Attacking Third',  xMin: 67, xMax: 100 },
  ];
  const fallbackHeatmapData = PITCH_ZONES.map(({ zone, xMin, xMax }) => {
    const zoneEvents = filteredMatchEvents.filter(
      (e: any) => typeof e.location?.x === 'number' && e.location.x >= xMin && e.location.x < xMax,
    );
    const successful = zoneEvents.filter((e: any) => e.is_successful).length;
    const total = zoneEvents.length;
    return {
      zone,
      intensity: filteredMatchEvents.length > 0 ? Math.min(100, Math.round((total / filteredMatchEvents.length) * 200)) : 0,
      effectiveness: total > 0 ? Math.round((successful / total) * 100) : 0,
    };
  }).filter((z) => z.intensity > 0);
  const heatmapData = Array.isArray(tacticalOverview?.heatmap) && tacticalOverview.heatmap.length > 0
    ? tacticalOverview.heatmap
    : fallbackHeatmapData;

  const sequenceInsights = tacticalOverview?.sequenceInsights || null;

  // Tactical analytics computed from loaded match events
  const passEvents       = filteredMatchEvents.filter((e: any) => e.type_name === 'pass');
  const passSuccessful   = passEvents.filter((e: any) => e.is_successful).length;
  const tackleEvents     = filteredMatchEvents.filter((e: any) => e.type_name === 'tackle');
  const duelEvents       = filteredMatchEvents.filter((e: any) => e.type_name === 'duel');
  const interceptEvents  = filteredMatchEvents.filter((e: any) => e.type_name === 'interception');
  const clearanceEvents  = filteredMatchEvents.filter((e: any) => e.type_name === 'clearance');
  const aerialEvents     = filteredMatchEvents.filter((e: any) => e.type_name === 'aerial');
  const aerialWon        = aerialEvents.filter((e: any) => e.is_successful).length;
  const foulEvents       = filteredMatchEvents.filter((e: any) => e.type_name === 'foul');
  const shotEvents       = filteredMatchEvents.filter((e: any) => e.type_name === 'shot');
  const goalEvents       = shotEvents.filter((e: any) => e.is_goal);
  const fallbackTacticalAnalytics = {
    pressingTriggers: filteredMatchEvents.length > 0 ? [
      { label: 'Tackle count',       value: tackleEvents.length,       suffix: '' },
      { label: 'Interception rate',  value: Math.round(interceptEvents.length / Math.max(1, filteredMatchEvents.length) * 100) },
      { label: 'Duel involvement',   value: duelEvents.length,         suffix: '' },
    ] : [],
    buildupPatterns: filteredMatchEvents.length > 0 ? [
      { label: 'Passes attempted',   value: passEvents.length,         suffix: '' },
      { label: 'Pass success rate',  value: Math.round(passSuccessful / Math.max(1, passEvents.length) * 100) },
      { label: 'Goals from shots',   value: goalEvents.length,         suffix: '' },
    ] : [],
    defensiveActions: filteredMatchEvents.length > 0 ? [
      { label: 'Clearances',         value: clearanceEvents.length,    suffix: '' },
      { label: 'Aerial duels won',   value: aerialWon,                 suffix: '' },
      { label: 'Fouls committed',    value: foulEvents.length,         suffix: '' },
    ] : [],
  };
  const tacticalAnalytics = tacticalOverview?.analytics || fallbackTacticalAnalytics;

  const selectedMatch = filteredMatchOptions.find((m: any) => String(m.id || m.matchId) === selectedMatchId);
  const selectedFormationLayout = FORMATION_LAYOUTS[selectedFormation] || FORMATION_LAYOUTS['4-3-3'];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Layers className="h-8 w-8 mr-3 text-purple-500" />
          Tactical Analyzer
        </h1>
        <div className="flex items-center space-x-4">
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="all">All Years</option>
            {availableYears.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <select
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="all">All Leagues</option>
            {availableLeagues.map((league) => (
              <option key={league} value={league}>{league}</option>
            ))}
          </select>
          {filteredMatchOptions.length > 0 && (
            <select
              value={selectedMatchId}
              onChange={(e) => setSelectedMatchId(e.target.value)}
              className="max-w-xs truncate px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
            >
              {filteredMatchOptions.map((match: any) => (
                <option key={String(match.id || match.matchId)} value={String(match.id || match.matchId)}>
                  {formatMatchLabel(match)}
                </option>
              ))}
            </select>
          )}
          <select
            value={analysisMode}
            onChange={(e) => setAnalysisMode(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="live">Live Analysis</option>
            <option value="historical">Historical Analysis</option>
            <option value="predictive">Predictive Analysis</option>
          </select>
          <button className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
            <Eye className="h-4 w-4" />
            <span>3D View</span>
          </button>
        </div>
      </div>

      {tacticalError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {tacticalError}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center rounded-xl bg-slate-800 px-6 py-20 text-slate-300">
          <Loader2 className="mr-3 h-5 w-5 animate-spin text-purple-400" />
          Loading tactical analysis...
        </div>
      )}

      {/* Formation Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Formation Analysis</h3>
          
          {/* Tactical Board */}
          <div className="relative bg-green-800 rounded-lg p-4 mb-6" style={{ aspectRatio: '16/10' }}>
            <div className="absolute inset-0 bg-gradient-to-b from-green-700 to-green-900 rounded-lg opacity-50"></div>
            
            {/* Field Lines */}
            <div className="absolute inset-0">
              <div className="absolute top-0 left-1/2 w-px h-full bg-white opacity-30 transform -translate-x-1/2"></div>
              <div className="absolute top-1/2 left-0 w-full h-px bg-white opacity-30 transform -translate-y-1/2"></div>
              <div className="absolute top-1/2 left-1/2 w-20 h-20 border border-white opacity-30 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
            </div>

            {/* Player Positions */}
            {selectedFormationLayout.map((player) => (
              <div
                key={`${selectedFormation}-${player.role}-${player.left}-${player.top}`}
                className={`absolute z-10 flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full text-[10px] font-bold text-white ${player.tone}`}
                style={{ left: player.left, top: player.top }}
              >
                {player.role}
              </div>
            ))}

            {/* Player Movements */}
            {playerMovements.map((movement: any, index: number) => (
              <div key={movement.id || index} className="absolute inset-0">
                <div 
                  className={`w-2 h-2 rounded-full ${movement.success ? 'bg-green-400' : 'bg-red-400'}`}
                  style={{ left: `${movement.from[0]}%`, top: `${movement.from[1]}%`, position: 'absolute' }}
                ></div>
                <div 
                  className={`w-1 h-1 rounded-full ${movement.success ? 'bg-green-300' : 'bg-red-300'}`}
                  style={{ left: `${movement.to[0]}%`, top: `${movement.to[1]}%`, position: 'absolute' }}
                ></div>
                <svg className="absolute inset-0 pointer-events-none">
                  <line
                    x1={`${movement.from[0]}%`}
                    y1={`${movement.from[1]}%`}
                    x2={`${movement.to[0]}%`}
                    y2={`${movement.to[1]}%`}
                    stroke={movement.success ? '#4ade80' : '#f87171'}
                    strokeWidth="2"
                    strokeDasharray={movement.type === 'pass' ? '5,5' : '0'}
                    markerEnd="url(#arrowhead)"
                  />
                </svg>
              </div>
            ))}
          </div>

          {/* Formation Selector */}
          <div className="flex space-x-2 mb-4">
            {formations.map((formation: any) => (
              <button
                key={formation.id}
                onClick={() => setSelectedFormation(formation.id)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  selectedFormation === formation.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {formation.name}
              </button>
            ))}
          </div>

          {/* Phase Selector */}
          <div className="flex space-x-2">
            {['attack', 'defense', 'transition'].map((phase) => (
              <button
                key={phase}
                onClick={() => setSelectedPhase(phase)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  selectedPhase === phase
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {phase.charAt(0).toUpperCase() + phase.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Formation Stats */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Formation Statistics</h3>
          <div className="space-y-4">
            {formations.length > 0 ? formations.map((formation: any) => (
              <div key={formation.id} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold">{formation.name}</span>
                  <span className="text-green-400 font-bold">{formation.effectiveness}%</span>
                </div>
                <div className="text-sm text-slate-400 mb-2">
                  Used by {formation.popularity}% of teams
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full"
                    style={{ width: `${formation.effectiveness}%` }}
                  ></div>
                </div>
              </div>
            )) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No live formation data available.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tactical Patterns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Target className="h-6 w-6 mr-2 text-yellow-400" />
            Tactical Patterns
          </h3>
          <div className="space-y-4">
            {tacticalPatterns.length > 0 ? tacticalPatterns.map((pattern: any, index: number) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{pattern.name}</span>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      pattern.impact === 'High' ? 'bg-red-600 text-red-100' :
                      'bg-yellow-600 text-yellow-100'
                    }`}>
                      {pattern.impact}
                    </span>
                    <span className={`text-sm ${
                      pattern.trend === 'increasing' ? 'text-green-400' :
                      pattern.trend === 'decreasing' ? 'text-red-400' : 'text-slate-400'
                    }`}>
                      {pattern.trend === 'increasing' ? '↗' : pattern.trend === 'decreasing' ? '↘' : '→'}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                  <div>
                    <div className="text-slate-400">Frequency</div>
                    <div className="font-bold text-blue-400">{pattern.frequency}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Success Rate</div>
                    <div className="font-bold text-green-400">{pattern.success}%</div>
                  </div>
                </div>
                <div className="text-xs text-slate-400">
                  Active in: {Array.isArray(pattern.zones) ? pattern.zones.join(', ') : 'N/A'}
                </div>
              </div>
            )) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No tactical pattern data available.
              </div>
            )}
          </div>
        </div>

        {/* Heat Map */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Activity className="h-6 w-6 mr-2 text-red-400" />
            Activity Heat Map
          </h3>
          <div className="space-y-4">
            {heatmapData.length > 0 ? heatmapData.map((zone: any, index: number) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-semibold">{zone.zone}</span>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">Effectiveness</div>
                    <div className="font-bold text-green-400">{zone.effectiveness}%</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Activity Intensity</span>
                    <span className="font-semibold">{zone.intensity}%</span>
                  </div>
                  <div className="w-full bg-slate-600 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-yellow-400 to-red-500 h-3 rounded-full"
                      style={{ width: `${zone.intensity}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            )) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No live heatmap data available.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Advanced Analytics */}
      {sequenceInsights && (
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold flex items-center">
                <Zap className="h-6 w-6 mr-2 text-emerald-400" />
                Live Sequence Intelligence
              </h3>
              <p className="text-sm text-slate-400 mt-1">
                {sequenceInsights.matchLabel} • Providers: {(sequenceInsights.providers || []).join(', ') || 'mixed event feed'}
              </p>
            </div>
            <div className="text-sm text-slate-400">
              Top sequences are ranked by territory gain, box entry, and shot-ending actions.
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {(sequenceInsights.teamSummaries || []).map((summary: any) => (
              <div key={summary.teamId} className="rounded-xl bg-slate-700 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold">{summary.teamName}</h4>
                  <span className="text-sm text-slate-400">{summary.totalSequences} sequences</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-slate-400">Direct Attacks</div>
                    <div className="text-lg font-bold text-emerald-400">{summary.directAttacks}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Final-Third Entries</div>
                    <div className="text-lg font-bold text-blue-400">{summary.finalThirdEntries}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Rapid Regains / Second Balls</div>
                    <div className="text-lg font-bold text-yellow-400">{summary.rapidRegains}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Box Entries</div>
                    <div className="text-lg font-bold text-purple-400">{summary.boxEntries}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Average Actions</div>
                    <div className="text-lg font-bold text-cyan-400">{summary.averageActions}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Average Duration</div>
                    <div className="text-lg font-bold text-rose-400">{summary.averageDurationSeconds}s</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div>
            <h4 className="font-semibold text-slate-200 mb-4">Top Live Sequences</h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {(sequenceInsights.topSequences || []).map((sequence: any, index: number) => (
                <div key={`${sequence.teamId}-${sequence.startMinute}-${index}`} className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-100">{sequence.teamName}</span>
                    <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-300">
                      {sequence.startMinute}' - {sequence.endMinute}'
                    </span>
                  </div>
                  <div className="text-sm text-slate-300 mb-3">
                    {sequence.actions} actions through the {sequence.route.toLowerCase()} with {sequence.territoryGain}% territory gain.
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-slate-500">Sequence Type</div>
                      <div className="text-slate-100">
                        {sequence.directAttack ? 'Direct attack' : sequence.sustainedPressure ? 'Sustained pressure' : 'Progression'}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500">Outcome</div>
                      <div className="text-slate-100">
                        {sequence.endedWithGoal ? 'Goal' : sequence.endedWithShot ? 'Shot ending' : sequence.boxEntry ? 'Box entry' : 'Territory gain'}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500">Duration</div>
                      <div className="text-slate-100">{sequence.durationSeconds}s</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Direct Ball Start</div>
                      <div className="text-slate-100">{sequence.directPlay ? 'Yes' : 'No'}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Zap className="h-6 w-6 mr-2 text-purple-400" />
          Advanced Tactical Analytics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: 'Pressing Triggers', tone: 'text-blue-400', items: tacticalAnalytics.pressingTriggers },
            { title: 'Build-up Patterns', tone: 'text-green-400', items: tacticalAnalytics.buildupPatterns },
            { title: 'Defensive Actions', tone: 'text-red-400', items: tacticalAnalytics.defensiveActions }
          ].map((section) => (
            <div key={section.title} className="p-4 bg-slate-700 rounded-lg">
              <h4 className={`font-semibold mb-3 ${section.tone}`}>{section.title}</h4>
              <div className="space-y-2 text-sm">
                {section.items?.length > 0 ? section.items.map((item: any) => (
                  <div key={item.label} className="flex justify-between">
                    <span>{item.label}</span>
                    <span className="text-slate-200">{item.value}{item.suffix || '%'}</span>
                  </div>
                )) : (
                  <div className="text-slate-400">No analytics available.</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TacticalAnalyzer;