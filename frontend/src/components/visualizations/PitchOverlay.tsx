import React, { useMemo } from 'react';

export interface PitchConfig {
  width: number;
  height: number;
  padding: number;
  pitchColor: string;
  lineColor: string;
}

const DEFAULT_CONFIG: PitchConfig = {
  width: 800,
  height: 600,
  padding: 20,
  pitchColor: '#1a5d1a',
  lineColor: '#ffffff',
};

interface PitchOverlayProps {
  config?: Partial<PitchConfig>;
  children?: React.ReactNode;
  onPitchClick?: (x: number, y: number) => void;
}

/**
 * PitchOverlay - Base component for football pitch visualization
 * Provides SVG canvas with football field markings
 * All coordinates are normalized (0-100) and converted to pixel space
 */
export const PitchOverlay: React.FC<PitchOverlayProps> = ({ config: userConfig, children, onPitchClick }) => {
  const config = { ...DEFAULT_CONFIG, ...userConfig };

  const pitchSize = useMemo(
    () => ({
      width: config.width - config.padding * 2,
      height: config.height - config.padding * 2,
    }),
    [config]
  );

  // Convert normalized coordinates (0-100) to pixel coordinates
  const toPixel = (x: number, y: number): [number, number] => [
    config.padding + (x / 100) * pitchSize.width,
    config.padding + (y / 100) * pitchSize.height,
  ];

  const handleClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!onPitchClick) return;

    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Convert pixel to normalized coordinates
    const normX = ((x - config.padding) / pitchSize.width) * 100;
    const normY = ((y - config.padding) / pitchSize.height) * 100;

    onPitchClick(Math.max(0, Math.min(100, normX)), Math.max(0, Math.min(100, normY)));
  };

  return (
    <svg
      width={config.width}
      height={config.height}
      viewBox={`0 0 ${config.width} ${config.height}`}
      className="pitch-overlay"
      style={{ cursor: onPitchClick ? 'crosshair' : 'default' }}
      onClick={handleClick}
    >
      {/* Pitch background */}
      <rect
        x={config.padding}
        y={config.padding}
        width={pitchSize.width}
        height={pitchSize.height}
        fill={config.pitchColor}
        stroke={config.lineColor}
        strokeWidth="2"
      />

      {/* Halfway line */}
      <line
        x1={config.padding + pitchSize.width / 2}
        y1={config.padding}
        x2={config.padding + pitchSize.width / 2}
        y2={config.padding + pitchSize.height}
        stroke={config.lineColor}
        strokeWidth="2"
      />

      {/* Center circle */}
      <circle
        cx={config.padding + pitchSize.width / 2}
        cy={config.padding + pitchSize.height / 2}
        r={pitchSize.height * 0.15}
        fill="none"
        stroke={config.lineColor}
        strokeWidth="1.5"
      />

      {/* Center spot */}
      <circle
        cx={config.padding + pitchSize.width / 2}
        cy={config.padding + pitchSize.height / 2}
        r="3"
        fill={config.lineColor}
      />

      {/* Left penalty area */}
      <rect
        x={config.padding}
        y={config.padding + pitchSize.height * 0.2}
        width={pitchSize.width * 0.17}
        height={pitchSize.height * 0.6}
        fill="none"
        stroke={config.lineColor}
        strokeWidth="1.5"
      />

      {/* Left goal area */}
      <rect
        x={config.padding}
        y={config.padding + pitchSize.height * 0.35}
        width={pitchSize.width * 0.05}
        height={pitchSize.height * 0.3}
        fill="none"
        stroke={config.lineColor}
        strokeWidth="1.5"
      />

      {/* Left penalty arc */}
      <path
        d={`M ${config.padding + pitchSize.width * 0.12} ${config.padding + pitchSize.height * 0.15}
           A ${pitchSize.height * 0.1} ${pitchSize.height * 0.1} 0 0 1 ${config.padding + pitchSize.width * 0.12} ${config.padding + pitchSize.height * 0.85}`}
        fill="none"
        stroke={config.lineColor}
        strokeWidth="1"
      />

      {/* Right penalty area */}
      <rect
        x={config.padding + pitchSize.width * 0.83}
        y={config.padding + pitchSize.height * 0.2}
        width={pitchSize.width * 0.17}
        height={pitchSize.height * 0.6}
        fill="none"
        stroke={config.lineColor}
        strokeWidth="1.5"
      />

      {/* Right goal area */}
      <rect
        x={config.padding + pitchSize.width * 0.95}
        y={config.padding + pitchSize.height * 0.35}
        width={pitchSize.width * 0.05}
        height={pitchSize.height * 0.3}
        fill="none"
        stroke={config.lineColor}
        strokeWidth="1.5"
      />

      {/* Right penalty arc */}
      <path
        d={`M ${config.padding + pitchSize.width * 0.88} ${config.padding + pitchSize.height * 0.15}
           A ${pitchSize.height * 0.1} ${pitchSize.height * 0.1} 0 0 0 ${config.padding + pitchSize.width * 0.88} ${config.padding + pitchSize.height * 0.85}`}
        fill="none"
        stroke={config.lineColor}
        strokeWidth="1"
      />

      {/* Left corner flags (visual only) */}
      <circle cx={config.padding} cy={config.padding} r="2" fill={config.lineColor} />
      <circle cx={config.padding} cy={config.padding + pitchSize.height} r="2" fill={config.lineColor} />

      {/* Right corner flags (visual only) */}
      <circle cx={config.padding + pitchSize.width} cy={config.padding} r="2" fill={config.lineColor} />
      <circle cx={config.padding + pitchSize.width} cy={config.padding + pitchSize.height} r="2" fill={config.lineColor} />

      {/* Children (visualizations rendered on top) */}
      {children}
    </svg>
  );
};

export default PitchOverlay;
