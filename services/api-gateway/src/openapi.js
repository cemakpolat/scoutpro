const fs = require('fs');
const path = require('path');

const ROUTE_MODULES = [
  { file: 'auth.js', mountPath: '/api/auth', tag: 'auth' },
  { file: 'players.js', mountPath: '/api/players', tag: 'players' },
  { file: 'detailed-stats.js', mountPath: '/api/players', tag: 'players' },
  { file: 'matches.js', mountPath: '/api/matches', tag: 'matches' },
  { file: 'teams.js', mountPath: '/api/teams', tag: 'teams' },
  { file: 'analytics.js', mountPath: '/api/analytics', tag: 'analytics' },
  { file: 'statistics.js', mountPath: '/api/statistics', tag: 'statistics' },
  { file: 'notifications.js', mountPath: '/api/notifications', tag: 'notifications' },
  { file: 'ml.js', mountPath: '/api/ml', tag: 'ml' },
  { file: 'search.js', mountPath: '/api/search', tag: 'search' },
  { file: 'reports.js', mountPath: '/api/v2/reports', tag: 'reports' },
  { file: 'exports.js', mountPath: '/api/v2/exports', tag: 'exports' },
  { file: 'imports.js', mountPath: '/api/v2/imports', tag: 'imports' },
  { file: 'calendar.js', mountPath: '/api/v2/calendar', tag: 'calendar' },
  { file: 'collaboration.js', mountPath: '/api/v2/collaboration', tag: 'collaboration' },
  { file: 'admin.js', mountPath: '/api/v2/admin', tag: 'admin' },
  { file: 'leagues.js', mountPath: '/api/leagues', tag: 'leagues' },
  { file: 'market.js', mountPath: '/api/market', tag: 'market' },
  { file: 'tactical.js', mountPath: '/api/tactical', tag: 'tactical' },
  { file: 'ai.js', mountPath: '/api/ai', tag: 'ai' },
  { file: 'videos.js', mountPath: '/api/v2/videos', tag: 'videos' },
  { file: 'events.js', mountPath: '/api/v2/events', tag: 'events' },
  { file: 'advancedAnalytics.js', mountPath: '/api/v2/analytics', tag: 'analytics' },
  { file: 'tasks.js', mountPath: '/api/tasks', tag: 'tasks' },
];

const TAG_DESCRIPTIONS = {
  system: 'Gateway metadata, health, and documentation endpoints.',
  auth: 'Authentication and current-user endpoints.',
  players: 'Player discovery, enrichment, and advanced statistics endpoints.',
  matches: 'Match discovery, live data, event feeds, and visualizations.',
  teams: 'Team catalog, squad, and event endpoints.',
  leagues: 'League list, detail, and match lookup endpoints.',
  analytics: 'Legacy analytics routes and v2 advanced analytics insights.',
  statistics: 'Statistics-service projections, rankings, and comparisons.',
  notifications: 'Notification feed and read-state management endpoints.',
  ml: 'Machine-learning catalog, training, prediction, and similarity endpoints.',
  search: 'Unified search, saved searches, and search history endpoints.',
  reports: 'Asynchronous report generation, listing, download, and deletion endpoints.',
  exports: 'Dataset export endpoints and export templates.',
  imports: 'Import templates, jobs, retries, and import report endpoints.',
  calendar: 'Calendar scheduling, trip planning, and match assignment endpoints.',
  collaboration: 'Workspace, task, and activity collaboration endpoints.',
  admin: 'Administrative monitoring and snapshot endpoints.',
  market: 'Market trends, predictions, and valuation endpoints.',
  tactical: 'Tactical patterns, formations, heatmaps, and overview endpoints.',
  ai: 'AI-generated insights and recommendation endpoints.',
  videos: 'Video upload, playback, annotation, and analysis endpoints.',
  events: 'Event listing endpoints.',
  tasks: 'Background task submission and status endpoints.',
  websocket: 'WebSocket status helpers.',
};

const METHODS_WITH_BODY = new Set(['post', 'put', 'patch']);
const ROUTE_PATTERN = /router\.(get|post|put|patch|delete)\(\s*['"`]([^'"`]+)['"`]/g;
const METHOD_VERBS = {
  get: 'Get',
  post: 'Submit',
  put: 'Update',
  patch: 'Patch',
  delete: 'Delete',
};

let cachedGeneratedPaths;

function buildGatewayOpenApiSpec(serverUrl) {
  return {
    openapi: '3.1.0',
    info: {
      title: 'ScoutPro API Gateway',
      version: '2.1.0',
      description: 'Unified HTTP contract for the ScoutPro frontend-facing gateway. Route coverage is generated from the mounted Express routers, while payload schemas remain permissive until endpoint-specific models are tightened.',
      contact: {
        name: 'ScoutPro Platform',
      },
      license: {
        name: 'Proprietary',
      },
    },
    servers: [
      {
        url: serverUrl,
        description: 'Current gateway origin',
      },
    ],
    tags: Object.entries(TAG_DESCRIPTIONS).map(([name, description]) => ({ name, description })),
    paths: mergePathMaps(buildGeneratedPaths(), buildManualPaths()),
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
      schemas: {
        HealthResponse: {
          type: 'object',
          required: ['status', 'service', 'version'],
          properties: {
            status: { type: 'string', example: 'healthy' },
            service: { type: 'string', example: 'api-gateway' },
            version: { type: 'string', example: '2.1.0' },
            mongodb: { type: 'string' },
            websocket: { type: 'string' },
          },
        },
        GatewayRoot: {
          type: 'object',
          required: ['service', 'version', 'endpoints'],
          properties: {
            service: { type: 'string' },
            version: { type: 'string' },
            docs: { type: 'string', example: '/docs' },
            openapi: { type: 'string', example: '/openapi.json' },
            endpoints: {
              type: 'object',
              additionalProperties: { type: 'string' },
            },
          },
        },
        ErrorResponse: {
          type: 'object',
          properties: {
            error: { type: 'string' },
            message: { type: 'string' },
            path: { type: 'string' },
          },
        },
        FlexibleEntity: {
          type: 'object',
          additionalProperties: true,
        },
        FlexiblePayload: {
          description: 'Permissive placeholder schema for endpoints that do not yet have a dedicated response model.',
          oneOf: [
            { $ref: '#/components/schemas/FlexibleEntity' },
            {
              type: 'array',
              items: { $ref: '#/components/schemas/FlexibleEntity' },
            },
            { type: 'string' },
            { type: 'number' },
            { type: 'boolean' },
            { type: 'null' },
          ],
        },
      },
    },
  };
}

function buildManualPaths() {
  return {
    '/': {
      get: {
        tags: ['system'],
        operationId: 'getGatewayRoot',
        summary: 'Gateway metadata',
        responses: {
          '200': {
            description: 'Gateway service metadata',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/GatewayRoot' },
              },
            },
          },
        },
      },
    },
    '/health': {
      get: {
        tags: ['system'],
        operationId: 'getGatewayHealth',
        summary: 'Gateway health',
        responses: {
          '200': {
            description: 'Gateway health status',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/HealthResponse' },
              },
            },
          },
        },
      },
    },
    '/openapi.json': {
      get: {
        tags: ['system'],
        operationId: 'getGatewayOpenApiDocument',
        summary: 'OpenAPI document',
        responses: {
          '200': {
            description: 'Generated OpenAPI specification for the gateway',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/FlexibleEntity' },
              },
            },
          },
        },
      },
    },
    '/docs': {
      get: {
        tags: ['system'],
        operationId: 'getGatewaySwaggerUi',
        summary: 'Swagger UI',
        responses: {
          '200': {
            description: 'Interactive Swagger UI HTML',
            content: {
              'text/html': {
                schema: { type: 'string' },
              },
            },
          },
        },
      },
    },
    '/api/ws/stats': {
      get: {
        tags: ['websocket'],
        operationId: 'getWebsocketStats',
        summary: 'WebSocket stats',
        responses: {
          '200': {
            description: 'WebSocket connection statistics',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/FlexibleEntity' },
              },
            },
          },
        },
      },
    },
  };
}

function buildGeneratedPaths() {
  if (cachedGeneratedPaths) {
    return cachedGeneratedPaths;
  }

  const generatedPaths = {};

  for (const routeModule of ROUTE_MODULES) {
    const routeFilePath = path.join(__dirname, 'routes', routeModule.file);

    let source;
    let matches;
    try {
      source = fs.readFileSync(routeFilePath, 'utf8');
      matches = source.matchAll(ROUTE_PATTERN);
    } catch (error) {
      continue;
    }

    for (const match of matches) {
      const method = match[1];
      const routePath = match[2];
      const fullPath = normalizeExpressPath(routeModule.mountPath, routePath);
      const pathItem = generatedPaths[fullPath] || {};

      if (pathItem[method]) {
        continue;
      }

      generatedPaths[fullPath] = {
        ...pathItem,
        [method]: buildGeneratedOperation(routeModule, method, fullPath),
      };
    }
  }

  cachedGeneratedPaths = generatedPaths;
  return generatedPaths;
}

function buildGeneratedOperation(routeModule, method, fullPath) {
  const operation = {
    tags: [routeModule.tag],
    operationId: buildOperationId(method, fullPath),
    summary: buildSummary(method, fullPath),
    description: `Auto-generated from ${routeModule.file} to keep the published contract aligned with mounted Express routes. Parameters and payload schemas should be tightened as endpoint-specific models become available.`,
    responses: buildGeneratedResponses(method, fullPath),
    'x-generated': true,
    'x-route-source': routeModule.file,
  };

  const parameters = extractPathParameters(fullPath);
  if (parameters.length > 0) {
    operation.parameters = parameters;
  }

  if (METHODS_WITH_BODY.has(method)) {
    operation.requestBody = buildGeneratedRequestBody(fullPath);
  }

  return operation;
}

function buildGeneratedResponses(method, fullPath) {
  const successStatus = method === 'post' && (fullPath === '/api/tasks' || fullPath.endsWith('/generate')) ? '202' : method === 'post' ? '201' : '200';

  return {
    [successStatus]: {
      description: `${METHOD_VERBS[method]} response for ${fullPath}`,
      content: {
        [getResponseContentType(fullPath)]: {
          schema: getResponseSchema(fullPath),
        },
      },
    },
    default: {
      description: 'Error response',
      content: {
        'application/json': {
          schema: { $ref: '#/components/schemas/ErrorResponse' },
        },
      },
    },
  };
}

function buildGeneratedRequestBody(fullPath) {
  if (fullPath.includes('/upload')) {
    return {
      required: true,
      content: {
        'multipart/form-data': {
          schema: {
            type: 'object',
            properties: {
              file: {
                type: 'string',
                format: 'binary',
              },
            },
            additionalProperties: true,
          },
        },
      },
    };
  }

  return {
    required: false,
    content: {
      'application/json': {
        schema: { $ref: '#/components/schemas/FlexibleEntity' },
      },
    },
  };
}

function getResponseContentType(fullPath) {
  if (fullPath.endsWith('/download') || fullPath.endsWith('/stream')) {
    return 'application/octet-stream';
  }

  return 'application/json';
}

function getResponseSchema(fullPath) {
  if (fullPath.endsWith('/download') || fullPath.endsWith('/stream')) {
    return {
      type: 'string',
      format: 'binary',
    };
  }

  return { $ref: '#/components/schemas/FlexiblePayload' };
}

function normalizeExpressPath(mountPath, routePath) {
  const normalizedPath = !routePath || routePath === '/' ? mountPath : `${mountPath}${routePath}`;
  return normalizedPath.replace(/\/+/g, '/').replace(/:(\w+)/g, '{$1}');
}

function extractPathParameters(fullPath) {
  return Array.from(fullPath.matchAll(/\{(\w+)\}/g), ([, name]) => ({
    name,
    in: 'path',
    required: true,
    schema: {
      type: 'string',
    },
  }));
}

function buildSummary(method, fullPath) {
  const summaryTarget = fullPath
    .split('/')
    .filter(Boolean)
    .filter((segment) => segment !== 'api' && segment !== 'v2')
    .map((segment) => segment.replace(/[{}]/g, '').replace(/-/g, ' '))
    .join(' ');

  return `${METHOD_VERBS[method]} ${summaryTarget || 'gateway resource'}`;
}

function buildOperationId(method, fullPath) {
  const tokens = [method].concat(
    fullPath
      .split('/')
      .filter(Boolean)
      .map((segment) => {
        if (segment.startsWith('{') && segment.endsWith('}')) {
          return `by-${segment.slice(1, -1)}`;
        }

        return segment;
      })
      .join('-')
      .replace(/[^a-zA-Z0-9-]+/g, '-')
      .split('-')
      .filter(Boolean)
  );

  return tokens
    .map((token, index) => {
      const lower = token.toLowerCase();
      return index === 0 ? lower : lower.charAt(0).toUpperCase() + lower.slice(1);
    })
    .join('');
}

function mergePathMaps(generatedPaths, manualPaths) {
  const mergedPaths = { ...generatedPaths };

  for (const [pathKey, pathItem] of Object.entries(manualPaths)) {
    mergedPaths[pathKey] = {
      ...(mergedPaths[pathKey] || {}),
      ...pathItem,
    };
  }

  return mergedPaths;
}

function renderSwaggerUiHtml(openApiUrl) {
  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ScoutPro API Gateway Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; background: #0f172a; }
      #swagger-ui { max-width: 1400px; margin: 0 auto; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: '${openApiUrl}',
        dom_id: '#swagger-ui',
        deepLinking: true,
        docExpansion: 'list',
        displayRequestDuration: true,
      });
    </script>
  </body>
</html>`;
}

module.exports = {
  buildGatewayOpenApiSpec,
  renderSwaggerUiHtml,
};
