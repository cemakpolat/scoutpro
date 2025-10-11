import React from 'react';

interface PotentialChartProps {
  data: Array<{ name: string; current: number; potential: number }>;
}

const PotentialChart: React.FC<PotentialChartProps> = ({ data }) => {
  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <h3 className="text-xl font-semibold mb-6">Potential vs Current Rating</h3>
      <div className="space-y-4">
        {data.map((player, index) => (
          <div key={index} className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">{player.name}</span>
              <span className="text-slate-400">{player.current} → {player.potential}</span>
            </div>
            <div className="relative">
              <div className="w-full bg-slate-700 rounded-full h-3">
                <div
                  className="bg-blue-400 h-3 rounded-full"
                  style={{ width: `${(player.current / 100) * 100}%` }}
                ></div>
              </div>
              <div className="absolute top-0 left-0 w-full h-3">
                <div
                  className="bg-green-400 h-3 rounded-full opacity-50"
                  style={{ width: `${(player.potential / 100) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PotentialChart;