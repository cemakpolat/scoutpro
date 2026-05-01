import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Download,
  X,
  Cpu,
  FileText,
  Database,
  RefreshCcw,
  Video,
} from 'lucide-react';
import apiService from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { BackgroundTask, TaskType } from '../types/tasks';

// ── helpers ──────────────────────────────────────────────────────────────────

function taskIcon(type: TaskType) {
  switch (type) {
    case 'ml_predict':
    case 'ml_train':
      return <Cpu className="h-4 w-4" />;
    case 'report_generate':
      return <FileText className="h-4 w-4" />;
    case 'data_export':
      return <Database className="h-4 w-4" />;
    case 'data_sync':
      return <RefreshCcw className="h-4 w-4" />;
    case 'video_analysis':
      return <Video className="h-4 w-4" />;
    default:
      return <Cpu className="h-4 w-4" />;
  }
}

function taskLabel(type: TaskType): string {
  const labels: Record<TaskType, string> = {
    ml_predict: 'ML Prediction',
    ml_train: 'ML Training',
    report_generate: 'Report Generation',
    data_export: 'Data Export',
    data_sync: 'Data Sync',
    video_analysis: 'Video Analysis',
  };
  return labels[type] ?? type;
}

function statusBadge(status: string) {
  switch (status) {
    case 'completed':
      return (
        <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 border border-green-500/30">
          <CheckCircle className="h-3 w-3" /> Done
        </span>
      );
    case 'running':
      return (
        <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30">
          <Loader2 className="h-3 w-3 animate-spin" /> Running
        </span>
      );
    case 'failed':
      return (
        <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30">
          <AlertCircle className="h-3 w-3" /> Failed
        </span>
      );
    default:
      return (
        <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-slate-500/15 text-slate-400 border border-slate-500/30">
          <Clock className="h-3 w-3" /> Pending
        </span>
      );
  }
}

function timeAgo(iso?: string): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  return `${Math.floor(diff / 3_600_000)}h ago`;
}

// ── sub-components ────────────────────────────────────────────────────────────

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-1 w-full bg-slate-700 rounded-full overflow-hidden">
      <div
        className="h-full bg-blue-500 transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

function TaskRow({ task, onResultClick }: { task: BackgroundTask; onResultClick: (t: BackgroundTask) => void }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-slate-700 rounded-lg bg-slate-800 overflow-hidden">
      <button
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-750 transition-colors text-left"
        onClick={() => setExpanded((p) => !p)}
      >
        <span className="text-slate-400">{taskIcon(task.task_type)}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-white">{taskLabel(task.task_type)}</span>
            {statusBadge(task.status)}
          </div>
          <div className="text-xs text-slate-500 mt-0.5 truncate">
            ID: {task.task_id.slice(0, 8)}… · {timeAgo(task.created_at)}
          </div>
        </div>
        {task.status === 'running' && (
          <span className="text-xs text-blue-400 whitespace-nowrap">{task.progress}%</span>
        )}
        {task.status === 'completed' && task.result && (
          <button
            onClick={(e) => { e.stopPropagation(); onResultClick(task); }}
            className="flex items-center gap-1 text-xs text-green-400 hover:text-green-300 px-2 py-1 rounded border border-green-500/30 transition-colors"
          >
            <Download className="h-3 w-3" /> Result
          </button>
        )}
        {expanded ? <ChevronUp className="h-4 w-4 text-slate-500 flex-shrink-0" /> : <ChevronDown className="h-4 w-4 text-slate-500 flex-shrink-0" />}
      </button>

      {task.status === 'running' && (
        <div className="px-4 pb-2">
          <ProgressBar value={task.progress} />
          <p className="text-xs text-slate-500 mt-1">{task.progress_msg}</p>
        </div>
      )}

      {expanded && (
        <div className="border-t border-slate-700 px-4 py-3 space-y-2 text-xs text-slate-400">
          {task.error && (
            <div className="bg-red-900/20 border border-red-500/30 rounded p-2 text-red-400">
              {task.error}
            </div>
          )}
          {task.result && (
            <pre className="bg-slate-900 rounded p-2 overflow-x-auto text-slate-300 max-h-40">
              {JSON.stringify(task.result, null, 2)}
            </pre>
          )}
          <div className="flex gap-4 text-slate-500">
            {task.created_at && <span>Created: {new Date(task.created_at).toLocaleString()}</span>}
            {task.completed_at && <span>Completed: {new Date(task.completed_at).toLocaleString()}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

// ── submission form ───────────────────────────────────────────────────────────

type TaskFormState = {
  task_type: TaskType;
  algorithm?: string;
  action?: 'predict' | 'train';
  report_type?: string;
  entity_id?: string;
  export_type?: string;
  format?: string;
  provider?: string;
  video_id?: string;
  analysis_type?: string;
};

function SubmitTaskForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [form, setForm] = useState<TaskFormState>({ task_type: 'ml_predict', action: 'predict' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (k: keyof TaskFormState, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const buildPayload = (): Record<string, unknown> => {
    switch (form.task_type) {
      case 'ml_predict':
      case 'ml_train':
        return { algorithm: form.algorithm || 'player_clustering', action: form.action || 'predict', input_data: {} };
      case 'report_generate':
        return { report_type: form.report_type || 'player', entity_id: form.entity_id || '', format: 'pdf' };
      case 'data_export':
        return { export_type: form.export_type || 'players', format: form.format || 'csv', filters: {} };
      case 'data_sync':
        return { provider: form.provider || 'statsbomb' };
      case 'video_analysis':
        return { video_id: form.video_id || '', analysis_type: form.analysis_type || 'highlight' };
      default:
        return {};
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await apiService.submitTask(form.task_type, buildPayload());
      if (!res.success) throw new Error(res.error?.message ?? 'Unknown error');
      onSubmitted();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit task');
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = 'w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500';
  const labelClass = 'block text-xs font-medium text-slate-400 mb-1';

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className={labelClass}>Task type</label>
        <select className={inputClass} value={form.task_type} onChange={(e) => update('task_type', e.target.value as TaskType)}>
          <option value="ml_predict">ML Prediction</option>
          <option value="ml_train">ML Training</option>
          <option value="report_generate">Report Generation</option>
          <option value="data_export">Data Export</option>
          <option value="data_sync">Data Sync</option>
          <option value="video_analysis">Video Analysis</option>
        </select>
      </div>

      {(form.task_type === 'ml_predict' || form.task_type === 'ml_train') && (
        <>
          <div>
            <label className={labelClass}>Algorithm</label>
            <select className={inputClass} value={form.algorithm} onChange={(e) => update('algorithm', e.target.value)}>
              <option value="player_clustering">Player Clustering</option>
              <option value="tactical_role_classifier">Tactical Role Classifier</option>
              <option value="performance_anomaly_detector">Performance Anomaly</option>
              <option value="fatigue_risk_predictor">Fatigue Risk</option>
              <option value="advanced_player_similarity">Player Similarity</option>
              <option value="expected_threat_model">Expected Threat (xT)</option>
              <option value="goals_linear_regression">Goals Regression</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Action</label>
            <select className={inputClass} value={form.action} onChange={(e) => update('action', e.target.value as 'predict' | 'train')}>
              <option value="predict">Predict</option>
              <option value="train">Train</option>
            </select>
          </div>
        </>
      )}

      {form.task_type === 'report_generate' && (
        <>
          <div>
            <label className={labelClass}>Report type</label>
            <select className={inputClass} value={form.report_type} onChange={(e) => update('report_type', e.target.value)}>
              <option value="player">Player</option>
              <option value="team">Team</option>
              <option value="match">Match</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Entity ID</label>
            <input className={inputClass} value={form.entity_id ?? ''} onChange={(e) => update('entity_id', e.target.value)} placeholder="player / team / match ID" />
          </div>
        </>
      )}

      {form.task_type === 'data_export' && (
        <>
          <div>
            <label className={labelClass}>Export type</label>
            <select className={inputClass} value={form.export_type} onChange={(e) => update('export_type', e.target.value)}>
              <option value="players">Players</option>
              <option value="matches">Matches</option>
              <option value="events">Events</option>
              <option value="statistics">Statistics</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Format</label>
            <select className={inputClass} value={form.format ?? 'csv'} onChange={(e) => update('format', e.target.value)}>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>
        </>
      )}

      {form.task_type === 'data_sync' && (
        <div>
          <label className={labelClass}>Provider</label>
          <select className={inputClass} value={form.provider ?? 'statsbomb'} onChange={(e) => update('provider', e.target.value)}>
            <option value="statsbomb">StatsBomb</option>
            <option value="opta">Opta</option>
            <option value="all">All</option>
          </select>
        </div>
      )}

      {form.task_type === 'video_analysis' && (
        <>
          <div>
            <label className={labelClass}>Video ID</label>
            <input className={inputClass} value={form.video_id ?? ''} onChange={(e) => update('video_id', e.target.value)} placeholder="Video identifier" />
          </div>
          <div>
            <label className={labelClass}>Analysis type</label>
            <select className={inputClass} value={form.analysis_type ?? 'highlight'} onChange={(e) => update('analysis_type', e.target.value)}>
              <option value="highlight">Highlight</option>
              <option value="heatmap">Heatmap</option>
              <option value="full">Full analysis</option>
            </select>
          </div>
        </>
      )}

      {error && <p className="text-xs text-red-400 bg-red-900/20 border border-red-500/30 rounded px-3 py-2">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
      >
        {submitting ? <><Loader2 className="h-4 w-4 animate-spin" /> Submitting…</> : 'Submit Task'}
      </button>
    </form>
  );
}

// ── main component ────────────────────────────────────────────────────────────

const POLL_INTERVAL_MS = 5000;

export default function TaskQueue() {
  const [tasks, setTasks] = useState<BackgroundTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [resultModal, setResultModal] = useState<{ task: BackgroundTask; downloadUrl?: string } | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { subscribe } = useWebSocket();

  const fetchTasks = useCallback(async () => {
    try {
      const res = await apiService.listTasks(50);
      if (res.success && res.data) setTasks(res.data);
    } catch {
      // silently tolerate errors (task-worker-service may be down)
    } finally {
      setLoading(false);
    }
  }, []);

  // Real-time: refresh immediately when a task completes via WebSocket
  useEffect(() => {
    subscribe('task_completed', () => fetchTasks());
  }, [subscribe, fetchTasks]);

  useEffect(() => {
    fetchTasks();
    timerRef.current = setInterval(fetchTasks, POLL_INTERVAL_MS);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [fetchTasks]);

  const handleResultClick = useCallback(async (task: BackgroundTask) => {
    try {
      const res = await apiService.getTaskResult(task.task_id);
      if (res.success && res.data) {
        setResultModal({ task, downloadUrl: res.data.download_url });
      }
    } catch {
      setResultModal({ task });
    }
  }, []);

  const pending = tasks.filter((t) => t.status === 'pending').length;
  const running = tasks.filter((t) => t.status === 'running').length;
  const completed = tasks.filter((t) => t.status === 'completed').length;
  const failed = tasks.filter((t) => t.status === 'failed').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Cpu className="h-8 w-8 text-blue-500" />
          Background Tasks
        </h1>
        <div className="flex items-center gap-3">
          <button onClick={fetchTasks} className="p-2 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors">
            <RefreshCw className="h-4 w-4 text-slate-400" />
          </button>
          <button
            onClick={() => setShowForm((p) => !p)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
          >
            {showForm ? <X className="h-4 w-4" /> : <Cpu className="h-4 w-4" />}
            {showForm ? 'Cancel' : 'New Task'}
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Pending', value: pending, color: 'text-slate-400' },
          { label: 'Running', value: running, color: 'text-blue-400' },
          { label: 'Completed', value: completed, color: 'text-green-400' },
          { label: 'Failed', value: failed, color: 'text-red-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-center">
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-slate-500 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Submit form */}
      {showForm && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
          <h2 className="text-base font-semibold mb-4">Submit a background task</h2>
          <SubmitTaskForm onSubmitted={() => { setShowForm(false); fetchTasks(); }} />
        </div>
      )}

      {/* Task list */}
      <div className="space-y-2">
        {loading && tasks.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading tasks…
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-16 text-slate-400 border border-slate-700 rounded-xl bg-slate-800">
            No tasks yet. Submit one using the "New Task" button.
          </div>
        ) : (
          tasks.map((task) => (
            <TaskRow key={task.task_id} task={task} onResultClick={handleResultClick} />
          ))
        )}
      </div>

      {/* Result modal */}
      {resultModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-lg w-full mx-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold">Task result</h3>
              <button onClick={() => setResultModal(null)} className="p-1 rounded hover:bg-slate-700 transition-colors">
                <X className="h-4 w-4" />
              </button>
            </div>
            {resultModal.downloadUrl ? (
              <a
                href={resultModal.downloadUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-medium transition-colors"
              >
                <Download className="h-4 w-4" /> Download file
              </a>
            ) : (
              <pre className="bg-slate-900 rounded-lg p-3 text-xs text-slate-300 overflow-x-auto max-h-72">
                {JSON.stringify(resultModal.task.result, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
