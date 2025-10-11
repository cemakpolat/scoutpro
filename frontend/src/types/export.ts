// Export and reporting types

export type ExportFormat = 'pdf' | 'excel' | 'csv' | 'json';
export type ExportStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ExportOptions {
  format: ExportFormat;
  fileName?: string;
  data: any;
  template?: string;
  includeCharts?: boolean;
  includeLogo?: boolean;
  pageOrientation?: 'portrait' | 'landscape';
  pageSize?: 'A4' | 'Letter' | 'Legal';
}

export interface PDFExportOptions extends ExportOptions {
  format: 'pdf';
  header?: string;
  footer?: string;
  branding?: {
    logo?: string;
    companyName?: string;
    colors?: {
      primary?: string;
      secondary?: string;
    };
  };
  sections?: PDFSection[];
}

export interface PDFSection {
  type: 'title' | 'text' | 'table' | 'chart' | 'image' | 'divider';
  content?: any;
  title?: string;
  data?: any;
  chartType?: 'bar' | 'line' | 'pie' | 'radar';
  imageUrl?: string;
  style?: Record<string, any>;
}

export interface ExcelExportOptions extends ExportOptions {
  format: 'excel';
  sheets?: ExcelSheet[];
  sheetName?: string;
}

export interface ExcelSheet {
  name: string;
  data: any[];
  columns?: ExcelColumn[];
  formatting?: {
    headerStyle?: Record<string, any>;
    alternateRows?: boolean;
    freezeHeader?: boolean;
  };
}

export interface ExcelColumn {
  header: string;
  key: string;
  width?: number;
  style?: Record<string, any>;
}

export interface CSVExportOptions extends ExportOptions {
  format: 'csv';
  delimiter?: ',' | ';' | '\t';
  includeHeaders?: boolean;
  columns?: string[];
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  type: 'player' | 'match' | 'team' | 'custom';
  format: ExportFormat;
  sections: PDFSection[];
  createdAt: string;
  updatedAt: string;
  isDefault?: boolean;
}

export interface ScheduledReport {
  id: string;
  name: string;
  description?: string;
  template: string; // template ID
  schedule: {
    frequency: 'daily' | 'weekly' | 'monthly' | 'custom';
    dayOfWeek?: number; // 0-6
    dayOfMonth?: number; // 1-31
    time?: string; // HH:mm
    cronExpression?: string;
  };
  recipients: string[]; // email addresses
  format: ExportFormat;
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ExportHistory {
  id: string;
  fileName: string;
  format: ExportFormat;
  status: ExportStatus;
  downloadUrl?: string;
  size?: number; // in bytes
  createdAt: string;
  expiresAt?: string;
  error?: string;
}

export interface ExportJob {
  id: string;
  status: ExportStatus;
  progress: number; // 0-100
  fileName: string;
  format: ExportFormat;
  createdAt: string;
  completedAt?: string;
  downloadUrl?: string;
  error?: string;
}
