import React, { useState } from 'react';
import {
  Calendar as CalendarIcon, ChevronLeft, ChevronRight,
  Plus, Filter, Download, MapPin, Users, Clock,
  Video, FileText, AlertCircle, Check, X, Plane,
  Edit2, Trash2, MoreVertical, Search
} from 'lucide-react';
import { CalendarEvent, ScoutingTrip, MatchSchedule } from '../types/calendar';
import { useCalendar } from '../context/CalendarContext';
import ConfirmDialog from './shared/ConfirmDialog';

const CalendarScheduling: React.FC = () => {
  const { events, trips, matches, addEvent, updateEvent, deleteEvent, updateMatch } = useCalendar();

  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'month' | 'week' | 'day' | 'list'>('month');
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [showNewEvent, setShowNewEvent] = useState(false);
  const [activeTab, setActiveTab] = useState<'calendar' | 'trips' | 'matches'>('calendar');
  const [showTripDetails, setShowTripDetails] = useState<string | null>(null);
  const [showMatchDetails, setShowMatchDetails] = useState<string | null>(null);

  // Edit/Delete states
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [deletingEvent, setDeletingEvent] = useState<string | null>(null);
  const [eventMenuOpen, setEventMenuOpen] = useState<string | null>(null);

  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState<CalendarEvent['type'] | 'all'>('all');

  // New Event form state
  const [eventTitle, setEventTitle] = useState('');
  const [eventDescription, setEventDescription] = useState('');
  const [eventType, setEventType] = useState<'match' | 'scouting_trip' | 'meeting' | 'reminder' | 'deadline'>('meeting');
  const [eventStartDate, setEventStartDate] = useState('');
  const [eventStartTime, setEventStartTime] = useState('');
  const [eventEndDate, setEventEndDate] = useState('');
  const [eventEndTime, setEventEndTime] = useState('');
  const [eventLocation, setEventLocation] = useState('');

  // Filter events based on search query and type filter
  const filteredEventsComputed = events.filter(event => {
    const matchesSearch = searchQuery === '' ||
      event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (event.description && event.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (event.location && event.location.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = eventTypeFilter === 'all' || event.type === eventTypeFilter;
    return matchesSearch && matchesType;
  });

  // Filter trips based on search query
  const filteredTripsComputed = trips.filter(trip => {
    const matchesSearch = searchQuery === '' ||
      trip.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      trip.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      trip.location.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  // Filter matches based on search query
  const filteredMatchesComputed = matches.filter(match => {
    const matchesSearch = searchQuery === '' ||
      match.homeTeam.toLowerCase().includes(searchQuery.toLowerCase()) ||
      match.awayTeam.toLowerCase().includes(searchQuery.toLowerCase()) ||
      match.venue.toLowerCase().includes(searchQuery.toLowerCase()) ||
      match.competition.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    return { daysInMonth, startingDayOfWeek, year, month };
  };

  const getEventsForDate = (date: Date) => {
    return filteredEventsComputed.filter(event => {
      const eventDate = new Date(event.startDate);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(currentDate);

  const previousMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const getEventTypeColor = (type: CalendarEvent['type']) => {
    const colors = {
      match: 'bg-green-600',
      scouting_trip: 'bg-blue-600',
      meeting: 'bg-purple-600',
      reminder: 'bg-yellow-600',
      deadline: 'bg-red-600'
    };
    return colors[type];
  };

  const getTripStatusColor = (status: ScoutingTrip['status']) => {
    const colors = {
      planned: 'bg-blue-600',
      in_progress: 'bg-yellow-600',
      completed: 'bg-green-600',
      cancelled: 'bg-red-600'
    };
    return colors[status];
  };

  const handleCreateEvent = () => {
    // Create new event
    const startDateTime = `${eventStartDate}T${eventStartTime || '00:00'}:00Z`;
    const endDateTime = eventEndDate && eventEndTime
      ? `${eventEndDate}T${eventEndTime}:00Z`
      : `${eventStartDate}T${eventStartTime || '23:59'}:00Z`;

    const newEvent: CalendarEvent = {
      id: `e${Date.now()}`,
      title: eventTitle,
      description: eventDescription,
      type: eventType,
      startDate: startDateTime,
      endDate: endDateTime,
      allDay: !eventStartTime,
      location: eventLocation || undefined,
      createdBy: 'u1'
    };

    // Add to events list using context
    addEvent(newEvent);

    // Reset form
    setEventTitle('');
    setEventDescription('');
    setEventType('meeting');
    setEventStartDate('');
    setEventStartTime('');
    setEventEndDate('');
    setEventEndTime('');
    setEventLocation('');
    setShowNewEvent(false);
  };

  const handleMarkAttending = (matchId: string) => {
    // Update match attendance status using context
    updateMatch(matchId, { isAttending: true, assignedScouts: ['u1'] });
  };

  const handleEditEvent = (event: CalendarEvent) => {
    setEditingEvent(event);
    setEventTitle(event.title);
    setEventDescription(event.description || '');
    setEventType(event.type);
    // Parse date and time from ISO string
    const startDate = new Date(event.startDate);
    setEventStartDate(startDate.toISOString().split('T')[0]);
    setEventStartTime(startDate.toTimeString().slice(0, 5));
    if (event.endDate) {
      const endDate = new Date(event.endDate);
      setEventEndDate(endDate.toISOString().split('T')[0]);
      setEventEndTime(endDate.toTimeString().slice(0, 5));
    }
    setEventLocation(event.location || '');
  };

  const handleUpdateEvent = () => {
    if (editingEvent) {
      const startDateTime = `${eventStartDate}T${eventStartTime || '00:00'}:00Z`;
      const endDateTime = eventEndDate && eventEndTime
        ? `${eventEndDate}T${eventEndTime}:00Z`
        : `${eventStartDate}T${eventStartTime || '23:59'}:00Z`;

      updateEvent(editingEvent.id, {
        title: eventTitle,
        description: eventDescription,
        type: eventType,
        startDate: startDateTime,
        endDate: endDateTime,
        allDay: !eventStartTime,
        location: eventLocation || undefined
      });

      setEditingEvent(null);
      setEventTitle('');
      setEventDescription('');
      setEventType('meeting');
      setEventStartDate('');
      setEventStartTime('');
      setEventEndDate('');
      setEventEndTime('');
      setEventLocation('');
    }
  };

  const handleDeleteEvent = () => {
    if (deletingEvent) {
      deleteEvent(deletingEvent);
      setDeletingEvent(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <CalendarIcon className="h-8 w-8 mr-3 text-green-500" />
          Calendar & Scheduling
        </h1>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowNewEvent(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>New Event</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab('calendar')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'calendar'
              ? 'border-green-500 text-green-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <CalendarIcon className="h-4 w-4" />
          <span>Calendar</span>
        </button>
        <button
          onClick={() => setActiveTab('trips')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'trips'
              ? 'border-green-500 text-green-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Plane className="h-4 w-4" />
          <span>Scouting Trips</span>
        </button>
        <button
          onClick={() => setActiveTab('matches')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'matches'
              ? 'border-green-500 text-green-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Video className="h-4 w-4" />
          <span>Match Schedule</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-5 w-5" />
          <input
            type="text"
            placeholder={`Search ${activeTab === 'calendar' ? 'events' : activeTab === 'trips' ? 'trips' : 'matches'}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>
        {activeTab === 'calendar' && (
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5 text-slate-400" />
            <select
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value as CalendarEvent['type'] | 'all')}
              className="px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              <option value="match">Match</option>
              <option value="scouting_trip">Scouting Trip</option>
              <option value="meeting">Meeting</option>
              <option value="reminder">Reminder</option>
              <option value="deadline">Deadline</option>
            </select>
            {eventTypeFilter !== 'all' && (
              <button
                onClick={() => setEventTypeFilter('all')}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        )}
        {(searchQuery || eventTypeFilter !== 'all') && (
          <div className="text-sm text-slate-400 whitespace-nowrap">
            {activeTab === 'calendar' && `${filteredEventsComputed.length} of ${events.length}`}
            {activeTab === 'trips' && `${filteredTripsComputed.length} of ${trips.length}`}
            {activeTab === 'matches' && `${filteredMatchesComputed.length} of ${matches.length}`}
          </div>
        )}
      </div>

      {/* Calendar Tab */}
      {activeTab === 'calendar' && (
        <div className="bg-slate-800 rounded-xl p-6">
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">
              {monthNames[month]} {year}
            </h2>
            <div className="flex items-center space-x-4">
              <div className="flex bg-slate-700 rounded-lg p-1">
                {(['month', 'week', 'day', 'list'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setViewMode(mode)}
                    className={`px-3 py-1 rounded text-sm transition-colors ${
                      viewMode === mode ? 'bg-slate-600' : 'hover:bg-slate-600'
                    }`}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </button>
                ))}
              </div>
              <button
                onClick={previousMonth}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                onClick={() => setCurrentDate(new Date())}
                className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
              >
                Today
              </button>
              <button
                onClick={nextMonth}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Month View */}
          {viewMode === 'month' && (
            <div className="grid grid-cols-7 gap-2">
              {/* Day headers */}
              {dayNames.map((day) => (
                <div key={day} className="text-center text-sm font-semibold text-slate-400 py-2">
                  {day}
                </div>
              ))}

              {/* Empty cells for days before month starts */}
              {Array.from({ length: startingDayOfWeek }).map((_, index) => (
                <div key={`empty-${index}`} className="aspect-square" />
              ))}

              {/* Days of the month */}
              {Array.from({ length: daysInMonth }).map((_, index) => {
                const day = index + 1;
                const date = new Date(year, month, day);
                const events = getEventsForDate(date);
                const isToday = date.toDateString() === new Date().toDateString();
                const isSelected = selectedDate?.toDateString() === date.toDateString();

                return (
                  <div
                    key={day}
                    onClick={() => setSelectedDate(date)}
                    className={`aspect-square p-2 rounded-lg border-2 cursor-pointer transition-all ${
                      isToday ? 'border-green-500 bg-green-900/20' :
                      isSelected ? 'border-blue-500 bg-blue-900/20' :
                      'border-transparent hover:border-slate-600 bg-slate-700'
                    }`}
                  >
                    <div className="text-sm font-semibold mb-1">{day}</div>
                    <div className="space-y-1">
                      {events.slice(0, 2).map((event) => (
                        <div
                          key={event.id}
                          className={`text-xs px-1 py-0.5 rounded truncate ${getEventTypeColor(event.type)} text-white`}
                          title={event.title}
                        >
                          {event.title}
                        </div>
                      ))}
                      {events.length > 2 && (
                        <div className="text-xs text-slate-400">+{events.length - 2} more</div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Week View */}
          {viewMode === 'week' && (
            <div className="space-y-2">
              <div className="grid grid-cols-7 gap-2">
                {dayNames.map((day) => (
                  <div key={day} className="text-center text-sm font-semibold text-slate-400 py-2">
                    {day}
                  </div>
                ))}
                {Array.from({ length: 7 }).map((_, index) => {
                  const date = new Date(currentDate);
                  date.setDate(currentDate.getDate() - currentDate.getDay() + index);
                  const events = getEventsForDate(date);
                  const isToday = date.toDateString() === new Date().toDateString();

                  return (
                    <div
                      key={index}
                      className={`min-h-[300px] p-3 rounded-lg border-2 ${
                        isToday ? 'border-green-500 bg-green-900/20' : 'border-slate-700 bg-slate-700'
                      }`}
                    >
                      <div className="text-sm font-semibold mb-2">{date.getDate()}</div>
                      <div className="space-y-2">
                        {events.map((event) => (
                          <div
                            key={event.id}
                            className={`text-xs p-2 rounded ${getEventTypeColor(event.type)} text-white`}
                          >
                            <div className="font-semibold">{event.title}</div>
                            <div className="opacity-75">{new Date(event.startDate).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Day View */}
          {viewMode === 'day' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">
                {currentDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
              </h3>
              <div className="space-y-3">
                {getEventsForDate(currentDate).map((event) => (
                  <div key={event.id} className="bg-slate-700 rounded-lg p-4 flex items-start space-x-4">
                    <div className={`w-1 h-full rounded ${getEventTypeColor(event.type)}`} />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-semibold">{event.title}</h4>
                        <span className={`px-2 py-1 rounded text-xs ${getEventTypeColor(event.type)}`}>
                          {event.type.replace('_', ' ')}
                        </span>
                      </div>
                      {event.description && (
                        <p className="text-sm text-slate-400 mb-2">{event.description}</p>
                      )}
                      <div className="flex items-center space-x-4 text-sm text-slate-400">
                        {event.location && (
                          <div className="flex items-center space-x-1">
                            <MapPin className="h-4 w-4" />
                            <span>{event.location}</span>
                          </div>
                        )}
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{new Date(event.startDate).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {getEventsForDate(currentDate).length === 0 && (
                  <p className="text-center text-slate-400 py-8">No events on this date</p>
                )}
              </div>
            </div>
          )}

          {/* List View */}
          {viewMode === 'list' && (
            <div className="space-y-3">
              {filteredEventsComputed.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                  <CalendarIcon className="h-16 w-16 mx-auto mb-4 opacity-30" />
                  <p className="text-lg mb-2">No events found</p>
                  <p className="text-sm">Try adjusting your search or filters</p>
                </div>
              )}
              {filteredEventsComputed
                .sort((a, b) => new Date(a.startDate).getTime() - new Date(b.startDate).getTime())
                .map((event) => (
                  <div key={event.id} className="bg-slate-700 rounded-lg p-4 flex items-start space-x-4">
                    <div className="text-center min-w-[60px]">
                      <div className="text-2xl font-bold">{new Date(event.startDate).getDate()}</div>
                      <div className="text-xs text-slate-400">{new Date(event.startDate).toLocaleDateString('en-US', { month: 'short' })}</div>
                    </div>
                    <div className={`w-1 rounded ${getEventTypeColor(event.type)}`} />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-semibold">{event.title}</h4>
                        <span className={`px-2 py-1 rounded text-xs ${getEventTypeColor(event.type)}`}>
                          {event.type.replace('_', ' ')}
                        </span>
                      </div>
                      {event.description && (
                        <p className="text-sm text-slate-400 mb-2">{event.description}</p>
                      )}
                      <div className="flex items-center space-x-4 text-sm text-slate-400">
                        {event.location && (
                          <div className="flex items-center space-x-1">
                            <MapPin className="h-4 w-4" />
                            <span>{event.location}</span>
                          </div>
                        )}
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{new Date(event.startDate).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    </div>
                    <div className="relative">
                      <button
                        onClick={() => setEventMenuOpen(eventMenuOpen === event.id ? null : event.id)}
                        className="p-1 hover:bg-slate-600 rounded transition-colors"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </button>
                      {eventMenuOpen === event.id && (
                        <div className="absolute right-0 mt-1 w-40 bg-slate-600 border border-slate-500 rounded-lg shadow-xl z-10">
                          <button
                            onClick={() => {
                              handleEditEvent(event);
                              setEventMenuOpen(null);
                            }}
                            className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-500 transition-colors text-left"
                          >
                            <Edit2 className="h-4 w-4" />
                            <span>Edit</span>
                          </button>
                          <button
                            onClick={() => {
                              setDeletingEvent(event.id);
                              setEventMenuOpen(null);
                            }}
                            className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-500 transition-colors text-left text-red-400"
                          >
                            <Trash2 className="h-4 w-4" />
                            <span>Delete</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          )}

          {/* Selected Date Events */}
          {selectedDate && (
            <div className="mt-6 pt-6 border-t border-slate-700">
              <h3 className="text-lg font-semibold mb-4">
                Events on {selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </h3>
              <div className="space-y-3">
                {getEventsForDate(selectedDate).map((event) => (
                  <div key={event.id} className="bg-slate-700 rounded-lg p-4 flex items-start space-x-4">
                    <div className={`w-1 h-full rounded ${getEventTypeColor(event.type)}`} />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-semibold">{event.title}</h4>
                        <span className={`px-2 py-1 rounded text-xs ${getEventTypeColor(event.type)}`}>
                          {event.type.replace('_', ' ')}
                        </span>
                      </div>
                      {event.description && (
                        <p className="text-sm text-slate-400 mb-2">{event.description}</p>
                      )}
                      <div className="flex items-center space-x-4 text-sm text-slate-400">
                        {event.location && (
                          <div className="flex items-center space-x-1">
                            <MapPin className="h-4 w-4" />
                            <span>{event.location}</span>
                          </div>
                        )}
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{new Date(event.startDate).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        {event.attendees && event.attendees.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <Users className="h-4 w-4" />
                            <span>{event.attendees.length} attendees</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="relative">
                      <button
                        onClick={() => setEventMenuOpen(eventMenuOpen === event.id ? null : event.id)}
                        className="p-1 hover:bg-slate-600 rounded transition-colors"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </button>
                      {eventMenuOpen === event.id && (
                        <div className="absolute right-0 mt-1 w-40 bg-slate-600 border border-slate-500 rounded-lg shadow-xl z-10">
                          <button
                            onClick={() => {
                              handleEditEvent(event);
                              setEventMenuOpen(null);
                            }}
                            className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-500 transition-colors text-left"
                          >
                            <Edit2 className="h-4 w-4" />
                            <span>Edit</span>
                          </button>
                          <button
                            onClick={() => {
                              setDeletingEvent(event.id);
                              setEventMenuOpen(null);
                            }}
                            className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-500 transition-colors text-left text-red-400"
                          >
                            <Trash2 className="h-4 w-4" />
                            <span>Delete</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {getEventsForDate(selectedDate).length === 0 && (
                  <p className="text-center text-slate-400 py-4">No events on this date</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scouting Trips Tab */}
      {activeTab === 'trips' && (
        <div className="space-y-4">
          {filteredTripsComputed.length === 0 && (
            <div className="text-center py-12 text-slate-400">
              <Plane className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg mb-2">No scouting trips found</p>
              <p className="text-sm">Try adjusting your search</p>
            </div>
          )}
          {filteredTripsComputed.map((trip) => (
            <div key={trip.id} className="bg-slate-800 rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="text-xl font-semibold">{trip.title}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${getTripStatusColor(trip.status)}`}>
                      {trip.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-slate-400">{trip.description}</p>
                </div>
                <Plane className="h-8 w-8 text-blue-400" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="flex items-center space-x-2 text-sm">
                  <CalendarIcon className="h-4 w-4 text-slate-400" />
                  <span>{new Date(trip.startDate).toLocaleDateString()} - {new Date(trip.endDate).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <MapPin className="h-4 w-4 text-slate-400" />
                  <span>{trip.location}</span>
                </div>
                {trip.budget && (
                  <div className="flex items-center space-x-2 text-sm">
                    <span className="text-slate-400">Budget:</span>
                    <span className="font-semibold text-green-400">€{trip.budget.toLocaleString()}</span>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-6 text-sm mb-4">
                <div className="flex items-center space-x-2">
                  <Video className="h-4 w-4 text-slate-400" />
                  <span>{trip.matches.length} matches</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="h-4 w-4 text-slate-400" />
                  <span>{trip.players.length} players</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="h-4 w-4 text-slate-400" />
                  <span>{trip.assignedTo.length} scouts</span>
                </div>
              </div>

              {trip.notes && (
                <div className="bg-slate-700 rounded-lg p-3 mb-4">
                  <p className="text-sm text-slate-300">{trip.notes}</p>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowTripDetails(trip.id)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
                >
                  View Details
                </button>
                <button
                  onClick={() => console.log('Edit trip:', trip.id)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
                >
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Match Schedule Tab */}
      {activeTab === 'matches' && (
        <div className="space-y-4">
          {filteredMatchesComputed.length === 0 && (
            <div className="text-center py-12 text-slate-400">
              <Video className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg mb-2">No matches found</p>
              <p className="text-sm">Try adjusting your search</p>
            </div>
          )}
          {filteredMatchesComputed.map((match) => (
            <div key={match.id} className="bg-slate-800 rounded-xl p-6 flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <h3 className="text-xl font-semibold">
                    {match.homeTeam} vs {match.awayTeam}
                  </h3>
                  {match.isAttending && (
                    <span className="px-2 py-1 bg-green-600 rounded text-xs">Attending</span>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                  <div className="flex items-center space-x-2 text-sm text-slate-400">
                    <CalendarIcon className="h-4 w-4" />
                    <span>{new Date(match.date).toLocaleDateString()} at {match.time}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-slate-400">
                    <MapPin className="h-4 w-4" />
                    <span>{match.venue}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-slate-400">
                    <FileText className="h-4 w-4" />
                    <span>{match.competition}</span>
                  </div>
                  {match.assignedScouts.length > 0 && (
                    <div className="flex items-center space-x-2 text-sm text-slate-400">
                      <Users className="h-4 w-4" />
                      <span>{match.assignedScouts.length} scouts assigned</span>
                    </div>
                  )}
                </div>

                {match.notes && (
                  <div className="bg-slate-700 rounded-lg p-3">
                    <p className="text-sm">{match.notes}</p>
                  </div>
                )}
              </div>

              <div className="flex flex-col space-y-2 ml-4">
                {!match.isAttending && (
                  <button
                    onClick={() => handleMarkAttending(match.id)}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm transition-colors whitespace-nowrap"
                  >
                    Mark Attending
                  </button>
                )}
                <button
                  onClick={() => setShowMatchDetails(match.id)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Event Modal */}
      {showNewEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Create New Event</h2>
              <button
                onClick={() => setShowNewEvent(false)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Event Title</label>
                <input
                  type="text"
                  value={eventTitle}
                  onChange={(e) => setEventTitle(e.target.value)}
                  placeholder="e.g., Man City vs Arsenal"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Event Type</label>
                <select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value as any)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="meeting">Meeting</option>
                  <option value="match">Match</option>
                  <option value="scouting_trip">Scouting Trip</option>
                  <option value="reminder">Reminder</option>
                  <option value="deadline">Deadline</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={eventDescription}
                  onChange={(e) => setEventDescription(e.target.value)}
                  placeholder="Event details..."
                  rows={2}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-2">Start Date</label>
                  <input
                    type="date"
                    value={eventStartDate}
                    onChange={(e) => setEventStartDate(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Start Time</label>
                  <input
                    type="time"
                    value={eventStartTime}
                    onChange={(e) => setEventStartTime(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-2">End Date</label>
                  <input
                    type="date"
                    value={eventEndDate}
                    onChange={(e) => setEventEndDate(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">End Time</label>
                  <input
                    type="time"
                    value={eventEndTime}
                    onChange={(e) => setEventEndTime(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Location</label>
                <input
                  type="text"
                  value={eventLocation}
                  onChange={(e) => setEventLocation(e.target.value)}
                  placeholder="e.g., Etihad Stadium"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              {(!eventTitle.trim() || !eventStartDate) && (
                <p className="text-xs text-slate-400">
                  * {!eventTitle.trim() ? 'Event title' : ''}{!eventTitle.trim() && !eventStartDate ? ' and ' : ''}{!eventStartDate ? 'start date' : ''} required
                </p>
              )}

              <div className="flex items-center space-x-3 pt-4">
                <button
                  onClick={handleCreateEvent}
                  disabled={!eventTitle.trim() || !eventStartDate}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title={!eventTitle.trim() || !eventStartDate ? 'Please fill in required fields' : ''}
                >
                  Create Event
                </button>
                <button
                  onClick={() => {
                    setShowNewEvent(false);
                    setEventTitle('');
                    setEventDescription('');
                    setEventType('meeting');
                    setEventStartDate('');
                    setEventStartTime('');
                    setEventEndDate('');
                    setEventEndTime('');
                    setEventLocation('');
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Event Modal */}
      {editingEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Edit Event</h2>
              <button
                onClick={() => {
                  setEditingEvent(null);
                  setEventTitle('');
                  setEventDescription('');
                  setEventType('meeting');
                  setEventStartDate('');
                  setEventStartTime('');
                  setEventEndDate('');
                  setEventEndTime('');
                  setEventLocation('');
                }}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Event Title</label>
                <input
                  type="text"
                  value={eventTitle}
                  onChange={(e) => setEventTitle(e.target.value)}
                  placeholder="e.g., Man City vs Arsenal"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Event Type</label>
                <select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value as any)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="meeting">Meeting</option>
                  <option value="match">Match</option>
                  <option value="scouting_trip">Scouting Trip</option>
                  <option value="reminder">Reminder</option>
                  <option value="deadline">Deadline</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={eventDescription}
                  onChange={(e) => setEventDescription(e.target.value)}
                  placeholder="Event details..."
                  rows={2}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-2">Start Date</label>
                  <input
                    type="date"
                    value={eventStartDate}
                    onChange={(e) => setEventStartDate(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Start Time</label>
                  <input
                    type="time"
                    value={eventStartTime}
                    onChange={(e) => setEventStartTime(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-2">End Date</label>
                  <input
                    type="date"
                    value={eventEndDate}
                    onChange={(e) => setEventEndDate(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">End Time</label>
                  <input
                    type="time"
                    value={eventEndTime}
                    onChange={(e) => setEventEndTime(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Location</label>
                <input
                  type="text"
                  value={eventLocation}
                  onChange={(e) => setEventLocation(e.target.value)}
                  placeholder="e.g., Etihad Stadium"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div className="flex items-center space-x-3 pt-4">
                <button
                  onClick={handleUpdateEvent}
                  disabled={!eventTitle.trim() || !eventStartDate}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Event
                </button>
                <button
                  onClick={() => {
                    setEditingEvent(null);
                    setEventTitle('');
                    setEventDescription('');
                    setEventType('meeting');
                    setEventStartDate('');
                    setEventStartTime('');
                    setEventEndDate('');
                    setEventEndTime('');
                    setEventLocation('');
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Event Confirmation */}
      <ConfirmDialog
        isOpen={deletingEvent !== null}
        onClose={() => setDeletingEvent(null)}
        onConfirm={handleDeleteEvent}
        title="Delete Event"
        message="Are you sure you want to delete this event? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Trip Details Modal */}
      {showTripDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Scouting Trip Details</h2>
              <button
                onClick={() => setShowTripDetails(null)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="text-slate-400 text-center py-8">
              Detailed trip information for trip ID: {showTripDetails}
            </div>
          </div>
        </div>
      )}

      {/* Match Details Modal */}
      {showMatchDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Match Details</h2>
              <button
                onClick={() => setShowMatchDetails(null)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="text-slate-400 text-center py-8">
              Detailed match information for match ID: {showMatchDetails}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarScheduling;
