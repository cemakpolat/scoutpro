import React, { useState } from 'react';
import {
  MessageSquare, Users, Activity as ActivityIcon, CheckSquare,
  Share2, Plus, Search, Filter, Clock, User, AtSign,
  Send, Edit2, Trash2, MoreVertical, Eye, Lock, Unlock,
  Folder, Star, Calendar, AlertCircle, X
} from 'lucide-react';
import { Comment, Workspace, Activity, Task } from '../types/collaboration';
import { useCollaboration } from '../context/CollaborationContext';
import ConfirmDialog from './shared/ConfirmDialog';

const CollaborationHub: React.FC = () => {
  const { workspaces, tasks, activities, addWorkspace, updateWorkspace, deleteWorkspace, addTask, updateTask, deleteTask } = useCollaboration();

  const [activeTab, setActiveTab] = useState<'comments' | 'workspaces' | 'activity' | 'tasks'>('workspaces');
  const [searchQuery, setSearchQuery] = useState('');
  const [showNewWorkspace, setShowNewWorkspace] = useState(false);
  const [showNewTask, setShowNewTask] = useState(false);

  // Edit/Delete states
  const [editingWorkspace, setEditingWorkspace] = useState<Workspace | null>(null);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deletingWorkspace, setDeletingWorkspace] = useState<string | null>(null);
  const [deletingTask, setDeletingTask] = useState<string | null>(null);
  const [viewingWorkspace, setViewingWorkspace] = useState<Workspace | null>(null);
  const [workspaceMenuOpen, setWorkspaceMenuOpen] = useState<string | null>(null);
  const [taskMenuOpen, setTaskMenuOpen] = useState<string | null>(null);

  // Filter states
  const [taskStatusFilter, setTaskStatusFilter] = useState<Task['status'] | 'all'>('all');
  const [taskPriorityFilter, setTaskPriorityFilter] = useState<Task['priority'] | 'all'>('all');

  // New Workspace form state
  const [workspaceName, setWorkspaceName] = useState('');
  const [workspaceDescription, setWorkspaceDescription] = useState('');
  const [workspaceIsPublic, setWorkspaceIsPublic] = useState(false);

  // New Task form state
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskPriority, setTaskPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('medium');
  const [taskDueDate, setTaskDueDate] = useState('');

  const formatRelativeTime = (timestamp: string): string => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getPriorityColor = (priority: Task['priority']) => {
    const colors = {
      low: 'bg-slate-600',
      medium: 'bg-yellow-600',
      high: 'bg-orange-600',
      urgent: 'bg-red-600'
    };
    return colors[priority];
  };

  const getStatusColor = (status: Task['status']) => {
    const colors = {
      pending: 'bg-slate-600',
      in_progress: 'bg-blue-600',
      completed: 'bg-green-600',
      cancelled: 'bg-red-600'
    };
    return colors[status];
  };

  const handleCreateWorkspace = () => {
    // Create new workspace
    const newWorkspace: Workspace = {
      id: `ws${Date.now()}`,
      name: workspaceName,
      description: workspaceDescription,
      owner: { id: 'u1', name: 'John Scout', email: 'john@scoutpro.com' },
      members: [
        { userId: 'u1', name: 'John Scout', email: 'john@scoutpro.com', role: 'owner', joinedAt: new Date().toISOString().split('T')[0] }
      ],
      createdAt: new Date().toISOString().split('T')[0],
      updatedAt: new Date().toISOString().split('T')[0],
      isPublic: workspaceIsPublic,
      items: []
    };

    // Add to workspaces list using context
    addWorkspace(newWorkspace);

    // Reset form
    setWorkspaceName('');
    setWorkspaceDescription('');
    setWorkspaceIsPublic(false);
    setShowNewWorkspace(false);
  };

  const handleCreateTask = () => {
    // Create new task
    const newTask: Task = {
      id: `t${Date.now()}`,
      title: taskTitle,
      description: taskDescription,
      assignedTo: ['u1'],
      assignedBy: 'u1',
      status: 'pending',
      priority: taskPriority,
      dueDate: taskDueDate || undefined,
      createdAt: new Date().toISOString().split('T')[0],
      updatedAt: new Date().toISOString().split('T')[0]
    };

    // Add to tasks list using context
    addTask(newTask);

    // Reset form
    setTaskTitle('');
    setTaskDescription('');
    setTaskPriority('medium');
    setTaskDueDate('');
    setShowNewTask(false);
  };

  const handleEditWorkspace = (workspace: Workspace) => {
    setEditingWorkspace(workspace);
    setWorkspaceName(workspace.name);
    setWorkspaceDescription(workspace.description);
    setWorkspaceIsPublic(workspace.isPublic);
  };

  const handleUpdateWorkspace = () => {
    if (editingWorkspace) {
      updateWorkspace(editingWorkspace.id, {
        name: workspaceName,
        description: workspaceDescription,
        isPublic: workspaceIsPublic
      });
      setEditingWorkspace(null);
      setWorkspaceName('');
      setWorkspaceDescription('');
      setWorkspaceIsPublic(false);
    }
  };

  const handleDeleteWorkspace = () => {
    if (deletingWorkspace) {
      deleteWorkspace(deletingWorkspace);
      setDeletingWorkspace(null);
    }
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setTaskTitle(task.title);
    setTaskDescription(task.description);
    setTaskPriority(task.priority);
    setTaskDueDate(task.dueDate || '');
  };

  const handleUpdateTask = () => {
    if (editingTask) {
      updateTask(editingTask.id, {
        title: taskTitle,
        description: taskDescription,
        priority: taskPriority,
        dueDate: taskDueDate || undefined
      });
      setEditingTask(null);
      setTaskTitle('');
      setTaskDescription('');
      setTaskPriority('medium');
      setTaskDueDate('');
    }
  };

  const handleDeleteTask = () => {
    if (deletingTask) {
      deleteTask(deletingTask);
      setDeletingTask(null);
    }
  };

  const handleToggleTaskStatus = (task: Task) => {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    updateTask(task.id, {
      status: newStatus,
      completedAt: newStatus === 'completed' ? new Date().toISOString().split('T')[0] : undefined
    });
  };

  // Filter workspaces based on search query
  const filteredWorkspaces = workspaces.filter(workspace => {
    const matchesSearch = searchQuery === '' ||
      workspace.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workspace.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  // Filter tasks based on search query and filters
  const filteredTasks = tasks.filter(task => {
    const matchesSearch = searchQuery === '' ||
      task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = taskStatusFilter === 'all' || task.status === taskStatusFilter;
    const matchesPriority = taskPriorityFilter === 'all' || task.priority === taskPriorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  // Filter activities based on search query
  const filteredActivities = activities.filter(activity => {
    const matchesSearch = searchQuery === '' ||
      activity.user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      activity.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      activity.entityName.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Users className="h-8 w-8 mr-3 text-blue-500" />
          Collaboration Hub
        </h1>
        <div className="flex items-center space-x-3">
          {activeTab === 'workspaces' && (
            <button
              onClick={() => setShowNewWorkspace(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span>New Workspace</span>
            </button>
          )}
          {activeTab === 'tasks' && (
            <button
              onClick={() => setShowNewTask(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span>New Task</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab('workspaces')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'workspaces'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Folder className="h-4 w-4" />
          <span>Workspaces</span>
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'activity'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <ActivityIcon className="h-4 w-4" />
          <span>Activity Feed</span>
        </button>
        <button
          onClick={() => setActiveTab('tasks')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'tasks'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <CheckSquare className="h-4 w-4" />
          <span>Tasks</span>
        </button>
        <button
          onClick={() => setActiveTab('comments')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'comments'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          <span>Comments</span>
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-5 w-5" />
        <input
          type="text"
          placeholder={`Search ${activeTab}...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Workspaces Tab */}
      {activeTab === 'workspaces' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredWorkspaces.length === 0 && (
            <div className="col-span-full text-center py-12 text-slate-400">
              <Folder className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg mb-2">No workspaces found</p>
              <p className="text-sm">Try adjusting your search or create a new workspace</p>
            </div>
          )}
          {filteredWorkspaces.map((workspace) => (
            <div key={workspace.id} className="bg-slate-800 rounded-xl p-6 hover:ring-2 hover:ring-blue-500 transition-all cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="text-lg font-semibold">{workspace.name}</h3>
                    {workspace.isPublic ? (
                      <Unlock className="h-4 w-4 text-green-400" title="Public" />
                    ) : (
                      <Lock className="h-4 w-4 text-slate-400" title="Private" />
                    )}
                  </div>
                  <p className="text-sm text-slate-400 line-clamp-2">{workspace.description}</p>
                </div>
                <div className="relative">
                  <button
                    onClick={() => setWorkspaceMenuOpen(workspaceMenuOpen === workspace.id ? null : workspace.id)}
                    className="p-1 hover:bg-slate-700 rounded transition-colors"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>
                  {workspaceMenuOpen === workspace.id && (
                    <div className="absolute right-0 mt-1 w-40 bg-slate-700 border border-slate-600 rounded-lg shadow-xl z-10">
                      <button
                        onClick={() => {
                          handleEditWorkspace(workspace);
                          setWorkspaceMenuOpen(null);
                        }}
                        className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-600 transition-colors text-left"
                      >
                        <Edit2 className="h-4 w-4" />
                        <span>Edit</span>
                      </button>
                      <button
                        onClick={() => {
                          setDeletingWorkspace(workspace.id);
                          setWorkspaceMenuOpen(null);
                        }}
                        className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-600 transition-colors text-left text-red-400"
                      >
                        <Trash2 className="h-4 w-4" />
                        <span>Delete</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-3 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Items</span>
                  <span className="font-semibold">{workspace.items.length}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Members</span>
                  <div className="flex -space-x-2">
                    {workspace.members.slice(0, 3).map((member, idx) => (
                      <div
                        key={member.userId}
                        className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 border-2 border-slate-800 flex items-center justify-center text-xs font-semibold"
                        title={member.name}
                      >
                        {member.name.charAt(0)}
                      </div>
                    ))}
                    {workspace.members.length > 3 && (
                      <div className="w-6 h-6 rounded-full bg-slate-700 border-2 border-slate-800 flex items-center justify-center text-xs">
                        +{workspace.members.length - 3}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-3 border-t border-slate-700">
                <button
                  onClick={() => setViewingWorkspace(workspace)}
                  className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
                >
                  <Eye className="h-4 w-4" />
                  <span>View</span>
                </button>
                <button
                  onClick={() => {
                    setViewingWorkspace(workspace);
                    // TODO: Show share modal after view modal
                  }}
                  className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
                >
                  <Share2 className="h-4 w-4" />
                  <span>Share</span>
                </button>
              </div>

              <div className="mt-3 text-xs text-slate-500">
                Updated {formatRelativeTime(workspace.updatedAt)}
              </div>
            </div>
          ))}

          {/* Create New Workspace Card */}
          <div
            onClick={() => setShowNewWorkspace(true)}
            className="bg-slate-800 rounded-xl p-6 border-2 border-dashed border-slate-700 hover:border-blue-500 transition-all cursor-pointer flex flex-col items-center justify-center min-h-[280px]"
          >
            <Plus className="h-12 w-12 text-slate-600 mb-3" />
            <p className="text-slate-400 font-medium">Create New Workspace</p>
            <p className="text-sm text-slate-500 mt-1">Collaborate with your team</p>
          </div>
        </div>
      )}

      {/* Activity Feed Tab */}
      {activeTab === 'activity' && (
        <div className="space-y-4">
          {filteredActivities.length === 0 && (
            <div className="text-center py-12 text-slate-400">
              <ActivityIcon className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg mb-2">No activity found</p>
              <p className="text-sm">Try adjusting your search</p>
            </div>
          )}
          {filteredActivities.map((activity) => (
            <div key={activity.id} className="bg-slate-800 rounded-xl p-4 flex items-start space-x-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center font-semibold">
                {activity.user.name.charAt(0)}
              </div>
              <div className="flex-1">
                <p className="text-sm">
                  <span className="font-semibold">{activity.user.name}</span>{' '}
                  <span className="text-slate-400">{activity.description}</span>{' '}
                  <span className="font-semibold text-blue-400">{activity.entityName}</span>
                </p>
                <p className="text-xs text-slate-500 mt-1">{formatRelativeTime(activity.timestamp)}</p>
              </div>
              <div className={`px-2 py-1 rounded text-xs ${
                activity.type === 'comment' ? 'bg-purple-600' :
                activity.type === 'share' ? 'bg-blue-600' :
                activity.type === 'create' ? 'bg-green-600' :
                'bg-orange-600'
              }`}>
                {activity.type}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tasks Tab */}
      {activeTab === 'tasks' && (
        <>
          {/* Task Filters */}
          <div className="flex items-center space-x-3 bg-slate-800 rounded-lg p-4">
            <Filter className="h-5 w-5 text-slate-400" />
            <div className="flex-1 flex items-center space-x-3">
              <select
                value={taskStatusFilter}
                onChange={(e) => setTaskStatusFilter(e.target.value as Task['status'] | 'all')}
                className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <select
                value={taskPriorityFilter}
                onChange={(e) => setTaskPriorityFilter(e.target.value as Task['priority'] | 'all')}
                className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Priority</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
              {(taskStatusFilter !== 'all' || taskPriorityFilter !== 'all') && (
                <button
                  onClick={() => {
                    setTaskStatusFilter('all');
                    setTaskPriorityFilter('all');
                  }}
                  className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
                >
                  Clear Filters
                </button>
              )}
            </div>
            <div className="text-sm text-slate-400">
              {filteredTasks.length} of {tasks.length} tasks
            </div>
          </div>

          <div className="space-y-4">
            {filteredTasks.length === 0 && (
              <div className="text-center py-12 text-slate-400">
                <CheckSquare className="h-16 w-16 mx-auto mb-4 opacity-30" />
                <p className="text-lg mb-2">No tasks found</p>
                <p className="text-sm">Try adjusting your search or filters, or create a new task</p>
              </div>
            )}
            {filteredTasks.map((task) => (
            <div key={task.id} className="bg-slate-800 rounded-xl p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="text-lg font-semibold">{task.title}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400">{task.description}</p>
                </div>
                <div className="relative">
                  <button
                    onClick={() => setTaskMenuOpen(taskMenuOpen === task.id ? null : task.id)}
                    className="p-1 hover:bg-slate-700 rounded transition-colors"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>
                  {taskMenuOpen === task.id && (
                    <div className="absolute right-0 mt-1 w-40 bg-slate-700 border border-slate-600 rounded-lg shadow-xl z-10">
                      <button
                        onClick={() => {
                          handleEditTask(task);
                          setTaskMenuOpen(null);
                        }}
                        className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-600 transition-colors text-left"
                      >
                        <Edit2 className="h-4 w-4" />
                        <span>Edit</span>
                      </button>
                      <button
                        onClick={() => {
                          setDeletingTask(task.id);
                          setTaskMenuOpen(null);
                        }}
                        className="w-full flex items-center space-x-2 px-4 py-2 hover:bg-slate-600 transition-colors text-left text-red-400"
                      >
                        <Trash2 className="h-4 w-4" />
                        <span>Delete</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center space-x-6 text-sm">
                {task.dueDate && (
                  <div className="flex items-center space-x-2 text-slate-400">
                    <Calendar className="h-4 w-4" />
                    <span>Due: {new Date(task.dueDate).toLocaleDateString()}</span>
                  </div>
                )}
                <div className="flex items-center space-x-2 text-slate-400">
                  <User className="h-4 w-4" />
                  <span>{task.assignedTo.length} assigned</span>
                </div>
              </div>

              {task.status !== 'completed' && (
                <div className="mt-4 flex items-center space-x-2">
                  <button
                    onClick={() => handleToggleTaskStatus(task)}
                    className="px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors"
                  >
                    Mark Complete
                  </button>
                  <button
                    onClick={() => handleEditTask(task)}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
                  >
                    Edit
                  </button>
                </div>
              )}
            </div>
          ))}
          </div>
        </>
      )}

      {/* Comments Tab */}
      {activeTab === 'comments' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="text-center py-12 text-slate-400">
            <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-30" />
            <p className="text-lg mb-2">Comments appear on entities</p>
            <p className="text-sm">Go to a player, match, or video to add comments</p>
          </div>
        </div>
      )}

      {/* New Workspace Modal */}
      {showNewWorkspace && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Create New Workspace</h2>
              <button
                onClick={() => setShowNewWorkspace(false)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Workspace Name</label>
                <input
                  type="text"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  placeholder="e.g., Premier League Prospects"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={workspaceDescription}
                  onChange={(e) => setWorkspaceDescription(e.target.value)}
                  placeholder="What is this workspace for?"
                  rows={3}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="workspace-public"
                  checked={workspaceIsPublic}
                  onChange={(e) => setWorkspaceIsPublic(e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="workspace-public" className="text-sm">
                  Make this workspace public
                </label>
              </div>

              {!workspaceName.trim() && (
                <p className="text-xs text-slate-400">* Workspace name is required</p>
              )}

              <div className="flex items-center space-x-3 pt-4">
                <button
                  onClick={handleCreateWorkspace}
                  disabled={!workspaceName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title={!workspaceName.trim() ? 'Please enter a workspace name' : ''}
                >
                  Create Workspace
                </button>
                <button
                  onClick={() => {
                    setShowNewWorkspace(false);
                    setWorkspaceName('');
                    setWorkspaceDescription('');
                    setWorkspaceIsPublic(false);
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Task Modal */}
      {showNewTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Create New Task</h2>
              <button
                onClick={() => setShowNewTask(false)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Task Title</label>
                <input
                  type="text"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  placeholder="e.g., Scout Haaland in next match"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                  placeholder="What needs to be done?"
                  rows={3}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Priority</label>
                <select
                  value={taskPriority}
                  onChange={(e) => setTaskPriority(e.target.value as 'low' | 'medium' | 'high' | 'urgent')}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Due Date</label>
                <input
                  type="date"
                  value={taskDueDate}
                  onChange={(e) => setTaskDueDate(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {!taskTitle.trim() && (
                <p className="text-xs text-slate-400">* Task title is required</p>
              )}

              <div className="flex items-center space-x-3 pt-4">
                <button
                  onClick={handleCreateTask}
                  disabled={!taskTitle.trim()}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title={!taskTitle.trim() ? 'Please enter a task title' : ''}
                >
                  Create Task
                </button>
                <button
                  onClick={() => {
                    setShowNewTask(false);
                    setTaskTitle('');
                    setTaskDescription('');
                    setTaskPriority('medium');
                    setTaskDueDate('');
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Workspace Modal */}
      {editingWorkspace && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Edit Workspace</h2>
              <button
                onClick={() => {
                  setEditingWorkspace(null);
                  setWorkspaceName('');
                  setWorkspaceDescription('');
                  setWorkspaceIsPublic(false);
                }}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Workspace Name</label>
                <input
                  type="text"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  placeholder="e.g., Premier League Prospects"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={workspaceDescription}
                  onChange={(e) => setWorkspaceDescription(e.target.value)}
                  placeholder="What is this workspace for?"
                  rows={3}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="edit-workspace-public"
                  checked={workspaceIsPublic}
                  onChange={(e) => setWorkspaceIsPublic(e.target.checked)}
                  className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="edit-workspace-public" className="text-sm">
                  Make this workspace public
                </label>
              </div>

              <div className="flex items-center space-x-3 pt-4">
                <button
                  onClick={handleUpdateWorkspace}
                  disabled={!workspaceName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Workspace
                </button>
                <button
                  onClick={() => {
                    setEditingWorkspace(null);
                    setWorkspaceName('');
                    setWorkspaceDescription('');
                    setWorkspaceIsPublic(false);
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Task Modal */}
      {editingTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Edit Task</h2>
              <button
                onClick={() => {
                  setEditingTask(null);
                  setTaskTitle('');
                  setTaskDescription('');
                  setTaskPriority('medium');
                  setTaskDueDate('');
                }}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Task Title</label>
                <input
                  type="text"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  placeholder="e.g., Scout Haaland in next match"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                  placeholder="What needs to be done?"
                  rows={3}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Priority</label>
                <select
                  value={taskPriority}
                  onChange={(e) => setTaskPriority(e.target.value as 'low' | 'medium' | 'high' | 'urgent')}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Due Date</label>
                <input
                  type="date"
                  value={taskDueDate}
                  onChange={(e) => setTaskDueDate(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex items-center space-x-3 pt-4">
                <button
                  onClick={handleUpdateTask}
                  disabled={!taskTitle.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Task
                </button>
                <button
                  onClick={() => {
                    setEditingTask(null);
                    setTaskTitle('');
                    setTaskDescription('');
                    setTaskPriority('medium');
                    setTaskDueDate('');
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Workspace Confirmation */}
      <ConfirmDialog
        isOpen={deletingWorkspace !== null}
        onClose={() => setDeletingWorkspace(null)}
        onConfirm={handleDeleteWorkspace}
        title="Delete Workspace"
        message="Are you sure you want to delete this workspace? This action cannot be undone and all associated data will be lost."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Delete Task Confirmation */}
      <ConfirmDialog
        isOpen={deletingTask !== null}
        onClose={() => setDeletingTask(null)}
        onConfirm={handleDeleteTask}
        title="Delete Task"
        message="Are you sure you want to delete this task? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Workspace View Modal */}
      {viewingWorkspace && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <h2 className="text-2xl font-bold">{viewingWorkspace.name}</h2>
                {viewingWorkspace.isPublic ? (
                  <Unlock className="h-5 w-5 text-green-400" title="Public" />
                ) : (
                  <Lock className="h-5 w-5 text-slate-400" title="Private" />
                )}
              </div>
              <button
                onClick={() => setViewingWorkspace(null)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Description */}
            <p className="text-slate-300 mb-6">{viewingWorkspace.description}</p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-slate-700 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-blue-400">{viewingWorkspace.items.length}</div>
                <div className="text-sm text-slate-400 mt-1">Items</div>
              </div>
              <div className="bg-slate-700 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-green-400">{viewingWorkspace.members.length}</div>
                <div className="text-sm text-slate-400 mt-1">Members</div>
              </div>
              <div className="bg-slate-700 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-purple-400">
                  {activities.filter(a => a.entityId === viewingWorkspace.id).length}
                </div>
                <div className="text-sm text-slate-400 mt-1">Activities</div>
              </div>
            </div>

            {/* Members Section */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <Users className="h-5 w-5 mr-2" />
                Members
              </h3>
              <div className="space-y-2">
                {viewingWorkspace.members.map((member) => (
                  <div key={member.userId} className="bg-slate-700 rounded-lg p-3 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center font-semibold">
                        {member.name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-semibold">{member.name}</div>
                        <div className="text-sm text-slate-400">{member.email}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        member.role === 'owner' ? 'bg-purple-600' :
                        member.role === 'admin' ? 'bg-blue-600' :
                        'bg-slate-600'
                      }`}>
                        {member.role}
                      </span>
                      <span className="text-xs text-slate-400">
                        Joined {new Date(member.joinedAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Items Section */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <Folder className="h-5 w-5 mr-2" />
                Items ({viewingWorkspace.items.length})
              </h3>
              {viewingWorkspace.items.length > 0 ? (
                <div className="space-y-2">
                  {viewingWorkspace.items.map((item) => (
                    <div key={item.id} className="bg-slate-700 rounded-lg p-3 flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{item.name}</div>
                        <div className="text-sm text-slate-400">{item.type}</div>
                      </div>
                      <span className="text-xs text-slate-400">
                        Added {new Date(item.addedAt).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-4">No items in this workspace yet</p>
              )}
            </div>

            {/* Recent Activity */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <ActivityIcon className="h-5 w-5 mr-2" />
                Recent Activity
              </h3>
              <div className="space-y-2">
                {activities
                  .filter(a => a.entityId === viewingWorkspace.id)
                  .slice(0, 5)
                  .map((activity) => (
                    <div key={activity.id} className="bg-slate-700 rounded-lg p-3 flex items-start space-x-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center text-xs font-semibold">
                        {activity.user.name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm">
                          <span className="font-semibold">{activity.user.name}</span>{' '}
                          <span className="text-slate-400">{activity.description}</span>{' '}
                          <span className="font-semibold text-blue-400">{activity.entityName}</span>
                        </p>
                        <p className="text-xs text-slate-500 mt-1">{formatRelativeTime(activity.timestamp)}</p>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs ${
                        activity.type === 'comment' ? 'bg-purple-600' :
                        activity.type === 'share' ? 'bg-blue-600' :
                        activity.type === 'create' ? 'bg-green-600' :
                        'bg-orange-600'
                      }`}>
                        {activity.type}
                      </div>
                    </div>
                  ))}
                {activities.filter(a => a.entityId === viewingWorkspace.id).length === 0 && (
                  <p className="text-center text-slate-400 py-4">No recent activity</p>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-3 mt-6 pt-6 border-t border-slate-700">
              <button
                onClick={() => {
                  handleEditWorkspace(viewingWorkspace);
                  setViewingWorkspace(null);
                }}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                Edit Workspace
              </button>
              <button
                onClick={() => setViewingWorkspace(null)}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CollaborationHub;
