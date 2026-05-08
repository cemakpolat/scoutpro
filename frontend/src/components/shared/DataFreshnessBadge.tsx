import React from 'react';

type FreshnessStatus = 'live' | 'verified' | 'historical' | 'stale';

interface DataFreshnessBadgeProps {
  status: FreshnessStatus;
  className?: string;
}

export const DataFreshnessBadge: React.FC<DataFreshnessBadgeProps> = ({ status, className = '' }) => {
  const getStyles = () => {
    switch (status) {
      case 'live':
        return 'bg-green-100 text-green-800 border-green-200 animate-pulse';
      case 'verified':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'historical':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'stale':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getLabel = () => {
    switch (status) {
      case 'live': return 'LIVE';
      case 'verified': return 'VERIFIED';
      case 'historical': return 'HISTORICAL';
      case 'stale': return 'STALE';
      default: return status.toUpperCase();
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStyles()} ${className}`}>
      {getLabel()}
    </span>
  );
};
