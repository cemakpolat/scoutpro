import React from 'react';
import { ArrowLeft, MapPin, Calendar, Clock, Users, BarChart3 } from 'lucide-react';

interface GameDetailProps {
  game: any;
  onBack: () => void;
}

const GameDetail: React.FC<GameDetailProps> = ({ game, onBack }) => {
  return (
    <div className="space-y-8">
      <button
        onClick={onBack}
        className="flex items-center space-x-2 text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-5 w-5" />
        <span>Back to Games</span>
      </button>

      {/* Game Header */}
      <div className="bg-slate-800 rounded-xl p-8">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center space-x-12 mb-4">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{game.homeTeam}</div>
              <div className="text-slate-400">{game.homeFormation}</div>
            </div>
            <div className="text-6xl font-bold text-green-400">
              {game.homeScore} - {game.awayScore}
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{game.awayTeam}</div>
              <div className="text-slate-400">{game.awayFormation}</div>
            </div>
          </div>
          <div className="flex items-center justify-center space-x-6 text-slate-300">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5" />
              <span>{game.date}</span>
            </div>
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5" />
              <span>{game.venue}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>{game.attendance} fans</span>
            </div>
          </div>
        </div>
      </div>

      {/* Match Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <BarChart3 className="h-6 w-6 mr-2 text-green-400" />
            Match Statistics
          </h3>
          <div className="space-y-4">
            {[
              { stat: 'Possession', home: 65, away: 35 },
              { stat: 'Shots', home: 18, away: 12 },
              { stat: 'Shots on Target', home: 8, away: 4 },
              { stat: 'Corners', home: 7, away: 3 },
              { stat: 'Fouls', home: 12, away: 16 },
              { stat: 'Yellow Cards', home: 2, away: 4 },
              { stat: 'Passes', home: 524, away: 398 },
              { stat: 'Pass Accuracy', home: 89, away: 82 },
            ].map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-blue-400 font-semibold">{item.home}</span>
                  <span className="text-slate-300">{item.stat}</span>
                  <span className="text-red-400 font-semibold">{item.away}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-blue-400 h-2 rounded-l-full"
                      style={{ width: `${(item.home / (item.home + item.away)) * 100}%` }}
                    ></div>
                  </div>
                  <div className="flex-1 bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-red-400 h-2 rounded-r-full ml-auto"
                      style={{ width: `${(item.away / (item.home + item.away)) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Events */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Clock className="h-6 w-6 mr-2 text-yellow-400" />
            Key Events
          </h3>
          <div className="space-y-4">
            {[
              { minute: 12, event: 'Goal', player: 'João Santos', team: game.homeTeam },
              { minute: 23, event: 'Yellow Card', player: 'Smith', team: game.awayTeam },
              { minute: 35, event: 'Goal', player: 'Johnson', team: game.awayTeam },
              { minute: 67, event: 'Substitution', player: 'García in, Silva out', team: game.homeTeam },
              { minute: 78, event: 'Goal', player: 'Rodríguez', team: game.homeTeam },
              { minute: 89, event: 'Red Card', player: 'Williams', team: game.awayTeam },
            ].map((event, index) => (
              <div key={index} className="flex items-center space-x-4 p-3 bg-slate-700 rounded-lg">
                <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center font-bold text-sm">
                  {event.minute}'
                </div>
                <div className="flex-1">
                  <div className="font-semibold">{event.event}</div>
                  <div className="text-slate-400 text-sm">{event.player} • {event.team}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Player Ratings */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Player Ratings</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h4 className="font-semibold mb-4 text-blue-400">{game.homeTeam}</h4>
            <div className="space-y-3">
              {[
                'João Santos (GK)', 'Silva (CB)', 'García (CB)', 'López (LB)', 'Martín (RB)',
                'Rodríguez (CM)', 'Hernández (CM)', 'Fernández (RW)', 'Díaz (LW)', 
                'Torres (CAM)', 'Moreno (ST)'
              ].map((player, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-slate-700 rounded">
                  <span className="text-sm">{player}</span>
                  <span className="font-bold text-green-400">{(Math.random() * 3 + 6).toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-semibold mb-4 text-red-400">{game.awayTeam}</h4>
            <div className="space-y-3">
              {[
                'Johnson (GK)', 'Smith (CB)', 'Brown (CB)', 'Davis (LB)', 'Wilson (RB)',
                'Miller (CM)', 'Moore (CM)', 'Taylor (RW)', 'Anderson (LW)', 
                'Thomas (CAM)', 'Jackson (ST)'
              ].map((player, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-slate-700 rounded">
                  <span className="text-sm">{player}</span>
                  <span className="font-bold text-green-400">{(Math.random() * 3 + 6).toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameDetail;