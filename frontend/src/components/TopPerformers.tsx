import React, { useMemo } from 'react';
import { useData } from '../context/DataContext';
import { usePlayerSequenceCoverage } from '../hooks/usePlayerSequenceCoverage';
import { Award, Target } from 'lucide-react';
import SequenceCoverageBadge from './SequenceCoverageBadge';

const TopPerformers: React.FC = () => {
  const { players, loading: loadingState } = useData();

  const topPerformers = players
    .filter(player => player.rating != null)
    .sort((a, b) => (b.rating || 0) - (a.rating || 0))
    .slice(0, 6);
  const topPerformerIds = useMemo(
    () => topPerformers.map((player) => String(player.id)).filter(Boolean),
    [topPerformers],
  );
  const { coverageByPlayerId } = usePlayerSequenceCoverage(topPerformerIds);

  if (loadingState.players) {
    return (
      <div className="bg-slate-800 rounded-xl p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-slate-700 rounded w-1/3 mb-6"></div>
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-20 bg-slate-700 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold flex items-center">
          <Award className="h-6 w-6 mr-2 text-yellow-400" />
          Elite Performance Index
        </h3>
        <div className="text-xs text-slate-400">Updated real-time</div>
      </div>
      
      <div className="space-y-4">
        {topPerformers.map((player, index) => (
          <div key={player.id} className="flex items-center space-x-4 p-4 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors">
            <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
              index === 0 ? 'bg-yellow-500 text-yellow-900' :
              index === 1 ? 'bg-gray-400 text-gray-900' :
              index === 2 ? 'bg-amber-600 text-amber-900' :
              'bg-green-600 text-white'
            }`}>
              {index + 1}
            </div>
            <img
              src={player.photo}
              alt={player.name}
              className="w-12 h-12 rounded-full object-cover"
            />
            <div className="flex-1">
              <div className="font-semibold text-lg">{player.name}</div>
              <div className="text-slate-400 text-sm">{player.position} • {player.club} • {player.nationality}</div>
              <div className="flex items-center space-x-3 mt-1">
                <span className="text-xs bg-blue-600/20 text-blue-300 px-2 py-1 rounded">
                  {player.goals}G {player.assists}A
                </span>
                <span className="text-xs bg-purple-600/20 text-purple-300 px-2 py-1 rounded">
                  xG: {player.xG}
                </span>
                <span className="text-xs bg-green-600/20 text-green-300 px-2 py-1 rounded">
                  {player.consistency != null ? `${player.consistency}% consistency` : `${(player.passAccuracy || 0).toFixed(0)}% pass acc`}
                </span>
              </div>
              <div className="mt-2 inline-block">
                <SequenceCoverageBadge coverage={coverageByPlayerId[String(player.id)]} compact />
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-yellow-400">{(player.rating || 0).toFixed(2)}</div>
              <div className="text-xs text-slate-400 mb-1">Performance Index</div>
              <div className="flex items-center text-sm text-slate-400">
                <Target className="h-4 w-4 mr-1 text-green-400" />
                <span className="text-green-400">{player.marketValue || '—'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 p-4 bg-slate-700 rounded-lg">
        <h4 className="font-semibold mb-2 text-yellow-400">Performance Insights</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-slate-400">Average Rating</div>
            <div className="font-bold text-white">
              {topPerformers.length > 0 ? 
                (topPerformers.reduce((sum, p) => sum + (p.rating || 0), 0) / topPerformers.length).toFixed(1) : 
                '0.0'
              }
            </div>
          </div>
          <div>
            <div className="text-slate-400">Total Market Value</div>
            <div className="font-bold text-green-400">
              €{topPerformers.reduce((sum, p) => {
                const raw = String(p.marketValue || '0').replace(/[€M,\s]/g, '');
                const value = parseFloat(raw) || 0;
                return sum + value;
              }, 0).toFixed(0)}M
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TopPerformers;