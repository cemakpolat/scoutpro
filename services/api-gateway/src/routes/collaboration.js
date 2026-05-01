const express = require('express');
const { v4: uuidv4 } = require('uuid');

const router = express.Router();

const DEFAULT_USER = {
  id: 'u1',
  name: 'John Scout',
  email: 'john@scoutpro.com',
};

const DEFAULT_WORKSPACES = [
  {
    id: 'ws1',
    name: 'Premier League Prospects',
    description: 'Tracking top young talent in the Premier League',
    owner: { id: 'u1', name: 'John Scout', email: 'john@scoutpro.com' },
    members: [
      { userId: 'u1', name: 'John Scout', email: 'john@scoutpro.com', role: 'owner', joinedAt: '2024-01-15' },
      { userId: 'u2', name: 'Sarah Analyst', email: 'sarah@scoutpro.com', role: 'editor', joinedAt: '2024-01-20' },
      { userId: 'u3', name: 'Mike Viewer', email: 'mike@scoutpro.com', role: 'viewer', joinedAt: '2024-02-01' },
    ],
    createdAt: '2024-01-15',
    updatedAt: '2024-10-01',
    isPublic: false,
    items: [
      { id: 'i1', type: 'player', entityId: 'p1', name: 'Erling Haaland', addedBy: 'u1', addedAt: '2024-01-16' },
      { id: 'i2', type: 'player', entityId: 'p2', name: 'Bukayo Saka', addedBy: 'u1', addedAt: '2024-01-17' },
      { id: 'i3', type: 'match', entityId: 'm1', name: 'Man City vs Arsenal', addedBy: 'u2', addedAt: '2024-01-20' },
    ],
  },
  {
    id: 'ws2',
    name: 'La Liga Midfielders',
    description: 'Scouting creative midfielders from La Liga',
    owner: { id: 'u2', name: 'Sarah Analyst', email: 'sarah@scoutpro.com' },
    members: [
      { userId: 'u2', name: 'Sarah Analyst', email: 'sarah@scoutpro.com', role: 'owner', joinedAt: '2024-02-10' },
      { userId: 'u1', name: 'John Scout', email: 'john@scoutpro.com', role: 'editor', joinedAt: '2024-02-11' },
    ],
    createdAt: '2024-02-10',
    updatedAt: '2024-09-28',
    isPublic: true,
    items: [
      { id: 'i4', type: 'player', entityId: 'p3', name: 'Pedri', addedBy: 'u2', addedAt: '2024-02-11' },
      { id: 'i5', type: 'player', entityId: 'p4', name: 'Jude Bellingham', addedBy: 'u1', addedAt: '2024-02-15' },
    ],
  },
];

const DEFAULT_TASKS = [
  {
    id: 't1',
    title: 'Scout Haaland in next match',
    description: 'Attend Man City vs Chelsea and focus on his positioning',
    assignedTo: ['u1', 'u2'],
    assignedBy: 'u1',
    status: 'in_progress',
    priority: 'high',
    dueDate: '2024-10-15',
    entityType: 'player',
    entityId: 'p1',
    createdAt: '2024-10-01',
    updatedAt: '2024-10-02',
  },
  {
    id: 't2',
    title: 'Complete video analysis for Pedri',
    description: 'Annotate all key moments from Barcelona vs Real Madrid',
    assignedTo: ['u2'],
    assignedBy: 'u1',
    status: 'pending',
    priority: 'medium',
    dueDate: '2024-10-10',
    entityType: 'player',
    entityId: 'p3',
    createdAt: '2024-09-28',
    updatedAt: '2024-09-28',
  },
  {
    id: 't3',
    title: 'Update scouting database',
    description: 'Add new players from academy showcase',
    assignedTo: ['u1'],
    assignedBy: 'u2',
    status: 'completed',
    priority: 'low',
    createdAt: '2024-09-25',
    updatedAt: '2024-09-30',
    completedAt: '2024-09-30',
  },
];

const DEFAULT_ACTIVITIES = [
  {
    id: 'a1',
    type: 'comment',
    user: { id: 'u1', name: 'John Scout', email: 'john@scoutpro.com' },
    entityType: 'player',
    entityId: 'p1',
    entityName: 'Erling Haaland',
    description: 'added a comment on',
    timestamp: '2024-10-02T10:30:00Z',
  },
  {
    id: 'a2',
    type: 'share',
    user: { id: 'u2', name: 'Sarah Analyst', email: 'sarah@scoutpro.com' },
    entityType: 'workspace',
    entityId: 'ws1',
    entityName: 'Premier League Prospects',
    description: 'shared workspace',
    timestamp: '2024-10-02T09:15:00Z',
  },
  {
    id: 'a3',
    type: 'create',
    user: { id: 'u1', name: 'John Scout', email: 'john@scoutpro.com' },
    entityType: 'workspace',
    entityId: 'ws2',
    entityName: 'La Liga Midfielders',
    description: 'created workspace',
    timestamp: '2024-10-01T16:20:00Z',
  },
  {
    id: 'a4',
    type: 'export',
    user: { id: 'u3', name: 'Mike Viewer', email: 'mike@scoutpro.com' },
    entityType: 'player',
    entityId: 'p1',
    entityName: 'Erling Haaland',
    description: 'exported report for',
    timestamp: '2024-10-01T14:45:00Z',
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
  const [workspaceCount, taskCount, activityCount] = await Promise.all([
    db.collection('collaboration_workspaces').countDocuments(),
    db.collection('collaboration_tasks').countDocuments(),
    db.collection('collaboration_activities').countDocuments(),
  ]);

  const operations = [];
  if (workspaceCount === 0) {
    operations.push(db.collection('collaboration_workspaces').insertMany(DEFAULT_WORKSPACES));
  }
  if (taskCount === 0) {
    operations.push(db.collection('collaboration_tasks').insertMany(DEFAULT_TASKS));
  }
  if (activityCount === 0) {
    operations.push(db.collection('collaboration_activities').insertMany(DEFAULT_ACTIVITIES));
  }

  if (operations.length > 0) {
    await Promise.all(operations);
  }
};

const loadSnapshot = async (db) => {
  await ensureSeedData(db);

  const [workspaces, tasks, activities] = await Promise.all([
    db.collection('collaboration_workspaces').find({}).sort({ updatedAt: -1, createdAt: -1 }).toArray(),
    db.collection('collaboration_tasks').find({}).sort({ updatedAt: -1, createdAt: -1 }).toArray(),
    db.collection('collaboration_activities').find({}).sort({ timestamp: -1 }).toArray(),
  ]);

  return {
    workspaces: workspaces.map(serializeDoc),
    tasks: tasks.map(serializeDoc),
    activities: activities.map(serializeDoc),
  };
};

const recordActivity = async (db, activity) => {
  await db.collection('collaboration_activities').insertOne({
    id: activity.id || uuidv4(),
    timestamp: activity.timestamp || new Date().toISOString(),
    user: activity.user || DEFAULT_USER,
    ...activity,
  });
};

router.get('/', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    res.json(await loadSnapshot(db));
  } catch (error) {
    console.error('Load collaboration snapshot error:', error);
    res.status(500).json({ error: 'Failed to load collaboration snapshot' });
  }
});

router.post('/workspaces', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    if (!req.body?.name) {
      return res.status(400).json({ error: 'name is required' });
    }

    const today = new Date().toISOString().split('T')[0];
    const workspace = {
      ...req.body,
      id: req.body.id || uuidv4(),
      owner: req.body.owner || DEFAULT_USER,
      members: Array.isArray(req.body.members) && req.body.members.length > 0
        ? req.body.members
        : [
            {
              userId: DEFAULT_USER.id,
              name: DEFAULT_USER.name,
              email: DEFAULT_USER.email,
              role: 'owner',
              joinedAt: today,
            },
          ],
      items: Array.isArray(req.body.items) ? req.body.items : [],
      createdAt: req.body.createdAt || today,
      updatedAt: today,
      isPublic: Boolean(req.body.isPublic),
    };

    await db.collection('collaboration_workspaces').insertOne(workspace);
    await recordActivity(db, {
      type: 'create',
      entityType: 'workspace',
      entityId: workspace.id,
      entityName: workspace.name,
      description: 'created workspace',
      user: workspace.owner,
    });

    res.status(201).json(workspace);
  } catch (error) {
    console.error('Create workspace error:', error);
    res.status(500).json({ error: 'Failed to create workspace' });
  }
});

router.put('/workspaces/:workspaceId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const existing = await db.collection('collaboration_workspaces').findOne({ id: req.params.workspaceId });
    if (!existing) {
      return res.status(404).json({ error: 'Workspace not found' });
    }

    const updatedWorkspace = {
      ...existing,
      ...req.body,
      id: existing.id,
      updatedAt: new Date().toISOString().split('T')[0],
    };

    await db.collection('collaboration_workspaces').updateOne(
      { id: req.params.workspaceId },
      { $set: updatedWorkspace }
    );

    await recordActivity(db, {
      type: 'edit',
      entityType: 'workspace',
      entityId: updatedWorkspace.id,
      entityName: updatedWorkspace.name,
      description: 'updated workspace',
      user: updatedWorkspace.owner || DEFAULT_USER,
    });

    res.json(serializeDoc(updatedWorkspace));
  } catch (error) {
    console.error('Update workspace error:', error);
    res.status(500).json({ error: 'Failed to update workspace' });
  }
});

router.delete('/workspaces/:workspaceId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const result = await db.collection('collaboration_workspaces').deleteOne({ id: req.params.workspaceId });
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Workspace not found' });
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Delete workspace error:', error);
    res.status(500).json({ error: 'Failed to delete workspace' });
  }
});

router.post('/tasks', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    if (!req.body?.title) {
      return res.status(400).json({ error: 'title is required' });
    }

    const today = new Date().toISOString().split('T')[0];
    const task = {
      ...req.body,
      id: req.body.id || uuidv4(),
      assignedTo: Array.isArray(req.body.assignedTo) ? req.body.assignedTo : [DEFAULT_USER.id],
      assignedBy: req.body.assignedBy || DEFAULT_USER.id,
      status: req.body.status || 'pending',
      priority: req.body.priority || 'medium',
      createdAt: req.body.createdAt || today,
      updatedAt: today,
    };

    await db.collection('collaboration_tasks').insertOne(task);
    await recordActivity(db, {
      type: 'create',
      entityType: 'task',
      entityId: task.id,
      entityName: task.title,
      description: 'created task',
    });

    res.status(201).json(task);
  } catch (error) {
    console.error('Create task error:', error);
    res.status(500).json({ error: 'Failed to create task' });
  }
});

router.put('/tasks/:taskId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const existing = await db.collection('collaboration_tasks').findOne({ id: req.params.taskId });
    if (!existing) {
      return res.status(404).json({ error: 'Task not found' });
    }

    const nextStatus = req.body.status || existing.status;
    const updatedTask = {
      ...existing,
      ...req.body,
      id: existing.id,
      updatedAt: new Date().toISOString().split('T')[0],
      completedAt: nextStatus === 'completed'
        ? (req.body.completedAt || existing.completedAt || new Date().toISOString().split('T')[0])
        : req.body.completedAt,
    };

    await db.collection('collaboration_tasks').updateOne(
      { id: req.params.taskId },
      { $set: updatedTask }
    );

    await recordActivity(db, {
      type: 'edit',
      entityType: 'task',
      entityId: updatedTask.id,
      entityName: updatedTask.title,
      description: nextStatus === 'completed' ? 'completed task' : 'updated task',
    });

    res.json(serializeDoc(updatedTask));
  } catch (error) {
    console.error('Update task error:', error);
    res.status(500).json({ error: 'Failed to update task' });
  }
});

router.delete('/tasks/:taskId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const result = await db.collection('collaboration_tasks').deleteOne({ id: req.params.taskId });
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Delete task error:', error);
    res.status(500).json({ error: 'Failed to delete task' });
  }
});

router.post('/activities', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    if (!req.body?.type || !req.body?.entityType || !req.body?.entityId || !req.body?.entityName) {
      return res.status(400).json({ error: 'type, entityType, entityId, and entityName are required' });
    }

    const activity = {
      ...req.body,
      id: req.body.id || uuidv4(),
      user: req.body.user || DEFAULT_USER,
      timestamp: req.body.timestamp || new Date().toISOString(),
    };

    await db.collection('collaboration_activities').insertOne(activity);
    res.status(201).json(activity);
  } catch (error) {
    console.error('Create activity error:', error);
    res.status(500).json({ error: 'Failed to create activity' });
  }
});

module.exports = router;