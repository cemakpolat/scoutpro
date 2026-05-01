const express = require('express');
const { v4: uuidv4 } = require('uuid');

const router = express.Router();

const DEFAULT_EVENTS = [
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
    ],
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
    createdBy: 'u2',
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
    createdBy: 'u1',
  },
];

const DEFAULT_TRIPS = [
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
    updatedAt: '2024-09-28',
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
    updatedAt: '2024-10-02',
  },
];

const DEFAULT_MATCHES = [
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
    notes: 'Focus on Haaland positioning and Saka dribbling',
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
    notes: 'El Clasico - Priority match',
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
  },
];

const serializeDoc = (doc) => ({
  ...doc,
  id: doc.id || doc._id?.toString(),
  _id: undefined,
});

const requireDb = (req, res) => {
  const db = req.app.locals.db;
  if (!db) {
    res.status(503).json({ error: 'Database unavailable' });
    return null;
  }
  return db;
};

const ensureSeedData = async (db) => {
  const [eventCount, tripCount, matchCount] = await Promise.all([
    db.collection('calendar_events').countDocuments(),
    db.collection('calendar_trips').countDocuments(),
    db.collection('calendar_matches').countDocuments(),
  ]);

  const operations = [];
  if (eventCount === 0) {
    operations.push(db.collection('calendar_events').insertMany(DEFAULT_EVENTS));
  }
  if (tripCount === 0) {
    operations.push(db.collection('calendar_trips').insertMany(DEFAULT_TRIPS));
  }
  if (matchCount === 0) {
    operations.push(db.collection('calendar_matches').insertMany(DEFAULT_MATCHES));
  }

  if (operations.length > 0) {
    await Promise.all(operations);
  }
};

const loadSnapshot = async (db) => {
  await ensureSeedData(db);

  const [events, trips, matches] = await Promise.all([
    db.collection('calendar_events').find({}).sort({ startDate: 1 }).toArray(),
    db.collection('calendar_trips').find({}).sort({ startDate: 1 }).toArray(),
    db.collection('calendar_matches').find({}).sort({ date: 1, time: 1 }).toArray(),
  ]);

  return {
    events: events.map(serializeDoc),
    trips: trips.map(serializeDoc),
    matches: matches.map(serializeDoc),
  };
};

router.get('/', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    res.json(await loadSnapshot(db));
  } catch (error) {
    console.error('Load calendar snapshot error:', error);
    res.status(500).json({ error: 'Failed to load calendar snapshot' });
  }
});

router.post('/events', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    if (!req.body?.title || !req.body?.startDate) {
      return res.status(400).json({ error: 'title and startDate are required' });
    }

    const event = {
      ...req.body,
      id: req.body.id || uuidv4(),
      createdBy: req.body.createdBy || 'u1',
      allDay: Boolean(req.body.allDay),
    };

    await db.collection('calendar_events').insertOne(event);
    res.status(201).json(event);
  } catch (error) {
    console.error('Create calendar event error:', error);
    res.status(500).json({ error: 'Failed to create calendar event' });
  }
});

router.put('/events/:eventId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const existing = await db.collection('calendar_events').findOne({ id: req.params.eventId });
    if (!existing) {
      return res.status(404).json({ error: 'Calendar event not found' });
    }

    const updatedEvent = {
      ...existing,
      ...req.body,
      id: existing.id,
    };

    await db.collection('calendar_events').updateOne(
      { id: req.params.eventId },
      { $set: updatedEvent }
    );

    res.json(serializeDoc(updatedEvent));
  } catch (error) {
    console.error('Update calendar event error:', error);
    res.status(500).json({ error: 'Failed to update calendar event' });
  }
});

router.delete('/events/:eventId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const result = await db.collection('calendar_events').deleteOne({ id: req.params.eventId });
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Calendar event not found' });
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Delete calendar event error:', error);
    res.status(500).json({ error: 'Failed to delete calendar event' });
  }
});

router.post('/trips', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    if (!req.body?.title || !req.body?.startDate || !req.body?.endDate) {
      return res.status(400).json({ error: 'title, startDate, and endDate are required' });
    }

    const trip = {
      ...req.body,
      id: req.body.id || uuidv4(),
      createdBy: req.body.createdBy || 'u1',
      createdAt: req.body.createdAt || new Date().toISOString().split('T')[0],
      updatedAt: req.body.updatedAt || new Date().toISOString().split('T')[0],
      matches: Array.isArray(req.body.matches) ? req.body.matches : [],
      players: Array.isArray(req.body.players) ? req.body.players : [],
      assignedTo: Array.isArray(req.body.assignedTo) ? req.body.assignedTo : [],
    };

    await db.collection('calendar_trips').insertOne(trip);
    res.status(201).json(trip);
  } catch (error) {
    console.error('Create scouting trip error:', error);
    res.status(500).json({ error: 'Failed to create scouting trip' });
  }
});

router.put('/trips/:tripId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const existing = await db.collection('calendar_trips').findOne({ id: req.params.tripId });
    if (!existing) {
      return res.status(404).json({ error: 'Scouting trip not found' });
    }

    const updatedTrip = {
      ...existing,
      ...req.body,
      id: existing.id,
      updatedAt: new Date().toISOString().split('T')[0],
    };

    await db.collection('calendar_trips').updateOne(
      { id: req.params.tripId },
      { $set: updatedTrip }
    );

    res.json(serializeDoc(updatedTrip));
  } catch (error) {
    console.error('Update scouting trip error:', error);
    res.status(500).json({ error: 'Failed to update scouting trip' });
  }
});

router.delete('/trips/:tripId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const result = await db.collection('calendar_trips').deleteOne({ id: req.params.tripId });
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Scouting trip not found' });
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Delete scouting trip error:', error);
    res.status(500).json({ error: 'Failed to delete scouting trip' });
  }
});

router.put('/matches/:matchId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const existing = await db.collection('calendar_matches').findOne({ id: req.params.matchId });
    if (!existing) {
      return res.status(404).json({ error: 'Match schedule not found' });
    }

    const updatedMatch = {
      ...existing,
      ...req.body,
      id: existing.id,
      assignedScouts: Array.isArray(req.body.assignedScouts)
        ? req.body.assignedScouts
        : existing.assignedScouts,
    };

    await db.collection('calendar_matches').updateOne(
      { id: req.params.matchId },
      { $set: updatedMatch }
    );

    res.json(serializeDoc(updatedMatch));
  } catch (error) {
    console.error('Update match schedule error:', error);
    res.status(500).json({ error: 'Failed to update match schedule' });
  }
});

module.exports = router;