function stripTrailingSlash(value: string): string {
  return value.endsWith('/') ? value.slice(0, -1) : value;
}

function resolveDefaultApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    // If accessed through a proxy/nginx on port 80/443, use relative path
    if ([80, 443, ''].includes(String(window.location.port))) {
      return '/api';
    }
    // If on dev server or direct API access, use direct URL
    if (['localhost', '127.0.0.1'].includes(window.location.hostname)) {
      return `${window.location.protocol}//${window.location.hostname}:3001/api`;
    }
  }

  return '/api';
}

export const API_BASE_URL = stripTrailingSlash(
  import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || resolveDefaultApiBaseUrl()
);

export const GATEWAY_BASE_URL = API_BASE_URL.endsWith('/api')
  ? API_BASE_URL.slice(0, -4) || ''
  : API_BASE_URL;

export const GATEWAY_HEALTH_URL = `${GATEWAY_BASE_URL || ''}/health`;