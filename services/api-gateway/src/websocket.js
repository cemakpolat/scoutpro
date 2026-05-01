/**
 * WebSocket Server - Integrated into API Gateway
 * Provides real-time updates for live matches, notifications,
 * player updates, market changes, tactical events, and background task completions.
 */
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

class WebSocketManager {
  constructor(server, db) {
    this.wss = new WebSocket.Server({ server, path: '/ws' });
    this.db = db;
    this.clients = new Map(); // clientId -> { ws, subscriptions }
    this.simulationIntervals = [];
    this.enableSimulation = process.env.ENABLE_WS_SIMULATION === 'true';

    this.wss.on('connection', (ws, req) => {
      const clientId = uuidv4();
      this.clients.set(clientId, {
        ws,
        subscriptions: new Set(),
        connectedAt: new Date().toISOString()
      });

      console.log(`[WS] Client connected: ${clientId} (total: ${this.clients.size})`);

      // Send welcome message
      this.sendTo(ws, {
        type: 'connected',
        data: { clientId, message: 'Connected to ScoutPro WebSocket' }
      });

      ws.on('message', (raw) => {
        try {
          const message = JSON.parse(raw.toString());
          this.handleMessage(clientId, message);
        } catch (err) {
          console.error('[WS] Invalid message:', err.message);
        }
      });

      ws.on('close', () => {
        this.clients.delete(clientId);
        console.log(`[WS] Client disconnected: ${clientId} (total: ${this.clients.size})`);
      });

      ws.on('error', (err) => {
        console.error(`[WS] Client error ${clientId}:`, err.message);
        this.clients.delete(clientId);
      });
    });

    if (this.enableSimulation) {
      this.startSimulations();
    } else {
      console.log('WebSocket simulations disabled; waiting for real upstream events');
    }

    this._taskKafkaConsumer = null;
    this._startTaskCompletionBridge().catch(err =>
      console.warn('[WS] Task completion Kafka bridge not started:', err.message)
    );

    console.log('✅ WebSocket server initialized on /ws');
  }

  async _startTaskCompletionBridge() {
    let Kafka;
    try {
      Kafka = require('kafkajs').Kafka;
    } catch {
      console.warn('[WS] kafkajs not available — task completion bridge disabled');
      return;
    }
    const brokers = (process.env.KAFKA_BOOTSTRAP_SERVERS || 'kafka:9092').split(',');
    const kafka = new Kafka({ clientId: 'api-gateway-ws', brokers });
    const consumer = kafka.consumer({ groupId: 'api-gateway-ws-group' });
    await consumer.connect();
    await consumer.subscribe({ topic: 'task.completed', fromBeginning: false });
    this._taskKafkaConsumer = consumer;

    await consumer.run({
      eachMessage: async ({ message }) => {
        try {
          const event = JSON.parse(message.value.toString());
          // Broadcast to all clients subscribed to 'tasks' or 'general'
          this.broadcast('task_completed', event, 'tasks');
        } catch (err) {
          console.error('[WS] Bad task.completed message:', err.message);
        }
      },
    });
    console.log('[WS] Subscribed to Kafka task.completed topic');
  }

  handleMessage(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client) return;

    switch (message.type) {
      case 'subscribe':
        this.handleSubscribe(clientId, message);
        break;
      case 'unsubscribe':
        this.handleUnsubscribe(clientId, message);
        break;
      case 'ping':
        this.sendTo(client.ws, { type: 'pong', data: { timestamp: Date.now() } });
        break;
      default:
        console.log(`[WS] Unknown message type: ${message.type}`);
    }
  }

  handleSubscribe(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client) return;

    const channel = message.channel || message.matchId || message.playerId || 'general';
    client.subscriptions.add(channel);

    this.sendTo(client.ws, {
      type: 'subscribed',
      data: { channel, subscriptions: Array.from(client.subscriptions) }
    });

    console.log(`[WS] Client ${clientId} subscribed to: ${channel}`);
  }

  handleUnsubscribe(clientId, message) {
    const client = this.clients.get(clientId);
    if (!client) return;

    const channel = message.channel || message.matchId || message.playerId;
    client.subscriptions.delete(channel);

    this.sendTo(client.ws, {
      type: 'unsubscribed',
      data: { channel, subscriptions: Array.from(client.subscriptions) }
    });
  }

  sendTo(ws, message) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  broadcast(type, data, channel = null) {
    const message = JSON.stringify({ type, data, timestamp: new Date().toISOString() });
    
    this.clients.forEach((client) => {
      if (client.ws.readyState !== WebSocket.OPEN) return;
      
      // If a channel is specified, only send to subscribers
      if (channel && !client.subscriptions.has(channel) && !client.subscriptions.has('general')) {
        return;
      }
      
      client.ws.send(message);
    });
  }

  // ===== Live Simulation Loops =====

  startSimulations() {
    // Live match updates every 5 seconds
    this.simulationIntervals.push(
      setInterval(() => this.sendLiveMatchUpdates(), 5000)
    );

    // Notification updates every 20 seconds
    this.simulationIntervals.push(
      setInterval(() => this.sendNotificationUpdate(), 20000)
    );

    // Market updates every 30 seconds
    this.simulationIntervals.push(
      setInterval(() => this.sendMarketUpdate(), 30000)
    );

    // Player stat updates every 15 seconds
    this.simulationIntervals.push(
      setInterval(() => this.sendPlayerUpdate(), 15000)
    );

    // Tactical updates every 25 seconds
    this.simulationIntervals.push(
      setInterval(() => this.sendTacticalUpdate(), 25000)
    );
  }

  async sendLiveMatchUpdates() {
    if (this.clients.size === 0) return;

    try {
      let liveMatches = [];
      if (this.db) {
        liveMatches = await this.db.collection('matches')
          .find({ status: 'live' })
          .toArray();
      }

      // If no live matches in DB, simulate one
      if (liveMatches.length === 0) {
        liveMatches = [{
          id: 'live-sim-1',
          homeTeam: 'Barcelona',
          awayTeam: 'Real Madrid',
          homeScore: Math.floor(Math.random() * 3),
          awayScore: Math.floor(Math.random() * 3),
          status: 'live'
        }];
      }

      liveMatches.forEach(match => {
        const minute = Math.floor(Math.random() * 90) + 1;
        const eventTypes = ['possession_change', 'shot', 'corner', 'foul', 'pass_completed', 'tackle'];
        const randomEvent = eventTypes[Math.floor(Math.random() * eventTypes.length)];

        const homePoss = 45 + Math.floor(Math.random() * 20);

        this.broadcast('match_update', {
          matchId: match.id || match._id?.toString(),
          minute,
          score: {
            home: match.homeScore || 0,
            away: match.awayScore || 0
          },
          event: {
            type: randomEvent,
            team: Math.random() > 0.5 ? 'home' : 'away',
            minute,
            description: `${randomEvent.replace('_', ' ')} at minute ${minute}`
          },
          stats: {
            possession: { home: homePoss, away: 100 - homePoss },
            shots: {
              home: Math.floor(Math.random() * 15),
              away: Math.floor(Math.random() * 15)
            },
            xG: {
              home: +(Math.random() * 3).toFixed(2),
              away: +(Math.random() * 3).toFixed(2)
            }
          }
        }, 'match');
      });
    } catch (err) {
      // Silently fail for simulation
    }
  }

  sendNotificationUpdate() {
    if (this.clients.size === 0) return;

    const types = ['transfer_alert', 'match_reminder', 'scouting_update', 'system', 'player_alert'];
    const type = types[Math.floor(Math.random() * types.length)];

    const messages = {
      transfer_alert: 'New transfer rumor: Player X linked to Club Y',
      match_reminder: 'Match starting in 30 minutes: Team A vs Team B',
      scouting_update: 'New scouting report available for Player Z',
      system: 'System update: New analytics features available',
      player_alert: 'Player performance alert: Rating change detected'
    };

    this.broadcast('notification', {
      id: uuidv4(),
      type,
      title: type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()),
      message: messages[type],
      read: false,
      createdAt: new Date().toISOString(),
      priority: Math.random() > 0.7 ? 'high' : 'normal'
    }, 'notifications');
  }

  sendMarketUpdate() {
    if (this.clients.size === 0) return;

    const players = ['Mbappé', 'Haaland', 'Bellingham', 'Saka', 'Pedri', 'Musiala'];
    const player = players[Math.floor(Math.random() * players.length)];
    const change = (Math.random() * 20 - 10).toFixed(1);

    this.broadcast('market_update', {
      player,
      currentValue: Math.floor(Math.random() * 150 + 50),
      change: parseFloat(change),
      trend: parseFloat(change) > 0 ? 'up' : 'down',
      currency: 'EUR',
      unit: 'M',
      timestamp: new Date().toISOString()
    }, 'market');
  }

  sendPlayerUpdate() {
    if (this.clients.size === 0) return;

    const names = ['K. Mbappé', 'E. Haaland', 'J. Bellingham', 'B. Saka', 'Pedri'];
    const name = names[Math.floor(Math.random() * names.length)];

    this.broadcast('player_update', {
      playerId: `p${Math.floor(Math.random() * 20) + 1}`,
      name,
      stat: 'rating',
      oldValue: (7 + Math.random()).toFixed(1),
      newValue: (7 + Math.random()).toFixed(1),
      reason: 'Recent match performance',
      timestamp: new Date().toISOString()
    }, 'player');
  }

  sendTacticalUpdate() {
    if (this.clients.size === 0) return;

    const formations = ['4-3-3', '4-4-2', '3-5-2', '4-2-3-1', '5-3-2'];
    const patterns = ['High Press', 'Counter Attack', 'Tiki-Taka', 'Wing Play', 'Long Ball'];

    this.broadcast('tactical_update', {
      team: ['Barcelona', 'Manchester City', 'Bayern Munich', 'Liverpool'][Math.floor(Math.random() * 4)],
      formation: formations[Math.floor(Math.random() * formations.length)],
      pattern: patterns[Math.floor(Math.random() * patterns.length)],
      effectiveness: Math.floor(Math.random() * 30 + 70),
      timestamp: new Date().toISOString()
    }, 'tactical');
  }

  stop() {
    this.simulationIntervals.forEach(id => clearInterval(id));
    this.simulationIntervals = [];
    if (this._taskKafkaConsumer) {
      this._taskKafkaConsumer.disconnect().catch(() => {});
    }
    this.wss.close();
  }

  getStats() {
    return {
      connectedClients: this.clients.size,
      clients: Array.from(this.clients.entries()).map(([id, c]) => ({
        id,
        subscriptions: Array.from(c.subscriptions),
        connectedAt: c.connectedAt
      }))
    };
  }
}

module.exports = WebSocketManager;
