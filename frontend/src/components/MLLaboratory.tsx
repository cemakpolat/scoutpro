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
import FeatureLensExplorer from './FeatureLensExplorer';
import type { ModelCenterContext, ModelCenterTab } from './ModelCenter';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import { MLAlgorithm, MLDataset, MLDatasetFeatureInsights, MLExperiment } from '../types';
import { exportService } from '../services/exportService';
import type { BackgroundTask } from '../types/tasks';
import {
  deleteCustomFeatureLensPreset,
  getStoredFeatureLensPresets,
  prettifyLensToken,
  saveCustomFeatureLensPreset,
  stringArraysEqual,
} from '../utils/featureLens';

type TrainingConfig = {
  trainTestSplit: string;
  crossValidation: string;
  optimizationMetric: string;
};

interface MLLaboratoryProps {
  onOpenModelCenter?: (tab: ModelCenterTab, context?: ModelCenterContext) => void;
}

function getExperimentDrilldown(experiment: MLExperiment): { label: string; tab: ModelCenterTab; context?: ModelCenterContext } {
  const normalizedValue = `${experiment.algorithm} ${experiment.name}`.toLowerCase();

  if (/(cluster|clustering|k-means|archetype)/.test(normalizedValue)) {
    return { label: 'Open Cluster Explorer', tab: 'clusters' };
  }

  if (/(similar|similarity)/.test(normalizedValue)) {
    return { label: 'Open Similar Players', tab: 'interactive', context: { interactivePanel: 'similar' } };
  }

  if (/(performance|fatigue|anomaly|role)/.test(normalizedValue)) {
    return { label: 'Open Interactive Predictions', tab: 'interactive', context: { interactivePanel: 'performance' } };
  }

  if (/(match|outcome|forecast)/.test(normalizedValue)) {
    return { label: 'Open Match Prediction', tab: 'match' };
  }

  if (/(xg|shot|threat|pass|sequence|event|possession)/.test(normalizedValue)) {
    return {
      label: 'Open Feature Lens',
      tab: 'lens',
      context: { lensPresetId: /(pass|sequence|possession)/.test(normalizedValue) ? 'buildup-passing' : 'shot-quality' },
    };
  }

  if (/team/.test(normalizedValue)) {
    return { label: 'Open Team Assessment', tab: 'team' };
  }

  return { label: 'Open Model Center', tab: 'navigator' };
}

const MLLaboratory: React.FC<MLLaboratoryProps> = ({ onOpenModelCenter }) => {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('');
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [selectedEventFamily, setSelectedEventFamily] = useState<string>('all');
  const [selectedTemporalScope, setSelectedTemporalScope] = useState<string>('all');
  const [selectedEventType, setSelectedEventType] = useState<string>('all');
  const [selectedInsightFields, setSelectedInsightFields] = useState<string[]>([]);
  const [featureLensPresets, setFeatureLensPresets] = useState(() => getStoredFeatureLensPresets());
  const [activePresetId, setActivePresetId] = useState<string | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingError, setTrainingError] = useState<string | null>(null);
  const [trainingResult, setTrainingResult] = useState<MLExperiment | null>(null);
  const [trainingStatusMessage, setTrainingStatusMessage] = useState('');
  const [activeTrainingTask, setActiveTrainingTask] = useState<BackgroundTask | null>(null);
  const [expandedExperimentId, setExpandedExperimentId] = useState<string | null>(null);
  const [featureInsights, setFeatureInsights] = useState<MLDatasetFeatureInsights | null>(null);
  const [featureInsightsLoading, setFeatureInsightsLoading] = useState(false);
  const [featureInsightsError, setFeatureInsightsError] = useState<string | null>(null);
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

  const eventFamilyOptions = useMemo(() => {
    const values = new Set<string>();
    (algorithms || []).forEach((algorithm) => (algorithm.eventFamilies || []).forEach((value) => values.add(value)));
    (datasets || []).forEach((dataset) => (dataset.eventFamilies || []).forEach((value) => values.add(value)));
    return Array.from(values).sort((left, right) => left.localeCompare(right));
  }, [algorithms, datasets]);

  const temporalScopeOptions = useMemo(() => {
    const values = new Set<string>();
    (algorithms || []).forEach((algorithm) => (algorithm.temporalScopes || []).forEach((value) => values.add(value)));
    (datasets || []).forEach((dataset) => (dataset.temporalScopes || []).forEach((value) => values.add(value)));
    return Array.from(values).sort((left, right) => left.localeCompare(right));
  }, [algorithms, datasets]);

  const filteredAlgorithms = useMemo(() => {
    return (algorithms || []).filter((algorithm) => {
      if (selectedEventFamily !== 'all' && !(algorithm.eventFamilies || []).includes(selectedEventFamily)) {
        return false;
      }

      if (selectedTemporalScope !== 'all' && !(algorithm.temporalScopes || []).includes(selectedTemporalScope)) {
        return false;
      }

      return true;
    });
  }, [algorithms, selectedEventFamily, selectedTemporalScope]);

  const filteredDatasets = useMemo(() => {
    return (datasets || []).filter((dataset) => {
      if (selectedEventFamily !== 'all' && !(dataset.eventFamilies || []).includes(selectedEventFamily)) {
        return false;
      }

      if (selectedTemporalScope !== 'all' && !(dataset.temporalScopes || []).includes(selectedTemporalScope)) {
        return false;
      }

      return true;
    });
  }, [datasets, selectedEventFamily, selectedTemporalScope]);

  const selectedAlgorithmData = filteredAlgorithms.find((algorithm) => algorithm.id === selectedAlgorithm) || null;
  const selectedDatasetData = filteredDatasets.find((dataset) => dataset.id === selectedDataset) || null;
  const compatibleDatasetIds = selectedAlgorithmData?.supportedDatasetIds || [];

  useEffect(() => {
    if (filteredAlgorithms.length === 0) {
      if (selectedAlgorithm) {
        setSelectedAlgorithm('');
      }
      return;
    }

    if (!selectedAlgorithm || !filteredAlgorithms.some((algorithm) => algorithm.id === selectedAlgorithm)) {
      const initialAlgorithm = filteredAlgorithms.find((algorithm) => algorithm.trainable) || filteredAlgorithms[0];
      setSelectedAlgorithm(initialAlgorithm.id);
    }
  }, [filteredAlgorithms, selectedAlgorithm]);

  useEffect(() => {
    if (!filteredDatasets.length) {
      if (selectedDataset) {
        setSelectedDataset('');
      }
      return;
    }

    if (!selectedAlgorithmData) {
      if (!selectedDataset) {
        setSelectedDataset(filteredDatasets[0].id);
      }
      return;
    }

    const recommendedDataset = filteredDatasets.find((dataset) => dataset.id === selectedAlgorithmData.recommendedDatasetId)
      || filteredDatasets.find((dataset) => compatibleDatasetIds.includes(dataset.id))
      || filteredDatasets[0];

    if (!selectedDataset || (compatibleDatasetIds.length > 0 && !compatibleDatasetIds.includes(selectedDataset))) {
      setSelectedDataset(recommendedDataset.id);
    }
  }, [compatibleDatasetIds, filteredDatasets, selectedAlgorithmData, selectedDataset]);

  useEffect(() => {
    setFeatureInsights(null);
    setFeatureInsightsError(null);
  }, [selectedDatasetData?.id]);

  useEffect(() => {
    if (!selectedDatasetData) {
      setFeatureInsights(null);
      setFeatureInsightsError(null);
      return;
    }

    let cancelled = false;

    const loadFeatureInsights = async () => {
      setFeatureInsightsLoading(true);
      setFeatureInsightsError(null);

      try {
        const response = await apiService.getMLDatasetFeatureInsights(selectedDatasetData.id, {
          eventType: selectedEventType !== 'all' ? selectedEventType : undefined,
          temporalScope: selectedTemporalScope !== 'all' ? selectedTemporalScope : undefined,
          fields: selectedInsightFields.length > 0 ? selectedInsightFields : undefined,
        });

        if (!response.success) {
          throw new Error(response.error.message);
        }

        if (cancelled) {
          return;
        }

        const nextInsights = response.data;
        setFeatureInsights(nextInsights);

        if (selectedEventType !== 'all' && !nextInsights.availableEventTypes.includes(selectedEventType)) {
          setSelectedEventType('all');
        }

        const availableFields = new Set(nextInsights.featureStats.map((entry) => entry.field));
        const sanitizedRequestedFields = selectedInsightFields.filter((field) => availableFields.has(field));
        const nextSelectedFields = (sanitizedRequestedFields.length > 0
          ? sanitizedRequestedFields
          : nextInsights.selectedFields.length > 0
            ? nextInsights.selectedFields
            : nextInsights.recommendedFields.slice(0, 4)
        ).slice(0, 6);

        if (!stringArraysEqual(selectedInsightFields, nextSelectedFields)) {
          setSelectedInsightFields(nextSelectedFields);
        }
      } catch (error) {
        if (!cancelled) {
          setFeatureInsightsError(error instanceof Error ? error.message : 'Failed to load feature insights');
          setFeatureInsights(null);
        }
      } finally {
        if (!cancelled) {
          setFeatureInsightsLoading(false);
        }
      }
    };

    void loadFeatureInsights();

    return () => {
      cancelled = true;
    };
  }, [selectedDatasetData, selectedEventType, selectedInsightFields, selectedTemporalScope]);

  const startTraining = async () => {
    if (!selectedAlgorithmData) {
      setTrainingError('Select an algorithm before starting training.');
      return;
    }

    if (!selectedAlgorithmData.trainable) {
      setTrainingError(selectedAlgorithmData.unavailableReason || `${selectedAlgorithmData.name} is not connected to a training pipeline yet.`);
      return;
    }

    if (!selectedDatasetData) {
      setTrainingError('Select a compatible dataset before starting training.');
      return;
    }

    setIsTraining(true);
    setTrainingProgress(0);
    setTrainingStatusMessage('Queueing background task...');
    setTrainingError(null);
    setTrainingResult(null);
    setActiveTrainingTask(null);

    try {
      const response = await apiService.trainModel(selectedAlgorithmData.id, selectedDatasetData.id, trainingConfig);

      if (!response.success) {
        throw new Error(response.error.message);
      }

      const queuedTask = response.data?.task as BackgroundTask | undefined;
      const queuedExperiment = response.data?.experiment as MLExperiment | undefined;

      if (!queuedTask?.task_id) {
        throw new Error('Training task was queued without a task identifier.');
      }

      setActiveTrainingTask(queuedTask);
      setTrainingProgress(Math.max(queuedTask.progress ?? 0, 5));
      setTrainingStatusMessage(queuedTask.progress_msg || 'Queued');

      if (queuedExperiment) {
        setExpandedExperimentId(queuedExperiment.id);
      }

      await refetchExperiments();

      const finishedTask = await apiService.pollTask(queuedTask.task_id, {
        intervalMs: 2000,
        timeoutMs: 30 * 60 * 1000,
        onProgress: (task) => {
          setActiveTrainingTask(task);
          setTrainingProgress(task.progress);
          setTrainingStatusMessage(task.progress_msg);
        },
      });

      setActiveTrainingTask(finishedTask);

      const latestExperiments = await apiService.getMLExperiments();
      if (latestExperiments.success && latestExperiments.data) {
        const completedExperiment = queuedExperiment
          ? latestExperiments.data.find((experiment) => experiment.id === queuedExperiment.id)
          : latestExperiments.data[0];

        if (completedExperiment) {
          setTrainingResult(completedExperiment);
          setExpandedExperimentId(completedExperiment.id);
        }
      }

      await refetchExperiments();

      if (finishedTask.status === 'failed') {
        throw new Error(finishedTask.error || 'Training failed');
      }

      setTrainingProgress(100);
      setTrainingStatusMessage(finishedTask.progress_msg || 'Done');
    } catch (error) {
      setTrainingError(error instanceof Error ? error.message : 'Training failed');
      setTrainingProgress(0);
      setTrainingStatusMessage('');
    } finally {
      setIsTraining(false);
    }
  };
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

  const handleToggleInsightField = (field: string) => {
    setActivePresetId(null);
    setSelectedInsightFields((current) => {
      if (current.includes(field)) {
        return current.filter((entry) => entry !== field);
      }

      if (current.length >= 6) {
        return [...current.slice(1), field];
      }

      return [...current, field];
    });
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

  const handleApplyPreset = (presetId: string) => {
    const preset = featureLensPresets.find((entry) => entry.id === presetId);
    if (!preset) {
      return;
    }

    setActivePresetId(preset.id);
    setSelectedEventFamily(preset.eventFamily);
    setSelectedTemporalScope(preset.temporalScope);
    setSelectedEventType(preset.eventType || 'all');
    setSelectedInsightFields(preset.fields.slice(0, 6));
    if (preset.datasetId) {
      setSelectedDataset(preset.datasetId);
    }
  };

  const handleSavePreset = (name: string) => {
    const nextPresetId = `custom-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')}`;
    const nextPresets = saveCustomFeatureLensPreset({
      id: nextPresetId,
      name,
      eventFamily: selectedEventFamily,
      temporalScope: selectedTemporalScope,
      eventType: selectedEventType,
      datasetId: selectedDatasetData?.id,
      fields: selectedInsightFields,
    });
    setFeatureLensPresets(nextPresets);
    setActivePresetId(nextPresetId);
  };

  const handleDeletePreset = (presetId: string) => {
    const nextPresets = deleteCustomFeatureLensPreset(presetId);
    setFeatureLensPresets(nextPresets);
    if (activePresetId === presetId) {
      setActivePresetId(null);
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

      <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-4 py-3 text-sm text-slate-300">
        ML Laboratory is the operational workspace for training pipelines, inspecting datasets, and reviewing experiment history. Use Model Center when you want to consume those models through team, match, player, or batch workflows.
      </div>

      <FeatureLensExplorer
        title="Event & Feature Lens"
        description="Narrow the model catalog by event family and temporal scope, then inspect how selectable numeric parameters move together inside the active dataset."
        filteredAlgorithmsCount={filteredAlgorithms.length}
        filteredDatasetsCount={filteredDatasets.length}
        activeDatasetName={selectedDatasetData?.name}
        eventFamilyOptions={eventFamilyOptions}
        temporalScopeOptions={temporalScopeOptions}
        selectedEventFamily={selectedEventFamily}
        selectedTemporalScope={selectedTemporalScope}
        selectedEventType={selectedEventType}
        selectedInsightFields={selectedInsightFields}
        featureInsights={featureInsights}
        featureInsightsLoading={featureInsightsLoading}
        featureInsightsError={featureInsightsError}
        presets={featureLensPresets}
        activePresetId={activePresetId}
        onPresetApply={handleApplyPreset}
        onPresetSave={handleSavePreset}
        onPresetDelete={handleDeletePreset}
        onEventFamilyChange={(value) => {
          setActivePresetId(null);
          setSelectedEventFamily(value);
        }}
        onTemporalScopeChange={(value) => {
          setActivePresetId(null);
          setSelectedTemporalScope(value);
        }}
        onEventTypeChange={(value) => {
          setActivePresetId(null);
          setSelectedEventType(value);
        }}
        onToggleField={handleToggleInsightField}
      />

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
          {!algorithmsLoading && !algorithmsError && filteredAlgorithms.length === 0 && (
            <p className="text-slate-400">No algorithms match the current event lens.</p>
          )}
          {!algorithmsLoading && !algorithmsError && filteredAlgorithms.length > 0 && (
            <div className="space-y-3">
              {filteredAlgorithms.map((algorithm) => (
                <div
                  key={algorithm.id}
                  onClick={() => setSelectedAlgorithm(algorithm.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedAlgorithm === algorithm.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-semibold">{algorithm.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs bg-slate-600 px-2 py-1 rounded">{algorithm.type}</span>
                      <span className={`text-xs px-2 py-1 rounded border ${algorithm.trainable ? 'border-green-500/30 bg-green-500/15 text-green-300' : 'border-amber-500/30 bg-amber-500/15 text-amber-300'}`}>
                        {algorithm.trainable ? 'Queueable' : 'Read only'}
                      </span>
                    </div>
                  </div>
                  <div className="text-sm text-slate-400 mb-2">{algorithm.description}</div>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(algorithm.eventFamilies || []).map((value) => (
                      <span key={`${algorithm.id}-family-${value}`} className="text-[10px] px-2 py-1 rounded-full bg-slate-700 text-slate-300">
                        {prettifyLensToken(value)}
                      </span>
                    ))}
                    {(algorithm.temporalScopes || []).map((value) => (
                      <span key={`${algorithm.id}-scope-${value}`} className="text-[10px] px-2 py-1 rounded-full bg-slate-900 border border-slate-600 text-slate-400">
                        {prettifyLensToken(value)}
                      </span>
                    ))}
                  </div>
                  {!algorithm.trainable && algorithm.unavailableReason && (
                    <div className="text-xs text-amber-300 mb-2">{algorithm.unavailableReason}</div>
                  )}
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
          {!datasetsLoading && !datasetsError && filteredDatasets.length === 0 && (
            <p className="text-slate-400">No datasets match the current event lens.</p>
          )}
          {!datasetsLoading && !datasetsError && filteredDatasets.length > 0 && (
            <div className="space-y-3">
              {filteredDatasets.map((dataset) => {
                const isCompatible = compatibleDatasetIds.length === 0 || compatibleDatasetIds.includes(dataset.id);
                const isRecommended = selectedAlgorithmData?.recommendedDatasetId === dataset.id;

                return (
                  <div
                    key={dataset.id}
                    onClick={() => {
                      if (isCompatible) {
                        setSelectedDataset(dataset.id);
                      }
                    }}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      !isCompatible
                        ? 'border-slate-800 opacity-50 cursor-not-allowed'
                        : selectedDataset === dataset.id
                          ? 'border-green-500 bg-green-500/10 cursor-pointer'
                          : 'border-slate-700 hover:border-slate-600 cursor-pointer'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2 gap-2">
                      <span className="font-semibold text-sm">{dataset.name}</span>
                      <div className="flex items-center gap-2">
                        {isRecommended && (
                          <span className="text-[10px] px-2 py-1 rounded border border-blue-500/30 bg-blue-500/15 text-blue-300">
                            Recommended
                          </span>
                        )}
                        <span className="text-xs text-green-400">{dataset.quality}% quality</span>
                      </div>
                    </div>
                    <div className="text-xs text-slate-400 mb-2">{dataset.description}</div>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {(dataset.eventFamilies || []).map((value) => (
                        <span key={`${dataset.id}-family-${value}`} className="text-[10px] px-2 py-1 rounded-full bg-slate-700 text-slate-300">
                          {prettifyLensToken(value)}
                        </span>
                      ))}
                      {(dataset.temporalScopes || []).map((value) => (
                        <span key={`${dataset.id}-scope-${value}`} className="text-[10px] px-2 py-1 rounded-full bg-slate-900 border border-slate-600 text-slate-400">
                          {prettifyLensToken(value)}
                        </span>
                      ))}
                    </div>
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
                    {!isCompatible && selectedAlgorithmData && (
                      <div className="text-[11px] text-amber-300 mt-2">
                        Not compatible with {selectedAlgorithmData.name}.
                      </div>
                    )}
                  </div>
                );
              })}
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

              <div className={`p-4 rounded-lg border text-sm ${selectedAlgorithmData.trainable ? 'bg-blue-500/10 border-blue-500/30 text-blue-100' : 'bg-amber-500/10 border-amber-500/30 text-amber-100'}`}>
                {selectedAlgorithmData.trainable
                  ? 'Training runs as a background task. The job will continue even if you navigate away from this page.'
                  : selectedAlgorithmData.unavailableReason || 'This algorithm is not connected to a trainable data pipeline yet.'}
              </div>

              <button
                onClick={startTraining}
                disabled={isTraining || !selectedAlgorithmData?.trainable || !selectedDatasetData}
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
                    <span>{selectedAlgorithmData.trainable ? 'Queue Training Job' : 'Training Unavailable'}</span>
                  </>
                )}
              </button>

              {(isTraining || trainingProgress === 100 || trainingProgress > 0) && (
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${trainingProgress}%` }}
                  ></div>
                </div>
              )}

              {(trainingStatusMessage || activeTrainingTask) && (
                <div className="p-4 bg-slate-700 rounded-lg text-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-white">Background Task</div>
                    {activeTrainingTask && (
                      <div className="text-xs text-slate-400">{activeTrainingTask.task_id.slice(0, 8)}...</div>
                    )}
                  </div>
                  <div className="text-slate-300">{trainingStatusMessage || activeTrainingTask?.progress_msg}</div>
                  {activeTrainingTask && (
                    <div className={`text-xs capitalize ${
                      activeTrainingTask.status === 'completed'
                        ? 'text-green-400'
                        : activeTrainingTask.status === 'failed'
                          ? 'text-red-400'
                          : 'text-blue-400'
                    }`}>
                      {activeTrainingTask.status}
                    </div>
                  )}
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
                  const drilldown = getExperimentDrilldown(experiment);

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

                              {onOpenModelCenter && (
                                <div className="pt-2">
                                  <button
                                    onClick={() => onOpenModelCenter(drilldown.tab, drilldown.context)}
                                    className="inline-flex items-center gap-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-sm font-medium text-cyan-200 transition-colors hover:bg-cyan-500/20"
                                  >
                                    {drilldown.label}
                                  </button>
                                </div>
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