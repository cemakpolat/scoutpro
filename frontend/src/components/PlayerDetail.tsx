import React, { useEffect, useState } from 'react';
import { ArrowLeft, MapPin, Calendar, DollarSign, TrendingUp, Activity, Shield, Target, Zap, Users, Loader2, Download } from 'lucide-react';
import apiService from '../services/api';

interface Player {
  id: string | number;
  name: string;
  position: string;
  team?: string;
  club?: string;
  age: number;
  nationality: string;
  marketValue: string;
  goals: number;
  assists: number;
  rating: number;
  matches?: number;
  appearances?: number;
  image?: string;
  photo?: string;
  passAccuracy?: number;
  xG?: number;
  xA?: number;
}

interface PlayerDetailProps {
  player: Player;
  onBack: () => void;
}

const PlayerDetail: React.FC<PlayerDetailProps> = ({ player: initialPlayer, onBack }) => {
  const [player, setPlayer] = useState(initialPlayer);
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      try {
        // Fetch advanced player insights from API
        const insightsRes = await apiService.getPlayerInsightsAdvanced(String(player.id));
        if (insightsRes.success && insightsRes.data) {
          setInsights(insightsRes.data);
        }
        // Fetch full player data
        const playerRes = await apiService.getPlayer(String(player.id));
        if (playerRes.success && playerRes.data) {
          setPlayer({ ...player, ...playerRes.data });
        }
      } catch (e) {
        // Silently fall back to initial player data
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [initialPlayer.id]);

  const handleDownloadReport = async () => {
    setDownloading(true);
    try {
      const blob = await apiService.generatePlayerReport(String(player.id));
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `player-report-${player.name.replace(/\s+/g, '-')}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to download report', e);
    } finally {
      setDownloading(false);
    }
  };

  const matchesPlayed = player.matches || player.appearances || 1;
  return (
    <div className="min-h-screen p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onBack}
              className="flex items-center text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Players
            </button>
            <button
              onClick={handleDownloadReport}
              disabled={downloading}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 rounded-lg text-sm transition-colors"
            >
              {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              <span>{downloading ? 'Generating...' : 'Download PDF'}</span>
            </button>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center space-x-6">
              <img
                src={player.image || player.photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&size=96&background=334155&color=fff`}
                alt={player.name}
                className="w-24 h-24 rounded-full object-cover"
              />
              <div>
                <h1 className="text-3xl font-bold text-white">{player.name}</h1>
                <div className="flex items-center space-x-4 mt-2 text-slate-400">
                  <span className="flex items-center">
                    <Shield className="w-4 h-4 mr-1" />
                    {player.position}
                  </span>
                  <span className="flex items-center">
                    <Users className="w-4 h-4 mr-1" />
                    {player.team || player.club}
                  </span>
                  <span className="flex items-center">
                    <MapPin className="w-4 h-4 mr-1" />
                    {player.nationality}
                  </span>
                  <span className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    {player.age} years
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Market Value</p>
                <p className="text-2xl font-bold text-white">{player.marketValue}</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Goals</p>
                <p className="text-2xl font-bold text-white">{player.goals}</p>
              </div>
              <Target className="w-8 h-8 text-red-500" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Assists</p>
                <p className="text-2xl font-bold text-white">{player.assists}</p>
              </div>
              <Zap className="w-8 h-8 text-yellow-500" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Rating</p>
                <p className="text-2xl font-bold text-white">{player.rating}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>

        {/* Performance Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Performance Metrics
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Matches Played</span>
                <span className="font-semibold text-white">{matchesPlayed}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Goals per Match</span>
                <span className="font-semibold text-white">{(player.goals / matchesPlayed).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Assists per Match</span>
                <span className="font-semibold text-white">{(player.assists / matchesPlayed).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Goal Contributions</span>
                <span className="font-semibold text-white">{player.goals + player.assists}</span>
              </div>
              {player.passAccuracy != null && (
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Pass Accuracy</span>
                  <span className="font-semibold text-white">{player.passAccuracy}%</span>
                </div>
              )}
              {player.xG != null && (
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">xG</span>
                  <span className="font-semibold text-white">{player.xG}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Form & Insights</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                <span className="text-sm text-slate-400">Last 5 matches</span>
                <div className="flex space-x-1">
                  {['W', 'W', 'D', 'W', 'L'].map((result, index) => (
                    <span
                      key={index}
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        result === 'W'
                          ? 'bg-green-500 text-white'
                          : result === 'D'
                          ? 'bg-yellow-500 text-white'
                          : 'bg-red-500 text-white'
                      }`}
                    >
                      {result}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Form Rating</span>
                <span className="font-semibold text-green-400">Excellent</span>
              </div>
            </div>

            {/* API-driven insights */}
            {insights && insights.insights && insights.insights.length > 0 && (
              <div className="mt-4 space-y-2">
                <h4 className="text-sm font-medium text-slate-400 mb-2">AI Insights</h4>
                {insights.insights.map((ins: any, i: number) => (
                  <div key={i} className="p-3 bg-slate-700 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-white">{ins.title}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        ins.impact === 'high' ? 'bg-red-600/30 text-red-300' : 'bg-yellow-600/30 text-yellow-300'
                      }`}>{ins.impact}</span>
                    </div>
                    <p className="text-xs text-slate-400">{ins.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerDetail;