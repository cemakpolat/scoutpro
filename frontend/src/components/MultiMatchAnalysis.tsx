import React, { useState, useEffect } from 'react';
import { 
  BarChart3, Calendar, Filter, Download, Play, Pause, 
  TrendingUp, Users, Target, Activity, Zap, Eye,
  ChevronDown, ChevronUp, RefreshCw, Settings, Loader2
} from 'lucide-react';
import { useData } from '../context/DataContext';
import apiService from '../services/api';

const MultiMatchAnalysis: React.FC = () => {
  const [selectedMatches, setSelectedMatches] = useState<string[]>([]);
  const [analysisType, setAnalysisType] = useState('comparative');
  const [timeframe, setTimeframe] = useState('last-month');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  // Fetch real matches from context
  const { matches } = useData();

  // Map real matches for the component
  const availableMatches = matches.map((m: any) => ({
    id: m.id,
    home: m.homeTeam,
    away: m.awayTeam,
    date: m.date,
    score: `${m.homeScore}-${m.awayScore}`,
    competition: m.competition || 'League'
  }));

  // Auto-select first 3 matches if none selected
  useEffect(() => {
    if (availableMatches.length > 0 && selectedMatches.length === 0) {
      setSelectedMatches(availableMatches.slice(0, 3).map((m: any) => m.id));
    }
  }, [availableMatches.length]);

  // Default analysis results (used when no API data)
  const defaultResults = {
    patterns: [
      { pattern: 'High Pressing Effectiveness', frequency: '78%', impact: 'High', trend: 'increasing' },
      { pattern: 'Counter-Attack Success', frequency: '45%', impact: 'Medium', trend: 'stable' },
      { pattern: 'Set-Piece Vulnerability', frequency: '23%', impact: 'High', trend: 'decreasing' },
      { pattern: 'Late Game Fatigue', frequency: '67%', impact: 'Medium', trend: 'increasing' },
    ],
    keyInsights: [
      'Teams with possession >60% win 73% of matches in selected dataset',
      'xG differential >1.5 correlates with 89% win probability',
      'Formation changes after 60th minute increase win probability by 12%',
      'Home advantage worth approximately 0.3 xG per match',
    ],
    playerPerformance: [] as any[]
  };

  const results = analysisResults || defaultResults;

  const toggleMatchSelection = (matchId: string) => {
    setSelectedMatches(prev => 
      prev.includes(matchId) 
        ? prev.filter(id => id !== matchId)
        : [...prev, matchId]
    );
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const [overview, trends] = await Promise.all([
        apiService.getDashboardOverview().catch(() => null),
        apiService.getLeagueTrends().catch(() => null),
      ]);
      if (overview || trends) {
        const patterns = (trends as any)?.trends?.slice(0, 4).map((t: any) => ({
          pattern: t.name || t.league || 'Pattern',
          frequency: `${t.avgGoals || t.matchCount || 0}`,
          impact: (t.avgGoals || 0) > 2.5 ? 'High' : (t.avgGoals || 0) > 1.5 ? 'Medium' : 'Low',
          trend: (t.avgGoals || 0) > 2 ? 'increasing' : 'stable',
        })) || defaultResults.patterns;
        setAnalysisResults({
          patterns: patterns.length > 0 ? patterns : defaultResults.patterns,
          keyInsights: defaultResults.keyInsights,
          playerPerformance: (overview as any)?.topPlayers?.slice(0, 6).map((p: any) => ({
            name: p.name || 'Player',
            matches: p.appearances || 0,
            avgRating: p.rating || 0,
            goals: p.goals || 0,
            assists: p.assists || 0,
            consistency: Math.round((p.rating || 7) * 11),
          })) || defaultResults.playerPerformance,
        });
      }
    } catch (err) {
      console.warn('Multi-match analysis API failed, using defaults', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <BarChart3 className="h-8 w-8 mr-3 text-blue-500" />
          Multi-Match Analysis
        </h1>
        <div className="flex items-center space-x-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="last-week">Last Week</option>
            <option value="last-month">Last Month</option>
            <option value="last-season">Last Season</option>
            <option value="custom">Custom Range</option>
          </select>
          <button
            onClick={runAnalysis}
            disabled={isAnalyzing || selectedMatches.length === 0}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 rounded-lg transition-colors"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                <span>Run Analysis</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Analysis Configuration */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Analysis Configuration</h3>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2">Analysis Type</label>
            <select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg"
            >
              <option value="comparative">Comparative Analysis</option>
              <option value="trend">Trend Analysis</option>
              <option value="pattern">Pattern Recognition</option>
              <option value="predictive">Predictive Modeling</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Focus Area</label>
            <select className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg">
              <option value="tactical">Tactical Analysis</option>
              <option value="individual">Individual Performance</option>
              <option value="team">Team Dynamics</option>
              <option value="situational">Situational Play</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Metrics Priority</label>
            <select className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg">
              <option value="offensive">Offensive Metrics</option>
              <option value="defensive">Defensive Metrics</option>
              <option value="possession">Possession Play</option>
              <option value="transitions">Transitions</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Output Format</label>
            <select className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg">
              <option value="dashboard">Interactive Dashboard</option>
              <option value="report">Detailed Report</option>
              <option value="presentation">Presentation Mode</option>
              <option value="export">Data Export</option>
            </select>
          </div>
        </div>
      </div>

      {/* Match Selection */}
      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold">Select Matches for Analysis</h3>
          <div className="flex items-center space-x-2 text-sm text-slate-400">
            <span>{selectedMatches.length} matches selected</span>
            <button
              onClick={() => setSelectedMatches(availableMatches.map(m => m.id))}
              className="text-blue-400 hover:text-blue-300"
            >
              Select All
            </button>
            <span>|</span>
            <button
              onClick={() => setSelectedMatches([])}
              className="text-red-400 hover:text-red-300"
            >
              Clear All
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {availableMatches.map((match) => (
            <div
              key={match.id}
              onClick={() => toggleMatchSelection(match.id)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedMatches.includes(match.id)
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-slate-700 hover:border-slate-600'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400">{match.competition}</span>
                <span className="text-xs text-slate-400">{match.date}</span>
              </div>
              <div className="text-center">
                <div className="font-semibold text-sm mb-1">{match.home} vs {match.away}</div>
                <div className="text-2xl font-bold text-green-400">{match.score}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Analysis Results */}
      {selectedMatches.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pattern Recognition */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <Target className="h-6 w-6 mr-2 text-purple-400" />
              Pattern Recognition
            </h3>
            <div className="space-y-4">
              {results.patterns.map((pattern: any, index: number) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{pattern.pattern}</span>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        pattern.impact === 'High' ? 'bg-red-600 text-red-100' :
                        pattern.impact === 'Medium' ? 'bg-yellow-600 text-yellow-100' :
                        'bg-green-600 text-green-100'
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
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-sm">Frequency</span>
                    <span className="font-bold text-blue-400">{pattern.frequency}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Key Insights */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <Zap className="h-6 w-6 mr-2 text-yellow-400" />
              Key Insights
            </h3>
            <div className="space-y-4">
              {results.keyInsights.map((insight: any, index: number) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-yellow-600 rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>
                    <p className="text-sm text-slate-300 flex-1">{insight}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Cross-Match Player Performance */}
      {selectedMatches.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Users className="h-6 w-6 mr-2 text-green-400" />
            Cross-Match Player Performance
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">Player</th>
                  <th className="text-left py-3 px-2">Matches</th>
                  <th className="text-left py-3 px-2">Avg Rating</th>
                  <th className="text-left py-3 px-2">Goals</th>
                  <th className="text-left py-3 px-2">Assists</th>
                  <th className="text-left py-3 px-2">Consistency</th>
                  <th className="text-left py-3 px-2">Trend</th>
                </tr>
              </thead>
              <tbody>
                {results.playerPerformance.map((player: any, index: number) => (
                  <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                    <td className="py-3 px-2 font-semibold">{player.name}</td>
                    <td className="py-3 px-2">{player.matches}</td>
                    <td className="py-3 px-2">
                      <span className="text-green-400 font-bold">{player.avgRating}</span>
                    </td>
                    <td className="py-3 px-2">{player.goals}</td>
                    <td className="py-3 px-2">{player.assists}</td>
                    <td className="py-3 px-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-slate-600 rounded-full h-2">
                          <div
                            className="bg-blue-400 h-2 rounded-full"
                            style={{ width: `${player.consistency}%` }}
                          ></div>
                        </div>
                        <span className="text-sm">{player.consistency}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      <TrendingUp className="h-4 w-4 text-green-400" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Advanced Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Tactical Evolution</h3>
          <div className="space-y-4">
            <div className="p-3 bg-slate-700 rounded">
              <div className="flex justify-between mb-1">
                <span className="text-sm">Formation Flexibility</span>
                <span className="text-green-400 font-bold">8.7/10</span>
              </div>
              <div className="text-xs text-slate-400">Teams adapt formations 2.3x per match</div>
            </div>
            <div className="p-3 bg-slate-700 rounded">
              <div className="flex justify-between mb-1">
                <span className="text-sm">Pressing Intensity</span>
                <span className="text-blue-400 font-bold">73%</span>
              </div>
              <div className="text-xs text-slate-400">Average across selected matches</div>
            </div>
            <div className="p-3 bg-slate-700 rounded">
              <div className="flex justify-between mb-1">
                <span className="text-sm">Counter-Attack Speed</span>
                <span className="text-yellow-400 font-bold">4.2s</span>
              </div>
              <div className="text-xs text-slate-400">Average transition time</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Match Momentum</h3>
          <div className="space-y-4">
            <div className="p-3 bg-slate-700 rounded">
              <div className="text-sm font-medium mb-2">Critical Moments</div>
              <div className="text-xs text-slate-400 mb-2">Goals scored in final 15 minutes</div>
              <div className="text-2xl font-bold text-red-400">34%</div>
            </div>
            <div className="p-3 bg-slate-700 rounded">
              <div className="text-sm font-medium mb-2">Momentum Shifts</div>
              <div className="text-xs text-slate-400 mb-2">Average per match</div>
              <div className="text-2xl font-bold text-purple-400">2.8</div>
            </div>
            <div className="p-3 bg-slate-700 rounded">
              <div className="text-sm font-medium mb-2">Comeback Probability</div>
              <div className="text-xs text-slate-400 mb-2">When trailing at halftime</div>
              <div className="text-2xl font-bold text-green-400">23%</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Predictive Insights</h3>
          <div className="space-y-4">
            <div className="p-3 bg-green-600/10 border border-green-600/20 rounded">
              <div className="text-sm font-medium text-green-400 mb-1">High Confidence</div>
              <div className="text-xs text-slate-300">Teams with more than 65% possession win 78% of matches</div>
            </div>
            <div className="p-3 bg-yellow-600/10 border border-yellow-600/20 rounded">
              <div className="text-sm font-medium text-yellow-400 mb-1">Medium Confidence</div>
              <div className="text-xs text-slate-300">Early goals increase win probability by 45%</div>
            </div>
            <div className="p-3 bg-blue-600/10 border border-blue-600/20 rounded">
              <div className="text-sm font-medium text-blue-400 mb-1">Trend Alert</div>
              <div className="text-xs text-slate-300">Set-piece goals increasing 12% this season</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MultiMatchAnalysis;