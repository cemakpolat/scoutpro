import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { API_BASE_URL } from '../config/api';
import {
  ExportOptions,
  PDFExportOptions,
  ExcelExportOptions,
  CSVExportOptions,
  ExportHistory,
  ReportTemplate,
  ScheduledReport,
  ExportJob,
  ExportFormat,
} from '../types/export';

class ExportService {
  private readonly STORAGE_KEY = 'scoutpro_export_history';
  private exportJobs: Map<string, ExportJob> = new Map();

  private async exportLocally(options: ExportOptions): Promise<{ blob: Blob; mimeType: string }> {
    switch (options.format) {
      case 'pdf':
        return {
          blob: await this.exportToPDF(options as PDFExportOptions),
          mimeType: 'application/pdf',
        };
      case 'excel':
        return {
          blob: await this.exportToExcel(options as ExcelExportOptions),
          mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        };
      case 'csv':
        return {
          blob: await this.exportToCSV(options as CSVExportOptions),
          mimeType: 'text/csv',
        };
      case 'json':
        return {
          blob: await this.exportToJSON(options),
          mimeType: 'application/json',
        };
      default:
        throw new Error(`Unsupported export format: ${options.format}`);
    }
  }

  /**
   * Main export function that routes to specific format handlers
   */
  async export(options: ExportOptions): Promise<ExportJob> {
    const jobId = `export-${Date.now()}`;
    const job: ExportJob = {
      id: jobId,
      status: 'processing',
      progress: 0,
      fileName: options.fileName || `export-${Date.now()}.${options.format}`,
      format: options.format,
      createdAt: new Date().toISOString(),
    };

    this.exportJobs.set(jobId, job);

    try {
      let blob: Blob;
      let mimeType: string;

      try {
        const baseUrl = API_BASE_URL;
        const response = await fetch(`${baseUrl}/v2/exports/custom`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            data: options.data,
            format: options.format,
            fileName: options.fileName,
            header: 'header' in options ? options.header : undefined,
          })
        });

        if (!response.ok) {
          throw new Error('Backend export failed: ' + response.statusText);
        }

        blob = await response.blob();
        mimeType = response.headers.get('Content-Type') || 'application/octet-stream';
      } catch (backendError) {
        console.warn('Backend export unavailable, falling back to local export:', backendError);
        const localExport = await this.exportLocally(options);
        blob = localExport.blob;
        mimeType = localExport.mimeType;
      }

      // Create download URL
      const downloadUrl = URL.createObjectURL(blob);

      // Update job
      job.status = 'completed';
      job.progress = 100;
      job.downloadUrl = downloadUrl;
      job.completedAt = new Date().toISOString();

      this.exportJobs.set(jobId, job);

      // Add to history
      this.addToHistory({
        id: jobId,
        fileName: job.fileName,
        format: options.format,
        status: 'completed',
        downloadUrl,
        size: blob.size,
        createdAt: job.createdAt,
      });

      // Trigger download
      if (typeof window !== 'undefined') {
        this.downloadBlob(blob, job.fileName, mimeType);
      }

      return job;
    } catch (error) {
      console.error('Export error:', error);
      job.status = 'failed';
      job.error = error instanceof Error ? error.message : 'Export failed';
      this.exportJobs.set(jobId, job);
      throw error;
    }
  }

  /**
   * Export to PDF format using jsPDF
   */
  private async exportToPDF(options: PDFExportOptions): Promise<Blob> {
    const { branding, header, footer } = options;
    const primaryColor = branding?.colors?.primary || '#10b981';

    // Create PDF document
    const doc = new jsPDF({
      orientation: options.pageOrientation || 'portrait',
      unit: 'mm',
      format: options.pageSize || 'a4',
    });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    let yPosition = 20;

    // Company branding header
    doc.setFillColor(primaryColor);
    doc.rect(0, 0, pageWidth, 15, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.text(branding?.companyName || 'ScoutPro', 15, 10);

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, pageWidth - 15, 10, { align: 'right' });

    yPosition = 25;

    // Report title
    if (header) {
      doc.setTextColor(0, 0, 0);
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text(header, 15, yPosition);
      yPosition += 10;
    }

    // Separator line
    doc.setDrawColor(200, 200, 200);
    doc.line(15, yPosition, pageWidth - 15, yPosition);
    yPosition += 8;

    // Process data
    if (Array.isArray(options.data) && options.data.length > 0) {
      // Table data
      const headers = Object.keys(options.data[0]);
      const tableData = options.data.map(row => headers.map(h => String(row[h] || '-')));

      autoTable(doc, {
        head: [headers],
        body: tableData,
        startY: yPosition,
        theme: 'striped',
        headStyles: {
          fillColor: primaryColor,
          textColor: 255,
          fontStyle: 'bold',
          fontSize: 10,
        },
        bodyStyles: {
          fontSize: 9,
          textColor: 50,
        },
        alternateRowStyles: {
          fillColor: [245, 245, 245],
        },
        margin: { left: 15, right: 15 },
        styles: {
          overflow: 'linebreak',
          cellPadding: 3,
        },
        columnStyles: {
          // Auto-adjust column widths
        },
      });

      yPosition = (doc as any).lastAutoTable.finalY + 10;
    } else if (typeof options.data === 'object') {
      // Key-value pairs
      const entries = Object.entries(options.data);
      const tableData = entries.map(([key, value]) => [key, String(value)]);

      autoTable(doc, {
        head: [['Property', 'Value']],
        body: tableData,
        startY: yPosition,
        theme: 'striped',
        headStyles: {
          fillColor: primaryColor,
          textColor: 255,
          fontStyle: 'bold',
        },
        margin: { left: 15, right: 15 },
      });

      yPosition = (doc as any).lastAutoTable.finalY + 10;
    }

    // Footer
    const footerText = footer || `© ${new Date().getFullYear()} ScoutPro. All rights reserved.`;
    doc.setFontSize(8);
    doc.setTextColor(100, 100, 100);
    doc.text(footerText, pageWidth / 2, pageHeight - 10, { align: 'center' });

    // Add page numbers
    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(100, 100, 100);
      doc.text(`Page ${i} of ${pageCount}`, pageWidth - 15, pageHeight - 10, { align: 'right' });
    }

    // Convert to blob
    return doc.output('blob');
  }

  /**
   * Generate HTML for PDF export
   */
  private generatePDFHTML(options: PDFExportOptions): string {
    const { branding, header, footer, sections } = options;

    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>${options.fileName || 'ScoutPro Report'}</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
              font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
              padding: 40px;
              background: white;
              color: #1e293b;
            }
            .header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding-bottom: 20px;
              border-bottom: 3px solid ${branding?.colors?.primary || '#10b981'};
              margin-bottom: 30px;
            }
            .logo {
              font-size: 24px;
              font-weight: bold;
              color: ${branding?.colors?.primary || '#10b981'};
            }
            .date {
              color: #64748b;
              font-size: 14px;
            }
            h1 {
              font-size: 28px;
              margin-bottom: 10px;
              color: #0f172a;
            }
            h2 {
              font-size: 22px;
              margin: 25px 0 15px;
              color: #1e293b;
            }
            h3 {
              font-size: 18px;
              margin: 20px 0 10px;
              color: #334155;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 20px 0;
            }
            th, td {
              padding: 12px;
              text-align: left;
              border-bottom: 1px solid #e2e8f0;
            }
            th {
              background: #f1f5f9;
              font-weight: 600;
              color: #0f172a;
            }
            tr:hover {
              background: #f8fafc;
            }
            .divider {
              height: 2px;
              background: #e2e8f0;
              margin: 30px 0;
            }
            .footer {
              margin-top: 50px;
              padding-top: 20px;
              border-top: 1px solid #e2e8f0;
              text-align: center;
              color: #64748b;
              font-size: 12px;
            }
            @media print {
              body { padding: 20px; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">${branding?.companyName || 'ScoutPro'}</div>
            <div class="date">${new Date().toLocaleDateString()}</div>
          </div>

          ${header ? `<h1>${header}</h1>` : ''}

          ${sections?.map(section => this.renderPDFSection(section)).join('') || ''}

          <div class="footer">
            ${footer || `© ${new Date().getFullYear()} ScoutPro. All rights reserved.`}
          </div>
        </body>
      </html>
    `;
  }

  /**
   * Render a PDF section
   */
  private renderPDFSection(section: any): string {
    switch (section.type) {
      case 'title':
        return `<h2>${section.content}</h2>`;
      case 'text':
        return `<p style="margin: 10px 0; line-height: 1.6;">${section.content}</p>`;
      case 'table':
        return this.renderTable(section.data);
      case 'divider':
        return '<div class="divider"></div>';
      default:
        return '';
    }
  }

  /**
   * Render a table
   */
  private renderTable(data: any[]): string {
    if (!data || data.length === 0) return '';

    const headers = Object.keys(data[0]);
    return `
      <table>
        <thead>
          <tr>
            ${headers.map(h => `<th>${h}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${data.map(row => `
            <tr>
              ${headers.map(h => `<td>${row[h] ?? '-'}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  /**
   * Export to Excel format
   */
  private async exportToExcel(options: ExcelExportOptions): Promise<Blob> {
    // In production, use libraries like ExcelJS or SheetJS (xlsx)
    // For now, we'll create a CSV-compatible format that Excel can open

    const sheets = options.sheets || [{ name: 'Sheet1', data: options.data }];
    let content = '';

    sheets.forEach((sheet, index) => {
      if (index > 0) content += '\n\n';
      content += `Sheet: ${sheet.name}\n`;

      if (sheet.data && sheet.data.length > 0) {
        const headers = sheet.columns?.map(c => c.header) || Object.keys(sheet.data[0]);
        content += headers.join('\t') + '\n';

        sheet.data.forEach(row => {
          const values = sheet.columns?.map(c => row[c.key] ?? '') || Object.values(row);
          content += values.join('\t') + '\n';
        });
      }
    });

    return new Blob([content], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
  }

  /**
   * Export to CSV format
   */
  private async exportToCSV(options: CSVExportOptions): Promise<Blob> {
    const delimiter = options.delimiter || ',';
    const data = Array.isArray(options.data) ? options.data : [options.data];

    if (data.length === 0) {
      return new Blob([''], { type: 'text/csv' });
    }

    let csv = '';

    // Add headers
    if (options.includeHeaders !== false) {
      const headers = options.columns || Object.keys(data[0]);
      csv += headers.map(h => this.escapeCsvValue(h)).join(delimiter) + '\n';
    }

    // Add rows
    data.forEach(row => {
      const columns = options.columns || Object.keys(row);
      const values = columns.map(col => this.escapeCsvValue(row[col]));
      csv += values.join(delimiter) + '\n';
    });

    return new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  }

  /**
   * Escape CSV value
   */
  private escapeCsvValue(value: any): string {
    if (value === null || value === undefined) return '';
    const str = String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  }

  /**
   * Export to JSON format
   */
  private async exportToJSON(options: ExportOptions): Promise<Blob> {
    const json = JSON.stringify(options.data, null, 2);
    return new Blob([json], { type: 'application/json' });
  }

  /**
   * Download blob as file
   */
  private downloadBlob(blob: Blob, fileName: string, mimeType: string): void {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.type = mimeType;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up URL after a delay
    setTimeout(() => URL.revokeObjectURL(link.href), 100);
  }

  /**
   * Get export job status
   */
  getJobStatus(jobId: string): ExportJob | undefined {
    return this.exportJobs.get(jobId);
  }

  /**
   * Add to export history
   */
  private addToHistory(item: ExportHistory): void {
    const history = this.getExportHistory();
    history.unshift(item);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(history.slice(0, 50)));
  }

  /**
   * Get export history
   */
  getExportHistory(): ExportHistory[] {
    const history = localStorage.getItem(this.STORAGE_KEY);
    return history ? JSON.parse(history) : [];
  }

  /**
   * Clear export history
   */
  clearHistory(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }

  /**
   * Get available report templates
   */
  getReportTemplates(): ReportTemplate[] {
    return [
      {
        id: 'player-profile',
        name: 'Player Profile Report',
        description: 'Comprehensive player analysis with stats and performance',
        type: 'player',
        format: 'pdf',
        sections: [
          { type: 'title', content: 'Player Profile' },
          { type: 'text', content: 'Detailed player information and statistics' },
          { type: 'table', data: [] },
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isDefault: true,
      },
      {
        id: 'match-report',
        name: 'Match Analysis Report',
        description: 'Complete match statistics and tactical analysis',
        type: 'match',
        format: 'pdf',
        sections: [
          { type: 'title', content: 'Match Report' },
          { type: 'text', content: 'Match overview and key statistics' },
          { type: 'table', data: [] },
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isDefault: true,
      },
      {
        id: 'scouting-summary',
        name: 'Scouting Summary',
        description: 'Scouting observations and player evaluations',
        type: 'custom',
        format: 'pdf',
        sections: [
          { type: 'title', content: 'Scouting Report' },
          { type: 'text', content: 'Scout observations and ratings' },
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isDefault: true,
      },
      {
        id: 'team-comparison',
        name: 'Team Comparison',
        description: 'Side-by-side team statistics comparison',
        type: 'team',
        format: 'excel',
        sections: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isDefault: true,
      },
    ];
  }

  /**
   * Get scheduled reports
   */
  getScheduledReports(): ScheduledReport[] {
    const saved = localStorage.getItem('scoutpro_scheduled_reports');
    return saved ? JSON.parse(saved) : [];
  }

  /**
   * Save scheduled report
   */
  saveScheduledReport(report: Omit<ScheduledReport, 'id' | 'createdAt' | 'updatedAt'>): ScheduledReport {
    const reports = this.getScheduledReports();
    const newReport: ScheduledReport = {
      ...report,
      id: `scheduled-${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    reports.push(newReport);
    localStorage.setItem('scoutpro_scheduled_reports', JSON.stringify(reports));

    return newReport;
  }

  /**
   * Delete scheduled report
   */
  deleteScheduledReport(id: string): void {
    const reports = this.getScheduledReports().filter(r => r.id !== id);
    localStorage.setItem('scoutpro_scheduled_reports', JSON.stringify(reports));
  }

  /**
   * Quick export player data
   */
  async exportPlayer(player: any, format: ExportFormat = 'pdf'): Promise<ExportJob> {
    const data = {
      'Player Name': player.name,
      'Position': player.position,
      'Age': player.age,
      'Nationality': player.nationality,
      'Current Club': player.club,
      'Market Value': player.marketValue,
      'Height': player.height,
      'Preferred Foot': player.foot,
    };

    return this.export({
      format,
      fileName: `${player.name.replace(/\s+/g, '_')}_profile.${format}`,
      data: [data],
    });
  }

  /**
   * Quick export match data
   */
  async exportMatch(match: any, format: ExportFormat = 'pdf'): Promise<ExportJob> {
    return this.export({
      format,
      fileName: `match_${match.id}_report.${format}`,
      data: match,
    });
  }

  /**
   * Quick export search results
   */
  async exportSearchResults(results: any[], format: ExportFormat = 'csv'): Promise<ExportJob> {
    return this.export({
      format,
      fileName: `search_results_${Date.now()}.${format}`,
      data: results,
    });
  }
}

export const exportService = new ExportService();
