import React from 'react';
import { ArrowLeft, MapPin, Calendar, DollarSign, TrendingUp, Activity, Shield, Target, Zap, Users } from 'lucide-react';

interface Player {
  id: number;
  name: string;
  position: string;
  team: string;
  age: number;
  nationality: string;
  marketValue: string;
  goals: number;
  assists: number;
  rating: number;
  matches: number;
  image: string;
}

interface PlayerDetailProps {
  player: Player;
  onBack: () => void;
}

const PlayerDetail: React.FC<PlayerDetailProps> = ({ player, onBack }) => {
  return (
    <div className="min-h-screen p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={onBack}
            className="flex items-center text-slate-400 hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Players
          </button>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center space-x-6">
              <img
                src={player.image}
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
                    {player.team}
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
                <span className="font-semibold text-white">{player.matches}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Goals per Match</span>
                <span className="font-semibold text-white">{(player.goals / player.matches).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Assists per Match</span>
                <span className="font-semibold text-white">{(player.assists / player.matches).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Goal Contributions</span>
                <span className="font-semibold text-white">{player.goals + player.assists}</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Form</h3>
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerDetail;