import React, { useState } from 'react';
import { Calendar, Clock, MapPin, BarChart3, Users } from 'lucide-react';
import GameCard from './GameCard';
import GameDetail from './GameDetail';
import { useData } from '../context/DataContext';

const GameAnalysis: React.FC = () => {
  const [selectedGame, setSelectedGame] = useState(null);
  const [filterDate, setFilterDate] = useState('');
  const { matches } = useData();

  if (selectedGame) {
    return <GameDetail game={selectedGame} onBack={() => setSelectedGame(null)} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Game Analysis</h1>
        <div className="flex items-center space-x-4">
          <input
            type="date"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-green-500"
          />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">47</div>
              <div className="text-slate-400 text-sm">Games This Month</div>
            </div>
            <Calendar className="h-8 w-8 text-green-400" />
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">156</div>
              <div className="text-slate-400 text-sm">Players Tracked</div>
            </div>
            <Users className="h-8 w-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">8.7</div>
              <div className="text-slate-400 text-sm">Avg Match Rating</div>
            </div>
            <BarChart3 className="h-8 w-8 text-yellow-400" />
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">23</div>
              <div className="text-slate-400 text-sm">Scouted Today</div>
            </div>
            <Clock className="h-8 w-8 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Games Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {matches.map((game) => (
          <GameCard
            key={game.id}
            game={game}
            onClick={() => setSelectedGame(game)}
          />
        ))}
      </div>
    </div>
  );
};

export default GameAnalysis;