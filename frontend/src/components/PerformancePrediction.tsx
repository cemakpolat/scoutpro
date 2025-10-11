import React from 'react';
import { TrendingUp, Target, Activity } from 'lucide-react';

const PerformancePrediction: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Next Match Predictions</h3>
        <div className="space-y-4">
          {[
            { name: 'Lionel Messi', rating: 8.9, goals: 1.2, assists: 0.8, motm: 85 },
            { name: 'Kylian Mbappé', rating: 8.7, goals: 1.5, assists: 0.4, motm: 78 },
            { name: 'Erling Haaland', rating: 8.5, goals: 1.8, assists: 0.2, motm: 72 },
            { name: 'Kevin De Bruyne', rating: 8.4, goals: 0.3, assists: 1.4, motm: 68 },
            { name: 'Pedri', rating: 8.2, goals: 0.2, assists: 0.9, motm: 65 },
          ].map((player, index) => (
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