import React, { useEffect, useState } from 'react';
import { AlertCircle, Flame } from 'lucide-react';
import apiService from '../../services/api';
import PitchOverlay from './PitchOverlay';

interface PrecomputedGrid {
  grid: Record<string, number>;
  cellCounts: Record<string, number>;
  maxIntensity: number;
  totalPoints: number;
}

interface HeatMapProps {
  matchId: string;
  teamId?: string;
  playerId?: string;
  width?: number;
  height?: number;
  title?: string;
  /** Optional pre-fetched grid data from a consolidated endpoint (e.g. /viz). */
  precomputedData?: PrecomputedGrid | null;
}

export const HeatMap: React.FC<HeatMapProps> = ({
  matchId,
  teamId,
  playerId,
  width = 800,
  height = 600,
  title = 'Activity Heatmap',
  precomputedData,
}) => {
  const [gridData, setGridData] = useState<PrecomputedGrid | null>(precomputedData ?? null);
  const [loading, setLoading] = useState(!precomputedData);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCell, setHoveredCell] = useState<string | null>(null);

  useEffect(() => {
    if (precomputedData !== undefined) {
      setGridData(precomputedData);
      setLoading(false);
      return;
    }

    const fetchHeatMap = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiService.getMatchHeatMap(matchId, teamId, playerId);
        if (response.success && response.data) {
          const raw = (response.data as any)?.data ?? response.data;
          // Accept either a pre-computed grid { grid, cellCounts, maxIntensity } or a legacy point array
          if (raw && typeof raw === 'object' && !Array.isArray(raw) && raw.grid) {
            setGridData(raw as PrecomputedGrid);
          } else {
            // Legacy fallback: compute grid from raw points on the frontend
            const points: { x: number; y: number; intensity?: number }[] = Array.isArray(raw) ? raw : raw?.heatmap || [];
            const GRID = 10;
            const grid: Record<string, number> = {};
            const cellCounts: Record<string, number> = {};
            for (const pt of points) {
              const cx = Math.min(Math.floor((pt.x / 100) * GRID), GRID - 1);
              const cy = Math.min(Math.floor((pt.y / 100) * GRID), GRID - 1);
              const key = `${cx},${cy}`;
              grid[key] = (grid[key] || 0) + (pt.intensity || 1);
              cellCounts[key] = (cellCounts[key] || 0) + 1;
            }
            const maxIntensity = Math.max(...Object.values(grid), 1);
            setGridData({ grid, cellCounts, maxIntensity, totalPoints: points.length });
          }
        } else {
          throw new Error(response.error?.message || 'Failed to load heat map');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading heat map');
      } finally {
        setLoading(false);
      }
    };

    if (matchId) fetchHeatMap();
  }, [matchId, teamId, playerId, precomputedData]);

  const heatmapGrid = gridData ?? { grid: {}, cellCounts: {}, maxIntensity: 1, totalPoints: 0 };
  const maxIntensity = heatmapGrid.maxIntensity;

  const getHeatColor = (intensity: number): string => {
    const normalized = intensity / maxIntensity;

    // Color gradient: blue -> cyan -> green -> yellow -> orange -> red
    if (normalized < 0.2) return '#1e3a8a'; // blue
    if (normalized < 0.4) return '#0891b2'; // cyan
    if (normalized < 0.6) return '#16a34a'; // green
    if (normalized < 0.8) return '#eab308'; // yellow
    if (normalized < 0.9) return '#f97316'; // orange
    return '#dc2626'; // red
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
        <div className="text-gray-400 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Loading heatmap...
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

  if (Object.keys(heatmapGrid.grid).length === 0) {
    return (
      <div className="flex items-center justify-center bg-slate-800 rounded-lg border border-slate-700" style={{ height: `${height / 2}px` }}>
        <div className="text-center text-slate-400">
          <Flame size={32} className="mx-auto mb-2 opacity-40" />
          <p>No activity data available for this match</p>
        </div>
      </div>
    );
  }

  const config = { width, height, padding: 20 };
  const cellWidth = (config.width - config.padding * 2) / 10;
  const cellHeight = (config.height - config.padding * 2) / 10;

  return (
    <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Flame size={20} />
          {title}
        </h3>
        <span className="text-sm text-slate-400">{heatmapGrid.totalPoints} events</span>
      </div>

      <div className="overflow-x-auto">
        <PitchOverlay config={config}>
          {/* Heatmap cells */}
          {Object.entries(heatmapGrid.grid).map(([cellKey, intensity]) => {
            const [cellX, cellY] = cellKey.split(',').map(Number);
            const x = config.padding + cellX * cellWidth;
            const y = config.padding + cellY * cellHeight;

            const isHovered = hoveredCell === cellKey;

            return (
              <rect
                key={cellKey}
                x={x}
                y={y}
                width={cellWidth}
                height={cellHeight}
                fill={getHeatColor(intensity)}
                opacity={isHovered ? 0.8 : 0.6}
                stroke={isHovered ? '#ffffff' : 'none'}
                strokeWidth={isHovered ? 2 : 0}
                style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                onMouseEnter={() => setHoveredCell(cellKey)}
                onMouseLeave={() => setHoveredCell(null)}
              />
            );
          })}
        </PitchOverlay>
      </div>

      {/* Legend */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm text-slate-400">Intensity:</span>
        </div>
        <div className="flex gap-2 items-center">
          <div className="w-6 h-6 bg-blue-900" />
          <div className="w-6 h-6 bg-cyan-600" />
          <div className="w-6 h-6 bg-green-600" />
          <div className="w-6 h-6 bg-yellow-500" />
          <div className="w-6 h-6 bg-orange-500" />
          <div className="w-6 h-6 bg-red-600" />
          <span className="text-sm text-slate-400 ml-2">Cold → Hot</span>
        </div>
      </div>

      {/* Cell details on hover */}
      {hoveredCell && (
        <div className="mt-4 bg-slate-800 rounded p-3 border border-slate-700">
          <div className="text-sm text-slate-300">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Cell:</span>
              <span className="text-white font-mono">{hoveredCell}</span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-slate-500">Events:</span>
              <span className="text-white">{heatmapGrid.cellCounts[hoveredCell] || 0}</span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-slate-500">Intensity:</span>
              <span className="text-white font-mono">{(heatmapGrid.grid[hoveredCell] || 0).toFixed(1)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HeatMap;
