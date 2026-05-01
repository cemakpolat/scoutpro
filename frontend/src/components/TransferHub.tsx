import React, { useState, useEffect } from 'react';
import {
  DollarSign, TrendingUp, TrendingDown, AlertTriangle, Clock,
  Calendar, Eye, Download, RefreshCw
} from 'lucide-react';
import { exportService } from '../services/exportService';
import { useData } from '../context/DataContext';
import apiService from '../services/api';

const formatCurrency = (value: unknown): string => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `€${Math.round(value / 1000000)}M`;
  }

  if (typeof value === 'string' && value.trim()) {
    return value;
  }

  return 'N/A';
};

const formatPercent = (value: unknown): number => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value > 1 ? value : Math.round(value * 100);
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? (parsed > 1 ? parsed : Math.round(parsed * 100)) : 0;
};

const TransferHub: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('market-watch');
  const [loading, setLoading] = useState(true);
  const [apiMarketTrends, setApiMarketTrends] = useState<any[]>([]);
  const [apiPredictions, setApiPredictions] = useState<any[]>([]);
  const [marketError, setMarketError] = useState('');

  const { players: contextPlayers } = useData();

  const loadMarketData = () => {
    setLoading(true);
    setMarketError('');

    Promise.all([
      apiService.getMarketTrends(),
      apiService.getTransferPredictions(),
    ]).then(([trends, predictions]) => {
      setApiMarketTrends(trends.data || []);
      setApiPredictions(predictions.data || []);
    }).catch((error) => {
      console.error('Failed to load transfer hub data:', error);
      setApiMarketTrends([]);
      setApiPredictions([]);
      setMarketError('Transfer market data is unavailable right now.');
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadMarketData();
  }, []);

  const transferRumors = apiPredictions.slice(0, 5).map((p: any) => ({
        player: p.playerName || p.name || 'Unknown Player',
        currentClub: p.currentClub || p.fromClub || 'Unknown',
        targetClub: p.targetClub || p.toClub || 'TBD',
        probability: formatPercent(p.probability || p.confidence || 0),
        value: formatCurrency(p.estimatedFee || p.value),
        status: formatPercent(p.probability || p.confidence || 0) > 70 ? 'hot' : formatPercent(p.probability || p.confidence || 0) > 40 ? 'warm' : 'cold',
        deadline: p.deadline || '2026-06-30',
        sources: p.sources || ['ScoutPro AI'],
      }));

  const marketTrends = apiMarketTrends.slice(0, 5).map((t: any) => ({
        position: t.position || t.name || 'Unknown',
        avgValue: formatCurrency(t.currentValue || t.avgValue || t.averageValue),
        change: `${(t.change || 0) > 0 ? '+' : ''}${Number(t.change || 0).toFixed(1)}%`,
        trend: (t.change || 0) > 0 ? 'up' : (t.change || 0) < 0 ? 'down' : 'stable',
      }));

  const contractExpirations = contextPlayers.length > 0
    ? contextPlayers
        .filter((p: any) => p.contractEnd || p.contractExpiry || p.contract)
        .slice(0, 6)
        .map((p: any) => ({
          player: p.name,
          club: p.club || p.team || 'Unknown',
          expires: p.contractEnd || p.contractExpiry || p.contract || 'Unknown',
          value: formatCurrency(p.marketValue || p.value),
          status: new Date(p.contractEnd || p.contractExpiry || '2026-12-31') < new Date('2026-06-30') ? 'critical' : 'expiring',
        }))
    : [];

  const valuationPredictions = apiPredictions.slice(0, 4).map((p: any) => ({
        player: p.playerName || p.name || 'Player',
        current: formatCurrency(p.currentValue || p.value),
        predicted: formatCurrency(p.predictedValue || p.estimatedFee),
        confidence: formatPercent(p.confidence || p.probability || 0),
        timeframe: p.timeframe || '12 months',
        factors: p.factors || ['Performance', 'Age', 'Market Demand'],
      }));

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

  const totalMarketActivity = apiMarketTrends.reduce((sum, trend) => sum + (Number(trend.currentValue) || 0), 0);
  const averageTransferFee = apiPredictions.length > 0
    ? apiPredictions.reduce((sum, prediction) => sum + (Number(prediction.estimatedFee) || 0), 0) / apiPredictions.length
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
                  <span className="rounded bg-slate-600 px-3 py-1 text-xs text-slate-200">
                    Backend prediction
                  </span>
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
                    <td colSpan={5} className="py-10 text-center text-slate-400">
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