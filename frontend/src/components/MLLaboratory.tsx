import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  BarChart3,
  Brain,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  Download,
  Eye,
  Play,
  RefreshCw,
  Settings,
  Star,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import { MLAlgorithm, MLDataset, MLExperiment } from '../types';
import { exportService } from '../services/exportService';

type TrainingConfig = {
  trainTestSplit: string;
  crossValidation: string;
  optimizationMetric: string;
};

const MLLaboratory: React.FC = () => {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('');
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingError, setTrainingError] = useState<string | null>(null);
  const [trainingResult, setTrainingResult] = useState<MLExperiment | null>(null);
  const [expandedExperimentId, setExpandedExperimentId] = useState<string | null>(null);
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>({
    trainTestSplit: '80/20',
    crossValidation: '5-Fold',
    optimizationMetric: 'Accuracy',
  });

  const {
    data: algorithms,
    loading: algorithmsLoading,
    error: algorithmsError,
    refetch: refetchAlgorithms,
  } = useApi<MLAlgorithm[]>(
    () => apiService.getMLAlgorithms(), []
  );
  const {
    data: datasets,
    loading: datasetsLoading,
    error: datasetsError,
    refetch: refetchDatasets,
  } = useApi<MLDataset[]>(
    () => apiService.getMLDatasets(), []
  );
  const {
    data: experiments,
    loading: experimentsLoading,
    error: experimentsError,
    refetch: refetchExperiments,
  } = useApi<MLExperiment[]>(
    () => apiService.getMLExperiments(), []
  );

  useEffect(() => {
    if (!selectedAlgorithm && algorithms?.length) {
      setSelectedAlgorithm(algorithms[0].id);
    }
  }, [algorithms, selectedAlgorithm]);

  useEffect(() => {
    if (!selectedDataset && datasets?.length) {
      setSelectedDataset(datasets[0].id);
    }
  }, [datasets, selectedDataset]);

  const startTraining = async () => {
    if (!selectedAlgorithm || !selectedDataset) {
      setTrainingError('Select an algorithm and dataset before starting training.');
      return;
    }

    setIsTraining(true);
    setTrainingProgress(15);
    setTrainingError(null);
    setTrainingResult(null);

    try {
      setTrainingProgress(45);
      const response = await apiService.trainModel(selectedAlgorithm, selectedDataset, trainingConfig);

      if (!response.success) {
        throw new Error(response.error.message);
      }

      setTrainingProgress(80);

      const experiment = (response.data?.experiment || response.data) as MLExperiment | undefined;
      if (experiment) {
        setTrainingResult(experiment);
        setExpandedExperimentId(experiment.id);
      }

      await refetchExperiments();
      setTrainingProgress(100);
    } catch (error) {
      setTrainingError(error instanceof Error ? error.message : 'Training failed');
      setTrainingProgress(0);
    } finally {
      setIsTraining(false);
    }
  };

  const selectedAlgorithmData = algorithms?.find((algorithm) => algorithm.id === selectedAlgorithm) || null;
  const selectedDatasetData = datasets?.find((dataset) => dataset.id === selectedDataset) || null;
  const latestExperiment = trainingResult || experiments?.[0] || null;

  const completedExperiments = useMemo(
    () => (experiments || []).filter((experiment) => experiment.status === 'completed'),
    [experiments],
  );

  const averageAccuracy = useMemo(() => {
    if (completedExperiments.length === 0) {
      return null;
    }

    const total = completedExperiments.reduce((sum, experiment) => sum + (experiment.accuracy || 0), 0);
    return total / completedExperiments.length;
  }, [completedExperiments]);

  const backendInsights = useMemo(() => {
    if (latestExperiment?.insights?.length) {
      return latestExperiment.insights;
    }

    const insights = [];

    if (selectedAlgorithmData?.bestFor?.length) {
      insights.push(`${selectedAlgorithmData.name} is strongest for ${selectedAlgorithmData.bestFor.join(', ')}.`);
    }

    if (selectedDatasetData) {
      insights.push(
        `${selectedDatasetData.name} exposes ${selectedDatasetData.features} features across ${selectedDatasetData.records} records.`
      );
      insights.push(`Dataset freshness: ${selectedDatasetData.lastUpdated}.`);
    }

    return insights;
  }, [latestExperiment, selectedAlgorithmData, selectedDatasetData]);

  const monitoringCards = [
    {
      label: 'Available Models',
      value: algorithms?.length ?? 0,
      detail: selectedAlgorithmData ? `${selectedAlgorithmData.name} selected` : 'Awaiting catalog',
      icon: Brain,
      accent: 'text-green-400',
    },
    {
      label: 'Datasets Online',
      value: datasets?.length ?? 0,
      detail: selectedDatasetData ? `${selectedDatasetData.quality}% quality on current dataset` : 'Awaiting dataset scan',
      icon: Database,
      accent: 'text-blue-400',
    },
    {
      label: 'Experiments Logged',
      value: experiments?.length ?? 0,
      detail: `${completedExperiments.length} completed`,
      icon: Activity,
      accent: 'text-yellow-400',
    },
    {
      label: 'Average Accuracy',
      value: averageAccuracy !== null ? `${averageAccuracy.toFixed(1)}%` : '-',
      detail: latestExperiment ? `Latest runtime ${latestExperiment.runtime}` : 'No completed runs yet',
      icon: Eye,
      accent: 'text-purple-400',
    },
  ];

  const handleRefresh = async () => {
    await Promise.all([refetchAlgorithms(), refetchDatasets(), refetchExperiments()]);
  };

  const handleTrainingConfigChange = (key: keyof TrainingConfig, value: string) => {
    setTrainingConfig((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleExport = async () => {
    if (!experiments || experiments.length === 0) {
      alert('No experiments to export');
      return;
    }

    const exportData = experiments.map(exp => ({
      Experiment: exp.name,
      Algorithm: exp.algorithm,
      Dataset: exp.dataset,
      Status: exp.status,
      Accuracy: exp.accuracy > 0 ? `${exp.accuracy}%` : '-',
      Runtime: exp.runtime,
      Created: exp.created,
    }));

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `ml_experiments_${Date.now()}.pdf`,
        data: exportData,
        header: 'ML Laboratory - Experiment History',
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('ML experiments exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Brain className="h-8 w-8 mr-3 text-purple-500" />
          ML Laboratory
        </h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={handleRefresh}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh Catalog</span>
          </button>
          <button onClick={handleExport} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export Model</span>
          </button>
        </div>
      </div>

      {/* Experiment Setup */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Algorithm Selection */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Cpu className="h-6 w-6 mr-2 text-blue-400" />
            Algorithm Selection
          </h3>
          {algorithmsLoading && <p className="text-slate-400">Loading algorithms...</p>}
          {algorithmsError && <p className="text-red-400">Error: {algorithmsError}</p>}
          {!algorithmsLoading && !algorithmsError && algorithms && (
            <div className="space-y-3">
              {algorithms.map((algorithm) => (
                <div
                  key={algorithm.id}
                  onClick={() => setSelectedAlgorithm(algorithm.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedAlgorithm === algorithm.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{algorithm.name}</span>
                    <span className="text-xs bg-slate-600 px-2 py-1 rounded">{algorithm.type}</span>
                  </div>
                  <div className="text-sm text-slate-400 mb-2">{algorithm.description}</div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <div className="text-slate-500">Accuracy</div>
                      <div className="font-bold text-green-400">{algorithm.accuracy}%</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Speed</div>
                      <div className="font-bold">{algorithm.speed}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Interpret</div>
                      <div className="font-bold">{algorithm.interpretability}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dataset Selection */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Database className="h-6 w-6 mr-2 text-green-400" />
            Dataset Selection
          </h3>
          {datasetsLoading && <p className="text-slate-400">Loading datasets...</p>}
          {datasetsError && <p className="text-red-400">Error: {datasetsError}</p>}
          {!datasetsLoading && !datasetsError && datasets && (
            <div className="space-y-3">
              {datasets.map((dataset) => (
                <div
                  key={dataset.id}
                  onClick={() => setSelectedDataset(dataset.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedDataset === dataset.id
                      ? 'border-green-500 bg-green-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">{dataset.name}</span>
                    <span className="text-xs text-green-400">{dataset.quality}% quality</span>
                  </div>
                  <div className="text-xs text-slate-400 mb-2">{dataset.description}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="text-slate-500">Size</div>
                      <div className="font-bold">{dataset.size}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Features</div>
                      <div className="font-bold">{dataset.features}</div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Updated: {dataset.lastUpdated}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Configuration & Training */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Settings className="h-6 w-6 mr-2 text-yellow-400" />
            Configuration
          </h3>
          
          {selectedAlgorithmData && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-700 rounded-lg">
                <h4 className="font-semibold mb-3">Algorithm Parameters</h4>
                <div className="space-y-2">
                  {Object.entries(selectedAlgorithmData.parameters).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-slate-400">{key}:</span>
                      <span className="font-mono">{JSON.stringify(value)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-slate-700 rounded-lg">
                <h4 className="font-semibold mb-3">Training Configuration</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Train/Test Split</label>
                    <select
                      value={trainingConfig.trainTestSplit}
                      onChange={(event) => handleTrainingConfigChange('trainTestSplit', event.target.value)}
                      className="w-full px-3 py-2 bg-slate-600 rounded text-sm"
                    >
                      <option>80/20</option>
                      <option>70/30</option>
                      <option>90/10</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Cross Validation</label>
                    <select
                      value={trainingConfig.crossValidation}
                      onChange={(event) => handleTrainingConfigChange('crossValidation', event.target.value)}
                      className="w-full px-3 py-2 bg-slate-600 rounded text-sm"
                    >
                      <option>5-Fold</option>
                      <option>10-Fold</option>
                      <option>Leave-One-Out</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Optimization Metric</label>
                    <select
                      value={trainingConfig.optimizationMetric}
                      onChange={(event) => handleTrainingConfigChange('optimizationMetric', event.target.value)}
                      className="w-full px-3 py-2 bg-slate-600 rounded text-sm"
                    >
                      <option>Accuracy</option>
                      <option>F1-Score</option>
                      <option>ROC-AUC</option>
                      <option>Mean Squared Error</option>
                    </select>
                  </div>
                </div>
              </div>

              <button
                onClick={startTraining}
                disabled={isTraining || !selectedAlgorithmData || !selectedDatasetData}
                className="w-full flex items-center justify-center space-x-2 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 rounded-lg font-semibold transition-colors"
              >
                {isTraining ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Training... {trainingProgress.toFixed(0)}%</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Start Training</span>
                  </>
                )}
              </button>

              {(isTraining || trainingProgress === 100) && (
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${trainingProgress}%` }}
                  ></div>
                </div>
              )}

              {trainingError && <div className="text-sm text-red-400">{trainingError}</div>}
              {trainingResult && (
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg text-sm">
                  <div className="font-semibold text-green-300">Latest Run Completed</div>
                  <div className="text-slate-300 mt-1">
                    {trainingResult.name} finished at {trainingResult.accuracy}% accuracy.
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Experiment History */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Activity className="h-6 w-6 mr-2 text-green-400" />
          Experiment History
        </h3>
        {experimentsLoading && <p className="text-slate-400">Loading experiments...</p>}
        {experimentsError && <p className="text-red-400">Error: {experimentsError}</p>}
        {!experimentsLoading && !experimentsError && experiments && experiments.length === 0 && (
          <p className="text-slate-400">No experiments have been created yet.</p>
        )}
        {!experimentsLoading && !experimentsError && experiments && experiments.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">Experiment</th>
                  <th className="text-left py-3 px-2">Algorithm</th>
                  <th className="text-left py-3 px-2">Dataset</th>
                  <th className="text-left py-3 px-2">Status</th>
                  <th className="text-left py-3 px-2">Accuracy</th>
                  <th className="text-left py-3 px-2">Runtime</th>
                  <th className="text-left py-3 px-2">Details</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((experiment) => {
                  const isExpanded = expandedExperimentId === experiment.id;

                  return (
                    <React.Fragment key={experiment.id}>
                      <tr className="border-b border-slate-700 hover:bg-slate-700/40">
                        <td className="py-3 px-2">
                          <div>
                            <div className="font-semibold">{experiment.name}</div>
                            <div className="text-xs text-slate-400">{experiment.created}</div>
                          </div>
                        </td>
                        <td className="py-3 px-2">{experiment.algorithm}</td>
                        <td className="py-3 px-2 text-sm">{experiment.dataset}</td>
                        <td className="py-3 px-2">
                          <div className="flex items-center space-x-2">
                            {experiment.status === 'completed' && <CheckCircle className="h-4 w-4 text-green-400" />}
                            {experiment.status === 'running' && <RefreshCw className="h-4 w-4 text-blue-400 animate-spin" />}
                            {experiment.status === 'failed' && <XCircle className="h-4 w-4 text-red-400" />}
                            <span className={`text-sm capitalize ${
                              experiment.status === 'completed' ? 'text-green-400' :
                              experiment.status === 'running' ? 'text-blue-400' : 'text-red-400'
                            }`}>
                              {experiment.status}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          {experiment.accuracy > 0 ? (
                            <span className="font-bold text-green-400">{experiment.accuracy}%</span>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </td>
                        <td className="py-3 px-2 text-sm text-slate-400">{experiment.runtime}</td>
                        <td className="py-3 px-2">
                          <button
                            onClick={() => setExpandedExperimentId(isExpanded ? null : experiment.id)}
                            className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs transition-colors"
                          >
                            {isExpanded ? 'Hide' : 'View'}
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="border-b border-slate-700 bg-slate-900/40">
                          <td className="px-4 py-4" colSpan={7}>
                            <div className="space-y-2">
                              <div className="text-sm font-semibold text-white">Backend Insights</div>
                              {experiment.insights.length > 0 ? (
                                <ul className="space-y-2 text-sm text-slate-300">
                                  {experiment.insights.map((insight, index) => (
                                    <li key={`${experiment.id}-${index}`} className="flex items-start space-x-2">
                                      <CheckCircle className="h-4 w-4 text-green-400 mt-0.5" />
                                      <span>{insight}</span>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <div className="text-sm text-slate-400">No experiment insights were returned for this run.</div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Model Performance Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <BarChart3 className="h-6 w-6 mr-2 text-blue-400" />
            Algorithm Performance Comparison
          </h3>
          {algorithmsLoading && <p className="text-slate-400">Loading algorithms...</p>}
          {algorithmsError && <p className="text-red-400">Error: {algorithmsError}</p>}
          {!algorithmsLoading && !algorithmsError && algorithms && (
            <div className="space-y-4">
              {algorithms.slice(0, 4).map((algorithm) => (
                <div key={algorithm.id} className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">{algorithm.name}</span>
                    <span className="text-sm font-bold text-green-400">{algorithm.accuracy}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full"
                      style={{ width: `${algorithm.accuracy}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Speed: {algorithm.speed}</span>
                    <span>Interpretability: {algorithm.interpretability}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <TrendingUp className="h-6 w-6 mr-2 text-purple-400" />
            Backend Training Insights
          </h3>
          <div className="space-y-4">
            {selectedAlgorithmData && (
              <div className="p-4 bg-slate-700 rounded-lg">
                <div className="text-sm text-slate-400 mb-1">Selected Algorithm</div>
                <div className="font-semibold text-white">{selectedAlgorithmData.name}</div>
                <div className="text-sm text-slate-400 mt-1">
                  Best for: {selectedAlgorithmData.bestFor.join(', ') || 'General modelling'}
                </div>
              </div>
            )}

            {selectedDatasetData && (
              <div className="p-4 bg-slate-700 rounded-lg">
                <div className="text-sm text-slate-400 mb-1">Selected Dataset</div>
                <div className="font-semibold text-white">{selectedDatasetData.name}</div>
                <div className="text-sm text-slate-400 mt-1">
                  {selectedDatasetData.records} records, {selectedDatasetData.features} features, updated {selectedDatasetData.lastUpdated}
                </div>
              </div>
            )}

            <div className="p-4 bg-slate-700 rounded-lg">
              <div className="text-sm text-slate-400 mb-3">Latest Backend Feedback</div>
              {backendInsights.length > 0 ? (
                <div className="space-y-2">
                  {backendInsights.map((insight, index) => (
                    <div key={`${insight}-${index}`} className="flex items-start space-x-2 text-sm text-slate-200">
                      <Star className="h-4 w-4 text-yellow-400 mt-0.5" />
                      <span>{insight}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-slate-400">Run a training job to populate backend experiment insights.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Eye className="h-6 w-6 mr-2 text-green-400" />
          Backend Model Monitoring
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {monitoringCards.map((card) => {
            const Icon = card.icon;

            return (
              <div key={card.label} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">{card.label}</span>
                  <Icon className={`h-4 w-4 ${card.accent}`} />
                </div>
                <div className="text-2xl font-bold text-white">{card.value}</div>
                <div className={`text-xs ${card.accent}`}>{card.detail}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default MLLaboratory;