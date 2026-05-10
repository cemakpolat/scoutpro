import React from 'react';
import { Search, Filter, Star, TrendingUp, Users, Target, Brain, AlertCircle, BarChart3, ChevronDown, ChevronUp } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import { Player, AIInsight } from '../types';
import { deriveAge } from '../utils/dataTransformers';
import { normalizePhaseLabel, resolveScoutingValuation, type PlayerScoutingPayload } from '../utils/scoutingData';
import ModelCenterLens from './ModelCenterLens';
import PlayerDetail from './PlayerDetail';
import type { ModelCenterContext, ModelCenterTab } from './ModelCenter';

interface ScoutingDashboardProps {
  onPlayerSelect?: (player: Player) => void;
  onOpenModelCenter?: (tab: ModelCenterTab, context?: ModelCenterContext) => void;
}

interface PositionOption {
  value: string;
  label: string;
  serverFilter?: string;
}

interface ScoutingTargetView {
  id: string;
  name: string;
  club: string;
  nationality: string;
  preferredFoot: string;
  displayPosition: string;
  positionGroup: string | null;
  detailedPosition: string | null;
  positionTokens: string[];
  age: number | null;
  ageLabel: string;
  marketValueLabel: string;
  marketValueNumeric: number;
  rating: number;
  goals: number;
  assists: number;
  passAccuracy: number;
  xG: number;
  xA: number;
  hasEventData: boolean;
  photo: string;
  raw: Player;
}

interface AdvancedScoutingFilters {
  nationality: string;
  club: string;
  preferredFoot: string;
  minimumRating: string;
  maximumMarketValue: string;
  minimumPassAccuracy: string;
  requiresEventData: boolean;
}

const DEFAULT_PLAYER_PHOTO = 'https://images.pexels.com/photos/274506/pexels-photo-274506.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop';

const DEFAULT_ADVANCED_FILTERS: AdvancedScoutingFilters = {
  nationality: 'all',
  club: 'all',
  preferredFoot: 'all',
  minimumRating: '',
  maximumMarketValue: '',
  minimumPassAccuracy: '',
  requiresEventData: false,
};

const POSITION_GROUP_MAP: Record<string, string> = {
  GK: 'GK',
  DF: 'DF',
  CB: 'DF',
  LB: 'DF',
  RB: 'DF',
  LWB: 'DF',
  RWB: 'DF',
  MF: 'MF',
  CDM: 'MF',
  CM: 'MF',
  CAM: 'MF',
  LM: 'MF',
  RM: 'MF',
  FW: 'FW',
  LW: 'FW',
  RW: 'FW',
  ST: 'FW',
  CF: 'FW',
  LF: 'FW',
  RF: 'FW',
};

const POSITION_LABELS: Record<string, string> = {
  GK: 'Goalkeeper',
  DF: 'Defender',
  MF: 'Midfielder',
  FW: 'Forward',
  CB: 'Center Back',
  LB: 'Left Back',
  RB: 'Right Back',
  LWB: 'Left Wing Back',
  RWB: 'Right Wing Back',
  CDM: 'Defensive Midfielder',
  CM: 'Central Midfielder',
  CAM: 'Attacking Midfielder',
  LM: 'Left Midfielder',
  RM: 'Right Midfielder',
  LW: 'Left Winger',
  RW: 'Right Winger',
  ST: 'Striker',
  CF: 'Center Forward',
  LF: 'Left Forward',
  RF: 'Right Forward',
};

const POSITION_OPTIONS: PositionOption[] = [
  { value: 'all', label: 'All Positions' },
  { value: 'GK', label: 'Goalkeepers', serverFilter: 'GK' },
  { value: 'DF', label: 'Defenders', serverFilter: 'DF' },
  { value: 'CB', label: 'Center Backs', serverFilter: 'DF' },
  { value: 'LB', label: 'Left Backs', serverFilter: 'DF' },
  { value: 'RB', label: 'Right Backs', serverFilter: 'DF' },
  { value: 'MF', label: 'Midfielders', serverFilter: 'MF' },
  { value: 'CDM', label: 'Defensive Midfielders', serverFilter: 'MF' },
  { value: 'CM', label: 'Central Midfielders', serverFilter: 'MF' },
  { value: 'CAM', label: 'Attacking Midfielders', serverFilter: 'MF' },
  { value: 'FW', label: 'Forwards', serverFilter: 'FW' },
  { value: 'LW', label: 'Left Wingers', serverFilter: 'FW' },
  { value: 'RW', label: 'Right Wingers', serverFilter: 'FW' },
  { value: 'ST', label: 'Strikers', serverFilter: 'FW' },
];

const toFiniteNumber = (value: unknown, fallback: number = 0): number => {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
};

const pickFirstString = (...values: unknown[]): string | null => {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }

  return null;
};

const normalizePositionToken = (value: unknown): string | null => {
  if (typeof value !== 'string') {
    return null;
  }

  const normalized = value.trim().toUpperCase();
  return normalized || null;
};

const normalizePreferredFoot = (value: unknown): string => {
  const normalized = pickFirstString(value)?.toLowerCase();
  if (!normalized) {
    return 'Unknown';
  }

  if (normalized === 'r' || normalized.includes('right')) {
    return 'Right';
  }

  if (normalized === 'l' || normalized.includes('left')) {
    return 'Left';
  }

  if (normalized.includes('both') || normalized.includes('either') || normalized.includes('ambi')) {
    return 'Both';
  }

  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
};

const resolvePositionGroup = (value: unknown): string | null => {
  const normalized = normalizePositionToken(value);
  if (!normalized) {
    return null;
  }

  if (POSITION_GROUP_MAP[normalized]) {
    return POSITION_GROUP_MAP[normalized];
  }

  if (normalized.includes('KEEP')) {
    return 'GK';
  }

  if (normalized.includes('DEF') || normalized.includes('BACK')) {
    return 'DF';
  }

  if (normalized.includes('MID')) {
    return 'MF';
  }

  if (normalized.includes('WING') || normalized.includes('FOR') || normalized.includes('STRIK')) {
    return 'FW';
  }

  return null;
};

const formatMarketValue = (value: unknown): { label: string; numeric: number } => {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    if (value >= 1000000) {
      return { label: `€${(value / 1000000).toFixed(1)}M`, numeric: value };
    }
    if (value >= 1000) {
      return { label: `€${(value / 1000).toFixed(0)}K`, numeric: value };
    }
    return { label: `€${value.toFixed(0)}`, numeric: value };
  }

  const rawText = pickFirstString(value);
  if (!rawText) {
    return { label: 'Value unavailable', numeric: 0 };
  }

  const cleaned = rawText.replace(/,/g, '').trim();
  const directNumeric = Number(cleaned.replace(/[^0-9.]/g, ''));

  if (/m$/i.test(cleaned) && Number.isFinite(directNumeric)) {
    return { label: cleaned.startsWith('€') ? cleaned : `€${cleaned.toUpperCase()}`, numeric: directNumeric * 1000000 };
  }

  if (/k$/i.test(cleaned) && Number.isFinite(directNumeric)) {
    return { label: cleaned.startsWith('€') ? cleaned : `€${cleaned.toUpperCase()}`, numeric: directNumeric * 1000 };
  }

  if (Number.isFinite(directNumeric) && directNumeric > 0) {
    return formatMarketValue(directNumeric);
  }

  return { label: rawText, numeric: 0 };
};

const getDisplayPosition = (detailedPosition: string | null, positionGroup: string | null, fallback: unknown): string => {
  if (detailedPosition && POSITION_LABELS[detailedPosition]) {
    return POSITION_LABELS[detailedPosition];
  }

  if (positionGroup && POSITION_LABELS[positionGroup]) {
    return POSITION_LABELS[positionGroup];
  }

  return pickFirstString(fallback) || 'Position unavailable';
};

const normalizeScoutingTarget = (player: Player | Record<string, unknown>, index: number): ScoutingTargetView => {
  const detailedPosition = normalizePositionToken(
    pickFirstString(
      (player as any).detailed_position,
      (player as any).detailedPosition,
      resolvePositionGroup((player as any).position) ? null : (player as any).position,
      resolvePositionGroup((player as any).raw_position) ? null : (player as any).raw_position,
      resolvePositionGroup((player as any).rawPosition) ? null : (player as any).rawPosition,
    )
  );
  const positionGroup = resolvePositionGroup(detailedPosition)
    || resolvePositionGroup((player as any).position)
    || resolvePositionGroup((player as any).raw_position)
    || resolvePositionGroup((player as any).rawPosition);
  const positionTokens = Array.from(new Set([
    detailedPosition,
    normalizePositionToken((player as any).position),
    normalizePositionToken((player as any).detailed_position),
    normalizePositionToken((player as any).detailedPosition),
    normalizePositionToken((player as any).raw_position),
    normalizePositionToken((player as any).rawPosition),
    positionGroup,
  ].filter((value): value is string => Boolean(value))));
  const age = deriveAge((player as any).age, (player as any).birth_date || (player as any).birthDate);
  const marketValue = formatMarketValue((player as any).marketValue);

  return {
    id: pickFirstString((player as any).id, (player as any).scoutpro_id, (player as any).uID) || `player-${index}`,
    name: pickFirstString(
      (player as any).name,
      `${pickFirstString((player as any).first, (player as any).firstName) || ''} ${pickFirstString((player as any).last, (player as any).lastName) || ''}`.trim(),
    ) || 'Unnamed player',
    club: pickFirstString((player as any).club, (player as any).team, (player as any).team_name, (player as any).clubName) || 'Club unavailable',
    nationality: pickFirstString((player as any).nationality, (player as any).country) || 'Nationality unavailable',
    preferredFoot: normalizePreferredFoot((player as any).preferredFoot ?? (player as any).preferred_foot),
    displayPosition: getDisplayPosition(detailedPosition, positionGroup, (player as any).position),
    positionGroup,
    detailedPosition,
    positionTokens,
    age: typeof age === 'number' ? age : null,
    ageLabel: typeof age === 'number' ? `${age} years` : 'Age unavailable',
    marketValueLabel: marketValue.label,
    marketValueNumeric: marketValue.numeric,
    rating: toFiniteNumber((player as any).rating),
    goals: toFiniteNumber((player as any).goals),
    assists: toFiniteNumber((player as any).assists),
    passAccuracy: toFiniteNumber((player as any).passAccuracy ?? (player as any).pass_accuracy),
    xG: toFiniteNumber((player as any).xG ?? (player as any).xg ?? (player as any).expectedGoals),
    xA: toFiniteNumber((player as any).xA ?? (player as any).xa ?? (player as any).expectedAssists),
    hasEventData: [
      toFiniteNumber((player as any).goals),
      toFiniteNumber((player as any).assists),
      toFiniteNumber((player as any).passAccuracy ?? (player as any).pass_accuracy),
      toFiniteNumber((player as any).xG ?? (player as any).xg ?? (player as any).expectedGoals),
      toFiniteNumber((player as any).xA ?? (player as any).xa ?? (player as any).expectedAssists),
    ].some((value) => value > 0),
    photo: pickFirstString((player as any).photo, (player as any).imageUrl) || DEFAULT_PLAYER_PHOTO,
    raw: player as Player,
  };
};

const matchesPositionSelection = (player: ScoutingTargetView, selectedPosition: string): boolean => {
  if (selectedPosition === 'all') {
    return true;
  }

  const normalizedSelection = selectedPosition.toUpperCase();
  const selectionGroup = resolvePositionGroup(normalizedSelection);

  if (normalizedSelection === selectionGroup) {
    return player.positionGroup === selectionGroup;
  }

  return player.positionTokens.includes(normalizedSelection);
};

const matchesAdvancedFilters = (player: ScoutingTargetView, filters: AdvancedScoutingFilters): boolean => {
  if (filters.nationality !== 'all' && player.nationality !== filters.nationality) {
    return false;
  }

  if (filters.club !== 'all' && player.club !== filters.club) {
    return false;
  }

  if (filters.preferredFoot !== 'all' && player.preferredFoot !== filters.preferredFoot) {
    return false;
  }

  const minimumRating = toFiniteNumber(filters.minimumRating, 0);
  if (minimumRating > 0 && player.rating < minimumRating) {
    return false;
  }

  const maximumMarketValueMillions = toFiniteNumber(filters.maximumMarketValue, 0);
  if (maximumMarketValueMillions > 0) {
    if (player.marketValueNumeric <= 0 || player.marketValueNumeric > maximumMarketValueMillions * 1000000) {
      return false;
    }
  }

  const minimumPassAccuracy = toFiniteNumber(filters.minimumPassAccuracy, 0);
  if (minimumPassAccuracy > 0 && player.passAccuracy < minimumPassAccuracy) {
    return false;
  }

  if (filters.requiresEventData && !player.hasEventData) {
    return false;
  }

  return true;
};

const countActiveAdvancedFilters = (filters: AdvancedScoutingFilters): number => {
  let count = 0;
  if (filters.nationality !== 'all') count += 1;
  if (filters.club !== 'all') count += 1;
  if (filters.preferredFoot !== 'all') count += 1;
  if (filters.minimumRating.trim()) count += 1;
  if (filters.maximumMarketValue.trim()) count += 1;
  if (filters.minimumPassAccuracy.trim()) count += 1;
  if (filters.requiresEventData) count += 1;
  return count;
};

const computeScoutingScore = (player: ScoutingTargetView, selectedPosition: string): number => {
  const selectionGroup = selectedPosition === 'all'
    ? player.positionGroup
    : (resolvePositionGroup(selectedPosition) || player.positionGroup);
  const ageUpside = player.age == null ? 4 : player.age <= 21 ? 12 : player.age <= 24 ? 10 : player.age <= 28 ? 6 : 2;
  const valueAdjustment = player.marketValueNumeric > 0
    ? Math.max(0, 12 - (player.marketValueNumeric / 25000000))
    : 4;
  const generalScore = player.rating * 7 + player.passAccuracy * 0.18 + player.goals * 4 + player.assists * 3 + player.xG * 4 + player.xA * 4;

  if (selectionGroup === 'GK') {
    return generalScore + player.rating * 4 + player.passAccuracy * 0.22 + ageUpside + valueAdjustment;
  }

  if (selectionGroup === 'DF') {
    return generalScore + player.rating * 3 + player.passAccuracy * 0.28 + player.assists * 2 + ageUpside + valueAdjustment;
  }

  if (selectionGroup === 'MF') {
    return generalScore + player.passAccuracy * 0.4 + player.assists * 3 + player.xA * 5 + ageUpside + valueAdjustment;
  }

  if (selectionGroup === 'FW') {
    return generalScore + player.goals * 6 + player.xG * 6 + player.assists * 2 + ageUpside + valueAdjustment;
  }

  return generalScore + ageUpside + valueAdjustment;
};

const buildRecommendationSummary = (player: ScoutingTargetView, positionLabel: string): string => {
  const signals: string[] = [];

  if (player.rating > 0) {
    signals.push(`${player.rating.toFixed(1)} rating`);
  }
  if (player.goals > 0) {
    signals.push(`${player.goals} goals`);
  }
  if (player.assists > 0) {
    signals.push(`${player.assists} assists`);
  }
  if (player.passAccuracy > 0) {
    signals.push(`${Math.round(player.passAccuracy)}% pass accuracy`);
  }
  if (player.xG > 0) {
    signals.push(`${player.xG.toFixed(1)} xG`);
  }
  if (player.xA > 0) {
    signals.push(`${player.xA.toFixed(1)} xA`);
  }

  const lead = `${player.club} • ${player.displayPosition}.`;
  if (signals.length === 0) {
    return `${lead} Clean profile for the ${positionLabel.toLowerCase()} shortlist, but live event metrics are still sparse.`;
  }

  return `${lead} ${signals.slice(0, 3).join(', ')} make this profile worth immediate scouting review.`;
};

const buildScoutingSummary = (
  player: ScoutingTargetView,
  positionLabel: string,
  snapshot?: PlayerScoutingPayload,
): string => {
  const phase = normalizePhaseLabel(snapshot?.scoutingProfile?.developmentCurve?.phase);
  const valuation = resolveScoutingValuation(snapshot)?.displayValue;
  const progressionValue = toFiniteNumber(snapshot?.scoutingProfile?.ballProgression?.progressionValuePer90);

  if (phase || valuation || progressionValue > 0) {
    const highlights = [
      phase ? `${phase} development phase` : null,
      valuation ? `model value ${valuation}` : null,
      progressionValue > 0 ? `${progressionValue.toFixed(2)} progression value/90` : null,
    ].filter((signal): signal is string => Boolean(signal));

    return `${player.club} • ${player.displayPosition}. ${highlights.join(', ')} support this ${positionLabel.toLowerCase()} shortlist case.`;
  }

  return buildRecommendationSummary(player, positionLabel);
};

const buildRecommendation = (
  player: ScoutingTargetView,
  score: number,
  positionLabel: string,
  index: number,
  timestamp: string,
  snapshot?: PlayerScoutingPayload,
): AIInsight => {
  const availableSignals = [
    player.rating > 0,
    player.age != null,
    player.passAccuracy > 0,
    player.goals + player.assists > 0,
    player.xG + player.xA > 0,
    player.marketValueNumeric > 0,
  ].filter(Boolean).length;
  const confidence = Math.min(0.96, 0.48 + availableSignals * 0.08 + Math.min(score / 200, 0.12));
  const headline = score >= 80
    ? `${player.name} is a priority ${positionLabel.toLowerCase()} target`
    : `${player.name} merits a live scouting review`;

  return {
    id: `scouting-reco-${player.id}-${index}`,
    type: 'recommendation',
    title: headline,
    description: buildScoutingSummary(player, positionLabel, snapshot),
    confidence,
    relatedEntityId: player.id,
    relatedEntityType: 'player',
    data: {
      score: Number(score.toFixed(1)),
      club: player.club,
      positionLabel: player.displayPosition,
      ageLabel: player.ageLabel,
      marketValueLabel: resolveScoutingValuation(snapshot)?.displayValue || player.marketValueLabel,
      phaseLabel: normalizePhaseLabel(snapshot?.scoutingProfile?.developmentCurve?.phase),
    },
    createdAt: timestamp,
    updatedAt: timestamp,
  };
};

const ScoutingDashboard: React.FC<ScoutingDashboardProps> = ({ onPlayerSelect, onOpenModelCenter }) => {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedPosition, setSelectedPosition] = React.useState<string>('all');
  const [ageRange, setAgeRange] = React.useState({ min: 16, max: 45 });
  const [selectedPlayer, setSelectedPlayer] = React.useState<Player | null>(null);
  const [showFeatureLens, setShowFeatureLens] = React.useState(false);
  const [scoutingSnapshots, setScoutingSnapshots] = React.useState<Record<string, PlayerScoutingPayload>>({});

  const selectedPositionOption = React.useMemo(
    () => POSITION_OPTIONS.find((option) => option.value === selectedPosition) || POSITION_OPTIONS[0],
    [selectedPosition],
  );

  const { data: targetPlayers, loading: targetsLoading } = useApi(
    () => apiService.getPlayers({
      position: selectedPositionOption.serverFilter ? [selectedPositionOption.serverFilter] : undefined,
      ageMin: ageRange.min,
      ageMax: ageRange.max,
    }, {
      search: searchTerm.trim() || undefined,
      limit: 200,
    }),
    [selectedPositionOption.serverFilter, ageRange.min, ageRange.max, searchTerm]
  );

  const scoutingTargets = React.useMemo(
    () => (Array.isArray(targetPlayers) ? targetPlayers : [])
      .map((player, index) => normalizeScoutingTarget(player, index))
      .filter((player) => matchesPositionSelection(player, selectedPosition)),
    [targetPlayers, selectedPosition]
  );

  const rankedTargets = React.useMemo(
    () => scoutingTargets
      .map((player) => ({ player, score: computeScoutingScore(player, selectedPosition) }))
      .sort((left, right) => right.score - left.score || right.player.rating - left.player.rating || left.player.name.localeCompare(right.player.name)),
    [scoutingTargets, selectedPosition]
  );

  React.useEffect(() => {
    const idsToHydrate = rankedTargets.slice(0, 8).map(({ player }) => player.id).filter((playerId) => !scoutingSnapshots[playerId]);
    if (!idsToHydrate.length) {
      return undefined;
    }

    let cancelled = false;

    Promise.allSettled(idsToHydrate.map((playerId) => apiService.getPlayerScoutingProfile(playerId)))
      .then((results) => {
        if (cancelled) {
          return;
        }

        setScoutingSnapshots((current) => {
          const next = { ...current };

          results.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value.success && result.value.data) {
              next[idsToHydrate[index]] = result.value.data as PlayerScoutingPayload;
            }
          });

          return next;
        });
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, [rankedTargets, scoutingSnapshots]);

  const aiRecommendations = React.useMemo<AIInsight[]>(() => {
    const timestamp = new Date().toISOString();
    return rankedTargets.slice(0, 5).map(({ player, score }, index) => (
      buildRecommendation(player, score, selectedPositionOption.label, index, timestamp, scoutingSnapshots[player.id])
    ));
  }, [rankedTargets, scoutingSnapshots, selectedPositionOption.label]);

  const aiLoading = targetsLoading;
  const shortlistCount = rankedTargets.filter(({ score }) => score >= 55).length;
  const visibleTargets = rankedTargets.map(({ player }) => player);
  const recentActivity = aiRecommendations.slice(0, 3).map((insight) => ({
    id: insight.id,
    message: insight.title,
    detail: insight.description,
  }));

  const handlePlayerClick = (player: Player) => {
    if (onPlayerSelect) {
      onPlayerSelect(player);
      return;
    }

    setSelectedPlayer(player);
  };

  const resetFilters = () => {
    setSearchTerm('');
    setSelectedPosition('all');
    setAgeRange({ min: 16, max: 45 });
  };

  if (selectedPlayer) {
    return <PlayerDetail player={selectedPlayer} onBack={() => setSelectedPlayer(null)} onOpenModelCenter={onOpenModelCenter} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Scouting Dashboard</h1>
          <p className="text-slate-400 mt-1">Discover and analyze potential transfer targets</p>
          <p className="text-xs text-slate-500 mt-2">
            Lens: {selectedPositionOption.label} • Age {ageRange.min}-{ageRange.max}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowFeatureLens((current) => !current)}
            className="bg-slate-700 text-white px-4 py-2 rounded-lg hover:bg-slate-600 transition-colors flex items-center space-x-2"
          >
            <BarChart3 className="w-4 h-4" />
            <span>{showFeatureLens ? 'Hide Lens' : 'Feature Lens'}</span>
          </button>
          <button
            onClick={() => onOpenModelCenter?.('interactive')}
            className="bg-slate-700 text-white px-4 py-2 rounded-lg hover:bg-slate-600 transition-colors flex items-center space-x-2"
          >
            <Brain className="w-4 h-4" />
            <span>Use Models</span>
          </button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
            <Target className="w-4 h-4" />
            <span>Add Target</span>
          </button>
        </div>
      </div>

      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 overflow-hidden">
        <button
          onClick={() => setShowFeatureLens((current) => !current)}
          className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-slate-700/40 transition-colors"
        >
          <div>
            <div className="flex items-center gap-2 text-lg font-semibold text-white">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              Scouting Feature Lens
            </div>
            <div className="mt-1 text-sm text-slate-400">
              Compare single events, possession-style windows, and lagged history without leaving the scouting shortlist.
            </div>
          </div>
          {showFeatureLens ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
        </button>

        {showFeatureLens && (
          <div className="border-t border-slate-700 p-6 bg-slate-900/30">
            <ModelCenterLens
              title="Scouting Feature Lens"
              description="Use the shared event and parameter lens directly inside scouting to compare shot-level, sequence-window, and lagged-history patterns before deciding which players deserve deeper review."
              datasetHeading="Scouting Lens Datasets"
              datasetDescription="Switch datasets here while staying on the shortlist. Saved lens presets and temporal filters carry over from ML Laboratory and Model Center."
              modelsHeading="Scouting-Relevant Models"
              modelsDescription="These are the connected models whose event families and temporal assumptions match the current scouting lens."
            />
          </div>
        )}
      </div>

      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search players or clubs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-400"
            />
          </div>

          <select
            value={selectedPosition}
            onChange={(e) => setSelectedPosition(e.target.value)}
            className="px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {POSITION_OPTIONS.map((position) => (
              <option key={position.value} value={position.value}>
                {position.label}
              </option>
            ))}
          </select>

          <div className="flex items-center space-x-2">
            <input
              type="number"
              placeholder="Min age"
              value={ageRange.min}
              onChange={(e) => setAgeRange((prev) => ({ ...prev, min: parseInt(e.target.value, 10) || 16 }))}
              className="w-20 px-3 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-400"
            />
            <span className="text-slate-400">-</span>
            <input
              type="number"
              placeholder="Max age"
              value={ageRange.max}
              onChange={(e) => setAgeRange((prev) => ({ ...prev, max: parseInt(e.target.value, 10) || 45 }))}
              className="w-20 px-3 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-400"
            />
          </div>

          <button
            onClick={resetFilters}
            className="flex items-center justify-center space-x-2 px-4 py-2 border border-slate-600 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
          >
            <Filter className="w-4 h-4" />
            <span>Reset Filters</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center space-x-2">
                <Brain className="w-5 h-5 text-purple-600" />
                <h2 className="text-xl font-semibold text-white">AI Recommendations</h2>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Prioritized from the current {selectedPositionOption.label.toLowerCase()} shortlist.
              </p>
            </div>
            <div className="p-6">
              {aiLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
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
              ) : aiRecommendations.length > 0 ? (
                <div className="space-y-4">
                  {aiRecommendations.map((insight) => (
                    <div key={insight.id} className="flex items-start space-x-4 p-4 bg-purple-900/20 rounded-lg border border-purple-800/30">
                      <div className="w-2 h-2 bg-purple-600 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-3">
                          <h3 className="font-medium text-white">{insight.title}</h3>
                          <div className="flex items-center gap-1 text-xs text-emerald-300">
                            <TrendingUp className="w-3 h-3" />
                            <span>Score {Number((insight.data?.score ?? 0)).toFixed(1)}</span>
                          </div>
                        </div>
                        <p className="text-sm text-slate-400 mt-1">{insight.description}</p>
                        <div className="flex flex-wrap items-center gap-2 mt-3">
                          <span className="text-xs bg-purple-900/40 text-purple-300 px-2 py-1 rounded">
                            {Math.round(insight.confidence * 100)}% confidence
                          </span>
                          <span className="text-xs bg-slate-900/60 text-slate-200 px-2 py-1 rounded">
                            {String(insight.data?.positionLabel || 'Role unavailable')}
                          </span>
                          <span className="text-xs bg-slate-900/60 text-slate-200 px-2 py-1 rounded">
                            {String(insight.data?.ageLabel || 'Age unavailable')}
                          </span>
                          <span className="text-xs bg-slate-900/60 text-slate-200 px-2 py-1 rounded">
                            {String(insight.data?.marketValueLabel || 'Value unavailable')}
                          </span>
                          {insight.data?.phaseLabel ? (
                            <span className="text-xs bg-cyan-500/10 text-cyan-200 px-2 py-1 rounded">
                              {String(insight.data.phaseLabel)}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400">No AI recommendations available for the current scouting lens.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Scouting Overview</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Active Targets</span>
                <span className="font-semibold text-blue-400">
                  {targetsLoading ? '...' : visibleTargets.length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Recommended Now</span>
                <span className="font-semibold text-green-400">{aiRecommendations.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Shortlist Grade</span>
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

      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700">
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Search Results</h2>
              <p className="text-xs text-slate-500 mt-2">Filtered by {selectedPositionOption.label.toLowerCase()} and current age band.</p>
            </div>
            <span className="text-sm text-slate-400">
              {targetsLoading ? 'Loading...' : `${visibleTargets.length} players found`}
            </span>
          </div>
        </div>
        <div className="p-6">
          {targetsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
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
          ) : visibleTargets.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {rankedTargets.map(({ player, score }) => (
                (() => {
                  const snapshot = scoutingSnapshots[player.id];
                  const valuationLabel = resolveScoutingValuation(snapshot)?.displayValue || player.marketValueLabel;
                  const phaseLabel = normalizePhaseLabel(snapshot?.scoutingProfile?.developmentCurve?.phase);

                  return (
                <div
                  key={player.id}
                  onClick={() => handlePlayerClick(player.raw)}
                  className="border border-slate-700 rounded-lg p-4 hover:shadow-md hover:border-slate-600 transition-all cursor-pointer bg-slate-900/50"
                >
                  <div className="flex items-center space-x-4">
                    <img
                      src={player.photo}
                      alt={player.name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h3 className="font-medium text-white truncate">{player.name}</h3>
                          <p className="text-sm text-slate-400 truncate">{player.displayPosition} • {player.club}</p>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-amber-300 whitespace-nowrap">
                          <TrendingUp className="w-3 h-3" />
                          <span>{score.toFixed(1)}</span>
                        </div>
                      </div>
                      <div className="flex items-center flex-wrap gap-2 mt-2">
                        <span className="text-xs bg-blue-900/40 text-blue-300 px-2 py-1 rounded">{player.ageLabel}</span>
                        <span className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">{valuationLabel}</span>
                        {phaseLabel ? (
                          <span className="text-xs bg-cyan-500/10 text-cyan-200 px-2 py-1 rounded">{phaseLabel}</span>
                        ) : null}
                        <span className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">
                          Rating {player.rating > 0 ? player.rating.toFixed(1) : '—'}
                        </span>
                      </div>
                    </div>
                    <Star className="w-4 h-4 text-slate-600 hover:text-yellow-500" />
                  </div>
                  <div className="grid grid-cols-3 gap-2 mt-4 text-xs">
                    <div className="rounded bg-slate-800/70 px-2 py-2">
                      <div className="text-slate-500">Goals</div>
                      <div className="text-white font-medium">{player.goals > 0 ? player.goals : '—'}</div>
                    </div>
                    <div className="rounded bg-slate-800/70 px-2 py-2">
                      <div className="text-slate-500">Assists</div>
                      <div className="text-white font-medium">{player.assists > 0 ? player.assists : '—'}</div>
                    </div>
                    <div className="rounded bg-slate-800/70 px-2 py-2">
                      <div className="text-slate-500">Pass Acc.</div>
                      <div className="text-white font-medium">{player.passAccuracy > 0 ? `${Math.round(player.passAccuracy)}%` : '—'}</div>
                    </div>
                  </div>
                </div>
                  );
                })()
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">No players found</h3>
              <p className="text-slate-400">Try widening the {selectedPositionOption.label.toLowerCase()} filter or adjusting the age range.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScoutingDashboard;