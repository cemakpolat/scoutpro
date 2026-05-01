import React, { useState } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Calendar, Filter, Download } from 'lucide-react';
import { useData } from '../context/DataContext';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import { exportService } from '../services/exportService';

const MarketAnalysis: React.FC = () => {
  const [timeframe, setTimeframe] = useState('1M');
  const [sortBy, setSortBy] = useState('value');

  const { players } = useData();
  const { data: marketTrends } = useApi(() => apiService.getMarketTrends(), []);

  const marketData = players.map((player, i) => {
    // Use a deterministic seed from the player id to avoid re-renders changing values
    const seed = player.id ? player.id.split('').reduce((acc: number, c: string) => acc + c.charCodeAt(0), 0) : i;
    const changePercent = ((seed % 41) - 20);           // -20 to +20, deterministic
    const transferProbability = (seed * 7 + i * 13) % 101; // 0-100, deterministic
    return {
      ...player,
      previousValue: parseFloat(String(player.marketValue || '0').replace(/[€M]/g, '')) * 0.9,
      changePercent,
      transferProbability,
    };
  });

  const topGainers = marketData
    .filter(player => player.changePercent > 0)
    .sort((a, b) => b.changePercent - a.changePercent)
    .slice(0, 5);

  const topLosers = marketData
    .filter(player => player.changePercent < 0)
    .sort((a, b) => a.changePercent - b.changePercent)
    .slice(0, 5);

  const handleExport = async () => {
    if (!marketData || marketData.length === 0) {
      alert('No market data to export');
      return;
    }

    const exportData = marketData.slice(0, 20).map(player => ({
      Player: player.name,
      Club: player.club,
      Position: player.position,
      'Market Value': player.marketValue,
      'Change %': `${player.changePercent > 0 ? '+' : ''}${player.changePercent.toFixed(1)}%`,
      'Transfer Probability': `${player.transferProbability}%`,
    }));

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `market_analysis_${timeframe}_${Date.now()}.pdf`,
        data: exportData,
        header: `Market Analysis - ${timeframe}`,
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('Market analysis exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Market Analysis</h1>
        <div className="flex items-center space-x-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="1W">Last Week</option>
            <option value="1M">Last Month</option>
            <option value="3M">Last 3 Months</option>
            <option value="1Y">Last Year</option>
          </select>
          <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Market Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">€2.4B</div>
              <div className="text-slate-400 text-sm">Total Market Value</div>
            </div>
            <TrendingUp className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            +12.5% this month
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">47</div>
              <div className="text-slate-400 text-sm">Active Transfers</div>
            </div>
            <DollarSign className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <Calendar className="h-4 w-4 mr-1" />
            23 this week
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">€89.2M</div>
              <div className="text-slate-400 text-sm">Avg Transfer Value</div>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            +8.2% vs last month
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">156</div>
              <div className="text-slate-400 text-sm">Hot Prospects</div>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-400" />
          </div>
          <div className="flex items-center mt-2 text-purple-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            12 new this week
          </div>
        </div>
      </div>

      {/* Market Movers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Gainers */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <TrendingUp className="h-6 w-6 mr-2 text-green-400" />
            Top Gainers
          </h3>
          <div className="space-y-4">
            {topGainers.map((player) => (
              <div key={player.id} className="flex items-center space-x-4 p-4 bg-slate-700 rounded-lg">
                <img
                  src={player.photo}
                  alt={player.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div className="flex-1">
                  <div className="font-semibold">{player.name}</div>
                  <div className="text-slate-400 text-sm">{player.club}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold">{player.marketValue}</div>
                  <div className="flex items-center text-green-400 text-sm">
                    <TrendingUp className="h-4 w-4 mr-1" />
                    +{player.changePercent.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Losers */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <TrendingDown className="h-6 w-6 mr-2 text-red-400" />
            Top Losers
          </h3>
          <div className="space-y-4">
            {topLosers.map((player) => (
              <div key={player.id} className="flex items-center space-x-4 p-4 bg-slate-700 rounded-lg">
                <img
                  src={player.photo}
                  alt={player.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div className="flex-1">
                  <div className="font-semibold">{player.name}</div>
                  <div className="text-slate-400 text-sm">{player.club}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold">{player.marketValue}</div>
                  <div className="flex items-center text-red-400 text-sm">
                    <TrendingDown className="h-4 w-4 mr-1" />
                    {player.changePercent.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Transfer Probability */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Transfer Probability Index</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-2">Player</th>
                <th className="text-left py-3 px-2">Current Club</th>
                <th className="text-left py-3 px-2">Market Value</th>
                <th className="text-left py-3 px-2">Change</th>
                <th className="text-left py-3 px-2">Transfer Probability</th>
                <th className="text-left py-3 px-2">Linked Clubs</th>
              </tr>
            </thead>
            <tbody>
              {marketData.slice(0, 10).map((player) => (
                <tr key={player.id} className="border-b border-slate-700 hover:bg-slate-700">
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-3">
                      <img
                        src={player.photo}
                        alt={player.name}
                        className="w-8 h-8 rounded-full object-cover"
                      />
                      <span className="font-semibold">{player.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-slate-300">{player.club}</td>
                  <td className="py-3 px-2 font-semibold">{player.marketValue}</td>
                  <td className="py-3 px-2">
                    <span className={`flex items-center ${
                      player.changePercent > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {player.changePercent > 0 ? (
                        <TrendingUp className="h-4 w-4 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 mr-1" />
                      )}
                      {Math.abs(player.changePercent).toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-slate-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            player.transferProbability > 70 ? 'bg-red-400' :
                            player.transferProbability > 40 ? 'bg-yellow-400' : 'bg-green-400'
                          }`}
                          style={{ width: `${player.transferProbability}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-semibold">{player.transferProbability}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-slate-400 text-sm">
                    Real Madrid, PSG, Bayern
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MarketAnalysis;