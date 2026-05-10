import React, { useState, useEffect } from 'react';

type Provider = 'opta' | 'statsbomb' | 'custom';

interface ProviderStatus {
  provider: Provider;
  is_configured: boolean;
  environment: string;
  is_active: boolean;
}

const PROVIDER_META: Record<Provider, { label: string; color: string; hasKey: boolean; hasUser: boolean; description: string }> = {
  opta:      { label: 'Opta',      color: 'purple', hasKey: true,  hasUser: true,  description: 'F1/F24/F40 feeds via REST API' },
  statsbomb: { label: 'StatsBomb', color: 'blue',   hasKey: true,  hasUser: false, description: 'Open data + commercial API' },
  custom:    { label: 'Custom',    color: 'gray',   hasKey: false, hasUser: false, description: 'File-based manual import, no credentials needed' },
};

const DOT_COLOR: Record<string, string> = {
  purple: 'bg-purple-500',
  blue:   'bg-blue-500',
  gray:   'bg-gray-400',
};

const BADGE_COLOR: Record<string, string> = {
  purple: 'bg-purple-100 text-purple-700',
  blue:   'bg-blue-100 text-blue-700',
  gray:   'bg-gray-100 text-gray-600',
};

export const ProviderCredentialsPanel = () => {
  const [selected, setSelected] = useState<Provider>('opta');
  const [statuses, setStatuses] = useState<ProviderStatus[]>([]);
  const [apiKey, setApiKey] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [environment, setEnvironment] = useState<'production' | 'staging' | 'development'>('production');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetch('/api/v2/batch-jobs/admin/providers')
      .then(r => r.json())
      .then(data => setStatuses(data.providers || []))
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/v2/batch-jobs/admin/providers/${selected}/credentials`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: selected,
          api_key: apiKey || undefined,
          username: username || undefined,
          password: password || undefined,
          environment,
          is_active: true,
        }),
      });
      if (!res.ok) throw new Error('Failed to save');
      setMessage({ type: 'success', text: `${PROVIDER_META[selected].label} credentials saved.` });
      setPassword('');
      // refresh statuses
      fetch('/api/v2/batch-jobs/admin/providers')
        .then(r => r.json())
        .then(data => setStatuses(data.providers || []))
        .catch(() => {});
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message || 'Save failed' });
    } finally {
      setSaving(false);
    }
  };

  const meta = PROVIDER_META[selected];
  const currentStatus = statuses.find(s => s.provider === selected);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      {/* Provider list */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Select Provider</h3>
        {(Object.keys(PROVIDER_META) as Provider[]).map(p => {
          const m = PROVIDER_META[p];
          const status = statuses.find(s => s.provider === p);
          return (
            <button
              key={p}
              onClick={() => { setSelected(p); setMessage(null); setApiKey(''); setUsername(''); setPassword(''); }}
              className={`w-full flex items-start gap-3 p-4 rounded-lg border text-left transition-colors ${
                selected === p ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className={`h-9 w-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${BADGE_COLOR[m.color]}`}>
                {m.label[0]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-gray-900">{m.label}</p>
                  {status && (
                    <span className={`h-1.5 w-1.5 rounded-full ${status.is_configured && status.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                  )}
                </div>
                <p className="text-xs text-gray-500 truncate">{m.description}</p>
                {status?.is_configured && (
                  <p className="text-xs text-gray-400 mt-0.5 capitalize">{status.environment}</p>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Credential form */}
      <div className="lg:col-span-2 space-y-4">
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-5 py-4 border-b border-gray-200 flex items-center gap-3">
            <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold ${BADGE_COLOR[meta.color]}`}>
              {meta.label[0]}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">{meta.label} Configuration</h3>
              {currentStatus?.is_configured ? (
                <p className="text-xs text-green-600">Configured · {currentStatus.environment}</p>
              ) : (
                <p className="text-xs text-gray-400">Not configured</p>
              )}
            </div>
          </div>

          <div className="p-5 space-y-4">
            {message && (
              <div className={`p-3 rounded-md text-sm border ${
                message.type === 'success'
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-red-50 border-red-200 text-red-700'
              }`}>
                {message.text}
              </div>
            )}

            {selected === 'custom' ? (
              <div className="py-4 text-center">
                <p className="text-sm text-gray-500">
                  Custom imports are file-based and require no credentials.
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Use the <strong>Data Management</strong> section to upload CSV or JSON files.
                </p>
              </div>
            ) : (
              <>
                {meta.hasKey && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={e => setApiKey(e.target.value)}
                      placeholder={currentStatus?.is_configured ? '••••••••  (leave blank to keep existing)' : 'Enter API key...'}
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm font-mono"
                    />
                  </div>
                )}
                {meta.hasUser && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                      <input
                        type="text"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        placeholder="Enter username..."
                        autoComplete="off"
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                      <input
                        type="password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        placeholder={currentStatus?.is_configured ? '••••••••  (leave blank to keep existing)' : 'Enter password...'}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                      />
                    </div>
                  </>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
                  <select
                    value={environment}
                    onChange={e => setEnvironment(e.target.value as typeof environment)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                  >
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development (mock)</option>
                  </select>
                </div>
                <div className="pt-1">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                  >
                    {saving ? 'Saving...' : 'Save Credentials'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-xs text-amber-800 space-y-1">
          <p className="font-semibold">Security</p>
          <p>Credentials are stored encrypted at rest and masked in all logs and audit trails.</p>
          <p>Only administrators can view or modify provider credentials.</p>
        </div>
      </div>
    </div>
  );
};
