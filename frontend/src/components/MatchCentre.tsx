import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import { useLiveMatch } from '../hooks/useWebSocket';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import { 
  Play, Pause, RotateCcw, Zap, TrendingUp, Activity, 
  Users, Target, Clock, MapPin, Thermometer 
} from 'lucide-react';

const MatchCentre: React.FC = () => {
  const [isLive, setIsLive] = useState(true);
  const [winProbability, setWinProbability] = useState({ home: 45, away: 35, draw: 20 });

  const { matches, loading: loadingState } = useData();
  const { data: liveMatches } = useApi(() => apiService.getLiveMatches(), []);

  // Find the first live match or fallback to first match
  const defaultMatch = matches.find(m => m.status === 'live') || liveMatches?.[0] || matches[0];
  const [selectedMatchId, setSelectedMatchId] = useState<string>(defaultMatch?.id || 'match-003');

  const { onMatchUpdate } = useLiveMatch(selectedMatchId);

  const currentMatch = matches.find(m => m.id === selectedMatchId) || liveMatches?.[0] || defaultMatch;
  const [currentMinute, setCurrentMinute] = useState(currentMatch?.status === 'live' ? 67 : 0);

  const { data: matchEvents } = useApi(
    () => selectedMatchId ? apiService.getMatchEvents(selectedMatchId) : Promise.resolve([]),
    [selectedMatchId]
  );

  // Real-time match updates
  useEffect(() => {
    console.log('[MatchCentre] Subscribing to match updates for:', selectedMatchId);

    const unsubscribe = onMatchUpdate((matchData) => {
      console.log('[MatchCentre] Received match update:', matchData);

      if (matchData.matchId === selectedMatchId) {
        console.log('[MatchCentre] Updating UI with new data');
        setCurrentMinute(matchData.minute);
        setWinProbability({
          home: Math.round(Math.random() * 40 + 30),
          away: Math.round(Math.random() * 40 + 30),
          draw: Math.round(Math.random() * 30 + 15)
        });
      }
    });

    return unsubscribe;
  }, [selectedMatchId, onMatchUpdate]);

  useEffect(() => {
    if (isLive) {
      const interval = setInterval(() => {
        setCurrentMinute(prev => prev + 1);
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [isLive]);

  console.log('[MatchCentre] Loading state:', loadingState);
  console.log('[MatchCentre] Current match:', currentMatch);
  console.log('[MatchCentre] All matches:', matches);

  if (loadingState.matches || !currentMatch) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading match data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Activity className="h-8 w-8 mr-3 text-red-500" />
          Match Centre
        </h1>
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
            isLive ? 'bg-red-600' : 'bg-slate-700'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-white animate-pulse' : 'bg-slate-400'}`}></div>
            <span className="text-sm font-medium">{isLive ? 'LIVE' : 'PAUSED'}</span>
          </div>
          <button
            onClick={() => setIsLive(!isLive)}
            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            {isLive ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Match Header */}
      <div className="bg-slate-800 rounded-xl p-8">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center space-x-12 mb-4">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{currentMatch.homeTeam}</div>
              <div className="text-slate-400">{currentMatch.homeFormation}</div>
            </div>
            <div className="text-center">
              <div className="text-6xl font-bold text-green-400 mb-2">
                {currentMatch.homeScore} - {currentMatch.awayScore}
              </div>
              <div className="text-2xl text-slate-300">{currentMinute}'</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{currentMatch.awayTeam}</div>
              <div className="text-slate-400">{currentMatch.awayFormation}</div>
            </div>
          </div>
          <div className="flex items-center justify-center space-x-6 text-slate-300">
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5" />
              <span>{currentMatch.venue}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>{currentMatch.attendance} fans</span>
            </div>
            <div className="flex items-center space-x-2">
              <Thermometer className="h-5 w-5" />
              <span>{currentMatch.weather}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Live Event Stream */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <Zap className="h-6 w-6 mr-2 text-yellow-400" />
              Live Event Stream
            </h3>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {(matchEvents || []).slice(0, 10).map((event, index) => (
                <div key={index} className="flex items-center space-x-4 p-4 bg-slate-700 rounded-lg">
                  <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center font-bold text-sm">
                    {event.minute}'
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        event.type === 'goal' ? 'bg-green-600 text-green-100' :
                        event.type === 'yellow_card' ? 'bg-yellow-600 text-yellow-100' :
                        event.type === 'substitution' ? 'bg-blue-600 text-blue-100' :
                        'bg-slate-600 text-slate-100'
                      }`}>
                        {event.type.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="font-semibold">{event.player}</span>
                      <span className="text-slate-400">• {event.team}</span>
                    </div>
                    {event.xG && (
                      <div className="text-sm text-slate-400 mt-1">
                        Expected Goals: {event.xG}
                      </div>
                    )}
                    {event.note && (
                      <div className="text-sm text-slate-400 mt-1">{event.note}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Commentary */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <Target className="h-6 w-6 mr-2 text-purple-400" />
              AI Commentary & Insights
            </h3>
            <div className="space-y-4">
              <div className="p-4 bg-purple-600/10 border border-purple-600/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Clock className="h-5 w-5 text-purple-400" />
                  <span className="font-semibold text-purple-400">Tactical Shift Detected</span>
                </div>
                <p className="text-sm text-slate-300">
                  {currentMatch.homeTeam}'s pressing intensity has increased by 23% since the 60th minute. 
                  {currentMatch.awayTeam} struggling to build from the back.
                </p>
              </div>
              
              <div className="p-4 bg-blue-600/10 border border-blue-600/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <TrendingUp className="h-5 w-5 text-blue-400" />
                  <span className="font-semibold text-blue-400">Performance Alert</span>
                </div>
                <p className="text-sm text-slate-300">
                  Key player is overperforming their xG by 0.4 this match. Currently on track for 
                  his best performance this season.
                </p>
              </div>

              <div className="p-4 bg-yellow-600/10 border border-yellow-600/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Activity className="h-5 w-5 text-yellow-400" />
                  <span className="font-semibold text-yellow-400">Momentum Shift</span>
                </div>
                <p className="text-sm text-slate-300">
                  Win probability has shifted 15% in {currentMatch.homeTeam}'s favor following the substitution. 
                  Fresh legs creating new attacking dimensions.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Win Probability */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Live Win Probability</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span>{currentMatch.homeTeam} Win</span>
                  <span className="font-bold text-blue-400">{winProbability.home}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div 
                    className="bg-blue-400 h-3 rounded-full transition-all duration-1000"
                    style={{ width: `${winProbability.home}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span>Draw</span>
                  <span className="font-bold text-yellow-400">{winProbability.draw}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div 
                    className="bg-yellow-400 h-3 rounded-full transition-all duration-1000"
                    style={{ width: `${winProbability.draw}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span>{currentMatch.awayTeam} Win</span>
                  <span className="font-bold text-red-400">{winProbability.away}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div 
                    className="bg-red-400 h-3 rounded-full transition-all duration-1000"
                    style={{ width: `${winProbability.away}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* What-If Scenarios */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <RotateCcw className="h-6 w-6 mr-2 text-green-400" />
              What-If Scenarios
            </h3>
            <div className="space-y-3">
              <button className="w-full p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-left transition-colors">
                <div className="font-medium text-sm">If Benzema scored (45')</div>
                <div className="text-xs text-slate-400">{currentMatch.awayTeam} win probability: 52%</div>
              </button>
              
              <button className="w-full p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-left transition-colors">
                <div className="font-medium text-sm">If Neymar stayed on</div>
                <div className="text-xs text-slate-400">{currentMatch.homeTeam} xG would be 0.3 higher</div>
              </button>
              
              <button className="w-full p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-left transition-colors">
                <div className="font-medium text-sm">Formation change to 3-5-2</div>
                <div className="text-xs text-slate-400">Predicted impact: +12% possession</div>
              </button>
            </div>
          </div>

          {/* Key Stats */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Live Statistics</h3>
            <div className="space-y-4">
              {[
                { stat: 'Possession', home: currentMatch.homePossession, away: currentMatch.awayPossession },
                { stat: 'Shots', home: currentMatch.homeShots, away: currentMatch.awayShots },
                { stat: 'xG', home: currentMatch.homeXG, away: currentMatch.awayXG },
                { stat: 'Pass Accuracy', home: currentMatch.homePassAccuracy, away: currentMatch.awayPassAccuracy },
                { stat: 'Corners', home: currentMatch.homeCorners, away: currentMatch.awayCorners },
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
        </div>
      </div>
    </div>
  );
};

export default MatchCentre;