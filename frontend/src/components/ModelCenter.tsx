import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  Clock3,
  Cpu,
  ListChecks,
  Sparkles,
  Target,
  Users,
} from 'lucide-react';
import ClusteringExplorer from './ClusteringExplorer';
import ModelCenterLens from './ModelCenterLens';
import TaskQueue from './TaskQueue';
import PlayerTrajectory from './PlayerTrajectory';
import TeamAssessment from './TeamAssessment';

export type ModelCenterTab = 'navigator' | 'team' | 'clusters' | 'lens' | 'batch' | 'trajectory';
export type ModelCenterInteractivePanel = 'similar' | 'performance';

export interface ModelCenterContext {
  playerId?: string;
  matchId?: string;
  teamId?: string;
  interactivePanel?: ModelCenterInteractivePanel;
  lensPresetId?: string;
}

interface ModelCenterProps {
  onNavigate: (tab: string) => void;
  initialTab?: ModelCenterTab;
  initialPlayerId?: string;
  initialTeamId?: string;
  initialLensPresetId?: string;
}

type AreaAction = {
  label: string;
  tab: string;
};

type AreaCard = {
  id: string;
  title: string;
  status: 'live' | 'partial' | 'planned';
  description: string;
  highlights: string[];
  actions: AreaAction[];
};

const AREA_CARDS: AreaCard[] = [
  {
    id: 'player',
    title: 'Player Assessment',
    status: 'live',
    description: 'Player profiles expose tactical role clustering, anomaly detection, rolling form, and expected metrics.',
    highlights: [
      'Open player detail pages to see actionable ML cards next to event-driven analytics.',
      'Use Player Comparison for similar-player search backed by ML similarity endpoints.',
    ],
    actions: [
      { label: 'Player Profiles', tab: 'players' },
      { label: 'Scouting Hub', tab: 'scouting' },
      { label: 'Player Comparison', tab: 'player-comparison' },
      { label: 'Player Trajectory', tab: 'trajectory' },
    ],
  },
  {
    id: 'match',
    title: 'Match Assessment',
    status: 'live',
    description: 'Match analysis covers shot maps, tactical metrics, sequence insights, and multi-match comparative and trend analysis.',
    highlights: [
      'Match Analysis shows tactical metrics, possession sequences, and shot-map level chance quality.',
      'Multi-Match Analysis supports comparative, trend, and predictive views.',
    ],
    actions: [
      { label: 'Match Analysis', tab: 'match-analysis' },
      { label: 'Multi-Match Analysis', tab: 'multi-match' },
    ],
  },
  {
    id: 'team',
    title: 'Team Assessment',
    status: 'live',
    description: 'Model Center now exposes a dedicated team assessment surface backed by team stats, insights, rankings, team-to-team comparison, forecast snapshots, and explainable risk flags.',
    highlights: [
      'Open Team Assessment here for direct team stats, forecast snapshots, risk flags, and side-by-side comparison.',
      'Analytics Lab still complements this with competition-level output and trend context.',
      'Use prefilled team workflows from analytics cards to jump straight into the selected team context.',
    ],
    actions: [
      { label: 'Open Team Assessment', tab: 'team' },
      { label: 'Analytics Lab', tab: 'analytics' },
      { label: 'Match Centre', tab: 'match-centre' },
    ],
  },
  {
    id: 'operations',
    title: 'Training And Experiment Ops',
    status: 'live',
    description: 'Use the ML Laboratory to train pipelines, monitor experiment history, and confirm which models are ready to consume here.',
    highlights: [
      'ML Laboratory is now the operational home for training and experiment status.',
      'This Model Center is the user-facing home for interactive usage and batch prediction flows.',
      'Expanded experiment details now drill directly into the matching consumption surface from ML Laboratory.',
    ],
    actions: [
      { label: 'Open ML Laboratory', tab: 'ml-lab' },
    ],
  },
];

const MISSING_SURFACES = [
  'Deeper cluster drill-downs that link archetypes to full player cohorts and filters.',
];

function statusTone(status: AreaCard['status']) {
  switch (status) {
    case 'live':
      return 'bg-green-500/15 text-green-300 border-green-500/30';
    case 'partial':
      return 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30';
    default:
      return 'bg-slate-500/15 text-slate-300 border-slate-500/30';
  }
}

const ModelCenter: React.FC<ModelCenterProps> = ({
  onNavigate,
  initialTab = 'navigator',
  initialPlayerId,
  initialTeamId,
  initialLensPresetId,
}) => {
  const [activeTab, setActiveTab] = useState<ModelCenterTab>(initialTab);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  const handleAction = (tab: string) => {
    if (tab === 'navigator' || tab === 'team' || tab === 'clusters' || tab === 'lens' || tab === 'batch' || tab === 'trajectory') {
      setActiveTab(tab as ModelCenterTab);
      return;
    }

    onNavigate(tab);
  };

  const statusCounts = useMemo(() => {
    return AREA_CARDS.reduce(
      (accumulator, card) => {
        accumulator[card.status] += 1;
        return accumulator;
      },
      { live: 0, partial: 0, planned: 0 },
    );
  }, []);

  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-slate-700 bg-gradient-to-br from-slate-800 via-slate-800 to-slate-900 p-6 lg:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-300">
              <Sparkles className="h-3.5 w-3.5" />
              Model Consumption Hub
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Model Center</h1>
              <p className="mt-2 text-slate-300">
                Train models in ML Laboratory, then use them here. This page brings together interactive predictions,
                batch model tasks, and clear entry points into the existing player, match, and team assessment surfaces.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:w-[420px]">
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-400">Live Surfaces</div>
              <div className="mt-2 text-2xl font-bold text-green-400">{statusCounts.live}</div>
              <div className="mt-1 text-xs text-slate-500">Ready for direct usage now</div>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-400">Partial Surfaces</div>
              <div className="mt-2 text-2xl font-bold text-yellow-400">{statusCounts.partial}</div>
              <div className="mt-1 text-xs text-slate-500">Visible but still missing drill-downs</div>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-400">Missing Next</div>
              <div className="mt-2 text-2xl font-bold text-blue-400">{MISSING_SURFACES.length}</div>
              <div className="mt-1 text-xs text-slate-500">Tracked in the implementation todo</div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 rounded-xl border border-slate-700 bg-slate-800 p-2">
        {[
          { id: 'navigator' as const, label: 'Assessment Navigator', icon: Target },
          { id: 'team' as const, label: 'Team Assessment', icon: Users },
          { id: 'clusters' as const, label: 'Clustering Explorer', icon: Brain },
          { id: 'lens' as const, label: 'Feature Lens', icon: BarChart3 },
          { id: 'batch' as const, label: 'Batch Tasks', icon: ListChecks },
          { id: 'trajectory' as const, label: 'Player Trajectory', icon: Activity },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === id
                ? 'bg-cyan-500 text-slate-950'
                : 'text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'navigator' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[2fr,1fr]">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {AREA_CARDS.map((card) => (
                <div key={card.id} className="rounded-xl border border-slate-700 bg-slate-800 p-6">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-semibold text-white">{card.title}</h2>
                      <p className="mt-2 text-sm text-slate-300">{card.description}</p>
                    </div>
                    <span className={`inline-flex shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium ${statusTone(card.status)}`}>
                      {card.status}
                    </span>
                  </div>

                  <div className="mt-4 space-y-2">
                    {card.highlights.map((highlight) => (
                      <div key={highlight} className="flex items-start gap-2 text-sm text-slate-400">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cyan-400" />
                        <span>{highlight}</span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-5 flex flex-wrap gap-2">
                    {card.actions.map((action) => (
                      <button
                        key={`${card.id}-${action.tab}`}
                        onClick={() => handleAction(action.tab)}
                        className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-200 transition-colors hover:border-cyan-400 hover:text-white"
                      >
                        {action.label}
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-6">
              <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
                <div className="flex items-center gap-2 text-lg font-semibold text-white">
                  <Clock3 className="h-5 w-5 text-yellow-400" />
                  Missing Next
                </div>
                <div className="mt-4 space-y-3">
                  {MISSING_SURFACES.map((item) => (
                    <div key={item} className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-3 text-sm text-slate-300">
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
                <div className="flex items-center gap-2 text-lg font-semibold text-white">
                  <Cpu className="h-5 w-5 text-blue-400" />
                  Quick Actions
                </div>
                <div className="mt-4 space-y-3">
                  <button
                    onClick={() => setActiveTab('team')}
                    className="flex w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-left text-sm text-slate-200 transition-colors hover:border-cyan-400 hover:text-white"
                  >
                    <span>Open Team Assessment</span>
                    <ArrowRight className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setActiveTab('clusters')}
                    className="flex w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-left text-sm text-slate-200 transition-colors hover:border-cyan-400 hover:text-white"
                  >
                    <span>Explore player archetype clusters</span>
                    <ArrowRight className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setActiveTab('batch')}
                    className="flex w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-left text-sm text-slate-200 transition-colors hover:border-cyan-400 hover:text-white"
                  >
                    <span>Queue a background batch task</span>
                    <ArrowRight className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onNavigate('ml-lab')}
                    className="flex w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-left text-sm text-slate-200 transition-colors hover:border-cyan-400 hover:text-white"
                  >
                    <span>Open ML Laboratory</span>
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'team' && <TeamAssessment initialTeamId={initialTeamId} />}

      {activeTab === 'clusters' && <ClusteringExplorer initialPlayerId={initialPlayerId} />}

      {activeTab === 'lens' && <ModelCenterLens initialPresetId={initialLensPresetId} />}

      {activeTab === 'batch' && (
        <div className="space-y-6">
          <div className="flex flex-col gap-4 rounded-xl border border-slate-700 bg-slate-800 p-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Background Model Tasks</h2>
              <p className="mt-1 text-sm text-slate-400">
                Submit clustering, prediction, training, export, and reporting jobs without leaving the frontend. This is the first visible batch operations surface.
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
              <Activity className="h-3.5 w-3.5 text-green-400" />
              Results stream back into the task history automatically
            </div>
          </div>

          <TaskQueue />
        </div>
      )}
      {activeTab === 'trajectory' && (
        <div className="space-y-6">
          <PlayerTrajectory playerId={initialPlayerId} />
        </div>
      )}
    </div>
  );
};

export default ModelCenter;