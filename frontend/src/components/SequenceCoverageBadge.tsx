import React from 'react';

interface SequenceCoverageBadgeProps {
  coverage?: {
    hasCoverage?: boolean;
    coverageState?: string;
    matchesAnalyzed?: number;
    totalSequences?: number;
  } | null;
  compact?: boolean;
}

const SequenceCoverageBadge: React.FC<SequenceCoverageBadgeProps> = ({ coverage, compact = false }) => {
  if (!coverage) {
    return null;
  }

  const hasCoverage = coverage.hasCoverage === true;
  const containerClassName = hasCoverage
    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
    : 'border-slate-600 bg-slate-700/60 text-slate-300';
  const label = hasCoverage ? 'Sequence Ready' : 'Profile Only';
  const detail = hasCoverage
    ? `${coverage.matchesAnalyzed || 0} matches • ${coverage.totalSequences || 0} sequences`
    : 'No live sequence coverage';

  return (
    <div className={`rounded-lg border px-2.5 py-1.5 ${containerClassName}`}>
      <div className="text-xs font-semibold uppercase tracking-wide">{label}</div>
      {!compact && (
        <div className="mt-0.5 text-[11px] opacity-90">{detail}</div>
      )}
    </div>
  );
};

export default SequenceCoverageBadge;