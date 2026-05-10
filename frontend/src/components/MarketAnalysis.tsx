import React, { useEffect, useMemo, useState } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Download } from 'lucide-react';
import { useData } from '../context/DataContext';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import { exportService } from '../services/exportService';
import {
  formatMarketValueCompact,
  normalizePhaseLabel,
  parseMarketValueToNumber,
  resolveClubName,
  resolvePlayerId,
  resolvePositionLabel,
  resolveScoutingValuation,
  type MarketValueEstimate,
  type PlayerScoutingPayload,
} from '../utils/scoutingData';

interface HydratedMarketPlayer {
  id: string;
  player: Record<string, any>;
  profile: PlayerScoutingPayload | null;
  valuation: MarketValueEstimate | null;
  currentValueNumeric: number;
  currentValueLabel: string;
  projectedValueNumeric: number;
  projectedValueLabel: string;
  phaseLabel: string | null;
  club: string;
  position: string;
}

const buildHydratedMarketPlayer = (
  player: Record<string, any>,
  profile: PlayerScoutingPayload | null,
): HydratedMarketPlayer | null => {
  const id = resolvePlayerId(player);
  if (!id) {
    return null;
  }

  const valuation = resolveScoutingValuation(profile);
  const currentValueNumeric = parseMarketValueToNumber(player.marketValue ?? player.currentValue ?? player.value);
  const projectedValueNumeric = valuation?.estimateMillionEUR
    ? valuation.estimateMillionEUR * 1_000_000
    : parseMarketValueToNumber(valuation?.displayValue);

  return {
    id,
    player,
    profile,
    valuation,
    currentValueNumeric,
    currentValueLabel: formatMarketValueCompact(player.marketValue ?? player.currentValue ?? player.value),
    projectedValueNumeric: projectedValueNumeric || currentValueNumeric,
    projectedValueLabel: valuation?.displayValue || formatMarketValueCompact(projectedValueNumeric || currentValueNumeric),
    phaseLabel: normalizePhaseLabel(profile?.scoutingProfile?.developmentCurve?.phase),
    club: resolveClubName(player),
    position: resolvePositionLabel(player),
  };
};

const MarketAnalysis: React.FC = () => {
  const [timeframe, setTimeframe] = useState('1M');
  const [hydratedMarketPlayers, setHydratedMarketPlayers] = useState<HydratedMarketPlayer[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(false);

  const { players } = useData();
  const { data: marketTrends } = useApi(() => apiService.getMarketTrends(), []);
  const { data: marketValuations, loading: valuationsLoading } = useApi(() => apiService.getMarketValuations(), []);

  useEffect(() => {
    if (!Array.isArray(marketValuations) || marketValuations.length === 0) {
      setHydratedMarketPlayers([]);
      return;
    }

    let cancelled = false;
    setProfilesLoading(true);

    Promise.allSettled(
      marketValuations.slice(0, 20).map(async (player) => {
        const playerId = resolvePlayerId(player);
        if (!playerId) {
          return buildHydratedMarketPlayer(player, null);
        }

        const scoutingRes = await apiService.getPlayerScoutingProfile(playerId);
        const profile = scoutingRes.success && scoutingRes.data
          ? scoutingRes.data as PlayerScoutingPayload
          : null;

        return buildHydratedMarketPlayer(player, profile);
      })
    ).then((results) => {
      if (cancelled) {
        return;
      }

      setHydratedMarketPlayers(
        results.flatMap((result) => (
          result.status === 'fulfilled' && result.value ? [result.value] : []
        ))
      );
    }).finally(() => {
      if (!cancelled) {
        setProfilesLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [marketValuations]);

  const marketData = useMemo(() => {
    if (hydratedMarketPlayers.length > 0) {
      return hydratedMarketPlayers.map((player) => {
        const currentValue = player.currentValueNumeric;
        const projectedValue = player.projectedValueNumeric;
        const changePercent = currentValue > 0
          ? ((projectedValue - currentValue) / currentValue) * 100
          : 0;
        const transferProbability = Math.min(
          99,
          Math.max(
            15,
            Math.round((player.valuation?.confidence || 50) + (player.phaseLabel === 'Pre Prime' ? 10 : 0) + (changePercent > 0 ? Math.min(changePercent, 12) : 0))
          )
        );

        return {
          ...player,
          name: String(player.player.name || player.profile?.player?.name || 'Unknown Player'),
          photo: String(player.player.photo || player.player.imageUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(String(player.player.name || 'Player'))}&size=96&background=334155&color=fff`),
          marketValue: player.projectedValueLabel,
          currentValueLabel: player.currentValueLabel,
          projectedValueLabel: player.projectedValueLabel,
          changePercent,
          transferProbability,
          scoutingSignal: player.phaseLabel || player.valuation?.band || 'Model pending',
          confidence: player.valuation?.confidence || 0,
        };
      });
    }

    return players.map((player, index) => {
      const numericValue = parseMarketValueToNumber(player.marketValue);
      const seed = player.id ? player.id.split('').reduce((acc: number, c: string) => acc + c.charCodeAt(0), 0) : index;
      const changePercent = ((seed % 41) - 20);
      const transferProbability = (seed * 7 + index * 13) % 101;
      return {
        ...player,
        currentValueLabel: formatMarketValueCompact(numericValue),
        projectedValueLabel: formatMarketValueCompact(numericValue),
        previousValue: numericValue * 0.9,
        changePercent,
        transferProbability,
        scoutingSignal: 'Profile only',
        confidence: 0,
      };
    });
  }, [hydratedMarketPlayers, players]);

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
      'Current Value': player.currentValueLabel,
      'Projected Value': player.projectedValueLabel,
      'Change %': `${player.changePercent > 0 ? '+' : ''}${player.changePercent.toFixed(1)}%`,
      'Transfer Probability': `${player.transferProbability}%`,
      'Scouting Signal': player.scoutingSignal,
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

  const totalProjectedValue = marketData.reduce((sum, player) => sum + parseMarketValueToNumber(player.projectedValueLabel || player.marketValue), 0);
  const averageProjectedValue = marketData.length > 0 ? totalProjectedValue / marketData.length : 0;
  const modelledAssets = marketData.length;
  const prePrimeAssets = marketData.filter((player) => player.scoutingSignal === 'Pre Prime').length;
  const isLoadingMarketData = valuationsLoading || profilesLoading;

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
              <div className="text-2xl font-bold text-white">{formatMarketValueCompact(totalProjectedValue)}</div>
              <div className="text-slate-400 text-sm">Projected Market Value</div>
            </div>
            <TrendingUp className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            {isLoadingMarketData ? 'Loading model signals' : `${topGainers.length} positive movers`}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{modelledAssets}</div>
              <div className="text-slate-400 text-sm">Modelled Assets</div>
            </div>
            <DollarSign className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            {marketData.filter((player) => player.transferProbability >= 70).length} high-interest profiles
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{formatMarketValueCompact(averageProjectedValue)}</div>
              <div className="text-slate-400 text-sm">Avg Projected Value</div>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            {marketTrends && Array.isArray(marketTrends) && marketTrends[0] ? `${String((marketTrends[0] as any).change || '+0.0%')} lead trend` : 'Awaiting market trend feed'}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{prePrimeAssets}</div>
              <div className="text-slate-400 text-sm">Pre-Prime Assets</div>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-400" />
          </div>
          <div className="flex items-center mt-2 text-purple-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            {marketData.filter((player) => player.changePercent > 10).length} rising valuations
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
                  <div className="font-semibold">{player.projectedValueLabel || player.marketValue}</div>
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
                  <div className="font-semibold">{player.projectedValueLabel || player.marketValue}</div>
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
                  <th className="text-left py-3 px-2">Projected Value</th>
                <th className="text-left py-3 px-2">Change</th>
                <th className="text-left py-3 px-2">Transfer Probability</th>
                  <th className="text-left py-3 px-2">Scouting Signal</th>
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
                  <td className="py-3 px-2 font-semibold">{player.projectedValueLabel || player.marketValue}</td>
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
                  <td className="py-3 px-2 text-slate-400 text-sm">{player.scoutingSignal}</td>
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