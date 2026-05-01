import React, { useEffect, useState } from 'react';
import { ArrowLeft, MapPin, Calendar, Clock, Users, BarChart3, Download, Loader2 } from 'lucide-react';
import apiService from '../services/api';

interface GameDetailProps {
  game: any;
  onBack: () => void;
}

const toNumber = (value: unknown): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const formatValue = (value: unknown, suffix = ''): string => {
  if (value === undefined || value === null || value === '') {
    return '—';
  }

  return `${value}${suffix}`;
};

const normalizeEvent = (event: any) => ({
  id: event.id || `${event.type || event.type_name || 'event'}-${event.minute || event.timestamp || Math.random()}`,
  minute: event.minute ?? event.timestamp ?? event.elapsed ?? '—',
  label: event.event || event.type_name || event.type || 'Match event',
  actor: event.player_name || event.player || event.playerId || null,
  team: event.team_name || event.team || null,
});

const GameDetail: React.FC<GameDetailProps> = ({ game, onBack }) => {
  const [matchEvents, setMatchEvents] = useState<any[]>([]);
  const [lineup, setLineup] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const fetchMatchData = async () => {
      setLoading(true);
      try {
        const [eventsRes, lineupRes] = await Promise.all([
          apiService.getMatchEvents(game.id),
          apiService.getMatchLineup(game.id),
        ]);
        if (eventsRes.success && eventsRes.data) {
          setMatchEvents(eventsRes.data);
        }
        if (lineupRes.success && lineupRes.data) {
          setLineup(lineupRes.data);
        }
      } catch (e) {
        console.error('Failed to load match detail data', e);
      }
      finally { setLoading(false); }
    };
    fetchMatchData();
  }, [game.id]);

  const handleDownloadReport = async () => {
    setDownloading(true);
    try {
      const blob = await apiService.generateMatchReport(String(game.id));
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `match-report-${game.homeTeam}-vs-${game.awayTeam}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to download match report', e);
    } finally {
      setDownloading(false);
    }
  };

  const stats = [
    { stat: 'Possession', home: toNumber(game.homePossession), away: toNumber(game.awayPossession), homeDisplay: formatValue(game.homePossession, '%'), awayDisplay: formatValue(game.awayPossession, '%') },
    { stat: 'Shots', home: toNumber(game.homeShots), away: toNumber(game.awayShots), homeDisplay: formatValue(game.homeShots), awayDisplay: formatValue(game.awayShots) },
    { stat: 'Shots on Target', home: toNumber(game.homeShotsOnTarget), away: toNumber(game.awayShotsOnTarget), homeDisplay: formatValue(game.homeShotsOnTarget), awayDisplay: formatValue(game.awayShotsOnTarget) },
    { stat: 'Corners', home: toNumber(game.homeCorners), away: toNumber(game.awayCorners), homeDisplay: formatValue(game.homeCorners), awayDisplay: formatValue(game.awayCorners) },
    { stat: 'Fouls', home: toNumber(game.homeFouls), away: toNumber(game.awayFouls), homeDisplay: formatValue(game.homeFouls), awayDisplay: formatValue(game.awayFouls) },
    { stat: 'Yellow Cards', home: toNumber(game.homeYellowCards), away: toNumber(game.awayYellowCards), homeDisplay: formatValue(game.homeYellowCards), awayDisplay: formatValue(game.awayYellowCards) },
    { stat: 'Passes', home: toNumber(game.homePasses), away: toNumber(game.awayPasses), homeDisplay: formatValue(game.homePasses), awayDisplay: formatValue(game.awayPasses) },
    { stat: 'Pass Accuracy', home: toNumber(game.homePassAccuracy), away: toNumber(game.awayPassAccuracy), homeDisplay: formatValue(game.homePassAccuracy, '%'), awayDisplay: formatValue(game.awayPassAccuracy, '%') },
  ];
  const hasDetailedStats = stats.some((item) => item.home > 0 || item.away > 0);
  const eventRows = matchEvents.map(normalizeEvent);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back to Games</span>
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

      {/* Game Header */}
      <div className="bg-slate-800 rounded-xl p-8">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center space-x-12 mb-4">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{game.homeTeam}</div>
              <div className="text-slate-400">{game.homeFormation || 'Formation unavailable'}</div>
            </div>
            <div className="text-6xl font-bold text-green-400">
              {game.homeScore} - {game.awayScore}
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{game.awayTeam}</div>
              <div className="text-slate-400">{game.awayFormation || 'Formation unavailable'}</div>
            </div>
          </div>
          <div className="flex items-center justify-center space-x-6 text-slate-300">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5" />
              <span>{formatValue(game.date)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5" />
              <span>{game.venue || 'Venue unavailable'}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>{game.attendance ? `${game.attendance} fans` : 'Attendance unavailable'}</span>
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
          {hasDetailedStats ? (
            <div className="space-y-4">
              {stats.map((item, index) => {
                const total = item.home + item.away;

                return (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-blue-400 font-semibold">{item.homeDisplay}</span>
                      <span className="text-slate-300">{item.stat}</span>
                      <span className="text-red-400 font-semibold">{item.awayDisplay}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-blue-400 h-2 rounded-l-full"
                          style={{ width: `${total > 0 ? (item.home / total) * 100 : 0}%` }}
                        ></div>
                      </div>
                      <div className="flex-1 bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-red-400 h-2 rounded-r-full ml-auto"
                          style={{ width: `${total > 0 ? (item.away / total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400">Detailed match statistics are not available from the backend for this fixture yet.</p>
          )}
        </div>

        {/* Key Events */}
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Clock className="h-6 w-6 mr-2 text-yellow-400" />
            Key Events
          </h3>
          {eventRows.length > 0 ? (
            <div className="space-y-4">
              {eventRows.map((event) => (
                <div key={event.id} className="flex items-center space-x-4 p-3 bg-slate-700 rounded-lg">
                  <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center font-bold text-sm">
                    {event.minute}'
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold">{event.label}</div>
                    <div className="text-slate-400 text-sm">{[event.actor, event.team].filter(Boolean).join(' • ') || 'No player metadata'}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">No backend event feed is available for this match yet.</p>
          )}
        </div>
      </div>

      {/* Player Ratings */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6">Player Ratings</h3>
        {loading ? (
          <div className="flex items-center gap-2 text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Loading lineup...</div>
        ) : lineup && Array.isArray(lineup.teams) && lineup.teams.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {(['home', 'away'] as const).map((side) => {
              const teamData = lineup.teams.find((t: any) => t.side === side);
              const players: any[] = teamData?.lineup || teamData?.players || [];
              const teamName = side === 'home' ? game.homeTeam : game.awayTeam;
              return (
                <div key={side}>
                  <h4 className={`font-semibold mb-4 ${side === 'home' ? 'text-blue-400' : 'text-red-400'}`}>{teamName}</h4>
                  <div className="space-y-3">
                    {players.map((player: any, index: number) => (
                      <div key={index} className="flex justify-between items-center p-2 bg-slate-700 rounded">
                        <span className="text-sm">
                          {player.player_name || player.name}
                          {player.position ? ` (${player.position.slice(0,2)})` : ''}
                        </span>
                        <span className="font-bold text-green-400">
                          {player.rating != null ? Number(player.rating).toFixed(1) : '—'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-400 text-sm">Lineup data not available for this match.</p>
        )}
      </div>
    </div>
  );
};

export default GameDetail;