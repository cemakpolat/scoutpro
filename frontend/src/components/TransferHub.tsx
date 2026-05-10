import React, { useState, useEffect, useMemo } from 'react';
import {
  DollarSign, TrendingUp, TrendingDown, AlertTriangle, Clock,
  Calendar, Eye, Download, RefreshCw
} from 'lucide-react';
import { exportService } from '../services/exportService';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import {
  dedupeByPlayerId,
  formatMarketValueCompact,
  normalizePhaseLabel,
  parseMarketValueToNumber,
  resolveClubName,
  resolveContractExpiry,
  resolvePlayerId,
  resolvePositionLabel,
  resolveScoutingValuation,
  toFiniteNumber,
  type MarketValueEstimate,
  type PlayerScoutingPayload,
} from '../utils/scoutingData';

const formatCurrency = (value: unknown): string => {
  return formatMarketValueCompact(value);
};

const formatPercent = (value: unknown): number => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value > 1 ? value : Math.round(value * 100);
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? (parsed > 1 ? parsed : Math.round(parsed * 100)) : 0;
};

interface HydratedTransferPlayer {
  id: string;
  player: Record<string, any>;
  profile: PlayerScoutingPayload | null;
  valuation: MarketValueEstimate | null;
  currentValueNumeric: number;
  currentValueLabel: string;
  club: string;
  position: string;
  contractExpiry: string | null;
}

const getExpirySortValue = (value: string | null): number => {
  if (!value) {
    return Number.POSITIVE_INFINITY;
  }

  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : Number.POSITIVE_INFINITY;
};

const buildHydratedTransferPlayer = (
  player: Record<string, any>,
  profile: PlayerScoutingPayload | null,
): HydratedTransferPlayer | null => {
  const id = resolvePlayerId(player);
  if (!id) {
    return null;
  }

  const valuation = resolveScoutingValuation(profile);
  const currentValueRaw = player.marketValue ?? player.currentValue ?? player.value ?? player.estimatedFee;

  return {
    id,
    player,
    profile,
    valuation,
    currentValueNumeric: parseMarketValueToNumber(currentValueRaw),
    currentValueLabel: formatCurrency(currentValueRaw),
    club: resolveClubName(player),
    position: resolvePositionLabel(player),
    contractExpiry: resolveContractExpiry(player),
  };
};

const TransferHub: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('market-watch');
  const [loading, setLoading] = useState(true);
  const [apiMarketTrends, setApiMarketTrends] = useState<any[]>([]);
  const [apiPredictions, setApiPredictions] = useState<any[]>([]);
  const [marketError, setMarketError] = useState('');
  const [hydratedPlayers, setHydratedPlayers] = useState<HydratedTransferPlayer[]>([]);

  const { players: contextPlayers } = useData();

  const loadMarketData = React.useCallback(async () => {
    setLoading(true);
    setMarketError('');

    try {
      const [trends, predictions, valuations] = await Promise.all([
        apiService.getMarketTrends(),
        apiService.getTransferPredictions(),
        apiService.getMarketValuations(),
      ]);

      setApiMarketTrends(Array.isArray(trends.data) ? trends.data : []);
      setApiPredictions(Array.isArray(predictions.data) ? predictions.data : []);

      const expiringPlayers = [...contextPlayers]
        .filter((player: any) => Boolean(resolveContractExpiry(player)))
        .sort((left: any, right: any) => getExpirySortValue(resolveContractExpiry(left)) - getExpirySortValue(resolveContractExpiry(right)))
        .slice(0, 8);

      const valuationPlayers = Array.isArray(valuations.data) ? valuations.data : [];
      const seedPlayers = dedupeByPlayerId([
        ...valuationPlayers,
        ...(expiringPlayers as Array<Record<string, any>>),
      ]).slice(0, 18);

      const scoutingResults = await Promise.allSettled(
        seedPlayers.map(async (player) => {
          const playerId = resolvePlayerId(player);
          if (!playerId) {
            return buildHydratedTransferPlayer(player, null);
          }

          const scoutingRes = await apiService.getPlayerScoutingProfile(playerId);
          const profile = scoutingRes.success && scoutingRes.data
            ? scoutingRes.data as PlayerScoutingPayload
            : null;

          return buildHydratedTransferPlayer(player, profile);
        })
      );

      setHydratedPlayers(
        scoutingResults.flatMap((result) => (
          result.status === 'fulfilled' && result.value ? [result.value] : []
        ))
      );
    } catch (error) {
      console.error('Failed to load transfer hub data:', error);
      setApiMarketTrends([]);
      setApiPredictions([]);
      setHydratedPlayers([]);
      setMarketError('Transfer market data is unavailable right now.');
    } finally {
      setLoading(false);
    }
  }, [contextPlayers]);

  useEffect(() => {
    void loadMarketData();
  }, [loadMarketData]);

  const hydratedPlayersById = useMemo(
    () => new Map(hydratedPlayers.map((entry) => [entry.id, entry])),
    [hydratedPlayers]
  );

  const hydratedPlayersByName = useMemo(
    () => new Map(
      hydratedPlayers
        .map((entry) => [String(entry.player.name || entry.profile?.player?.name || '').trim().toLowerCase(), entry] as const)
        .filter(([name]) => Boolean(name))
    ),
    [hydratedPlayers]
  );

  const transferRumors = useMemo(() => apiPredictions.slice(0, 5).map((prediction: any) => {
    const playerName = String(prediction.playerName || prediction.name || 'Unknown Player');
    const matchedPlayer = hydratedPlayersByName.get(playerName.trim().toLowerCase());
    const matchedValuation = matchedPlayer?.valuation;
    const scoutingPhase = normalizePhaseLabel(matchedPlayer?.profile?.scoutingProfile?.developmentCurve?.phase);

    return {
      player: playerName,
      currentClub: prediction.currentClub || prediction.fromClub || matchedPlayer?.club || 'Unknown',
      targetClub: prediction.targetClub || prediction.toClub || 'TBD',
      probability: formatPercent(prediction.probability || prediction.confidence || matchedValuation?.confidence || 0),
      value: matchedValuation?.displayValue || formatCurrency(prediction.estimatedFee || prediction.value),
      status: formatPercent(prediction.probability || prediction.confidence || matchedValuation?.confidence || 0) > 70 ? 'hot' : formatPercent(prediction.probability || prediction.confidence || matchedValuation?.confidence || 0) > 40 ? 'warm' : 'cold',
      deadline: prediction.deadline || prediction.window || '2026-06-30',
      sources: prediction.sources || ['ScoutPro AI'],
      scoutingSignal: scoutingPhase || matchedValuation?.band || null,
      dataSource: matchedPlayer ? 'Scouting profile' : 'Backend prediction',
    };
  }), [apiPredictions, hydratedPlayersByName]);

  const valuationDrivenTrends = useMemo(() => {
    if (!hydratedPlayers.length) {
      return [];
    }

    const grouped = new Map<string, { currentTotal: number; projectedTotal: number; count: number }>();

    hydratedPlayers.forEach((entry) => {
      const key = entry.position || 'Unknown';
      const group = grouped.get(key) || { currentTotal: 0, projectedTotal: 0, count: 0 };
      const projectedValue = entry.valuation?.estimateMillionEUR
        ? entry.valuation.estimateMillionEUR * 1_000_000
        : parseMarketValueToNumber(entry.valuation?.displayValue);
      group.currentTotal += entry.currentValueNumeric;
      group.projectedTotal += projectedValue || entry.currentValueNumeric;
      group.count += 1;
      grouped.set(key, group);
    });

    return Array.from(grouped.entries())
      .map(([position, values]) => {
        const averageCurrent = values.count > 0 ? values.currentTotal / values.count : 0;
        const averageProjected = values.count > 0 ? values.projectedTotal / values.count : 0;
        const changePct = averageCurrent > 0
          ? ((averageProjected - averageCurrent) / averageCurrent) * 100
          : 0;

        return {
          position,
          avgValue: formatCurrency(averageProjected || averageCurrent),
          change: `${changePct >= 0 ? '+' : ''}${changePct.toFixed(1)}%`,
          trend: changePct > 0 ? 'up' : changePct < 0 ? 'down' : 'stable',
        };
      })
      .sort((left, right) => parseMarketValueToNumber(right.avgValue) - parseMarketValueToNumber(left.avgValue))
      .slice(0, 5);
  }, [hydratedPlayers]);

  const marketTrends = valuationDrivenTrends.length > 0
    ? valuationDrivenTrends
    : apiMarketTrends.slice(0, 5).map((trend: any) => ({
        position: trend.position || trend.name || 'Unknown',
        avgValue: formatCurrency(trend.currentValue || trend.avgValue || trend.averageValue),
        change: `${(trend.change || 0) > 0 ? '+' : ''}${Number(trend.change || 0).toFixed(1)}%`,
        trend: (trend.change || 0) > 0 ? 'up' : (trend.change || 0) < 0 ? 'down' : 'stable',
      }));

  const contractExpirations = useMemo(() => contextPlayers.length > 0
    ? [...contextPlayers]
        .filter((player: any) => Boolean(resolveContractExpiry(player)))
        .sort((left: any, right: any) => getExpirySortValue(resolveContractExpiry(left)) - getExpirySortValue(resolveContractExpiry(right)))
        .slice(0, 6)
        .map((player: any) => {
          const playerId = resolvePlayerId(player);
          const matchedPlayer = playerId ? hydratedPlayersById.get(playerId) : undefined;
          const valuation = matchedPlayer?.valuation;
          const expiry = resolveContractExpiry(player) || 'Unknown';
          const phase = normalizePhaseLabel(matchedPlayer?.profile?.scoutingProfile?.developmentCurve?.phase);

          return {
            player: player.name || 'Unknown Player',
            club: resolveClubName(player),
            expires: expiry,
            value: valuation?.displayValue || formatCurrency(player.marketValue || player.value),
            status: getExpirySortValue(expiry) < new Date('2026-06-30').getTime() ? 'critical' : 'expiring',
            phase: phase || matchedPlayer?.valuation?.band || 'Model pending',
          };
        })
    : [], [contextPlayers, hydratedPlayersById]);

  const valuationPredictions = useMemo(() => {
    if (hydratedPlayers.length > 0) {
      return [...hydratedPlayers]
        .filter((entry) => entry.valuation)
        .sort((left, right) => {
          const leftValue = left.valuation?.estimateMillionEUR ? left.valuation.estimateMillionEUR * 1_000_000 : parseMarketValueToNumber(left.valuation?.displayValue);
          const rightValue = right.valuation?.estimateMillionEUR ? right.valuation.estimateMillionEUR * 1_000_000 : parseMarketValueToNumber(right.valuation?.displayValue);
          return rightValue - leftValue;
        })
        .slice(0, 4)
        .map((entry) => {
          const phase = normalizePhaseLabel(entry.profile?.scoutingProfile?.developmentCurve?.phase);
          const nextCluster = typeof entry.profile?.scoutingProfile?.developmentCurve?.nextCluster === 'string'
            ? entry.profile.scoutingProfile.developmentCurve.nextCluster
            : null;
          const progressionValue = toFiniteNumber(entry.profile?.scoutingProfile?.ballProgression?.progressionValuePer90);

          return {
            player: String(entry.player.name || entry.profile?.player?.name || 'Player'),
            current: entry.currentValueLabel,
            predicted: entry.valuation?.displayValue || entry.currentValueLabel,
            confidence: formatPercent(entry.valuation?.confidence || 0),
            timeframe: phase === 'Pre Prime' ? 'Next 12 months' : nextCluster || 'Current window',
            factors: [
              phase,
              entry.valuation?.band ? String(entry.valuation.band).replace(/-/g, ' ') : null,
              progressionValue > 0 ? `${progressionValue.toFixed(2)} progression value/90` : null,
            ].filter((factor): factor is string => Boolean(factor)),
          };
        });
    }

    return apiPredictions.slice(0, 4).map((prediction: any) => ({
      player: prediction.playerName || prediction.name || 'Player',
      current: formatCurrency(prediction.currentValue || prediction.value),
      predicted: formatCurrency(prediction.predictedValue || prediction.estimatedFee),
      confidence: formatPercent(prediction.confidence || prediction.probability || 0),
      timeframe: prediction.timeframe || '12 months',
      factors: prediction.factors || ['Performance', 'Age', 'Market Demand'],
    }));
  }, [apiPredictions, hydratedPlayers]);

  const transferAlerts = [
    transferRumors[0]
      ? {
          type: 'rumor',
          message: `${transferRumors[0].player} linked with ${transferRumors[0].targetClub}`,
          time: 'Prediction feed',
        }
      : null,
    contractExpirations[0]
      ? {
          type: 'contract',
          message: `${contractExpirations[0].player} contract status: ${contractExpirations[0].expires}`,
          time: 'Player registry',
        }
      : null,
    marketTrends[0]
      ? {
          type: 'value',
          message: `${marketTrends[0].position} market at ${marketTrends[0].avgValue} (${marketTrends[0].change})`,
          time: 'Market trends',
        }
      : null,
    valuationPredictions[0]
      ? {
          type: 'deadline',
          message: `${valuationPredictions[0].player} projected at ${valuationPredictions[0].predicted}`,
          time: 'Prediction model',
        }
      : null,
  ].filter(Boolean) as Array<{ type: 'rumor' | 'contract' | 'value' | 'deadline'; message: string; time: string }>;

  const totalMarketActivity = hydratedPlayers.length > 0
    ? hydratedPlayers.reduce((sum, entry) => {
        const projectedValue = entry.valuation?.estimateMillionEUR
          ? entry.valuation.estimateMillionEUR * 1_000_000
          : parseMarketValueToNumber(entry.valuation?.displayValue);
        return sum + (projectedValue || entry.currentValueNumeric);
      }, 0)
    : apiMarketTrends.reduce((sum, trend) => sum + (Number(trend.currentValue) || 0), 0);
  const averageTransferFee = apiPredictions.length > 0
    ? transferRumors.reduce((sum, rumor) => sum + parseMarketValueToNumber(rumor.value), 0) / Math.max(transferRumors.length, 1)
    : 0;

  const handleExport = async () => {
    let exportData: any[] = [];

    if (selectedTab === 'rumors') {
      exportData = transferRumors.map(rumor => ({
        Player: rumor.player,
        'From': rumor.currentClub,
        'To': rumor.targetClub,
        'Probability': `${rumor.probability}%`,
        'Value': rumor.value,
        'Status': rumor.status,
        'Deadline': rumor.deadline,
      }));
    } else if (selectedTab === 'valuations') {
      exportData = valuationPredictions.map(pred => ({
        Player: pred.player,
        'Current Value': pred.current,
        'Predicted Value': pred.predicted,
        'Confidence': `${pred.confidence}%`,
        'Timeframe': pred.timeframe,
      }));
    } else if (selectedTab === 'contracts') {
      exportData = contractExpirations.map(contract => ({
        Player: contract.player,
        Club: contract.club,
        'Expires': contract.expires,
        'Market Value': contract.value,
        'Status': contract.status,
      }));
    } else {
      exportData = marketTrends.map(trend => ({
        Position: trend.position,
        'Avg Value': trend.avgValue,
        'Change': trend.change,
        'Trend': trend.trend,
      }));
    }

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `transfer_hub_${selectedTab}_${Date.now()}.pdf`,
        data: exportData,
        header: `Transfer Hub - ${selectedTab.replace('-', ' ').toUpperCase()}`,
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('Transfer report exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <DollarSign className="h-8 w-8 mr-3 text-green-500" />
          Transfer Hub
        </h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={loadMarketData}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh Market</span>
          </button>
          <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {marketError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {marketError}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex space-x-2 mb-6">
          {[
            { id: 'market-watch', label: 'Market Watch', icon: Eye },
            { id: 'rumors', label: 'Transfer Rumors', icon: AlertTriangle },
            { id: 'valuations', label: 'Valuations', icon: TrendingUp },
            { id: 'contracts', label: 'Contract Expiry', icon: Clock }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  selectedTab === tab.id
                    ? 'bg-green-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Market Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{formatCurrency(totalMarketActivity)}</div>
              <div className="text-slate-400 text-sm">Market Activity</div>
            </div>
            <DollarSign className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            {marketTrends[0]?.change || 'No live delta'}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{transferRumors.length}</div>
              <div className="text-slate-400 text-sm">Active Rumors</div>
            </div>
            <AlertTriangle className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <RefreshCw className="h-4 w-4 mr-1" />
            Backend feed
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{contractExpirations.length}</div>
              <div className="text-slate-400 text-sm">Contracts Expiring</div>
            </div>
            <Clock className="h-8 w-8 text-red-400" />
          </div>
          <div className="flex items-center mt-2 text-red-400 text-sm">
            <AlertTriangle className="h-4 w-4 mr-1" />
            Player registry scan
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{formatCurrency(averageTransferFee)}</div>
              <div className="text-slate-400 text-sm">Avg Transfer Fee</div>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-blue-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            Prediction average
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center rounded-xl bg-slate-800 px-6 py-20 text-slate-300">
          Loading transfer market data...
        </div>
      ) : (
        <>

      {/* Dynamic Content Based on Selected Tab */}
      {selectedTab === 'market-watch' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Market Trends by Position</h3>
            <div className="space-y-4">
              {marketTrends.length > 0 ? marketTrends.map((trend, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{trend.position}</span>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold">{trend.avgValue}</span>
                      <span className={`flex items-center text-sm ${
                        trend.trend === 'up' ? 'text-green-400' :
                        trend.trend === 'down' ? 'text-red-400' : 'text-slate-400'
                      }`}>
                        {trend.trend === 'up' ? <TrendingUp className="h-4 w-4 mr-1" /> :
                         trend.trend === 'down' ? <TrendingDown className="h-4 w-4 mr-1" /> : null}
                        {trend.change}
                      </span>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                  No live market trend data available.
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Recent Transfer Alerts</h3>
            <div className="space-y-4">
              {transferAlerts.length > 0 ? transferAlerts.map((alert, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-full ${
                      alert.type === 'rumor' ? 'bg-yellow-600' :
                      alert.type === 'contract' ? 'bg-red-600' :
                      alert.type === 'value' ? 'bg-green-600' : 'bg-blue-600'
                    }`}>
                      {alert.type === 'rumor' && <AlertTriangle className="h-4 w-4" />}
                      {alert.type === 'contract' && <Clock className="h-4 w-4" />}
                      {alert.type === 'value' && <TrendingUp className="h-4 w-4" />}
                      {alert.type === 'deadline' && <Calendar className="h-4 w-4" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm">{alert.message}</p>
                      <p className="text-xs text-slate-400 mt-1">{alert.time}</p>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                  No backend transfer alerts available.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'rumors' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Transfer Rumors</h3>
          <div className="space-y-4">
            {transferRumors.length > 0 ? transferRumors.map((rumor, index) => (
              <div key={index} className="p-6 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="font-bold text-lg">{rumor.player}</h4>
                    <p className="text-slate-400">{rumor.currentClub} → {rumor.targetClub}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-400">{rumor.probability}%</div>
                    <div className="text-sm text-slate-400">Probability</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-slate-400">Estimated Value</div>
                    <div className="font-semibold">{rumor.value}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">Contract Deadline</div>
                    <div className="font-semibold">{rumor.deadline}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">Status</div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      rumor.status === 'hot' ? 'bg-red-600 text-red-100' :
                      rumor.status === 'warm' ? 'bg-yellow-600 text-yellow-100' :
                      'bg-blue-600 text-blue-100'
                    }`}>
                      {rumor.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-sm text-slate-400">
                    Sources: {rumor.sources.join(', ')}
                  </div>
                    <div className="flex items-center gap-2">
                      {rumor.scoutingSignal ? (
                        <span className="rounded bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200">
                          {rumor.scoutingSignal}
                        </span>
                      ) : null}
                      <span className="rounded bg-slate-600 px-3 py-1 text-xs text-slate-200">
                        {rumor.dataSource}
                      </span>
                    </div>
                </div>
              </div>
            )) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No live transfer predictions available.
              </div>
            )}
          </div>
        </div>
      )}

      {selectedTab === 'valuations' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">AI Valuation Predictions</h3>
          <div className="space-y-6">
            {valuationPredictions.length > 0 ? valuationPredictions.map((prediction, index) => (
              <div key={index} className="p-6 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold text-lg">{prediction.player}</h4>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">Confidence</div>
                    <div className="font-bold text-purple-400">{prediction.confidence}%</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-slate-400">Current Value</div>
                    <div className="text-xl font-bold">{prediction.current}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">Predicted Value</div>
                    <div className="text-xl font-bold text-green-400">{prediction.predicted}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">Timeframe</div>
                    <div className="font-semibold">{prediction.timeframe}</div>
                  </div>
                </div>

                <div className="mb-4">
                  <div className="text-sm text-slate-400 mb-2">Key Factors</div>
                  <div className="flex flex-wrap gap-2">
                    {prediction.factors.map((factor, i) => (
                      <span key={i} className="px-2 py-1 bg-slate-600 text-slate-300 text-xs rounded">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full"
                    style={{ width: `${prediction.confidence}%` }}
                  ></div>
                </div>
              </div>
            )) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No valuation predictions available.
              </div>
            )}
          </div>
        </div>
      )}

      {selectedTab === 'contracts' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Contract Expirations</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">Player</th>
                  <th className="text-left py-3 px-2">Club</th>
                  <th className="text-left py-3 px-2">Expires</th>
                  <th className="text-left py-3 px-2">Market Value</th>
                  <th className="text-left py-3 px-2">Scouting Phase</th>
                  <th className="text-left py-3 px-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {contractExpirations.length > 0 ? contractExpirations.map((contract, index) => (
                  <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                    <td className="py-3 px-2 font-semibold">{contract.player}</td>
                    <td className="py-3 px-2">{contract.club}</td>
                    <td className="py-3 px-2">{contract.expires}</td>
                    <td className="py-3 px-2 font-semibold text-green-400">{contract.value}</td>
                    <td className="py-3 px-2 text-slate-300">{contract.phase}</td>
                    <td className="py-3 px-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        contract.status === 'critical' ? 'bg-red-600 text-red-100' :
                        'bg-yellow-600 text-yellow-100'
                      }`}>
                        {contract.status}
                      </span>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={6} className="py-10 text-center text-slate-400">
                      No contract expiry data available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
        </>
      )}
    </div>
  );
};

export default TransferHub;