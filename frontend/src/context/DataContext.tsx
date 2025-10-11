import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { Player, Match, Team, Notification, TacticalPattern, MarketTrend } from '../types';
import { useWebSocket } from '../hooks/useWebSocket';
import { useApi } from '../hooks/useApi'; // Import useApi
import apiService from '../services/api'; // Import apiService

interface DataState {
  players: Player[];
  matches: Match[];
  teams: Team[];
  notifications: Notification[];
  tacticalPatterns: TacticalPattern[];
  marketTrends: MarketTrend[];
  loading: {
    players: boolean;
    matches: boolean;
    teams: boolean;
    notifications: boolean;
  };
  errors: {
    players: string | null;
    matches: string | null;
    teams: string | null;
    notifications: string | null;
  };
}

type DataAction = 
  | { type: 'SET_PLAYERS'; payload: Player[] }
  | { type: 'SET_MATCHES'; payload: Match[] }
  | { type: 'SET_TEAMS'; payload: Team[] }
  | { type: 'SET_NOTIFICATIONS'; payload: Notification[] }
  | { type: 'SET_TACTICAL_PATTERNS'; payload: TacticalPattern[] }
  | { type: 'SET_MARKET_TRENDS'; payload: MarketTrend[] }
  | { type: 'UPDATE_PLAYER'; payload: Player }
  | { type: 'UPDATE_MATCH'; payload: Match }
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'MARK_NOTIFICATION_READ'; payload: string }
  | { type: 'SET_LOADING'; payload: { key: keyof DataState['loading']; value: boolean } }
  | { type: 'SET_ERROR'; payload: { key: keyof DataState['errors']; value: string | null } };

const initialState: DataState = {
  players: [],
  matches: [],
  teams: [],
  notifications: [],
  tacticalPatterns: [],
  marketTrends: [],
  loading: {
    players: false,
    matches: false,
    teams: false,
    notifications: false,
  },
  errors: {
    players: null,
    matches: null,
    teams: null,
    notifications: null,
  },
};

function dataReducer(state: DataState, action: DataAction): DataState {
  switch (action.type) {
    case 'SET_PLAYERS':
      return { ...state, players: action.payload };
    case 'SET_MATCHES':
      return { ...state, matches: action.payload };
    case 'SET_TEAMS':
      return { ...state, teams: action.payload };
    case 'SET_NOTIFICATIONS':
      return { ...state, notifications: action.payload };
    case 'SET_TACTICAL_PATTERNS':
      return { ...state, tacticalPatterns: action.payload };
    case 'SET_MARKET_TRENDS':
      return { ...state, marketTrends: action.payload };
    case 'UPDATE_PLAYER':
      return {
        ...state,
        players: state.players.map(player =>
          player.id === action.payload.id ? action.payload : player
        ),
      };
    case 'UPDATE_MATCH':
      return {
        ...state,
        matches: state.matches.map(match =>
          match.id === action.payload.id ? action.payload : match
        ),
      };
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [action.payload, ...state.notifications],
      };
    case 'MARK_NOTIFICATION_READ':
      return {
        ...state,
        notifications: state.notifications.map(notification =>
          notification.id === action.payload
            ? { ...notification, read: true }
            : notification
        ),
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: { ...state.loading, [action.payload.key]: action.payload.value },
      };
    case 'SET_ERROR':
      return {
        ...state,
        errors: { ...state.errors, [action.payload.key]: action.payload.value },
      };
    default:
      return state;
  }
}

interface DataContextType extends DataState {
  dispatch: React.Dispatch<DataAction>;
  refreshPlayers: () => void;
  refreshMatches: () => void;
  refreshTeams: () => void;
  refreshNotifications: () => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

interface DataProviderProps {
  children: ReactNode;
}

export function DataProvider({ children }: DataProviderProps) {
  const [state, dispatch] = useReducer(dataReducer, initialState);
  const { subscribe } = useWebSocket();

  // Fetch initial data using useApi
  const { data: playersData, loading: playersLoading, error: playersError, refetch: refetchPlayers } = useApi(
    () => apiService.getPlayers(), []
  );
  const { data: matchesData, loading: matchesLoading, error: matchesError, refetch: refetchMatches } = useApi(
    () => apiService.getMatches(), []
  );
  const { data: teamsData, loading: teamsLoading, error: teamsError, refetch: refetchTeams } = useApi(
    () => apiService.getTeams(), []
  );
  const { data: notificationsData, loading: notificationsLoading, error: notificationsError, refetch: refetchNotifications } = useApi(
    () => apiService.getNotifications(), []
  );

  useEffect(() => {
    if (playersData) dispatch({ type: 'SET_PLAYERS', payload: playersData });
  }, [playersData]);

  useEffect(() => {
    if (matchesData) dispatch({ type: 'SET_MATCHES', payload: matchesData });
  }, [matchesData]);

  useEffect(() => {
    if (teamsData) dispatch({ type: 'SET_TEAMS', payload: teamsData });
  }, [teamsData]);

  useEffect(() => {
    if (notificationsData) dispatch({ type: 'SET_NOTIFICATIONS', payload: notificationsData });
  }, [notificationsData]);

  useEffect(() => {
    dispatch({ type: 'SET_LOADING', payload: { key: 'players', value: playersLoading } });
    dispatch({ type: 'SET_ERROR', payload: { key: 'players', value: playersError } });
  }, [playersLoading, playersError]);

  useEffect(() => {
    dispatch({ type: 'SET_LOADING', payload: { key: 'matches', value: matchesLoading } });
    dispatch({ type: 'SET_ERROR', payload: { key: 'matches', value: matchesError } });
  }, [matchesLoading, matchesError]);

  useEffect(() => {
    dispatch({ type: 'SET_LOADING', payload: { key: 'teams', value: teamsLoading } });
    dispatch({ type: 'SET_ERROR', payload: { key: 'teams', value: teamsError } });
  }, [teamsLoading, teamsError]);

  useEffect(() => {
    dispatch({ type: 'SET_LOADING', payload: { key: 'notifications', value: notificationsLoading } });
    dispatch({ type: 'SET_ERROR', payload: { key: 'notifications', value: notificationsError } });
  }, [notificationsLoading, notificationsError]);


  // WebSocket event handlers
  useEffect(() => {
    const unsubscribePlayerUpdate = subscribe('player_update', (player: Player) => {
      dispatch({ type: 'UPDATE_PLAYER', payload: player });
    });

    const unsubscribeMatchUpdate = subscribe('match_update', (match: Match) => {
      dispatch({ type: 'UPDATE_MATCH', payload: match });
    });

    const unsubscribeNotification = subscribe('notification', (notification: Notification) => {
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
    });

    return () => {
      unsubscribePlayerUpdate();
      unsubscribeMatchUpdate();
      unsubscribeNotification();
    };
  }, [subscribe]);

  const contextValue: DataContextType = {
    ...state,
    dispatch,
    refreshPlayers: refetchPlayers,
    refreshMatches: refetchMatches,
    refreshTeams: refetchTeams,
    refreshNotifications: refetchNotifications,
  };

  return (
    <DataContext.Provider value={contextValue}>
      {children}
    </DataContext.Provider>
  );
}

export function useData() {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
}

export function useDataContext() {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useDataContext must be used within a DataProvider');
  }
  return context;
}