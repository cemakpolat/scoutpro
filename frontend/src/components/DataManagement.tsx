import React, { useState } from 'react';
import { Database, Upload, Download, RefreshCw, Filter, Search, CheckCircle, AlertTriangle, XCircle, Clock, BarChart3, FileText, Zap, Settings, Eye, Trash2, CreditCard as Edit, Plus } from 'lucide-react';

const DataManagement: React.FC = () => {
  const [selectedDataset, setSelectedDataset] = useState('player-stats');
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const datasets = [
    {
      id: 'player-stats',
      name: 'Player Statistics',
      size: '2.4GB',
      records: '2,847,392',
      lastUpdated: '2 hours ago',
      status: 'healthy',
      sources: ['Opta', 'StatsBomb', 'Wyscout'],
      quality: 98.2,
      completeness: 94.7
    },
    {
      id: 'match-events',
      name: 'Match Events',
      size: '1.8GB',
      records: '1,234,567',
      lastUpdated: '1 hour ago',
      status: 'healthy',
      sources: ['ChyronHego', 'DataStadium'],
      quality: 96.8,
      completeness: 92.3
    },
    {
      id: 'transfer-data',
      name: 'Transfer Market',
      size: '456MB',
      records: '89,234',
      lastUpdated: '30 minutes ago',
      status: 'warning',
      sources: ['Transfermarkt', 'CIES'],
      quality: 94.1,
      completeness: 87.9
    },
    {
      id: 'injury-data',
      name: 'Injury Records',
      size: '234MB',
      records: '45,678',
      lastUpdated: '6 hours ago',
      status: 'error',
      sources: ['PhysioRoom', 'Club Reports'],
      quality: 89.3,
      completeness: 76.4
    },
    {
      id: 'tactical-data',
      name: 'Tactical Analysis',
      size: '3.1GB',
      records: '567,890',
      lastUpdated: '45 minutes ago',
      status: 'healthy',
      sources: ['InStat', 'Metrica Sports'],
      quality: 97.5,
      completeness: 91.8
    }
  ];

  const dataQualityIssues = [
    { type: 'Missing Values', count: 1247, severity: 'medium', dataset: 'Player Statistics' },
    { type: 'Duplicate Records', count: 89, severity: 'high', dataset: 'Match Events' },
    { type: 'Outliers Detected', count: 234, severity: 'low', dataset: 'Transfer Market' },
    { type: 'Schema Mismatch', count: 12, severity: 'high', dataset: 'Injury Records' },
    { type: 'Encoding Issues', count: 45, severity: 'medium', dataset: 'Tactical Analysis' }
  ];

  const pipelineJobs = [
    { id: 1, name: 'Daily Player Stats Update', status: 'running', progress: 67, eta: '12 min' },
    { id: 2, name: 'Match Events Processing', status: 'completed', progress: 100, eta: 'Completed' },
    { id: 3, name: 'Transfer Data Validation', status: 'failed', progress: 45, eta: 'Failed' },
    { id: 4, name: 'Injury Data Cleaning', status: 'queued', progress: 0, eta: 'Queued' }
  ];

  const simulateUpload = () => {
    setIsProcessing(true);
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          return 100;
        }
        return prev + Math.random() * 15;
      });
    }, 500);
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Database className="h-8 w-8 mr-3 text-blue-500" />
          Data Management
        </h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={simulateUpload}
            disabled={isProcessing}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 rounded-lg transition-colors"
          >
            <Upload className="h-4 w-4" />
            <span>Upload Data</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            <RefreshCw className="h-4 w-4" />
            <span>Sync All</span>
          </button>
        </div>
      </div>

      {/* Data Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">8.1TB</div>
              <div className="text-slate-400 text-sm">Total Data Size</div>
            </div>
            <Database className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <CheckCircle className="h-4 w-4 mr-1" />
            Storage healthy
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">4.7M</div>
              <div className="text-slate-400 text-sm">Total Records</div>
            </div>
            <FileText className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <RefreshCw className="h-4 w-4 mr-1" />
            Updated 2h ago
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">96.4%</div>
              <div className="text-slate-400 text-sm">Data Quality</div>
            </div>
            <BarChart3 className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <AlertTriangle className="h-4 w-4 mr-1" />
            3 issues found
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">12</div>
              <div className="text-slate-400 text-sm">Active Pipelines</div>
            </div>
            <Zap className="h-8 w-8 text-purple-400" />
          </div>
          <div className="flex items-center mt-2 text-purple-400 text-sm">
            <Clock className="h-4 w-4 mr-1" />
            3 running now
          </div>
        </div>
      </div>

      {/* Dataset Management */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Dataset Management</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-2">Dataset</th>
                <th className="text-left py-3 px-2">Size</th>
                <th className="text-left py-3 px-2">Records</th>
                <th className="text-left py-3 px-2">Quality</th>
                <th className="text-left py-3 px-2">Completeness</th>
                <th className="text-left py-3 px-2">Status</th>
                <th className="text-left py-3 px-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((dataset) => (
                <tr key={dataset.id} className="border-b border-slate-700 hover:bg-slate-700">
                  <td className="py-3 px-2">
                    <div>
                      <div className="font-semibold">{dataset.name}</div>
                      <div className="text-xs text-slate-400">
                        Sources: {dataset.sources.join(', ')}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-2">{dataset.size}</td>
                  <td className="py-3 px-2">{dataset.records}</td>
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-slate-600 rounded-full h-2">
                        <div
                          className="bg-green-400 h-2 rounded-full"
                          style={{ width: `${dataset.quality}%` }}
                        ></div>
                      </div>
                      <span className="text-sm">{dataset.quality}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-slate-600 rounded-full h-2">
                        <div
                          className="bg-blue-400 h-2 rounded-full"
                          style={{ width: `${dataset.completeness}%` }}
                        ></div>
                      </div>
                      <span className="text-sm">{dataset.completeness}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      dataset.status === 'healthy' ? 'bg-green-600 text-green-100' :
                      dataset.status === 'warning' ? 'bg-yellow-600 text-yellow-100' :
                      'bg-red-600 text-red-100'
                    }`}>
                      {dataset.status}
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex space-x-2">
                      <button className="p-1 bg-blue-600 hover:bg-blue-700 rounded transition-colors">
                        <Eye className="h-3 w-3" />
                      </button>
                      <button className="p-1 bg-green-600 hover:bg-green-700 rounded transition-colors">
                        <Edit className="h-3 w-3" />
                      </button>
                      <button className="p-1 bg-red-600 hover:bg-red-700 rounded transition-colors">
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Data Quality Issues */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <AlertTriangle className="h-6 w-6 mr-2 text-yellow-400" />
            Data Quality Issues
          </h3>
          <div className="space-y-4">
            {dataQualityIssues.map((issue, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{issue.type}</span>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      issue.severity === 'high' ? 'bg-red-600 text-red-100' :
                      issue.severity === 'medium' ? 'bg-yellow-600 text-yellow-100' :
                      'bg-green-600 text-green-100'
                    }`}>
                      {issue.severity}
                    </span>
                    <span className="text-slate-400">{issue.count} issues</span>
                  </div>
                </div>
                <div className="text-sm text-slate-400">{issue.dataset}</div>
                <button className="mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs transition-colors">
                  Fix Issues
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Pipeline Status */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Zap className="h-6 w-6 mr-2 text-purple-400" />
            Data Pipeline Status
          </h3>
          <div className="space-y-4">
            {pipelineJobs.map((job) => (
              <div key={job.id} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{job.name}</span>
                  <div className="flex items-center space-x-2">
                    {job.status === 'running' && <RefreshCw className="h-4 w-4 text-blue-400 animate-spin" />}
                    {job.status === 'completed' && <CheckCircle className="h-4 w-4 text-green-400" />}
                    {job.status === 'failed' && <XCircle className="h-4 w-4 text-red-400" />}
                    {job.status === 'queued' && <Clock className="h-4 w-4 text-yellow-400" />}
                    <span className={`text-sm capitalize ${
                      job.status === 'running' ? 'text-blue-400' :
                      job.status === 'completed' ? 'text-green-400' :
                      job.status === 'failed' ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <div className="w-full bg-slate-600 rounded-full h-2 mr-4">
                    <div
                      className={`h-2 rounded-full ${
                        job.status === 'completed' ? 'bg-green-400' :
                        job.status === 'failed' ? 'bg-red-400' :
                        job.status === 'running' ? 'bg-blue-400' : 'bg-slate-500'
                      }`}
                      style={{ width: `${job.progress}%` }}
                    ></div>
                  </div>
                  <span className="text-sm text-slate-400">{job.eta}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {isProcessing && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Upload in Progress</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Uploading player statistics...</span>
              <span className="text-blue-400 font-semibold">{uploadProgress.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3">
              <div
                className="bg-blue-400 h-3 rounded-full transition-all duration-500"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataManagement;