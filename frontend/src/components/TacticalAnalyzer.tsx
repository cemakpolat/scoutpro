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

const PHASE_EVENT_TYPES: Record<string, Set<string>> = {
  attack: new Set(['shot', 'pass', 'duel', 'take_on', 'carry', 'cross']),
  defense: new Set(['tackle', 'interception', 'clearance', 'block', 'ball_recovery', 'pressure', 'foul']),
  transition: new Set(['pass', 'duel', 'ball_recovery', 'take_on', 'carry', 'dribble']),
};

const resolveLiveMatchLabel = (match: any): string => {
  const homeTeamId = String(match?.homeTeamId || match?.home_team_id || '').trim();
  const awayTeamId = String(match?.awayTeamId || match?.away_team_id || '').trim();
  const homeTeam = match?.homeTeam || match?.home_team || (homeTeamId && homeTeamId !== '0' ? `Team ${homeTeamId}` : 'Home');
  const awayTeam = match?.awayTeam || match?.away_team || (awayTeamId && awayTeamId !== '0' ? `Team ${awayTeamId}` : 'Away');
  return `${homeTeam} vs ${awayTeam}`;
};

const createLocalResponse = <T,>(data: T) => ({
  success: true as const,
  data,
  meta: { timestamp: new Date().toISOString(), source: 'client' },
});

const normalizeEventType = (event: any): string => {
  const rawValue = event?.type_name || event?.type?.name || event?.type || event?.event_type || '';
  return String(rawValue).trim().toLowerCase().replace(/[\s-]+/g, '_');
};

const isSuccessfulEvent = (event: any): boolean => {
  if (typeof event?.is_successful === 'boolean') {
    return event.is_successful;
  }
  if (typeof event?.successful === 'boolean') {
    return event.successful;
  }
  if (typeof event?.success === 'boolean') {
    return event.success;
  }

  const outcome = String(event?.outcome_name || event?.outcome?.name || '').trim().toLowerCase();
  return ['successful', 'complete', 'completed', 'won', 'success'].some((token) => outcome.includes(token));
};

const getEventLocation = (event: any) => {
  if (typeof event?.location?.x === 'number' && typeof event?.location?.y === 'number') {
    return event.location;
  }
  if (typeof event?.x === 'number' && typeof event?.y === 'number') {
    return { x: event.x, y: event.y };
  }
  return null;
};

const getEventEndLocation = (event: any, nextEvent?: any) => {
  if (typeof event?.end_location?.x === 'number' && typeof event?.end_location?.y === 'number') {
    return event.end_location;
  }
  return getEventLocation(nextEvent);
};

const getZoneFromX = (xValue: number): 'defensive' | 'middle' | 'attacking' => {
  if (xValue <= 33) {
    return 'defensive';
  }
  if (xValue <= 66) {
    return 'middle';
  }
  return 'attacking';
};

const prettifyLabel = (value: string): string => {
  return String(value || 'unknown')
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
};

const resolveTeamName = (match: any, teamId: string): string => {
  const normalizedTeamId = String(teamId || '').trim();
  if (!normalizedTeamId) {
    return 'Unknown Team';
  }

  const homeTeamId = String(match?.homeTeamId || match?.home_team_id || '').trim();
  const awayTeamId = String(match?.awayTeamId || match?.away_team_id || '').trim();

  if (homeTeamId && homeTeamId === normalizedTeamId) {
    return match?.homeTeam || match?.home_team || `Team ${normalizedTeamId}`;
  }
  if (awayTeamId && awayTeamId === normalizedTeamId) {
    return match?.awayTeam || match?.away_team || `Team ${normalizedTeamId}`;
  }

  return `Team ${normalizedTeamId}`;
};

const buildFallbackMatchTacticalSnapshot = (events: any[]) => {
  const defensiveActions = new Set(['tackle', 'interception', 'foul', 'clearance', 'block']);
  const teamStats: Record<string, {
    passes: number;
    passesInOppHalf: number;
    defensiveActions: number;
    defensiveActionsInOppHalf: number;
    pressures: number;
    zones: Record<'defensive' | 'middle' | 'attacking', number>;
  }> = {};

  events.forEach((event) => {
    const teamId = String(event?.team_id || event?.teamId || '').trim();
    if (!teamId) {
      return;
    }

    if (!teamStats[teamId]) {
      teamStats[teamId] = {
        passes: 0,
        passesInOppHalf: 0,
        defensiveActions: 0,
        defensiveActionsInOppHalf: 0,
        pressures: 0,
        zones: { defensive: 0, middle: 0, attacking: 0 },
      };
    }

    const eventType = normalizeEventType(event);
    const location = getEventLocation(event) || { x: 50, y: 50 };
    const xValue = Number(location.x) || 0;

    if (eventType === 'pass') {
      teamStats[teamId].passes += 1;
      if (xValue > 50) {
        teamStats[teamId].passesInOppHalf += 1;
      }
      teamStats[teamId].zones[getZoneFromX(xValue)] += 1;
      return;
    }

    if (defensiveActions.has(eventType)) {
      teamStats[teamId].defensiveActions += 1;
      if (xValue > 50) {
        teamStats[teamId].defensiveActionsInOppHalf += 1;
      }
      return;
    }

    if (eventType === 'pressure') {
      teamStats[teamId].pressures += 1;
    }
  });

  const teams = Object.keys(teamStats);
  const tacticalMetrics = teams.reduce<Record<string, any>>((accumulator, teamId) => {
    const opponentPassesInOwnHalf = teams.reduce((sum, otherTeamId) => {
      if (otherTeamId === teamId) {
        return sum;
      }
      const otherTeam = teamStats[otherTeamId];
      return sum + otherTeam.passes - otherTeam.passesInOppHalf;
    }, 0);

    const defensiveActionsInOppHalf = Math.max(teamStats[teamId].defensiveActionsInOppHalf, 1);
    const totalPasses = Math.max(teamStats[teamId].passes, 1);
    const ppda = Number((opponentPassesInOwnHalf / defensiveActionsInOppHalf).toFixed(2));
    const pressStyle = ppda < 10 ? 'high press' : ppda < 20 ? 'medium press' : 'low press';

    accumulator[teamId] = {
      ppda,
      press_style: pressStyle,
      passes: teamStats[teamId].passes,
      defensive_actions: teamStats[teamId].defensiveActions,
      pressures: teamStats[teamId].pressures,
      possession_zones_pct: {
        defensive: Number(((teamStats[teamId].zones.defensive / totalPasses) * 100).toFixed(1)),
        middle: Number(((teamStats[teamId].zones.middle / totalPasses) * 100).toFixed(1)),
        attacking: Number(((teamStats[teamId].zones.attacking / totalPasses) * 100).toFixed(1)),
      },
    };

    return accumulator;
  }, {});

  return {
    teams,
    tactical_metrics: tacticalMetrics,
  };
};

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
    data: formationCatalogData,
    loading: formationCatalogLoading,
    error: formationCatalogError,
  } = useApi(
    () => apiService.getTacticalOverview(),
    []
  );
  const {
    data: matchTacticalMetricsData,
    loading: matchMetricsLoading,
    error: matchMetricsError,
  } = useApi(
    () => selectedMatchId ? apiService.getMatchTacticalMetrics(selectedMatchId) : Promise.resolve(createLocalResponse<any>(null)),
    [selectedMatchId]
  );
  const {
    data: sequenceInsightsData,
    loading: sequenceLoading,
    error: sequenceError,
  } = useApi(
    () => selectedMatchId ? apiService.getMatchSequenceInsights(selectedMatchId) : Promise.resolve(createLocalResponse<any>(null)),
    [selectedMatchId]
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
  const formationCatalog = formationCatalogData && typeof formationCatalogData === 'object' ? formationCatalogData : null;
  const matchTacticalMetrics = useMemo(() => {
    if (matchTacticalMetricsData && typeof matchTacticalMetricsData === 'object' && matchTacticalMetricsData.tactical_metrics) {
      return matchTacticalMetricsData;
    }

    return buildFallbackMatchTacticalSnapshot(matchEvents);
  }, [matchEvents, matchTacticalMetricsData]);
  const sequenceInsights = sequenceInsightsData && typeof sequenceInsightsData === 'object' ? sequenceInsightsData : null;
  const loading = eventsLoading || formationCatalogLoading || matchMetricsLoading || sequenceLoading;
  const tacticalError = [eventsError, formationCatalogError, matchMetricsError, sequenceError].filter(Boolean).join(' · ');

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

  const selectedMatch = filteredMatchOptions.find((match: any) => String(match.id || match.matchId) === selectedMatchId);

  const filteredMatchEvents = useMemo(() => {
    const allowedTypes = PHASE_EVENT_TYPES[selectedPhase] || null;
    if (!allowedTypes) {
      return matchEvents;
    }

    return matchEvents.filter((event: any) => allowedTypes.has(normalizeEventType(event)));
  }, [matchEvents, selectedPhase]);

  const tacticalPatterns = useMemo(() => {
    const patternsByType = new Map<string, {
      count: number;
      success: number;
      zones: Record<'defensive' | 'middle' | 'attacking', number>;
    }>();

    filteredMatchEvents.forEach((event: any) => {
      const type = normalizeEventType(event) || 'unknown';
      const existing = patternsByType.get(type) || {
        count: 0,
        success: 0,
        zones: { defensive: 0, middle: 0, attacking: 0 },
      };

      existing.count += 1;
      if (isSuccessfulEvent(event)) {
        existing.success += 1;
      }

      const location = getEventLocation(event);
      if (location) {
        existing.zones[getZoneFromX(Number(location.x) || 0)] += 1;
      }

      patternsByType.set(type, existing);
    });

    return Array.from(patternsByType.entries())
      .sort((left, right) => right[1].count - left[1].count)
      .slice(0, 4)
      .map(([type, stats]) => {
        const share = stats.count / Math.max(filteredMatchEvents.length, 1);
        const successRate = Math.round((stats.success / Math.max(stats.count, 1)) * 100);
        const dominantZones = Object.entries(stats.zones)
          .filter(([, count]) => count > 0)
          .sort((left, right) => right[1] - left[1])
          .slice(0, 2)
          .map(([zone]) => prettifyLabel(zone));

        return {
          name: prettifyLabel(type),
          count: stats.count,
          frequency: Math.round(share * 100),
          success: successRate,
          dominantZones,
          impact: share >= 0.25 ? 'High' : share >= 0.12 ? 'Medium' : 'Low',
          quality: successRate >= 70 ? 'Reliable' : successRate >= 45 ? 'Mixed' : 'Low Yield',
        };
      });
  }, [filteredMatchEvents]);

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
  const formations = Array.isArray(formationCatalog?.formations) && formationCatalog.formations.length > 0
    ? formationCatalog.formations
    : fallbackFormations;

  const playerMovements = useMemo(() => {
    return filteredMatchEvents
      .map((event: any, index: number, events: any[]) => {
        const startLocation = getEventLocation(event);
        const targetLocation = getEventEndLocation(event, events[index + 1]);
        if (!startLocation || !targetLocation) {
          return null;
        }

        return {
          id: event.event_id || event.id || `${normalizeEventType(event)}-${index}`,
          from: [startLocation.x, startLocation.y],
          to: [targetLocation.x, targetLocation.y],
          type: normalizeEventType(event) || 'pass',
          success: isSuccessfulEvent(event),
        };
      })
      .filter(Boolean)
      .slice(0, 8);
  }, [filteredMatchEvents]);

  const teamTacticalCards = useMemo(() => {
    const metrics = matchTacticalMetrics?.tactical_metrics || {};
    const teamIds = Array.isArray(matchTacticalMetrics?.teams) && matchTacticalMetrics.teams.length > 0
      ? matchTacticalMetrics.teams
      : Object.keys(metrics);

    return teamIds.map((teamId: string) => {
      const metric = metrics[teamId] || {};
      const zones = metric.possession_zones_pct || {};
      return {
        teamId,
        name: resolveTeamName(selectedMatch, teamId),
        ppda: Number(metric.ppda) || 0,
        pressStyle: prettifyLabel(metric.press_style || 'unavailable'),
        passes: Number(metric.passes) || 0,
        defensiveActions: Number(metric.defensive_actions) || 0,
        pressures: Number(metric.pressures) || 0,
        zones: {
          defensive: Number(zones.defensive) || 0,
          middle: Number(zones.middle) || 0,
          attacking: Number(zones.attacking) || 0,
        },
      };
    });
  }, [matchTacticalMetrics, selectedMatch]);

  const tacticalSummarySections = useMemo(() => {
    const teamSequenceSummaries = new Map<string, any>(
      Array.isArray(sequenceInsights?.teamSummaries)
        ? sequenceInsights.teamSummaries.map((summary: any) => [String(summary.teamId), summary])
        : []
    );

    return [
      {
        title: 'Pressing Profile',
        tone: 'text-blue-400',
        items: teamTacticalCards.map((team) => ({
          label: team.name,
          value: `${team.ppda.toFixed(1)} PPDA • ${team.pressStyle}`,
        })),
      },
      {
        title: 'Ball Progression',
        tone: 'text-green-400',
        items: teamTacticalCards.map((team) => ({
          label: team.name,
          value: `${team.passes} passes • ${team.zones.attacking.toFixed(1)}% attacking-third share`,
        })),
      },
      {
        title: 'Sequence Output',
        tone: 'text-red-400',
        items: teamTacticalCards.map((team) => {
          const sequenceSummary = teamSequenceSummaries.get(team.teamId);
          return {
            label: team.name,
            value: sequenceSummary
              ? `${sequenceSummary.directAttacks} direct • ${sequenceSummary.boxEntries} box • ${sequenceSummary.shotEndings} shot endings`
              : 'No sequence summary available',
          };
        }),
      },
    ];
  }, [sequenceInsights, teamTacticalCards]);

  const selectedFormationLayout = FORMATION_LAYOUTS[selectedFormation] || FORMATION_LAYOUTS['4-3-3'];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center">
            <Layers className="h-8 w-8 mr-3 text-purple-500" />
            Tactical Analyzer
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            {selectedMatch
              ? `Selected match: ${resolveLiveMatchLabel(selectedMatch)}. Pattern cards use the selected phase, while the zone bars and pressing metrics come from the match tactical snapshot.`
              : 'Select a match to load match-specific tactical patterns, zone splits, and sequence output.'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
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
          <h3 className="text-xl font-semibold mb-2">Formation Analysis</h3>
          <p className="mb-6 text-sm text-slate-400">
            The board shows the selected tactical template overlaid with live event traces from the chosen match and phase.
          </p>
          
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
                  <defs>
                    <marker id="tactical-arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                      <path d="M0,0 L8,4 L0,8 z" fill={movement.success ? '#4ade80' : '#f87171'} />
                    </marker>
                  </defs>
                  <line
                    x1={`${movement.from[0]}%`}
                    y1={`${movement.from[1]}%`}
                    x2={`${movement.to[0]}%`}
                    y2={`${movement.to[1]}%`}
                    stroke={movement.success ? '#4ade80' : '#f87171'}
                    strokeWidth="2"
                    strokeDasharray={movement.type === 'pass' ? '5,5' : '0'}
                    markerEnd="url(#tactical-arrowhead)"
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
          <h3 className="text-xl font-semibold mb-2">Formation Benchmarks</h3>
          <p className="mb-6 text-sm text-slate-400">
            These benchmark cards show catalog-wide formation usage and effectiveness, not the selected match lineup.
          </p>
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
                      pattern.impact === 'Medium' ? 'bg-yellow-600 text-yellow-100' : 'bg-slate-600 text-slate-100'
                    }`}>
                      {pattern.impact}
                    </span>
                    <span className="text-xs text-slate-400">{pattern.quality}</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                  <div>
                    <div className="text-slate-400">Share Of Phase Events</div>
                    <div className="font-bold text-blue-400">{pattern.frequency}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Success Rate</div>
                    <div className="font-bold text-green-400">{pattern.success}%</div>
                  </div>
                </div>
                <div className="text-xs text-slate-400">
                  Zone focus: {pattern.dominantZones.length > 0 ? pattern.dominantZones.join(', ') : 'Unspecified'}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {pattern.count} traced events in the selected phase
                </div>
              </div>
            )) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No tactical pattern data available.
              </div>
            )}
          </div>
        </div>

        {/* Match Zone Activity */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Activity className="h-6 w-6 mr-2 text-red-400" />
            Match Zone Activity
          </h3>
          <p className="mb-6 text-sm text-slate-400">
            These charts are match-specific. Each stacked bar shows where a team circulated possession in the selected fixture.
          </p>
          <div className="space-y-4">
            {teamTacticalCards.length > 0 ? teamTacticalCards.map((team) => (
              <div key={team.teamId} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-semibold">{team.name}</span>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">Press Style</div>
                    <div className="font-bold text-green-400">{team.pressStyle}</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 text-sm mb-4">
                  <div className="rounded-lg bg-slate-800 px-3 py-3">
                    <div className="text-xs uppercase tracking-wide text-slate-500">PPDA</div>
                    <div className="mt-1 text-lg font-semibold text-white">{team.ppda.toFixed(1)}</div>
                  </div>
                  <div className="rounded-lg bg-slate-800 px-3 py-3">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Passes</div>
                    <div className="mt-1 text-lg font-semibold text-white">{team.passes}</div>
                  </div>
                  <div className="rounded-lg bg-slate-800 px-3 py-3">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Def Actions</div>
                    <div className="mt-1 text-lg font-semibold text-white">{team.defensiveActions}</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Possession zones</span>
                    <span className="font-semibold">{team.zones.attacking.toFixed(1)}% final third</span>
                  </div>
                  <div className="flex w-full overflow-hidden rounded-full bg-slate-600 h-3">
                    <div
                      className="bg-red-500 h-3"
                      style={{ width: `${team.zones.defensive}%` }}
                    ></div>
                    <div
                      className="bg-yellow-500 h-3"
                      style={{ width: `${team.zones.middle}%` }}
                    ></div>
                    <div
                      className="bg-green-500 h-3"
                      style={{ width: `${team.zones.attacking}%` }}
                    ></div>
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs text-slate-400">
                    <span>Def {team.zones.defensive.toFixed(1)}%</span>
                    <span>Mid {team.zones.middle.toFixed(1)}%</span>
                    <span>Att {team.zones.attacking.toFixed(1)}%</span>
                    <span>Pressures {team.pressures}</span>
                  </div>
                </div>
              </div>
            )) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No match tactical snapshot available.
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
          Match Tactical Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {tacticalSummarySections.map((section) => (
            <div key={section.title} className="p-4 bg-slate-700 rounded-lg">
              <h4 className={`font-semibold mb-3 ${section.tone}`}>{section.title}</h4>
              <div className="space-y-2 text-sm">
                {section.items?.length > 0 ? section.items.map((item: any) => (
                  <div key={item.label} className="flex justify-between">
                    <span>{item.label}</span>
                    <span className="text-slate-200 text-right">{item.value}</span>
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