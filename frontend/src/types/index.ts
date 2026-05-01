// Core Data Models
export interface Player {
  id: string;
  name: string;
  age: number;
  position: string;
  club: string;
  nationality: string;
  rating: number;
  marketValue: string;
  photo: string;
  contract: string;
  height: string;
  weight: string;
  preferredFoot: string;
  goals: number;
  assists: number;
  appearances: number;
  minutesPlayed: number;
  xG: number;
  xA: number;
  passAccuracy: number;
  dribbleSuccess: number;
  sprintSpeed: number;
  pressureResistance: number;
  workRate: string;
  weakFoot: number;
  skillMoves: number;
  injuryHistory: string;
  strongAttributes: string[];
  weakAttributes: string[];
  tacticalRole: string;
  adaptabilityScore: number;
  mentalStrength: number;
  leadership: number;
  consistency: number;
  createdAt: string;
  updatedAt: string;
}

export interface Match {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  date: string;
  venue: string;
  attendance: string;
  status: 'scheduled' | 'live' | 'finished' | 'postponed';
  homeFormation: string;
  awayFormation: string;
  competition: string;
  referee: string;
  weather: string;
  homeXG: number;
  awayXG: number;
  homePossession: number;
  awayPossession: number;
  homeShots: number;
  awayShots: number;
  homeShotsOnTarget: number;
  awayShotsOnTarget: number;
  homeCorners: number;
  awayCorners: number;
  homeFouls: number;
  awayFouls: number;
  homeYellowCards: number;
  awayYellowCards: number;
  homeRedCards: number;
  awayRedCards: number;
  homePasses: number;
  awayPasses: number;
  homePassAccuracy: number;
  awayPassAccuracy: number;
  createdAt: string;
  updatedAt: string;
}

export interface Team {
  id: string;
  name: string;
  shortName: string;
  logo: string;
  league: string;
  country: string;
  founded: number;
  stadium: string;
  capacity: number;
  manager: string;
  formation: string;
  playingStyle: string;
  marketValue: string;
  averageAge: number;
  createdAt: string;
  updatedAt: string;
}

export interface League {
  id: string;
  name: string;
  country: string;
  level: number;
  season: string;
  teams: number;
  logo: string;
  coefficient: number;
  createdAt: string;
  updatedAt: string;
}

export interface TransferRumor {
  id: string;
  playerId: string;
  currentClubId: string;
  targetClubId: string;
  probability: number;
  estimatedValue: string;
  status: 'hot' | 'warm' | 'cold' | 'completed' | 'denied';
  deadline: string;
  sources: string[];
  reliability: number;
  createdAt: string;
  updatedAt: string;
}

export interface Notification {
  id: string;
  type: 'performance' | 'market' | 'tactical' | 'injury' | 'transfer' | 'system';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  read: boolean;
  userId?: string;
  relatedEntityId?: string;
  relatedEntityType?: 'player' | 'match' | 'team' | 'transfer';
  createdAt: string;
  updatedAt: string;
}

export interface PerformanceMetric {
  id: string;
  playerId: string;
  matchId: string;
  rating: number;
  goals: number;
  assists: number;
  shots: number;
  shotsOnTarget: number;
  passes: number;
  passAccuracy: number;
  tackles: number;
  interceptions: number;
  dribbles: number;
  dribbleSuccess: number;
  aerialDuels: number;
  aerialDuelsWon: number;
  distanceCovered: number;
  sprintDistance: number;
  topSpeed: number;
  heatmapData: HeatmapZone[];
  createdAt: string;
  updatedAt: string;
}

export interface HeatmapZone {
  zone: string;
  x: number;
  y: number;
  intensity: number;
  actions: number;
  effectiveness: number;
}

export interface TacticalPattern {
  id: string;
  name: string;
  description: string;
  frequency: number;
  successRate: number;
  zones: string[];
  impact: 'low' | 'medium' | 'high';
  trend: 'increasing' | 'stable' | 'decreasing';
  teamIds: string[];
  createdAt: string;
  updatedAt: string;
}

export interface MarketTrend {
  id: string;
  position: string;
  averageValue: string;
  change: string;
  trend: 'up' | 'down' | 'stable';
  timeframe: string;
  sampleSize: number;
  createdAt: string;
  updatedAt: string;
}

export interface AIInsight {
  id: string;
  type: 'prediction' | 'analysis' | 'recommendation' | 'alert';
  title: string;
  description: string;
  confidence: number;
  relatedEntityId: string;
  relatedEntityType: 'player' | 'match' | 'team' | 'market';
  data: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface Analytics {
  id: string;
  type: string;
  predictions?: {
    total: number;
    accuracy: number;
  };
  metrics?: Record<string, any>;
  trends?: any[];
  createdAt: string;
  updatedAt: string;
}

// New ML-related interfaces
export interface MLAlgorithm {
  id: string;
  name: string;
  type: string;
  description: string;
  accuracy: number;
  speed: string;
  interpretability: string;
  bestFor: string[];
  parameters: Record<string, any>;
}

export interface MLDataset {
  id: string;
  name: string;
  size: string;
  records: string;
  features: number;
  timespan: string;
  description: string;
  quality: number;
  lastUpdated: string;
}

export interface MLExperiment {
  id: string;
  name: string;
  algorithm: string;
  dataset: string;
  status: 'completed' | 'running' | 'failed';
  accuracy: number;
  runtime: string;
  created: string;
  insights: string[];
}

// API Response Types
export interface ApiResponse<T> {
  success: true;
  data: T;
  message?: string;
  meta?: {
    timestamp: string;
    source: string;
  };
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

// WebSocket Message Types
export interface WebSocketMessage {
  type:
    | 'match_update'
    | 'player_update'
    | 'notification'
    | 'market_update'
    | 'tactical_update'
    | 'connected'
    | 'subscribed'
    | 'unsubscribed'
    | 'pong';
  data: any;
  timestamp: string;
}

export interface LiveMatchUpdate {
  matchId: string;
  minute: number;
  score: {
    home: number;
    away: number;
  };
  events: MatchEvent[];
  stats: LiveMatchStats;
}

export interface MatchEvent {
  id: string;
  type: 'goal' | 'yellow_card' | 'red_card' | 'substitution' | 'var_check' | 'penalty';
  minute: number;
  playerId: string;
  playerName: string;
  team: 'home' | 'away';
  description: string;
  xG?: number;
}

export interface LiveMatchStats {
  possession: {
    home: number;
    away: number;
  };
  shots: {
    home: number;
    away: number;
  };
  shotsOnTarget: {
    home: number;
    away: number;
  };
  xG: {
    home: number;
    away: number;
  };
  passes: {
    home: number;
    away: number;
  };
  passAccuracy: {
    home: number;
    away: number;
  };
}

// Filter and Query Types
export interface PlayerFilters {
  position?: string[];
  league?: string[];
  nationality?: string[];
  ageMin?: number;
  ageMax?: number;
  marketValueMin?: number;
  marketValueMax?: number;
  ratingMin?: number;
  ratingMax?: number;
  club?: string[];
}

export interface MatchFilters {
  competition?: string[];
  dateFrom?: string;
  dateTo?: string;
  teams?: string[];
  status?: string[];
  limit?: number;
  skip?: number;
}

export interface QueryParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  search?: string;
}

// Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'scout' | 'analyst' | 'viewer';
  team?: string;
  avatar?: string;
  permissions: string[];
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  role?: 'scout' | 'analyst' | 'viewer';
  team?: string;
}

// Export collaboration types
export * from './collaboration';

// Export calendar types
export * from './calendar';

// Export video types
export * from './video';

// Export import types
export * from './import';