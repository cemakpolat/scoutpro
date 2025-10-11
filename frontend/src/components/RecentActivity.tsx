import React from 'react';
import { useData } from '../context/DataContext';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import { Clock, User, BarChart3, TrendingUp, AlertTriangle, CheckCircle, Zap, Target } from 'lucide-react';

const RecentActivity: React.FC = () => {
  const { notifications } = useData();
  const { data: aiInsights } = useApi(() => apiService.getAIInsights('general'), []);
  
  // Combine notifications and AI insights into activity feed
  const activities = [
    ...(notifications || []).slice(0, 3).map(notification => ({
      id: notification.id,
      type: notification.type,
      message: notification.message,
      time: new Date(notification.createdAt).toLocaleString(),
      icon: getIconForType(notification.type),
      priority: notification.priority
    })),
    ...(aiInsights || []).slice(0, 3).map(insight => ({
      id: insight.id,
      type: insight.type,
      message: insight.description,
      time: new Date(insight.createdAt).toLocaleString(),
      icon: getIconForType(insight.type),
      priority: insight.confidence > 80 ? 'high' : 'medium'
    }))
  ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 6);

  function getIconForType(type: string) {
    switch (type) {
      case 'prediction':
      case 'ai_prediction':
        return Zap;
      case 'analysis':
      case 'match_analysis':
        return BarChart3;
      case 'performance':
      case 'performance_alert':
        return TrendingUp;
      case 'injury':
      case 'injury_risk':
        return AlertTriangle;
      case 'tactical':
      case 'tactical_insight':
        return Target;
      default:
        return CheckCircle;
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'border-l-red-500 bg-red-500/5';
      case 'high': return 'border-l-yellow-500 bg-yellow-500/5';
      case 'medium': return 'border-l-blue-500 bg-blue-500/5';
      default: return 'border-l-green-500 bg-green-500/5';
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold flex items-center">
          <Clock className="h-6 w-6 mr-2 text-blue-400" />
          Intelligence Feed
        </h3>
        <div className="text-xs text-slate-400">Live updates</div>
      </div>
      
      <div className="space-y-3">
        {activities.length > 0 ? activities.map((activity) => {
          const Icon = activity.icon;
          return (
            <div key={activity.id} className={`flex items-start space-x-3 p-3 border-l-4 rounded-lg transition-colors hover:bg-slate-700/50 ${getPriorityColor(activity.priority)}`}>
              <div className={`p-2 rounded-lg ${
                activity.priority === 'critical' ? 'bg-red-600' :
                activity.priority === 'high' ? 'bg-yellow-600' :
                activity.priority === 'medium' ? 'bg-blue-600' :
                'bg-green-600'
              }`}>
                <Icon className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium leading-relaxed">{activity.message}</div>
                <div className="flex items-center justify-between mt-2">
                  <div className="text-slate-400 text-xs">{activity.time}</div>
                  <div className={`text-xs px-2 py-1 rounded ${
                    activity.priority === 'critical' ? 'bg-red-600/20 text-red-300' :
                    activity.priority === 'high' ? 'bg-yellow-600/20 text-yellow-300' :
                    activity.priority === 'medium' ? 'bg-blue-600/20 text-blue-300' :
                    'bg-green-600/20 text-green-300'
                  }`}>
                    {activity.priority.toUpperCase()}
                  </div>
                </div>
              </div>
            </div>
          );
        }) : (
          <div className="text-center py-8 text-slate-400">
            <Clock className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No recent activity</p>
          </div>
        )}
      </div>
      
      <div className="mt-6 pt-4 border-t border-slate-700">
        <button className="w-full text-sm text-blue-400 hover:text-blue-300 transition-colors font-medium">
          View All Intelligence Reports →
        </button>
      </div>
    </div>
  );
};

export default RecentActivity;