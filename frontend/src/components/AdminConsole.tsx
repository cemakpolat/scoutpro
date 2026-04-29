import React, { useState, useEffect } from 'react';
import { 
  Shield, Users, Key, Bell, Settings, Activity, 
  Eye, Lock, CreditCard, Database, AlertTriangle, Loader2
} from 'lucide-react';
import apiService from '../services/api';
import { useData } from '../context/DataContext';

const AdminConsole: React.FC = () => {
  const [activeSection, setActiveSection] = useState('users');
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [dashboardStats, setDashboardStats] = useState<any>(null);

  const { players, teams } = useData();

  // Fetch system health from API on mount
  useEffect(() => {
    Promise.all([
      apiService.getDashboardOverview().catch(() => null),
    ]).then(([overview]) => {
      if (overview) setDashboardStats(overview);
    });

    // Check API health
    fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api'}/health`)
      .then(r => r.json())
      .then(data => setSystemHealth(data))
      .catch(() => {});
  }, []);

  const userRoles = [
    { name: 'John Smith', role: 'Head Scout', access: 'Full Access', lastActive: '2 hours ago', status: 'active' },
    { name: 'Sarah Wilson', role: 'Analyst', access: 'Analytics Only', lastActive: '1 day ago', status: 'active' },
    { name: 'Mike Johnson', role: 'Coach', access: 'Reports Only', lastActive: '3 hours ago', status: 'active' },
    { name: 'Emma Davis', role: 'Executive', access: 'Executive Dashboard', lastActive: '1 week ago', status: 'inactive' },
  ];

  const apiKeys = [
    { name: 'Mobile App', key: 'sk_live_...7x9z', created: '2024-01-15', lastUsed: '2 hours ago', status: 'active' },
    { name: 'Data Export', key: 'sk_live_...3m8n', created: '2024-01-10', lastUsed: '1 day ago', status: 'active' },
    { name: 'Third Party Integration', key: 'sk_live_...9k2l', created: '2023-12-20', lastUsed: '1 month ago', status: 'inactive' },
  ];

  const auditLogs = [
    { user: 'John Smith', action: 'Viewed player report', resource: 'Kylian Mbappé', time: '10 min ago' },
    { user: 'Sarah Wilson', action: 'Generated analytics report', resource: 'Team Performance', time: '1 hour ago' },
    { user: 'Mike Johnson', action: 'Downloaded PDF report', resource: 'Match Analysis', time: '2 hours ago' },
    { user: 'Emma Davis', action: 'Accessed executive dashboard', resource: 'Market Overview', time: '1 day ago' },
  ];

  const subscriptions = [
    { club: 'Manchester United', plan: 'Enterprise', users: 25, expires: '2024-12-31', status: 'active' },
    { club: 'Barcelona FC', plan: 'Professional', users: 15, expires: '2024-11-15', status: 'active' },
    { club: 'Bayern Munich', plan: 'Professional', users: 12, expires: '2024-10-20', status: 'expiring' },
    { club: 'Juventus', plan: 'Basic', users: 5, expires: '2024-09-30', status: 'expired' },
  ];

  const sections = [
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'permissions', label: 'Permissions', icon: Lock },
    { id: 'api', label: 'API Keys', icon: Key },
    { id: 'audit', label: 'Audit Logs', icon: Eye },
    { id: 'subscriptions', label: 'Subscriptions', icon: CreditCard },
    { id: 'system', label: 'System Health', icon: Activity },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Shield className="h-8 w-8 mr-3 text-red-500" />
          Admin Console
        </h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-600 rounded-lg">
            <Activity className="h-4 w-4" />
            <span className="text-sm">System Healthy</span>
          </div>
        </div>
      </div>

      {/* Section Navigation */}
      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex flex-wrap gap-2">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  activeSection === section.id
                    ? 'bg-red-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="text-sm">{section.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Dynamic Content */}
      {activeSection === 'users' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold">User Management</h3>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
              Add User
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">User</th>
                  <th className="text-left py-3 px-2">Role</th>
                  <th className="text-left py-3 px-2">Access Level</th>
                  <th className="text-left py-3 px-2">Last Active</th>
                  <th className="text-left py-3 px-2">Status</th>
                  <th className="text-left py-3 px-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {userRoles.map((user, index) => (
                  <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                    <td className="py-3 px-2 font-semibold">{user.name}</td>
                    <td className="py-3 px-2">{user.role}</td>
                    <td className="py-3 px-2">{user.access}</td>
                    <td className="py-3 px-2 text-slate-400">{user.lastActive}</td>
                    <td className="py-3 px-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        user.status === 'active' ? 'bg-green-600 text-green-100' : 'bg-red-600 text-red-100'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="py-3 px-2">
                      <div className="flex space-x-2">
                        <button className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs transition-colors">
                          Edit
                        </button>
                        <button className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs transition-colors">
                          Suspend
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeSection === 'permissions' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Role-Based Access Control</h3>
            <div className="space-y-4">
              {[
                { role: 'Head Scout', permissions: ['Full Database Access', 'Report Generation', 'User Management', 'API Access'] },
                { role: 'Analyst', permissions: ['Analytics Dashboard', 'Report Generation', 'Data Export'] },
                { role: 'Coach', permissions: ['Player Reports', 'Match Analysis', 'Basic Dashboard'] },
                { role: 'Executive', permissions: ['Executive Dashboard', 'Market Intelligence', 'High-Level Reports'] },
              ].map((role, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <h4 className="font-semibold mb-3">{role.role}</h4>
                  <div className="space-y-2">
                    {role.permissions.map((permission, i) => (
                      <div key={i} className="flex items-center space-x-2">
                        <input type="checkbox" defaultChecked className="rounded" />
                        <span className="text-sm">{permission}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Permission Matrix</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-2">Feature</th>
                    <th className="text-center py-2">Scout</th>
                    <th className="text-center py-2">Analyst</th>
                    <th className="text-center py-2">Coach</th>
                    <th className="text-center py-2">Executive</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { feature: 'Player Database', scout: true, analyst: true, coach: true, executive: false },
                    { feature: 'Match Centre', scout: true, analyst: true, coach: true, executive: false },
                    { feature: 'Analytics Lab', scout: true, analyst: true, coach: false, executive: true },
                    { feature: 'Report Builder', scout: true, analyst: true, coach: true, executive: true },
                    { feature: 'Admin Console', scout: true, analyst: false, coach: false, executive: false },
                  ].map((row, index) => (
                    <tr key={index} className="border-b border-slate-700">
                      <td className="py-2 font-medium">{row.feature}</td>
                      <td className="text-center py-2">
                        {row.scout ? <span className="text-green-400">✓</span> : <span className="text-red-400">✗</span>}
                      </td>
                      <td className="text-center py-2">
                        {row.analyst ? <span className="text-green-400">✓</span> : <span className="text-red-400">✗</span>}
                      </td>
                      <td className="text-center py-2">
                        {row.coach ? <span className="text-green-400">✓</span> : <span className="text-red-400">✗</span>}
                      </td>
                      <td className="text-center py-2">
                        {row.executive ? <span className="text-green-400">✓</span> : <span className="text-red-400">✗</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeSection === 'api' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold">API Key Management</h3>
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
              Generate New Key
            </button>
          </div>
          <div className="space-y-4">
            {apiKeys.map((api, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-semibold">{api.name}</h4>
                    <p className="text-sm text-slate-400 font-mono">{api.key}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      api.status === 'active' ? 'bg-green-600 text-green-100' : 'bg-red-600 text-red-100'
                    }`}>
                      {api.status}
                    </span>
                    <button className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-xs transition-colors">
                      Revoke
                    </button>
                  </div>
                </div>
                <div className="flex justify-between text-sm text-slate-400">
                  <span>Created: {api.created}</span>
                  <span>Last used: {api.lastUsed}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeSection === 'audit' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Audit Trail</h3>
          <div className="space-y-3">
            {auditLogs.map((log, index) => (
              <div key={index} className="flex items-center space-x-4 p-3 bg-slate-700 rounded-lg">
                <Eye className="h-5 w-5 text-blue-400" />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold">{log.user}</span>
                    <span className="text-slate-400">•</span>
                    <span>{log.action}</span>
                    <span className="text-slate-400">•</span>
                    <span className="text-blue-400">{log.resource}</span>
                  </div>
                  <div className="text-sm text-slate-400">{log.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeSection === 'subscriptions' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Subscription Management</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">Club</th>
                  <th className="text-left py-3 px-2">Plan</th>
                  <th className="text-left py-3 px-2">Users</th>
                  <th className="text-left py-3 px-2">Expires</th>
                  <th className="text-left py-3 px-2">Status</th>
                  <th className="text-left py-3 px-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {subscriptions.map((sub, index) => (
                  <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                    <td className="py-3 px-2 font-semibold">{sub.club}</td>
                    <td className="py-3 px-2">{sub.plan}</td>
                    <td className="py-3 px-2">{sub.users}</td>
                    <td className="py-3 px-2">{sub.expires}</td>
                    <td className="py-3 px-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        sub.status === 'active' ? 'bg-green-600 text-green-100' :
                        sub.status === 'expiring' ? 'bg-yellow-600 text-yellow-100' :
                        'bg-red-600 text-red-100'
                      }`}>
                        {sub.status}
                      </span>
                    </td>
                    <td className="py-3 px-2">
                      <div className="flex space-x-2">
                        <button className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs transition-colors">
                          Manage
                        </button>
                        <button className="px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-xs transition-colors">
                          Renew
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeSection === 'system' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">System Health</h3>
            <div className="space-y-4">
              {[
                { service: 'API Gateway', status: systemHealth ? 'healthy' : 'unknown', uptime: '99.9%', response: systemHealth ? '45ms' : 'N/A' },
                { service: 'Database', status: systemHealth?.mongodb === 'connected' ? 'healthy' : 'warning', uptime: '99.8%', response: '12ms' },
                { service: 'ML Models', status: 'healthy', uptime: '99.7%', response: '234ms' },
                { service: 'Data Pipeline', status: dashboardStats ? 'healthy' : 'unknown', uptime: dashboardStats ? '99.5%' : 'N/A', response: '89ms' },
              ].map((service, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{service.service}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      service.status === 'healthy' ? 'bg-green-600 text-green-100' :
                      service.status === 'warning' ? 'bg-yellow-600 text-yellow-100' :
                      'bg-red-600 text-red-100'
                    }`}>
                      {service.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-slate-400">Uptime</div>
                      <div className="font-semibold">{service.uptime}</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Response Time</div>
                      <div className="font-semibold">{service.response}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">System Alerts</h3>
            <div className="space-y-3">
              <div className="p-3 bg-yellow-600/10 border border-yellow-600/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-1">
                  <AlertTriangle className="h-4 w-4 text-yellow-400" />
                  <span className="font-semibold text-yellow-400">Warning</span>
                </div>
                <p className="text-sm text-slate-300">
                  File storage usage at 85%. Consider upgrading storage plan.
                </p>
                <div className="text-xs text-slate-400 mt-1">2 hours ago</div>
              </div>

              <div className="p-3 bg-blue-600/10 border border-blue-600/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-1">
                  <Database className="h-4 w-4 text-blue-400" />
                  <span className="font-semibold text-blue-400">Info</span>
                </div>
                <p className="text-sm text-slate-300">
                  Database maintenance scheduled for tonight at 2 AM UTC.
                </p>
                <div className="text-xs text-slate-400 mt-1">1 day ago</div>
              </div>

              <div className="p-3 bg-green-600/10 border border-green-600/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-1">
                  <Activity className="h-4 w-4 text-green-400" />
                  <span className="font-semibold text-green-400">Success</span>
                </div>
                <p className="text-sm text-slate-300">
                  ML models updated successfully. Accuracy improved by 2.3%.
                </p>
                <div className="text-xs text-slate-400 mt-1">3 days ago</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminConsole;