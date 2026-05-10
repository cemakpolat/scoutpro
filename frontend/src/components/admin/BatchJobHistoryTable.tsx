import React, { useState, useEffect, useCallback } from 'react';

interface BatchJob {
  job_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  records_processed?: number;
  records_failed?: number;
  error_message?: string;
  retry_of?: string;
  request?: {
    provider: string;
    resource_type: string;
    start_date: string;
    end_date: string;
    competition_id?: string;
    season_id?: string;
  };
}

const STATUS_CONFIG: Record<string, { label: string; badge: string; dot: string }> = {
  pending:     { label: 'Pending',   badge: 'bg-yellow-100 text-yellow-800', dot: 'bg-yellow-400' },
  in_progress: { label: 'Running',   badge: 'bg-blue-100 text-blue-800',     dot: 'bg-blue-500 animate-pulse' },
  completed:   { label: 'Completed', badge: 'bg-green-100 text-green-800',   dot: 'bg-green-500' },
  failed:      { label: 'Failed',    badge: 'bg-red-100 text-red-800',       dot: 'bg-red-500' },
  cancelled:   { label: 'Cancelled', badge: 'bg-gray-100 text-gray-500',     dot: 'bg-gray-400' },
};

const PROVIDER_BADGE: Record<string, string> = {
  opta:      'bg-purple-100 text-purple-700',
  statsbomb: 'bg-blue-100 text-blue-700',
  custom:    'bg-gray-100 text-gray-600',
};

function formatDate(iso?: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function formatDuration(start?: string | null, end?: string | null) {
  if (!start || !end) return null;
  const secs = Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000);
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

interface Props {
  refreshKey?: number;
  onStatsUpdate?: (stats: { total: number; running: number; completed: number; failed: number }) => void;
}

export const BatchJobHistoryTable = ({ refreshKey = 0, onStatsUpdate }: Props) => {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch('/api/v2/batch-jobs');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list: BatchJob[] = Array.isArray(data) ? data : (data.jobs || []);
      setJobs(list);
      setError('');
      onStatsUpdate?.({
        total: list.length,
        running: list.filter(j => j.status === 'in_progress' || j.status === 'pending').length,
        completed: list.filter(j => j.status === 'completed').length,
        failed: list.filter(j => j.status === 'failed').length,
      });
    } catch (err: any) {
      setError('Could not load jobs — is the batch-data-manager service running?');
    } finally {
      setLoading(false);
    }
  }, [onStatsUpdate]);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [fetchJobs, refreshKey]);

  const doAction = async (jobId: string, action: 'cancel' | 'retry') => {
    setActionLoading(jobId);
    try {
      const res = await fetch(`/api/v2/batch-jobs/${jobId}/${action}`, { method: 'POST' });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `${action} failed`);
      }
      await fetchJobs();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = jobs.filter(job => {
    if (statusFilter !== 'all' && job.status !== statusFilter) return false;
    if (providerFilter !== 'all' && job.request?.provider !== providerFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        job.job_id.toLowerCase().includes(q) ||
        job.request?.provider?.toLowerCase().includes(q) ||
        job.request?.resource_type?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const hasActiveJobs = jobs.some(j => j.status === 'pending' || j.status === 'in_progress');

  return (
    <div className="bg-white rounded-lg border border-gray-200 flex flex-col">
      {/* Toolbar */}
      <div className="px-5 py-3.5 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center gap-3">
        <h2 className="text-sm font-semibold text-gray-900 flex-1">
          Job History
          {hasActiveJobs && (
            <span className="ml-2 inline-block h-2 w-2 rounded-full bg-blue-500 animate-pulse" title="Jobs running" />
          )}
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 w-32"
          />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="all">All statuses</option>
            <option value="pending">Pending</option>
            <option value="in_progress">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            value={providerFilter}
            onChange={e => setProviderFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="all">All providers</option>
            <option value="opta">Opta</option>
            <option value="statsbomb">StatsBomb</option>
            <option value="custom">Custom</option>
          </select>
          <button
            onClick={fetchJobs}
            title="Refresh"
            className="text-gray-500 hover:text-gray-800 border border-gray-300 rounded-md p-1.5 hover:bg-gray-50 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {error && (
        <div className="px-5 py-3 bg-red-50 border-b border-red-100 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <div className="p-10 flex flex-col items-center gap-3 text-gray-400">
          <div className="animate-spin h-6 w-6 border-2 border-indigo-400 border-t-transparent rounded-full" />
          <span className="text-sm">Loading jobs...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-10 text-center text-gray-400 text-sm">
          {jobs.length === 0
            ? 'No ingestion jobs yet. Create one using the form.'
            : 'No jobs match the current filters.'}
        </div>
      ) : (
        <ul className="divide-y divide-gray-100">
          {filtered.map(job => {
            const cfg = STATUS_CONFIG[job.status] || STATUS_CONFIG.pending;
            const isExpanded = expandedJob === job.job_id;
            const isActioning = actionLoading === job.job_id;
            const duration = formatDuration(job.started_at, job.completed_at);
            const canCancel = job.status === 'pending' || job.status === 'in_progress';
            const canRetry = job.status === 'failed' || job.status === 'cancelled';

            return (
              <li key={job.job_id} className="hover:bg-gray-50 transition-colors">
                {/* Main row */}
                <button
                  className="w-full text-left px-5 py-4 focus:outline-none"
                  onClick={() => setExpandedJob(isExpanded ? null : job.job_id)}
                >
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className={`h-2 w-2 rounded-full shrink-0 ${cfg.dot}`} />
                    <span className="text-sm font-mono font-medium text-gray-900">{job.job_id}</span>

                    {job.request?.provider && (
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full uppercase tracking-wide ${PROVIDER_BADGE[job.request.provider] || 'bg-gray-100 text-gray-600'}`}>
                        {job.request.provider}
                      </span>
                    )}
                    {job.request?.resource_type && (
                      <span className="text-xs text-gray-500 capitalize">
                        {job.request.resource_type.replace('_', ' ')}
                      </span>
                    )}
                    {job.retry_of && (
                      <span className="text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">retry</span>
                    )}

                    <span className={`ml-auto px-2.5 py-0.5 text-xs font-semibold rounded-full ${cfg.badge}`}>
                      {cfg.label}
                    </span>
                    <svg
                      className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>

                  {/* Progress bar */}
                  {job.status === 'in_progress' && job.progress != null && (
                    <div className="mt-2.5 flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-blue-500 h-1.5 rounded-full transition-all duration-700"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 shrink-0 tabular-nums">{job.progress}%</span>
                    </div>
                  )}

                  {/* Quick info */}
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-0.5 text-xs text-gray-400">
                    {job.request?.start_date && job.request?.end_date && (
                      <span>{job.request.start_date} → {job.request.end_date}</span>
                    )}
                    <span>Created {formatDate(job.created_at)}</span>
                    {duration && <span>Duration: {duration}</span>}
                    {job.records_processed != null && (
                      <span className="text-green-600 font-medium">{job.records_processed.toLocaleString()} records</span>
                    )}
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-5 pb-4 border-t border-gray-100 bg-gray-50">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-3 text-sm">
                      {[
                        { label: 'Competition', value: job.request?.competition_id || '—' },
                        { label: 'Season', value: job.request?.season_id || '—' },
                        { label: 'Started', value: formatDate(job.started_at) },
                        { label: 'Finished', value: formatDate(job.completed_at) },
                      ].map(item => (
                        <div key={item.label}>
                          <p className="text-xs text-gray-400 uppercase tracking-wide">{item.label}</p>
                          <p className="text-gray-900 mt-0.5 font-medium">{item.value}</p>
                        </div>
                      ))}
                      {job.records_failed != null && (
                        <div>
                          <p className="text-xs text-gray-400 uppercase tracking-wide">Failed Records</p>
                          <p className={`mt-0.5 font-medium ${job.records_failed > 0 ? 'text-red-600' : 'text-gray-900'}`}>
                            {job.records_failed}
                          </p>
                        </div>
                      )}
                      {job.retry_of && (
                        <div>
                          <p className="text-xs text-gray-400 uppercase tracking-wide">Retry Of</p>
                          <p className="text-gray-700 mt-0.5 font-mono text-xs">{job.retry_of}</p>
                        </div>
                      )}
                    </div>

                    {job.error_message && (
                      <div className="mt-1 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 font-mono whitespace-pre-wrap">
                        {job.error_message}
                      </div>
                    )}

                    <div className="mt-3 flex gap-2">
                      {canRetry && (
                        <button
                          onClick={() => doAction(job.job_id, 'retry')}
                          disabled={isActioning}
                          className="px-3 py-1.5 text-xs font-medium bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                        >
                          {isActioning ? 'Retrying...' : '↺ Retry Job'}
                        </button>
                      )}
                      {canCancel && (
                        <button
                          onClick={() => doAction(job.job_id, 'cancel')}
                          disabled={isActioning}
                          className="px-3 py-1.5 text-xs font-medium border border-red-300 text-red-600 rounded-md hover:bg-red-50 disabled:opacity-50 transition-colors"
                        >
                          {isActioning ? 'Cancelling...' : '✕ Cancel'}
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {!loading && filtered.length > 0 && (
        <div className="px-5 py-2.5 border-t border-gray-100 text-xs text-gray-400">
          Showing {filtered.length} of {jobs.length} job{jobs.length !== 1 ? 's' : ''} · Auto-refreshes every 5s
        </div>
      )}
    </div>
  );
};
