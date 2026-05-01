/**
 * Auth Routes - JWT-based authentication
 */
const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');

const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET || 'scoutpro-secret-key-2025';
const JWT_EXPIRES_IN = '7d';
const AUTH_OP_TIMEOUT_MS = Number(process.env.AUTH_OP_TIMEOUT_MS || 5000);
const AUTH_DEV_FASTPATH_ENABLED = process.env.NODE_ENV !== 'production' && process.env.AUTH_DEV_FASTPATH !== 'false';

function getDefaultRoleAndPermissions(email) {
  let role = 'scout';
  let permissions = ['view_players', 'view_matches', 'create_reports', 'export_data', 'video_analysis'];

  if (email.includes('admin')) {
    role = 'admin';
    permissions = [
      'view_players', 'view_matches', 'create_reports', 'export_data',
      'manage_users', 'manage_system', 'manage_data', 'delete_data',
      'view_analytics', 'manage_roles', 'ml_access', 'video_analysis'
    ];
  } else if (email.includes('analyst')) {
    role = 'analyst';
    permissions = ['view_players', 'view_matches', 'view_analytics', 'create_reports', 'ml_access'];
  } else if (email.includes('viewer')) {
    role = 'viewer';
    permissions = ['view_players', 'view_matches', 'view_reports'];
  }

  return { role, permissions };
}

function tryBuildDevUser(email, password) {
  if (!AUTH_DEV_FASTPATH_ENABLED) {
    return null;
  }

  const defaultCredentials = {
    'admin@scoutpro.com': 'admin123',
    'analyst@scoutpro.com': 'analyst123',
    'scout@scoutpro.com': 'scout123',
    'viewer@scoutpro.com': 'viewer123',
  };

  if (defaultCredentials[email] !== password) {
    return null;
  }

  const { role, permissions } = getDefaultRoleAndPermissions(email);

  return {
    _id: uuidv4(),
    id: uuidv4(),
    email,
    name: email.split('@')[0],
    role,
    team: 'ScoutPro FC',
    avatar: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
    permissions,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
}

function withTimeout(promise, timeoutMs, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms`)), timeoutMs);
    }),
  ]);
}

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body || {};
    const normalizedEmail = typeof email === 'string' ? email.trim().toLowerCase() : '';
    
    if (!normalizedEmail || !password) {
      return res.status(400).json({ message: 'Email and password required' });
    }

    const db = req.app.locals.db;
    let dbAvailable = Boolean(db);
    let user = tryBuildDevUser(normalizedEmail, password);

    if (user) {
      const token = jwt.sign(
        { userId: user.id || user._id, email: user.email, role: user.role },
        JWT_SECRET,
        { expiresIn: JWT_EXPIRES_IN }
      );

      return res.json({ token, user });
    }

    if (dbAvailable) {
      try {
        user = await withTimeout(
          db.collection('users').findOne({ email: normalizedEmail }, { maxTimeMS: AUTH_OP_TIMEOUT_MS }),
          AUTH_OP_TIMEOUT_MS,
          'Auth user lookup'
        );
      } catch (lookupError) {
        // Keep auth available in development even if Mongo is temporarily slow/unavailable.
        dbAvailable = false;
        console.error('Auth lookup degraded mode:', lookupError.message);
      }
    }

    if (!user) {
      // Auto-create user for development convenience
      const { role, permissions } = getDefaultRoleAndPermissions(normalizedEmail);

      const hashedPassword = await withTimeout(
        bcrypt.hash(password, 10),
        AUTH_OP_TIMEOUT_MS,
        'Password hash'
      );
      user = {
        _id: uuidv4(),
        id: uuidv4(),
        email: normalizedEmail,
        name: normalizedEmail.split('@')[0],
        password: hashedPassword,
        role,
        team: 'ScoutPro FC',
        avatar: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
        permissions,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      if (dbAvailable) {
        try {
          await withTimeout(
            db.collection('users').insertOne(user),
            AUTH_OP_TIMEOUT_MS,
            'Auth user insert'
          );
        } catch (insertError) {
          console.error('Auth insert failed, continuing with in-memory user:', insertError.message);
        }
      }
    } else {
      // Verify password
      if (typeof user.password !== 'string' || user.password.length === 0) {
        return res.status(401).json({ message: 'Invalid credentials' });
      }

      const isValid = await withTimeout(
        bcrypt.compare(password, user.password),
        AUTH_OP_TIMEOUT_MS,
        'Password compare'
      );
      if (!isValid) {
        return res.status(401).json({ message: 'Invalid credentials' });
      }
    }

    // Generate JWT token
    const token = jwt.sign(
      { userId: user.id || user._id, email: user.email, role: user.role },
      JWT_SECRET,
      { expiresIn: JWT_EXPIRES_IN }
    );

    // Return user without password
    const { password: _, ...userWithoutPassword } = user;
    userWithoutPassword.id = userWithoutPassword.id || userWithoutPassword._id;

    res.json({
      token,
      user: userWithoutPassword
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Login failed' });
  }
});

// POST /api/auth/register
router.post('/register', async (req, res) => {
  try {
    const { email, password, name, role, team } = req.body;

    if (!email || !password || !name) {
      return res.status(400).json({ message: 'Email, password, and name required' });
    }

    const db = req.app.locals.db;

    if (db) {
      const existing = await db.collection('users').findOne({ email });
      if (existing) {
        return res.status(409).json({ message: 'User already exists' });
      }
    }

    const userRole = role || 'viewer';
    let permissions = ['view_players', 'view_matches'];
    if (userRole === 'admin') {
      permissions = [
        'view_players', 'view_matches', 'create_reports', 'export_data',
        'manage_users', 'manage_system', 'manage_data', 'delete_data',
        'view_analytics', 'manage_roles', 'ml_access', 'video_analysis'
      ];
    } else if (userRole === 'scout') {
      permissions = ['view_players', 'view_matches', 'create_reports', 'export_data', 'video_analysis'];
    } else if (userRole === 'analyst') {
      permissions = ['view_players', 'view_matches', 'view_analytics', 'create_reports', 'ml_access'];
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const user = {
      id: uuidv4(),
      email,
      name,
      password: hashedPassword,
      role: userRole,
      team: team || '',
      avatar: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
      permissions,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    if (db) {
      await db.collection('users').insertOne(user);
    }

    const token = jwt.sign(
      { userId: user.id, email: user.email, role: user.role },
      JWT_SECRET,
      { expiresIn: JWT_EXPIRES_IN }
    );

    const { password: _, ...userWithoutPassword } = user;

    res.status(201).json({
      token,
      user: userWithoutPassword
    });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ message: 'Registration failed' });
  }
});

// GET /api/auth/me
router.get('/me', async (req, res) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ message: 'No token provided' });
    }

    const token = authHeader.split(' ')[1];
    const decoded = jwt.verify(token, JWT_SECRET);

    const db = req.app.locals.db;
    if (db) {
      const user = await db.collection('users').findOne({ email: decoded.email });
      if (user) {
        const { password: _, ...userWithoutPassword } = user;
        userWithoutPassword.id = userWithoutPassword.id || userWithoutPassword._id;
        return res.json(userWithoutPassword);
      }
    }

    res.json({ id: decoded.userId, email: decoded.email, role: decoded.role });
  } catch (error) {
    res.status(401).json({ message: 'Invalid token' });
  }
});

module.exports = router;
