import React from 'react';
import { Users, Eye, Activity } from 'lucide-react';
import { useData } from '../context/DataContext';
import StatCard from './StatCard';
import RecentActivity from './RecentActivity';
import TopPerformers from './TopPerformers';

const Dashboard: React.FC = () => {
  const { players, matches, teams } = useData();

  const metrics = {
    totalPlayers: players.length,
    totalMatches: matches.length,
    totalTeams: (teams as any[])?.length ?? 0,
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Player Database"
          value={metrics.totalPlayers.toLocaleString()}
          icon={Users}
        />
        <StatCard
          title="Match Count"
          value={metrics.totalMatches.toLocaleString()}
          icon={Eye}
        />
        <StatCard
          title="Team Count"
          value={metrics.totalTeams.toLocaleString()}
          icon={Activity}
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

    </div>
  );
};

export default Dashboard;