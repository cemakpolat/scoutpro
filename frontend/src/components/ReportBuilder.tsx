import React, { useEffect, useMemo, useState } from 'react';
import {
  FileText,
  Download,
  BookTemplate as Template,
  Wand2,
  BarChart3,
  Users,
  Target,
  TrendingUp,
  Eye,
  Loader2,
  CheckCircle,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import { buildMatchCatalog, filterMatchCatalog, formatMatchLabel, getAvailableLeagues, getAvailableYears } from '../utils/matchFilters';

type TemplateConfig = {
  id: 'player-analysis' | 'team-tactical' | 'market-intelligence' | 'match-analysis';
  name: string;
  description: string;
  sections: string[];
  icon: React.ComponentType<{ className?: string }>;
  backendMode: 'direct' | 'queued';
};

const templates: TemplateConfig[] = [
  {
    id: 'player-analysis',
    name: 'Player Analysis',
    description: 'Comprehensive individual player evaluation',
    sections: ['Performance Metrics', 'Strengths & Weaknesses', 'Market Value', 'Recommendations'],
    icon: Users,
    backendMode: 'direct',
  },
  {
    id: 'team-tactical',
    name: 'Team Tactical Report',
    description: 'In-depth tactical analysis of team performance',
    sections: ['Formation Analysis', 'Playing Style', 'Key Players', 'Tactical Recommendations'],
    icon: Target,
    backendMode: 'direct',
  },
  {
    id: 'market-intelligence',
    name: 'Market Intelligence',
    description: 'Transfer market insights and valuations',
    sections: ['Market Trends', 'Player Valuations', 'Transfer Predictions', 'Investment Opportunities'],
    icon: TrendingUp,
    backendMode: 'queued',
  },
  {
    id: 'match-analysis',
    name: 'Match Analysis',
    description: 'Detailed post-match performance breakdown',
    sections: ['Key Events', 'Player Ratings', 'Tactical Analysis', 'Performance Insights'],
    icon: BarChart3,
    backendMode: 'direct',
  },
];

const buildDefaultTitle = (templateId: TemplateConfig['id']) => {
  const template = templates.find((item) => item.id === templateId);
  return template ? `${template.name} Report` : 'ScoutPro Report';
};

const downloadBlob = (blob: Blob, fileName: string) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
};

const formatDateTime = (value?: string) => {
  if (!value) return 'Pending';

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

const ReportBuilder: React.FC = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateConfig['id']>('player-analysis');
  const [reportTitle, setReportTitle] = useState(buildDefaultTitle('player-analysis'));
  const [targetPlayerId, setTargetPlayerId] = useState('');
  const [targetTeamId, setTargetTeamId] = useState('');
  const [targetMatchId, setTargetMatchId] = useState('');
  const [selectedMatchYear, setSelectedMatchYear] = useState('all');
  const [selectedMatchLeague, setSelectedMatchLeague] = useState('all');
  const [timePeriod, setTimePeriod] = useState('Current Season');
  const [comparisonPlayers, setComparisonPlayers] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [generatedMessage, setGeneratedMessage] = useState('');

  const { players, teams, matches } = useData();
  const { data: reportList, refetch: refetchReports } = useApi(
    () => apiService.listReports(), []
  );

  const selectedTemplateConfig = templates.find((template) => template.id === selectedTemplate) || templates[0];
  const comparisonOptions = players.slice(0, 6);
  const recentReports = (reportList || []).slice(0, 5);
  const processingReports = recentReports.filter((report: any) => report.status && report.status !== 'completed');
  const reportMatchCatalog = useMemo(() => buildMatchCatalog(matches), [matches]);
  const availableMatchYears = useMemo(() => getAvailableYears(reportMatchCatalog), [reportMatchCatalog]);
  const availableMatchLeagues = useMemo(
    () => getAvailableLeagues(reportMatchCatalog, selectedMatchYear),
    [reportMatchCatalog, selectedMatchYear],
  );
  const filteredReportMatches = useMemo(
    () => filterMatchCatalog(reportMatchCatalog, { year: selectedMatchYear, league: selectedMatchLeague }).map((entry) => entry.source),
    [reportMatchCatalog, selectedMatchYear, selectedMatchLeague],
  );

  const selectedPlayer = players.find((player: any) => String(player.id) === String(targetPlayerId));
  const selectedTeam = teams.find((team: any) => String(team.id) === String(targetTeamId));
  const selectedMatch = filteredReportMatches.find((match: any) => String(match.id) === String(targetMatchId));

  useEffect(() => {
    if (selectedMatchYear !== 'all' && !availableMatchYears.includes(selectedMatchYear)) {
      setSelectedMatchYear('all');
    }
  }, [availableMatchYears, selectedMatchYear]);

  useEffect(() => {
    if (selectedMatchLeague !== 'all' && !availableMatchLeagues.includes(selectedMatchLeague)) {
      setSelectedMatchLeague('all');
    }
  }, [availableMatchLeagues, selectedMatchLeague]);

  useEffect(() => {
    if (selectedTemplate !== 'match-analysis') {
      return;
    }

    if (!targetMatchId && filteredReportMatches.length > 0) {
      setTargetMatchId(String(filteredReportMatches[0].id));
      return;
    }

    if (targetMatchId && !filteredReportMatches.some((match: any) => String(match.id) === String(targetMatchId))) {
      setTargetMatchId(filteredReportMatches.length > 0 ? String(filteredReportMatches[0].id) : '');
    }
  }, [filteredReportMatches, selectedTemplate, targetMatchId]);

  const reportRequest = useMemo(() => {
    switch (selectedTemplate) {
      case 'player-analysis':
        return {
          type: 'player',
          entityId: String(targetPlayerId || players[0]?.id || ''),
          entityLabel: selectedPlayer ? selectedPlayer.name : (players[0]?.name || 'No player selected'),
        };
      case 'team-tactical':
        return {
          type: 'team',
          entityId: String(targetTeamId || teams[0]?.id || ''),
          entityLabel: selectedTeam ? selectedTeam.name : (teams[0]?.name || 'No team selected'),
        };
      case 'match-analysis':
        return {
          type: 'match',
          entityId: String(targetMatchId || filteredReportMatches[0]?.id || ''),
          entityLabel: selectedMatch
            ? `${selectedMatch.homeTeam} vs ${selectedMatch.awayTeam}`
            : (filteredReportMatches[0] ? `${filteredReportMatches[0].homeTeam} vs ${filteredReportMatches[0].awayTeam}` : 'No match selected'),
        };
      default:
        return {
          type: 'market',
          entityId: 'overview',
          entityLabel: 'Global market overview',
        };
    }
  }, [selectedTemplate, targetPlayerId, targetTeamId, targetMatchId, players, teams, filteredReportMatches, selectedPlayer, selectedTeam, selectedMatch]);

  useEffect(() => {
    if (processingReports.length === 0) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      refetchReports();
    }, 2500);

    return () => window.clearInterval(intervalId);
  }, [processingReports.length, refetchReports]);

  const handleTemplateChange = (templateId: TemplateConfig['id']) => {
    setSelectedTemplate(templateId);
    setReportTitle(buildDefaultTitle(templateId));
    setGeneratedMessage('');
  };

  const handleDownloadRecent = async (reportId: string) => {
    try {
      const blob = await apiService.downloadReport(reportId);
      downloadBlob(blob, `report-${reportId}.pdf`);
    } catch (error) {
      console.error('Download report error:', error);
      setGeneratedMessage('Could not download the selected backend report.');
    }
  };

  const handleQueueReport = async () => {
    if (!reportRequest.entityId) {
      setGeneratedMessage('Select a valid entity before queuing a report.');
      return;
    }

    setGenerating(true);
    setGeneratedMessage('');

    try {
      const response = await apiService.generateAsyncReport(reportRequest.type, reportRequest.entityId, 'pdf', {
        title: reportTitle,
        template: selectedTemplate,
        entity_label: reportRequest.entityLabel,
        time_period: timePeriod,
        comparison_players: comparisonPlayers,
      });
      if (response.success && response.data?.job_id) {
        setGeneratedMessage(`Backend report job ${response.data.job_id} started for ${reportRequest.entityLabel}.`);
        refetchReports();
        return;
      }

      setGeneratedMessage('Backend report job could not be created.');
    } catch (error) {
      console.error('Queue report error:', error);
      setGeneratedMessage('Backend report job failed to start.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteRecent = async (reportId: string) => {
    try {
      const response = await apiService.deleteReport(reportId);
      if (!response.success) {
        throw new Error(response.error.message);
      }

      setGeneratedMessage(`Deleted backend report ${reportId}.`);
      await refetchReports();
    } catch (error) {
      console.error('Delete report error:', error);
      setGeneratedMessage('Could not delete the selected backend report.');
    }
  };

  const handleExport = async () => {
    if (!reportRequest.entityId) {
      setGeneratedMessage('Select a valid entity before exporting.');
      return;
    }

    setGenerating(true);
    setGeneratedMessage('');

    try {
      if (selectedTemplate === 'market-intelligence') {
        await handleQueueReport();
        return;
      }

      let blob: Blob;
      if (selectedTemplate === 'player-analysis') {
        blob = await apiService.generatePlayerReport(reportRequest.entityId);
      } else if (selectedTemplate === 'team-tactical') {
        blob = await apiService.generateTeamReport(reportRequest.entityId);
      } else {
        blob = await apiService.generateMatchReport(reportRequest.entityId);
      }

      downloadBlob(blob, `${reportTitle.replace(/\s+/g, '_')}_${Date.now()}.pdf`);
      setGeneratedMessage(`PDF downloaded for ${reportRequest.entityLabel}.`);
    } catch (error) {
      console.error('Export report error:', error);
      setGeneratedMessage('Export failed.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <FileText className="h-8 w-8 mr-3 text-green-500" />
          Report Builder
        </h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={handleQueueReport}
            disabled={generating}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 rounded-lg transition-colors"
          >
            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
            <span>Queue Backend Job</span>
          </button>
          <button
            onClick={handleExport}
            disabled={generating}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 rounded-lg transition-colors"
          >
            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            <span>{selectedTemplateConfig.backendMode === 'direct' ? 'Download PDF' : 'Queue PDF'}</span>
          </button>
        </div>
      </div>

      {generatedMessage && (
        <div className="flex items-center gap-2 text-sm p-3 bg-slate-800 rounded-lg border border-slate-700">
          <CheckCircle className="h-4 w-4 text-green-400" />
          <span className="text-green-300">{generatedMessage}</span>
        </div>
      )}

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Template className="h-6 w-6 mr-2 text-blue-400" />
          Choose Report Template
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {templates.map((template) => {
            const Icon = template.icon;
            return (
              <div
                key={template.id}
                onClick={() => handleTemplateChange(template.id)}
                className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedTemplate === template.id
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-slate-700 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <Icon className={`h-8 w-8 ${selectedTemplate === template.id ? 'text-blue-400' : 'text-slate-400'}`} />
                  <span className={`px-2 py-1 text-xs rounded ${template.backendMode === 'direct' ? 'bg-green-600 text-green-100' : 'bg-yellow-600 text-yellow-100'}`}>
                    {template.backendMode === 'direct' ? 'Direct PDF' : 'Queued Job'}
                  </span>
                </div>
                <h4 className="font-semibold mb-2">{template.name}</h4>
                <p className="text-sm text-slate-400 mb-4">{template.description}</p>
                <div className="space-y-1">
                  {template.sections.map((section, index) => (
                    <div key={index} className="text-xs text-slate-500">
                      • {section}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Report Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Report Title</label>
                <input
                  type="text"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {selectedTemplate === 'player-analysis' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Target Player</label>
                  <select
                    value={targetPlayerId}
                    onChange={(e) => setTargetPlayerId(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                  >
                    <option value="">Select a player...</option>
                    {players.map((player: any) => (
                      <option key={player.id} value={player.id}>{player.name} - {player.club}</option>
                    ))}
                  </select>
                </div>
              )}

              {selectedTemplate === 'team-tactical' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Target Team</label>
                  <select
                    value={targetTeamId}
                    onChange={(e) => setTargetTeamId(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                  >
                    <option value="">Select a team...</option>
                    {teams.map((team: any) => (
                      <option key={team.id} value={team.id}>{team.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {selectedTemplate === 'match-analysis' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Match Filters</label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                    <select
                      value={selectedMatchYear}
                      onChange={(e) => setSelectedMatchYear(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                    >
                      <option value="all">All Years</option>
                      {availableMatchYears.map((year) => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                    <select
                      value={selectedMatchLeague}
                      onChange={(e) => setSelectedMatchLeague(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                    >
                      <option value="all">All Leagues</option>
                      {availableMatchLeagues.map((league) => (
                        <option key={league} value={league}>{league}</option>
                      ))}
                    </select>
                  </div>
                  <label className="block text-sm font-medium mb-2">Target Match</label>
                  <select
                    value={targetMatchId}
                    onChange={(e) => setTargetMatchId(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                  >
                    <option value="">Select a match...</option>
                    {filteredReportMatches.map((match: any) => (
                      <option key={match.id} value={match.id}>{formatMatchLabel(match)}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">Time Period</label>
                <select
                  value={timePeriod}
                  onChange={(e) => setTimePeriod(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
                >
                  <option>Current Season</option>
                  <option>Last 6 Months</option>
                  <option>Last 12 Months</option>
                  <option>Career Overview</option>
                </select>
              </div>

              {selectedTemplate === 'player-analysis' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Comparison Players</label>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {comparisonOptions.map((player: any) => (
                      <label key={player.id} className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={comparisonPlayers.includes(String(player.id))}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setComparisonPlayers([...comparisonPlayers, String(player.id)]);
                            } else {
                              setComparisonPlayers(comparisonPlayers.filter((value) => value !== String(player.id)));
                            }
                          }}
                          className="rounded"
                        />
                        <span>{player.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Backend Narrative Scope</h3>
            <div className="space-y-3 text-sm text-slate-300">
              <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
                <div className="text-slate-400 mb-1">Template</div>
                <div className="font-medium">{selectedTemplateConfig.name}</div>
              </div>
              <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
                <div className="text-slate-400 mb-1">Target</div>
                <div className="font-medium">{reportRequest.entityLabel}</div>
              </div>
              <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
                <div className="text-slate-400 mb-1">Time Period</div>
                <div className="font-medium">{timePeriod}</div>
              </div>
              {comparisonPlayers.length > 0 && (
                <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
                  <div className="text-slate-400 mb-1">Comparison Inputs</div>
                  <div className="font-medium">
                    {comparisonPlayers
                      .map((playerId) => players.find((player: any) => String(player.id) === playerId)?.name)
                      .filter(Boolean)
                      .join(', ')}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-slate-800 rounded-xl p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold">Report Preview</h3>
              <div className="flex items-center space-x-2 text-sm text-slate-400">
                <Eye className="h-5 w-5" />
                <span>Backend-aligned outline</span>
              </div>
            </div>

            <div className="border-b border-slate-700 pb-6">
              <h1 className="text-2xl font-bold mb-2">{reportTitle}</h1>
              <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
                <span>Generated: {new Date().toLocaleDateString()}</span>
                <span>Target: {reportRequest.entityLabel}</span>
                <span>Period: {timePeriod}</span>
              </div>
            </div>

            <div className="space-y-4">
              {selectedTemplateConfig.sections.map((section) => (
                <div key={section} className="border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">{section}</h4>
                    <span className="px-2 py-1 rounded text-xs bg-green-600/20 text-green-300 border border-green-600/30">
                      Included
                    </span>
                  </div>
                  <p className="text-sm text-slate-400">
                    This section will be assembled from the active backend data sources for {reportRequest.entityLabel.toLowerCase()}.
                  </p>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-700 pt-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-400" />
                  Recent Backend Reports
                </h4>
                <button
                  onClick={() => refetchReports()}
                  className="flex items-center gap-2 rounded-lg bg-slate-700 px-3 py-2 text-sm hover:bg-slate-600 transition-colors"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </button>
              </div>

              <div className="space-y-3">
                {recentReports.length > 0 ? recentReports.map((report: any) => (
                  <div key={report.id} className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-900/40 px-4 py-3">
                    <div>
                      <div className="font-medium">{report.title || `${report.type || 'general'} report`}</div>
                      <div className="text-sm text-slate-400">
                        {(report.entity_label || report.entity_id || 'Unknown target')} • {formatDateTime(report.completedAt || report.createdAt)}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`rounded px-2 py-1 text-xs ${report.status === 'completed' ? 'bg-green-600/20 text-green-300 border border-green-600/30' : 'bg-yellow-600/20 text-yellow-200 border border-yellow-600/30'}`}>
                        {report.status || 'processing'}
                      </span>
                      <button
                        onClick={() => handleDownloadRecent(report.id)}
                        disabled={report.status !== 'completed'}
                        className="rounded-lg bg-blue-600 px-3 py-2 text-sm hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-400 transition-colors"
                      >
                        Download
                      </button>
                      <button
                        onClick={() => handleDeleteRecent(report.id)}
                        className="rounded-lg bg-slate-700 px-3 py-2 text-sm hover:bg-slate-600 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                )) : (
                  <div className="rounded-lg border border-slate-700 bg-slate-900/40 px-4 py-8 text-center text-slate-400">
                    No backend reports have been generated yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportBuilder;