import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { CalendarEvent, ScoutingTrip, MatchSchedule } from '../types/calendar';
import apiService from '../services/api';

interface CalendarContextType {
  events: CalendarEvent[];
  trips: ScoutingTrip[];
  matches: MatchSchedule[];
  addEvent: (event: CalendarEvent) => void;
  updateEvent: (id: string, updates: Partial<CalendarEvent>) => void;
  deleteEvent: (id: string) => void;
  addTrip: (trip: ScoutingTrip) => void;
  updateTrip: (id: string, updates: Partial<ScoutingTrip>) => void;
  deleteTrip: (id: string) => void;
  updateMatch: (id: string, updates: Partial<MatchSchedule>) => void;
}

const CalendarContext = createContext<CalendarContextType | undefined>(undefined);

export const CalendarProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [trips, setTrips] = useState<ScoutingTrip[]>([]);
  const [matches, setMatches] = useState<MatchSchedule[]>([]);

  const loadCalendar = async () => {
    const response = await apiService.getCalendarSnapshot();
    if (response.success && response.data) {
      setEvents(response.data.events || []);
      setTrips(response.data.trips || []);
      setMatches(response.data.matches || []);
      return;
    }

    console.error('Failed to load calendar snapshot', response.error);
  };

  useEffect(() => {
    void loadCalendar();
  }, []);

  const addEvent = (event: CalendarEvent) => {
    void (async () => {
      const response = await apiService.createCalendarEvent(event);
      if (response.success && response.data) {
        setEvents(prev => [...prev, response.data]);
        return;
      }

      console.error('Failed to create calendar event', response.error);
    })();
  };

  const updateEvent = (id: string, updates: Partial<CalendarEvent>) => {
    void (async () => {
      const response = await apiService.updateCalendarEvent(id, updates);
      if (response.success && response.data) {
        setEvents(prev => prev.map(event => (event.id === id ? response.data! : event)));
        return;
      }

      console.error('Failed to update calendar event', response.error);
    })();
  };

  const deleteEvent = (id: string) => {
    void (async () => {
      const response = await apiService.deleteCalendarEvent(id);
      if (response.success) {
        setEvents(prev => prev.filter(event => event.id !== id));
        return;
      }

      console.error('Failed to delete calendar event', response.error);
    })();
  };

  const addTrip = (trip: ScoutingTrip) => {
    void (async () => {
      const response = await apiService.createScoutingTrip(trip);
      if (response.success && response.data) {
        setTrips(prev => [...prev, response.data]);
        return;
      }

      console.error('Failed to create scouting trip', response.error);
    })();
  };

  const updateTrip = (id: string, updates: Partial<ScoutingTrip>) => {
    void (async () => {
      const response = await apiService.updateScoutingTrip(id, updates);
      if (response.success && response.data) {
        setTrips(prev => prev.map(trip => (trip.id === id ? response.data! : trip)));
        return;
      }

      console.error('Failed to update scouting trip', response.error);
    })();
  };

  const deleteTrip = (id: string) => {
    void (async () => {
      const response = await apiService.deleteScoutingTrip(id);
      if (response.success) {
        setTrips(prev => prev.filter(trip => trip.id !== id));
        return;
      }

      console.error('Failed to delete scouting trip', response.error);
    })();
  };

  const updateMatch = (id: string, updates: Partial<MatchSchedule>) => {
    void (async () => {
      const response = await apiService.updateMatchSchedule(id, updates);
      if (response.success && response.data) {
        setMatches(prev => prev.map(match => (match.id === id ? response.data! : match)));
        return;
      }

      console.error('Failed to update match schedule', response.error);
    })();
  };

  const value = {
    events,
    trips,
    matches,
    addEvent,
    updateEvent,
    deleteEvent,
    addTrip,
    updateTrip,
    deleteTrip,
    updateMatch
  };

  return (
    <CalendarContext.Provider value={value}>
      {children}
    </CalendarContext.Provider>
  );
};

export const useCalendar = () => {
  const context = useContext(CalendarContext);
  if (context === undefined) {
    throw new Error('useCalendar must be used within a CalendarProvider');
  }
  return context;
};
