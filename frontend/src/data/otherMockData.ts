import { Notification, MarketTrend, AIInsight, TacticalPattern, Analytics } from '../types';

export const mockNotifications: Notification[] = [
  {
    id: 'notif-001',
    type: 'performance',
    title: 'Exceptional Performance Alert',
    message: 'Marcus Silva scored a hat-trick with 9.5 match rating',
    priority: 'high',
    read: false,
    relatedEntityId: 'player-001',
    relatedEntityType: 'player',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 'notif-002',
    type: 'market',
    title: 'Market Value Increase',
    message: 'Luca Rossi market value increased by 15% to €58M',
    priority: 'medium',
    read: false,
    relatedEntityId: 'player-003',
    relatedEntityType: 'player',
    createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 'notif-003',
    type: 'tactical',
    title: 'New Tactical Pattern Detected',
    message: 'Bayern Munich showing increased high pressing effectiveness (92%)',
    priority: 'medium',
    read: true,
    relatedEntityId: 'team-003',
    relatedEntityType: 'team',
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 'notif-004',
    type: 'injury',
    title: 'Injury Report',
    message: 'Diego Fernández returned to training after ankle recovery',
    priority: 'low',
    read: true,
    relatedEntityId: 'player-007',
    relatedEntityType: 'player',
    createdAt: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 'notif-005',
    type: 'transfer',
    title: 'Transfer Rumor',
    message: 'Kai Schulz linked with Premier League move, 75% probability',
    priority: 'high',
    read: false,
    relatedEntityId: 'player-006',
    relatedEntityType: 'player',
    createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 'notif-006',
    type: 'system',
    title: 'New ML Model Deployed',
    message: 'Player Potential v3.2 model now active with 91.2% accuracy',
    priority: 'low',
    read: false,
    createdAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString()
  }
];

export const mockMarketTrends: MarketTrend[] = [
  {
    id: 'trend-001',
    position: 'ST',
    averageValue: '€75M',
    change: '+12%',
    trend: 'up',
    timeframe: 'Last 6 months',
    sampleSize: 145,
    createdAt: '2025-09-30T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'trend-002',
    position: 'CM',
    averageValue: '€58M',
    change: '+8%',
    trend: 'up',
    timeframe: 'Last 6 months',
    sampleSize: 203,
    createdAt: '2025-09-30T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'trend-003',
    position: 'CB',
    averageValue: '€52M',
    change: '+3%',
    trend: 'stable',
    timeframe: 'Last 6 months',
    sampleSize: 178,
    createdAt: '2025-09-30T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'trend-004',
    position: 'RW',
    averageValue: '€68M',
    change: '+15%',
    trend: 'up',
    timeframe: 'Last 6 months',
    sampleSize: 156,
    createdAt: '2025-09-30T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'trend-005',
    position: 'GK',
    averageValue: '€28M',
    change: '-2%',
    trend: 'down',
    timeframe: 'Last 6 months',
    sampleSize: 98,
    createdAt: '2025-09-30T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  }
];

export const mockAIInsights: AIInsight[] = [
  {
    id: 'insight-001',
    type: 'prediction',
    title: 'Breakout Player Prediction',
    description: 'Kai Schulz showing exceptional progression curve. Predicted to reach 8.8 rating within 12 months.',
    confidence: 87,
    relatedEntityId: 'player-006',
    relatedEntityType: 'player',
    data: {
      currentRating: 8.2,
      predictedRating: 8.8,
      timeframe: '12 months',
      keyFactors: ['Goal contribution', 'Consistency', 'Age curve']
    },
    createdAt: '2025-09-30T10:00:00Z',
    updatedAt: '2025-09-30T10:00:00Z'
  },
  {
    id: 'insight-002',
    type: 'analysis',
    title: 'Tactical Evolution Detected',
    description: 'Manchester City adapting formation patterns with 23% increase in wide play effectiveness.',
    confidence: 92,
    relatedEntityId: 'team-002',
    relatedEntityType: 'team',
    data: {
      formationChanges: ['4-2-3-1', '4-3-3'],
      effectiveness: 92,
      keyMetric: 'Wide play success'
    },
    createdAt: '2025-09-29T15:00:00Z',
    updatedAt: '2025-09-29T15:00:00Z'
  },
  {
    id: 'insight-003',
    type: 'recommendation',
    title: 'Scouting Recommendation',
    description: 'Yuki Tanaka represents exceptional value at current market price. Projected 40% value increase.',
    confidence: 85,
    relatedEntityId: 'player-008',
    relatedEntityType: 'player',
    data: {
      currentValue: '€35M',
      projectedValue: '€49M',
      timeframe: '18 months',
      riskLevel: 'Low'
    },
    createdAt: '2025-09-28T12:00:00Z',
    updatedAt: '2025-09-28T12:00:00Z'
  },
  {
    id: 'insight-004',
    type: 'alert',
    title: 'Performance Decline Warning',
    description: 'Viktor Petrov showing signs of fatigue with 15% decrease in sprint metrics over last 3 matches.',
    confidence: 78,
    relatedEntityId: 'player-010',
    relatedEntityType: 'player',
    data: {
      metric: 'Sprint distance',
      decline: '15%',
      recommendation: 'Rest rotation advised'
    },
    createdAt: '2025-09-30T08:00:00Z',
    updatedAt: '2025-09-30T08:00:00Z'
  },
  {
    id: 'insight-005',
    type: 'prediction',
    title: 'Match Outcome Analysis',
    description: 'PSG vs Marseille: 68% win probability for PSG based on recent form and head-to-head statistics.',
    confidence: 68,
    relatedEntityId: 'match-004',
    relatedEntityType: 'match',
    data: {
      homeWinProbability: 68,
      drawProbability: 20,
      awayWinProbability: 12,
      keyFactors: ['Home advantage', 'Recent form', 'Squad depth']
    },
    createdAt: '2025-09-30T09:00:00Z',
    updatedAt: '2025-09-30T09:00:00Z'
  }
];

export const mockAnalytics: Analytics = {
  id: 'analytics-dashboard',
  type: 'dashboard',
  predictions: {
    total: 1247,
    accuracy: 87.3
  },
  metrics: {
    totalPlayers: 10,
    totalMatches: 8,
    totalTeams: 10,
    marketValueTracked: 650
  },
  trends: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
};

export const mockTacticalPatterns: TacticalPattern[] = [
  {
    id: 'pattern-001',
    name: 'High Press Trigger',
    description: 'Coordinated pressing when opponent receives ball in defensive third',
    frequency: 18,
    successRate: 72,
    zones: ['Defensive Third', 'Left Channel'],
    impact: 'high',
    trend: 'increasing',
    teamIds: ['team-002', 'team-005'],
    createdAt: '2025-09-01T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'pattern-002',
    name: 'Wing Overload',
    description: 'Overloading wide areas with full-back and winger combinations',
    frequency: 24,
    successRate: 65,
    zones: ['Wide Left', 'Wide Right'],
    impact: 'high',
    trend: 'stable',
    teamIds: ['team-001', 'team-003'],
    createdAt: '2025-09-01T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'pattern-003',
    name: 'Central Build-up',
    description: 'Progressive passing through central midfield lines',
    frequency: 32,
    successRate: 58,
    zones: ['Central Midfield', 'Attacking Third Center'],
    impact: 'medium',
    trend: 'decreasing',
    teamIds: ['team-004', 'team-007'],
    createdAt: '2025-09-01T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'pattern-004',
    name: 'Counter-Attack Speed',
    description: 'Rapid transitions from defense to attack within 5 passes',
    frequency: 15,
    successRate: 78,
    zones: ['All zones'],
    impact: 'high',
    trend: 'increasing',
    teamIds: ['team-005', 'team-009'],
    createdAt: '2025-09-01T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  },
  {
    id: 'pattern-005',
    name: 'Set Piece Routine',
    description: 'Short corner variations with near-post runs',
    frequency: 8,
    successRate: 42,
    zones: ['Penalty Area'],
    impact: 'medium',
    trend: 'stable',
    teamIds: ['team-006', 'team-008'],
    createdAt: '2025-09-01T00:00:00Z',
    updatedAt: '2025-09-30T00:00:00Z'
  }
];
