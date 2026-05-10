import React, { useState, useCallback } from 'react';
import { BatchJobHistoryTable } from './BatchJobHistoryTable';
import { ProviderCredentialsPanel } from './ProviderCredentialsPanel';

const PROVIDERS = [
  { value: 'opta', label: 'Opta', description: 'Primary event data (F1/F24/F40)' },
  { value: 'statsbomb', label: 'StatsBomb', description: 'Open & commercial datasets' },
  { value: 'custom', label: 'Custom CSV', description: 'Manual file-based import' },
] as const;

const RESOURCE_TYPES = [
  { value: 'match', label: 'Matches & Events', hint: 'Full match event timelines (F24)' },
  { value: 'player', label: 'Player Metadata', hint: 'Player profiles & bio data (F40)' },
  { value: 'team', label: 'Team Squads', hint: 'Squad composition & rosters (F1)' },
] as const;

interface JobStats {
  total: number;
  running: number;
  completed: number;
  failed: number;
}

export const DataIngestionDashboard = () => {
  const [activeTab, setActiveTab] = useState<'jobs' | 'credentials'>('jobs');
  const [provider, setProvider] = useState('opta');
  const [resourceType, setResourceType] = useState('match');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [competitionId, setCompetitionId] = useState('');
  const [seasonId, setSeasonId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [jobStats, setJobStats] = useState<JobStats>({ total: 0, running: 0, completed: 0, failed: 0 });
  const [refreshKey, setRefreshKey] = useState(0);

  const handleStatsUpdate = useCallback((stats: JobStats) => {
    setJobStats(stats);
  }, []);

  const handleTriggerJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const idempotencyToken = `job_${provider}_${resourceType}_${Date.now()}`;

      const response = await fetch('/api/v2/batch-jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          resource_type: resourceType,
          start_date: startDate,
          end_date: endDate,
          competition_id: competitionId || undefined,
          season_id: seasonId || undefined,
          idempotency_token: idempotencyToken,
        }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.error || `Request failed: ${response.statusText}`);

      setSuccess(`Job ${data.job_id} queued successfully`);
      setStartDate('');
      setEndDate('');
      setCompetitionId('');
      setSeasonId('');
      setRefreshKey(k => k + 1);
    } catch (err: any) {
      setError(err.message || 'Failed to trigger batch job');
    } finally {
      setLoading(false);
    }
  };

  const successRate = jobStats.total > 0 ? Math.round((jobStats.completed / jobStats.total) * 100) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Batch Data Manager</h1>
          <p className="text-sm text-gray-500 mt-0.5">Orchestrate historical and bulk data ingestion across providers</p>
        </div>
        <div className="flex gap-2">
          {(['jobs', 'credentials'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors capitalize ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {tab === 'jobs' ? 'Ingestion Jobs' : 'Provider Config'}
            </button>
          ))}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Jobs', value: jobStats.total, color: 'text-gray-900' },
          { label: 'Running', value: jobStats.running, color: 'text-blue-600' },
          { label: 'Completed', value: jobStats.completed, color: 'text-green-600' },
          { label: 'Failed', value: jobStats.failed, color: 'text-red-600' },
        ].map(stat => (
          <div key={stat.label} className="bg-white rounded-lg border border-gray-200 px-4 py-3">
            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">{stat.label}</p>
            <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
            {stat.label === 'Completed' && successRate !== null && (
              <p className="text-xs text-gray-400 mt-0.5">{successRate}% success rate</p>
            )}
          </div>
        ))}
      </div>

      {activeTab === 'jobs' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Form panel */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="px-5 py-4 border-b border-gray-200">
                <h2 className="text-sm font-semibold text-gray-900">New Ingestion Job</h2>
              </div>
              <div className="p-5">
                <form onSubmit={handleTriggerJob} className="space-y-5">
                  {error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex gap-2">
                      <span className="shrink-0 mt-0.5">⚠</span>
                      <span>{error}</span>
                    </div>
                  )}
                  {success && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-700 flex gap-2">
                      <span className="shrink-0 mt-0.5">✓</span>
                      <span>{success}</span>
                    </div>
                  )}

                  {/* Provider selection */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Data Provider
                    </label>
                    <div className="space-y-2">
                      {PROVIDERS.map(p => (
                        <label
                          key={p.value}
                          className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                            provider === p.value
                              ? 'border-indigo-500 bg-indigo-50'
                              : 'border-gray-200 hover:border-gray-300 bg-white'
                          } ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
                        >
                          <input
                            type="radio"
                            name="provider"
                            value={p.value}
                            checked={provider === p.value}
                            onChange={e => setProvider(e.target.value)}
                            disabled={loading}
                            className="mt-0.5 text-indigo-600"
                          />
                          <div>
                            <p className="text-sm font-medium text-gray-900 leading-none">{p.label}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{p.description}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Resource type */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                      Resource Type
                    </label>
                    <select
                      value={resourceType}
                      onChange={e => setResourceType(e.target.value)}
                      disabled={loading}
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                    >
                      {RESOURCE_TYPES.map(r => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-400">
                      {RESOURCE_TYPES.find(r => r.value === resourceType)?.hint}
                    </p>
                  </div>

                  {/* Date range */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                      Date Range
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">From</label>
                        <input
                          type="date"
                          value={startDate}
                          onChange={e => setStartDate(e.target.value)}
                          disabled={loading}
                          required
                          max={endDate || undefined}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">To</label>
                        <input
                          type="date"
                          value={endDate}
                          onChange={e => setEndDate(e.target.value)}
                          disabled={loading}
                          required
                          min={startDate || undefined}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Optional filters */}
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                      Filters <span className="font-normal normal-case">(optional)</span>
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Competition ID</label>
                        <input
                          type="text"
                          placeholder="e.g. 115"
                          value={competitionId}
                          onChange={e => setCompetitionId(e.target.value)}
                          disabled={loading}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Season ID</label>
                        <input
                          type="text"
                          placeholder="e.g. 2023"
                          value={seasonId}
                          onChange={e => setSeasonId(e.target.value)}
                          disabled={loading}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full flex justify-center items-center gap-2 rounded-md bg-indigo-600 py-2.5 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? (
                      <>
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Queueing...
                      </>
                    ) : 'Queue Ingestion Job'}
                  </button>
                </form>
              </div>
            </div>

            {/* Notes */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-xs text-amber-800 space-y-1.5">
              <p className="font-semibold">Important</p>
              <p>Imports are destructive-upserts — re-importing a season won't duplicate records but consumes compute.</p>
              <p>Batch jobs use an isolated Kafka topology and never block live match ingestion.</p>
              <p>Jobs tagged <code className="bg-amber-100 px-1 rounded">HISTORICAL</code> in the DataContext after import.</p>
            </div>
          </div>

          {/* Job history */}
          <div className="lg:col-span-2">
            <BatchJobHistoryTable refreshKey={refreshKey} onStatsUpdate={handleStatsUpdate} />
          </div>
        </div>
      ) : (
        <ProviderCredentialsPanel />
      )}
    </div>
  );
};
