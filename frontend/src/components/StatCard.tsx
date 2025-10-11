import React from 'react';
import { Video as LucideIcon, ArrowUp, ArrowDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'increase' | 'decrease';
  icon: LucideIcon;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, changeType, icon: Icon }) => {
  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <div className="p-3 bg-slate-700 rounded-lg">
          <Icon className="h-6 w-6 text-green-400" />
        </div>
        {change && changeType && (
          <div className={`flex items-center space-x-1 text-sm ${
            changeType === 'increase' ? 'text-green-400' : 'text-red-400'
          }`}>
            {changeType === 'increase' ? (
              <ArrowUp className="h-4 w-4" />
            ) : (
              <ArrowDown className="h-4 w-4" />
            )}
            <span>{change}</span>
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-slate-400 text-sm">{title}</div>
    </div>
  );
};

export default StatCard;