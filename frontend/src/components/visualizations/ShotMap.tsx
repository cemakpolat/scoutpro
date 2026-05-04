import React, { useEffect, useState } from 'react';
import { AlertCircle, Target } from 'lucide-react';
import apiService from '../../services/api';
import PitchOverlay from './PitchOverlay';

interface ShotEvent {
  id: string;
  player_id: string;
  player_name: string;
  x: number;
  y: number;
  is_goal: boolean;
  xg?: number;
  is_successful?: boolean;
  body_part?: string;
  shot_type?: string;
  timestamp?: string;
}

interface ShotMapProps {
  matchId: string;
  width?: number;
  height?: number;
  onShotClick?: (shot: ShotEvent) => void;
  /** Optional pre-fetched shots from a consolidated endpoint (e.g. /viz). */
  precomputedShots?: ShotEvent[] | null;
}

export const ShotMap: React.FC<ShotMapProps> = ({
  matchId,
  width = 800,
  height = 600,
  onShotClick,
  precomputedShots,
}) => {
  const [shots, setShots] = useState<ShotEvent[]>(precomputedShots ?? []);
  const [loading, setLoading] = useState(!precomputedShots);
  const [error, setError] = useState<string | null>(null);
  const [hoveredShot, setHoveredShot] = useState<string | null>(null);

  useEffect(() => {
    if (precomputedShots !== undefined) {
      setShots(precomputedShots ?? []);
      setLoading(false);
      return;
    }

    const fetchShotMap = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiService.getMatchShotMap(matchId);
        if (response.success && response.data) {
          const raw = (response.data as any)?.data ?? response.data;
          const shotData = Array.isArray(raw) ? raw : raw?.shots || [];
          setShots(shotData);
        } else {
          throw new Error(response.error?.message || 'Failed to load shot map');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading shots');
      } finally {
        setLoading(false);
      }
    };

    if (matchId) fetchShotMap();
  }, [matchId, precomputedShots]);

  const handleShotClick = (shot: ShotEvent) => {
    if (onShotClick) {
      onShotClick(shot);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
        <div className="text-gray-400 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Loading shot map...
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

  const config = { width, height, padding: 20 };
  const maxXG = Math.max(...shots.map(s => s.xg || 0.1), 0.5);

  if (shots.length === 0) {
    return (
      <div className="flex items-center justify-center bg-slate-800 rounded-lg border border-slate-700" style={{ height: `${height / 2}px` }}>
        <div className="text-center text-slate-400">
          <Target size={32} className="mx-auto mb-2 opacity-40" />
          <p>No shot data available for this match</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Target size={20} />
          Shot Map
        </h3>
        <span className="text-sm text-slate-400">{shots.length} shots</span>
      </div>

      <div className="overflow-x-auto">
        <PitchOverlay config={config}>
          {/* Shot markers */}
          {shots.map((shot) => {
            // Normalize coordinates to 0-100 range if they're in pixel space
            const x = shot.x > 1 ? (shot.x / 100) : shot.x;
            const y = shot.y > 1 ? (shot.y / 100) : shot.y;

            const pixelX = config.padding + (x * (config.width - config.padding * 2));
            const pixelY = config.padding + (y * (config.height - config.padding * 2));

            // Size proportional to xG
            const radius = Math.max(6, Math.min(16, (shot.xg || 0.3) * 20));
            const isGoal = shot.is_goal || shot.is_successful;
            const fillColor = isGoal ? '#10b981' : '#ef4444'; // Green for goal, red for miss

            return (
              <g key={shot.id}>
                {/* Shot circle */}
                <circle
                  cx={pixelX}
                  cy={pixelY}
                  r={radius}
                  fill={fillColor}
                  opacity={hoveredShot === shot.id ? 0.9 : 0.7}
                  stroke={hoveredShot === shot.id ? '#ffffff' : fillColor}
                  strokeWidth={hoveredShot === shot.id ? 3 : 1}
                  style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                  onClick={() => handleShotClick(shot)}
                  onMouseEnter={() => setHoveredShot(shot.id)}
                  onMouseLeave={() => setHoveredShot(null)}
                />

                {/* xG label on hover */}
                {hoveredShot === shot.id && (
                  <text
                    x={pixelX}
                    y={pixelY}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#ffffff"
                    fontSize="10"
                    fontWeight="bold"
                  >
                    {(shot.xg || 0).toFixed(2)}
                  </text>
                )}
              </g>
            );
          })}
        </PitchOverlay>
      </div>

      {/* Legend */}
      <div className="mt-4 flex gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded-full" />
          <span className="text-slate-300">Goal</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded-full" />
          <span className="text-slate-300">Missed Shot</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-400">● (small)</span>
          <span className="text-slate-300">Low xG</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-400">● (large)</span>
          <span className="text-slate-300">High xG</span>
        </div>
      </div>

      {/* Shot details on hover */}
      {hoveredShot && (
        <div className="mt-4 bg-slate-800 rounded p-3 border border-slate-700">
          {shots
            .filter(s => s.id === hoveredShot)
            .map(shot => (
              <div key={shot.id} className="text-sm text-slate-300">
                <p className="font-semibold text-white">{shot.player_name}</p>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <div>
                    <span className="text-slate-500">xG:</span>
                    <span className="ml-2 text-white font-mono">{(shot.xg || 0).toFixed(3)}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Result:</span>
                    <span className={`ml-2 font-semibold ${shot.is_goal ? 'text-green-400' : 'text-red-400'}`}>
                      {shot.is_goal ? 'GOAL' : 'MISS'}
                    </span>
                  </div>
                  {shot.body_part && (
                    <div>
                      <span className="text-slate-500">Body part:</span>
                      <span className="ml-2 text-white capitalize">{shot.body_part}</span>
                    </div>
                  )}
                  {shot.shot_type && (
                    <div>
                      <span className="text-slate-500">Type:</span>
                      <span className="ml-2 text-white capitalize">{shot.shot_type}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
};

export default ShotMap;
