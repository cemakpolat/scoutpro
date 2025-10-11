// Collaboration & Sharing Types

export type CommentableType = 'player' | 'match' | 'video' | 'report';

export interface Comment {
  id: string;
  entityType: CommentableType;
  entityId: string;
  content: string;
  mentions: string[]; // User IDs
  author: {
    id: string;
    name: string;
    email: string;
    avatar?: string;
  };
  createdAt: string;
  updatedAt: string;
  replies?: Comment[];
  isEdited: boolean;
}

export interface Activity {
  id: string;
  type: 'comment' | 'share' | 'edit' | 'create' | 'view' | 'export' | 'assign';
  user: {
    id: string;
    name: string;
    email: string;
    avatar?: string;
  };
  entityType: CommentableType | 'workspace' | 'task';
  entityId: string;
  entityName: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Workspace {
  id: string;
  name: string;
  description: string;
  owner: {
    id: string;
    name: string;
    email: string;
  };
  members: WorkspaceMember[];
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
  items: WorkspaceItem[];
}

export interface WorkspaceMember {
  userId: string;
  name: string;
  email: string;
  role: 'owner' | 'editor' | 'viewer';
  joinedAt: string;
  avatar?: string;
}

export interface WorkspaceItem {
  id: string;
  type: 'player' | 'match' | 'video' | 'report';
  entityId: string;
  name: string;
  addedBy: string;
  addedAt: string;
  notes?: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  assignedTo: string[];
  assignedBy: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  dueDate?: string;
  entityType?: CommentableType;
  entityId?: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface ShareLink {
  id: string;
  entityType: CommentableType;
  entityId: string;
  createdBy: string;
  expiresAt?: string;
  isPublic: boolean;
  password?: string;
  views: number;
  maxViews?: number;
  createdAt: string;
}
