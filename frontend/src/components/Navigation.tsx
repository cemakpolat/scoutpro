import React, { useState } from 'react';
import {
  Home, Users, Activity, Search, FileText, BarChart3, Settings,
  Target, Bell, ChevronDown, Zap, TrendingUp, Shield, Menu, X, LogOut, User as UserIcon, Film,
  Calendar as CalendarIcon, Upload, Cpu
} from 'lucide-react';
import { Database, Layers, LineChart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface NavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  notifications: any[];
}

const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab, notifications }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const unreadCount = notifications.filter(n => !n.read).length;

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'search', label: 'Advanced Search', icon: Search },
    { id: 'player-comparison', label: 'Player Comparison', icon: Users },
    { id: 'video-analysis', label: 'Video Analysis', icon: Film },
    { id: 'collaboration', label: 'Collaboration Hub', icon: Users },
    { id: 'calendar', label: 'Calendar & Schedule', icon: CalendarIcon },
    { id: 'match-centre', label: 'Match Centre', icon: Activity },
    { id: 'match-analysis', label: 'Match Analysis', icon: Target },
    { id: 'multi-match', label: 'Multi-Match Analysis', icon: BarChart3 },
    { id: 'players', label: 'Player Profiles', icon: Users },
    { id: 'scouting', label: 'Scouting Hub', icon: Target },
    { id: 'reports', label: 'Report Builder', icon: FileText },
    { id: 'analytics', label: 'Analytics Lab', icon: BarChart3 },
    { id: 'ml-lab', label: 'ML Laboratory', icon: TrendingUp },
    { id: 'data-management', label: 'Data Management', icon: Database },
    { id: 'data-importer', label: 'Data Import/Export', icon: Upload },
    { id: 'task-queue', label: 'Background Tasks', icon: Cpu },
    { id: 'tactical-analyzer', label: 'Tactical Analyzer', icon: Layers },
    { id: 'performance-tracker', label: 'Performance Tracker', icon: LineChart },
    { id: 'admin', label: 'Admin Console', icon: Shield },
  ];

  const handleNavClick = (tabId: string) => {
    setActiveTab(tabId);
    setIsSidebarOpen(false); // Close sidebar on mobile after selection
  };

  return (
    <>
      {/* Mobile Menu Button - Fixed at top left */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition-colors"
        aria-label="Toggle menu"
      >
        {isSidebarOpen ? (
          <X className="h-6 w-6 text-white" />
        ) : (
          <Menu className="h-6 w-6 text-white" />
        )}
      </button>

      {/* Overlay for mobile when sidebar is open */}
      {isSidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <nav
        className={`fixed left-0 top-0 h-full w-64 bg-slate-800 border-r border-slate-700 z-50 flex flex-col transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-6 flex-shrink-0">
          <div className="flex items-center space-x-3 mb-8">
            <div className="p-2 bg-gradient-to-br from-green-400 to-blue-500 rounded-lg">
              <Target className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">ScoutPro</h1>
              <p className="text-xs text-slate-400">Advanced Analytics</p>
            </div>
          </div>

          {/* Notification Bell */}
          <div className="relative mb-6">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="w-full flex items-center justify-between p-3 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors"
            >
              <div className="flex items-center space-x-2">
                <Bell className="h-5 w-5 text-yellow-400" />
                <span className="text-sm">Notifications</span>
              </div>
              {unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Scrollable navigation items */}
        <div className="flex-1 overflow-y-auto px-6 pb-6">
          <ul className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.id}>
                  <button
                    onClick={() => handleNavClick(item.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                      activeTab === item.id
                        ? 'bg-gradient-to-r from-green-600 to-blue-600 text-white shadow-lg'
                        : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                    }`}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* User Profile & Logout */}
        <div className="px-6 pb-6 border-t border-slate-700 pt-4 flex-shrink-0">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
              {user?.avatar ? (
                <img src={user.avatar} alt={user.name} className="w-full h-full rounded-full object-cover" />
              ) : (
                <UserIcon className="h-5 w-5 text-white" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name}</p>
              <p className="text-xs text-slate-400 truncate capitalize">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center space-x-2 px-4 py-2 text-slate-300 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span className="text-sm">Logout</span>
          </button>
        </div>
      </nav>
    </>
  );
};

export default Navigation;