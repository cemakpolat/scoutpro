import React, { useMemo, useState } from 'react';
import {
  Database,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  BarChart3,
  FileText,
  Zap,
} from 'lucide-react';
import apiService from '../services/api';
import { useData } from '../context/DataContext';
import { useApi } from '../hooks/useApi';

const calculateCompleteness = (records: any[], checks: Array<(record: any) => boolean>): number => {
  if (records.length === 0) {
    return 100;
  }

  const totalChecks = records.length * checks.length;
  const passedChecks = records.reduce(
    (sum, record) => sum + checks.filter((check) => check(record)).length,
    0,
  );

  return Math.round((passedChecks / Math.max(totalChecks, 1)) * 100);
};

const getDatasetStatus = (score: number): 'healthy' | 'warning' | 'critical' => {
  if (score >= 90) return 'healthy';
  if (score >= 70) return 'warning';
  return 'critical';
};

const DataManagement: React.FC = () => {
  const [statusMessage, setStatusMessage] = useState('');
  const { players, matches, teams } = useData();
  const { data: overviewData, refetch: refetchOverview } = useApi(
    () => apiService.getDashboardOverview(),
    [],
  );
  const { data: importJobsData, loading: importJobsLoading, refetch: refetchImportJobs } = useApi(
    () => apiService.listImportJobs(),
    [],
  );
  const { data: reportJobsData, refetch: refetchReports } = useApi(
    () => apiService.listReports(),
    [],
  );

  // Ensure these are always arrays
  const importJobs = importJobsData || [];
  const reportJobs = reportJobsData || [];

  const summary = overviewData?.summary || overviewData?.data || {};
  const totalPlayers = summary.totalPlayers || players?.length || 0;
  const totalMatches = summary.totalMatches || matches?.length || 0;
  const totalTeams = summary.totalTeams || teams?.length || 0;

  const playerCompleteness = calculateCompleteness(players || [], [
    (player) => Boolean(player?.name),
    (player) => Boolean(player?.position),
    (player) => Boolean(player?.club || player?.team),
    (player) => player?.age != null,
  ]);

  const matchCompleteness = calculateCompleteness(matches || [], [
    (match) => Boolean(match?.homeTeam || match?.homeTeamId),
    (match) => Boolean(match?.awayTeam || match?.awayTeamId),
    (match) => Boolean(match?.date),
    (match) => match?.status != null,
  ]);

  const teamCompleteness = calculateCompleteness(teams || [], [
    (team) => Boolean(team?.name),
    (team) => Boolean(team?.league),
    (team) => Boolean(team?.country),
  ]);

  const reportCompleteness = calculateCompleteness(reportJobs || [], [
    (report) => Boolean(report?.id || report?._id),
    (report) => Boolean(report?.status),
    (report) => Boolean(report?.createdAt || report?.created_at),
  ]);

  const importCompleteness = calculateCompleteness(importJobs || [], [
    (job) => Boolean(job?.id || job?._id),
    (job) => Boolean(job?.status),
    (job) => Boolean(job?.createdAt || job?.created_at),
  ]);

  const datasets = useMemo(
    () => [
      {
        id: 'player-stats',
        name: 'Player Statistics',
        endpoint: '/api/players',
        records: totalPlayers,
        quality: playerCompleteness,
        completeness: playerCompleteness,
        status: getDatasetStatus(playerCompleteness),
      },
      {
        id: 'match-events',
        name: 'Match Registry',
        endpoint: '/api/matches',
        records: totalMatches,
        quality: matchCompleteness,
        completeness: matchCompleteness,
        status: getDatasetStatus(matchCompleteness),
      },
      {
        id: 'team-data',
        name: 'Team Directory',
        endpoint: '/api/teams',
        records: totalTeams,
        quality: teamCompleteness,
        completeness: teamCompleteness,
        status: getDatasetStatus(teamCompleteness),
      },
      {
        id: 'reports',
        name: 'Generated Reports',
        endpoint: '/api/v2/reports/list',
        records: reportJobs.length,
        quality: reportCompleteness,
        completeness: reportCompleteness,
        status: getDatasetStatus(reportCompleteness),
      },
      {
        id: 'imports',
        name: 'Import Jobs',
        endpoint: '/api/v2/imports/jobs',
        records: importJobs.length,
        quality: importCompleteness,
        completeness: importCompleteness,
        status: getDatasetStatus(importCompleteness),
      },
    ],
    [
      importCompleteness,
      importJobs.length,
      matchCompleteness,
      playerCompleteness,
      reportCompleteness,
      reportJobs.length,
      teamCompleteness,
      totalMatches,
      totalPlayers,
      totalTeams,
    ],
  );

  const totalRecords = datasets.reduce((sum, dataset) => sum + dataset.records, 0);
  const averageCompleteness = datasets.length > 0
    ? Math.round(datasets.reduce((sum, dataset) => sum + dataset.completeness, 0) / datasets.length)
    : 0;
  const activeImportJobs = ((importJobs || []) as any[]).filter((job) => ['pending', 'processing', 'running', 'partial'].includes(String(job?.status || '').toLowerCase())).length;
  const failedImportJobs = ((importJobs || []) as any[]).filter((job) => String(job?.status || '').toLowerCase() === 'failed').length;

  const dataQualityIssues = useMemo(
    () => [
      {
        type: 'Players missing positions',
        count: (players || []).filter((player: any) => !player?.position).length,
        severity: 'medium',
        dataset: 'Player Statistics',
      },
      {
        type: 'Players missing club/team',
        count: (players || []).filter((player: any) => !(player?.club || player?.team)).length,
        severity: 'medium',
        dataset: 'Player Statistics',
      },
      {
        type: 'Matches missing competition',
        count: (matches || []).filter((match: any) => !match?.competition).length,
        severity: 'low',
        dataset: 'Match Registry',
      },
      {
        type: 'Teams missing league or country',
        count: (teams || []).filter((team: any) => !team?.league || !team?.country).length,
        severity: 'medium',
        dataset: 'Team Directory',
      },
      {
        type: 'Failed import jobs',
        count: failedImportJobs,
        severity: failedImportJobs > 0 ? 'high' : 'low',
        dataset: 'Import Jobs',
      },
    ].filter((issue) => issue.count > 0),
    [failedImportJobs, matches, players, teams],
  );

  const pipelineJobs = useMemo(
    () => (importJobs as any[]).slice(0, 6).map((job, index) => ({
      id: job.id || job._id || index,
      name: job.name || job.fileName || job.type || 'Import Job',
      status: String(job.status || 'pending').toLowerCase(),
      progress: job.progress != null
        ? Number(job.progress)
        : String(job.status || '').toLowerCase() === 'completed'
          ? 100
          : String(job.status || '').toLowerCase() === 'failed'
            ? 0
            : 50,
      createdAt: job.createdAt || job.created_at || job.updatedAt || job.updated_at,
    })),
    [importJobs],
  );

  const handleRefresh = async () => {
    setStatusMessage('Refreshing live dataset snapshot...');
    try {
      await Promise.all([refetchOverview(), refetchImportJobs(), refetchReports()]);
      setStatusMessage('Live dataset snapshot refreshed.');
    } catch (error) {
      console.error('Failed to refresh data management snapshot:', error);
      setStatusMessage('Could not refresh the live dataset snapshot.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Database className="h-8 w-8 mr-3 text-blue-500" />
          Data Management
        </h1>
        <button
          onClick={handleRefresh}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Refresh Snapshot</span>
        </button>
      </div>

      {statusMessage && (
        <div className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-300">
          {statusMessage}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{datasets.length}</div>
              <div className="text-slate-400 text-sm">Datasets Online</div>
            </div>
            <Database className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <CheckCircle className="h-4 w-4 mr-1" />
            Endpoint snapshot available
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{totalRecords.toLocaleString()}</div>
              <div className="text-slate-400 text-sm">Total Records</div>
            </div>
            <FileText className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <RefreshCw className="h-4 w-4 mr-1" />
            Live read-model counts
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{averageCompleteness}%</div>
              <div className="text-slate-400 text-sm">Average Completeness</div>
            </div>
            <BarChart3 className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <AlertTriangle className="h-4 w-4 mr-1" />
            Derived from required field coverage
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{activeImportJobs}</div>
              <div className="text-slate-400 text-sm">Active Import Jobs</div>
            </div>
            <Zap className="h-8 w-8 text-purple-400" />
          </div>
          <div className="flex items-center mt-2 text-purple-400 text-sm">
            <Clock className="h-4 w-4 mr-1" />
            {failedImportJobs} failed jobs
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Dataset Coverage</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-2">Dataset</th>
                <th className="text-left py-3 px-2">Endpoint</th>
                <th className="text-left py-3 px-2">Records</th>
                <th className="text-left py-3 px-2">Quality</th>
                <th className="text-left py-3 px-2">Completeness</th>
                <th className="text-left py-3 px-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((dataset) => (
                <tr key={dataset.id} className="border-b border-slate-700 hover:bg-slate-700">
                  <td className="py-3 px-2 font-semibold">{dataset.name}</td>
                  <td className="py-3 px-2 text-sm text-slate-400">{dataset.endpoint}</td>
                  <td className="py-3 px-2">{dataset.records.toLocaleString()}</td>
                  <td className="py-3 px-2 text-green-400">{dataset.quality}%</td>
                  <td className="py-3 px-2 text-blue-400">{dataset.completeness}%</td>
                  <td className="py-3 px-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      dataset.status === 'healthy'
                        ? 'bg-green-600 text-green-100'
                        : dataset.status === 'warning'
                          ? 'bg-yellow-600 text-yellow-100'
                          : 'bg-red-600 text-red-100'
                    }`}>
                      {dataset.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <AlertTriangle className="h-6 w-6 mr-2 text-yellow-400" />
            Data Quality Indicators
          </h3>
          {dataQualityIssues.length > 0 ? (
            <div className="space-y-4">
              {dataQualityIssues.map((issue, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{issue.type}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      issue.severity === 'high'
                        ? 'bg-red-600 text-red-100'
                        : issue.severity === 'medium'
                          ? 'bg-yellow-600 text-yellow-100'
                          : 'bg-green-600 text-green-100'
                    }`}>
                      {issue.severity}
                    </span>
                  </div>
                  <div className="text-sm text-slate-400">{issue.dataset}</div>
                  <div className="mt-2 text-sm text-slate-200">{issue.count} affected records</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
              No missing-field issues were detected in the current backend snapshot.
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Zap className="h-6 w-6 mr-2 text-purple-400" />
            Import Job Status
          </h3>
          {importJobsLoading ? (
            <div className="flex items-center gap-2 text-slate-400 text-sm">
              <RefreshCw className="h-4 w-4 animate-spin" /> Loading import jobs...
            </div>
          ) : pipelineJobs.length > 0 ? (
            <div className="space-y-4">
              {pipelineJobs.map((job) => (
                <div key={job.id} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{job.name}</span>
                    <div className="flex items-center space-x-2">
                      {job.status === 'completed' && <CheckCircle className="h-4 w-4 text-green-400" />}
                      {job.status === 'failed' && <XCircle className="h-4 w-4 text-red-400" />}
                      {job.status !== 'completed' && job.status !== 'failed' && <Clock className="h-4 w-4 text-yellow-400" />}
                      <span className={`text-sm capitalize ${
                        job.status === 'completed'
                          ? 'text-green-400'
                          : job.status === 'failed'
                            ? 'text-red-400'
                            : 'text-yellow-400'
                      }`}>
                        {job.status}
                      </span>
                    </div>
                  </div>
                  <div className="mb-2 w-full rounded-full bg-slate-600 h-2">
                    <div
                      className={`h-2 rounded-full ${
                        job.status === 'completed'
                          ? 'bg-green-400'
                          : job.status === 'failed'
                            ? 'bg-red-400'
                            : 'bg-blue-400'
                      }`}
                      style={{ width: `${Math.max(0, Math.min(100, job.progress))}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-slate-400">Updated: {job.createdAt || 'Unknown'}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
              No import jobs have been created through the backend yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DataManagement;
