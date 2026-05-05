import React from 'react';
import { TrendingUp, Users, Eye, Star, ArrowUp, ArrowDown, Target, Activity, Brain, Globe } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import StatCard from './StatCard';
import RecentActivity from './RecentActivity';
import TopPerformers from './TopPerformers';

const formatMetric = (value: unknown, suffix = ''): string => {
  if (value === undefined || value === null || value === '') {
    return '—';
  }

  return `${value}${suffix}`;
};

const Dashboard: React.FC = () => {
  const { players, matches } = useData();
  
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
      const rawValue = typeof player.marketValue === 'string'
        ? player.marketValue
        : typeof player.marketValue === 'number'
          ? String(player.marketValue)
          : '';
      const value = parseFloat(rawValue.replace(/[^\d.]/g, '')) || 0;
      return sum + value;
    }, 0),
    aiPredictions: analytics?.predictions?.total || analytics?.transferPredictions || 0,
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
          icon={Users}
        />
        <StatCard
          title="Matches Analyzed"
          value={metrics.totalMatches.toLocaleString()}
          icon={Eye}
        />
        <StatCard
          title="Total Market Value Tracked"
          value={`€${(metrics.totalMarketValue / 1000).toFixed(1)}B`}
          icon={TrendingUp}
        />
        <StatCard
          title="AI Predictions Generated"
          value={metrics.aiPredictions.toLocaleString()}
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
      {!marketLoading && marketTrends && Array.isArray(marketTrends) && (
        <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Globe className="h-6 w-6 mr-2 text-blue-400" />
          Global Market Intelligence
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {marketTrends.slice(0, 3).map((trend, index) => (
            <div key={index} className="p-4 bg-slate-700 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-semibold">{trend?.position || 'N/A'}</h4>
                <span className="text-green-400 font-bold">{trend?.change || '—'}</span>
              </div>
              <div className="text-2xl font-bold text-white mb-2">{trend?.averageValue || '—'}</div>
              <div className="text-sm text-slate-400 mb-3">Average Market Value</div>
              <div className="text-xs text-slate-400">
                Live market trend feed
              </div>
            </div>
          ))}
        </div>
      </div>
      )}

      {/* Tactical Intelligence */}
      {!tacticalLoading && tacticalPatterns && Array.isArray(tacticalPatterns) && (
        <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Target className="h-6 w-6 mr-2 text-purple-400" />
          Tactical Intelligence & Trends
        </h3>
        <div className="space-y-4">
          {tacticalPatterns.slice(0, 3).map((pattern, index) => {
            const zones = Array.isArray(pattern?.zones) ? pattern.zones : [];
            return (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-lg">{pattern?.name || 'Unknown Pattern'}</h4>
                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <div className="text-sm text-slate-400">Adoption</div>
                      <div className="font-bold text-blue-400">{pattern?.frequency || 0}%</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-slate-400">Effectiveness</div>
                      <div className="font-bold text-green-400">{pattern?.successRate || 0}%</div>
                    </div>
                  </div>
                </div>
                <p className="text-slate-300 text-sm mb-3">{pattern?.description || 'No description available'}</p>
                <div className="flex items-center justify-between">
                  <div className="text-xs text-slate-400">
                    Active Zones: {zones.length > 0 ? zones.join(', ') : 'N/A'}
                  </div>
                  <div className="text-xs text-purple-400 font-medium">
                    Impact: {pattern?.impact || 'N/A'}
                  </div>
                </div>
              </div>
            );
          })}
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
            <div className="text-3xl font-bold text-green-400 mb-2">{formatMetric(analytics?.modelAccuracy, analytics?.modelAccuracy != null ? '%' : '')}</div>
            <div className="text-slate-400">AI Model Accuracy</div>
            <div className="text-xs text-green-400 mt-1">Live analytics service metric</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400 mb-2">{formatMetric(analytics?.activeScouts)}</div>
            <div className="text-slate-400">Daily Active Scouts</div>
            <div className="text-xs text-blue-400 mt-1">Live dashboard feed</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-400 mb-2">{formatMetric(analytics?.transferPredictions || analytics?.predictions?.total)}</div>
            <div className="text-slate-400">Transfer Predictions</div>
            <div className="text-xs text-yellow-400 mt-1">Current backend prediction volume</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400 mb-2">{formatMetric(analytics?.responseTime, analytics?.responseTime != null ? 'ms' : '')}</div>
            <div className="text-slate-400">Avg Response Time</div>
            <div className="text-xs text-purple-400 mt-1">Real-time analytics</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;