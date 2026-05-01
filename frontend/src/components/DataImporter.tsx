import React, { useRef, useState } from 'react';
import {
  Upload,
  Download,
  FileText,
  CheckCircle,
  AlertCircle,
  X,
  Play,
  RefreshCw,
  Eye,
  Database,
  File,
  List,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { ImportJob, ImportPreview, ImportTemplate, ImportType } from '../types/import';
import apiService from '../services/api';

const inferFormat = (fileName: string): 'csv' | 'excel' | 'json' => {
  const lowerName = fileName.toLowerCase();
  if (lowerName.endsWith('.json')) return 'json';
  if (lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls')) return 'excel';
  return 'csv';
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
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

const downloadBlob = (blob: Blob, fileName: string) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
};

const buildPreview = async (file: File): Promise<ImportPreview> => {
  const format = inferFormat(file.name);

  if (format === 'csv') {
    const text = await file.text();
    const lines = text.split(/\r?\n/).filter(Boolean);
    const headers = lines[0]?.split(',').map((value) => value.trim()) || [];
    const rows = lines.slice(1, 4).map((line) => line.split(',').map((value) => value.trim()));

    return {
      headers,
      rows,
      totalRows: Math.max(0, lines.length - 1)
    };
  }

  if (format === 'json') {
    try {
      const parsed = JSON.parse(await file.text());
      const data = Array.isArray(parsed) ? parsed : [parsed];
      const firstRow = data[0] || {};
      const headers = Object.keys(firstRow);
      const rows = data.slice(0, 3).map((row) => headers.map((header) => String(row?.[header] ?? '')));

      return {
        headers,
        rows,
        totalRows: data.length
      };
    } catch {
      return {
        headers: ['File', 'Format', 'Preview'],
        rows: [[file.name, format, 'JSON preview unavailable']],
        totalRows: 1
      };
    }
  }

  return {
    headers: ['File', 'Size', 'Format'],
    rows: [[file.name, formatFileSize(file.size), format.toUpperCase()]],
    totalRows: 1
  };
};

const DataImporter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'import' | 'history' | 'templates'>('import');
  const [selectedType, setSelectedType] = useState<ImportType>('players');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState<ImportPreview | null>(null);
  const [actionMessage, setActionMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const [expandedTemplateId, setExpandedTemplateId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    data: importJobs = [],
    loading: jobsLoading,
    error: jobsError,
    refetch: refetchJobs,
  } = useApi(() => apiService.listImportJobs(), []);

  const {
    data: importTemplates = [],
    loading: templatesLoading,
    error: templatesError,
    refetch: refetchTemplates,
  } = useApi(() => apiService.listImportTemplates(), []);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadedFile(file);
    setShowPreview(true);
    setActionMessage('');

    try {
      const preview = await buildPreview(file);
      setPreviewData(preview);
    } catch (error) {
      console.error('Preview generation error:', error);
      setPreviewData({
        headers: ['File', 'Size'],
        rows: [[file.name, formatFileSize(file.size)]],
        totalRows: 1
      });
    }
  };

  const resetUploadState = () => {
    setUploadedFile(null);
    setPreviewData(null);
    setShowPreview(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleStartImport = async () => {
    if (!uploadedFile) return;

    setIsSubmitting(true);
    setActionMessage('');

    try {
      const response = await apiService.createImportJob({
        type: selectedType,
        fileName: uploadedFile.name,
        fileSize: uploadedFile.size,
        format: inferFormat(uploadedFile.name),
        totalRows: previewData?.totalRows,
        preview: previewData,
        createdBy: 'current_user@scoutpro.com'
      });

      if (response.success) {
        setActionMessage(`Import job started for ${uploadedFile.name}.`);
        resetUploadState();
        setActiveTab('history');
        refetchJobs();
      }
    } catch (error) {
      console.error('Create import job error:', error);
      setActionMessage('Import could not be started.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetryImport = async (jobId: string) => {
    try {
      await apiService.retryImportJob(jobId);
      setActionMessage(`Retry started for import job ${jobId}.`);
      refetchJobs();
    } catch (error) {
      console.error('Retry import job error:', error);
      setActionMessage('Retry failed.');
    }
  };

  const handleDownloadReport = async (jobId: string) => {
    try {
      const blob = await apiService.downloadImportJobReport(jobId);
      downloadBlob(blob, `import-report-${jobId}.json`);
    } catch (error) {
      console.error('Download import report error:', error);
      setActionMessage('Import report could not be downloaded.');
    }
  };

  const handleDownloadTemplate = (template: ImportTemplate) => {
    const headers = [...template.requiredFields, ...template.optionalFields].join(',');
    const sampleRow = template.sampleData[0] || {};
    const values = [...template.requiredFields, ...template.optionalFields]
      .map((field) => sampleRow[field as keyof typeof sampleRow] || '')
      .join(',');

    const blob = new Blob([`${headers}\n${values}`], { type: 'text/csv' });
    downloadBlob(blob, `${template.name.replace(/\s+/g, '_')}.csv`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Database className="h-8 w-8 mr-3 text-orange-500" />
          Data Import/Export
        </h1>
      </div>

      {actionMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-green-300">
          <CheckCircle className="h-4 w-4 text-green-400" />
          <span>{actionMessage}</span>
        </div>
      )}

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

      {activeTab === 'import' && (
        <div className="space-y-6">
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
                    onClick={(event) => {
                      event.stopPropagation();
                      resetUploadState();
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
                  onClick={handleStartImport}
                  disabled={isSubmitting}
                  className="flex-1 flex items-center justify-center space-x-2 px-4 py-3 bg-orange-600 hover:bg-orange-700 disabled:bg-slate-600 rounded-lg transition-colors"
                >
                  <Play className="h-4 w-4" />
                  <span>{isSubmitting ? 'Starting...' : 'Start Import'}</span>
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

          {showPreview && uploadedFile && previewData && (
            <div className="bg-slate-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4">Data Preview</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      {previewData.headers.map((header) => (
                        <th key={header} className="text-left py-2 px-3">{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.rows.map((row, index) => (
                      <tr key={index} className="border-b border-slate-700">
                        {row.map((cell, cellIndex) => (
                          <td key={`${index}-${cellIndex}`} className="py-2 px-3">{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 text-sm text-slate-400">
                Preview showing {previewData.rows.length} of {previewData.totalRows} rows
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => refetchJobs()}
              className="flex items-center gap-2 rounded-lg bg-slate-700 px-4 py-2 text-sm hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh History
            </button>
          </div>

          {jobsError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {jobsError}
            </div>
          )}

          {jobsLoading ? (
            <div className="rounded-xl bg-slate-800 px-6 py-16 text-center text-slate-300">
              Loading import jobs...
            </div>
          ) : importJobs.length === 0 ? (
            <div className="rounded-xl bg-slate-800 px-6 py-16 text-center text-slate-400">
              No backend import jobs found.
            </div>
          ) : importJobs.map((job: ImportJob) => (
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

              {job.errors.length > 0 && (
                <div className="bg-red-900/20 border border-red-600/50 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <AlertCircle className="h-4 w-4 text-red-400" />
                    <span className="font-semibold text-red-400">{job.errors.length} Errors</span>
                  </div>
                  <div className="space-y-1">
                    {job.errors.slice(0, 3).map((error, index) => (
                      <div key={index} className="text-sm text-red-300">
                        Row {error.row}: {error.error}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-2 mt-4">
                <button
                  onClick={() => setExpandedJobId(expandedJobId === job.id ? null : job.id)}
                  className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
                >
                  {expandedJobId === job.id ? 'Hide Details' : 'View Details'}
                </button>
                {(job.status === 'completed' || job.status === 'partial') && (
                  <button
                    onClick={() => handleDownloadReport(job.id)}
                    className="px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors"
                  >
                    Download Report
                  </button>
                )}
                {job.status === 'failed' && (
                  <button
                    onClick={() => handleRetryImport(job.id)}
                    className="px-3 py-1.5 bg-orange-600 hover:bg-orange-700 rounded text-sm transition-colors"
                  >
                    Retry Import
                  </button>
                )}
              </div>

              {expandedJobId === job.id && (
                <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/40 p-4 text-sm text-slate-300">
                  <div>Created by: {job.createdBy}</div>
                  <div>Started: {job.startedAt ? new Date(job.startedAt).toLocaleString() : 'Pending'}</div>
                  <div>Completed: {job.completedAt ? new Date(job.completedAt).toLocaleString() : 'Pending'}</div>
                  <div>Format: {job.format}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'templates' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => refetchTemplates()}
              className="flex items-center gap-2 rounded-lg bg-slate-700 px-4 py-2 text-sm hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh Templates
            </button>
          </div>

          {templatesError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {templatesError}
            </div>
          )}

          {templatesLoading ? (
            <div className="rounded-xl bg-slate-800 px-6 py-16 text-center text-slate-300">
              Loading import templates...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {importTemplates.map((template: ImportTemplate) => (
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
                      onClick={() => setExpandedTemplateId(expandedTemplateId === template.id ? null : template.id)}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
                      title="Preview Template"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </div>

                  {expandedTemplateId === template.id && (
                    <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/40 p-4 text-sm text-slate-300">
                      <div className="font-medium mb-2">Sample Data</div>
                      <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-slate-400">
                        {JSON.stringify(template.sampleData[0] || {}, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DataImporter;