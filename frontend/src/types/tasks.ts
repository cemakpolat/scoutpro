export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

export type TaskType =
  | 'ml_predict'
  | 'ml_train'
  | 'report_generate'
  | 'data_export'
  | 'data_sync'
  | 'video_analysis';

export interface BackgroundTask {
  task_id: string;
  task_type: TaskType;
  status: TaskStatus;
  progress: number;
  progress_msg: string;
  result?: unknown;
  result_ref?: { storage: string; bucket: string; key: string };
  error?: string;
  created_at?: string;
  completed_at?: string;
}

export interface TaskResult {
  task_id: string;
  status: TaskStatus;
  result?: unknown;
  download_url?: string;
}
