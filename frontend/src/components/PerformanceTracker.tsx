import React, { useState } from 'react';
import {
  LineChart, TrendingUp, TrendingDown, Target, Activity,
  Users, Calendar, BarChart3, Zap, AlertTriangle, CheckCircle,
  Clock, Star, Award, Filter, Download, RefreshCw
} from 'lucide-react';
import { exportService } from '../services/exportService';

const PerformanceTracker: React.FC = () => {
  const [selectedPlayer, setSelectedPlayer] = useState('mbappe');
  const [timeframe, setTimeframe] = useState('season');
  const [metricType, setMetricType] = useState('overall');

  const players = [
    { id: 'mbappe', name: 'Kylian Mbappé', position: 'LW/ST', club: 'PSG' },
    { id: 'haaland', name: 'Erling Haaland', position: 'ST', club: 'Manchester City' },
    { id: 'messi', name: 'Lionel Messi', position: 'RW/CAM', club: 'Inter Miami' },
    { id: 'pedri', name: 'Pedri', position: 'CM', club: 'Barcelona' }
  ];

  const performanceMetrics = {
    mbappe: {
      overall: 9.2,
      goals: 28,
      assists: 12,
      xG: 24.7,
      xA: 9.8,
      passAccuracy: 87,
      dribbleSuccess: 78,
      sprintSpeed: 35.2,
      distanceCovered: 10.8,
      form: [8.5, 9.1, 8.8, 9.4, 9.2, 8.9, 9.6, 9.0, 9.3, 9.1],
      trend: 'stable'
    }
  };

  const developmentTracking = [
    {
      metric: 'Technical Skills',
      current: 92,
      target: 95,
      progress: 87,
      trend: 'improving',
      timeToTarget: '8 months'
    },
    {
      metric: 'Physical Attributes',
      current: 89,
      target: 92,
      progress: 73,
      trend: 'improving',
      timeToTarget: '12 months'
    },
    {
      metric: 'Mental Strength',
      current: 85,
      target: 90,
      progress: 60,
      trend: 'stable',
      timeToTarget: '18 months'
    },
    {
      metric: 'Tactical Awareness',
      current: 88,
      target: 93,
      progress: 45,
      trend: 'improving',
      timeToTarget: '15 months'
    }
  ];

  const performanceAlerts = [
    {
      type: 'improvement',
      message: 'Mbappé sprint speed increased by 2.1 km/h in last month',
      severity: 'positive',
      time: '2 hours ago'
    },
    {
      type: 'concern',
      message: 'Pedri pass accuracy dropped below 90% threshold',
      severity: 'warning',
      time: '1 day ago'
    },
    {
      type: 'milestone',
      message: 'Haaland reached 25 goals milestone 3 games ahead of projection',
      severity: 'positive',
      time: '3 days ago'
    },
    {
      type: 'injury_risk',
      message: 'Messi workload exceeding recommended limits',
      severity: 'critical',
      time: '1 week ago'
    }
  ];

  const comparisonData = [
    { player: 'Kylian Mbappé', rating: 9.2, goals: 28, assists: 12, efficiency: 94 },
    { player: 'Erling Haaland', rating: 9.0, goals: 32, assists: 5, efficiency: 91 },
    { player: 'Lionel Messi', rating: 8.8, goals: 18, assists: 22, efficiency: 89 },
    { player: 'Pedri', rating: 8.5, goals: 4, assists: 15, efficiency: 87 }
  ];

  const injuryRiskFactors = [
    { factor: 'Workload Management', risk: 23, status: 'low' },
    { factor: 'Previous Injuries', risk: 45, status: 'medium' },
    { factor: 'Playing Surface', risk: 12, status: 'low' },
    { factor: 'Match Intensity', risk: 67, status: 'high' },
    { factor: 'Recovery Time', risk: 34, status: 'medium' }
  ];

  const handleExport = async () => {
    const selectedPlayerData = players.find(p => p.id === selectedPlayer);

    const exportData = [
      {
        Category: 'Overview',
        Metric: 'Overall Rating',
        Value: performanceMetrics.mbappe.overall,
      },
      {
        Category: 'Overview',
        Metric: 'Goals',
        Value: performanceMetrics.mbappe.goals,
      },
      {
        Category: 'Overview',
        Metric: 'Assists',
        Value: performanceMetrics.mbappe.assists,
      },
      {
        Category: 'Performance',
        Metric: 'Pass Accuracy',
        Value: `${performanceMetrics.mbappe.passAccuracy}%`,
      },
      {
        Category: 'Performance',
        Metric: 'Dribble Success',
        Value: `${performanceMetrics.mbappe.dribbleSuccess}%`,
      },
      {
        Category: 'Physical',
        Metric: 'Sprint Speed',
        Value: `${performanceMetrics.mbappe.sprintSpeed} km/h`,
      },
      {
        Category: 'Physical',
        Metric: 'Distance Covered',
        Value: `${performanceMetrics.mbappe.distanceCovered} km`,
      },
    ];

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `performance_${selectedPlayerData?.name.replace(/\s+/g, '_')}_${Date.now()}.pdf`,
        data: exportData,
        header: `Performance Tracker - ${selectedPlayerData?.name || 'Player'}`,
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('Performance report exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <LineChart className="h-8 w-8 mr-3 text-blue-500" />
          Performance Tracker
        </h1>
        <div className="flex items-center space-x-4">
          <select
            value={selectedPlayer}
            onChange={(e) => setSelectedPlayer(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            {players.map((player) => (
              <option key={player.id} value={player.id}>
                {player.name}
              </option>
            ))}
          </select>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="season">Current Season</option>
            <option value="month">Last Month</option>
            <option value="week">Last Week</option>
          </select>
          <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">9.2</div>
              <div className="text-slate-400 text-sm">Overall Rating</div>
            </div>
            <Star className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            +0.3 this month
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">28</div>
              <div className="text-slate-400 text-sm">Goals Scored</div>
            </div>
            <Target className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <Award className="h-4 w-4 mr-1" />
            Above xG by 3.3
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">94%</div>
              <div className="text-slate-400 text-sm">Efficiency</div>
            </div>
            <BarChart3 className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-blue-400 text-sm">
            <CheckCircle className="h-4 w-4 mr-1" />
            Top 5% in league
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">23%</div>
              <div className="text-slate-400 text-sm">Injury Risk</div>
            </div>
            <Activity className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <CheckCircle className="h-4 w-4 mr-1" />
            Low risk level
          </div>
        </div>
      </div>

      {/* Performance Chart & Development Tracking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Performance Trend</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Last 10 matches</span>
              <span className="text-sm text-green-400">Trending: Stable</span>
            </div>
            
            {/* Simulated Chart */}
            <div className="h-48 bg-slate-700 rounded-lg p-4 flex items-end justify-between">
              {performanceMetrics.mbappe.form.map((rating, index) => (
                <div key={index} className="flex flex-col items-center">
                  <div
                    className="bg-blue-400 rounded-t"
                    style={{ 
                      height: `${(rating / 10) * 160}px`,
                      width: '20px'
                    }}
                  ></div>
                  <span className="text-xs text-slate-400 mt-2">{rating}</span>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="text-slate-400">Average</div>
                <div className="font-bold text-blue-400">9.1</div>
              </div>
              <div className="text-center">
                <div className="text-slate-400">Peak</div>
                <div className="font-bold text-green-400">9.6</div>
              </div>
              <div className="text-center">
                <div className="text-slate-400">Low</div>
                <div className="font-bold text-red-400">8.5</div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Development Tracking</h3>
          <div className="space-y-4">
            {developmentTracking.map((item, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{item.metric}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-slate-400">{item.current}/100</span>
                    <span className={`text-sm ${
                      item.trend === 'improving' ? 'text-green-400' : 'text-slate-400'
                    }`}>
                      {item.trend === 'improving' ? '↗' : '→'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 mb-2">
                  <div className="flex-1 bg-slate-600 rounded-full h-2">
                    <div
                      className="bg-blue-400 h-2 rounded-full"
                      style={{ width: `${item.progress}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-slate-400">{item.progress}%</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Target: {item.target}</span>
                  <span>ETA: {item.timeToTarget}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Comparison */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Performance Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-2">Player</th>
                <th className="text-left py-3 px-2">Rating</th>
                <th className="text-left py-3 px-2">Goals</th>
                <th className="text-left py-3 px-2">Assists</th>
                <th className="text-left py-3 px-2">Efficiency</th>
                <th className="text-left py-3 px-2">Trend</th>
              </tr>
            </thead>
            <tbody>
              {comparisonData.map((player, index) => (
                <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                  <td className="py-3 px-2 font-semibold">{player.player}</td>
                  <td className="py-3 px-2">
                    <span className="text-yellow-400 font-bold">{player.rating}</span>
                  </td>
                  <td className="py-3 px-2">{player.goals}</td>
                  <td className="py-3 px-2">{player.assists}</td>
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-slate-600 rounded-full h-2">
                        <div
                          className="bg-green-400 h-2 rounded-full"
                          style={{ width: `${player.efficiency}%` }}
                        ></div>
                      </div>
                      <span className="text-sm">{player.efficiency}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <TrendingUp className="h-4 w-4 text-green-400" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alerts & Injury Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <AlertTriangle className="h-6 w-6 mr-2 text-yellow-400" />
            Performance Alerts
          </h3>
          <div className="space-y-4">
            {performanceAlerts.map((alert, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-full ${
                    alert.severity === 'positive' ? 'bg-green-600' :
                    alert.severity === 'warning' ? 'bg-yellow-600' :
                    'bg-red-600'
                  }`}>
                    {alert.severity === 'positive' && <CheckCircle className="h-4 w-4" />}
                    {alert.severity === 'warning' && <AlertTriangle className="h-4 w-4" />}
                    {alert.severity === 'critical' && <Activity className="h-4 w-4" />}
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

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Activity className="h-6 w-6 mr-2 text-red-400" />
            Injury Risk Analysis
          </h3>
          <div className="space-y-4">
            {injuryRiskFactors.map((factor, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{factor.factor}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    factor.status === 'low' ? 'bg-green-600 text-green-100' :
                    factor.status === 'medium' ? 'bg-yellow-600 text-yellow-100' :
                    'bg-red-600 text-red-100'
                  }`}>
                    {factor.status}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-slate-600 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        factor.status === 'low' ? 'bg-green-400' :
                        factor.status === 'medium' ? 'bg-yellow-400' :
                        'bg-red-400'
                      }`}
                      style={{ width: `${factor.risk}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold">{factor.risk}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceTracker;