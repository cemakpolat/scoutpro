// Player comparison types

export interface PlayerComparison {
  id: string;
  name: string;
  players: string[]; // player IDs
  createdAt: string;
  updatedAt: string;
}

export interface ComparisonAttribute {
  category: string;
  attributes: {
    name: string;
    key: string;
    unit?: string;
    maxValue?: number;
    higher_is_better?: boolean;
  }[];
}

export interface RadarChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
    borderWidth?: number;
    fill?: boolean;
  }[];
}

export interface ComparisonMetric {
  name: string;
  player1Value: number | string;
  player2Value: number | string;
  difference?: number;
  percentageDiff?: number;
  winner?: 'player1' | 'player2' | 'tie';
  unit?: string;
}

export interface ComparisonCategory {
  name: string;
  metrics: ComparisonMetric[];
}

export interface SimilarPlayer {
  id: string;
  name: string;
  position: string;
  age: number;
  club: string;
  nationality: string;
  similarityScore: number; // 0-100
  matchingAttributes: string[];
  image?: string;
  marketValue?: string;
}

export interface SimilaritySearchOptions {
  playerId: string;
  limit?: number;
  minSimilarity?: number;
  samePosition?: boolean;
  sameLeague?: boolean;
  ageRange?: {
    min?: number;
    max?: number;
  };
  attributes?: string[]; // which attributes to compare
}

export interface HeadToHeadStats {
  player1: {
    id: string;
    name: string;
    wins: number;
    draws: number;
    losses: number;
    goalsScored: number;
    assists: number;
    cleanSheets?: number;
  };
  player2: {
    id: string;
    name: string;
    wins: number;
    draws: number;
    losses: number;
    goalsScored: number;
    assists: number;
    cleanSheets?: number;
  };
  matches: {
    date: string;
    competition: string;
    result: string;
    player1Stats: any;
    player2Stats: any;
  }[];
}
