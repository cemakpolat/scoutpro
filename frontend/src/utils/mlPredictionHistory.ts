export type InteractivePredictionType = 'player-performance' | 'match-outcome';

export interface InteractivePredictionRun {
  id: string;
  type: InteractivePredictionType;
  title: string;
  summary: string;
  createdAt: string;
  saved: boolean;
  input: Record<string, unknown>;
  result: Record<string, unknown>;
  context?: Record<string, string>;
}

const INTERACTIVE_PREDICTION_HISTORY_KEY = 'scoutpro.interactivePredictionRuns.v1';
const MAX_INTERACTIVE_PREDICTION_RUNS = 40;

function readPredictionRuns(): InteractivePredictionRun[] {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const rawValue = window.localStorage.getItem(INTERACTIVE_PREDICTION_HISTORY_KEY);
    const parsedValue = rawValue ? JSON.parse(rawValue) : [];
    return Array.isArray(parsedValue)
      ? parsedValue.filter((entry) => entry && typeof entry.id === 'string' && typeof entry.type === 'string')
      : [];
  } catch {
    return [];
  }
}

function writePredictionRuns(runs: InteractivePredictionRun[]) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(INTERACTIVE_PREDICTION_HISTORY_KEY, JSON.stringify(runs));
}

export function getInteractivePredictionRuns(type?: InteractivePredictionType): InteractivePredictionRun[] {
  const runs = readPredictionRuns().sort((left, right) => right.createdAt.localeCompare(left.createdAt));
  return type ? runs.filter((entry) => entry.type === type) : runs;
}

export function recordInteractivePredictionRun(
  run: Omit<InteractivePredictionRun, 'id' | 'createdAt' | 'saved'> & { saved?: boolean },
): InteractivePredictionRun {
  const nextRun: InteractivePredictionRun = {
    ...run,
    id: `${run.type}-${Date.now()}`,
    createdAt: new Date().toISOString(),
    saved: Boolean(run.saved),
  };

  const nextRuns = [nextRun, ...readPredictionRuns()].slice(0, MAX_INTERACTIVE_PREDICTION_RUNS);
  writePredictionRuns(nextRuns);
  return nextRun;
}

export function toggleSavedInteractivePredictionRun(runId: string): InteractivePredictionRun[] {
  const nextRuns = readPredictionRuns().map((entry) => (
    entry.id === runId ? { ...entry, saved: !entry.saved } : entry
  ));
  writePredictionRuns(nextRuns);
  return nextRuns.sort((left, right) => right.createdAt.localeCompare(left.createdAt));
}

export function deleteInteractivePredictionRun(runId: string): InteractivePredictionRun[] {
  const nextRuns = readPredictionRuns().filter((entry) => entry.id !== runId);
  writePredictionRuns(nextRuns);
  return nextRuns.sort((left, right) => right.createdAt.localeCompare(left.createdAt));
}