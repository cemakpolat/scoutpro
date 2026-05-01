import {
  ApiResponse,
  ApiError,
  Player,
  Match,
  Team,
  League,
  Notification,
  Analytics,
  AIInsight,
  MarketTrend,
  PlayerFilters,
  MatchFilters,
  QueryParams,
  MLAlgorithm,
  MLDataset,
  MLExperiment
} from '../types';
import { CalendarEvent, MatchSchedule, ScoutingTrip } from '../types/calendar';
import { Activity as CollaborationActivity, Task, Workspace } from '../types/collaboration';
import { SavedSearch, SearchHistory } from '../types/search';

import { API_BASE_URL } from '../config/api';

class ApiService {
  private baseUrl: string;
  private apiKey: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.apiKey = import.meta.env.VITE_API_KEY || '';
  }

  private normalizeRequestBody(body: RequestInit['body'], contentType: string | null): RequestInit['body'] {
    if (!body || !contentType?.includes('application/json')) {
      return body;
    }

    if (
      typeof body === 'string' ||
      body instanceof FormData ||
      body instanceof Blob ||
      body instanceof URLSearchParams ||
      body instanceof ArrayBuffer
    ) {
      return body;
    }

    return JSON.stringify(body);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = new Headers(options.headers);
      const isFormData = options.body instanceof FormData;
      const authToken = typeof window !== 'undefined' ? localStorage.getItem('scoutpro_token') : null;

      if (authToken && !headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${authToken}`);
      } else if (this.apiKey && !headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${this.apiKey}`);
      }

      if (!isFormData && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
      }

      const body = this.normalizeRequestBody(options.body, headers.get('Content-Type'));

      const response = await fetch(url, {
        ...options,
        headers,
        body,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          success: false,
          error: {
            code: response.status.toString(),
            message: errorData.message || `HTTP ${response.status}: ${response.statusText}`,
            details: errorData
          }
        };
      }

      let data: T;

      if (response.status === 204) {
        data = undefined as T;
      } else {
        const contentType = response.headers.get('content-type') || '';

        if (contentType.includes('application/json')) {
          data = await response.json();
        } else {
          const rawText = await response.text();
          data = (rawText ? rawText : undefined) as T;
        }
      }

      return {
        success: true,
        data,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'api'
        }
      };
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: error instanceof Error ? error.message : 'Network request failed',
          details: error
        }
      };
    }
  }

  // Player endpoints
  async getPlayers(filters?: PlayerFilters, queryParams?: QueryParams): Promise<ApiResponse<Player[]>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    if (queryParams?.search?.trim()) {
      params.set('search', queryParams.search.trim());
    }

    if (queryParams?.limit) {
      params.set('limit', String(queryParams.limit));
    }

    const queryString = params.toString();
    return this.request<Player[]>(`/players${queryString ? `?${queryString}` : ''}`);
  }

  async getPlayer(id: string): Promise<ApiResponse<Player>> {
    return this.request<Player>(`/players/${id}`);
  }

  async searchPlayers(query: string): Promise<ApiResponse<Player[]>> {
    return this.request<Player[]>(`/players/search?q=${encodeURIComponent(query)}`);
  }

  async createPlayer(player: Record<string, unknown>): Promise<ApiResponse<{ player_id: string }>> {
    return this.request<{ player_id: string }>('/players', {
      method: 'POST',
      body: player,
    });
  }

  // Match endpoints
  async getMatches(filters?: MatchFilters): Promise<ApiResponse<Match[]>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    const queryString = params.toString();
    return this.request<Match[]>(`/matches${queryString ? `?${queryString}` : ''}`);
  }

  async getMatch(id: string): Promise<ApiResponse<Match>> {
    return this.request<Match>(`/matches/${id}`);
  }

  async getLiveMatches(): Promise<ApiResponse<Match[]>> {
    return this.request<Match[]>('/matches/live');
  }

  async getMatchEvents(matchId: string): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/matches/${matchId}/events`);
  }

  async getMatchLineup(matchId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/matches/${matchId}/lineup`);
  }

  // Team endpoints
  async getTeams(): Promise<ApiResponse<Team[]>> {
    return this.request<Team[]>('/teams');
  }

  async getTeam(id: string): Promise<ApiResponse<Team>> {
    return this.request<Team>(`/teams/${id}`);
  }

  // League endpoints
  async getLeagues(): Promise<ApiResponse<League[]>> {
    return this.request<League[]>('/leagues');
  }

  async getLeague(id: string): Promise<ApiResponse<League>> {
    return this.request<League>(`/leagues/${id}`);
  }

  // Analytics endpoints
  async getAnalytics(type: string): Promise<ApiResponse<Analytics>> {
    return this.request<Analytics>(`/analytics/${type}`);
  }

  async getPlayerAnalytics(playerId: string): Promise<ApiResponse<Analytics>> {
    return this.request<Analytics>(`/analytics/player/${playerId}`);
  }

  async getMatchAnalytics(matchId: string): Promise<ApiResponse<Analytics>> {
    return this.request<Analytics>(`/analytics/match/${matchId}`);
  }

  // AI Insights endpoints
  async getAIInsights(type: string): Promise<ApiResponse<AIInsight[]>> {
    return this.request<AIInsight[]>(`/ai/insights/${type}`);
  }

  async getPlayerInsights(playerId: string): Promise<ApiResponse<AIInsight[]>> {
    return this.request<AIInsight[]>(`/ai/insights/player/${playerId}`);
  }

  // Market endpoints
  async getMarketTrends(): Promise<ApiResponse<MarketTrend[]>> {
    return this.request<MarketTrend[]>('/market/trends');
  }

  async getTransferPredictions(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/market/predictions');
  }

  // Notification endpoints
  async getNotifications(): Promise<ApiResponse<Notification[]>> {
    return this.request<Notification[]>('/notifications');
  }

  async markNotificationRead(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/notifications/${id}/read`, { method: 'PUT' });
  }

  // Tactical patterns endpoint
  async getTacticalPatterns(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/tactical/patterns');
  }

  async getTacticalOverview(formation?: string, phase?: string, matchId?: string): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (formation) params.set('formation', formation);
    if (phase) params.set('phase', phase);
    if (matchId) params.set('matchId', matchId);
    const query = params.toString();

    return this.request<any>(`/tactical/overview${query ? `?${query}` : ''}`);
  }

  // ML endpoints
  async getMLAlgorithms(): Promise<ApiResponse<MLAlgorithm[]> | ApiError> {
    return this.request<MLAlgorithm[]>('/ml/algorithms');
  }

  async getMLDatasets(): Promise<ApiResponse<MLDataset[]> | ApiError> {
    return this.request<MLDataset[]>('/ml/datasets');
  }

  async getMLExperiments(): Promise<ApiResponse<MLExperiment[]> | ApiError> {
    return this.request<MLExperiment[]>('/ml/experiments');
  }

  async createMLExperiment(experiment: Partial<MLExperiment>): Promise<ApiResponse<MLExperiment>> {
    return this.request<MLExperiment>('/ml/experiments', {
      method: 'POST',
      body: JSON.stringify(experiment)
    });
  }

  async trainModel(algorithmId: string, datasetId: string, config: any): Promise<ApiResponse<any>> {
    return this.request<any>('/ml/train', {
      method: 'POST',
      body: JSON.stringify({ algorithmId, datasetId, config })
    });
  }

  // ============ NEW SERVICES (2025-10-19) ============

  // Report Service endpoints (Port 8009)
  async generatePlayerReport(playerId: string, format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/reports/player/${playerId}?format=${format}`);
    if (!response.ok) {
      throw new Error(`Failed to generate report: ${response.statusText}`);
    }
    return response.blob();
  }

  async generateTeamReport(teamId: string, format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/reports/team/${teamId}?format=${format}`);
    if (!response.ok) {
      throw new Error(`Failed to generate report: ${response.statusText}`);
    }
    return response.blob();
  }

  async generateMatchReport(matchId: string, format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/reports/match/${matchId}?format=${format}`);
    if (!response.ok) {
      throw new Error(`Failed to generate report: ${response.statusText}`);
    }
    return response.blob();
  }

  async generateAsyncReport(
    type: string,
    entityId: string,
    format: string,
    metadata: Record<string, any> = {}
  ): Promise<ApiResponse<{ job_id: string }>> {
    return this.request<{ job_id: string }>('/v2/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ type, entity_id: entityId, format, ...metadata })
    });
  }

  async getReportStatus(reportId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/reports/${reportId}/status`);
  }

  async downloadReport(reportId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/reports/${reportId}/download`);
    if (!response.ok) {
      throw new Error(`Failed to download report: ${response.statusText}`);
    }
    return response.blob();
  }

  async listReports(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/v2/reports/list');
  }

  async deleteReport(reportId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/reports/${reportId}`, { method: 'DELETE' });
  }

  async getAdminSnapshot(): Promise<ApiResponse<any>> {
    return this.request<any>('/v2/admin/snapshot');
  }

  // Export Service endpoints (Port 8010)
  async exportPlayers(format: 'csv' | 'json' | 'excel' = 'csv', filters?: any): Promise<Blob> {
    const params = new URLSearchParams({ format });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
    }
    const response = await fetch(`${this.baseUrl}/v2/exports/players?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to export players: ${response.statusText}`);
    }
    return response.blob();
  }

  async exportTeams(format: 'csv' | 'json' | 'excel' = 'csv'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/exports/teams?format=${format}`);
    if (!response.ok) {
      throw new Error(`Failed to export teams: ${response.statusText}`);
    }
    return response.blob();
  }

  async exportMatches(format: 'csv' | 'json' | 'excel' = 'csv', filters?: any): Promise<Blob> {
    const params = new URLSearchParams({ format });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
    }
    const response = await fetch(`${this.baseUrl}/v2/exports/matches?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to export matches: ${response.statusText}`);
    }
    return response.blob();
  }

  async exportStatistics(format: 'csv' | 'json' | 'excel' = 'csv'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/exports/statistics?format=${format}`);
    if (!response.ok) {
      throw new Error(`Failed to export statistics: ${response.statusText}`);
    }
    return response.blob();
  }

  async exportCustom(data: any[], format: 'csv' | 'json' | 'excel', columns?: string[]): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/exports/custom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data, format, columns })
    });
    if (!response.ok) {
      throw new Error(`Failed to export custom data: ${response.statusText}`);
    }
    return response.blob();
  }

  async getExportTemplate(entityType: 'players' | 'teams' | 'matches'): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/exports/templates/${entityType}`);
  }

  async listImportTemplates(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/v2/imports/templates');
  }

  async getImportTemplate(type: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/imports/templates/${type}`);
  }

  async listImportJobs(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/v2/imports/jobs');
  }

  async createImportJob(payload: any): Promise<ApiResponse<any>> {
    return this.request<any>('/v2/imports/jobs', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async retryImportJob(jobId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/imports/jobs/${jobId}/retry`, {
      method: 'POST'
    });
  }

  async downloadImportJobReport(jobId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/v2/imports/jobs/${jobId}/report`);
    if (!response.ok) {
      throw new Error(`Failed to download import report: ${response.statusText}`);
    }
    return response.blob();
  }

  // Video Service endpoints (Port 8011)
  async uploadVideo(file: File, matchId?: string, metadata?: any): Promise<ApiResponse<{ video_id: string }>> {
    const formData = new FormData();
    formData.append('file', file);
    if (matchId) formData.append('match_id', matchId);
    if (metadata) formData.append('metadata', JSON.stringify(metadata));

    const response = await fetch(`${this.baseUrl}/v2/videos/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      return {
        success: false,
        error: {
          code: response.status.toString(),
          message: `Failed to upload video: ${response.statusText}`
        }
      };
    }

    const data = await response.json();
    return {
      success: true,
      data,
      meta: { timestamp: new Date().toISOString(), source: 'api' }
    };
  }

  async getVideoMetadata(videoId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/videos/${videoId}`);
  }

  async getVideoStreamUrl(videoId: string): string {
    return `${this.baseUrl}/v2/videos/${videoId}/stream`;
  }

  async analyzeVideo(videoId: string, analysisType: string = 'full'): Promise<ApiResponse<{ job_id: string }>> {
    return this.request<{ job_id: string }>(`/v2/videos/${videoId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ analysis_type: analysisType })
    });
  }

  async listVideos(matchId?: string): Promise<ApiResponse<any[]>> {
    const url = matchId ? `/v2/videos?match_id=${matchId}` : '/v2/videos';
    return this.request<any[]>(url);
  }

  async createVideoEntry(payload: any): Promise<ApiResponse<any>> {
    return this.request<any>('/v2/videos', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async listVideoAnnotations(videoId: string): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/v2/videos/${videoId}/annotations`);
  }

  async createVideoAnnotation(videoId: string, payload: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/videos/${videoId}/annotations`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async updateVideoAnnotation(videoId: string, annotationId: string, payload: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/videos/${videoId}/annotations/${annotationId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  }

  async deleteVideoAnnotation(videoId: string, annotationId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/videos/${videoId}/annotations/${annotationId}`, {
      method: 'DELETE'
    });
  }

  async deleteVideo(videoId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/videos/${videoId}`, { method: 'DELETE' });
  }

  // ==== Phase 1, 2, 3: Enhanced Event Analytics (Statistics Service) ====
  async getPlayerEnhancedPassStats(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/events/passes/enhanced/player/${playerId}`);
  }

  async getPlayerExpectedMetrics(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/events/expected-metrics/player/${playerId}`);
  }

  async getPlayerCompositeIndex(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/events/composite-index/player/${playerId}`);
  }

  async getPlayerHeatmap(playerId: string, eventType?: string): Promise<ApiResponse<any>> {
    const query = eventType ? `?event_type=${eventType}` : '';
    return this.request<any>(`/v2/events/heatmap/player/${playerId}${query}`);
  }

  async getPlayerSimilarity(playerId: string, targets: string[] = []): Promise<ApiResponse<any>> {
    const query = targets.length > 0 ? `?targets=${targets.join(',')}` : '';
    return this.request<any>(`/v2/events/similarity/player/${playerId}${query}`);
  }
  // =======================================================================
  
  // ==== Phase 4: Machine Learning (Engine Integrations) ====
  async predictTacticalRole(stats: Record<string, any>): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v2/ml/engine/predict/tactical_role_classifier', {
      method: 'POST',
      body: stats,
    });
  }

  async predictPerformanceAnomaly(stats: Record<string, any>): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v2/ml/engine/predict/performance_anomaly_detector', {
      method: 'POST',
      body: stats,
    });
  }

  async predictFatigueRisk(stats: Record<string, any>): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v2/ml/engine/predict/fatigue_risk_predictor', {
      method: 'POST',
      body: stats,
    });
  }
  // =======================================================================

  // Analytics Service endpoints (Port 8012) - Advanced BI Dashboard
  async getDashboardOverview(): Promise<ApiResponse<any>> {
    return this.request<any>('/v2/analytics/dashboard/overview');
  }

  async getTeamDashboard(teamId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/dashboard/team/${teamId}`);
  }

  async getPlayerDashboard(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/dashboard/player/${playerId}`);
  }

  async getPlayerStatistics(
    playerId: string,
    options?: { competitionId?: string; seasonId?: string; per90?: boolean }
  ): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (options?.competitionId) params.append('competition_id', options.competitionId);
    if (options?.seasonId) params.append('season_id', options.seasonId);
    if (options?.per90) params.append('per_90', 'true');

    return this.request<any>(`/statistics/player/${playerId}${params.toString() ? `?${params.toString()}` : ''}`);
  }

  async getTeamStatistics(
    teamId: string,
    options?: { competitionId?: string; seasonId?: string }
  ): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (options?.competitionId) params.append('competition_id', options.competitionId);
    if (options?.seasonId) params.append('season_id', options.seasonId);

    return this.request<any>(`/statistics/team/${teamId}${params.toString() ? `?${params.toString()}` : ''}`);
  }

  async aggregatePlayerStatistics(
    playerId: string,
    startDate: string,
    endDate: string
  ): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
    });

    return this.request<any>(`/statistics/aggregate/player/${playerId}?${params.toString()}`);
  }

  async getLeagueTrends(leagueId?: string): Promise<ApiResponse<any>> {
    const url = `/v2/analytics/trends/league?competition=${encodeURIComponent(leagueId || 'all')}`;
    return this.request<any>(url);
  }

  async getPlayerRankings(metric: string, limit: number = 20, leagueId?: string): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams({ stat_name: metric, limit: limit.toString() });
    if (leagueId) params.append('competition_id', leagueId);
    return this.request<any[]>(`/statistics/rankings/players?${params.toString()}`);
  }

  async getTeamRankings(metric: string, limit: number = 20, leagueId?: string): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams({ stat_name: metric, limit: limit.toString() });
    if (leagueId) params.append('competition_id', leagueId);
    return this.request<any[]>(`/statistics/rankings/teams?${params.toString()}`);
  }

  async getTeamInsights(teamId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/insights/team/${teamId}`);
  }

  async getPlayerInsightsAdvanced(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/insights/player/${playerId}`);
  }

  async getPlayerSequenceInsights(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/insights/player/${playerId}/sequences`);
  }

  async getPlayerSequenceCoverage(playerIds: string[]): Promise<ApiResponse<any>> {
    return this.request<any>('/v2/analytics/insights/players/sequences', {
      method: 'POST',
      body: {
        player_ids: playerIds,
      },
    });
  }

  async findSimilarPlayers(
    playerStats: Record<string, any>,
    candidatePlayers: Record<string, any>[],
    topN: number = 10,
    useAdvancedML: boolean = false
  ): Promise<ApiResponse<any[]>> {
    if (useAdvancedML) {
        return this.request<any[]>('/ml/engine/predict/advanced_player_similarity', {
          method: 'POST',
          body: {
            player_stats: playerStats,
            candidate_players: candidatePlayers,
            top_n: topN,
          },
        });
    }
    return this.request<any[]>('/ml/similarity/players', {
      method: 'POST',
      body: {
        player_stats: playerStats,
        candidate_players: candidatePlayers,
        top_n: topN,
      },
    });
  }

  async comparePlayers(playerIds: string[]): Promise<ApiResponse<any>> {
    return this.request<any>('/v2/analytics/comparison/players', {
      method: 'POST',
      body: { player_ids: playerIds },
    });
  }

  async compareTeams(teamIds: string[]): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    teamIds.forEach((teamId) => params.append('team_ids', teamId));
    return this.request<any>(`/v2/analytics/comparison/teams?${params.toString()}`);
  }

  async getCalendarSnapshot(): Promise<ApiResponse<{ events: CalendarEvent[]; trips: ScoutingTrip[]; matches: MatchSchedule[] }>> {
    return this.request<{ events: CalendarEvent[]; trips: ScoutingTrip[]; matches: MatchSchedule[] }>('/v2/calendar');
  }

  async createCalendarEvent(event: CalendarEvent): Promise<ApiResponse<CalendarEvent>> {
    return this.request<CalendarEvent>('/v2/calendar/events', {
      method: 'POST',
      body: event,
    });
  }

  async updateCalendarEvent(id: string, updates: Partial<CalendarEvent>): Promise<ApiResponse<CalendarEvent>> {
    return this.request<CalendarEvent>(`/v2/calendar/events/${id}`, {
      method: 'PUT',
      body: updates,
    });
  }

  async deleteCalendarEvent(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/calendar/events/${id}`, {
      method: 'DELETE',
    });
  }

  async createScoutingTrip(trip: ScoutingTrip): Promise<ApiResponse<ScoutingTrip>> {
    return this.request<ScoutingTrip>('/v2/calendar/trips', {
      method: 'POST',
      body: trip,
    });
  }

  async updateScoutingTrip(id: string, updates: Partial<ScoutingTrip>): Promise<ApiResponse<ScoutingTrip>> {
    return this.request<ScoutingTrip>(`/v2/calendar/trips/${id}`, {
      method: 'PUT',
      body: updates,
    });
  }

  async deleteScoutingTrip(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/calendar/trips/${id}`, {
      method: 'DELETE',
    });
  }

  async updateMatchSchedule(id: string, updates: Partial<MatchSchedule>): Promise<ApiResponse<MatchSchedule>> {
    return this.request<MatchSchedule>(`/v2/calendar/matches/${id}`, {
      method: 'PUT',
      body: updates,
    });
  }

  async getCollaborationSnapshot(): Promise<ApiResponse<{ workspaces: Workspace[]; tasks: Task[]; activities: CollaborationActivity[] }>> {
    return this.request<{ workspaces: Workspace[]; tasks: Task[]; activities: CollaborationActivity[] }>('/v2/collaboration');
  }

  async createWorkspace(workspace: Workspace): Promise<ApiResponse<Workspace>> {
    return this.request<Workspace>('/v2/collaboration/workspaces', {
      method: 'POST',
      body: workspace,
    });
  }

  async updateWorkspace(id: string, updates: Partial<Workspace>): Promise<ApiResponse<Workspace>> {
    return this.request<Workspace>(`/v2/collaboration/workspaces/${id}`, {
      method: 'PUT',
      body: updates,
    });
  }

  async deleteWorkspace(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/collaboration/workspaces/${id}`, {
      method: 'DELETE',
    });
  }

  async createTask(task: Task): Promise<ApiResponse<Task>> {
    return this.request<Task>('/v2/collaboration/tasks', {
      method: 'POST',
      body: task,
    });
  }

  async updateTask(id: string, updates: Partial<Task>): Promise<ApiResponse<Task>> {
    return this.request<Task>(`/v2/collaboration/tasks/${id}`, {
      method: 'PUT',
      body: updates,
    });
  }

  async deleteTask(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/collaboration/tasks/${id}`, {
      method: 'DELETE',
    });
  }

  async createCollaborationActivity(activity: CollaborationActivity): Promise<ApiResponse<CollaborationActivity>> {
    return this.request<CollaborationActivity>('/v2/collaboration/activities', {
      method: 'POST',
      body: activity,
    });
  }

  async getSavedSearches(): Promise<ApiResponse<SavedSearch[]>> {
    return this.request<SavedSearch[]>('/search/saved');
  }

  async createSavedSearch(search: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt'>): Promise<ApiResponse<SavedSearch>> {
    return this.request<SavedSearch>('/search/saved', {
      method: 'POST',
      body: search,
    });
  }

  async updateSavedSearch(id: string, updates: Partial<SavedSearch>): Promise<ApiResponse<SavedSearch>> {
    return this.request<SavedSearch>(`/search/saved/${id}`, {
      method: 'PUT',
      body: updates,
    });
  }

  async deleteSavedSearch(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/search/saved/${id}`, {
      method: 'DELETE',
    });
  }

  async getSearchHistory(): Promise<ApiResponse<SearchHistory[]>> {
    return this.request<SearchHistory[]>('/search/history');
  }

  async addSearchHistoryEntry(entry: Omit<SearchHistory, 'id' | 'timestamp'>): Promise<ApiResponse<SearchHistory>> {
    return this.request<SearchHistory>('/search/history', {
      method: 'POST',
      body: entry,
    });
  }

  async clearSearchHistory(): Promise<ApiResponse<void>> {
    return this.request<void>('/search/history', {
      method: 'DELETE',
    });
  }

  // ─── ML v2 endpoints ────────────────────────────────────────────────────────

  async getMLFeatureStatus(): Promise<ApiResponse<any>> {
    return this.request<any>('/ml/features/status');
  }

  async trainPlayerPerformanceModel(): Promise<ApiResponse<any>> {
    return this.request<any>('/ml/train/player-performance', { method: 'POST' });
  }

  async findSimilarPlayersById(playerId: string, topN: number = 5): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/ml/similarity/players', {
      method: 'POST',
      body: JSON.stringify({ player_id: playerId, top_n: topN }),
    });
  }

  async predictPlayerPerformance(features: Record<string, number>): Promise<ApiResponse<any>> {
    return this.request<any>('/ml/predict/player-performance', {
      method: 'POST',
      body: JSON.stringify({ features }),
    });
  }

  // ─── Video upload with XHR progress tracking ────────────────────────────────

  uploadVideoWithProgress(
    formData: FormData,
    onProgress?: (pct: number) => void
  ): Promise<ApiResponse<{ video_id: string }>> {
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${this.baseUrl}/v2/videos/upload`);
      if (this.apiKey) {
        xhr.setRequestHeader('Authorization', `Bearer ${this.apiKey}`);
      }
      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        });
      }
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve({
              success: true,
              data: JSON.parse(xhr.responseText),
              meta: { timestamp: new Date().toISOString(), source: 'api' },
            });
          } catch {
            resolve({ success: false, error: { code: 'PARSE_ERROR', message: 'Invalid JSON response' } });
          }
        } else {
          resolve({ success: false, error: { code: xhr.status.toString(), message: xhr.statusText } });
        }
      };
      xhr.onerror = () =>
        resolve({ success: false, error: { code: 'NETWORK_ERROR', message: 'Network request failed' } });
      xhr.send(formData);
    });
  }

  async streamVideo(videoId: string): Promise<string> {
    return `${this.baseUrl}/v2/videos/${videoId}/stream`;
  }

  // ─── Real-time Player Statistics (aggregated from match events) ────────────

  async getPlayerStatisticsRealtime(
    limit: number = 100,
    skip: number = 0,
    sortBy: string = 'goals'
  ): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({
      limit: Math.min(limit, 500).toString(),
      skip: Math.max(skip, 0).toString(),
      sortBy: sortBy,
    });
    return this.request<any>(`/players/statistics?${params.toString()}`);
  }

  async getPlayerStatisticsById(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/players/${playerId}/statistics`);
  }

  // ─── Detailed Player Statistics (computed from event handlers) ────────────

  async getPlayerDetailedStats(playerId: string | number): Promise<ApiResponse<any>> {
    return this.request<any>(`/players/${playerId}/detailed-stats`);
  }

  async getPlayerMatchDetailedStats(playerId: string | number, matchId: string | number): Promise<ApiResponse<any>> {
    return this.request<any>(`/players/${playerId}/match-stats/${matchId}`);
  }

  async getPlayerLeaderboard(metric: 'passes' | 'aerials' | 'shooting' = 'passes', limit: number = 20): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({
      limit: Math.min(limit, 100).toString(),
    });
    return this.request<any>(`/players/stats/leaders/${metric}?${params.toString()}`);
  }

  // ─── Match Data ────────────────────────────────────────────────────────────

  async getMatchesEnriched(limit: number = 50, skip: number = 0): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({
      limit: Math.min(limit, 500).toString(),
      skip: Math.max(skip, 0).toString(),
    });
    return this.request<any>(`/matches/enriched/list?${params.toString()}`);
  }

  // ─── Match Visualizations ──────────────────────────────────────────────────

  async getMatchShotMap(matchId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/matches/${matchId}/shots-map`);
  }

  async getMatchHeatMap(matchId: string, teamId?: string, playerId?: string): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (teamId) params.append('team_id', teamId);
    if (playerId) params.append('player_id', playerId);
    const query = params.toString();
    return this.request<any>(`/matches/${matchId}/heat-map${query ? `?${query}` : ''}`);
  }

  async getMatchPassMap(matchId: string, teamId?: string): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (teamId) params.append('team_id', teamId);
    const query = params.toString();
    return this.request<any>(`/matches/${matchId}/pass-map${query ? `?${query}` : ''}`);
  }

  async getMatchPossession(matchId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/matches/${matchId}/possession`);
  }

  async getMatchPressureMap(matchId: string, teamId?: string): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (teamId) params.append('team_id', teamId);
    const query = params.toString();
    return this.request<any>(`/matches/${matchId}/pressure-map${query ? `?${query}` : ''}`);
  }

  // ─── Player Comparison ─────────────────────────────────────────────────────

  async getPlayerComparison(playerIds: string[]): Promise<ApiResponse<any>> {
    return this.request<any>('/players/compare', {
      method: 'POST',
      body: JSON.stringify({ player_ids: playerIds }),
    });
  }

  async getPlayerPercentiles(playerId: string, position?: string): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (position) params.append('position', position);
    const query = params.toString();
    return this.request<any>(`/players/${playerId}/percentiles${query ? `?${query}` : ''}`);
  }
}

const apiService = new ApiService();
export default apiService;