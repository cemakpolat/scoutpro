import React, { useState, useEffect } from 'react';
import {
  DollarSign, TrendingUp, TrendingDown, AlertTriangle, Clock,
  Users, Target, Zap, Calendar, MapPin, Star, Eye, Filter,
  Search, Download, Bell, CheckCircle, XCircle, RefreshCw, Loader2
} from 'lucide-react';
import { exportService } from '../services/exportService';
import { useData } from '../context/DataContext';
import apiService from '../services/api';

const TransferHub: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('market-watch');
  const [priceRange, setPriceRange] = useState([0, 200]);
  const [loading, setLoading] = useState(true);
  const [apiMarketTrends, setApiMarketTrends] = useState<any>(null);
  const [apiPredictions, setApiPredictions] = useState<any>(null);

  const { players: contextPlayers } = useData();

  // Fetch market data from API
  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiService.getMarketTrends().catch(() => null),
      apiService.getTransferPredictions().catch(() => null),
    ]).then(([trends, predictions]) => {
      if (trends) setApiMarketTrends(trends);
      if (predictions) setApiPredictions(predictions);
    }).finally(() => setLoading(false));
  }, []);

  // Build transfer rumors from API predictions or fallback
  const transferRumors = apiPredictions?.data?.length > 0
    ? apiPredictions.data.slice(0, 5).map((p: any) => ({
        player: p.playerName || p.name || 'Unknown Player',
        currentClub: p.currentClub || p.fromClub || 'Unknown',
        targetClub: p.targetClub || p.toClub || 'TBD',
        probability: p.probability || p.confidence || 50,
        value: p.estimatedFee || p.value || '€0M',
        status: (p.probability || 50) > 70 ? 'hot' : (p.probability || 50) > 40 ? 'warm' : 'cold',
        deadline: p.deadline || '2026-06-30',
        sources: p.sources || ['ScoutPro AI'],
      }))
    : [
        { player: 'Transfer Target 1', currentClub: 'Club A', targetClub: 'Club B', probability: 75, value: '€60M', status: 'hot', deadline: '2026-06-30', sources: ['ScoutPro Analysis'] },
        { player: 'Transfer Target 2', currentClub: 'Club C', targetClub: 'Club D', probability: 45, value: '€35M', status: 'warm', deadline: '2026-08-31', sources: ['Market Analysis'] },
      ];

  // Build market trends from API or fallback
  const marketTrends = apiMarketTrends?.data?.length > 0
    ? apiMarketTrends.data.slice(0, 5).map((t: any) => ({
        position: t.position || t.name || 'Unknown',
        avgValue: t.avgValue || `€${t.averageValue || 0}M`,
        change: t.change || `${t.changePercent > 0 ? '+' : ''}${t.changePercent || 0}%`,
        trend: (t.changePercent || 0) > 0 ? 'up' : (t.changePercent || 0) < 0 ? 'down' : 'stable',
      }))
    : [
        { position: 'Striker', avgValue: '€67M', change: '+15%', trend: 'up' },
        { position: 'Winger', avgValue: '€45M', change: '+8%', trend: 'up' },
        { position: 'Midfielder', avgValue: '€38M', change: '-3%', trend: 'down' },
        { position: 'Defender', avgValue: '€32M', change: '+2%', trend: 'stable' },
        { position: 'Goalkeeper', avgValue: '€28M', change: '-5%', trend: 'down' },
      ];

  // Build contract expirations from context players or fallback
  const contractExpirations = contextPlayers.length > 0
    ? contextPlayers
        .filter((p: any) => p.contractEnd || p.contractExpiry)
        .slice(0, 6)
        .map((p: any) => ({
          player: p.name,
          club: p.club || p.team || 'Unknown',
          expires: p.contractEnd || p.contractExpiry || '2026-06-30',
          value: p.marketValue || `€${p.value || 10}M`,
          status: new Date(p.contractEnd || p.contractExpiry || '2026-12-31') < new Date('2026-06-30') ? 'critical' : 'expiring',
        }))
    : [
        { player: 'Player A', club: 'Club X', expires: '2026-06-30', value: '€25M', status: 'critical' },
        { player: 'Player B', club: 'Club Y', expires: '2026-12-31', value: '€15M', status: 'expiring' },
      ];

  // Valuation predictions - built from API or fallback (fixes the crash bug)
  const valuationPredictions = apiPredictions?.data?.length > 0
    ? apiPredictions.data.slice(0, 4).map((p: any) => ({
        player: p.playerName || p.name || 'Player',
        current: p.currentValue || p.value || '€50M',
        predicted: p.predictedValue || p.estimatedFee || '€65M',
        confidence: p.confidence || p.probability || 75,
        timeframe: p.timeframe || '12 months',
        factors: p.factors || ['Performance', 'Age', 'Market Demand'],
      }))
    : [
        { player: 'Top Prospect 1', current: '€80M', predicted: '€110M', confidence: 88, timeframe: '12 months', factors: ['Age', 'Performance', 'Demand'] },
        { player: 'Top Prospect 2', current: '€60M', predicted: '€85M', confidence: 82, timeframe: '12 months', factors: ['Form', 'Contract', 'League'] },
      ];

  const transferAlerts = [
    { type: 'rumor', message: `${transferRumors[0]?.player || 'Transfer'} rumor gaining momentum`, time: '5 min ago' },
    { type: 'contract', message: `${contractExpirations[0]?.player || 'Player'} contract expiring soon`, time: '1 hour ago' },
    { type: 'value', message: 'Market values updated from latest data', time: '2 hours ago' },
    { type: 'deadline', message: 'Transfer window updates available', time: '1 day ago' },
  ];

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
            onClick={() => {
              alert('🔔 Set Custom Alert\n\nConfigure alerts for:\n- Transfer rumors\n- Contract expirations\n- Market value changes\n- Transfer deadline reminders\n\n(Alert configuration will be available once backend is connected)');
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Bell className="h-4 w-4" />
            <span>Set Alert</span>
          </button>
          <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

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
              <div className="text-2xl font-bold text-white">€2.4B</div>
              <div className="text-slate-400 text-sm">Market Activity</div>
            </div>
            <DollarSign className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            +12% this window
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">247</div>
              <div className="text-slate-400 text-sm">Active Rumors</div>
            </div>
            <AlertTriangle className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <RefreshCw className="h-4 w-4 mr-1" />
            23 new today
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">89</div>
              <div className="text-slate-400 text-sm">Contracts Expiring</div>
            </div>
            <Clock className="h-8 w-8 text-red-400" />
          </div>
          <div className="flex items-center mt-2 text-red-400 text-sm">
            <AlertTriangle className="h-4 w-4 mr-1" />
            12 this month
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">€89M</div>
              <div className="text-slate-400 text-sm">Avg Transfer Fee</div>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-blue-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            +8% vs last window
          </div>
        </div>
      </div>

      {/* Dynamic Content Based on Selected Tab */}
      {selectedTab === 'market-watch' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Market Trends by Position</h3>
            <div className="space-y-4">
              {marketTrends.map((trend, index) => (
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
              ))}
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Recent Transfer Alerts</h3>
            <div className="space-y-4">
              {transferAlerts.map((alert, index) => (
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
              ))}
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'rumors' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Transfer Rumors</h3>
          <div className="space-y-4">
            {transferRumors.map((rumor, index) => (
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
                  <button
                    onClick={() => {
                      alert(`📍 Tracking Transfer Rumor\n\n${rumor.player}: ${rumor.currentClub} → ${rumor.targetClub}\nProbability: ${rumor.probability}%\nValue: ${rumor.value}\n\nYou will receive notifications about updates to this rumor.\n\n(Rumor tracking will be available once backend is connected)`);
                    }}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
                  >
                    Track Rumor
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedTab === 'valuations' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">AI Valuation Predictions</h3>
          <div className="space-y-6">
            {valuationPredictions.map((prediction, index) => (
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
            ))}
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
                  <th className="text-left py-3 px-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {contractExpirations.map((contract, index) => (
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
                    <td className="py-3 px-2">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => {
                            alert(`📍 Tracking ${contract.player}\n\nClub: ${contract.club}\nContract expires: ${contract.expires}\nValue: ${contract.value}\n\nYou will receive updates about this player's contract situation.\n\n(Contract tracking will be available once backend is connected)`);
                          }}
                          className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs transition-colors"
                        >
                          Track
                        </button>
                        <button
                          onClick={() => {
                            alert(`🔔 Alert Set for ${contract.player}\n\nYou will be notified:\n- 90 days before expiration\n- 30 days before expiration\n- On expiration date\n\n(Contract alerts will be available once backend is connected)`);
                          }}
                          className="px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs transition-colors"
                        >
                          Alert
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransferHub;