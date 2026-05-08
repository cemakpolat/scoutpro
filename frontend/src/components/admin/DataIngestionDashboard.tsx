import React, { useState } from 'react';
import { BatchJobHistoryTable } from './BatchJobHistoryTable';

export const DataIngestionDashboard = () => {
  const [provider, setProvider] = useState('opta');
  const [resourceType, setResourceType] = useState('match');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const handleTriggerJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Generate unique idempotency token to prevent duplicate runs
      const idempotencyToken = `job_${provider}_${resourceType}_${Date.now()}`;
      
      const response = await fetch('/api/v2/batch-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider,
          resource_type: resourceType,
          start_date: startDate,
          end_date: endDate,
          idempotency_token: idempotencyToken,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger job: ${response.statusText}`);
      }

      const data = await response.json();
      setSuccess(`Job created: ${data.job_id || 'Job queued successfully'}`);
      // Reset form
      setStartDate('');
      setEndDate('');
    } catch (err: any) {
      setError(err.message || 'Failed to trigger batch job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Data Ingestion Manager</h1>
        <p className="text-gray-500">Orchestrate historical and batch data jobs across multiple providers.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Submission Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Trigger New Batch Import</h2>
          </div>
          <div className="p-6">
            <form onSubmit={handleTriggerJob} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
                  {error}
                </div>
              )}
              {success && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-700">
                  {success}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700">Data Provider</label>
                <select 
                  value={provider} 
                  onChange={e => setProvider(e.target.value)}
                  disabled={loading}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="opta">Opta (Primary)</option>
                  <option value="statsbomb">StatsBomb</option>
                  <option value="custom">Custom CSV</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Resource Type</label>
                <select 
                  value={resourceType} 
                  onChange={e => setResourceType(e.target.value)}
                  disabled={loading}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="match">Matches & Events</option>
                  <option value="player">Player Metadata</option>
                  <option value="team">Team Squads</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Start Date</label>
                  <input 
                    type="date" 
                    value={startDate} 
                    onChange={e => setStartDate(e.target.value)}
                    disabled={loading}
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">End Date</label>
                  <input 
                    type="date" 
                    value={endDate} 
                    onChange={e => setEndDate(e.target.value)}
                    disabled={loading}
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" 
                  />
                </div>
              </div>

              <div className="pt-4">
                <button 
                  type="submit" 
                  disabled={loading}
                  className="w-full inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Queueing...' : 'Queue Ingestion Job'}
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Ingestion Rules & Warnings</h2>
          </div>
          <div className="p-6 space-y-4 text-sm text-gray-600">
            <p><strong>Idempotent Operations:</strong> Data imports are destructive-upserts based on the provider ID metric. Importing a historical season twice will not duplicate items, but it <em>will</em> consume substantial compute.</p>
            <p><strong>Data Freshness:</strong> Bulk data imported through this pipeline will automatically be tagged with the <code>HISTORICAL</code> freshness parameter in the ScoutPro DataContext.</p>
            <p><strong>Live Interruption:</strong> Batch jobs use a secondary Kafka topology. The live ingestion topics are entirely walled-off; a large multi-season import here will NEVER block a live match tick.</p>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-bold tracking-tight text-gray-900 mb-4">Active & Historical Jobs</h2>
        <BatchJobHistoryTable />
      </div>
    </div>
  );
};
