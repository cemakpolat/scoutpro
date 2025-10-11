import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Workspace, Activity, Task } from '../types/collaboration';

interface CollaborationContextType {
  workspaces: Workspace[];
  tasks: Task[];
  activities: Activity[];
  addWorkspace: (workspace: Workspace) => void;
  updateWorkspace: (id: string, updates: Partial<Workspace>) => void;
  deleteWorkspace: (id: string) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  deleteTask: (id: string) => void;
  addActivity: (activity: Activity) => void;
}

const CollaborationContext = createContext<CollaborationContextType | undefined>(undefined);

const STORAGE_KEYS = {
  WORKSPACES: 'scoutpro_workspaces',
  TASKS: 'scoutpro_tasks',
  ACTIVITIES: 'scoutpro_activities'
};

// Initial mock data
const initialWorkspaces: Workspace[] = [
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
    ]
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
    ]
  }
];

const initialTasks: Task[] = [
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
    updatedAt: '2024-10-02'
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
    updatedAt: '2024-09-28'
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
    completedAt: '2024-09-30'
  }
];

const initialActivities: Activity[] = [
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
  }
];

export const CollaborationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.WORKSPACES);
    return stored ? JSON.parse(stored) : initialWorkspaces;
  });

  const [tasks, setTasks] = useState<Task[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.TASKS);
    return stored ? JSON.parse(stored) : initialTasks;
  });

  const [activities, setActivities] = useState<Activity[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.ACTIVITIES);
    return stored ? JSON.parse(stored) : initialActivities;
  });

  // Persist to localStorage on changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.WORKSPACES, JSON.stringify(workspaces));
  }, [workspaces]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.TASKS, JSON.stringify(tasks));
  }, [tasks]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.ACTIVITIES, JSON.stringify(activities));
  }, [activities]);

  const addWorkspace = (workspace: Workspace) => {
    setWorkspaces(prev => [workspace, ...prev]);
  };

  const updateWorkspace = (id: string, updates: Partial<Workspace>) => {
    setWorkspaces(prev => prev.map(ws =>
      ws.id === id ? { ...ws, ...updates, updatedAt: new Date().toISOString().split('T')[0] } : ws
    ));
  };

  const deleteWorkspace = (id: string) => {
    setWorkspaces(prev => prev.filter(ws => ws.id !== id));
  };

  const addTask = (task: Task) => {
    setTasks(prev => [task, ...prev]);
  };

  const updateTask = (id: string, updates: Partial<Task>) => {
    setTasks(prev => prev.map(task =>
      task.id === id ? { ...task, ...updates, updatedAt: new Date().toISOString().split('T')[0] } : task
    ));
  };

  const deleteTask = (id: string) => {
    setTasks(prev => prev.filter(task => task.id !== id));
  };

  const addActivity = (activity: Activity) => {
    setActivities(prev => [activity, ...prev]);
  };

  const value = {
    workspaces,
    tasks,
    activities,
    addWorkspace,
    updateWorkspace,
    deleteWorkspace,
    addTask,
    updateTask,
    deleteTask,
    addActivity
  };

  return (
    <CollaborationContext.Provider value={value}>
      {children}
    </CollaborationContext.Provider>
  );
};

export const useCollaboration = () => {
  const context = useContext(CollaborationContext);
  if (context === undefined) {
    throw new Error('useCollaboration must be used within a CollaborationProvider');
  }
  return context;
};
