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
const reportsRouter = require('./routes/reports');
const exportsRouter = require('./routes/exports');
const leaguesRouter = require('./routes/leagues');
const marketRouter = require('./routes/market');
const tacticalRouter = require('./routes/tactical');
const aiRouter = require('./routes/ai');
const videosRouter = require('./routes/videos');
const advancedAnalyticsRouter = require('./routes/advancedAnalytics');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000', 'http://localhost:80', '*'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));

// MongoDB connection
const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin';

let db;
async function connectDB() {
  try {
    const client = new MongoClient(MONGODB_URL);
    await client.connect();
    db = client.db('scoutpro');
    console.log('✅ Connected to MongoDB');
    
    // Make db available to routes
    app.locals.db = db;
    return db;
  } catch (error) {
    console.error('❌ MongoDB connection failed:', error.message);
    console.log('⚠️  Gateway will serve mock/seed data fallbacks');
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

app.get('/', (req, res) => {
  res.json({ 
    service: 'ScoutPro API Gateway', 
    version: '2.1.0',
    endpoints: {
      auth: '/api/auth',
      players: '/api/players',
      matches: '/api/matches',
      teams: '/api/teams',
      leagues: '/api/leagues',
      analytics: '/api/analytics',
      notifications: '/api/notifications',
      ml: '/api/ml',
      search: '/api/search',
      reports: '/api/v2/reports',
      exports: '/api/v2/exports',
      videos: '/api/v2/videos',
      advancedAnalytics: '/api/v2/analytics',
      market: '/api/market',
      tactical: '/api/tactical',
      ai: '/api/ai',
      websocket: 'ws://localhost:3001/ws'
    }
  });
});

// API Routes
app.use('/api/auth', authRouter);
app.use('/api/players', playersRouter);
app.use('/api/matches', matchesRouter);
app.use('/api/teams', teamsRouter);
app.use('/api/analytics', analyticsRouter);
app.use('/api/notifications', notificationsRouter);
app.use('/api/ml', mlRouter);
app.use('/api/search', searchRouter);
app.use('/api/v2/reports', reportsRouter);
app.use('/api/v2/exports', exportsRouter);
app.use('/api/leagues', leaguesRouter);
app.use('/api/market', marketRouter);
app.use('/api/tactical', tacticalRouter);
app.use('/api/ai', aiRouter);
app.use('/api/v2/videos', videosRouter);
app.use('/api/v2/analytics', advancedAnalyticsRouter);

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
    console.log(`   Docs:      http://localhost:${PORT}/`);
    console.log(`   WebSocket: ws://localhost:${PORT}/ws`);
    console.log('');
  });
}

start().catch(console.error);

module.exports = app;
