import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { CalendarEvent, ScoutingTrip, MatchSchedule } from '../types/calendar';

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

const STORAGE_KEYS = {
  EVENTS: 'scoutpro_events',
  TRIPS: 'scoutpro_trips',
  MATCHES: 'scoutpro_matches'
};

// Initial mock data
const initialEvents: CalendarEvent[] = [
  {
    id: 'e1',
    title: 'Man City vs Arsenal',
    description: 'Scout Haaland and Saka',
    type: 'match',
    startDate: '2024-10-15T15:00:00Z',
    endDate: '2024-10-15T17:00:00Z',
    allDay: false,
    location: 'Etihad Stadium',
    createdBy: 'u1',
    attendees: [
      { userId: 'u1', name: 'John Scout', email: 'john@scoutpro.com', status: 'accepted', isOrganizer: true },
      { userId: 'u2', name: 'Sarah Analyst', email: 'sarah@scoutpro.com', status: 'accepted', isOrganizer: false },
    ]
  },
  {
    id: 'e2',
    title: 'Team Meeting',
    description: 'Weekly scouting report review',
    type: 'meeting',
    startDate: '2024-10-18T10:00:00Z',
    endDate: '2024-10-18T11:00:00Z',
    allDay: false,
    location: 'Virtual - Zoom',
    createdBy: 'u2'
  },
  {
    id: 'e3',
    title: 'Barcelona vs Real Madrid',
    description: 'El Clasico - Scout Pedri and Bellingham',
    type: 'match',
    startDate: '2024-10-26T20:00:00Z',
    endDate: '2024-10-26T22:00:00Z',
    allDay: false,
    location: 'Camp Nou, Barcelona',
    createdBy: 'u1'
  }
];

const initialTrips: ScoutingTrip[] = [
  {
    id: 'st1',
    title: 'La Liga Scouting Tour',
    description: 'Visit 5 matches across Spain',
    startDate: '2024-10-20',
    endDate: '2024-10-27',
    location: 'Spain',
    matches: ['m1', 'm2', 'm3'],
    players: ['p3', 'p4', 'p5'],
    assignedTo: ['u1', 'u2'],
    status: 'planned',
    budget: 5000,
    notes: 'Focus on midfielders aged 18-23',
    createdBy: 'u1',
    createdAt: '2024-09-15',
    updatedAt: '2024-09-28'
  },
  {
    id: 'st2',
    title: 'Premier League Weekend',
    description: 'North West England matches',
    startDate: '2024-11-02',
    endDate: '2024-11-03',
    location: 'Manchester & Liverpool',
    matches: ['m4', 'm5'],
    players: ['p1', 'p2'],
    assignedTo: ['u1'],
    status: 'in_progress',
    budget: 1500,
    createdBy: 'u1',
    createdAt: '2024-10-01',
    updatedAt: '2024-10-02'
  }
];

const initialMatches: MatchSchedule[] = [
  {
    id: 'ms1',
    homeTeam: 'Manchester City',
    awayTeam: 'Arsenal',
    competition: 'Premier League',
    venue: 'Etihad Stadium',
    date: '2024-10-15',
    time: '15:00',
    isAttending: true,
    assignedScouts: ['u1', 'u2'],
    notes: 'Focus on Haaland positioning and Saka dribbling'
  },
  {
    id: 'ms2',
    homeTeam: 'Barcelona',
    awayTeam: 'Real Madrid',
    competition: 'La Liga',
    venue: 'Camp Nou',
    date: '2024-10-26',
    time: '20:00',
    isAttending: true,
    assignedScouts: ['u1'],
    notes: 'El Clasico - Priority match'
  },
  {
    id: 'ms3',
    homeTeam: 'Liverpool',
    awayTeam: 'Chelsea',
    competition: 'Premier League',
    venue: 'Anfield',
    date: '2024-11-03',
    time: '16:30',
    isAttending: false,
    assignedScouts: [],
  }
];

export const CalendarProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [events, setEvents] = useState<CalendarEvent[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.EVENTS);
    return stored ? JSON.parse(stored) : initialEvents;
  });

  const [trips, setTrips] = useState<ScoutingTrip[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.TRIPS);
    return stored ? JSON.parse(stored) : initialTrips;
  });

  const [matches, setMatches] = useState<MatchSchedule[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.MATCHES);
    return stored ? JSON.parse(stored) : initialMatches;
  });

  // Persist to localStorage on changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.EVENTS, JSON.stringify(events));
  }, [events]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.TRIPS, JSON.stringify(trips));
  }, [trips]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.MATCHES, JSON.stringify(matches));
  }, [matches]);

  const addEvent = (event: CalendarEvent) => {
    setEvents(prev => [...prev, event]);
  };

  const updateEvent = (id: string, updates: Partial<CalendarEvent>) => {
    setEvents(prev => prev.map(event =>
      event.id === id ? { ...event, ...updates } : event
    ));
  };

  const deleteEvent = (id: string) => {
    setEvents(prev => prev.filter(event => event.id !== id));
  };

  const addTrip = (trip: ScoutingTrip) => {
    setTrips(prev => [...prev, trip]);
  };

  const updateTrip = (id: string, updates: Partial<ScoutingTrip>) => {
    setTrips(prev => prev.map(trip =>
      trip.id === id ? { ...trip, ...updates, updatedAt: new Date().toISOString().split('T')[0] } : trip
    ));
  };

  const deleteTrip = (id: string) => {
    setTrips(prev => prev.filter(trip => trip.id !== id));
  };

  const updateMatch = (id: string, updates: Partial<MatchSchedule>) => {
    setMatches(prev => prev.map(match =>
      match.id === id ? { ...match, ...updates } : match
    ));
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
