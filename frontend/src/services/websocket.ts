import { WebSocketMessage, LiveMatchUpdate, Notification } from '../types';

type WebSocketEventHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private isConnecting = false;
  private url: string;

  constructor() {
    this.url = import.meta.env.VITE_WS_URL || 'ws://localhost:3001/ws';
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        return;
      }

      this.isConnecting = true;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit('connected', null);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.emit('disconnected', { code: event.code, reason: event.reason });
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private handleMessage(message: WebSocketMessage): void {
    console.log('WebSocket message received:', message.type);
    
    switch (message.type) {
      case 'connected':
        this.emit('server_connected', message.data);
        break;
      case 'subscribed':
        this.emit('subscribed', message.data);
        break;
      case 'unsubscribed':
        this.emit('unsubscribed', message.data);
        break;
      case 'pong':
        this.emit('pong', message.data);
        break;
      case 'match_update':
        this.emit('match_update', message.data as LiveMatchUpdate);
        break;
      case 'player_update':
        this.emit('player_update', message.data);
        break;
      case 'notification':
        this.emit('notification', message.data as Notification);
        break;
      case 'market_update':
        this.emit('market_update', message.data);
        break;
      case 'tactical_update':
        this.emit('tactical_update', message.data);
        break;
      default:
        console.warn('Unknown message type:', message.type);
    }
  }

  on(event: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }
  }

  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  // Convenience methods for specific subscriptions
  subscribeToMatch(matchId: string): void {
    this.send({
      type: 'subscribe',
      channel: 'match',
      matchId
    });
  }

  unsubscribeFromMatch(matchId: string): void {
    this.send({
      type: 'unsubscribe',
      channel: 'match',
      matchId
    });
  }

  subscribeToPlayer(playerId: string): void {
    this.send({
      type: 'subscribe',
      channel: 'player',
      playerId
    });
  }

  unsubscribeFromPlayer(playerId: string): void {
    this.send({
      type: 'unsubscribe',
      channel: 'player',
      playerId
    });
  }

  subscribeToNotifications(userId: string): void {
    this.send({
      type: 'subscribe',
      channel: 'notifications',
      userId
    });
  }

  subscribeToMarketUpdates(): void {
    this.send({
      type: 'subscribe',
      channel: 'market'
    });
  }

  getConnectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
export default wsService;