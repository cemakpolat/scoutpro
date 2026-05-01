#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import socket
import ssl
import struct
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


DEFAULT_GATEWAY_URL = os.environ.get('SCOUTPRO_GATEWAY_URL', 'http://localhost:3001')
DEFAULT_LIVE_INGESTION_URL = os.environ.get('SCOUTPRO_LIVE_INGESTION_URL', 'http://localhost:28006')
DEFAULT_WEBSOCKET_SERVICE_URL = os.environ.get('SCOUTPRO_WEBSOCKET_SERVICE_URL', 'http://localhost:28080')
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get('SCOUTPRO_SMOKE_TIMEOUT', '10'))
DEFAULT_WAIT_SECONDS = int(os.environ.get('SCOUTPRO_SMOKE_WAIT_SECONDS', '180'))
DEFAULT_SMOKE_EMAIL = os.environ.get('SCOUTPRO_SMOKE_EMAIL', 'admin-smoke@scoutpro.dev')
DEFAULT_SMOKE_PASSWORD = os.environ.get('SCOUTPRO_SMOKE_PASSWORD', 'scoutpro123!')


class SmokeFailure(RuntimeError):
    pass


@dataclass
class HttpResponse:
    status: int
    body: bytes
    content_type: str

    def json(self) -> Any:
        return json.loads(self.body.decode('utf-8'))

    def text(self) -> str:
        return self.body.decode('utf-8', errors='replace')


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


@dataclass
class RouteCheck:
    name: str
    method: str
    path: str
    body: dict[str, Any] | None = None
    headers: dict[str, str] | None = None
    validator: Callable[[HttpResponse], str] | None = None


def info(message: str) -> None:
    print(message, flush=True)


def request_json_response(
    base_url: str,
    path: str,
    method: str = 'GET',
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> HttpResponse:
    request_headers = {'Accept': 'application/json'}
    if headers:
      request_headers.update(headers)

    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        request_headers['Content-Type'] = 'application/json'

    request = Request(urljoin(base_url.rstrip('/') + '/', path.lstrip('/')), data=data, headers=request_headers, method=method)

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return HttpResponse(
                status=response.status,
                body=response.read(),
                content_type=response.headers.get('Content-Type', ''),
            )
    except HTTPError as error:
        return HttpResponse(
            status=error.code,
            body=error.read(),
            content_type=error.headers.get('Content-Type', ''),
        )
    except URLError as error:
        raise SmokeFailure(f'{method} {path} failed: {error}') from error


def expect_status(response: HttpResponse, expected: set[int], label: str) -> None:
    if response.status not in expected:
        body = response.text().strip()
        raise SmokeFailure(f'{label} returned {response.status}: {body[:300]}')


def wait_for_health(base_url: str, path: str = '/health', wait_seconds: int = DEFAULT_WAIT_SECONDS) -> None:
    deadline = time.time() + wait_seconds
    last_error = 'service did not respond'

    while time.time() < deadline:
        try:
            response = request_json_response(base_url, path)
            if response.status == 200:
                payload = response.json()
                if isinstance(payload, dict) and payload.get('status') == 'healthy':
                    info(f'wait: {base_url}{path} is healthy')
                    return
                last_error = f'unexpected health payload: {payload}'
            else:
                last_error = f'HTTP {response.status}'
        except (SmokeFailure, json.JSONDecodeError) as error:
            last_error = str(error)

        time.sleep(2)

    raise SmokeFailure(f'timed out waiting for {base_url}{path}: {last_error}')


def require_json_object(response: HttpResponse, label: str) -> dict[str, Any]:
    expect_status(response, {200, 201}, label)
    payload = response.json()
    if not isinstance(payload, dict):
        raise SmokeFailure(f'{label} returned non-object JSON: {payload!r}')
    return payload


def require_json_array(response: HttpResponse, label: str) -> list[Any]:
    expect_status(response, {200}, label)
    payload = response.json()
    if not isinstance(payload, list):
        raise SmokeFailure(f'{label} returned non-array JSON: {payload!r}')
    return payload


def validate_health(response: HttpResponse) -> str:
    payload = require_json_object(response, 'health')
    if payload.get('status') != 'healthy':
        raise SmokeFailure(f'health payload did not report healthy: {payload}')
    return payload.get('service', 'healthy')


def validate_auth_login(response: HttpResponse) -> str:
    payload = require_json_object(response, 'auth login')
    token = payload.get('token')
    user = payload.get('user') or {}
    if not token or not isinstance(user, dict):
        raise SmokeFailure(f'auth login did not return token and user: {payload}')
    return user.get('email', 'token issued')


def validate_auth_me(response: HttpResponse) -> str:
    payload = require_json_object(response, 'auth me')
    if not payload.get('email'):
        raise SmokeFailure(f'auth me did not return email: {payload}')
    return payload['email']


def validate_overview(response: HttpResponse) -> str:
    payload = require_json_object(response, 'analytics overview')
    summary = payload.get('summary') or payload
    total_players = summary.get('totalPlayers')
    return f'totalPlayers={total_players}'


def validate_array_length(label: str) -> Callable[[HttpResponse], str]:
    def _validator(response: HttpResponse) -> str:
        items = require_json_array(response, label)
        return f'items={len(items)}'

    return _validator


def validate_object_keys(label: str, required_keys: list[str]) -> Callable[[HttpResponse], str]:
    def _validator(response: HttpResponse) -> str:
        payload = require_json_object(response, label)
        missing = [key for key in required_keys if key not in payload]
        if missing:
            raise SmokeFailure(f'{label} missing keys {missing}: {payload}')
        return ','.join(required_keys)

    return _validator


def validate_search(response: HttpResponse) -> str:
    payload = require_json_object(response, 'search')
    categories = [key for key in ('players', 'teams', 'matches', 'results') if key in payload]
    if not categories:
        raise SmokeFailure(f'search payload missing expected categories: {payload}')
    return ','.join(categories)


def validate_statistics(response: HttpResponse) -> str:
    payload = response.json()
    if isinstance(payload, list):
        return f'items={len(payload)}'
    if isinstance(payload, dict):
        if 'rankings' in payload and isinstance(payload['rankings'], list):
            return f'rankings={len(payload["rankings"])}'
        return ','.join(sorted(payload.keys())[:4])
    raise SmokeFailure(f'statistics returned unexpected payload: {payload!r}')


def validate_market(response: HttpResponse) -> str:
    payload = response.json()
    if isinstance(payload, list):
        return f'trends={len(payload)}'
    if isinstance(payload, dict) and 'data' in payload:
        return f'data={len(payload["data"])}'
    raise SmokeFailure(f'market trends returned unexpected payload: {payload!r}')


def validate_tactical(response: HttpResponse) -> str:
    payload = require_json_object(response, 'tactical overview')
    keys = [key for key in ('formation', 'teamStats', 'sequenceInsights', 'stats') if key in payload]
    if not keys:
        raise SmokeFailure(f'tactical overview missing expected keys: {payload}')
    return ','.join(keys)


def validate_ai(response: HttpResponse) -> str:
    payload = response.json()
    if isinstance(payload, list):
        return f'insights={len(payload)}'
    if isinstance(payload, dict):
        return ','.join(sorted(payload.keys())[:4])
    raise SmokeFailure(f'ai insights returned unexpected payload: {payload!r}')


def validate_videos(response: HttpResponse) -> str:
    payload = response.json()
    if isinstance(payload, list):
        return f'videos={len(payload)}'
    if isinstance(payload, dict) and 'items' in payload:
        return f'videos={len(payload["items"])}'
    raise SmokeFailure(f'videos list returned unexpected payload: {payload!r}')


def validate_ws_stats(response: HttpResponse) -> str:
    payload = require_json_object(response, 'websocket stats')
    if 'connectedClients' not in payload:
        raise SmokeFailure(f'websocket stats missing connectedClients: {payload}')
    return f'connectedClients={payload["connectedClients"]}'


def run_route_checks(base_url: str, token: str) -> list[CheckResult]:
    auth_headers = {'Authorization': f'Bearer {token}'}
    checks = [
        RouteCheck('gateway_health', 'GET', '/health', validator=validate_health),
        RouteCheck('auth_me', 'GET', '/api/auth/me', headers=auth_headers, validator=validate_auth_me),
        RouteCheck('players_list', 'GET', '/api/players?limit=1', validator=validate_array_length('players list')),
        RouteCheck('matches_live', 'GET', '/api/matches/live', validator=validate_array_length('live matches')),
        RouteCheck('teams_list', 'GET', '/api/teams', validator=validate_array_length('teams list')),
        RouteCheck('analytics_legacy_overview', 'GET', '/api/analytics/overview', validator=validate_object_keys('legacy analytics', ['totalPlayers', 'topPlayers'])),
        RouteCheck('statistics_player_rankings', 'GET', '/api/statistics/rankings/players?stat_name=goals&limit=3', validator=validate_statistics),
        RouteCheck('notifications_list', 'GET', '/api/notifications', validator=validate_array_length('notifications list')),
        RouteCheck('ml_algorithms', 'GET', '/api/ml/algorithms', validator=validate_array_length('ml algorithms')),
        RouteCheck('search_global', 'GET', '/api/search?q=Tarik&limit=3', validator=validate_search),
        RouteCheck('reports_list', 'GET', '/api/v2/reports/list', validator=validate_array_length('reports list')),
        RouteCheck('exports_templates_players', 'GET', '/api/v2/exports/templates/players', validator=validate_object_keys('exports templates', ['columns', 'formats'])),
        RouteCheck('imports_templates', 'GET', '/api/v2/imports/templates', validator=validate_array_length('imports templates')),
        RouteCheck('calendar_snapshot', 'GET', '/api/v2/calendar', validator=validate_object_keys('calendar snapshot', ['events', 'trips', 'matches'])),
        RouteCheck('collaboration_snapshot', 'GET', '/api/v2/collaboration', validator=validate_object_keys('collaboration snapshot', ['workspaces', 'tasks', 'activities'])),
        RouteCheck('admin_snapshot', 'GET', '/api/v2/admin/snapshot', validator=validate_object_keys('admin snapshot', ['systemHealth', 'auditLogs'])),
        RouteCheck('leagues_list', 'GET', '/api/leagues', validator=validate_array_length('leagues list')),
        RouteCheck('market_trends', 'GET', '/api/market/trends', validator=validate_market),
        RouteCheck('tactical_overview', 'GET', '/api/tactical/overview', validator=validate_tactical),
        RouteCheck('ai_insights_all', 'GET', '/api/ai/insights/all', validator=validate_ai),
        RouteCheck('videos_list', 'GET', '/api/v2/videos', validator=validate_videos),
        RouteCheck('advanced_analytics_overview', 'GET', '/api/v2/analytics/dashboard/overview', validator=validate_overview),
        RouteCheck('gateway_websocket_stats', 'GET', '/api/ws/stats', validator=validate_ws_stats),
    ]

    results: list[CheckResult] = []

    for check in checks:
        response = request_json_response(
            base_url,
            check.path,
            method=check.method,
            body=check.body,
            headers=check.headers,
        )
        expect_status(response, {200, 201}, check.name)
        detail = check.validator(response) if check.validator else f'HTTP {response.status}'
        results.append(CheckResult(check.name, True, detail))
        info(f'PASS {check.name}: {detail}')

    return results


def open_websocket(parsed_base: Any, path: str) -> socket.socket:
    host = parsed_base.hostname or 'localhost'
    secure = parsed_base.scheme == 'https'
    port = parsed_base.port or (443 if secure else 80)
    raw_socket = socket.create_connection((host, port), timeout=DEFAULT_TIMEOUT_SECONDS)

    if secure:
        context = ssl.create_default_context()
        raw_socket = context.wrap_socket(raw_socket, server_hostname=host)

    raw_socket.settimeout(DEFAULT_TIMEOUT_SECONDS)

    key = base64.b64encode(secrets.token_bytes(16)).decode('ascii')
    request = (
        f'GET {path} HTTP/1.1\r\n'
        f'Host: {host}:{port}\r\n'
        'Upgrade: websocket\r\n'
        'Connection: Upgrade\r\n'
        f'Sec-WebSocket-Key: {key}\r\n'
        'Sec-WebSocket-Version: 13\r\n'
        '\r\n'
    )
    raw_socket.sendall(request.encode('ascii'))

    response = b''
    while b'\r\n\r\n' not in response:
        chunk = raw_socket.recv(4096)
        if not chunk:
            raise SmokeFailure(f'websocket handshake closed unexpectedly for {path}')
        response += chunk

    header_text = response.split(b'\r\n\r\n', 1)[0].decode('ascii', errors='replace')
    if '101' not in header_text.splitlines()[0]:
        raise SmokeFailure(f'websocket handshake failed for {path}: {header_text}')

    return raw_socket


def read_ws_frame(raw_socket: socket.socket) -> str:
    header = raw_socket.recv(2)
    if len(header) < 2:
        raise SmokeFailure('websocket frame header truncated')

    first_byte, second_byte = header
    opcode = first_byte & 0x0F
    masked = (second_byte & 0x80) != 0
    payload_length = second_byte & 0x7F

    if payload_length == 126:
        payload_length = struct.unpack('!H', raw_socket.recv(2))[0]
    elif payload_length == 127:
        payload_length = struct.unpack('!Q', raw_socket.recv(8))[0]

    masking_key = raw_socket.recv(4) if masked else b''
    payload = b''
    while len(payload) < payload_length:
        chunk = raw_socket.recv(payload_length - len(payload))
        if not chunk:
            raise SmokeFailure('websocket payload truncated')
        payload += chunk

    if masked:
        payload = bytes(byte ^ masking_key[index % 4] for index, byte in enumerate(payload))

    if opcode == 0x8:
        raise SmokeFailure('websocket closed unexpectedly')
    if opcode != 0x1:
        raise SmokeFailure(f'unexpected websocket opcode {opcode}')

    return payload.decode('utf-8', errors='replace')


def send_ws_text(raw_socket: socket.socket, payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload).encode('utf-8')
    mask_key = secrets.token_bytes(4)
    masked_payload = bytes(byte ^ mask_key[index % 4] for index, byte in enumerate(encoded))
    header = bytearray([0x81])
    length = len(encoded)

    if length < 126:
        header.append(0x80 | length)
    elif length < (1 << 16):
        header.append(0x80 | 126)
        header.extend(struct.pack('!H', length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack('!Q', length))

    raw_socket.sendall(bytes(header) + mask_key + masked_payload)


def validate_gateway_websocket(base_url: str) -> CheckResult:
    parsed = urlparse(base_url)
    raw_socket = open_websocket(parsed, '/ws')

    try:
        welcome = json.loads(read_ws_frame(raw_socket))
        if welcome.get('type') != 'connected':
            raise SmokeFailure(f'gateway websocket did not send connected message: {welcome}')

        send_ws_text(raw_socket, {'type': 'ping'})
        pong = json.loads(read_ws_frame(raw_socket))
        if pong.get('type') != 'pong':
            raise SmokeFailure(f'gateway websocket did not respond with pong: {pong}')

        send_ws_text(raw_socket, {'type': 'subscribe', 'channel': 'match'})
        subscription = json.loads(read_ws_frame(raw_socket))
        if subscription.get('type') != 'subscribed':
            raise SmokeFailure(f'gateway websocket did not confirm subscription: {subscription}')

        detail = f'clientId={welcome.get("data", {}).get("clientId", "unknown")}'
        info(f'PASS gateway_websocket_flow: {detail}')
        return CheckResult('gateway_websocket_flow', True, detail)
    finally:
        raw_socket.close()


def validate_internal_websocket_service(service_url: str) -> CheckResult:
    parsed = urlparse(service_url)
    raw_socket = open_websocket(parsed, '/ws')

    try:
        send_ws_text(raw_socket, {'type': 'ping'})
        pong = json.loads(read_ws_frame(raw_socket))
        if pong.get('type') != 'pong':
            raise SmokeFailure(f'internal websocket service did not respond with pong: {pong}')

        send_ws_text(raw_socket, {'type': 'subscribe', 'topic': 'match.updates'})
        subscription = json.loads(read_ws_frame(raw_socket))
        if subscription.get('type') != 'subscription_confirmed':
            raise SmokeFailure(f'internal websocket service did not confirm subscription: {subscription}')

        detail = subscription.get('topic', 'match.updates')
        info(f'PASS websocket_service_flow: {detail}')
        return CheckResult('websocket_service_flow', True, detail)
    finally:
        raw_socket.close()


def resolve_compose_command(repo_root: Path) -> list[str]:
    candidates = [
        ['docker', 'compose'],
        ['docker-compose'],
    ]

    for candidate in candidates:
        result = subprocess.run(
            [*candidate, 'version'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode == 0:
            return candidate

    raise SmokeFailure('No docker compose command is available on PATH')


def validate_data_sync_cli(repo_root: Path) -> CheckResult:
    compose_command = resolve_compose_command(repo_root)
    command = [*compose_command, 'exec', '-T', 'data-sync-service', 'python', 'main.py', '--help']
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=max(DEFAULT_TIMEOUT_SECONDS, 20),
        check=False,
    )

    if result.returncode != 0:
        raise SmokeFailure(f'data-sync CLI failed with {result.returncode}: {result.stderr.strip()}')

    stdout = result.stdout.strip()
    if '--once' not in stdout or '--job' not in stdout:
        raise SmokeFailure(f'data-sync CLI help output missing expected flags: {stdout}')

    info('PASS data_sync_cli: help output includes expected flags')
    return CheckResult('data_sync_cli', True, 'help flags present')


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='ScoutPro gateway and service smoke suite')
    parser.add_argument('--gateway-url', default=DEFAULT_GATEWAY_URL)
    parser.add_argument('--live-ingestion-url', default=DEFAULT_LIVE_INGESTION_URL)
    parser.add_argument('--websocket-service-url', default=DEFAULT_WEBSOCKET_SERVICE_URL)
    parser.add_argument('--wait-seconds', type=int, default=DEFAULT_WAIT_SECONDS)
    parser.add_argument('--repo-root', default=str(Path(__file__).resolve().parents[1]))
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []

    try:
        wait_for_health(args.gateway_url, '/health', args.wait_seconds)
        wait_for_health(args.live_ingestion_url, '/health', args.wait_seconds)
        wait_for_health(args.websocket_service_url, '/health', args.wait_seconds)

        login_response = request_json_response(
            args.gateway_url,
            '/api/auth/login',
            method='POST',
            body={'email': DEFAULT_SMOKE_EMAIL, 'password': DEFAULT_SMOKE_PASSWORD},
        )
        token_payload = require_json_object(login_response, 'auth login')
        token = token_payload.get('token')
        if not token:
            raise SmokeFailure(f'auth login did not return a token: {token_payload}')
        info(f'PASS auth_login: {token_payload.get("user", {}).get("email", DEFAULT_SMOKE_EMAIL)}')

        run_route_checks(args.gateway_url, token)
        validate_gateway_websocket(args.gateway_url)
        internal_health = request_json_response(args.websocket_service_url, '/health')
        validate_health(internal_health)
        info(f'PASS websocket_service_health: {args.websocket_service_url}/health')
        validate_internal_websocket_service(args.websocket_service_url)
        validate_data_sync_cli(repo_root)

        info('All ScoutPro smoke checks passed.')
        return 0
    except SmokeFailure as error:
        failures.append(str(error))
    except (json.JSONDecodeError, TimeoutError, subprocess.TimeoutExpired) as error:
        failures.append(str(error))

    for failure in failures:
        info(f'FAIL {failure}')

    return 1


if __name__ == '__main__':
    sys.exit(main())