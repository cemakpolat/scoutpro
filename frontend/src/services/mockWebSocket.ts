import { mockMatches } from '../data/matchesMockData';
import { mockPlayers } from '../data/playersMockData';
import { mockNotifications } from '../data/otherMockData';

type WebSocketMessageType = 'match_update' | 'player_update' | 'notification' | 'market_update' | 'tactical_update';
type CallbackFunction = (data: any) => void;

class MockWebSocketService {
  private subscribers: Map<WebSocketMessageType, Set<CallbackFunction>> = new Map();
  private intervalIds: number[] = [];
  private isRunning: boolean = false;

  constructor() {
    // Initialize subscriber maps
    const types: WebSocketMessageType[] = [
      'match_update',
      'player_update',
      'notification',
      'market_update',
      'tactical_update'
    ];

    types.forEach(type => {
      this.subscribers.set(type, new Set());
    });
  }

  /**
   * Start sending mock updates
   */
  start() {
    if (this.isRunning) return;

    this.isRunning = true;
    console.log('[MockWebSocket] Starting mock updates...');

    // Send live match updates every 5 seconds
    const matchInterval = window.setInterval(() => {
      this.sendLiveMatchUpdates();
    }, 5000);
    this.intervalIds.push(matchInterval);

    // Send player updates every 15 seconds
    const playerInterval = window.setInterval(() => {
      this.sendPlayerUpdate();
    }, 15000);
    this.intervalIds.push(playerInterval);

    // Send notifications every 20 seconds
    const notificationInterval = window.setInterval(() => {
      this.sendNotification();
    }, 20000);
    this.intervalIds.push(notificationInterval);

    // Send market updates every 30 seconds
    const marketInterval = window.setInterval(() => {
      this.sendMarketUpdate();
    }, 30000);
    this.intervalIds.push(marketInterval);
  }

  /**
   * Stop sending mock updates
   */
  stop() {
    if (!this.isRunning) return;

    this.isRunning = false;
    this.intervalIds.forEach(id => window.clearInterval(id));
    this.intervalIds = [];
    console.log('[MockWebSocket] Stopped mock updates');
  }

  /**
   * Subscribe to a message type
   */
  subscribe(type: WebSocketMessageType, callback: CallbackFunction): () => void {
    const callbacks = this.subscribers.get(type);
    if (callbacks) {
      callbacks.add(callback);
    }

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(type);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  /**
   * Emit an event to all subscribers
   */
  private emit(type: WebSocketMessageType, data: any) {
    const callbacks = this.subscribers.get(type);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[MockWebSocket] Error in callback for ${type}:`, error);
        }
      });
    }
  }

  /**
   * Send live match updates
   */
  private sendLiveMatchUpdates() {
    const liveMatches = mockMatches.filter(m => m.status === 'live');

    if (liveMatches.length === 0) {
      console.log('[MockWebSocket] No live matches found');
      return;
    }

    console.log(`[MockWebSocket] Sending updates for ${liveMatches.length} live matches`);

    liveMatches.forEach(match => {
      // Simulate random events
      const eventTypes = ['possession_change', 'shot', 'corner', 'foul', 'card'];
      const randomEvent = eventTypes[Math.floor(Math.random() * eventTypes.length)];

      const update = {
        matchId: match.id,
        minute: Math.floor(Math.random() * 90) + 1,
        score: {
          home: match.homeScore,
          away: match.awayScore
        },
        event: {
          type: randomEvent,
          team: Math.random() > 0.5 ? 'home' : 'away',
          description: `${randomEvent} event occurred`
        },
        stats: {
          possession: {
            home: match.homePossession + Math.floor(Math.random() * 5) - 2,
            away: match.awayPossession + Math.floor(Math.random() * 5) - 2
          },
          shots: {
            home: match.homeShots,
            away: match.awayShots
          },
          xG: {
            home: match.homeXG,
            away: match.awayXG
          }
        },
        timestamp: new Date().toISOString()
      };

      console.log(`[MockWebSocket] Match update for ${match.id}:`, update);
      this.emit('match_update', update);
    });
  }

  /**
   * Send player performance update
   */
  private sendPlayerUpdate() {
    const randomPlayer = mockPlayers[Math.floor(Math.random() * mockPlayers.length)];

    const update = {
      ...randomPlayer,
      rating: randomPlayer.rating + (Math.random() * 0.4 - 0.2), // Slight rating change
      marketValue: randomPlayer.marketValue,
      recentForm: Array.from({ length: 5 }, () =>
        Math.floor(Math.random() * 10) + 1
      ),
      timestamp: new Date().toISOString()
    };

    this.emit('player_update', update);
  }

  /**
   * Send new notification
   */
  private sendNotification() {
    const notificationTypes = [
      {
        type: 'performance' as const,
        title: 'Performance Alert',
        message: `${mockPlayers[0].name} exceptional performance in recent match`,
        priority: 'high' as const
      },
      {
        type: 'market' as const,
        title: 'Market Update',
        message: 'Market values updated for 15 players',
        priority: 'medium' as const
      },
      {
        type: 'tactical' as const,
        title: 'Tactical Insight',
        message: 'New pressing pattern detected in top leagues',
        priority: 'low' as const
      }
    ];

    const randomNotification = notificationTypes[Math.floor(Math.random() * notificationTypes.length)];

    const notification = {
      id: `notif-${Date.now()}`,
      ...randomNotification,
      read: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      timestamp: new Date().toISOString()
    };

    this.emit('notification', notification);
  }

  /**
   * Send market update
   */
  private sendMarketUpdate() {
    const positions = ['ST', 'CM', 'CB', 'RW', 'GK'];
    const randomPosition = positions[Math.floor(Math.random() * positions.length)];

    const update = {
      position: randomPosition,
      averageValue: `€${Math.floor(Math.random() * 50 + 30)}M`,
      change: `${Math.random() > 0.5 ? '+' : '-'}${Math.floor(Math.random() * 10)}%`,
      trend: Math.random() > 0.5 ? 'up' : 'down',
      timestamp: new Date().toISOString()
    };

    this.emit('market_update', update);
  }

  /**
   * Manually send a match goal update
   */
  sendGoalUpdate(matchId: string, scoringTeam: 'home' | 'away') {
    const match = mockMatches.find(m => m.id === matchId);
    if (!match) return;

    const newScore = {
      home: scoringTeam === 'home' ? match.homeScore + 1 : match.homeScore,
      away: scoringTeam === 'away' ? match.awayScore + 1 : match.awayScore
    };

    const update = {
      matchId,
      minute: Math.floor(Math.random() * 90) + 1,
      score: newScore,
      event: {
        type: 'goal',
        team: scoringTeam,
        player: mockPlayers[0].name,
        description: `GOAL! ${mockPlayers[0].name} scores!`
      },
      stats: {
        possession: {
          home: match.homePossession,
          away: match.awayPossession
        },
        shots: {
          home: scoringTeam === 'home' ? match.homeShots + 1 : match.homeShots,
          away: scoringTeam === 'away' ? match.awayShots + 1 : match.awayShots
        }
      },
      timestamp: new Date().toISOString()
    };

    this.emit('match_update', update);
  }
}

// Create singleton instance
const mockWebSocketService = new MockWebSocketService();

export default mockWebSocketService;
