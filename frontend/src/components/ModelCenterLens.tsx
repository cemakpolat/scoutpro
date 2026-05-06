import React, { useEffect, useMemo, useState } from 'react';
import { Brain, Database } from 'lucide-react';
import FeatureLensExplorer from './FeatureLensExplorer';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import type { MLAlgorithm, MLDataset, MLDatasetFeatureInsights } from '../types';
import {
  deleteCustomFeatureLensPreset,
  getStoredFeatureLensPresets,
  prettifyLensToken,
  saveCustomFeatureLensPreset,
  stringArraysEqual,
} from '../utils/featureLens';

interface ModelCenterLensProps {
  title?: string;
  description?: string;
  datasetHeading?: string;
  datasetDescription?: string;
  modelsHeading?: string;
  modelsDescription?: string;
  initialPresetId?: string;
}

const ModelCenterLens: React.FC<ModelCenterLensProps> = ({
  title = 'Reusable Feature Lens',
  description = 'Use the same event and parameter lens from ML Laboratory here in Model Center so prediction, exploration, and training share one analytical language.',
  datasetHeading = 'Active Lens Datasets',
  datasetDescription = 'Switch datasets without leaving Model Center. The shared lens persists its event family, temporal scope, and saved presets here too.',
  modelsHeading = 'Matching Models In This Lens',
  modelsDescription = 'These are the currently connected models whose event families and temporal assumptions match the active lens.',
  initialPresetId,
}) => {
  const [selectedDataset, setSelectedDataset] = useState('');
  const [selectedEventFamily, setSelectedEventFamily] = useState('all');
  const [selectedTemporalScope, setSelectedTemporalScope] = useState('all');
  const [selectedEventType, setSelectedEventType] = useState('all');
  const [selectedInsightFields, setSelectedInsightFields] = useState<string[]>([]);
  const [featureInsights, setFeatureInsights] = useState<MLDatasetFeatureInsights | null>(null);
  const [featureInsightsLoading, setFeatureInsightsLoading] = useState(false);
  const [featureInsightsError, setFeatureInsightsError] = useState<string | null>(null);
  const [featureLensPresets, setFeatureLensPresets] = useState(() => getStoredFeatureLensPresets());
  const [activePresetId, setActivePresetId] = useState<string | null>(null);

  const {
    data: algorithms,
    loading: algorithmsLoading,
    error: algorithmsError,
  } = useApi<MLAlgorithm[]>(() => apiService.getMLAlgorithms(), []);
  const {
    data: datasets,
    loading: datasetsLoading,
    error: datasetsError,
  } = useApi<MLDataset[]>(() => apiService.getMLDatasets(), []);

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

  const selectedDatasetData = filteredDatasets.find((dataset) => dataset.id === selectedDataset) || null;

  useEffect(() => {
    if (filteredDatasets.length === 0) {
      if (selectedDataset) {
        setSelectedDataset('');
      }
      return;
    }

    if (!selectedDataset || !filteredDatasets.some((dataset) => dataset.id === selectedDataset)) {
      setSelectedDataset(filteredDatasets[0].id);
    }
  }, [filteredDatasets, selectedDataset]);

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

  useEffect(() => {
    if (!initialPresetId || activePresetId === initialPresetId) {
      return;
    }

    const presetExists = featureLensPresets.some((entry) => entry.id === initialPresetId);
    if (presetExists) {
      handleApplyPreset(initialPresetId);
    }
  }, [activePresetId, featureLensPresets, initialPresetId]);

  return (
    <div className="space-y-6">
      <FeatureLensExplorer
        title={title}
        description={description}
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
        featureInsightsError={featureInsightsError || algorithmsError || datasetsError}
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

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[0.9fr,1.1fr]">
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-white">
            <Database className="h-5 w-5 text-green-400" />
            {datasetHeading}
          </div>
          <div className="mt-2 text-sm text-slate-400">
            {datasetDescription}
          </div>

          {datasetsLoading && <div className="mt-4 text-sm text-slate-400">Loading datasets...</div>}
          {!datasetsLoading && filteredDatasets.length === 0 && (
            <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-4 text-sm text-slate-400">
              No datasets match the current lens.
            </div>
          )}

          <div className="mt-4 space-y-3">
            {filteredDatasets.map((dataset) => (
              <button
                key={dataset.id}
                onClick={() => setSelectedDataset(dataset.id)}
                className={`w-full rounded-lg border p-4 text-left transition-colors ${
                  selectedDataset === dataset.id
                    ? 'border-cyan-400 bg-cyan-500/10'
                    : 'border-slate-700 bg-slate-900/70 hover:border-slate-500'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="font-semibold text-white">{dataset.name}</div>
                  <div className="text-xs text-green-300">{dataset.quality}% quality</div>
                </div>
                <div className="mt-2 text-xs text-slate-400">{dataset.description}</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(dataset.temporalScopes || []).map((value) => (
                    <span key={`${dataset.id}-${value}`} className="rounded-full border border-slate-600 bg-slate-800 px-2 py-1 text-[10px] text-slate-300">
                      {prettifyLensToken(value)}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-white">
            <Brain className="h-5 w-5 text-cyan-400" />
            {modelsHeading}
          </div>
          <div className="mt-2 text-sm text-slate-400">
            {modelsDescription}
          </div>

          {algorithmsLoading && <div className="mt-4 text-sm text-slate-400">Loading models...</div>}
          {!algorithmsLoading && filteredAlgorithms.length === 0 && (
            <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-4 text-sm text-slate-400">
              No models match the current event family and temporal scope.
            </div>
          )}

          <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
            {filteredAlgorithms.map((algorithm) => (
              <div key={algorithm.id} className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-semibold text-white">{algorithm.name}</div>
                  <span className="text-xs text-cyan-300">{algorithm.type}</span>
                </div>
                <div className="mt-2 text-xs text-slate-400">{algorithm.description}</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(algorithm.eventFamilies || []).map((value) => (
                    <span key={`${algorithm.id}-family-${value}`} className="rounded-full bg-slate-800 px-2 py-1 text-[10px] text-slate-300">
                      {prettifyLensToken(value)}
                    </span>
                  ))}
                  {(algorithm.temporalScopes || []).map((value) => (
                    <span key={`${algorithm.id}-scope-${value}`} className="rounded-full border border-slate-600 bg-slate-950 px-2 py-1 text-[10px] text-slate-400">
                      {prettifyLensToken(value)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelCenterLens;