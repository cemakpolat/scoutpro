import type { MLDatasetFeatureInsights } from '../types';

export interface FeatureLensPreset {
  id: string;
  name: string;
  eventFamily: string;
  temporalScope: string;
  eventType: string;
  fields: string[];
  datasetId?: string;
  isDefault?: boolean;
}

const FEATURE_LENS_STORAGE_KEY = 'scoutpro.featureLensPresets.v1';

export const DEFAULT_FEATURE_LENS_PRESETS: FeatureLensPreset[] = [
  {
    id: 'shot-quality',
    name: 'Shot Quality',
    eventFamily: 'shots',
    temporalScope: 'single_event',
    eventType: 'shot',
    datasetId: 'ds-match-events',
    fields: ['location.x', 'location.y', 'timestamp_seconds', 'is_successful', 'is_goal', 'type_id'],
    isDefault: true,
  },
  {
    id: 'buildup-passing',
    name: 'Buildup Passing',
    eventFamily: 'passing',
    temporalScope: 'sequence_window',
    eventType: 'pass',
    datasetId: 'ds-match-events',
    fields: ['sequence.event_count', 'sequence.duration_seconds', 'sequence.progression_x', 'sequence.success_rate', 'event_counts.pass', 'sequence.avg_location_x'],
    isDefault: true,
  },
  {
    id: 'fatigue-workload',
    name: 'Fatigue vs Workload',
    eventFamily: 'workload',
    temporalScope: 'rolling_form',
    eventType: 'all',
    datasetId: 'ds-player-statistics',
    fields: ['current.matches_played', 'window.matches_played', 'current.pass_accuracy', 'window.pass_accuracy', 'current.duel_win_rate', 'window.duel_win_rate'],
    isDefault: true,
  },
];

export function prettifyLensToken(value: string): string {
  return String(value || '')
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function formatInsightNumber(value: number | null, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }

  return value.toFixed(digits);
}

export function stringArraysEqual(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((value, index) => value === right[index]);
}

export function correlationTone(coefficient: number): string {
  if (coefficient >= 0.6) {
    return 'bg-green-500/20 text-green-200';
  }

  if (coefficient <= -0.6) {
    return 'bg-red-500/20 text-red-200';
  }

  return 'bg-slate-700 text-slate-200';
}

export function getStoredFeatureLensPresets(): FeatureLensPreset[] {
  if (typeof window === 'undefined') {
    return DEFAULT_FEATURE_LENS_PRESETS;
  }

  try {
    const raw = window.localStorage.getItem(FEATURE_LENS_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    const customPresets = Array.isArray(parsed)
      ? parsed.filter((preset) => preset && typeof preset.id === 'string' && typeof preset.name === 'string')
      : [];
    return [...DEFAULT_FEATURE_LENS_PRESETS, ...customPresets];
  } catch {
    return DEFAULT_FEATURE_LENS_PRESETS;
  }
}

export function saveCustomFeatureLensPreset(preset: FeatureLensPreset): FeatureLensPreset[] {
  if (typeof window === 'undefined') {
    return DEFAULT_FEATURE_LENS_PRESETS;
  }

  const existingCustomPresets = getStoredFeatureLensPresets().filter((entry) => !entry.isDefault);
  const nextCustomPresets = [
    ...existingCustomPresets.filter((entry) => entry.id !== preset.id),
    { ...preset, isDefault: false },
  ];
  window.localStorage.setItem(FEATURE_LENS_STORAGE_KEY, JSON.stringify(nextCustomPresets));
  return [...DEFAULT_FEATURE_LENS_PRESETS, ...nextCustomPresets];
}

export function deleteCustomFeatureLensPreset(presetId: string): FeatureLensPreset[] {
  if (typeof window === 'undefined') {
    return DEFAULT_FEATURE_LENS_PRESETS;
  }

  const nextCustomPresets = getStoredFeatureLensPresets()
    .filter((entry) => !entry.isDefault && entry.id !== presetId)
    .map((entry) => ({ ...entry, isDefault: false }));
  window.localStorage.setItem(FEATURE_LENS_STORAGE_KEY, JSON.stringify(nextCustomPresets));
  return [...DEFAULT_FEATURE_LENS_PRESETS, ...nextCustomPresets];
}

export function deriveCorrelationLookup(featureInsights: MLDatasetFeatureInsights | null): Map<string, number> {
  const lookup = new Map<string, number>();
  (featureInsights?.correlations || []).forEach((entry) => {
    lookup.set(`${entry.left}::${entry.right}`, entry.coefficient);
    lookup.set(`${entry.right}::${entry.left}`, entry.coefficient);
  });
  return lookup;
}