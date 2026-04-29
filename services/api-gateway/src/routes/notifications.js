/**
 * Notifications Routes
 */
const express = require('express');
const router = express.Router();

// GET /api/notifications
router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const notifications = await db.collection('notifications')
      .find({})
      .sort({ createdAt: -1 })
      .limit(50)
      .toArray();

    const normalized = notifications.map(n => ({
      ...n,
      id: n.id || n._id?.toString(),
      _id: undefined
    }));

    res.json(normalized);
  } catch (error) {
    console.error('Notifications error:', error);
    res.status(500).json({ error: 'Failed to fetch notifications' });
  }
});

// PUT /api/notifications/:id/read
router.put('/:id/read', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json({ success: true });

    await db.collection('notifications').updateOne(
      { id: req.params.id },
      { $set: { read: true, updatedAt: new Date().toISOString() } }
    );

    res.json({ success: true });
  } catch (error) {
    console.error('Mark read error:', error);
    res.status(500).json({ error: 'Failed to mark notification read' });
  }
});

// POST /api/notifications - Create notification
router.post('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const { v4: uuidv4 } = require('uuid');
    const notification = {
      id: uuidv4(),
      ...req.body,
      read: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    await db.collection('notifications').insertOne(notification);
    res.status(201).json(notification);
  } catch (error) {
    console.error('Notification create error:', error);
    res.status(500).json({ error: 'Failed to create notification' });
  }
});

module.exports = router;
