import React, { useState } from 'react';
import { 
  BarChart3, TrendingUp, Users, Target, Zap, 
  Map, Activity, Brain, Filter, Calendar 
} from 'lucide-react';

const AnalyticsDashboard: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState('xT');
  const [timeframe, setTimeframe] = useState('season');

  const teamStyles = [
    { name: 'Manchester City', style: 'Possession Heavy', similarity: 94, color: 'bg-blue-500' },
    { name: 'Barcelona', style: 'Possession Heavy', similarity: 91, color: 'bg-blue-500' },
    { name: 'Liverpool', style: 'Counter-Pressing', similarity: 88, color: 'bg-red-500' },
    { name: 'Borussia Dortmund', style: 'Counter-Pressing', similarity: 85, color: 'bg-red-500' },
    { name: 'Real Madrid', style: 'Transition Based', similarity: 82, color: 'bg-purple-500' },
    { name: 'Bayern Munich', style: 'High Intensity', similarity: 89, color: 'bg-green-500' },
  ];

  const xTData = [
    { zone: 'Final Third', value: 0.85, color: 'bg-red-500' },
    { zone: 'Penalty Area', value: 0.92, color: 'bg-red-600' },
    { zone: 'Central Midfield', value: 0.23, color: 'bg-yellow-500' },
    { zone: 'Wide Areas', value: 0.31, color: 'bg-orange-500' },
    { zone: 'Defensive Third', value: 0.08, color: 'bg-green-500' },
  ];

  const playerDevelopment = [
    { name: 'Pedri', age: 21, currentRating: 85, projectedRating: 92, development: '+7' },
    { name: 'Gavi', age: 19, currentRating: 82, projectedRating: 89, development: '+7' },
    { name: 'Jude Bellingham', age: 20, currentRating: 84, projectedRating: 91, development: '+7' },
    { name: 'Jamal Musiala', age: 21, currentRating: 83, projectedRating: 88, development: '+5' },
    { name: 'Eduardo Camavinga', age: 21, currentRating: 81, projectedRating: 87, development: '+6' },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <BarChart3 className="h-8 w-8 mr-3 text-purple-500" />
          Analytics Lab
        </h1>
        <div className="flex items-center space-x-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="season">Current Season</option>
            <option value="month">Last Month</option>
            <option value="week">Last Week</option>
          </select>
          <button className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
            <Brain className="h-4 w-4" />
            <span>AI Insights</span>
          </button>
        </div>
      </div>

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">847</div>
              <div className="text-slate-400 text-sm">Teams Analyzed</div>
            </div>
            <Users className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            +23 this week
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">12.4K</div>
              <div className="text-slate-400 text-sm">Data Points</div>
            </div>
            <Activity className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            Real-time updates
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">94.7%</div>
              <div className="text-slate-400 text-sm">Model Accuracy</div>
            </div>
            <Target className="h-8 w-8 text-purple-400" />
          </div>
          <div className="flex items-center mt-2 text-purple-400 text-sm">
            <Zap className="h-4 w-4 mr-1" />
            ML Enhanced
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">156</div>
              <div className="text-slate-400 text-sm">Scenarios Run</div>
            </div>
            <Brain className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <Activity className="h-4 w-4 mr-1" />
            Simulations active
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Team Style Clustering */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Users className="h-6 w-6 mr-2 text-blue-400" />
            Team Style Clustering
          </h3>
          <div className="space-y-4">
            {teamStyles.map((team, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded-full ${team.color}`}></div>
                    <span className="font-semibold">{team.name}</span>
                  </div>
                  <span className="text-slate-400 text-sm">{team.similarity}% match</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">{team.style}</span>
                  <div className="w-24 bg-slate-600 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${team.color}`}
                      style={{ width: `${team.similarity}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Expected Threat (xT) Maps */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Map className="h-6 w-6 mr-2 text-red-400" />
            Expected Threat (xT) Analysis
          </h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-4 mb-4">
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm"
              >
                <option value="xT">Expected Threat</option>
                <option value="xG">Expected Goals</option>
                <option value="xA">Expected Assists</option>
              </select>
              <span className="text-sm text-slate-400">Player: Kylian Mbappé</span>
            </div>
            
            {xTData.map((zone, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">{zone.zone}</span>
                  <span className="text-sm font-semibold">{zone.value}</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${zone.color}`}
                    style={{ width: `${zone.value * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
            
            <div className="mt-6 p-4 bg-slate-700 rounded-lg">
              <h4 className="font-semibold mb-2 text-red-400">Key Insight</h4>
              <p className="text-sm text-slate-300">
                Mbappé generates highest threat in penalty area (0.92 xT) and shows 
                exceptional ability to create danger from wide positions.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Player Development Tracking */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <TrendingUp className="h-6 w-6 mr-2 text-green-400" />
          Player Development Tracking
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-2">Player</th>
                <th className="text-left py-3 px-2">Age</th>
                <th className="text-left py-3 px-2">Current Rating</th>
                <th className="text-left py-3 px-2">Projected Rating</th>
                <th className="text-left py-3 px-2">Development</th>
                <th className="text-left py-3 px-2">Trajectory</th>
                <th className="text-left py-3 px-2">Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {playerDevelopment.map((player, index) => (
                <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                  <td className="py-3 px-2 font-semibold">{player.name}</td>
                  <td className="py-3 px-2">{player.age}</td>
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-2">
                      <span>{player.currentRating}</span>
                      <div className="w-16 bg-slate-600 rounded-full h-2">
                        <div
                          className="bg-blue-400 h-2 rounded-full"
                          style={{ width: `${player.currentRating}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-400 font-semibold">{player.projectedRating}</span>
                      <div className="w-16 bg-slate-600 rounded-full h-2">
                        <div
                          className="bg-green-400 h-2 rounded-full"
                          style={{ width: `${player.projectedRating}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <span className="text-green-400 font-semibold">{player.development}</span>
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center">
                      <TrendingUp className="h-4 w-4 text-green-400 mr-1" />
                      <span className="text-green-400 text-sm">Positive</span>
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <span className="px-2 py-1 bg-green-600 text-green-100 text-xs rounded">
                      Low
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Set-Piece Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Target className="h-6 w-6 mr-2 text-yellow-400" />
            Set-Piece Analysis
          </h3>
          <div className="space-y-4">
            {[
              { type: 'Corner Kicks', success: 23, total: 67, probability: 34 },
              { type: 'Free Kicks', success: 8, total: 45, probability: 18 },
              { type: 'Penalties', success: 12, total: 14, probability: 86 },
              { type: 'Throw-ins', success: 156, total: 234, probability: 67 },
            ].map((setpiece, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{setpiece.type}</span>
                  <span className="text-yellow-400 font-bold">{setpiece.probability}%</span>
                </div>
                <div className="flex justify-between text-sm text-slate-400 mb-2">
                  <span>Success: {setpiece.success}/{setpiece.total}</span>
                  <span>Conversion Rate</span>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-yellow-400 h-2 rounded-full"
                    style={{ width: `${setpiece.probability}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Brain className="h-6 w-6 mr-2 text-purple-400" />
            Scenario Simulations
          </h3>
          <div className="space-y-4">
            <div className="p-4 bg-purple-600/10 border border-purple-600/20 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Zap className="h-5 w-5 text-purple-400" />
                <span className="font-semibold text-purple-400">Active Simulation</span>
              </div>
              <p className="text-sm text-slate-300 mb-3">
                "What if Mbappé joins Manchester City?"
              </p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-slate-400">Expected Goals</div>
                  <div className="font-semibold text-green-400">+0.8 per game</div>
                </div>
                <div>
                  <div className="text-slate-400">Team Performance</div>
                  <div className="font-semibold text-blue-400">+12% win rate</div>
                </div>
              </div>
            </div>

            <div className="p-4 bg-blue-600/10 border border-blue-600/20 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="h-5 w-5 text-blue-400" />
                <span className="font-semibold text-blue-400">Formation Impact</span>
              </div>
              <p className="text-sm text-slate-300 mb-3">
                "4-3-3 vs 4-2-3-1 with current squad"
              </p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-slate-400">Possession</div>
                  <div className="font-semibold text-green-400">+7%</div>
                </div>
                <div>
                  <div className="text-slate-400">Defensive Stability</div>
                  <div className="font-semibold text-yellow-400">-3%</div>
                </div>
              </div>
            </div>

            <button className="w-full bg-purple-600 hover:bg-purple-700 py-3 rounded-lg font-semibold transition-colors">
              Run New Simulation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;