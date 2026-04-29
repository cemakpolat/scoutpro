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
  MLAlgorithm,
  MLDataset,
  MLExperiment
} from '../types';
import { mockMLAlgorithms, mockMLDatasets, mockMLExperiments } from '../data/mlMockData';
import { mockPlayers } from '../data/playersMockData';
import { mockMatches } from '../data/matchesMockData';
import { mockTeams } from '../data/teamsMockData';
import { mockNotifications, mockMarketTrends, mockAIInsights, mockTacticalPatterns, mockAnalytics } from '../data/otherMockData';

class ApiService {
  private baseUrl: string;
  private apiKey: string;
  private useMockData: boolean;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || '/api/v1';
    this.apiKey = import.meta.env.VITE_API_KEY || '';
    this.useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` }),
        ...options.headers,
      };

      const response = await fetch(url, {
        ...options,
        headers,
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

      const data = await response.json();
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
  async getPlayers(filters?: PlayerFilters): Promise<ApiResponse<Player[]>> {
    if (this.useMockData) {
      // Apply filters to mock data
      let filteredPlayers = [...mockPlayers];

      if (filters) {
        if (filters.position) {
          filteredPlayers = filteredPlayers.filter(p => filters.position?.includes(p.position));
        }
        if (filters.club) {
          filteredPlayers = filteredPlayers.filter(p => filters.club?.includes(p.club));
        }
        if (filters.ageMin) {
          filteredPlayers = filteredPlayers.filter(p => p.age >= filters.ageMin!);
        }
        if (filters.ageMax) {
          filteredPlayers = filteredPlayers.filter(p => p.age <= filters.ageMax!);
        }
      }

      return {
        success: true,
        data: filteredPlayers,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock'
        }
      };
    }

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
    const response = await this.request<Player[]>(`/players${queryString ? `?${queryString}` : ''}`);

    // Fallback to mock data if API fails
    if (!response.success) {
      return {
        success: true,
        data: mockPlayers,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock-fallback'
        }
      };
    }
    return response;
  }

  async getPlayer(id: string): Promise<ApiResponse<Player>> {
    if (this.useMockData) {
      const player = mockPlayers.find(p => p.id === id);
      if (player) {
        return {
          success: true,
          data: player,
          meta: { timestamp: new Date().toISOString(), source: 'mock' }
        };
      }
    }

    const response = await this.request<Player>(`/players/${id}`);
    if (!response.success) {
      const player = mockPlayers.find(p => p.id === id);
      if (player) {
        return {
          success: true,
          data: player,
          meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
        };
      }
    }
    return response;
  }

  async searchPlayers(query: string): Promise<ApiResponse<Player[]>> {
    if (this.useMockData) {
      const results = mockPlayers.filter(p =>
        p.name.toLowerCase().includes(query.toLowerCase()) ||
        p.club.toLowerCase().includes(query.toLowerCase()) ||
        p.position.toLowerCase().includes(query.toLowerCase())
      );
      return {
        success: true,
        data: results,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<Player[]>(`/players/search?q=${encodeURIComponent(query)}`);
    if (!response.success) {
      return {
        success: true,
        data: mockPlayers,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  // Match endpoints
  async getMatches(filters?: MatchFilters): Promise<ApiResponse<Match[]>> {
    if (this.useMockData) {
      let filteredMatches = [...mockMatches];
      if (filters) {
        if (filters.status) {
          filteredMatches = filteredMatches.filter(m => filters.status?.includes(m.status));
        }
        if (filters.teams) {
          filteredMatches = filteredMatches.filter(m =>
            filters.teams?.includes(m.homeTeam) || filters.teams?.includes(m.awayTeam)
          );
        }
      }
      return {
        success: true,
        data: filteredMatches,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

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
    const response = await this.request<Match[]>(`/matches${queryString ? `?${queryString}` : ''}`);
    if (!response.success) {
      return {
        success: true,
        data: mockMatches,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async getMatch(id: string): Promise<ApiResponse<Match>> {
    if (this.useMockData) {
      const match = mockMatches.find(m => m.id === id);
      if (match) {
        return {
          success: true,
          data: match,
          meta: { timestamp: new Date().toISOString(), source: 'mock' }
        };
      }
    }

    const response = await this.request<Match>(`/matches/${id}`);
    if (!response.success) {
      const match = mockMatches.find(m => m.id === id);
      if (match) {
        return {
          success: true,
          data: match,
          meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
        };
      }
    }
    return response;
  }

  async getLiveMatches(): Promise<ApiResponse<Match[]>> {
    if (this.useMockData) {
      const liveMatches = mockMatches.filter(m => m.status === 'live');
      return {
        success: true,
        data: liveMatches,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<Match[]>('/matches/live');
    if (!response.success) {
      const liveMatches = mockMatches.filter(m => m.status === 'live');
      return {
        success: true,
        data: liveMatches,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async getMatchEvents(matchId: string): Promise<ApiResponse<any[]>> {
    if (this.useMockData) {
      return {
        success: true,
        data: [],
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<any[]>(`/matches/${matchId}/events`);
    if (!response.success) {
      return {
        success: true,
        data: [],
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  // Team endpoints
  async getTeams(): Promise<ApiResponse<Team[]>> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockTeams,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<Team[]>('/teams');
    if (!response.success) {
      return {
        success: true,
        data: mockTeams,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async getTeam(id: string): Promise<ApiResponse<Team>> {
    if (this.useMockData) {
      const team = mockTeams.find(t => t.id === id);
      if (team) {
        return {
          success: true,
          data: team,
          meta: { timestamp: new Date().toISOString(), source: 'mock' }
        };
      }
    }

    const response = await this.request<Team>(`/teams/${id}`);
    if (!response.success) {
      const team = mockTeams.find(t => t.id === id);
      if (team) {
        return {
          success: true,
          data: team,
          meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
        };
      }
    }
    return response;
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
    if (this.useMockData) {
      return {
        success: true,
        data: mockAnalytics,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<Analytics>(`/analytics/${type}`);
    if (!response.success) {
      return {
        success: true,
        data: mockAnalytics,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async getPlayerAnalytics(playerId: string): Promise<ApiResponse<Analytics>> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockAnalytics,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<Analytics>(`/analytics/player/${playerId}`);
    if (!response.success) {
      return {
        success: true,
        data: mockAnalytics,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async getMatchAnalytics(matchId: string): Promise<ApiResponse<Analytics>> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockAnalytics,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<Analytics>(`/analytics/match/${matchId}`);
    if (!response.success) {
      return {
        success: true,
        data: mockAnalytics,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  // AI Insights endpoints
  async getAIInsights(type: string): Promise<ApiResponse<AIInsight[]>> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockAIInsights,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<AIInsight[]>(`/ai/insights/${type}`);
    if (!response.success) {
      return {
        success: true,
        data: mockAIInsights,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async getPlayerInsights(playerId: string): Promise<ApiResponse<AIInsight[]>> {
    if (this.useMockData) {
      const insights = mockAIInsights.filter(i => i.relatedEntityId === playerId);
      return {
        success: true,
        data: insights,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<AIInsight[]>(`/ai/insights/player/${playerId}`);
    if (!response.success) {
      const insights = mockAIInsights.filter(i => i.relatedEntityId === playerId);
      return {
        success: true,
        data: insights,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  // Market endpoints
  async getMarketTrends(): Promise<ApiResponse<MarketTrend[]>> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockMarketTrends,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<MarketTrend[]>('/market/trends');
    if (!response.success) {
      return {
        success: true,
        data: mockMarketTrends,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async getTransferPredictions(): Promise<ApiResponse<any[]>> {
    if (this.useMockData) {
      return {
        success: true,
        data: [],
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<any[]>('/market/predictions');
    if (!response.success) {
      return {
        success: true,
        data: [],
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  // Notification endpoints
  async getNotifications(): Promise<ApiResponse<Notification[]>> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockNotifications,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<Notification[]>('/notifications');
    if (!response.success) {
      return {
        success: true,
        data: mockNotifications,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  async markNotificationRead(id: string): Promise<ApiResponse<void>> {
    if (this.useMockData) {
      // In mock mode, just return success
      return {
        success: true,
        data: undefined as any,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    return this.request<void>(`/notifications/${id}/read`, { method: 'PUT' });
  }

  // Tactical patterns endpoint
  async getTacticalPatterns(): Promise<ApiResponse<any[]>> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockTacticalPatterns,
        meta: { timestamp: new Date().toISOString(), source: 'mock' }
      };
    }

    const response = await this.request<any[]>('/tactical/patterns');
    if (!response.success) {
      return {
        success: true,
        data: mockTacticalPatterns,
        meta: { timestamp: new Date().toISOString(), source: 'mock-fallback' }
      };
    }
    return response;
  }

  // ML endpoints
  async getMLAlgorithms(): Promise<ApiResponse<MLAlgorithm[]> | ApiError> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockMLAlgorithms,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock'
        }
      };
    }

    const response = await this.request<MLAlgorithm[]>('/ml/algorithms');
    // Fallback to mock data if API fails
    if (!response.success) {
      return {
        success: true,
        data: mockMLAlgorithms,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock-fallback'
        }
      };
    }
    return response;
  }

  async getMLDatasets(): Promise<ApiResponse<MLDataset[]> | ApiError> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockMLDatasets,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock'
        }
      };
    }

    const response = await this.request<MLDataset[]>('/ml/datasets');
    // Fallback to mock data if API fails
    if (!response.success) {
      return {
        success: true,
        data: mockMLDatasets,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock-fallback'
        }
      };
    }
    return response;
  }

  async getMLExperiments(): Promise<ApiResponse<MLExperiment[]> | ApiError> {
    if (this.useMockData) {
      return {
        success: true,
        data: mockMLExperiments,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock'
        }
      };
    }

    const response = await this.request<MLExperiment[]>('/ml/experiments');
    // Fallback to mock data if API fails
    if (!response.success) {
      return {
        success: true,
        data: mockMLExperiments,
        meta: {
          timestamp: new Date().toISOString(),
          source: 'mock-fallback'
        }
      };
    }
    return response;
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

  async generateAsyncReport(type: string, entityId: string, format: string): Promise<ApiResponse<{ job_id: string }>> {
    return this.request<{ job_id: string }>('/v2/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ type, entity_id: entityId, format })
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

  async deleteVideo(videoId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/v2/videos/${videoId}`, { method: 'DELETE' });
  }

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

  async getLeagueTrends(leagueId?: string): Promise<ApiResponse<any>> {
    const url = leagueId ? `/v2/analytics/trends/league?league_id=${leagueId}` : '/v2/analytics/trends/league';
    return this.request<any>(url);
  }

  async getPlayerRankings(metric: string, limit: number = 20, leagueId?: string): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams({ metric, limit: limit.toString() });
    if (leagueId) params.append('league_id', leagueId);
    return this.request<any[]>(`/v2/analytics/rankings/players?${params.toString()}`);
  }

  async getTeamRankings(metric: string, limit: number = 20, leagueId?: string): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams({ metric, limit: limit.toString() });
    if (leagueId) params.append('league_id', leagueId);
    return this.request<any[]>(`/v2/analytics/rankings/teams?${params.toString()}`);
  }

  async getTeamInsights(teamId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/insights/team/${teamId}`);
  }

  async getPlayerInsightsAdvanced(playerId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/insights/player/${playerId}`);
  }

  async comparePlayers(playerIds: string[]): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/comparison/players?ids=${playerIds.join(',')}`);
  }

  async compareTeams(teamIds: string[]): Promise<ApiResponse<any>> {
    return this.request<any>(`/v2/analytics/comparison/teams?ids=${teamIds.join(',')}`);
  }
}

const apiService = new ApiService();
export default apiService;