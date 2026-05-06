import React, { useMemo, useState } from 'react';
import { BarChart3, RefreshCw, Save, Trash2 } from 'lucide-react';
import type { MLDatasetFeatureInsights } from '../types';
import type { FeatureLensPreset } from '../utils/featureLens';
import { correlationTone, formatInsightNumber, prettifyLensToken } from '../utils/featureLens';

interface FeatureLensExplorerProps {
  title?: string;
  description?: string;
  filteredAlgorithmsCount: number;
  filteredDatasetsCount: number;
  activeDatasetName?: string;
  eventFamilyOptions: string[];
  temporalScopeOptions: string[];
  selectedEventFamily: string;
  selectedTemporalScope: string;
  selectedEventType: string;
  selectedInsightFields: string[];
  featureInsights: MLDatasetFeatureInsights | null;
  featureInsightsLoading: boolean;
  featureInsightsError: string | null;
  presets: FeatureLensPreset[];
  activePresetId: string | null;
  onPresetApply: (presetId: string) => void;
  onPresetSave: (name: string) => void;
  onPresetDelete: (presetId: string) => void;
  onEventFamilyChange: (value: string) => void;
  onTemporalScopeChange: (value: string) => void;
  onEventTypeChange: (value: string) => void;
  onToggleField: (field: string) => void;
}

const FeatureLensExplorer: React.FC<FeatureLensExplorerProps> = ({
  title = 'Event & Feature Lens',
  description = 'Filter models and datasets by event family and temporal scope, then inspect how numeric parameters move together.',
  filteredAlgorithmsCount,
  filteredDatasetsCount,
  activeDatasetName,
  eventFamilyOptions,
  temporalScopeOptions,
  selectedEventFamily,
  selectedTemporalScope,
  selectedEventType,
  selectedInsightFields,
  featureInsights,
  featureInsightsLoading,
  featureInsightsError,
  presets,
  activePresetId,
  onPresetApply,
  onPresetSave,
  onPresetDelete,
  onEventFamilyChange,
  onTemporalScopeChange,
  onEventTypeChange,
  onToggleField,
}) => {
  const [presetName, setPresetName] = useState('');

  const correlationLookup = useMemo(() => {
    const lookup = new Map<string, number>();
    (featureInsights?.correlations || []).forEach((entry) => {
      lookup.set(`${entry.left}::${entry.right}`, entry.coefficient);
      lookup.set(`${entry.right}::${entry.left}`, entry.coefficient);
    });
    return lookup;
  }, [featureInsights]);

  const activeCorrelationFields = featureInsights?.selectedFields?.length
    ? featureInsights.selectedFields
    : selectedInsightFields;

  const topCorrelations = (featureInsights?.correlations || []).slice(0, 6);

  return (
    <div className="bg-slate-800 rounded-xl p-6 space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-xl font-semibold flex items-center">
            <BarChart3 className="h-6 w-6 mr-2 text-cyan-400" />
            {title}
          </h3>
          <p className="mt-2 text-sm text-slate-400 max-w-3xl">{description}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-200">
            {filteredAlgorithmsCount} models in lens
          </span>
          <span className="px-3 py-1 rounded-full border border-green-500/30 bg-green-500/10 text-green-200">
            {filteredDatasetsCount} datasets in lens
          </span>
        </div>
      </div>

      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 space-y-4">
        <div>
          <div className="text-sm font-semibold text-white">Saved Lens Presets</div>
          <div className="mt-1 text-xs text-slate-500">Reopen common analytical slices or save your current lens for reuse.</div>
        </div>
        <div className="flex flex-wrap gap-2">
          {presets.map((preset) => (
            <div key={preset.id} className="flex items-center gap-1">
              <button
                onClick={() => onPresetApply(preset.id)}
                className={`rounded-full px-3 py-1 text-xs transition-colors ${
                  activePresetId === preset.id
                    ? 'bg-cyan-500 text-slate-950'
                    : 'border border-slate-700 bg-slate-800 text-slate-300 hover:border-cyan-400 hover:text-white'
                }`}
              >
                {preset.name}
              </button>
              {!preset.isDefault && (
                <button
                  onClick={() => onPresetDelete(preset.id)}
                  className="rounded-full border border-slate-700 bg-slate-800 p-1 text-slate-400 hover:text-red-300"
                  title={`Delete ${preset.name}`}
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              )}
            </div>
          ))}
        </div>
        <div className="flex flex-col gap-2 lg:flex-row">
          <input
            type="text"
            value={presetName}
            onChange={(event) => setPresetName(event.target.value)}
            placeholder="Save current lens as..."
            className="flex-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
          />
          <button
            onClick={() => {
              if (!presetName.trim()) {
                return;
              }
              onPresetSave(presetName.trim());
              setPresetName('');
            }}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition-colors hover:bg-cyan-400"
          >
            <Save className="h-4 w-4" />
            Save Preset
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <label className="block rounded-lg border border-slate-700 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">Event Family</div>
          <select
            value={selectedEventFamily}
            onChange={(event) => onEventFamilyChange(event.target.value)}
            className="mt-2 w-full bg-transparent text-sm text-white outline-none"
          >
            <option value="all">All Event Families</option>
            {eventFamilyOptions.map((option) => (
              <option key={option} value={option}>{prettifyLensToken(option)}</option>
            ))}
          </select>
        </label>

        <label className="block rounded-lg border border-slate-700 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">Temporal Scope</div>
          <select
            value={selectedTemporalScope}
            onChange={(event) => onTemporalScopeChange(event.target.value)}
            className="mt-2 w-full bg-transparent text-sm text-white outline-none"
          >
            <option value="all">All Temporal Scopes</option>
            {temporalScopeOptions.map((option) => (
              <option key={option} value={option}>{prettifyLensToken(option)}</option>
            ))}
          </select>
        </label>

        <label className="block rounded-lg border border-slate-700 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">Event Type</div>
          <select
            value={selectedEventType}
            onChange={(event) => onEventTypeChange(event.target.value)}
            disabled={!featureInsights || featureInsights.availableEventTypes.length === 0}
            className="mt-2 w-full bg-transparent text-sm text-white outline-none disabled:text-slate-500"
          >
            <option value="all">All Event Types</option>
            {(featureInsights?.availableEventTypes || []).map((eventType) => (
              <option key={eventType} value={eventType}>{prettifyLensToken(eventType)}</option>
            ))}
          </select>
          <div className="mt-2 text-xs text-slate-500">
            {(featureInsights?.availableEventTypes || []).length > 0
              ? 'Switch between shot, pass, carry, and other live event slices.'
              : 'Aggregate datasets do not expose per-event typing.'}
          </div>
        </label>

        <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">Active Dataset Lens</div>
          <div className="mt-2 text-sm font-semibold text-white">{activeDatasetName || 'No dataset selected'}</div>
          <div className="mt-2 text-xs text-slate-500">
            {(featureInsights?.sampleSize || 0) > 0
              ? `${featureInsights?.sampleSize} sampled rows at ${prettifyLensToken(featureInsights.activeTemporalScope)} scope.`
              : 'Select a dataset lens to inspect parameter relationships.'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr,1.1fr]">
        <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-lg font-semibold text-white">Selectable Parameters</div>
              <div className="mt-1 text-sm text-slate-400">Choose up to six fields to inspect how they correlate with each other.</div>
            </div>
            {featureInsightsLoading && <RefreshCw className="h-4 w-4 animate-spin text-cyan-300" />}
          </div>

          {featureInsightsError && (
            <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {featureInsightsError}
            </div>
          )}

          {!featureInsightsError && !featureInsightsLoading && featureInsights && featureInsights.featureStats.length === 0 && (
            <div className="mt-4 rounded-lg border border-slate-700 bg-slate-800/70 px-4 py-5 text-sm text-slate-400">
              No numeric fields were available for the current lens. Try another dataset or widen the filters.
            </div>
          )}

          {featureInsights && featureInsights.featureStats.length > 0 && (
            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              {featureInsights.featureStats.slice(0, 16).map((entry) => {
                const isSelected = selectedInsightFields.includes(entry.field);
                return (
                  <button
                    key={entry.field}
                    onClick={() => onToggleField(entry.field)}
                    className={`rounded-lg border p-4 text-left transition-colors ${
                      isSelected
                        ? 'border-cyan-400 bg-cyan-500/10'
                        : 'border-slate-700 bg-slate-800/70 hover:border-slate-500'
                    }`}
                  >
                    <div className="text-sm font-semibold text-white">{prettifyLensToken(entry.field.replace(/\./g, '_'))}</div>
                    <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
                      <span>Coverage {(entry.coverage * 100).toFixed(0)}%</span>
                      <span>•</span>
                      <span>Mean {formatInsightNumber(entry.mean)}</span>
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      Min {formatInsightNumber(entry.min)} • Max {formatInsightNumber(entry.max)}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
          <div>
            <div className="text-lg font-semibold text-white">Correlation Explorer</div>
            <div className="mt-1 text-sm text-slate-400">A Pearson view over the currently selected dataset slice and temporal scope.</div>
          </div>

          {activeCorrelationFields.length < 2 ? (
            <div className="mt-4 rounded-lg border border-slate-700 bg-slate-800/70 px-4 py-5 text-sm text-slate-400">
              Select at least two parameters to render the correlation matrix.
            </div>
          ) : (
            <div className="mt-4 space-y-5">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr>
                      <th className="px-2 py-2 text-left text-slate-500">Field</th>
                      {activeCorrelationFields.map((field) => (
                        <th key={field} className="px-2 py-2 text-left text-slate-500 whitespace-nowrap">{prettifyLensToken(field.replace(/\./g, '_'))}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {activeCorrelationFields.map((rowField) => (
                      <tr key={rowField} className="border-t border-slate-800">
                        <td className="px-2 py-2 font-medium text-white whitespace-nowrap">{prettifyLensToken(rowField.replace(/\./g, '_'))}</td>
                        {activeCorrelationFields.map((columnField) => {
                          const coefficient = rowField === columnField
                            ? 1
                            : correlationLookup.get(`${rowField}::${columnField}`);

                          return (
                            <td key={`${rowField}-${columnField}`} className="px-2 py-2">
                              <div className={`inline-flex min-w-[72px] items-center justify-center rounded px-2 py-1 text-xs font-semibold ${correlationTone(coefficient ?? 0)}`}>
                                {coefficient === undefined ? 'n/a' : coefficient.toFixed(2)}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div>
                <div className="text-sm font-semibold text-white">Strongest Relationships In This Slice</div>
                <div className="mt-3 space-y-2">
                  {topCorrelations.length === 0 && (
                    <div className="text-sm text-slate-400">No stable pairwise relationships were available for the current selection.</div>
                  )}
                  {topCorrelations.map((entry) => (
                    <div key={`${entry.left}-${entry.right}`} className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/70 px-4 py-3 text-sm">
                      <div>
                        <div className="font-medium text-white">
                          {prettifyLensToken(entry.left.replace(/\./g, '_'))} vs {prettifyLensToken(entry.right.replace(/\./g, '_'))}
                        </div>
                        <div className="mt-1 text-xs text-slate-500">{entry.sampleSize} overlapping samples</div>
                      </div>
                      <div className={`rounded px-2 py-1 text-xs font-semibold ${correlationTone(entry.coefficient)}`}>
                        {entry.coefficient.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeatureLensExplorer;