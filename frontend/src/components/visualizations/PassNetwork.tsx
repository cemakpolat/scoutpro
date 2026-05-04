import React, { useEffect, useState, useMemo } from 'react';
import { AlertCircle, Share2 } from 'lucide-react';
import apiService from '../../services/api';
import PitchOverlay from './PitchOverlay';

interface PlayerNode {
  player_id: string;
  player_name: string;
  x: number;
  y: number;
  touches: number;
  passes: number;
}

interface PassConnection {
  from_player_id: string;
  to_player_id: string;
  passes: number;
  accuracy: number;
}

interface PassMapData {
  players: PlayerNode[];
  connections: PassConnection[];
}

interface PassNetworkProps {
  matchId: string;
  teamId?: string;
  width?: number;
  height?: number;
  /** Optional pre-fetched data from a consolidated endpoint (e.g. /viz). */
  precomputedData?: PassMapData | null;
}

export const PassNetwork: React.FC<PassNetworkProps> = ({
  matchId,
  teamId,
  width = 800,
  height = 600,
  precomputedData,
}) => {
  const [passData, setPassData] = useState<PassMapData | null>(precomputedData ?? null);
  const [loading, setLoading] = useState(!precomputedData);
  const [error, setError] = useState<string | null>(null);
  const [hoveredPlayer, setHoveredPlayer] = useState<string | null>(null);
  const [hoveredConnection, setHoveredConnection] = useState<string | null>(null);

  useEffect(() => {
    if (precomputedData !== undefined) {
      setPassData(precomputedData);
      setLoading(false);
      return;
    }

    const fetchPassMap = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiService.getMatchPassMap(matchId, teamId);
        if (response.success && response.data) {
          const raw = (response.data as any)?.data ?? response.data;
          setPassData({
            players: Array.isArray(raw?.players) ? raw.players : [],
            connections: Array.isArray(raw?.connections) ? raw.connections : [],
          });
        } else {
          throw new Error(response.error?.message || 'Failed to load pass map');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading pass map');
      } finally {
        setLoading(false);
      }
    };

    if (matchId) fetchPassMap();
  }, [matchId, teamId, precomputedData]);

  const maxTouches = useMemo(() => {
    if (!passData?.players?.length) return 1;
    const touches = passData.players.map(p => p.touches);
    return Math.max(...touches, 1);
  }, [passData]);

  const maxPasses = useMemo(() => {
    if (!passData?.connections?.length) return 1;
    const passes = passData.connections.map(c => c.passes);
    return Math.max(...passes, 1);
  }, [passData]);

  const getAccuracyColor = (accuracy: number): string => {
    if (accuracy >= 0.9) return '#10b981'; // green
    if (accuracy >= 0.8) return '#84cc16'; // lime
    if (accuracy >= 0.7) return '#eab308'; // yellow
    if (accuracy >= 0.6) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
        <div className="text-gray-400 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Loading pass network...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center bg-slate-800 rounded-lg p-4" style={{ height: `${height}px` }}>
        <div className="text-red-400 flex items-center gap-2">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!passData || !passData.players?.length) {
    return (
      <div className="flex items-center justify-center bg-slate-800 rounded-lg border border-slate-700" style={{ height: `${height / 2}px` }}>
        <div className="text-center text-slate-400">
          <Share2 size={32} className="mx-auto mb-2 opacity-40" />
          <p>No pass data available for this match</p>
        </div>
      </div>
    );
  }

  const config = { width, height, padding: 20 };

  return (
    <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Share2 size={20} />
          Pass Network
        </h3>
        <span className="text-sm text-slate-400">{passData.players.length} players</span>
      </div>

      <div className="overflow-x-auto">
        <PitchOverlay config={config}>
          {/* Pass connections (lines) */}
          {passData.connections.map((conn, idx) => {
            const fromPlayer = passData.players.find(p => p.player_id === conn.from_player_id);
            const toPlayer = passData.players.find(p => p.player_id === conn.to_player_id);

            if (!fromPlayer || !toPlayer) return null;

            const fromX = config.padding + (fromPlayer.x / 100) * (config.width - config.padding * 2);
            const fromY = config.padding + (fromPlayer.y / 100) * (config.height - config.padding * 2);
            const toX = config.padding + (toPlayer.x / 100) * (config.width - config.padding * 2);
            const toY = config.padding + (toPlayer.y / 100) * (config.height - config.padding * 2);

            const connKey = `${conn.from_player_id}-${conn.to_player_id}`;
            const isHovered = hoveredConnection === connKey || hoveredPlayer === conn.from_player_id || hoveredPlayer === conn.to_player_id;

            const strokeWidth = Math.max(1, Math.min(8, (conn.passes / maxPasses) * 6));

            return (
              <line
                key={connKey}
                x1={fromX}
                y1={fromY}
                x2={toX}
                y2={toY}
                stroke={getAccuracyColor(conn.accuracy)}
                strokeWidth={isHovered ? strokeWidth + 2 : strokeWidth}
                opacity={isHovered ? 1 : 0.6}
                style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                onMouseEnter={() => setHoveredConnection(connKey)}
                onMouseLeave={() => setHoveredConnection(null)}
              />
            );
          })}

          {/* Player nodes */}
          {passData.players.map(player => {
            const pixelX = config.padding + (player.x / 100) * (config.width - config.padding * 2);
            const pixelY = config.padding + (player.y / 100) * (config.height - config.padding * 2);

            const radius = Math.max(8, Math.min(20, (player.touches / maxTouches) * 16));
            const isHovered = hoveredPlayer === player.player_id;

            return (
              <g
                key={player.player_id}
                onMouseEnter={() => setHoveredPlayer(player.player_id)}
                onMouseLeave={() => setHoveredPlayer(null)}
              >
                {/* Player circle */}
                <circle
                  cx={pixelX}
                  cy={pixelY}
                  r={radius}
                  fill="#3b82f6"
                  opacity={isHovered ? 0.9 : 0.7}
                  stroke={isHovered ? '#ffffff' : '#3b82f6'}
                  strokeWidth={isHovered ? 3 : 1}
                  style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                />

                {/* Player number/initial on hover */}
                {isHovered && (
                  <text
                    x={pixelX}
                    y={pixelY}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#ffffff"
                    fontSize="12"
                    fontWeight="bold"
                  >
                    {player.player_name.charAt(0)}
                  </text>
                )}
              </g>
            );
          })}
        </PitchOverlay>
      </div>

      {/* Legend */}
      <div className="mt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-slate-400 mb-2">Node Size (Touches):</div>
            <div className="flex items-center gap-4">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
              <span className="text-xs text-slate-400">Few</span>
              <div className="w-5 h-5 bg-blue-500 rounded-full" />
              <span className="text-xs text-slate-400">Many</span>
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-400 mb-2">Line Width (Passes):</div>
            <div className="flex items-center gap-2">
              <svg width="15" height="8"><line x1="0" y1="4" x2="15" y2="4" stroke="#3b82f6" strokeWidth="1" /></svg>
              <span className="text-xs text-slate-400">Few</span>
              <svg width="15" height="8"><line x1="0" y1="4" x2="15" y2="4" stroke="#3b82f6" strokeWidth="4" /></svg>
              <span className="text-xs text-slate-400">Many</span>
            </div>
          </div>
        </div>

        <div className="mt-3">
          <div className="text-sm text-slate-400 mb-2">Pass Accuracy:</div>
          <div className="flex gap-3">
            <div className="flex items-center gap-1">
              <div className="w-3 h-0.5 bg-green-600" />
              <span className="text-xs text-slate-400">90%+</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-0.5 bg-yellow-500" />
              <span className="text-xs text-slate-400">70%</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-0.5 bg-red-600" />
              <span className="text-xs text-slate-400">&lt;60%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Details on hover */}
      {hoveredPlayer && passData.players.find(p => p.player_id === hoveredPlayer) && (
        <div className="mt-4 bg-slate-800 rounded p-3 border border-slate-700">
          {(() => {
            const player = passData.players.find(p => p.player_id === hoveredPlayer)!;
            const playerConnections = passData.connections.filter(
              c => c.from_player_id === hoveredPlayer || c.to_player_id === hoveredPlayer
            );

            return (
              <div className="text-sm text-slate-300">
                <p className="font-semibold text-white text-base">{player.player_name}</p>
                <div className="grid grid-cols-3 gap-3 mt-2">
                  <div>
                    <span className="text-slate-500">Touches:</span>
                    <span className="ml-2 text-white font-mono">{player.touches}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Passes:</span>
                    <span className="ml-2 text-white font-mono">{player.passes}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Connections:</span>
                    <span className="ml-2 text-white font-mono">{playerConnections.length}</span>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {hoveredConnection && passData.connections.find(c => `${c.from_player_id}-${c.to_player_id}` === hoveredConnection) && (
        <div className="mt-4 bg-slate-800 rounded p-3 border border-slate-700">
          {(() => {
            const conn = passData.connections.find(c => `${c.from_player_id}-${c.to_player_id}` === hoveredConnection)!;
            const fromPlayer = passData.players.find(p => p.player_id === conn.from_player_id)!;
            const toPlayer = passData.players.find(p => p.player_id === conn.to_player_id)!;

            return (
              <div className="text-sm text-slate-300">
                <p className="font-semibold text-white">
                  {fromPlayer.player_name} → {toPlayer.player_name}
                </p>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  <div>
                    <span className="text-slate-500">Passes:</span>
                    <span className="ml-2 text-white font-mono">{conn.passes}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Accuracy:</span>
                    <span className="ml-2 text-white font-mono">{(conn.accuracy * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default PassNetwork;
