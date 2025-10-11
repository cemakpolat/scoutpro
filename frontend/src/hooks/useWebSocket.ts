import { useEffect, useCallback, useRef } from 'react';
import wsService from '../services/websocket';
import mockWebSocketService from '../services/mockWebSocket';

// Determine which service to use based on environment
const useMockWebSocket = import.meta.env.VITE_USE_MOCK_DATA === 'true';
const activeWsService = useMockWebSocket ? mockWebSocketService : wsService;

// Global flag to ensure WebSocket is only started once
let globalWebSocketInitialized = false;

export function useWebSocket() {
  const isInitialized = useRef(false);

  useEffect(() => {
    if (useMockWebSocket) {
      // Mock WebSocket auto-starts (only once globally)
      if (!globalWebSocketInitialized && !isInitialized.current) {
        console.log('[useWebSocket] Starting mock WebSocket service');
        mockWebSocketService.start();
        isInitialized.current = true;
        globalWebSocketInitialized = true;
      }
      // Don't stop on unmount since this is a global service
      return () => {
        // Keep the service running for other components
      };
    } else {
      // Real WebSocket connection
      if (!isInitialized.current) {
        wsService.connect().catch(error => {
          console.error('Failed to connect to WebSocket:', error);
        });
        isInitialized.current = true;
      }

      return () => {
        if (isInitialized.current) {
          wsService.disconnect();
          isInitialized.current = false;
        }
      };
    }
  }, []);

  const subscribe = useCallback((event: string, handler: (data: any) => void) => {
    if (useMockWebSocket) {
      return mockWebSocketService.subscribe(event as any, handler);
    } else {
      wsService.on(event, handler);
      return () => {
        wsService.off(event, handler);
      };
    }
  }, []);

  const send = useCallback((message: any) => {
    if (!useMockWebSocket) {
      wsService.send(message);
    }
  }, []);

  const subscribeToMatch = useCallback((matchId: string) => {
    if (!useMockWebSocket) {
      wsService.subscribeToMatch(matchId);
    }
  }, []);

  const unsubscribeFromMatch = useCallback((matchId: string) => {
    if (!useMockWebSocket) {
      wsService.unsubscribeFromMatch(matchId);
    }
  }, []);

  const subscribeToPlayer = useCallback((playerId: string) => {
    if (!useMockWebSocket) {
      wsService.subscribeToPlayer(playerId);
    }
  }, []);

  const unsubscribeFromPlayer = useCallback((playerId: string) => {
    if (!useMockWebSocket) {
      wsService.unsubscribeFromPlayer(playerId);
    }
  }, []);

  const subscribeToNotifications = useCallback((userId: string) => {
    if (!useMockWebSocket) {
      wsService.subscribeToNotifications(userId);
    }
  }, []);

  const subscribeToMarketUpdates = useCallback(() => {
    if (!useMockWebSocket) {
      wsService.subscribeToMarketUpdates();
    }
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
    isConnected: useMockWebSocket ? true : wsService.isConnected(),
    connectionState: useMockWebSocket ? 'connected' : wsService.getConnectionState()
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