import React, { useState, useEffect } from 'react';
import { TrendingUp, Target, Activity, Loader2 } from 'lucide-react';
import { useData } from '../context/DataContext';
import apiService from '../services/api';

const PerformancePrediction: React.FC = () => {
  const { players: contextPlayers } = useData();
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiService.getPlayerRankings('rating', 5).then((res: any) => {
      const ranked = res?.data || res?.players || [];
      if (Array.isArray(ranked) && ranked.length > 0) {
        setPredictions(ranked.map((p: any) => ({
          name: p.name,
          rating: p.rating || 7.5,
          goals: p.goals ? (p.goals / Math.max(p.appearances || 1, 1)).toFixed(1) : '0.5',
          assists: p.assists ? (p.assists / Math.max(p.appearances || 1, 1)).toFixed(1) : '0.3',
          motm: Math.round((p.rating || 7.5) * 9),
        })));
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  // Fallback to context players if API predictions empty
  const playerPredictions = predictions.length > 0 ? predictions :
    contextPlayers.slice(0, 5).map((p: any) => ({
      name: p.name,
      rating: p.rating || 7.5,
      goals: (p.goals ? p.goals / Math.max(p.appearances || 1, 1) : 0.5).toFixed(1),
      assists: (p.assists ? p.assists / Math.max(p.appearances || 1, 1) : 0.3).toFixed(1),
      motm: Math.round((p.rating || 7.5) * 9),
    }));

  // Final fallback for empty state
  const displayPredictions = playerPredictions.length > 0 ? playerPredictions : [
    { name: 'Player 1', rating: 8.0, goals: '0.8', assists: '0.4', motm: 72 },
    { name: 'Player 2', rating: 7.8, goals: '0.6', assists: '0.5', motm: 70 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Next Match Predictions</h3>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
          </div>
        ) : (
        <div className="space-y-4">
          {displayPredictions.map((player: any, index: number) => (
            <div key={index} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <div className="font-semibold">{player.name}</div>
                <div className="text-green-400 font-bold">{player.rating}</div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-slate-400">Goals</div>
                  <div className="font-semibold">{player.goals}</div>
                </div>
                <div className="text-center">
                  <div className="text-slate-400">Assists</div>
                  <div className="font-semibold">{player.assists}</div>
                </div>
                <div className="text-center">
                  <div className="text-slate-400">MOTM %</div>
                  <div className="font-semibold">{player.motm}%</div>
                </div>
              </div>
            </div>
          ))}
        </div>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Performance Factors</h3>
        <div className="space-y-4">
          <div className="p-4 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span>Form & Fitness</span>
              <TrendingUp className="h-5 w-5 text-green-400" />
            </div>
            <div className="text-sm text-slate-300 mb-2">
              Recent performance trends and physical condition analysis
            </div>
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div className="bg-green-400 h-2 rounded-full" style={{ width: '87%' }}></div>
            </div>
          </div>

          <div className="p-4 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span>Opponent Analysis</span>
              <Target className="h-5 w-5 text-blue-400" />
            </div>
            <div className="text-sm text-slate-300 mb-2">
              Historical performance against specific teams and playstyles
            </div>
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div className="bg-blue-400 h-2 rounded-full" style={{ width: '73%' }}></div>
            </div>
          </div>

          <div className="p-4 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span>Environmental Factors</span>
              <Activity className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="text-sm text-slate-300 mb-2">
              Weather, venue, time of day, and crowd impact analysis
            </div>
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div className="bg-yellow-400 h-2 rounded-full" style={{ width: '64%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformancePrediction;