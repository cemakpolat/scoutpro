import React, { useState } from 'react';
import { ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';
import { ShotMap, HeatMap, PassNetwork } from './visualizations';
import ErrorBoundary from './ErrorBoundary';

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

/**
 * MatchDetailWithVisualizations - Complete match analysis view
 * Integrates Shot Map, Heat Maps, Pass Networks into one dashboard
 */
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
    passNetwork: true,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  return (
    <div className="bg-slate-900 min-h-screen text-white">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 mb-4">
            {onBack && (
              <button
                onClick={onBack}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                title="Go back"
              >
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

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Shot Map Section */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('shotMap')}
            className="w-full px-4 py-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors"
          >
            <h2 className="text-xl font-semibold">Shot Map</h2>
            {expandedSections.shotMap ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </button>

          {expandedSections.shotMap && (
            <div className="border-t border-slate-700 p-4">
              <ErrorBoundary>
                <ShotMap matchId={matchId} width={900} height={700} />
              </ErrorBoundary>
            </div>
          )}
        </section>

        {/* Heat Maps Section */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('heatMap')}
            className="w-full px-4 py-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors"
          >
            <h2 className="text-xl font-semibold">Player Activity</h2>
            {expandedSections.heatMap ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </button>

          {expandedSections.heatMap && (
            <div className="border-t border-slate-700 p-4 space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{homeTeam} - Player Activity</h3>
                <ErrorBoundary>
                  <HeatMap matchId={matchId} teamId={homeTeamId} title={`${homeTeam} Activity`} width={900} height={700} />
                </ErrorBoundary>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{awayTeam} - Player Activity</h3>
                <ErrorBoundary>
                  <HeatMap matchId={matchId} teamId={awayTeamId} title={`${awayTeam} Activity`} width={900} height={700} />
                </ErrorBoundary>
              </div>
            </div>
          )}
        </section>

        {/* Pass Networks Section */}
        <section className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('passNetwork')}
            className="w-full px-4 py-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors"
          >
            <h2 className="text-xl font-semibold">Pass Networks</h2>
            {expandedSections.passNetwork ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </button>

          {expandedSections.passNetwork && (
            <div className="border-t border-slate-700 p-4 space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{homeTeam} - Pass Network</h3>
                <ErrorBoundary>
                  <PassNetwork matchId={matchId} teamId={homeTeamId} width={900} height={700} />
                </ErrorBoundary>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">{awayTeam} - Pass Network</h3>
                <ErrorBoundary>
                  <PassNetwork matchId={matchId} teamId={awayTeamId} width={900} height={700} />
                </ErrorBoundary>
              </div>
            </div>
          )}
        </section>

        {/* Info Footer */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-sm text-slate-400">
            💡 <strong>Tip:</strong> Hover over elements in the visualizations for more details. 
            Click to expand or collapse sections to focus on specific analysis.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MatchDetailWithVisualizations;
