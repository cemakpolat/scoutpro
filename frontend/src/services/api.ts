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
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api';
    this.apiKey = import.meta.env.VITE_API_KEY || '';
    this.useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true' || false;
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
}

const apiService = new ApiService();
export default apiService;