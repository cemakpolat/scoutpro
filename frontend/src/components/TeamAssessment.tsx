import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  BarChart3,
  GitCompareArrows,
  Loader2,
  Shield,
  Target,
  Trophy,
  Users,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import type { Team } from '../types';

type TeamInsightItem = {
  title?: string;
  value?: string | number;
  description?: string;
};

type TeamSummary = {
  matchesAnalyzed?: number;
  avgGoalsFor?: number;
  avgGoalsAgainst?: number;
  form?: string[];
  passAccuracy?: number;
  manager?: string | null;
  squadSize?: number;
};

type TeamInsightsPayload = {
  team?: Partial<Team> & { name?: string; manager?: string | null };
  summary?: TeamSummary;
  insights?: TeamInsightItem[];
  last_updated?: string;
};

type TeamComparisonPayload = {
  team_ids?: string[];
  teams?: Array<{
    team_id?: string;
    team?: Partial<Team> & { name?: string };
    summary?: TeamSummary;
  }>;
};

type TeamRiskFlag = {
  title: string;
  level: 'low' | 'medium' | 'high';
  description: string;
};

type TeamForecastSnapshot = {
  outlook: string;
  confidenceLabel: string;
  projectedGoalsFor: number;
  projectedGoalsAgainst: number;
  stabilityScore: number;
  rationale: string;
};

type TeamComparisonCardProfile = {
  teamId: string;
  name: string;
  roleLabel: string;
  summary: TeamSummary;
  stats: any;
};

const TEAM_RANKING_LIMIT = 6;

function normalizeTeamKey(value: unknown): string {
  return String(value ?? '').trim().replace(/^t/i, '');
}

function formatValue(value: unknown, digits: number = 0): string {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  const numericValue = Number(value);
  if (Number.isFinite(numericValue)) {
    return numericValue.toFixed(digits);
  }

  return String(value);
}

function toNumericValue(...values: unknown[]): number {
  for (const value of values) {
    const numericValue = Number(value);
    if (Number.isFinite(numericValue)) {
      return numericValue;
    }
  }

  return 0;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function deriveFormMomentum(form: string[] = []): number {
  if (form.length === 0) {
    return 0;
  }

  const total = form.reduce((accumulator, entry) => {
    const normalizedEntry = String(entry).trim().toUpperCase();
    if (normalizedEntry.startsWith('W')) {
      return accumulator + 1;
    }
    if (normalizedEntry.startsWith('L')) {
      return accumulator - 1;
    }
    return accumulator;
  }, 0);

  return total / form.length;
}

function deriveFormVolatility(form: string[] = []): number {
  if (form.length < 2) {
    return 0;
  }

  let changes = 0;
  for (let index = 1; index < form.length; index += 1) {
    if (form[index] !== form[index - 1]) {
      changes += 1;
    }
  }

  return changes / (form.length - 1);
}

function riskTone(level: TeamRiskFlag['level']): string {
  if (level === 'high') {
    return 'border-red-500/30 bg-red-500/10 text-red-100';
  }
  if (level === 'medium') {
    return 'border-amber-500/30 bg-amber-500/10 text-amber-100';
  }
  return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100';
}

function buildTeamForecastSnapshot(teamStats: any, summary: TeamSummary, selectedRanking: any): TeamForecastSnapshot {
  const goalsForPerMatch = toNumericValue(teamStats?.goals_per_match, summary.avgGoalsFor);
  const goalsAgainstPerMatch = toNumericValue(teamStats?.goals_against_per_match, teamStats?.goals_conceded_per_match, summary.avgGoalsAgainst);
  const passAccuracy = toNumericValue(teamStats?.pass_accuracy, summary.passAccuracy);
  const shotsPerMatch = toNumericValue(
    teamStats?.shots_per_match,
    teamStats?.shots && teamStats?.matches_played ? Number(teamStats.shots) / Number(teamStats.matches_played) : null,
  );
  const formMomentum = deriveFormMomentum(summary.form || []);
  const formVolatility = deriveFormVolatility(summary.form || []);
  const rankingBoost = selectedRanking?.rank ? clamp((8 - Number(selectedRanking.rank)) * 0.08, -0.2, 0.4) : 0;

  const stabilityScore = clamp(
    48 + passAccuracy * 0.32 - goalsAgainstPerMatch * 14 + formMomentum * 12 - formVolatility * 10,
    0,
    100,
  );

  const projectedGoalsFor = Number((goalsForPerMatch + shotsPerMatch * 0.04 + rankingBoost + Math.max(0, formMomentum) * 0.15).toFixed(2));
  const projectedGoalsAgainst = Number((Math.max(0.2, goalsAgainstPerMatch - passAccuracy * 0.002 + formVolatility * 0.18 - rankingBoost * 0.25)).toFixed(2));
  const edge = projectedGoalsFor - projectedGoalsAgainst;

  const outlook = edge >= 0.7
    ? 'Strong positive outlook'
    : edge >= 0.15
      ? 'Competitive edge'
      : edge > -0.15
        ? 'Balanced but fragile'
        : 'Pressure building';

  const confidenceLabel = stabilityScore >= 72
    ? 'High confidence'
    : stabilityScore >= 55
      ? 'Moderate confidence'
      : 'Watch closely';

  return {
    outlook,
    confidenceLabel,
    projectedGoalsFor,
    projectedGoalsAgainst,
    stabilityScore: Number(stabilityScore.toFixed(0)),
    rationale: `Based on ${formatValue(summary.matchesAnalyzed, 0)} analysed matches, ${formatValue(passAccuracy, 1)}% pass accuracy, and current form ${summary.form && summary.form.length > 0 ? summary.form.join(' · ') : 'not available'}.`,
  };
}

function buildTeamRiskFlags(teamStats: any, summary: TeamSummary, selectedRanking: any): TeamRiskFlag[] {
  const goalsAgainstPerMatch = toNumericValue(teamStats?.goals_against_per_match, teamStats?.goals_conceded_per_match, summary.avgGoalsAgainst);
  const passAccuracy = toNumericValue(teamStats?.pass_accuracy, summary.passAccuracy);
  const squadSize = toNumericValue(summary.squadSize);
  const matchesAnalyzed = toNumericValue(summary.matchesAnalyzed, teamStats?.matches_played);
  const formMomentum = deriveFormMomentum(summary.form || []);
  const formVolatility = deriveFormVolatility(summary.form || []);
  const flags: TeamRiskFlag[] = [];

  if (goalsAgainstPerMatch >= 1.45) {
    flags.push({
      title: 'Defensive leakage',
      level: 'high',
      description: `${goalsAgainstPerMatch.toFixed(2)} goals conceded per match is putting pressure on the current structure.`,
    });
  } else if (goalsAgainstPerMatch >= 1.0) {
    flags.push({
      title: 'Containment under pressure',
      level: 'medium',
      description: `${goalsAgainstPerMatch.toFixed(2)} goals conceded per match suggests the back line still needs stabilising support.`,
    });
  }

  if (passAccuracy > 0 && passAccuracy < 78) {
    flags.push({
      title: 'Control slippage',
      level: passAccuracy < 74 ? 'high' : 'medium',
      description: `${passAccuracy.toFixed(1)}% pass accuracy is below the level usually needed to sustain territory and tempo.`,
    });
  }

  if (formMomentum < 0 || formVolatility > 0.65) {
    flags.push({
      title: 'Form volatility',
      level: formMomentum < -0.2 ? 'high' : 'medium',
      description: `Recent form ${summary.form && summary.form.length > 0 ? summary.form.join(' · ') : 'is unavailable'} shows instability in week-to-week output.`,
    });
  }

  if (squadSize > 0 && squadSize < 23 && matchesAnalyzed >= 20) {
    flags.push({
      title: 'Squad load risk',
      level: 'medium',
      description: `${formatValue(squadSize, 0)} players covering ${formatValue(matchesAnalyzed, 0)} tracked matches points to a thinner rotation.`,
    });
  }

  if (flags.length === 0) {
    flags.push({
      title: 'Stable baseline',
      level: 'low',
      description: selectedRanking?.rank
        ? `The current profile is stable enough to support a top-${selectedRanking.rank} ranking position.`
        : 'No major statistical risk signal is currently standing out from the available team feed.',
    });
  }

  return flags.slice(0, 4);
}

function buildComparisonSummary(teamStats: any, summary: TeamSummary = {}): TeamSummary {
  const matchesAnalyzed = toNumericValue(summary.matchesAnalyzed, teamStats?.matches_played);
  const avgGoalsFor = toNumericValue(
    summary.avgGoalsFor,
    teamStats?.goals_per_match,
    matchesAnalyzed > 0 ? toNumericValue(teamStats?.goals) / matchesAnalyzed : null,
  );
  const avgGoalsAgainst = toNumericValue(
    summary.avgGoalsAgainst,
    teamStats?.goals_against_per_match,
    teamStats?.goals_conceded_per_match,
    matchesAnalyzed > 0 ? toNumericValue(teamStats?.goals_against) / matchesAnalyzed : null,
  );
  const passAccuracy = toNumericValue(summary.passAccuracy, teamStats?.pass_accuracy);

  return {
    matchesAnalyzed: matchesAnalyzed || undefined,
    avgGoalsFor: avgGoalsFor || undefined,
    avgGoalsAgainst: avgGoalsAgainst || undefined,
    form: summary.form,
    passAccuracy: passAccuracy || undefined,
    manager: summary.manager,
    squadSize: toNumericValue(summary.squadSize) || undefined,
  };
}

function buildDrilldownPriorities(teamStats: any, summary: TeamSummary, riskFlags: TeamRiskFlag[]): string[] {
  const priorities: string[] = [];

  if (riskFlags.some((flag) => flag.title === 'Defensive leakage')) {
    priorities.push('Inspect recent concession patterns and possession losses before progressing this team into higher-confidence forecasts.');
  }

  if (riskFlags.some((flag) => flag.title === 'Control slippage')) {
    priorities.push('Open buildup and passing views to compare control metrics with the current comparison team.');
  }

  if ((summary.form || []).length > 0) {
    priorities.push(`Compare the latest form run ${summary.form?.join(' · ')} against the full-sample averages before committing to a projection.`);
  }

  if (priorities.length === 0) {
    priorities.push('Use the comparison panel below to stress-test this team against a stronger or weaker peer before building a scenario.');
    priorities.push('Review the team intelligence cards to identify which insight deserves a deeper tactical drill-down next.');
  }

  const shotsPerMatch = toNumericValue(teamStats?.shots_per_match);
  if (shotsPerMatch > 0) {
    priorities.push(`Shot volume is currently ${shotsPerMatch.toFixed(2)} per match, so chance creation should stay part of the next review pass.`);
  }

  return priorities.slice(0, 3);
}

function TeamMetricCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-bold text-white">{value}</div>
      <div className="mt-1 text-xs text-slate-400">{detail}</div>
    </div>
  );
}

interface TeamAssessmentProps {
  initialTeamId?: string;
}

const TeamAssessment: React.FC<TeamAssessmentProps> = ({ initialTeamId }) => {
  const {
    data: teams,
    loading: teamsLoading,
    error: teamsError,
  } = useApi<Team[]>(() => apiService.getTeams(), []);
  const {
    data: rankings,
    loading: rankingsLoading,
    error: rankingsError,
  } = useApi<any[]>(() => apiService.getTeamRankings('goals', TEAM_RANKING_LIMIT), []);

  const [selectedTeamId, setSelectedTeamId] = useState('');
  const [comparisonTeamId, setComparisonTeamId] = useState('');

  useEffect(() => {
    if (!teams || teams.length === 0) {
      return;
    }

    if (initialTeamId && teams.some((team) => String(team.id) === String(initialTeamId))) {
      if (selectedTeamId !== String(initialTeamId)) {
        setSelectedTeamId(String(initialTeamId));
      }
      return;
    }

    if (!selectedTeamId) {
      setSelectedTeamId(teams[0].id);
    }

    if (!comparisonTeamId && teams.length > 1) {
      setComparisonTeamId(teams[1].id);
    }
  }, [comparisonTeamId, initialTeamId, selectedTeamId, teams]);

  useEffect(() => {
    if (!teams || teams.length === 0) {
      return;
    }

    if (comparisonTeamId === selectedTeamId) {
      const fallbackTeam = teams.find((team) => team.id !== selectedTeamId);
      setComparisonTeamId(fallbackTeam?.id || '');
    }
  }, [comparisonTeamId, selectedTeamId, teams]);

  const {
    data: teamStats,
    loading: statsLoading,
    error: statsError,
  } = useApi<any>(
    () => (selectedTeamId ? apiService.getTeamStatistics(selectedTeamId) : Promise.resolve({ success: true, data: null } as any)),
    [selectedTeamId],
  );

  const {
    data: teamInsights,
    loading: insightsLoading,
    error: insightsError,
  } = useApi<TeamInsightsPayload>(
    () => (selectedTeamId ? apiService.getTeamInsights(selectedTeamId) : Promise.resolve({ success: true, data: null } as any)),
    [selectedTeamId],
  );

  const {
    data: comparisonData,
    loading: comparisonLoading,
    error: comparisonError,
  } = useApi<TeamComparisonPayload | null>(
    () => (
      selectedTeamId && comparisonTeamId
        ? apiService.compareTeams([selectedTeamId, comparisonTeamId])
        : Promise.resolve({ success: true, data: null } as any)
    ),
    [comparisonTeamId, selectedTeamId],
  );

  const {
    data: comparisonTeamStats,
    loading: comparisonStatsLoading,
    error: comparisonStatsError,
  } = useApi<any>(
    () => (comparisonTeamId ? apiService.getTeamStatistics(comparisonTeamId) : Promise.resolve({ success: true, data: null } as any)),
    [comparisonTeamId],
  );

  const {
    data: comparisonTeamInsights,
    loading: comparisonInsightsLoading,
    error: comparisonInsightsError,
  } = useApi<TeamInsightsPayload>(
    () => (comparisonTeamId ? apiService.getTeamInsights(comparisonTeamId) : Promise.resolve({ success: true, data: null } as any)),
    [comparisonTeamId],
  );

  const teamList = teams || [];
  const rankingRows = rankings || [];
  const selectedTeam = teamList.find((team) => team.id === selectedTeamId) || null;
  const comparisonOptions = teamList.filter((team) => team.id !== selectedTeamId);
  const summary = teamInsights?.summary || {};
  const insights = teamInsights?.insights || [];
  const comparisonTeams = comparisonData?.teams || [];
  const comparisonSummary = comparisonTeamInsights?.summary || {};

  const selectedRanking = useMemo(() => {
    return rankingRows.find((row) => {
      const rowKey = normalizeTeamKey(row?.scoutpro_team_id || row?.team_id || row?.opta_team_id);
      return rowKey === normalizeTeamKey(selectedTeamId);
    }) || null;
  }, [rankingRows, selectedTeamId]);

  const forecastSnapshot = useMemo(
    () => buildTeamForecastSnapshot(teamStats, summary, selectedRanking),
    [selectedRanking, summary, teamStats],
  );

  const riskFlags = useMemo(
    () => buildTeamRiskFlags(teamStats, summary, selectedRanking),
    [selectedRanking, summary, teamStats],
  );

  const drillDownPriorities = useMemo(
    () => buildDrilldownPriorities(teamStats, summary, riskFlags),
    [riskFlags, summary, teamStats],
  );

  const comparisonProfiles = useMemo<TeamComparisonCardProfile[]>(() => {
    const comparisonProfilesById = new Map<string, TeamComparisonPayload['teams'][number]>();
    comparisonTeams.forEach((entry) => {
      const key = String(entry?.team_id || entry?.team?.id || '').trim();
      if (key) {
        comparisonProfilesById.set(key, entry);
      }
    });

    const primaryProfile = comparisonProfilesById.get(String(selectedTeamId));
    const peerProfile = comparisonProfilesById.get(String(comparisonTeamId));

    const profiles: TeamComparisonCardProfile[] = [];

    if (selectedTeamId) {
      profiles.push({
        teamId: String(selectedTeamId),
        name: selectedTeam?.name || primaryProfile?.team?.name || teamInsights?.team?.name || 'Selected Team',
        roleLabel: 'Primary Team',
        summary: {
          ...buildComparisonSummary(teamStats, summary),
          ...buildComparisonSummary(teamStats, primaryProfile?.summary || {}),
        },
        stats: teamStats,
      });
    }

    if (comparisonTeamId) {
      const comparisonTeam = teamList.find((team) => team.id === comparisonTeamId);
      profiles.push({
        teamId: String(comparisonTeamId),
        name: comparisonTeam?.name || peerProfile?.team?.name || comparisonTeamInsights?.team?.name || 'Comparison Team',
        roleLabel: 'Comparison Team',
        summary: {
          ...buildComparisonSummary(comparisonTeamStats, comparisonSummary),
          ...buildComparisonSummary(comparisonTeamStats, peerProfile?.summary || {}),
        },
        stats: comparisonTeamStats,
      });
    }

    return profiles;
  }, [comparisonTeamId, comparisonTeamInsights?.team?.name, comparisonTeamStats, comparisonSummary, comparisonTeams, selectedTeam, selectedTeamId, summary, teamInsights?.team?.name, teamList, teamStats]);

  const metricCards = useMemo(() => {
    return [
      {
        label: 'Ranking Position',
        value: selectedRanking?.rank ? `#${selectedRanking.rank}` : '—',
        detail: selectedRanking?.stat_name ? `Based on ${selectedRanking.stat_name}` : 'Ranking unavailable for selected team',
      },
      {
        label: 'Matches Played',
        value: formatValue(teamStats?.matches_played, 0),
        detail: `${formatValue(summary.matchesAnalyzed, 0)} matches with advanced team insights`,
      },
      {
        label: 'Goals Scored',
        value: formatValue(teamStats?.goals, 0),
        detail: `${formatValue(teamStats?.goals_per_match, 2)} per match`,
      },
      {
        label: 'Pass Accuracy',
        value: `${formatValue(teamStats?.pass_accuracy ?? summary.passAccuracy, 2)}%`,
        detail: `${formatValue(teamStats?.passes_successful, 0)} successful passes`,
      },
      {
        label: 'Shots Created',
        value: formatValue(teamStats?.shots, 0),
        detail: `${formatValue(teamStats?.shots_per_match, 2)} shots per match`,
      },
      {
        label: 'Squad Depth',
        value: formatValue(summary.squadSize, 0),
        detail: teamInsights?.team?.manager || summary.manager || 'Manager not available in current feed',
      },
    ];
  }, [selectedRanking, summary.manager, summary.matchesAnalyzed, summary.passAccuracy, summary.squadSize, teamInsights?.team?.manager, teamStats]);

  if (teamsLoading && teamList.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-slate-700 bg-slate-800 px-6 py-16 text-slate-300">
        <Loader2 className="mr-3 h-5 w-5 animate-spin text-cyan-400" />
        Loading team assessment surface...
      </div>
    );
  }

  if (teamsError) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
        Failed to load teams: {teamsError}
      </div>
    );
  }

  if (teamList.length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800 px-6 py-12 text-center text-slate-400">
        No teams are available yet, so team assessment cannot be rendered.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-xl border border-slate-700 bg-slate-800 p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Team Assessment</h2>
          <p className="mt-1 text-sm text-slate-400">
            This team surface combines direct statistics, advanced insights, forecast snapshots, explainable risk flags,
            and side-by-side comparison from the currently connected team feeds.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">Primary Team</label>
            <select
              value={selectedTeamId}
              onChange={(event) => setSelectedTeamId(event.target.value)}
              className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
            >
              {teamList.map((team) => (
                <option key={team.id} value={team.id}>{team.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">Comparison Team</label>
            <select
              value={comparisonTeamId}
              onChange={(event) => setComparisonTeamId(event.target.value)}
              className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
            >
              {comparisonOptions.map((team) => (
                <option key={team.id} value={team.id}>{team.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {(statsError || insightsError || rankingsError || comparisonError || comparisonStatsError || comparisonInsightsError) && (
        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-100">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-yellow-300" />
            <div>
              <div className="font-medium">Some team data could not be loaded completely.</div>
              <div className="mt-1 text-xs text-yellow-200/90">
                {[statsError, insightsError, rankingsError, comparisonError, comparisonStatsError, comparisonInsightsError].filter(Boolean).join(' · ')}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {metricCards.map((card) => (
          <TeamMetricCard key={card.label} label={card.label} value={card.value} detail={card.detail} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.15fr,0.85fr]">
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-white">
            <Target className="h-5 w-5 text-emerald-400" />
            Forecast Snapshot
          </div>
          <div className="mt-2 text-sm text-slate-400">
            This forecast is derived from the current team stats, form, and ranking context already visible on this page.
          </div>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-500">Outlook</div>
              <div className="mt-2 text-xl font-bold text-white">{forecastSnapshot.outlook}</div>
              <div className="mt-1 text-xs text-slate-400">{forecastSnapshot.confidenceLabel}</div>
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-500">Projected Goals For</div>
              <div className="mt-2 text-xl font-bold text-emerald-300">{forecastSnapshot.projectedGoalsFor.toFixed(2)}</div>
              <div className="mt-1 text-xs text-slate-400">Per upcoming scenario window</div>
            </div>
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-500">Projected Goals Against</div>
              <div className="mt-2 text-xl font-bold text-amber-300">{forecastSnapshot.projectedGoalsAgainst.toFixed(2)}</div>
              <div className="mt-1 text-xs text-slate-400">Lower is better</div>
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/70 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">Stability Score</div>
                <div className="mt-1 text-2xl font-bold text-white">{forecastSnapshot.stabilityScore}</div>
              </div>
              <div className="max-w-xs text-xs text-right text-slate-400">{forecastSnapshot.rationale}</div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-white">
            <AlertCircle className="h-5 w-5 text-amber-400" />
            Risk Flags
          </div>
          <div className="mt-2 text-sm text-slate-400">
            Flags stay explainable because they are derived directly from the same team stats and form context.
          </div>

          <div className="mt-5 space-y-3">
            {riskFlags.map((flag) => (
              <div key={flag.title} className={`rounded-lg border px-4 py-4 ${riskTone(flag.level)}`}>
                <div className="flex items-center justify-between gap-3">
                  <div className="font-semibold text-white">{flag.title}</div>
                  <div className="text-[11px] uppercase tracking-wide">{flag.level}</div>
                </div>
                <div className="mt-2 text-sm text-slate-300">{flag.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-white">
            <Shield className="h-5 w-5 text-cyan-400" />
            Team Intelligence Snapshot
          </div>
          <div className="mt-2 text-sm text-slate-400">
            {selectedTeam?.name || teamInsights?.team?.name || 'Selected team'} is currently viewed through the available team read model and analytics-service insights.
          </div>

          <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
            {insights.length > 0 ? insights.map((insight, index) => (
              <div key={`${insight.title || 'insight'}-${index}`} className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                <div className="text-xs uppercase tracking-wide text-cyan-300">{insight.title || 'Insight'}</div>
                <div className="mt-2 text-2xl font-bold text-white">{insight.value ?? '—'}</div>
                <div className="mt-1 text-sm text-slate-400">{insight.description || 'No description available.'}</div>
              </div>
            )) : (
              <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 text-sm text-slate-400 md:col-span-2">
                Team insights are not populated for the selected team yet.
              </div>
            )}
          </div>

          <div className="mt-5 rounded-lg border border-slate-700 bg-slate-900/70 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Target className="h-4 w-4 text-blue-400" />
              Current Coverage
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">Manager</div>
                <div className="mt-1 text-sm text-slate-200">{teamInsights?.team?.manager || summary.manager || 'Unavailable'}</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">Tracked Form</div>
                <div className="mt-1 text-sm text-slate-200">{summary.form && summary.form.length > 0 ? summary.form.join(' · ') : 'Not available'}</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wide text-slate-500">Last Update</div>
                <div className="mt-1 text-sm text-slate-200">{teamInsights?.last_updated ? new Date(teamInsights.last_updated).toLocaleString() : 'Unavailable'}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-white">
            <Trophy className="h-5 w-5 text-yellow-400" />
            Goal Ranking Board
          </div>
          <div className="mt-2 text-sm text-slate-400">
            Top teams by current goal output from the team statistics ranking feed.
          </div>

          <div className="mt-4 space-y-3">
            {rankingsLoading && rankingRows.length === 0 ? (
              <div className="flex items-center text-sm text-slate-400">
                <Loader2 className="mr-2 h-4 w-4 animate-spin text-cyan-400" />
                Loading team rankings...
              </div>
            ) : rankingRows.length > 0 ? rankingRows.map((row, index) => {
              const isSelectedTeam = normalizeTeamKey(row?.scoutpro_team_id || row?.team_id || row?.opta_team_id) === normalizeTeamKey(selectedTeamId);
              return (
                <div
                  key={`${row?.team_id || row?.opta_team_id || row?.team_name || index}`}
                  className={`rounded-lg border px-4 py-3 ${isSelectedTeam ? 'border-cyan-500/40 bg-cyan-500/10' : 'border-slate-700 bg-slate-900/70'}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-white">#{row?.rank || index + 1} {row?.team_name || row?.name || 'Unknown Team'}</div>
                      <div className="mt-1 text-xs text-slate-400">
                        {formatValue(row?.matches_played, 0)} matches · {formatValue(row?.pass_accuracy, 2)}% pass accuracy
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-400">{formatValue(row?.goals, 0)}</div>
                      <div className="text-xs text-slate-500">Goals</div>
                    </div>
                  </div>
                </div>
              );
            }) : (
              <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-6 text-sm text-slate-400">
                Team rankings are not available from the backend yet.
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
        <div className="flex items-center gap-2 text-lg font-semibold text-white">
          <GitCompareArrows className="h-5 w-5 text-purple-400" />
          Team Comparison
        </div>
        <div className="mt-2 text-sm text-slate-400">
          Compare summary-level performance, attack/defence balance, and squad depth for two teams using the existing analytics-service comparison contract.
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {(comparisonLoading || comparisonStatsLoading || comparisonInsightsLoading) && comparisonProfiles.length === 0 ? (
            <div className="flex items-center rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-6 text-sm text-slate-400 lg:col-span-2">
              <Loader2 className="mr-2 h-4 w-4 animate-spin text-cyan-400" />
              Loading comparison summary...
            </div>
          ) : comparisonProfiles.length > 0 ? comparisonProfiles.map((entry) => (
            <div key={entry.teamId} className={`rounded-lg border p-4 ${entry.roleLabel === 'Primary Team' ? 'border-cyan-500/30 bg-cyan-500/5' : 'border-slate-700 bg-slate-900/70'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">{entry.roleLabel}</div>
                  <div className="mt-1 text-lg font-semibold text-white">{entry.name}</div>
                  <div className="text-xs text-slate-500">Comparison summary</div>
                </div>
                <Users className="h-5 w-5 text-slate-500" />
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-slate-800 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Avg Goals For</div>
                  <div className="mt-1 font-semibold text-white">{formatValue(entry.summary.avgGoalsFor, 2)}</div>
                </div>
                <div className="rounded-lg bg-slate-800 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Avg Goals Against</div>
                  <div className="mt-1 font-semibold text-white">{formatValue(entry.summary.avgGoalsAgainst, 2)}</div>
                </div>
                <div className="rounded-lg bg-slate-800 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Pass Accuracy</div>
                  <div className="mt-1 font-semibold text-white">{formatValue(entry.summary.passAccuracy, 2)}%</div>
                </div>
                <div className="rounded-lg bg-slate-800 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Squad Size</div>
                  <div className="mt-1 font-semibold text-white">{formatValue(entry.summary.squadSize, 0)}</div>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-slate-800 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Matches Analysed</div>
                  <div className="mt-1 font-semibold text-white">{formatValue(entry.summary.matchesAnalyzed, 0)}</div>
                </div>
                <div className="rounded-lg bg-slate-800 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Tracked Form</div>
                  <div className="mt-1 font-semibold text-white">{entry.summary.form && entry.summary.form.length > 0 ? entry.summary.form.join(' · ') : 'Unavailable'}</div>
                </div>
              </div>
            </div>
          )) : (
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-6 text-sm text-slate-400 lg:col-span-2">
              Select two teams to load comparison data.
            </div>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
        <div className="flex items-center gap-2 text-lg font-semibold text-white">
          <BarChart3 className="h-5 w-5 text-blue-400" />
          Next Drill-Down Priorities
        </div>
        <div className="mt-2 text-sm text-slate-400">
          Use these priorities to decide which comparison, lens, or scenario should be opened next from the current team state.
        </div>
        <div className="mt-4 space-y-3">
          {drillDownPriorities.map((item) => (
            <div key={item} className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-4 text-sm text-slate-300">
              {item}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TeamAssessment;