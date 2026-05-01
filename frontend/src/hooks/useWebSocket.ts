import { useEffect, useCallback, useRef } from 'react';
import wsService from '../services/websocket';

// Global flag to ensure WebSocket is only started once
let globalWebSocketInitialized = false;
let realWebSocketConsumers = 0;
let pendingDisconnectTimer: ReturnType<typeof setTimeout> | null = null;

export function useWebSocket() {
  const isInitialized = useRef(false);

  useEffect(() => {
    if (pendingDisconnectTimer) {
      clearTimeout(pendingDisconnectTimer);
      pendingDisconnectTimer = null;
    }

    if (!isInitialized.current) {
      realWebSocketConsumers += 1;
      isInitialized.current = true;
    }

    if (!globalWebSocketInitialized) {
      globalWebSocketInitialized = true;

      wsService.connect().catch(error => {
        globalWebSocketInitialized = false;
        console.error('Failed to connect to WebSocket:', error);
      });
    }

    return () => {
      if (isInitialized.current) {
        isInitialized.current = false;
        realWebSocketConsumers = Math.max(0, realWebSocketConsumers - 1);

        if (realWebSocketConsumers === 0) {
          pendingDisconnectTimer = setTimeout(() => {
            if (realWebSocketConsumers === 0) {
              wsService.disconnect();
              globalWebSocketInitialized = false;
            }

            pendingDisconnectTimer = null;
          }, 250);
        }
      }
    };
  }, []);

  const subscribe = useCallback((event: string, handler: (data: any) => void) => {
    wsService.on(event, handler);
    return () => {
      wsService.off(event, handler);
    };
  }, []);

  const send = useCallback((message: any) => {
    wsService.send(message);
  }, []);

  const subscribeToMatch = useCallback((matchId: string) => {
    wsService.subscribeToMatch(matchId);
  }, []);

  const unsubscribeFromMatch = useCallback((matchId: string) => {
    wsService.unsubscribeFromMatch(matchId);
  }, []);

  const subscribeToPlayer = useCallback((playerId: string) => {
    wsService.subscribeToPlayer(playerId);
  }, []);

  const unsubscribeFromPlayer = useCallback((playerId: string) => {
    wsService.unsubscribeFromPlayer(playerId);
  }, []);

  const subscribeToNotifications = useCallback((userId: string) => {
    wsService.subscribeToNotifications(userId);
  }, []);

  const subscribeToMarketUpdates = useCallback(() => {
    wsService.subscribeToMarketUpdates();
  }, []);

  return {
    subscribe,
    send,
    subscribeToMatch,
    unsubscribeFromMatch,
    subscribeToPlayer,
    unsubscribeFromPlayer,
    subscribeToNotifications,
    subscribeToMarketUpdates,
    isConnected: wsService.isConnected(),
    connectionState: wsService.getConnectionState()
  };
}

export function useLiveMatch(matchId: string) {
  const { subscribe, subscribeToMatch, unsubscribeFromMatch } = useWebSocket();

  useEffect(() => {
    if (matchId) {
      subscribeToMatch(matchId);
      
      return () => {
        unsubscribeFromMatch(matchId);
      };
    }
  }, [matchId, subscribeToMatch, unsubscribeFromMatch]);

  const onMatchUpdate = useCallback((handler: (data: any) => void) => {
    return subscribe('match_update', handler);
  }, [subscribe]);

  return {
    onMatchUpdate
  };
}

export function useLiveNotifications(userId?: string) {
  const { subscribe, subscribeToNotifications } = useWebSocket();

  useEffect(() => {
    if (userId) {
      subscribeToNotifications(userId);
    }
  }, [userId, subscribeToNotifications]);

  const onNotification = useCallback((handler: (data: any) => void) => {
    return subscribe('notification', handler);
  }, [subscribe]);

  return {
    onNotification
  };
}