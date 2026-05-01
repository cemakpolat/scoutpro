import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Workspace, Activity, Task } from '../types/collaboration';
import apiService from '../services/api';

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

export const CollaborationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);

  const loadCollaboration = async () => {
    const response = await apiService.getCollaborationSnapshot();
    if (response.success && response.data) {
      setWorkspaces(response.data.workspaces || []);
      setTasks(response.data.tasks || []);
      setActivities(response.data.activities || []);
      return;
    }

    console.error('Failed to load collaboration snapshot', response.error);
  };

  useEffect(() => {
    void loadCollaboration();
  }, []);

  const addWorkspace = (workspace: Workspace) => {
    void (async () => {
      const response = await apiService.createWorkspace(workspace);
      if (response.success) {
        await loadCollaboration();
        return;
      }

      console.error('Failed to create workspace', response.error);
    })();
  };

  const updateWorkspace = (id: string, updates: Partial<Workspace>) => {
    void (async () => {
      const response = await apiService.updateWorkspace(id, updates);
      if (response.success) {
        await loadCollaboration();
        return;
      }

      console.error('Failed to update workspace', response.error);
    })();
  };

  const deleteWorkspace = (id: string) => {
    void (async () => {
      const response = await apiService.deleteWorkspace(id);
      if (response.success) {
        await loadCollaboration();
        return;
      }

      console.error('Failed to delete workspace', response.error);
    })();
  };

  const addTask = (task: Task) => {
    void (async () => {
      const response = await apiService.createTask(task);
      if (response.success) {
        await loadCollaboration();
        return;
      }

      console.error('Failed to create task', response.error);
    })();
  };

  const updateTask = (id: string, updates: Partial<Task>) => {
    void (async () => {
      const response = await apiService.updateTask(id, updates);
      if (response.success) {
        await loadCollaboration();
        return;
      }

      console.error('Failed to update task', response.error);
    })();
  };

  const deleteTask = (id: string) => {
    void (async () => {
      const response = await apiService.deleteTask(id);
      if (response.success) {
        await loadCollaboration();
        return;
      }

      console.error('Failed to delete task', response.error);
    })();
  };

  const addActivity = (activity: Activity) => {
    void (async () => {
      const response = await apiService.createCollaborationActivity(activity);
      if (response.success && response.data) {
        setActivities(prev => [response.data!, ...prev]);
        return;
      }

      console.error('Failed to create activity', response.error);
    })();
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
