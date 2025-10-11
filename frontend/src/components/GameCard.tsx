import React from 'react';
import { Match } from '../types';
import { Calendar, MapPin, Clock, Users } from 'lucide-react';

interface GameCardProps {
  game: Match;
  onClick: () => void;
}

const GameCard: React.FC<GameCardProps> = ({ game, onClick }) => {
  return (
    <div 
      onClick={onClick}
      className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-green-500 transition-all cursor-pointer hover:transform hover:scale-105"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Calendar className="h-5 w-5 text-slate-400" />
          <span className="text-slate-400 text-sm">
            {new Date(game.date).toLocaleDateString()}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Clock className="h-4 w-4 text-slate-400" />
          <span className="text-slate-400 text-sm">{game.status}</span>
        </div>
      </div>

      <div className="text-center mb-4">
        <div className="flex items-center justify-center space-x-8">
          <div className="text-center">
            <div className="font-bold text-lg">{game.homeTeam}</div>
            <div className="text-slate-400 text-sm">{game.homeFormation}</div>
          </div>
          <div className="text-3xl font-bold text-green-400">
            {game.homeScore} - {game.awayScore}
          </div>
          <div className="text-center">
            <div className="font-bold text-lg">{game.awayTeam}</div>
            <div className="text-slate-400 text-sm">{game.awayFormation}</div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-slate-700">
        <div className="flex items-center space-x-2 text-sm text-slate-400">
          <MapPin className="h-4 w-4" />
          <span>{game.venue}</span>
        </div>
        {game.attendance && (
          <div className="flex items-center space-x-2 text-sm text-slate-400">
            <Users className="h-4 w-4" />
            <span>{game.attendance} fans</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default GameCard;