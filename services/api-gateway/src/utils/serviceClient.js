const { URL } = require('url');

function buildServiceUrl(baseUrl, path, query = {}) {
  const url = new URL(path, `${baseUrl.replace(/\/$/, '')}/`);

  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => url.searchParams.append(key, String(item)));
      return;
    }

    url.searchParams.append(key, String(value));
  });

  return url.toString();
}

async function requestJson(baseUrl, path, options = {}) {
  const {
    method = 'GET',
    query = {},
    body,
    headers = {},
    timeoutMs = 10000,
  } = options;

  const controller = new AbortController();
  const timeoutId = timeoutMs > 0
    ? setTimeout(() => controller.abort(), timeoutMs)
    : null;

    try {
      const response = await fetch(buildServiceUrl(baseUrl, path, query), {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });

      const text = await response.text();
      let payload = null;

      if (text) {
        try {
          payload = JSON.parse(text);
        } catch {
          payload = { raw: text };
        }
      }

      return {
        ok: response.ok,
        status: response.status,
        payload,
      };
    } catch (error) {
      if (error?.name === 'AbortError') {
        return {
          ok: false,
          status: 504,
          payload: {
            error: 'Upstream request timed out',
            message: `Request to ${buildServiceUrl(baseUrl, path, query)} timed out after ${timeoutMs}ms`,
          },
        };
      }

      throw error;
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
}

function unwrapPayload(payload) {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return payload.data;
  }
  return payload;
}

function ensureSuccess(result, fallbackMessage) {
  if (result.ok) {
    return result.payload;
  }

  const error = new Error(fallbackMessage);
  error.status = result.status;
  error.payload = result.payload;
  throw error;
}

function normalizeEntity(entity) {
  if (!entity || typeof entity !== 'object') {
    return entity;
  }

  const normalized = { ...entity };

  if (normalized.uID !== undefined && normalized.id === undefined) {
    normalized.id = String(normalized.uID);
  }

  delete normalized._id;
  return normalized;
}

function normalizeList(items) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items.map(normalizeEntity);
}

function sendGatewayError(res, error, fallbackMessage) {
  if (error.status && error.payload) {
    return res.status(error.status).json(error.payload);
  }

  return res.status(502).json({
    error: fallbackMessage,
    message: error.message,
  });
}

module.exports = {
  ensureSuccess,
  normalizeEntity,
  normalizeList,
  requestJson,
  sendGatewayError,
  unwrapPayload,
};