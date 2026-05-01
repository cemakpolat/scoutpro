const express = require('express');

const router = express.Router();

const roleDefinitions = [
  {
    id: 'admin',
    label: 'Admin',
    access: 'Full Access',
    permissions: ['User Management', 'System Controls', 'Reports', 'Exports', 'Data Governance'],
  },
  {
    id: 'scout',
    label: 'Head Scout',
    access: 'Scouting + Reports',
    permissions: ['Player Database', 'Match Centre', 'Report Builder', 'Collaboration Hub'],
  },
  {
    id: 'analyst',
    label: 'Analyst',
    access: 'Analytics Only',
    permissions: ['Analytics Lab', 'ML Laboratory', 'Report Builder', 'Exports'],
  },
  {
    id: 'coach',
    label: 'Coach',
    access: 'Reports Only',
    permissions: ['Reports', 'Calendar', 'Match Centre'],
  },
  {
    id: 'executive',
    label: 'Executive',
    access: 'Executive Dashboard',
    permissions: ['Dashboard', 'Market Intelligence', 'Reports'],
  },
  {
    id: 'viewer',
    label: 'Executive',
    access: 'Executive Dashboard',
    permissions: ['Dashboard', 'Reports'],
  },
];

const permissionMatrix = [
  { feature: 'Player Database', admin: true, scout: true, analyst: true, coach: true, executive: false },
  { feature: 'Match Centre', admin: true, scout: true, analyst: true, coach: true, executive: false },
  { feature: 'Analytics Lab', admin: true, scout: true, analyst: true, coach: false, executive: true },
  { feature: 'Report Builder', admin: true, scout: true, analyst: true, coach: true, executive: true },
  { feature: 'Admin Console', admin: true, scout: false, analyst: false, coach: false, executive: false },
];

function isoHoursAgo(hours) {
  return new Date(Date.now() - (hours * 60 * 60 * 1000)).toISOString();
}

function isoDaysAgo(days) {
  return new Date(Date.now() - (days * 24 * 60 * 60 * 1000)).toISOString();
}

function buildSeedApiKeys() {
  return [
    { id: 'api-mobile-app', name: 'Mobile App', key: 'sk_live_...7x9z', createdAt: isoDaysAgo(105), lastUsed: isoHoursAgo(2), status: 'active' },
    { id: 'api-data-export', name: 'Data Export', key: 'sk_live_...3m8n', createdAt: isoDaysAgo(120), lastUsed: isoHoursAgo(28), status: 'active' },
    { id: 'api-third-party', name: 'Third Party Integration', key: 'sk_live_...9k2l', createdAt: isoDaysAgo(160), lastUsed: isoDaysAgo(18), status: 'inactive' },
  ];
}

function buildSeedAuditLogs() {
  return [
    { id: 'audit-1', user: 'Admin Demo', action: 'Reviewed user permissions', resource: 'Role Matrix', time: isoHoursAgo(1) },
    { id: 'audit-2', user: 'Lead Analyst', action: 'Generated backend report', resource: 'Market Intelligence', time: isoHoursAgo(4) },
    { id: 'audit-3', user: 'Scout Demo', action: 'Viewed player dossier', resource: 'Tarik Cetin', time: isoHoursAgo(9) },
    { id: 'audit-4', user: 'Executive Demo', action: 'Opened executive dashboard', resource: 'Global Overview', time: isoDaysAgo(1) },
  ];
}

function buildSeedSubscriptions() {
  return [
    { id: 'sub-1', club: 'ScoutPro Demo FC', plan: 'Enterprise', users: 25, expires: '2026-12-31', status: 'active' },
    { id: 'sub-2', club: 'Caykur Rizespor', plan: 'Professional', users: 12, expires: '2026-11-15', status: 'active' },
    { id: 'sub-3', club: 'Samsunspor', plan: 'Professional', users: 10, expires: '2026-06-20', status: 'expiring' },
    { id: 'sub-4', club: 'Development Sandbox', plan: 'Basic', users: 4, expires: '2026-04-15', status: 'expired' },
  ];
}

function stripMongoId(document) {
  if (!document || typeof document !== 'object') {
    return document;
  }

  const { _id, ...rest } = document;
  return {
    ...rest,
    id: String(rest.id || _id || ''),
  };
}

async function ensureSeededCollection(db, collectionName, factory) {
  if (!db) {
    return factory();
  }

  const collection = db.collection(collectionName);
  const existing = await collection.find({}).sort({ createdAt: -1 }).limit(50).toArray();
  if (existing.length > 0) {
    return existing.map(stripMongoId);
  }

  const seed = factory();
  await collection.insertMany(seed);
  return seed;
}

function getRoleDefinition(roleId) {
  return roleDefinitions.find((role) => role.id === roleId) || roleDefinitions.find((role) => role.id === 'viewer');
}

function normalizeUser(user) {
  const role = getRoleDefinition(user.role);
  const lastActive = user.updatedAt || user.lastActive || user.createdAt || new Date().toISOString();
  const lastActiveDate = new Date(lastActive);
  const isRecent = !Number.isNaN(lastActiveDate.getTime())
    ? (Date.now() - lastActiveDate.getTime()) < (7 * 24 * 60 * 60 * 1000)
    : true;

  return {
    id: String(user.id || user._id || ''),
    name: user.name || user.email?.split('@')[0] || 'Unknown User',
    email: user.email || '',
    role: role.label,
    access: role.access,
    team: user.team || '',
    lastActive,
    status: isRecent ? 'active' : 'inactive',
    permissions: Array.isArray(user.permissions) && user.permissions.length > 0
      ? user.permissions
      : role.permissions,
  };
}

function buildFallbackUsers() {
  return [
    normalizeUser({ id: 'user-admin', name: 'Admin Demo', email: 'admin@scoutpro.dev', role: 'admin', team: 'ScoutPro HQ', lastActive: isoHoursAgo(2) }),
    normalizeUser({ id: 'user-scout', name: 'Scout Demo', email: 'scout@scoutpro.dev', role: 'scout', team: 'ScoutPro HQ', lastActive: isoHoursAgo(6) }),
    normalizeUser({ id: 'user-analyst', name: 'Lead Analyst', email: 'analyst@scoutpro.dev', role: 'analyst', team: 'ScoutPro HQ', lastActive: isoDaysAgo(1) }),
    normalizeUser({ id: 'user-exec', name: 'Executive Demo', email: 'viewer@scoutpro.dev', role: 'viewer', team: 'ScoutPro HQ', lastActive: isoDaysAgo(12) }),
  ];
}

function buildSystemHealth(db, req, summary) {
  const wsStats = req.app.locals.wsManager?.getStats?.() || { connectedClients: 0 };

  return {
    status: db ? 'healthy' : 'degraded',
    mongodb: db ? 'connected' : 'disconnected',
    websocketClients: wsStats.connectedClients || 0,
    services: [
      {
        service: 'API Gateway',
        status: 'healthy',
        uptime: `${Math.max(1, Math.round(process.uptime() / 60))} min`,
        response: 'live',
      },
      {
        service: 'MongoDB',
        status: db ? 'healthy' : 'warning',
        uptime: db ? 'connected' : 'degraded',
        response: db ? `${summary.totalPlayers} player docs` : 'unavailable',
      },
      {
        service: 'Reports Pipeline',
        status: summary.totalReports > 0 ? 'healthy' : 'unknown',
        uptime: `${summary.totalReports} reports`,
        response: `${summary.activeApiKeys} active keys`,
      },
      {
        service: 'Realtime Channel',
        status: 'healthy',
        uptime: `${wsStats.connectedClients || 0} clients`,
        response: db ? 'ready' : 'fallback',
      },
    ],
    alerts: [
      {
        id: 'alert-storage',
        type: 'warning',
        title: 'Storage Monitoring',
        message: `Reporting pipeline has generated ${summary.totalReports} report artifacts. Review storage growth if the count continues to climb.`,
        time: isoHoursAgo(3),
      },
      {
        id: 'alert-db',
        type: db ? 'info' : 'warning',
        title: db ? 'Database Connected' : 'Database Fallback Mode',
        message: db
          ? `MongoDB is connected with ${summary.totalPlayers} player records and ${summary.totalTeams} team records available.`
          : 'Gateway is serving seed data because MongoDB is unavailable.',
        time: isoHoursAgo(8),
      },
      {
        id: 'alert-reports',
        type: 'success',
        title: 'Reports Pipeline Ready',
        message: `${summary.activeSubscriptions} active subscriptions can generate backend reports immediately.`,
        time: isoDaysAgo(1),
      },
    ],
  };
}

router.get('/snapshot', async (req, res) => {
  try {
    const db = req.app.locals.db;

    let users = buildFallbackUsers();
    let apiKeys = buildSeedApiKeys();
    let auditLogs = buildSeedAuditLogs();
    let subscriptions = buildSeedSubscriptions();
    let totalPlayers = 0;
    let totalTeams = 0;
    let totalReports = 0;

    if (db) {
      const userDocs = await db.collection('users').find({}).sort({ updatedAt: -1 }).limit(50).toArray();
      if (userDocs.length > 0) {
        users = userDocs.map(normalizeUser);
      }

      apiKeys = await ensureSeededCollection(db, 'admin_api_keys', buildSeedApiKeys);
      auditLogs = await ensureSeededCollection(db, 'admin_audit_logs', buildSeedAuditLogs);
      subscriptions = await ensureSeededCollection(db, 'admin_subscriptions', buildSeedSubscriptions);
      totalPlayers = await db.collection('players').estimatedDocumentCount();
      totalTeams = await db.collection('teams').estimatedDocumentCount();
      totalReports = await db.collection('reports').estimatedDocumentCount();
    }

    const summary = {
      totalUsers: users.length,
      activeUsers: users.filter((user) => user.status === 'active').length,
      totalPlayers,
      totalTeams,
      totalReports,
      activeApiKeys: apiKeys.filter((key) => key.status === 'active').length,
      activeSubscriptions: subscriptions.filter((subscription) => subscription.status === 'active').length,
    };

    res.json({
      summary,
      users,
      roles: roleDefinitions,
      permissionMatrix,
      apiKeys,
      auditLogs,
      subscriptions,
      systemHealth: buildSystemHealth(db, req, summary),
    });
  } catch (error) {
    console.error('Admin snapshot error:', error);
    res.status(500).json({
      error: 'Failed to load admin snapshot',
      message: error.message,
    });
  }
});

module.exports = router;