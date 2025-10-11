// Data Import/Export Types

export type ImportType = 'players' | 'matches' | 'stats' | 'videos';
export type ImportStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'partial';
export type ImportFormat = 'csv' | 'excel' | 'json';

export interface ImportJob {
  id: string;
  type: ImportType;
  format: ImportFormat;
  fileName: string;
  fileSize: number;
  totalRows: number;
  processedRows: number;
  successRows: number;
  failedRows: number;
  status: ImportStatus;
  errors: ImportError[];
  mapping?: ColumnMapping;
  createdBy: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  progress: number; // 0-100
}

export interface ImportError {
  row: number;
  column?: string;
  error: string;
  value?: any;
}

export interface ColumnMapping {
  [csvColumn: string]: string; // maps CSV column to entity field
}

export interface ImportPreview {
  headers: string[];
  rows: any[][];
  totalRows: number;
  suggestedMapping?: ColumnMapping;
}

export interface DataValidation {
  field: string;
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ImportTemplate {
  id: string;
  name: string;
  type: ImportType;
  description: string;
  requiredFields: string[];
  optionalFields: string[];
  sampleData: any[];
  mapping: ColumnMapping;
}

export interface APIIntegration {
  id: string;
  name: string;
  type: 'opta' | 'statsbomb' | 'wyscout' | 'custom';
  apiKey: string;
  endpoint: string;
  isActive: boolean;
  lastSync?: string;
  syncFrequency?: 'manual' | 'hourly' | 'daily' | 'weekly';
  createdAt: string;
  updatedAt: string;
}

export interface BulkOperation {
  id: string;
  operation: 'update' | 'delete' | 'create';
  entityType: ImportType;
  affectedIds: string[];
  changes?: Record<string, any>;
  status: ImportStatus;
  createdBy: string;
  createdAt: string;
  completedAt?: string;
}
