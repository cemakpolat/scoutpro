function buildGatewayOpenApiSpec(serverUrl) {
  return {
    openapi: '3.1.0',
    info: {
      title: 'ScoutPro API Gateway',
      version: '2.1.0',
      description: 'Unified HTTP contract for ScoutPro frontend-facing gateway endpoints.',
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
    tags: [
      { name: 'system', description: 'Gateway metadata and health endpoints.' },
      { name: 'players', description: 'Player list and detail endpoints aggregated by the gateway.' },
      { name: 'matches', description: 'Match list and detail endpoints aggregated by the gateway.' },
      { name: 'teams', description: 'Team list and detail endpoints aggregated by the gateway.' },
      { name: 'analytics', description: 'Legacy and v2 analytics routes exposed to the frontend.' },
      { name: 'statistics', description: 'Statistics-service projections exposed via the gateway.' },
      { name: 'tasks', description: 'Background task submission and tracking endpoints.' },
      { name: 'websocket', description: 'WebSocket status helpers.' },
    ],
    paths: {
      '/': {
        get: {
          tags: ['system'],
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
      '/api/players': {
        get: {
          tags: ['players'],
          summary: 'List players',
          parameters: [
            { name: 'search', in: 'query', schema: { type: 'string' } },
            { name: 'q', in: 'query', schema: { type: 'string' } },
            { name: 'position', in: 'query', schema: { type: 'string' } },
            { name: 'nationality', in: 'query', schema: { type: 'string' } },
            { name: 'club', in: 'query', schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer', minimum: 1, maximum: 500, default: 100 } },
          ],
          responses: {
            '200': {
              description: 'Player list',
              content: {
                'application/json': {
                  schema: {
                    type: 'array',
                    items: { $ref: '#/components/schemas/FlexibleEntity' },
                  },
                },
              },
            },
          },
        },
      },
      '/api/players/{id}': {
        get: {
          tags: ['players'],
          summary: 'Get player detail',
          parameters: [
            { name: 'id', in: 'path', required: true, schema: { type: 'string' } },
          ],
          responses: {
            '200': {
              description: 'Player detail',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
            '404': {
              description: 'Player not found',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/ErrorResponse' },
                },
              },
            },
          },
        },
      },
      '/api/matches': {
        get: {
          tags: ['matches'],
          summary: 'List matches',
          parameters: [
            { name: 'limit', in: 'query', schema: { type: 'integer', minimum: 1, maximum: 500, default: 100 } },
            { name: 'status', in: 'query', schema: { type: 'string' } },
            { name: 'competition_id', in: 'query', schema: { type: 'string' } },
            { name: 'season_id', in: 'query', schema: { type: 'string' } },
          ],
          responses: {
            '200': {
              description: 'Match list',
              content: {
                'application/json': {
                  schema: {
                    type: 'array',
                    items: { $ref: '#/components/schemas/FlexibleEntity' },
                  },
                },
              },
            },
          },
        },
      },
      '/api/teams': {
        get: {
          tags: ['teams'],
          summary: 'List teams',
          responses: {
            '200': {
              description: 'Team list',
              content: {
                'application/json': {
                  schema: {
                    type: 'array',
                    items: { $ref: '#/components/schemas/FlexibleEntity' },
                  },
                },
              },
            },
          },
        },
      },
      '/api/analytics/{type}': {
        get: {
          tags: ['analytics'],
          summary: 'Legacy analytics overview routes',
          parameters: [
            {
              name: 'type',
              in: 'path',
              required: true,
              schema: {
                type: 'string',
                enum: ['overview', 'dashboard', 'top-performers'],
              },
            },
          ],
          responses: {
            '200': {
              description: 'Legacy analytics payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/analytics/player/{playerId}': {
        get: {
          tags: ['analytics'],
          summary: 'Legacy player analytics',
          parameters: [
            { name: 'playerId', in: 'path', required: true, schema: { type: 'string' } },
          ],
          responses: {
            '200': {
              description: 'Player analytics payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/analytics/match/{matchId}': {
        get: {
          tags: ['analytics'],
          summary: 'Legacy match analytics',
          parameters: [
            { name: 'matchId', in: 'path', required: true, schema: { type: 'string' } },
          ],
          responses: {
            '200': {
              description: 'Match analytics payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/v2/analytics/dashboard/overview': {
        get: {
          tags: ['analytics'],
          summary: 'Overview dashboard',
          responses: {
            '200': {
              description: 'Analytics overview dashboard payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/v2/analytics/dashboard/player/{player_id}': {
        get: {
          tags: ['analytics'],
          summary: 'Player dashboard',
          parameters: [
            { name: 'player_id', in: 'path', required: true, schema: { type: 'string' } },
          ],
          responses: {
            '200': {
              description: 'Player dashboard payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/v2/analytics/dashboard/team/{team_id}': {
        get: {
          tags: ['analytics'],
          summary: 'Team dashboard',
          parameters: [
            { name: 'team_id', in: 'path', required: true, schema: { type: 'string' } },
          ],
          responses: {
            '200': {
              description: 'Team dashboard payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/v2/analytics/advanced-metrics/{match_id}': {
        get: {
          tags: ['analytics'],
          summary: 'Match advanced metrics',
          parameters: [
            { name: 'match_id', in: 'path', required: true, schema: { type: 'string' } },
            { name: 'time_bucket', in: 'query', schema: { type: 'string', default: '5m' } },
          ],
          responses: {
            '200': {
              description: 'Advanced match metrics payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/statistics/player/{playerId}': {
        get: {
          tags: ['statistics'],
          summary: 'Player statistics',
          parameters: [
            { name: 'playerId', in: 'path', required: true, schema: { type: 'string' } },
            { name: 'competition_id', in: 'query', schema: { type: 'string' } },
            { name: 'season_id', in: 'query', schema: { type: 'string' } },
            { name: 'per_90', in: 'query', schema: { type: 'boolean' } },
          ],
          responses: {
            '200': {
              description: 'Player statistics payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/statistics/team/{teamId}': {
        get: {
          tags: ['statistics'],
          summary: 'Team statistics',
          parameters: [
            { name: 'teamId', in: 'path', required: true, schema: { type: 'string' } },
            { name: 'competition_id', in: 'query', schema: { type: 'string' } },
            { name: 'season_id', in: 'query', schema: { type: 'string' } },
          ],
          responses: {
            '200': {
              description: 'Team statistics payload',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/statistics/rankings/players': {
        get: {
          tags: ['statistics'],
          summary: 'Player rankings',
          parameters: [
            { name: 'stat_name', in: 'query', schema: { type: 'string', default: 'passes' } },
            { name: 'position', in: 'query', schema: { type: 'string' } },
            { name: 'competition_id', in: 'query', schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer', default: 50 } },
          ],
          responses: {
            '200': {
              description: 'Player rankings payload',
              content: {
                'application/json': {
                  schema: {
                    type: 'array',
                    items: { $ref: '#/components/schemas/FlexibleEntity' },
                  },
                },
              },
            },
          },
        },
      },
      '/api/statistics/rankings/teams': {
        get: {
          tags: ['statistics'],
          summary: 'Team rankings',
          parameters: [
            { name: 'stat_name', in: 'query', schema: { type: 'string', default: 'goals' } },
            { name: 'competition_id', in: 'query', schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer', default: 50 } },
          ],
          responses: {
            '200': {
              description: 'Team rankings payload',
              content: {
                'application/json': {
                  schema: {
                    type: 'array',
                    items: { $ref: '#/components/schemas/FlexibleEntity' },
                  },
                },
              },
            },
          },
        },
      },
      '/api/tasks': {
        get: {
          tags: ['tasks'],
          summary: 'List tasks',
          parameters: [
            { name: 'limit', in: 'query', schema: { type: 'integer', default: 50 } },
          ],
          responses: {
            '200': {
              description: 'Recent background tasks',
              content: {
                'application/json': {
                  schema: {
                    type: 'array',
                    items: { $ref: '#/components/schemas/FlexibleEntity' },
                  },
                },
              },
            },
          },
        },
        post: {
          tags: ['tasks'],
          summary: 'Submit task',
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['task_type', 'payload'],
                  properties: {
                    task_type: { type: 'string' },
                    payload: { type: 'object', additionalProperties: true },
                  },
                },
              },
            },
          },
          responses: {
            '202': {
              description: 'Task accepted',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/FlexibleEntity' },
                },
              },
            },
          },
        },
      },
      '/api/ws/stats': {
        get: {
          tags: ['websocket'],
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
    },
    components: {
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
      },
    },
  };
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