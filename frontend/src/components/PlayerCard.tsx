import React from 'react';
import { Player } from '../types';
import { MapPin, Calendar, TrendingUp } from 'lucide-react';

interface PlayerCardProps {
  player: Player;
  onClick: () => void;
}

const PlayerCard: React.FC<PlayerCardProps> = ({ player, onClick }) => {
  return (
    <div 
      onClick={onClick}
      className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-green-500 transition-all cursor-pointer hover:transform hover:scale-105"
    >
      <div className="flex items-center space-x-4 mb-4">
        <img
          src={player.photo}
          alt={player.name}
          className="w-16 h-16 rounded-full object-cover"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = 'https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&cs=tinysrgb&w=400';
          }}
        />
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{player.name}</h3>
          <div className="text-slate-400 text-sm">{player.position}</div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-green-400">{player.rating}</div>
          <div className="text-slate-400 text-xs">Rating</div>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-slate-400">
          <MapPin className="h-4 w-4 mr-2" />
          {player.club}
        </div>
        <div className="flex items-center text-sm text-slate-400">
          <Calendar className="h-4 w-4 mr-2" />
          {player.age} years old
        </div>
      </div>

      <div className="flex justify-between items-center pt-4 border-t border-slate-700">
        <div className="text-sm">
          <div className="text-slate-400">Market Value</div>
          <div className="font-semibold text-green-400">{player.marketValue}</div>
        </div>
        {player.consistency && (
          <div className="flex items-center text-sm text-green-400">
            <TrendingUp className="h-4 w-4 mr-1" />
            {player.consistency}% consistent
          </div>
        )}
      </div>
    </div>
  );
};

export default PlayerCard;