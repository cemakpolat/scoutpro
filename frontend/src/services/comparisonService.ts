import {
  ComparisonAttribute,
  ComparisonCategory,
  ComparisonMetric,
  RadarChartData,
  SimilarPlayer,
  SimilaritySearchOptions,
  HeadToHeadStats,
  PlayerComparison,
} from '../types/comparison';
import { Player } from '../types';

class ComparisonService {
  private readonly STORAGE_KEY = 'scoutpro_comparisons';

  /**
   * Get comparison attributes organized by category
   */
  getComparisonAttributes(): ComparisonAttribute[] {
    return [
      {
        category: 'Physical',
        attributes: [
          { name: 'Height', key: 'height', unit: 'cm', maxValue: 200, higher_is_better: true },
          { name: 'Weight', key: 'weight', unit: 'kg', maxValue: 100, higher_is_better: false },
          { name: 'Speed', key: 'speed', maxValue: 100, higher_is_better: true },
          { name: 'Strength', key: 'strength', maxValue: 100, higher_is_better: true },
          { name: 'Stamina', key: 'stamina', maxValue: 100, higher_is_better: true },
        ],
      },
      {
        category: 'Technical',
        attributes: [
          { name: 'Passing', key: 'passing', maxValue: 100, higher_is_better: true },
          { name: 'Dribbling', key: 'dribbling', maxValue: 100, higher_is_better: true },
          { name: 'Shooting', key: 'shooting', maxValue: 100, higher_is_better: true },
          { name: 'Ball Control', key: 'ballControl', maxValue: 100, higher_is_better: true },
          { name: 'Crossing', key: 'crossing', maxValue: 100, higher_is_better: true },
        ],
      },
      {
        category: 'Mental',
        attributes: [
          { name: 'Vision', key: 'vision', maxValue: 100, higher_is_better: true },
          { name: 'Positioning', key: 'positioning', maxValue: 100, higher_is_better: true },
          { name: 'Decision Making', key: 'decisionMaking', maxValue: 100, higher_is_better: true },
          { name: 'Work Rate', key: 'workRate', maxValue: 100, higher_is_better: true },
          { name: 'Composure', key: 'composure', maxValue: 100, higher_is_better: true },
        ],
      },
      {
        category: 'Defensive',
        attributes: [
          { name: 'Tackling', key: 'tackling', maxValue: 100, higher_is_better: true },
          { name: 'Marking', key: 'marking', maxValue: 100, higher_is_better: true },
          { name: 'Interceptions', key: 'interceptions', maxValue: 100, higher_is_better: true },
          { name: 'Heading', key: 'heading', maxValue: 100, higher_is_better: true },
          { name: 'Aggression', key: 'aggression', maxValue: 100, higher_is_better: false },
        ],
      },
      {
        category: 'Performance',
        attributes: [
          { name: 'Goals', key: 'goals', maxValue: 50, higher_is_better: true },
          { name: 'Assists', key: 'assists', maxValue: 30, higher_is_better: true },
          { name: 'Pass Accuracy', key: 'passAccuracy', unit: '%', maxValue: 100, higher_is_better: true },
          { name: 'Shots per Game', key: 'shotsPerGame', maxValue: 10, higher_is_better: true },
          { name: 'Key Passes', key: 'keyPasses', maxValue: 5, higher_is_better: true },
        ],
      },
    ];
  }

  /**
   * Compare two or more players
   */
  comparePlayers(players: any[]): ComparisonCategory[] {
    if (players.length < 2) {
      throw new Error('At least 2 players required for comparison');
    }

    const attributes = this.getComparisonAttributes();
    const categories: ComparisonCategory[] = [];

    attributes.forEach(attrCategory => {
      const metrics: ComparisonMetric[] = [];

      attrCategory.attributes.forEach(attr => {
        const values = players.map(p => this.getPlayerAttributeValue(p, attr.key));

        const metric: ComparisonMetric = {
          name: attr.name,
          player1Value: values[0],
          player2Value: values[1],
          unit: attr.unit,
        };

        // Calculate difference for numeric values
        if (typeof values[0] === 'number' && typeof values[1] === 'number') {
          metric.difference = values[0] - values[1];
          metric.percentageDiff = values[1] !== 0
            ? ((values[0] - values[1]) / values[1]) * 100
            : 0;

          // Determine winner
          if (Math.abs(metric.difference) < 0.01) {
            metric.winner = 'tie';
          } else if (attr.higher_is_better) {
            metric.winner = values[0] > values[1] ? 'player1' : 'player2';
          } else {
            metric.winner = values[0] < values[1] ? 'player1' : 'player2';
          }
        }

        metrics.push(metric);
      });

      categories.push({
        name: attrCategory.category,
        metrics,
      });
    });

    return categories;
  }

  /**
   * Get player attribute value
   */
  private getPlayerAttributeValue(player: any, key: string): number | string {
    // Try direct key
    if (player[key] !== undefined) {
      return player[key];
    }

    // Try stats object
    if (player.stats && player.stats[key] !== undefined) {
      return player.stats[key];
    }

    // Try attributes object
    if (player.attributes && player.attributes[key] !== undefined) {
      return player.attributes[key];
    }

    // Generate mock value based on position and age for demo
    return this.generateMockAttribute(player, key);
  }

  /**
   * Generate mock attribute value (for demo purposes)
   */
  private generateMockAttribute(player: any, key: string): number {
    const baseValue = 50 + Math.random() * 40; // 50-90 range

    // Adjust based on position
    const positionModifiers: Record<string, Record<string, number>> = {
      'Forward': {
        shooting: 20,
        speed: 15,
        dribbling: 10,
        tackling: -20,
        marking: -15,
      },
      'Midfielder': {
        passing: 20,
        vision: 15,
        stamina: 10,
        heading: -10,
      },
      'Defender': {
        tackling: 20,
        marking: 20,
        heading: 15,
        shooting: -20,
        dribbling: -10,
      },
      'Goalkeeper': {
        positioning: 25,
        strength: 10,
        shooting: -30,
        dribbling: -20,
      },
    };

    const modifier = positionModifiers[player.position]?.[key] || 0;
    return Math.min(100, Math.max(0, baseValue + modifier));
  }

  /**
   * Generate radar chart data for comparison
   */
  generateRadarChartData(players: any[], attributes: string[]): RadarChartData {
    const colors = [
      { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgb(16, 185, 129)' },
      { bg: 'rgba(59, 130, 246, 0.2)', border: 'rgb(59, 130, 246)' },
      { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgb(239, 68, 68)' },
      { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgb(245, 158, 11)' },
      { bg: 'rgba(168, 85, 247, 0.2)', border: 'rgb(168, 85, 247)' },
      { bg: 'rgba(236, 72, 153, 0.2)', border: 'rgb(236, 72, 153)' },
    ];

    const datasets = players.map((player, index) => ({
      label: player.name,
      data: attributes.map(attr => this.getPlayerAttributeValue(player, attr) as number),
      backgroundColor: colors[index % colors.length].bg,
      borderColor: colors[index % colors.length].border,
      borderWidth: 2,
      fill: true,
    }));

    return {
      labels: attributes.map(attr => this.formatAttributeName(attr)),
      datasets,
    };
  }

  /**
   * Format attribute name for display
   */
  private formatAttributeName(key: string): string {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim();
  }

  /**
   * Find similar players using ML-powered similarity algorithm
   */
  async findSimilarPlayers(options: SimilaritySearchOptions): Promise<SimilarPlayer[]> {
    // In production, this would call an ML API
    // For now, we'll use a similarity algorithm based on weighted attributes

    const targetPlayer = await this.getPlayerById(options.playerId);
    if (!targetPlayer) {
      throw new Error('Player not found');
    }

    // Mock player database
    const allPlayers = this.getMockPlayers();

    // Calculate similarity scores
    const similarities = allPlayers
      .filter(p => p.id !== targetPlayer.id)
      .map(player => ({
        player,
        score: this.calculateSimilarityScore(targetPlayer, player, options),
      }))
      .filter(({ score }) => score >= (options.minSimilarity || 50))
      .sort((a, b) => b.score - a.score)
      .slice(0, options.limit || 10);

    // Convert to SimilarPlayer format
    return similarities.map(({ player, score }) => ({
      id: player.id,
      name: player.name,
      position: player.position,
      age: player.age,
      club: player.club,
      nationality: player.nationality,
      similarityScore: Math.round(score),
      matchingAttributes: this.getMatchingAttributes(targetPlayer, player),
      image: player.image,
      marketValue: player.marketValue,
    }));
  }

  /**
   * Calculate similarity score between two players
   */
  private calculateSimilarityScore(
    player1: any,
    player2: any,
    options: SimilaritySearchOptions
  ): number {
    let totalScore = 0;
    let weights = 0;

    // Position similarity (high weight)
    if (options.samePosition && player1.position !== player2.position) {
      return 0;
    }
    if (player1.position === player2.position) {
      totalScore += 20;
    }
    weights += 20;

    // Age similarity
    const ageDiff = Math.abs(player1.age - player2.age);
    const ageScore = Math.max(0, 10 - ageDiff) * 1.5; // 15 points max
    totalScore += ageScore;
    weights += 15;

    // Attribute similarity
    const attributes = options.attributes || [
      'passing', 'dribbling', 'shooting', 'speed', 'stamina',
      'tackling', 'marking', 'vision', 'positioning'
    ];

    attributes.forEach(attr => {
      const val1 = this.getPlayerAttributeValue(player1, attr) as number;
      const val2 = this.getPlayerAttributeValue(player2, attr) as number;
      const diff = Math.abs(val1 - val2);
      const attrScore = Math.max(0, 100 - diff) / 100 * 7; // 7 points per attribute
      totalScore += attrScore;
      weights += 7;
    });

    // League similarity (bonus)
    if (options.sameLeague && player1.league === player2.league) {
      totalScore += 10;
      weights += 10;
    }

    return (totalScore / weights) * 100;
  }

  /**
   * Get matching attributes between players
   */
  private getMatchingAttributes(player1: any, player2: any): string[] {
    const attributes = [
      'position', 'age', 'nationality', 'height', 'foot',
      'passing', 'dribbling', 'shooting', 'speed'
    ];

    return attributes.filter(attr => {
      const val1 = this.getPlayerAttributeValue(player1, attr);
      const val2 = this.getPlayerAttributeValue(player2, attr);

      if (typeof val1 === 'string') {
        return val1 === val2;
      }

      if (typeof val1 === 'number' && typeof val2 === 'number') {
        return Math.abs(val1 - val2) < 10; // Within 10 points
      }

      return false;
    });
  }

  /**
   * Get head-to-head statistics
   */
  async getHeadToHeadStats(player1Id: string, player2Id: string): Promise<HeadToHeadStats> {
    // Mock head-to-head data
    return {
      player1: {
        id: player1Id,
        name: 'Player 1',
        wins: 5,
        draws: 3,
        losses: 2,
        goalsScored: 12,
        assists: 8,
      },
      player2: {
        id: player2Id,
        name: 'Player 2',
        wins: 2,
        draws: 3,
        losses: 5,
        goalsScored: 8,
        assists: 6,
      },
      matches: [
        {
          date: '2024-09-15',
          competition: 'Premier League',
          result: '2-1',
          player1Stats: { goals: 1, assists: 1 },
          player2Stats: { goals: 0, assists: 0 },
        },
        {
          date: '2024-08-20',
          competition: 'Premier League',
          result: '1-1',
          player1Stats: { goals: 1, assists: 0 },
          player2Stats: { goals: 1, assists: 0 },
        },
      ],
    };
  }

  /**
   * Save comparison
   */
  saveComparison(name: string, playerIds: string[]): PlayerComparison {
    const comparisons = this.getSavedComparisons();
    const newComparison: PlayerComparison = {
      id: `comparison-${Date.now()}`,
      name,
      players: playerIds,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    comparisons.push(newComparison);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(comparisons));

    return newComparison;
  }

  /**
   * Get saved comparisons
   */
  getSavedComparisons(): PlayerComparison[] {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  }

  /**
   * Delete comparison
   */
  deleteComparison(id: string): void {
    const comparisons = this.getSavedComparisons().filter(c => c.id !== id);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(comparisons));
  }

  /**
   * Get player by ID (mock)
   */
  private async getPlayerById(id: string): Promise<any> {
    const players = this.getMockPlayers();
    return players.find(p => p.id === id) || players[0];
  }

  /**
   * Get mock players database
   */
  private getMockPlayers(): any[] {
    return [
      {
        id: 'p1',
        name: 'Kylian Mbappé',
        position: 'Forward',
        age: 25,
        club: 'Real Madrid',
        nationality: 'France',
        league: 'La Liga',
        height: 178,
        foot: 'Right',
        marketValue: '€180M',
        image: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=100',
      },
      {
        id: 'p2',
        name: 'Erling Haaland',
        position: 'Forward',
        age: 24,
        club: 'Manchester City',
        nationality: 'Norway',
        league: 'Premier League',
        height: 194,
        foot: 'Left',
        marketValue: '€170M',
      },
      {
        id: 'p3',
        name: 'Vinicius Junior',
        position: 'Forward',
        age: 24,
        club: 'Real Madrid',
        nationality: 'Brazil',
        league: 'La Liga',
        height: 176,
        foot: 'Right',
        marketValue: '€150M',
      },
      {
        id: 'p4',
        name: 'Jude Bellingham',
        position: 'Midfielder',
        age: 21,
        club: 'Real Madrid',
        nationality: 'England',
        league: 'La Liga',
        height: 186,
        foot: 'Right',
        marketValue: '€150M',
      },
      {
        id: 'p5',
        name: 'Pedri',
        position: 'Midfielder',
        age: 22,
        club: 'Barcelona',
        nationality: 'Spain',
        league: 'La Liga',
        height: 174,
        foot: 'Right',
        marketValue: '€100M',
      },
      {
        id: 'p6',
        name: 'Kevin De Bruyne',
        position: 'Midfielder',
        age: 33,
        club: 'Manchester City',
        nationality: 'Belgium',
        league: 'Premier League',
        height: 181,
        foot: 'Right',
        marketValue: '€70M',
      },
      {
        id: 'p7',
        name: 'Virgil van Dijk',
        position: 'Defender',
        age: 33,
        club: 'Liverpool',
        nationality: 'Netherlands',
        league: 'Premier League',
        height: 193,
        foot: 'Right',
        marketValue: '€45M',
      },
      {
        id: 'p8',
        name: 'Antonio Rüdiger',
        position: 'Defender',
        age: 31,
        club: 'Real Madrid',
        nationality: 'Germany',
        league: 'La Liga',
        height: 190,
        foot: 'Right',
        marketValue: '€35M',
      },
    ];
  }
}

export const comparisonService = new ComparisonService();
