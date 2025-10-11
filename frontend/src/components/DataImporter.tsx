import React, { useState, useRef } from 'react';
import {
  Upload, Download, FileText, CheckCircle, AlertCircle,
  X, Play, Pause, RefreshCw, Eye, Settings, Database,
  ArrowRight, File, Table, List, BarChart3
} from 'lucide-react';
import { ImportJob, ImportTemplate, ImportType } from '../types/import';

const DataImporter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'import' | 'history' | 'templates'>('import');
  const [selectedType, setSelectedType] = useState<ImportType>('players');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mock data
  const mockJobs: ImportJob[] = [
    {
      id: 'job1',
      type: 'players',
      format: 'csv',
      fileName: 'premier_league_players.csv',
      fileSize: 245000,
      totalRows: 500,
      processedRows: 500,
      successRows: 487,
      failedRows: 13,
      status: 'completed',
      errors: [
        { row: 45, column: 'age', error: 'Invalid age value', value: 'twenty' },
        { row: 127, column: 'marketValue', error: 'Market value exceeds maximum', value: '99999999999' },
      ],
      createdBy: 'admin@scoutpro.com',
      createdAt: '2024-10-01T10:30:00Z',
      completedAt: '2024-10-01T10:32:15Z',
      progress: 100
    },
    {
      id: 'job2',
      type: 'matches',
      format: 'excel',
      fileName: 'laliga_matches_2024.xlsx',
      fileSize: 180000,
      totalRows: 380,
      processedRows: 200,
      successRows: 195,
      failedRows: 5,
      status: 'processing',
      errors: [],
      createdBy: 'analyst@scoutpro.com',
      createdAt: '2024-10-02T09:15:00Z',
      progress: 53
    },
    {
      id: 'job3',
      type: 'stats',
      format: 'json',
      fileName: 'player_stats_batch_1.json',
      fileSize: 520000,
      totalRows: 1200,
      processedRows: 0,
      successRows: 0,
      failedRows: 0,
      status: 'pending',
      errors: [],
      createdBy: 'admin@scoutpro.com',
      createdAt: '2024-10-02T11:00:00Z',
      progress: 0
    }
  ];

  const mockTemplates: ImportTemplate[] = [
    {
      id: 't1',
      name: 'Player Import Template',
      type: 'players',
      description: 'Standard template for importing player data',
      requiredFields: ['name', 'position', 'age', 'nationality'],
      optionalFields: ['club', 'marketValue', 'height', 'foot', 'rating'],
      sampleData: [
        { name: 'John Doe', position: 'ST', age: 24, nationality: 'England', club: 'Manchester United' }
      ],
      mapping: {
        'Player Name': 'name',
        'Position': 'position',
        'Age': 'age',
        'Country': 'nationality'
      }
    },
    {
      id: 't2',
      name: 'Match Import Template',
      type: 'matches',
      description: 'Template for importing match data',
      requiredFields: ['homeTeam', 'awayTeam', 'date', 'competition'],
      optionalFields: ['venue', 'score', 'attendance', 'referee'],
      sampleData: [
        { homeTeam: 'Barcelona', awayTeam: 'Real Madrid', date: '2024-10-26', competition: 'La Liga' }
      ],
      mapping: {
        'Home': 'homeTeam',
        'Away': 'awayTeam',
        'Date': 'date',
        'League': 'competition'
      }
    }
  ];

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setShowPreview(true);
    }
  };

  const handleDownloadTemplate = (template: ImportTemplate) => {
    // Create CSV content
    const headers = [...template.requiredFields, ...template.optionalFields].join(',');
    const sampleRow = template.sampleData[0];
    const values = [...template.requiredFields, ...template.optionalFields]
      .map(field => sampleRow[field as keyof typeof sampleRow] || '')
      .join(',');

    const csvContent = `${headers}\n${values}`;
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${template.name.replace(/\s+/g, '_')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusColor = (status: ImportJob['status']) => {
    const colors = {
      pending: 'bg-slate-600',
      processing: 'bg-blue-600',
      completed: 'bg-green-600',
      failed: 'bg-red-600',
      partial: 'bg-yellow-600'
    };
    return colors[status];
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Database className="h-8 w-8 mr-3 text-orange-500" />
          Data Import/Export
        </h1>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab('import')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'import'
              ? 'border-orange-500 text-orange-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Upload className="h-4 w-4" />
          <span>Import Data</span>
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-orange-500 text-orange-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <List className="h-4 w-4" />
          <span>Import History</span>
        </button>
        <button
          onClick={() => setActiveTab('templates')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'templates'
              ? 'border-orange-500 text-orange-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>Templates</span>
        </button>
      </div>

      {/* Import Tab */}
      {activeTab === 'import' && (
        <div className="space-y-6">
          {/* Data Type Selection */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Select Data Type</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {(['players', 'matches', 'stats', 'videos'] as ImportType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setSelectedType(type)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedType === type
                      ? 'border-orange-500 bg-orange-900/20'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-lg font-semibold capitalize">{type}</div>
                    <div className="text-xs text-slate-400 mt-1">Import {type} data</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* File Upload */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Upload File</h3>

            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-600 rounded-xl p-12 text-center hover:border-orange-500 transition-colors cursor-pointer"
            >
              <Upload className="h-16 w-16 mx-auto mb-4 text-slate-500" />
              <p className="text-lg font-medium mb-2">Click to upload or drag and drop</p>
              <p className="text-sm text-slate-400">CSV, Excel, or JSON files (max 10MB)</p>
              {uploadedFile && (
                <div className="mt-4 inline-flex items-center space-x-2 bg-slate-700 px-4 py-2 rounded-lg">
                  <File className="h-4 w-4 text-green-400" />
                  <span className="text-sm font-medium">{uploadedFile.name}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setUploadedFile(null);
                      setShowPreview(false);
                    }}
                    className="p-1 hover:bg-slate-600 rounded"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.json"
              onChange={handleFileSelect}
              className="hidden"
            />

            {uploadedFile && (
              <div className="mt-4 flex items-center space-x-3">
                <button
                  onClick={() => {
                    alert(`✅ Import started for ${uploadedFile.name}!\n\nType: ${selectedType}\n\n(Note: Import will process once backend is connected)`);
                    setUploadedFile(null);
                    setShowPreview(false);
                  }}
                  className="flex-1 flex items-center justify-center space-x-2 px-4 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg transition-colors"
                >
                  <Play className="h-4 w-4" />
                  <span>Start Import</span>
                </button>
                <button
                  onClick={() => setShowPreview(!showPreview)}
                  className="flex items-center space-x-2 px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  <Eye className="h-4 w-4" />
                  <span>{showPreview ? 'Hide' : 'Preview'}</span>
                </button>
              </div>
            )}
          </div>

          {/* Preview */}
          {showPreview && uploadedFile && (
            <div className="bg-slate-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4">Data Preview</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-2 px-3">Name</th>
                      <th className="text-left py-2 px-3">Position</th>
                      <th className="text-left py-2 px-3">Age</th>
                      <th className="text-left py-2 px-3">Nationality</th>
                      <th className="text-left py-2 px-3">Club</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-slate-700">
                      <td className="py-2 px-3">Sample Player 1</td>
                      <td className="py-2 px-3">ST</td>
                      <td className="py-2 px-3">24</td>
                      <td className="py-2 px-3">England</td>
                      <td className="py-2 px-3">Manchester United</td>
                    </tr>
                    <tr className="border-b border-slate-700">
                      <td className="py-2 px-3">Sample Player 2</td>
                      <td className="py-2 px-3">CM</td>
                      <td className="py-2 px-3">26</td>
                      <td className="py-2 px-3">Spain</td>
                      <td className="py-2 px-3">Barcelona</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="mt-4 text-sm text-slate-400">
                Preview showing 2 of 500 rows
              </div>
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {mockJobs.map((job) => (
            <div key={job.id} className="bg-slate-800 rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="text-lg font-semibold">{job.fileName}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-slate-400">
                    <span className="capitalize">{job.type}</span>
                    <span>•</span>
                    <span>{formatFileSize(job.fileSize)}</span>
                    <span>•</span>
                    <span>{job.totalRows} rows</span>
                  </div>
                </div>
                <div className="text-sm text-slate-400">
                  {new Date(job.createdAt).toLocaleString()}
                </div>
              </div>

              {/* Progress Bar */}
              {job.status === 'processing' && (
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-slate-400">Progress</span>
                    <span className="font-semibold">{job.progress}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-slate-700 rounded-lg p-3">
                  <div className="text-2xl font-bold text-green-400">{job.successRows}</div>
                  <div className="text-xs text-slate-400">Successful</div>
                </div>
                <div className="bg-slate-700 rounded-lg p-3">
                  <div className="text-2xl font-bold text-red-400">{job.failedRows}</div>
                  <div className="text-xs text-slate-400">Failed</div>
                </div>
                <div className="bg-slate-700 rounded-lg p-3">
                  <div className="text-2xl font-bold text-blue-400">{job.processedRows}</div>
                  <div className="text-xs text-slate-400">Processed</div>
                </div>
              </div>

              {/* Errors */}
              {job.errors.length > 0 && (
                <div className="bg-red-900/20 border border-red-600/50 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <AlertCircle className="h-4 w-4 text-red-400" />
                    <span className="font-semibold text-red-400">{job.errors.length} Errors</span>
                  </div>
                  <div className="space-y-1">
                    {job.errors.slice(0, 3).map((error, idx) => (
                      <div key={idx} className="text-sm text-red-300">
                        Row {error.row}: {error.error}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center space-x-2 mt-4">
                <button
                  onClick={() => {
                    alert(`📊 Import Job Details\n\nFile: ${job.fileName}\nType: ${job.type}\nStatus: ${job.status}\nTotal Rows: ${job.totalRows}\nSuccess: ${job.successRows}\nFailed: ${job.failedRows}\n\n(Full details will be available once backend is connected)`);
                  }}
                  className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
                >
                  View Details
                </button>
                {job.status === 'completed' && (
                  <button
                    onClick={() => {
                      alert(`📥 Downloading import report for "${job.fileName}"...\n\n(Report download will be available once backend is connected)`);
                    }}
                    className="px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors"
                  >
                    Download Report
                  </button>
                )}
                {job.status === 'failed' && (
                  <button
                    onClick={() => {
                      alert(`🔄 Retrying import for "${job.fileName}"...\n\n(Retry functionality will be available once backend is connected)`);
                    }}
                    className="px-3 py-1.5 bg-orange-600 hover:bg-orange-700 rounded text-sm transition-colors"
                  >
                    Retry Import
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {mockTemplates.map((template) => (
            <div key={template.id} className="bg-slate-800 rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold mb-2">{template.name}</h3>
                  <p className="text-sm text-slate-400">{template.description}</p>
                </div>
                <FileText className="h-8 w-8 text-orange-400" />
              </div>

              <div className="space-y-3 mb-4">
                <div>
                  <div className="text-sm font-medium mb-1">Required Fields ({template.requiredFields.length})</div>
                  <div className="flex flex-wrap gap-1">
                    {template.requiredFields.map((field) => (
                      <span key={field} className="px-2 py-1 bg-red-900/30 text-red-400 rounded text-xs">
                        {field}*
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium mb-1">Optional Fields ({template.optionalFields.length})</div>
                  <div className="flex flex-wrap gap-1">
                    {template.optionalFields.map((field) => (
                      <span key={field} className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-xs">
                        {field}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleDownloadTemplate(template)}
                  className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg text-sm transition-colors"
                >
                  <Download className="h-4 w-4" />
                  <span>Download Template</span>
                </button>
                <button
                  onClick={() => {
                    alert(`👁️ Template Preview: ${template.name}\n\nRequired Fields:\n${template.requiredFields.join(', ')}\n\nOptional Fields:\n${template.optionalFields.join(', ')}\n\nSample Data:\n${JSON.stringify(template.sampleData[0], null, 2)}\n\n(Full preview will be available once backend is connected)`);
                  }}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
                  title="Preview Template"
                >
                  <Eye className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DataImporter;
