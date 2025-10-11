// Calendar & Scheduling Types

export type EventType = 'match' | 'scouting_trip' | 'meeting' | 'reminder' | 'deadline';

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  type: EventType;
  startDate: string;
  endDate: string;
  allDay: boolean;
  location?: string;
  attendees?: EventAttendee[];
  createdBy: string;
  reminders?: EventReminder[];
  recurring?: RecurringPattern;
  entityType?: 'player' | 'match' | 'team';
  entityId?: string;
  metadata?: Record<string, any>;
}

export interface EventAttendee {
  userId: string;
  name: string;
  email: string;
  status: 'pending' | 'accepted' | 'declined' | 'tentative';
  isOrganizer: boolean;
}

export interface EventReminder {
  id: string;
  type: 'email' | 'push' | 'sms';
  minutesBefore: number;
}

export interface RecurringPattern {
  frequency: 'daily' | 'weekly' | 'monthly' | 'yearly';
  interval: number; // e.g., every 2 weeks
  endDate?: string;
  count?: number; // number of occurrences
  daysOfWeek?: number[]; // 0-6 (Sunday-Saturday)
}

export interface ScoutingTrip {
  id: string;
  title: string;
  description: string;
  startDate: string;
  endDate: string;
  location: string;
  matches: string[]; // Match IDs
  players: string[]; // Player IDs to scout
  assignedTo: string[];
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  budget?: number;
  notes?: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface MatchSchedule {
  id: string;
  homeTeam: string;
  awayTeam: string;
  competition: string;
  venue: string;
  date: string;
  time: string;
  isAttending: boolean;
  assignedScouts: string[];
  notes?: string;
}
