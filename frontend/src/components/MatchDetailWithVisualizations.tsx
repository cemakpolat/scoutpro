import React, { useState, useEffect } from 'react';
import { ArrowLeft, ChevronDown, ChevronUp, Activity, Target, TrendingUp } from 'lucide-react';
import { ShotMap, HeatMap, PassNetwork } from './visualizations';
import ErrorBoundary from './ErrorBoundary';
import apiService from '../services/api';

interface MatchDetailWithVisualizationsProps {
  matchId: string;
  homeTeam?: string;
  awayTeam?: string;
  homeTeamId?: string;
  awayTeamId?: string;
  homeScore?: number;
  awayScore?: number;
  onBack?: () => void;
}

function TacticalMetricsPanel({ matchId }: { matchId: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiService.getMatchTacticalMetrics(matchId)
      .then(r => setData(r.success ? r.data : null))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [matchId]);

  if (loading) return <p className="text-slate-400 text-sm animate-pulse">Loading tactical metrics…</p>;
  if (!data || !data.tactical_metrics) return <p className="text-slate-500 text-sm">No tactical data available.</p>;

  const teams: string[] = data.teams || Object.keys(data.tactical_metrics);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {teams.map((teamId: string) => {
        const m = data.tactical_metrics[teamId];
        if (!m) return null;
        const zones = m.possession_zones_pct || {};
        return (
          <div key={teamId} className="bg-slate-700 rounded-lg p-4 space-y-3">
            <h4 className="font-semibold text-sm text-slate-200">Team {teamId}</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-slate-400 text-xs">PPDA</p>
                <p className="text-white font-bold">{m.ppda}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Press style</p>
                <p className="text-white font-bold capitalize">{m.press_style}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Passes</p>
                <p className="text-white font-bold">{m.passes}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Defensive actions</p>
                <p className="text-white font-bold">{m.defensive_actions}</p>
              </div>
            </div>
            {Object.keys(zones).length > 0 && (
              <div>
                <p className="text-slate-400 text-xs mb-1">Possession zones</p>
                <div className="flex gap-1 h-4">
                  {(['defensive', 'middle', 'attacking'] as const).map(z => (
                    <div
                      key={z}
                      style={{ width: `${zones[z] ?? 33}%` }}
                      className={`rounded text-xs flex items-center justify-center text-white ${
                        z === 'defensive' ? 'bg-red-600' : z === 'middle' ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      title={`${z}: ${zones[z]}%`}
                    >
                      {(zones[z] ?? 0) > 15 ? `${zones[z]}%` : ''}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 mt-1 text-xs text-slate-400">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 bg-red-600 rounded" />Def {zones.defensive ?? 0}%</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 bg-yellow-600 rounded" />Mid {zones.middle ?? 0}%</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-600 rounded" />Att {zones.attacking ?? 0}%</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function SequenceInsightsPanel({ matchId }: { matchId: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiService.getMatchSequenceInsights(matchId)
      .then(r => setData(r.success ? r.data : null))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [matchId]);

  if (loading) return <p className="text-slate-400 text-sm animate-pulse">Loading sequence data…</p>;
  if (!data || (!data.teamSummaries?.length && !data.topSequences?.length)) return <p className="text-slate-500 text-sm">No sequence data available.</p>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.teamSummaries.map((s: any) => (
          <div key={s.teamId} className="bg-slate-700 rounded-lg p-4">
            <h4 className="font-semibold text-sm text-slate-200 mb-3">{s.teamName || `Team ${s.teamId}`}</h4>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              {[
                { label: 'Sequences', value: s.totalSequences },
                { label: 'Box entries', value: s.boxEntries },
                { label: 'Shots', value: s.shotEndings },
                { label: 'Goals', value: s.goals },
                { label: 'Direct attacks', value: s.directAttacks },
                { label: 'Rapid regains', value: s.rapidRegains },
              ].map(({ label, value }) => (
                <div key={label} className="bg-slate-600 rounded p-2">
                  <p className="text-white font-bold">{value ?? 0}</p>
                  <p className="text-slate-400 text-xs">{label}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {data.topSequences?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-300 mb-2">Top Sequences</h4>
          <div className="space-y-2">
            {data.topSequences.slice(0, 4).map((seq: any, i: number) => (
              <div key={i} className="bg-slate-700 rounded-lg p-3 flex items-center gap-4 text-sm">
                <span className="text-slate-400 text-xs w-16">{seq.startMinute}'–{seq.endMinute}'</span>
                <span className="font-medium text-slate-200 flex-1">{seq.teamName}</span>
                <div className="flex gap-2 text-xs">
                  {seq.endedWithGoal && <span className="bg-green-700 text-white px-2 py-0.5 rounded">GOAL</span>}
                  {seq.endedWithShot && !seq.endedWithGoal && <span className="bg-blue-700 text-white px-2 py-0.5 rounded">Shot</span>}
                  {seq.boxEntry && <span className="bg-purple-700 text-white px-2 py-0.5 rounded">Box</span>}
                  {seq.directAttack && <span className="bg-yellow-700 text-white px-2 py-0.5 rounded">Direct</span>}
                </div>
                <span className="text-slate-400 text-xs">{seq.actions} actions</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export const MatchDetailWithVisualizations: React.FC<MatchDetailWithVisualizationsProps> = ({
  matchId,
  homeTeam = 'Home Team',
  awayTeam = 'Away Team',
  homeTeamId,
  awayTeamId,
  homeScore = 0,
  awayScore = 0,
  onBack,
}) => {
  const [expandedSections, setExpandedSections] = useState({
    shotMap: true,
    heatMap: true,
    passNetwork: false,
    tactical: true,
    sequences: true,
  });

  // Consolidated visualization data fetched in one request
  const [vizData, setVizData] = useState<any>(null);
  const [vizLoading, setVizLoading] = useState(true);

  useEffect(() => {
    setVizLoading(true);
    apiService.getMatchViz(matchId, homeTeamId, awayTeamId)
      .then(r => setVizData(r.success ? r.data : null))
      .catch(() => setVizData(null))
      .finally(() => setVizLoading(false));
  }, [matchId, homeTeamId, awayTeamId]);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const SectionHeader = ({ id, title, icon }: { id: keyof typeof expandedSections; title: string; icon?: React.ReactNode }) => (
    <button
      onClick={() => toggleSection(id)}
      className="w-full px-4 py-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors"
    >
      <div className="flex items-center gap-2">
        {icon}
        <h2 className="text-xl font-semibold">{title}</h2>
      </div>
      {expandedSections[id]
        ? <ChevronUp className="w-5 h-5 text-slate-400" />
        : <ChevronDown className="w-5 h-5 text-slate-400" />}
    </button>
  );

  return (
    <div className="bg-slate-900 min-h-screen text-white">
      <div className="bg-slate-800 border-b border-slate-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 mb-4">
            {onBack && (
              <button onClick={onBack} className="p-2 hover:bg-slate-700 rounded-lg transition-colors" title="Go back">
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
            <div className="flex-1">
              <h1 className="text-2xl font-bold mb-2">Match Analysis</h1>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="font-semibold">{homeTeam}</p>
                  <p className="text-lg font-bold text-green-400">{homeScore}</p>
                </div>
                <div className="text-2xl font-bold text-slate-500">-</div>
                <div className="text-left">
                  <p className="font-semibold">{awayTeam}</p>
                  <p className="text-lg font-bold text-green-400">{awayScore}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Tactical Metrics — fetched independently (analytics service, cached) */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <SectionHeader id="tactical" title="Tactical Metrics" icon={<Activity className="w-5 h-5 text-blue-400" />} />
          {expandedSections.tactical && (
            <div className="border-t border-slate-700 p-4">
              <ErrorBoundary>
                <TacticalMetricsPanel matchId={matchId} />
              </ErrorBoundary>
            </div>
          )}
        </section>

        {/* Sequence Insights — fetched independently (analytics service, cached) */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <SectionHeader id="sequences" title="Possession Sequences" icon={<TrendingUp className="w-5 h-5 text-purple-400" />} />
          {expandedSections.sequences && (
            <div className="border-t border-slate-700 p-4">
              <ErrorBoundary>
                <SequenceInsightsPanel matchId={matchId} />
              </ErrorBoundary>
            </div>
          )}
        </section>

        {/* Shot Map — data from consolidated /viz call */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <SectionHeader id="shotMap" title="Shot Map" icon={<Target className="w-5 h-5 text-red-400" />} />
          {expandedSections.shotMap && (
            <div className="border-t border-slate-700 p-4">
              <ErrorBoundary>
                <ShotMap
                  matchId={matchId}
                  width={900}
                  height={700}
                  precomputedShots={vizLoading ? undefined : (vizData?.shots ?? null)}
                />
              </ErrorBoundary>
            </div>
          )}
        </section>

        {/* Heat Maps — pre-computed grids from consolidated /viz call */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <SectionHeader id="heatMap" title="Player Activity" />
          {expandedSections.heatMap && (
            <div className="border-t border-slate-700 p-4 space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{homeTeam} - Player Activity</h3>
                <ErrorBoundary>
                  <HeatMap
                    matchId={matchId}
                    teamId={homeTeamId}
                    title={`${homeTeam} Activity`}
                    width={900}
                    height={700}
                    precomputedData={vizLoading ? undefined : (vizData?.heatmap_home ?? null)}
                  />
                </ErrorBoundary>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{awayTeam} - Player Activity</h3>
                <ErrorBoundary>
                  <HeatMap
                    matchId={matchId}
                    teamId={awayTeamId}
                    title={`${awayTeam} Activity`}
                    width={900}
                    height={700}
                    precomputedData={vizLoading ? undefined : (vizData?.heatmap_away ?? null)}
                  />
                </ErrorBoundary>
              </div>
            </div>
          )}
        </section>

        {/* Pass Networks — pre-computed from consolidated /viz call */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <SectionHeader id="passNetwork" title="Pass Networks" />
          {expandedSections.passNetwork && (
            <div className="border-t border-slate-700 p-4 space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{homeTeam} - Pass Network</h3>
                <ErrorBoundary>
                  <PassNetwork
                    matchId={matchId}
                    teamId={homeTeamId}
                    width={900}
                    height={700}
                    precomputedData={vizLoading ? undefined : (vizData?.pass_network_home ?? null)}
                  />
                </ErrorBoundary>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{awayTeam} - Pass Network</h3>
                <ErrorBoundary>
                  <PassNetwork
                    matchId={matchId}
                    teamId={awayTeamId}
                    width={900}
                    height={700}
                    precomputedData={vizLoading ? undefined : (vizData?.pass_network_away ?? null)}
                  />
                </ErrorBoundary>
              </div>
            </div>
          )}
        </section>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-sm text-slate-400">
            Hover over elements in the visualizations for more details. Click section headers to expand or collapse.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MatchDetailWithVisualizations;
