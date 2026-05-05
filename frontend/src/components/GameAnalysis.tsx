import React, { useMemo, useState } from 'react';
import { Calendar, Clock, MapPin, BarChart3, Users } from 'lucide-react';
import GameCard from './GameCard';
import GameDetail from './GameDetail';
import { useData } from '../context/DataContext';

const parseDate = (value?: string) => {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const toNumber = (value: unknown): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const GameAnalysis: React.FC = () => {
  const [selectedGame, setSelectedGame] = useState<any>(null);
  const [filterDate, setFilterDate] = useState('');
  const { matches, players } = useData();

  const filteredMatches = useMemo(() => {
    if (!filterDate) {
      return matches;
    }

    return matches.filter((match) => {
      const parsed = parseDate(match.date);
      return parsed ? parsed.toISOString().slice(0, 10) === filterDate : false;
    });
  }, [filterDate, matches]);

  // Use the most recent month in the dataset (not the current calendar month)
  const gamesThisMonth = useMemo(() => {
    if (matches.length === 0) return 0;
    const dates = matches.map(m => parseDate(m.date)).filter(Boolean) as Date[];
    if (dates.length === 0) return matches.length;
    const latest = new Date(Math.max(...dates.map(d => d.getTime())));
    return matches.filter((match) => {
      const parsed = parseDate(match.date);
      return parsed
        ? parsed.getMonth() === latest.getMonth() && parsed.getFullYear() === latest.getFullYear()
        : false;
    }).length;
  }, [matches]);

  const averageGoals = useMemo(() => {
    if (matches.length === 0) {
      return 0;
    }

    const totalGoals = matches.reduce(
      (sum, match) => sum + toNumber(match.homeScore) + toNumber(match.awayScore),
      0,
    );

    return totalGoals / matches.length;
  }, [matches]);

  // Count matches that have scores recorded (completed matches in the dataset)
  const liveMatches = matches.filter((match) => {
    const status = String(match.status || '').toLowerCase();
    if (['live', 'in_progress'].includes(status)) return true;
    return toNumber(match.homeScore) > 0 || toNumber(match.awayScore) > 0;
  }).length;

  const trackedTeams = useMemo(() => {
    const identifiers = matches.flatMap((match) => [
      match.homeTeamId,
      match.awayTeamId,
      match.homeTeam,
      match.awayTeam,
    ]).filter(Boolean);

    return new Set(identifiers.map((value) => String(value))).size;
  }, [matches]);

  const secondaryStatValue = players.length > 0 ? players.length : trackedTeams;
  const secondaryStatLabel = players.length > 0 ? 'Players Tracked' : 'Teams In Feed';
  const activityValue = filteredMatches.length;
  const activityLabel = filterDate ? 'Matches On Date' : 'Total Matches';

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
              <div className="text-2xl font-bold text-white">{gamesThisMonth}</div>
              <div className="text-slate-400 text-sm">Games This Month</div>
            </div>
            <Calendar className="h-8 w-8 text-green-400" />
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{secondaryStatValue}</div>
              <div className="text-slate-400 text-sm">{secondaryStatLabel}</div>
            </div>
            <Users className="h-8 w-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{averageGoals.toFixed(1)}</div>
              <div className="text-slate-400 text-sm">Avg Goals / Match</div>
            </div>
            <BarChart3 className="h-8 w-8 text-yellow-400" />
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{activityValue}</div>
              <div className="text-slate-400 text-sm">{activityLabel}</div>
            </div>
            <Clock className="h-8 w-8 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Games Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredMatches.length > 0 ? (
          filteredMatches.map((game) => (
            <GameCard
              key={game.id}
              game={game}
              onClick={() => setSelectedGame(game)}
            />
          ))
        ) : (
          <div className="col-span-full rounded-xl border border-slate-700 bg-slate-800 px-6 py-12 text-center text-slate-400">
            No backend matches are available for the selected date.
          </div>
        )}
      </div>
    </div>
  );
};

export default GameAnalysis;