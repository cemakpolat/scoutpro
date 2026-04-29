import React, { useState, useEffect } from 'react';
import { Brain, BarChart3, Target, TrendingUp, TrendingDown, Zap, Users, Star, Activity, Loader2 } from 'lucide-react';
import PotentialChart from './PotentialChart';
import PerformancePrediction from './PerformancePrediction';
import apiService from '../services/api';
import { useData } from '../context/DataContext';

const MLAnalysis: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('potential');
  const [overviewStats, setOverviewStats] = useState<any>(null);

  const { players: contextPlayers } = useData();

  // Fetch overview stats from API
  useEffect(() => {
    apiService.getDashboardOverview().then((res: any) => {
      if (res?.data) setOverviewStats(res.data);
    }).catch(() => {});
  }, []);

  const models = [
    { id: 'potential', name: 'Player Potential', icon: Star },
    { id: 'performance', name: 'Performance Prediction', icon: Activity },
    { id: 'injury', name: 'Injury Risk Analysis', icon: Target },
    { id: 'market', name: 'Market Value Prediction', icon: TrendingUp },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Brain className="h-8 w-8 mr-3 text-purple-400" />
          ML Insights & Predictions
        </h1>
        <div className="flex items-center space-x-2 text-sm text-slate-400">
          <Zap className="h-4 w-4" />
          <span>AI Models last updated 2 hours ago</span>
        </div>
      </div>

      {/* Model Selection */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-4">Select Analysis Model</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {models.map((model) => {
            const Icon = model.icon;
            return (
              <button
                key={model.id}
                onClick={() => setSelectedModel(model.id)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedModel === model.id
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-slate-700 hover:border-slate-600'
                }`}
              >
                <Icon className={`h-6 w-6 mx-auto mb-2 ${
                  selectedModel === model.id ? 'text-purple-400' : 'text-slate-400'
                }`} />
                <div className="text-sm font-medium">{model.name}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* AI Insights Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">94.2%</div>
              <div className="text-slate-400 text-sm">Model Accuracy</div>
            </div>
            <Target className="h-8 w-8 text-green-400" />
          </div>
        </div>
        
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{overviewStats?.summary?.totalPlayers || contextPlayers.length || '—'}</div>
              <div className="text-slate-400 text-sm">Players Analyzed</div>
            </div>
            <Users className="h-8 w-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{contextPlayers.filter((p: any) => (p.rating || 0) >= 8).length || '—'}</div>
              <div className="text-slate-400 text-sm">High Potential</div>
            </div>
            <Star className="h-8 w-8 text-yellow-400" />
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">87%</div>
              <div className="text-slate-400 text-sm">Prediction Success</div>
            </div>
            <BarChart3 className="h-8 w-8 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Dynamic Content Based on Selected Model */}
      {selectedModel === 'potential' && <PotentialAnalysis />}
      {selectedModel === 'performance' && <PerformancePrediction />}
      {selectedModel === 'injury' && <InjuryRiskAnalysis />}
      {selectedModel === 'market' && <MarketValuePrediction />}
    </div>
  );
};

const PotentialAnalysis: React.FC = () => {
  const [topPlayers, setTopPlayers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiService.getPlayerRankings('rating', 5).then((res: any) => {
      const ranked = res?.data || res?.players || [];
      if (Array.isArray(ranked) && ranked.length > 0) {
        setTopPlayers(ranked.map((p: any) => ({
          name: p.name,
          club: p.club || p.team || 'Unknown',
          potential: Math.min(99, Math.round((p.rating || 80) * 1.1)),
          current: Math.round(p.rating || 80),
        })));
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const displayPlayers = topPlayers.length > 0 ? topPlayers : [
    { name: 'Top Prospect 1', club: 'Club A', potential: 94, current: 84 },
    { name: 'Top Prospect 2', club: 'Club B', potential: 92, current: 82 },
    { name: 'Top Prospect 3', club: 'Club C', potential: 91, current: 81 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Top Potential Players</h3>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin text-purple-400" /></div>
        ) : (
        <div className="space-y-4">
          {displayPlayers.map((player: any, index: number) => (
            <div key={index} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <div>
                  <div className="font-semibold">{player.name}</div>
                  <div className="text-slate-400 text-sm">{player.club}</div>
                </div>
                <div className="text-right">
                  <div className="text-purple-400 font-bold">{player.potential}</div>
                  <div className="text-slate-400 text-sm">Max Potential</div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-slate-400">Current: {player.current}</span>
                <div className="flex-1 bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full"
                    style={{ width: `${(player.current / player.potential) * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm text-purple-400">+{player.potential - player.current}</span>
              </div>
            </div>
          ))}
        </div>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Potential Growth Factors</h3>
        <div className="space-y-6">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span>Technical Skills</span>
              <span className="text-green-400 font-semibold">85%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className="bg-green-400 h-2 rounded-full" style={{ width: '85%' }}></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span>Physical Development</span>
              <span className="text-blue-400 font-semibold">78%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className="bg-blue-400 h-2 rounded-full" style={{ width: '78%' }}></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span>Mental Attributes</span>
              <span className="text-yellow-400 font-semibold">92%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className="bg-yellow-400 h-2 rounded-full" style={{ width: '92%' }}></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span>Tactical Understanding</span>
              <span className="text-purple-400 font-semibold">88%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className="bg-purple-400 h-2 rounded-full" style={{ width: '88%' }}></div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-slate-700 rounded-lg">
            <h4 className="font-semibold mb-2 text-purple-400">AI Recommendation</h4>
            <p className="text-sm text-slate-300">
              Focus on physical conditioning and tactical training. Current trajectory suggests 
              potential rating increase of 8-12 points over next 2 seasons with proper development.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const InjuryRiskAnalysis: React.FC = () => {
  const [injuryPlayers, setInjuryPlayers] = useState<any[]>([]);

  useEffect(() => {
    apiService.getPlayerRankings('rating', 5).then((res: any) => {
      const ranked = res?.data || res?.players || [];
      if (Array.isArray(ranked) && ranked.length > 0) {
        setInjuryPlayers(ranked.map((p: any, i: number) => ({
          name: p.name,
          club: p.club || p.team || 'Unknown',
          risk: Math.max(30, 85 - i * 8 + Math.round(Math.random() * 10)),
          type: ['Muscle Fatigue', 'Joint Stress', 'Overload', 'Recovery', 'Muscle Strain'][i % 5],
        })));
      }
    }).catch(() => {});
  }, []);

  const displayPlayers = injuryPlayers.length > 0 ? injuryPlayers : [
    { name: 'Player A', club: 'Club 1', risk: 78, type: 'Muscle Fatigue' },
    { name: 'Player B', club: 'Club 2', risk: 65, type: 'Overload' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Injury Risk Assessment</h3>
        <div className="space-y-4">
          {displayPlayers.map((player: any, index: number) => (
            <div key={index} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <div>
                  <div className="font-semibold">{player.name}</div>
                  <div className="text-slate-400 text-sm">{player.club}</div>
                </div>
                <div className="text-right">
                  <div className={`font-bold ${
                    player.risk > 75 ? 'text-red-400' : 
                    player.risk > 60 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {player.risk}%
                  </div>
                  <div className="text-slate-400 text-sm">Risk Level</div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">{player.type}</span>
                <div className={`px-2 py-1 rounded text-xs ${
                  player.risk > 75 ? 'bg-red-600 text-red-100' : 
                  player.risk > 60 ? 'bg-yellow-600 text-yellow-100' : 'bg-green-600 text-green-100'
                }`}>
                  {player.risk > 75 ? 'HIGH' : player.risk > 60 ? 'MEDIUM' : 'LOW'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Prevention Recommendations</h3>
        <div className="space-y-4">
          <div className="p-4 bg-red-600/10 border border-red-600/20 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-5 w-5 text-red-400" />
              <span className="font-semibold text-red-400">High Risk Players</span>
            </div>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>• Immediate rest and recovery protocol</li>
              <li>• Reduced training intensity for 1-2 weeks</li>
              <li>• Enhanced physiotherapy sessions</li>
              <li>• Monitor vital signs closely</li>
            </ul>
          </div>

          <div className="p-4 bg-yellow-600/10 border border-yellow-600/20 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Activity className="h-5 w-5 text-yellow-400" />
              <span className="font-semibold text-yellow-400">Medium Risk Players</span>
            </div>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>• Modified training schedule</li>
              <li>• Additional warm-up routines</li>
              <li>• Preventive physiotherapy</li>
              <li>• Regular fitness assessments</li>
            </ul>
          </div>

          <div className="p-4 bg-green-600/10 border border-green-600/20 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Star className="h-5 w-5 text-green-400" />
              <span className="font-semibold text-green-400">Low Risk Players</span>
            </div>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>• Maintain current training load</li>
              <li>• Continue regular monitoring</li>
              <li>• Focus on performance optimization</li>
              <li>• Standard recovery protocols</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

const MarketValuePrediction: React.FC = () => {
  const [marketPlayers, setMarketPlayers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiService.getMarketTrends().catch(() => null),
      apiService.getPlayerRankings('rating', 5).catch(() => null),
    ]).then(([trends, rankings]) => {
      const ranked = rankings?.data || rankings?.players || [];
      if (Array.isArray(ranked) && ranked.length > 0) {
        setMarketPlayers(ranked.map((p: any) => {
          const val = p.marketValue || p.value || 50;
          const predicted = Math.round(val * 1.2);
          const change = '+' + Math.round(((predicted - val) / val) * 100) + '%';
          return {
            name: p.name,
            current: `€${val}M`,
            predicted: `€${predicted}M`,
            change,
            confidence: Math.min(95, Math.round(75 + (p.rating || 0) * 2)),
          };
        }));
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const displayPlayers = marketPlayers.length > 0 ? marketPlayers : [
    { name: 'Top Player 1', current: '€80M', predicted: '€100M', change: '+25%', confidence: 88 },
    { name: 'Top Player 2', current: '€60M', predicted: '€78M', change: '+30%', confidence: 85 },
  ];

  return (
    <div className="space-y-8">
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Market Value Predictions (Next 12 Months)</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-2">Player</th>
                <th className="text-left py-3 px-2">Current Value</th>
                <th className="text-left py-3 px-2">Predicted Value</th>
                <th className="text-left py-3 px-2">Change</th>
                <th className="text-left py-3 px-2">Confidence</th>
                <th className="text-left py-3 px-2">Key Factors</th>
              </tr>
            </thead>
            <tbody>
              {displayPlayers.map((player: any, index: number) => (
                <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                  <td className="py-3 px-2 font-semibold">{player.name}</td>
                  <td className="py-3 px-2">{player.current}</td>
                  <td className="py-3 px-2 text-green-400 font-semibold">{player.predicted}</td>
                  <td className="py-3 px-2">
                    <span className="text-green-400 flex items-center">
                      <TrendingUp className="h-4 w-4 mr-1" />
                      {player.change}
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-12 bg-slate-600 rounded-full h-2">
                        <div
                          className="bg-purple-400 h-2 rounded-full"
                          style={{ width: `${player.confidence}%` }}
                        ></div>
                      </div>
                      <span className="text-sm">{player.confidence}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-slate-400 text-sm">
                    Age, Performance, Contracts
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Value Drivers Analysis</h3>
          <div className="space-y-4">
            {[
              { factor: 'Performance Metrics', weight: 35, impact: 'High' },
              { factor: 'Age & Contract Status', weight: 25, impact: 'High' },
              { factor: 'Market Demand', weight: 20, impact: 'Medium' },
              { factor: 'Team Success', weight: 15, impact: 'Medium' },
              { factor: 'Media Exposure', weight: 5, impact: 'Low' },
            ].map((driver, index) => (
              <div key={index} className="p-3 bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{driver.factor}</span>
                  <span className={`text-sm px-2 py-1 rounded ${
                    driver.impact === 'High' ? 'bg-red-600 text-red-100' :
                    driver.impact === 'Medium' ? 'bg-yellow-600 text-yellow-100' :
                    'bg-green-600 text-green-100'
                  }`}>
                    {driver.impact}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-slate-600 rounded-full h-2">
                    <div
                      className="bg-blue-400 h-2 rounded-full"
                      style={{ width: `${driver.weight}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-slate-400">{driver.weight}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Market Trends</h3>
          <div className="space-y-4">
            <div className="p-4 bg-green-600/10 border border-green-600/20 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="h-5 w-5 text-green-400" />
                <span className="font-semibold text-green-400">Rising Markets</span>
              </div>
              <p className="text-sm text-slate-300">
                Young attackers and versatile midfielders showing 15-25% value increases. 
                Premier League and La Liga players command premium valuations.
              </p>
            </div>

            <div className="p-4 bg-yellow-600/10 border border-yellow-600/20 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="h-5 w-5 text-yellow-400" />
                <span className="font-semibold text-yellow-400">Stable Segments</span>
              </div>
              <p className="text-sm text-slate-300">
                Established defenders and goalkeepers maintaining steady values. 
                Players aged 26-29 showing consistent market stability.
              </p>
            </div>

            <div className="p-4 bg-red-600/10 border border-red-600/20 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingDown className="h-5 w-5 text-red-400" />
                <span className="font-semibold text-red-400">Declining Factors</span>
              </div>
              <p className="text-sm text-slate-300">
                Players over 30 facing 5-10% annual depreciation. Injury-prone players 
                showing accelerated value decline regardless of talent.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLAnalysis;