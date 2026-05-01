import React, { useMemo, useState } from 'react';
import { 
  Shield, Users, Key, Bell, Settings, Activity, 
  Eye, Lock, CreditCard, Database, AlertTriangle, Loader2, RefreshCw, FileText
} from 'lucide-react';
import apiService from '../services/api';
import { useApi } from '../hooks/useApi';

const formatDateTime = (value?: string) => {
  if (!value) {
    return 'Pending';
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
};

const AdminConsole: React.FC = () => {
  const [activeSection, setActiveSection] = useState('users');
  const { data: adminSnapshot, loading, error, refetch } = useApi<any>(
    () => apiService.getAdminSnapshot(), []
  );

  const summary = adminSnapshot?.summary || {
    totalUsers: 0,
    activeUsers: 0,
    totalPlayers: 0,
    totalTeams: 0,
    totalReports: 0,
    activeApiKeys: 0,
  };
  const userRoles = adminSnapshot?.users || [];
  const roles = adminSnapshot?.roles || [];
  const permissionRows = adminSnapshot?.permissionMatrix || [];
  const apiKeys = adminSnapshot?.apiKeys || [];
  const auditLogs = adminSnapshot?.auditLogs || [];
  const subscriptions = adminSnapshot?.subscriptions || [];
  const systemHealth = adminSnapshot?.systemHealth || { status: 'unknown', services: [], alerts: [] };

  const summaryCards = useMemo(() => ([
    { label: 'Users', value: summary.totalUsers, detail: `${summary.activeUsers} active`, icon: Users, tone: 'text-blue-400' },
    { label: 'Active API Keys', value: summary.activeApiKeys, detail: 'Backend-managed integrations', icon: Key, tone: 'text-emerald-400' },
    { label: 'Reports Generated', value: summary.totalReports, detail: 'Persisted backend jobs', icon: FileText, tone: 'text-purple-400' },
    { label: 'Indexed Players', value: summary.totalPlayers, detail: `${summary.totalTeams} teams available`, icon: Database, tone: 'text-amber-400' },
  ]), [summary.activeApiKeys, summary.activeUsers, summary.totalPlayers, summary.totalReports, summary.totalTeams, summary.totalUsers]);

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
          <button
            onClick={() => refetch()}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span className="text-sm">Refresh</span>
          </button>
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${systemHealth.status === 'healthy' ? 'bg-green-600' : systemHealth.status === 'degraded' ? 'bg-yellow-600' : 'bg-slate-700'}`}>
            <Activity className="h-4 w-4" />
            <span className="text-sm">{systemHealth.status === 'healthy' ? 'System Healthy' : systemHealth.status === 'degraded' ? 'Degraded Mode' : 'Loading Health'}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading && !adminSnapshot ? (
        <div className="flex items-center justify-center rounded-xl bg-slate-800 px-6 py-20 text-slate-300">
          <Loader2 className="mr-3 h-5 w-5 animate-spin text-red-400" />
          Loading admin snapshot...
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {summaryCards.map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.label} className="bg-slate-800 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-2xl font-bold text-white">{card.value}</div>
                      <div className="text-slate-400 text-sm">{card.label}</div>
                    </div>
                    <Icon className={`h-8 w-8 ${card.tone}`} />
                  </div>
                  <div className="text-sm text-slate-400">{card.detail}</div>
                </div>
              );
            })}
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
                    <td className="py-3 px-2">
                      <div className="font-semibold">{user.name}</div>
                      <div className="text-xs text-slate-400">{user.email || user.team || 'No team assigned'}</div>
                    </td>
                    <td className="py-3 px-2">{user.role}</td>
                    <td className="py-3 px-2">{user.access}</td>
                    <td className="py-3 px-2 text-slate-400">{formatDateTime(user.lastActive)}</td>
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
              {roles.map((role, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold">{role.label}</h4>
                    <span className="text-xs text-slate-400">{role.access}</span>
                  </div>
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
                  {permissionRows.map((row, index) => (
                    <tr key={index} className="border-b border-slate-700">
                      <td className="py-2 font-medium">{row.feature}</td>
                      <td className="text-center py-2">
                        {row.admin ? <span className="text-green-400">✓</span> : <span className="text-red-400">✗</span>}
                      </td>
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
                  <span>Created: {formatDateTime(api.createdAt || api.created)}</span>
                  <span>Last used: {formatDateTime(api.lastUsed)}</span>
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
                  <div className="text-sm text-slate-400">{formatDateTime(log.time)}</div>
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
                ...(systemHealth.services || []),
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
              {(systemHealth.alerts || []).map((alert: any) => {
                const tone = alert.type === 'warning'
                  ? 'bg-yellow-600/10 border-yellow-600/20 text-yellow-400'
                  : alert.type === 'success'
                    ? 'bg-green-600/10 border-green-600/20 text-green-400'
                    : 'bg-blue-600/10 border-blue-600/20 text-blue-400';
                const Icon = alert.type === 'warning' ? AlertTriangle : alert.type === 'success' ? Activity : Database;

                return (
                  <div key={alert.id} className={`p-3 border rounded-lg ${tone}`}>
                    <div className="flex items-center space-x-2 mb-1">
                      <Icon className="h-4 w-4" />
                      <span className="font-semibold">{alert.title}</span>
                    </div>
                    <p className="text-sm text-slate-300">
                      {alert.message}
                    </p>
                    <div className="text-xs text-slate-400 mt-1">{formatDateTime(alert.time)}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
        </>
      )}
    </div>
  );
};

export default AdminConsole;