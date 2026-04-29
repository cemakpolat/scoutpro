import React, { useState, useEffect } from 'react';
import { 
  Layers, Play, Pause, RotateCcw, Zap, Target, Activity,
  Users, ArrowRight, ArrowUp, ArrowDown, Circle, Square,
  Triangle, Hexagon, Settings, Eye, Download, Share2, Loader2
} from 'lucide-react';
import apiService from '../services/api';
import { useData } from '../context/DataContext';

const TacticalAnalyzer: React.FC = () => {
  const [selectedFormation, setSelectedFormation] = useState('4-3-3');
  const [analysisMode, setAnalysisMode] = useState('live');
  const [selectedPhase, setSelectedPhase] = useState('attack');
  const [loading, setLoading] = useState(true);
  const [apiTactical, setApiTactical] = useState<any>(null);

  const { players: contextPlayers, teams } = useData();

  // Fetch tactical data from API
  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiService.getTacticalPatterns().catch(() => null),
      apiService.getTeamRankings('points', 5).catch(() => null),
    ]).then(([patterns, rankings]) => {
      setApiTactical({ patterns: patterns?.data, rankings: rankings?.data });
    }).finally(() => setLoading(false));
  }, []);

  const formations = [
    { id: '4-3-3', name: '4-3-3', popularity: 34, effectiveness: 87 },
    { id: '4-2-3-1', name: '4-2-3-1', popularity: 28, effectiveness: 84 },
    { id: '3-5-2', name: '3-5-2', popularity: 18, effectiveness: 82 },
    { id: '4-4-2', name: '4-4-2', popularity: 12, effectiveness: 79 },
    { id: '3-4-3', name: '3-4-3', popularity: 8, effectiveness: 85 }
  ];

  // Build tactical patterns from API data or fallback
  const tacticalPatterns = apiTactical?.patterns?.length > 0
    ? apiTactical.patterns.slice(0, 4).map((p: any) => ({
        name: p.name || p.pattern || 'Pattern',
        frequency: p.frequency || p.usage || 50,
        success: p.successRate || p.success || 60,
        zones: p.zones || ['Midfield'],
        impact: (p.successRate || p.success || 60) > 65 ? 'High' : 'Medium',
        trend: p.trend || 'stable',
      }))
    : [
        { name: 'High Pressing', frequency: 78, success: 67, zones: ['Final Third', 'Midfield'], impact: 'High', trend: 'increasing' },
        { name: 'Counter-Attack', frequency: 45, success: 73, zones: ['Defensive Third', 'Wide Areas'], impact: 'Medium', trend: 'stable' },
        { name: 'Possession Play', frequency: 89, success: 62, zones: ['Midfield', 'Wide Areas'], impact: 'High', trend: 'increasing' },
        { name: 'Set Piece Routine', frequency: 23, success: 34, zones: ['Penalty Area'], impact: 'Medium', trend: 'decreasing' },
      ];

  // Build player movements from context players or fallback
  const playerMovements = contextPlayers.length > 0
    ? contextPlayers.slice(0, 4).map((p: any, i: number) => ({
        player: p.name?.split(' ').pop() || `Player ${i + 1}`,
        from: [20 + i * 15, 30 + i * 10],
        to: [60 + i * 10, 25 + i * 8],
        type: i % 2 === 0 ? 'run' : 'pass',
        success: i % 3 !== 2,
      }))
    : [
        { player: 'Player 1', from: [20, 30], to: [80, 25], type: 'run', success: true },
        { player: 'Player 2', from: [40, 60], to: [65, 45], type: 'pass', success: true },
        { player: 'Player 3', from: [60, 70], to: [75, 30], type: 'dribble', success: false },
        { player: 'Player 4', from: [45, 50], to: [55, 40], type: 'pass', success: true },
      ];

  const heatmapData = [
    { zone: 'Left Wing', intensity: 85, effectiveness: 72 },
    { zone: 'Right Wing', intensity: 78, effectiveness: 68 },
    { zone: 'Central Midfield', intensity: 92, effectiveness: 84 },
    { zone: 'Penalty Area', intensity: 67, effectiveness: 91 },
    { zone: 'Defensive Third', intensity: 45, effectiveness: 76 }
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Layers className="h-8 w-8 mr-3 text-purple-500" />
          Tactical Analyzer
        </h1>
        <div className="flex items-center space-x-4">
          <select
            value={analysisMode}
            onChange={(e) => setAnalysisMode(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="live">Live Analysis</option>
            <option value="historical">Historical Analysis</option>
            <option value="predictive">Predictive Analysis</option>
          </select>
          <button className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
            <Eye className="h-4 w-4" />
            <span>3D View</span>
          </button>
        </div>
      </div>

      {/* Formation Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Formation Analysis</h3>
          
          {/* Tactical Board */}
          <div className="relative bg-green-800 rounded-lg p-4 mb-6" style={{ aspectRatio: '16/10' }}>
            <div className="absolute inset-0 bg-gradient-to-b from-green-700 to-green-900 rounded-lg opacity-50"></div>
            
            {/* Field Lines */}
            <div className="absolute inset-0">
              <div className="absolute top-0 left-1/2 w-px h-full bg-white opacity-30 transform -translate-x-1/2"></div>
              <div className="absolute top-1/2 left-0 w-full h-px bg-white opacity-30 transform -translate-y-1/2"></div>
              <div className="absolute top-1/2 left-1/2 w-20 h-20 border border-white opacity-30 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
            </div>

            {/* Player Positions */}
            {selectedFormation === '4-3-3' && (
              <>
                {/* Goalkeeper */}
                <div className="absolute bottom-4 left-1/2 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-xs font-bold transform -translate-x-1/2">
                  GK
                </div>
                
                {/* Defense */}
                <div className="absolute bottom-16 left-1/4 w-6 h-6 bg-blue-400 rounded-full flex items-center justify-center text-xs transform -translate-x-1/2">
                  LB
                </div>
                <div className="absolute bottom-16 left-2/5 w-6 h-6 bg-blue-400 rounded-full flex items-center justify-center text-xs transform -translate-x-1/2">
                  CB
                </div>
                <div className="absolute bottom-16 right-2/5 w-6 h-6 bg-blue-400 rounded-full flex items-center justify-center text-xs transform translate-x-1/2">
                  CB
                </div>
                <div className="absolute bottom-16 right-1/4 w-6 h-6 bg-blue-400 rounded-full flex items-center justify-center text-xs transform translate-x-1/2">
                  RB
                </div>

                {/* Midfield */}
                <div className="absolute bottom-32 left-1/3 w-6 h-6 bg-green-400 rounded-full flex items-center justify-center text-xs transform -translate-x-1/2">
                  CM
                </div>
                <div className="absolute bottom-32 left-1/2 w-6 h-6 bg-green-400 rounded-full flex items-center justify-center text-xs transform -translate-x-1/2">
                  CM
                </div>
                <div className="absolute bottom-32 right-1/3 w-6 h-6 bg-green-400 rounded-full flex items-center justify-center text-xs transform translate-x-1/2">
                  CM
                </div>

                {/* Attack */}
                <div className="absolute bottom-48 left-1/4 w-6 h-6 bg-red-400 rounded-full flex items-center justify-center text-xs transform -translate-x-1/2">
                  LW
                </div>
                <div className="absolute bottom-48 left-1/2 w-6 h-6 bg-red-400 rounded-full flex items-center justify-center text-xs transform -translate-x-1/2">
                  ST
                </div>
                <div className="absolute bottom-48 right-1/4 w-6 h-6 bg-red-400 rounded-full flex items-center justify-center text-xs transform translate-x-1/2">
                  RW
                </div>
              </>
            )}

            {/* Player Movements */}
            {playerMovements.map((movement, index) => (
              <div key={index} className="absolute">
                <div 
                  className={`w-2 h-2 rounded-full ${movement.success ? 'bg-green-400' : 'bg-red-400'}`}
                  style={{ left: `${movement.from[0]}%`, top: `${movement.from[1]}%` }}
                ></div>
                <div 
                  className={`w-1 h-1 rounded-full ${movement.success ? 'bg-green-300' : 'bg-red-300'}`}
                  style={{ left: `${movement.to[0]}%`, top: `${movement.to[1]}%` }}
                ></div>
                <svg className="absolute inset-0 pointer-events-none">
                  <line
                    x1={`${movement.from[0]}%`}
                    y1={`${movement.from[1]}%`}
                    x2={`${movement.to[0]}%`}
                    y2={`${movement.to[1]}%`}
                    stroke={movement.success ? '#4ade80' : '#f87171'}
                    strokeWidth="2"
                    strokeDasharray={movement.type === 'pass' ? '5,5' : '0'}
                    markerEnd="url(#arrowhead)"
                  />
                </svg>
              </div>
            ))}
          </div>

          {/* Formation Selector */}
          <div className="flex space-x-2 mb-4">
            {formations.map((formation) => (
              <button
                key={formation.id}
                onClick={() => setSelectedFormation(formation.id)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  selectedFormation === formation.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {formation.name}
              </button>
            ))}
          </div>

          {/* Phase Selector */}
          <div className="flex space-x-2">
            {['attack', 'defense', 'transition'].map((phase) => (
              <button
                key={phase}
                onClick={() => setSelectedPhase(phase)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  selectedPhase === phase
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {phase.charAt(0).toUpperCase() + phase.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Formation Stats */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Formation Statistics</h3>
          <div className="space-y-4">
            {formations.map((formation) => (
              <div key={formation.id} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold">{formation.name}</span>
                  <span className="text-green-400 font-bold">{formation.effectiveness}%</span>
                </div>
                <div className="text-sm text-slate-400 mb-2">
                  Used by {formation.popularity}% of teams
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-purple-400 h-2 rounded-full"
                    style={{ width: `${formation.effectiveness}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tactical Patterns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Target className="h-6 w-6 mr-2 text-yellow-400" />
            Tactical Patterns
          </h3>
          <div className="space-y-4">
            {tacticalPatterns.map((pattern, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{pattern.name}</span>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      pattern.impact === 'High' ? 'bg-red-600 text-red-100' :
                      'bg-yellow-600 text-yellow-100'
                    }`}>
                      {pattern.impact}
                    </span>
                    <span className={`text-sm ${
                      pattern.trend === 'increasing' ? 'text-green-400' :
                      pattern.trend === 'decreasing' ? 'text-red-400' : 'text-slate-400'
                    }`}>
                      {pattern.trend === 'increasing' ? '↗' : pattern.trend === 'decreasing' ? '↘' : '→'}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                  <div>
                    <div className="text-slate-400">Frequency</div>
                    <div className="font-bold text-blue-400">{pattern.frequency}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Success Rate</div>
                    <div className="font-bold text-green-400">{pattern.success}%</div>
                  </div>
                </div>
                <div className="text-xs text-slate-400">
                  Active in: {pattern.zones.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Heat Map */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Activity className="h-6 w-6 mr-2 text-red-400" />
            Activity Heat Map
          </h3>
          <div className="space-y-4">
            {heatmapData.map((zone, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-semibold">{zone.zone}</span>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">Effectiveness</div>
                    <div className="font-bold text-green-400">{zone.effectiveness}%</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Activity Intensity</span>
                    <span className="font-semibold">{zone.intensity}%</span>
                  </div>
                  <div className="w-full bg-slate-600 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-yellow-400 to-red-500 h-3 rounded-full"
                      style={{ width: `${zone.intensity}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Advanced Analytics */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Zap className="h-6 w-6 mr-2 text-purple-400" />
          Advanced Tactical Analytics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-slate-700 rounded-lg">
            <h4 className="font-semibold mb-3 text-blue-400">Pressing Triggers</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Ball Loss in Final Third</span>
                <span className="text-green-400">87%</span>
              </div>
              <div className="flex justify-between">
                <span>Goalkeeper Distribution</span>
                <span className="text-yellow-400">64%</span>
              </div>
              <div className="flex justify-between">
                <span>Wide Area Possession</span>
                <span className="text-red-400">43%</span>
              </div>
            </div>
          </div>

          <div className="p-4 bg-slate-700 rounded-lg">
            <h4 className="font-semibold mb-3 text-green-400">Build-up Patterns</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Short Passing</span>
                <span className="text-green-400">78%</span>
              </div>
              <div className="flex justify-between">
                <span>Long Ball</span>
                <span className="text-yellow-400">23%</span>
              </div>
              <div className="flex justify-between">
                <span>Wing Play</span>
                <span className="text-blue-400">56%</span>
              </div>
            </div>
          </div>

          <div className="p-4 bg-slate-700 rounded-lg">
            <h4 className="font-semibold mb-3 text-red-400">Defensive Actions</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>High Press Success</span>
                <span className="text-green-400">67%</span>
              </div>
              <div className="flex justify-between">
                <span>Interceptions</span>
                <span className="text-blue-400">89</span>
              </div>
              <div className="flex justify-between">
                <span>Tackles Won</span>
                <span className="text-yellow-400">73%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TacticalAnalyzer;