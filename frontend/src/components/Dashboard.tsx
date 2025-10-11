import React from 'react';
import { TrendingUp, Users, Eye, Star, ArrowUp, ArrowDown, Target, Activity, Brain, Globe } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import StatCard from './StatCard';
import RecentActivity from './RecentActivity';
import TopPerformers from './TopPerformers';

const Dashboard: React.FC = () => {
  const { players, matches, loading: loadingState, errors } = useData();
  
  // Fetch dashboard analytics
  const { data: analytics, loading: analyticsLoading } = useApi(
    () => apiService.getAnalytics('dashboard'),
    []
  );

  // Fetch market intelligence
  const { data: marketTrends, loading: marketLoading } = useApi(
    () => apiService.getMarketTrends(),
    []
  );

  // Fetch tactical patterns
  const { data: tacticalPatterns, loading: tacticalLoading } = useApi(
    () => apiService.getTacticalPatterns(),
    []
  );

  // Calculate real-time metrics from live data
  const metrics = {
    totalPlayers: players.length,
    totalMatches: matches.length,
    totalMarketValue: players.reduce((sum, player) => {
      const value = parseFloat(player.marketValue.replace(/[€M]/g, '')) || 0;
      return sum + value;
    }, 0),
    aiPredictions: analytics?.predictions?.total || 0,
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Executive Dashboard</h1>
        <div className="text-slate-400">
          Real-time data • Last sync: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Global Player Database"
          value={metrics.totalPlayers.toLocaleString()}
          change="+2.3%"
          changeType="increase"
          icon={Users}
        />
        <StatCard
          title="Matches Analyzed"
          value={metrics.totalMatches.toLocaleString()}
          change="+8.7%"
          changeType="increase"
          icon={Eye}
        />
        <StatCard
          title="Total Market Value Tracked"
          value={`€${(metrics.totalMarketValue / 1000).toFixed(1)}B`}
          change="+15.8%"
          changeType="increase"
          icon={TrendingUp}
        />
        <StatCard
          title="AI Predictions Generated"
          value={metrics.aiPredictions.toLocaleString()}
          change="+23.4%"
          changeType="increase"
          icon={Brain}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <TopPerformers />
        </div>
        <div>
          <RecentActivity />
        </div>
      </div>

      {/* Market Intelligence */}
      {!marketLoading && marketTrends && (
        <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Globe className="h-6 w-6 mr-2 text-blue-400" />
          Global Market Intelligence
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {marketTrends.slice(0, 3).map((trend, index) => (
            <div key={index} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-semibold">{trend.position}</h4>
                <span className="text-green-400 font-bold">{trend.change}</span>
              </div>
              <div className="text-2xl font-bold text-white mb-2">{trend.averageValue}</div>
              <div className="text-sm text-slate-400 mb-3">Average Market Value</div>
              <div className="space-y-2">
                <div className="text-xs text-slate-400">Hot Markets:</div>
                <div className="flex flex-wrap gap-1">
                  {['Premier League', 'La Liga', 'Serie A'].map((market, i) => (
                    <span key={i} className="px-2 py-1 bg-blue-600/20 text-blue-300 text-xs rounded">
                      {market}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      )}

      {/* Tactical Intelligence */}
      {!tacticalLoading && tacticalPatterns && (
        <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Target className="h-6 w-6 mr-2 text-purple-400" />
          Tactical Intelligence & Trends
        </h3>
        <div className="space-y-4">
          {tacticalPatterns.slice(0, 3).map((pattern, index) => (
            <div key={index} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-lg">{pattern.name}</h4>
                <div className="flex items-center space-x-4">
                  <div className="text-center">
                    <div className="text-sm text-slate-400">Adoption</div>
                    <div className="font-bold text-blue-400">{pattern.frequency}%</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-slate-400">Effectiveness</div>
                    <div className="font-bold text-green-400">{pattern.successRate}%</div>
                  </div>
                </div>
              </div>
              <p className="text-slate-300 text-sm mb-3">{pattern.description}</p>
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  Active Zones: {pattern.zones.join(', ')}
                </div>
                <div className="text-xs text-purple-400 font-medium">
                  Impact: {pattern.impact}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      )}

      {/* Performance Overview */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Activity className="h-6 w-6 mr-2 text-green-400" />
          Platform Performance Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">{analytics?.modelAccuracy || '97.3'}%</div>
            <div className="text-slate-400">AI Model Accuracy</div>
            <div className="text-xs text-green-400 mt-1">+2.1% this month</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400 mb-2">{analytics?.activeScouts || '2,847'}</div>
            <div className="text-slate-400">Daily Active Scouts</div>
            <div className="text-xs text-blue-400 mt-1">+18% vs last week</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-400 mb-2">{analytics?.transferPredictions || '847'}</div>
            <div className="text-slate-400">Transfer Predictions</div>
            <div className="text-xs text-yellow-400 mt-1">89% success rate</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400 mb-2">{analytics?.responseTime || '156'}ms</div>
            <div className="text-slate-400">Avg Response Time</div>
            <div className="text-xs text-purple-400 mt-1">Real-time analytics</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;