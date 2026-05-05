/**
 * ScoutPro API Gateway
 * Unified entry point for the frontend to communicate with all backend microservices.
 * Handles auth, data normalization, and proxying to microservices.
 */
require('dotenv').config();
const http = require('http');
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const { MongoClient, ObjectId } = require('mongodb');
const WebSocketManager = require('./websocket');

const authRouter = require('./routes/auth');
const playersRouter = require('./routes/players');
const matchesRouter = require('./routes/matches');
const teamsRouter = require('./routes/teams');
const analyticsRouter = require('./routes/analytics');
const notificationsRouter = require('./routes/notifications');
const mlRouter = require('./routes/ml');
const searchRouter = require('./routes/search');
const statisticsRouter = require('./routes/statistics');
const reportsRouter = require('./routes/reports');
const exportsRouter = require('./routes/exports');
const importsRouter = require('./routes/imports');
const leaguesRouter = require('./routes/leagues');
const marketRouter = require('./routes/market');
const tacticalRouter = require('./routes/tactical');
const aiRouter = require('./routes/ai');
const videosRouter = require('./routes/videos');
const advancedAnalyticsRouter = require('./routes/advancedAnalytics');
const eventsRouter = require('./routes/events');
const calendarRouter = require('./routes/calendar');
const collaborationRouter = require('./routes/collaboration');
const adminRouter = require('./routes/admin');
const detailedStatsRouter = require('./routes/detailed-stats');
const tasksRouter = require('./routes/tasks');
const { buildGatewayOpenApiSpec, renderSwaggerUiHtml } = require('./openapi');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3001;
const MONGO_SERVER_SELECTION_TIMEOUT_MS = Number(process.env.MONGO_SERVER_SELECTION_TIMEOUT_MS || 5000);
const MONGO_CONNECT_TIMEOUT_MS = Number(process.env.MONGO_CONNECT_TIMEOUT_MS || 5000);
const MONGO_SOCKET_TIMEOUT_MS = Number(process.env.MONGO_SOCKET_TIMEOUT_MS || 10000);

// Middleware
app.use(cors({
  origin: ['http://localhost', 'http://localhost:80', 'http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));

// MongoDB connection
if (!process.env.MONGODB_URL) {
  if (process.env.NODE_ENV === 'production') {
    throw new Error('MONGODB_URL env var is required in production');
  }
  console.error('⚠️  MONGODB_URL not set — connecting to unauthenticated localhost MongoDB. Set MONGODB_URL for any real deployment.');
}
const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://localhost:27017/scoutpro';

let db;
let _mongoRetryTimer = null;
const MONGO_RETRY_INTERVAL_MS = Number(process.env.MONGO_RETRY_INTERVAL_MS || 10000);

async function connectDB() {
  if (_mongoRetryTimer) {
    clearTimeout(_mongoRetryTimer);
    _mongoRetryTimer = null;
  }
  try {
    const client = new MongoClient(MONGODB_URL, {
      serverSelectionTimeoutMS: MONGO_SERVER_SELECTION_TIMEOUT_MS,
      connectTimeoutMS: MONGO_CONNECT_TIMEOUT_MS,
      socketTimeoutMS: MONGO_SOCKET_TIMEOUT_MS,
      maxPoolSize: 20,
    });
    await client.connect();
    db = client.db('scoutpro');
    console.log('✅ Connected to MongoDB');

    // Handle unexpected disconnections — reconnect automatically
    client.on('close', () => {
      console.warn('⚠️  MongoDB connection closed — scheduling reconnect');
      db = null;
      app.locals.db = null;
      _mongoRetryTimer = setTimeout(connectDB, MONGO_RETRY_INTERVAL_MS);
    });

    // Make db available to routes
    app.locals.db = db;
    return db;
  } catch (error) {
    console.error('❌ MongoDB connection failed:', error.message);
    console.log(`⚠️  Will retry in ${MONGO_RETRY_INTERVAL_MS / 1000}s…`);
    _mongoRetryTimer = setTimeout(connectDB, MONGO_RETRY_INTERVAL_MS);
    return null;
  }
}

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'api-gateway',
    version: '2.1.0',
    mongodb: db ? 'connected' : 'disconnected',
    websocket: app.locals.wsManager ? `${app.locals.wsManager.getStats().connectedClients} clients` : 'not initialized'
  });
});

app.get('/openapi.json', (req, res) => {
  const forwardedProto = req.get('x-forwarded-proto');
  const protocol = forwardedProto ? forwardedProto.split(',')[0].trim() : req.protocol;
  const serverUrl = `${protocol}://${req.get('host')}`;
  res.json(buildGatewayOpenApiSpec(serverUrl));
});

app.get('/docs', (req, res) => {
  res.type('html').send(renderSwaggerUiHtml('/openapi.json'));
});

app.get('/', (req, res) => {
  res.json({ 
    service: 'ScoutPro API Gateway', 
    version: '2.1.0',
    docs: '/docs',
    openapi: '/openapi.json',
    endpoints: {
      auth: '/api/auth',
      players: '/api/players',
      matches: '/api/matches',
      teams: '/api/teams',
      leagues: '/api/leagues',
      analytics: '/api/analytics',
      statistics: '/api/statistics',
      notifications: '/api/notifications',
      ml: '/api/ml',
      search: '/api/search',
      reports: '/api/v2/reports',
      exports: '/api/v2/exports',
      imports: '/api/v2/imports',
      calendar: '/api/v2/calendar',
      collaboration: '/api/v2/collaboration',
      admin: '/api/v2/admin',
      videos: '/api/v2/videos',
      events: '/api/v2/events',
      advancedAnalytics: '/api/v2/analytics',
      market: '/api/market',
      tactical: '/api/tactical',
      ai: '/api/ai',
      tasks: '/api/tasks',
      websocket: 'ws://localhost:3001/ws'
    }
  });
});

// API Routes
app.use('/api/auth', authRouter);
app.use('/api/players', playersRouter);
app.use('/api/players', detailedStatsRouter);
app.use('/api/matches', matchesRouter);
app.use('/api/teams', teamsRouter);
app.use('/api/analytics', analyticsRouter);
app.use('/api/statistics', statisticsRouter);
app.use('/api/notifications', notificationsRouter);
app.use('/api/ml', mlRouter);
app.use('/api/search', searchRouter);
app.use('/api/v2/reports', reportsRouter);
app.use('/api/v2/exports', exportsRouter);
app.use('/api/v2/imports', importsRouter);
app.use('/api/v2/calendar', calendarRouter);
app.use('/api/v2/collaboration', collaborationRouter);
app.use('/api/v2/admin', adminRouter);
app.use('/api/leagues', leaguesRouter);
app.use('/api/market', marketRouter);
app.use('/api/tactical', tacticalRouter);
app.use('/api/ai', aiRouter);
app.use('/api/v2/videos', videosRouter);
app.use('/api/v2/events', eventsRouter);
app.use('/api/v2/analytics', advancedAnalyticsRouter);
app.use('/api/tasks', tasksRouter);

// WebSocket stats endpoint
app.get('/api/ws/stats', (req, res) => {
  if (app.locals.wsManager) {
    res.json(app.locals.wsManager.getStats());
  } else {
    res.json({ connectedClients: 0, clients: [] });
  }
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found', path: req.path });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Gateway error:', err);
  res.status(500).json({ 
    error: 'Internal server error', 
    message: err.message 
  });
});

// Start server
async function start() {
  const db = await connectDB();
  
  // Initialize WebSocket manager
  const wsManager = new WebSocketManager(server, db);
  app.locals.wsManager = wsManager;
  
  server.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🚀 ScoutPro API Gateway running on port ${PORT}`);
    console.log(`   Health:    http://localhost:${PORT}/health`);
    console.log(`   Docs:      http://localhost:${PORT}/docs`);
    console.log(`   OpenAPI:   http://localhost:${PORT}/openapi.json`);
    console.log(`   WebSocket: ws://localhost:${PORT}/ws`);
    console.log('');
  });
}

start().catch(console.error);

module.exports = app;
