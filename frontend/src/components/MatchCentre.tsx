import React, { useState, useEffect, useMemo } from 'react';
import { useApi } from '../hooks/useApi';
import { useLiveMatch } from '../hooks/useWebSocket';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import { hasReliableLiveContext, normalizeMatchStatus, resolveTeamName as resolveTeamNameFromContext } from '../utils/dataTransformers';
import { buildMatchCatalog, filterMatchCatalog, formatMatchLabel, getAvailableLeagues, getAvailableYears } from '../utils/matchFilters';
import { 
  Play, Pause, RotateCcw, Zap, TrendingUp, Activity, 
  Users, Target, Clock, MapPin, Thermometer 
} from 'lucide-react';

const createLocalResponse = <T,>(data: T) => ({
  success: true,
  data,
  meta: { timestamp: new Date().toISOString(), source: 'client' },
});

const clamp = (value: number, min: number, max: number): number => Math.max(min, Math.min(max, value));

const getNumericValue = (value: unknown, fallback = 0): number => {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
};

const getSummaryForTeam = (sequenceInsights: any, teamId: string | number | undefined, fallbackTeamName: string) => {
  const normalizedTeamId = String(teamId || '');
  return sequenceInsights?.teamSummaries?.find((summary: any) => String(summary.teamId) === normalizedTeamId)
    || sequenceInsights?.teamSummaries?.find((summary: any) => summary.teamName === fallbackTeamName)
    || {
      teamId: normalizedTeamId,
      teamName: fallbackTeamName,
      totalSequences: 0,
      directAttacks: 0,
      sustainedPressure: 0,
      finalThirdEntries: 0,
      boxEntries: 0,
      shotEndings: 0,
      goals: 0,
      rapidRegains: 0,
      averageActions: 0,
      averageDurationSeconds: 0,
    };
};

const buildWinProbability = (matchView: any, homeSummary: any, awaySummary: any) => {
  const scoreSwing = (matchView.homeScore - matchView.awayScore) * 18;
  const xgSwing = (matchView.homeXG - matchView.awayXG) * 12;
  const sequenceSwing = (homeSummary.boxEntries - awaySummary.boxEntries) * 1.8
    + (homeSummary.finalThirdEntries - awaySummary.finalThirdEntries) * 0.8
    + (homeSummary.rapidRegains - awaySummary.rapidRegains) * 0.15
    + (homeSummary.directAttacks - awaySummary.directAttacks) * 0.8;
  const advantage = clamp(scoreSwing + xgSwing + sequenceSwing, -42, 42);
  const draw = clamp(Math.round(24 - Math.abs(matchView.homeScore - matchView.awayScore) * 6 - Math.abs(advantage) / 8), 10, 28);
  const remaining = 100 - draw;
  const home = clamp(Math.round(remaining / 2 + advantage / 2), 1, remaining - 1);
  const away = 100 - draw - home;

  return { home, draw, away };
};

const describeSequenceOutcome = (sequence: any): string => {
  if (sequence?.endedWithGoal) return 'and finished with a goal';
  if (sequence?.endedWithShot) return 'and ended with a shot';
  if (sequence?.boxEntry) return 'and broke into the box';
  if (sequence?.finalThirdEntry) return 'and entered the final third';
  return 'and gained territory';
};

const MatchCentre: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [selectedYear, setSelectedYear] = useState('all');
  const [selectedLeague, setSelectedLeague] = useState('all');

  const { matches, teams, loading: loadingState } = useData();
  const matchOptions = matches.filter((match: any) => Boolean(match?.id));

  const matchCatalog = useMemo(() => buildMatchCatalog(matchOptions), [matchOptions]);
  const availableYears = useMemo(() => getAvailableYears(matchCatalog), [matchCatalog]);
  const availableLeagues = useMemo(
    () => getAvailableLeagues(matchCatalog, selectedYear),
    [matchCatalog, selectedYear],
  );
  const filteredMatchOptions = useMemo(
    () => filterMatchCatalog(matchCatalog, { year: selectedYear, league: selectedLeague }).map((entry) => entry.source),
    [matchCatalog, selectedYear, selectedLeague],
  );

  useEffect(() => {
    if (selectedYear !== 'all' && !availableYears.includes(selectedYear)) {
      setSelectedYear('all');
    }
  }, [availableYears, selectedYear]);

  useEffect(() => {
    if (selectedLeague !== 'all' && !availableLeagues.includes(selectedLeague)) {
      setSelectedLeague('all');
    }
  }, [availableLeagues, selectedLeague]);

  const defaultMatch = filteredMatchOptions.find((match: any) => hasReliableLiveContext(match, teams))
    || filteredMatchOptions[0]
    || matchOptions.find((match: any) => hasReliableLiveContext(match, teams))
    || matchOptions[0];
  const [selectedMatchId, setSelectedMatchId] = useState<string>(defaultMatch?.id ? String(defaultMatch.id) : '');

  useEffect(() => {
    if ((!selectedMatchId || !filteredMatchOptions.some((match: any) => String(match.id) === String(selectedMatchId))) && defaultMatch?.id) {
      setSelectedMatchId(String(defaultMatch.id));
    }
  }, [defaultMatch?.id, filteredMatchOptions, selectedMatchId]);

  const { onMatchUpdate } = useLiveMatch(selectedMatchId);

  const currentMatch = filteredMatchOptions.find((match: any) => String(match.id) === String(selectedMatchId)) || defaultMatch;
  const normalizedStatus = normalizeMatchStatus(currentMatch?.status, currentMatch?.date, currentMatch?.homeScore ?? currentMatch?.home_score, currentMatch?.awayScore ?? currentMatch?.away_score);
  const hasLiveFeed = currentMatch ? hasReliableLiveContext(currentMatch, teams) : false;
  const [currentMinute, setCurrentMinute] = useState(getNumericValue(currentMatch?.minute ?? currentMatch?.currentMinute, normalizedStatus === 'live' ? 67 : 0));
  const homeTeamId = currentMatch?.homeTeamId || currentMatch?.home_team_id;
  const awayTeamId = currentMatch?.awayTeamId || currentMatch?.away_team_id;
  const resolveTeamName = (teamName: unknown, teamId: string | number | undefined, fallback: string) => (
    resolveTeamNameFromContext(teamName, teamId, teams, fallback)
  );

  const matchView = {
    homeTeam: resolveTeamName(currentMatch?.homeTeam || currentMatch?.home_team, homeTeamId, 'Home'),
    awayTeam: resolveTeamName(currentMatch?.awayTeam || currentMatch?.away_team, awayTeamId, 'Away'),
    homeScore: currentMatch?.homeScore ?? currentMatch?.home_score ?? 0,
    awayScore: currentMatch?.awayScore ?? currentMatch?.away_score ?? 0,
    homeFormation: currentMatch?.homeFormation || currentMatch?.home_formation || 'N/A',
    awayFormation: currentMatch?.awayFormation || currentMatch?.away_formation || 'N/A',
    venue: currentMatch?.venue || 'Venue TBC',
    attendance: currentMatch?.attendance || 0,
    weather: currentMatch?.weather || 'Clear',
    homePossession: Number(currentMatch?.homePossession ?? currentMatch?.home_possession ?? 50),
    awayPossession: Number(currentMatch?.awayPossession ?? currentMatch?.away_possession ?? 50),
    homeShots: Number(currentMatch?.homeShots ?? currentMatch?.home_shots ?? 0),
    awayShots: Number(currentMatch?.awayShots ?? currentMatch?.away_shots ?? 0),
    homeXG: Number(currentMatch?.homeXG ?? currentMatch?.home_xg ?? 0),
    awayXG: Number(currentMatch?.awayXG ?? currentMatch?.away_xg ?? 0),
    homePassAccuracy: Number(currentMatch?.homePassAccuracy ?? currentMatch?.home_pass_accuracy ?? 0),
    awayPassAccuracy: Number(currentMatch?.awayPassAccuracy ?? currentMatch?.away_pass_accuracy ?? 0),
    homeCorners: Number(currentMatch?.homeCorners ?? currentMatch?.home_corners ?? 0),
    awayCorners: Number(currentMatch?.awayCorners ?? currentMatch?.away_corners ?? 0),
  };

  const { data: matchEvents, refetch: refetchMatchEvents } = useApi(
    () => selectedMatchId ? apiService.getMatchEvents(selectedMatchId) : Promise.resolve(createLocalResponse([])),
    [selectedMatchId]
  );
  const { data: lineupData } = useApi(
    () => selectedMatchId ? apiService.getMatchLineup(selectedMatchId) : Promise.resolve(createLocalResponse(null)),
    [selectedMatchId]
  );
  const [activeTab, setActiveTab] = useState<'live' | 'lineup'>('live');
  const { data: tacticalOverview, refetch: refetchSequenceInsights } = useApi(
    () => selectedMatchId ? apiService.getTacticalOverview(undefined, undefined, selectedMatchId) : Promise.resolve(createLocalResponse(null)),
    [selectedMatchId]
  );
  const sequenceInsights = tacticalOverview?.sequenceInsights;
  const homeSummary = getSummaryForTeam(sequenceInsights, homeTeamId, matchView.homeTeam);
  const awaySummary = getSummaryForTeam(sequenceInsights, awayTeamId, matchView.awayTeam);
  const topSequence = sequenceInsights?.topSequences?.[0] || null;
  const winProbability = buildWinProbability(matchView, homeSummary, awaySummary);
  const commentaryCards = sequenceInsights ? [
    {
      title: 'Sequence Pressure Snapshot',
      tone: 'text-purple-400',
      bg: 'bg-purple-600/10 border-purple-600/20',
      icon: Clock,
      body: topSequence
        ? `${topSequence.teamName} produced the strongest spell so far: ${topSequence.actions} actions across ${topSequence.durationSeconds}s through the ${String(topSequence.route || 'central lane').toLowerCase()}, ${describeSequenceOutcome(topSequence)}.`
        : `${matchView.homeTeam} and ${matchView.awayTeam} are still building enough event volume for a stable sequence read.`
    },
    {
      title: 'Regain Battle',
      tone: 'text-blue-400',
      bg: 'bg-blue-600/10 border-blue-600/20',
      icon: TrendingUp,
      body: homeSummary.rapidRegains === awaySummary.rapidRegains
        ? `${matchView.homeTeam} and ${matchView.awayTeam} are level on rapid regains and second balls, so the next transition wave should decide territory.`
        : `${homeSummary.rapidRegains > awaySummary.rapidRegains ? matchView.homeTeam : matchView.awayTeam} are winning the regain battle ${Math.abs(homeSummary.rapidRegains - awaySummary.rapidRegains)} to ${Math.min(homeSummary.rapidRegains, awaySummary.rapidRegains)}, which is shaping the transition phase.`
    },
    {
      title: 'Final-Third Access',
      tone: 'text-yellow-400',
      bg: 'bg-yellow-600/10 border-yellow-600/20',
      icon: Activity,
      body: `${matchView.homeTeam} have ${homeSummary.finalThirdEntries} final-third entries and ${homeSummary.boxEntries} box entries, while ${matchView.awayTeam} sit on ${awaySummary.finalThirdEntries} and ${awaySummary.boxEntries}. That explains the current territorial balance more cleanly than possession alone.`
    },
  ] : [
    {
      title: 'Tactical Shift Detected',
      tone: 'text-purple-400',
      bg: 'bg-purple-600/10 border-purple-600/20',
      icon: Clock,
      body: `${matchView.homeTeam}'s pressure is climbing through the middle third, but the live sequence model has not fully materialized yet.`
    },
    {
      title: 'Performance Alert',
      tone: 'text-blue-400',
      bg: 'bg-blue-600/10 border-blue-600/20',
      icon: TrendingUp,
      body: `${matchView.homeTeam} and ${matchView.awayTeam} are still waiting on enough event detail for a stronger attacking read.`
    },
    {
      title: 'Momentum Shift',
      tone: 'text-yellow-400',
      bg: 'bg-yellow-600/10 border-yellow-600/20',
      icon: Activity,
      body: `The live event stream is active, but the richer sequence layer needs a few more actions before it can separate direct attacks from sustained pressure.`
    },
  ];
  const whatIfScenarios = sequenceInsights ? [
    {
      title: `${matchView.homeTeam}: convert next box entry`,
      detail: `${matchView.homeTeam} already have ${homeSummary.boxEntries} box entries. Another clean box action would push their model edge toward ${Math.min(92, winProbability.home + 6)}%.`
    },
    {
      title: `${matchView.awayTeam}: sustain the regain rate`,
      detail: `${matchView.awayTeam} need to keep rapid regains above ${Math.max(homeSummary.rapidRegains, awaySummary.rapidRegains)} to flatten the territory gap and re-enter the final third faster.`
    },
    {
      title: 'Next direct attack swing',
      detail: `The next direct attack from either side is likely to move win probability by 4-7 points because both teams are already combining high regain counts with live shot volume.`
    },
  ] : [
    {
      title: 'Next sequence swing',
      detail: `The next cluster of live events will sharpen the pressure and regain model for both teams.`
    },
  ];
  const liveStatisticRows = [
    { stat: 'Possession', home: matchView.homePossession, away: matchView.awayPossession },
    { stat: 'Shots', home: matchView.homeShots, away: matchView.awayShots },
    { stat: 'xG', home: matchView.homeXG, away: matchView.awayXG },
    { stat: 'Rapid Regains / Second Balls', home: homeSummary.rapidRegains, away: awaySummary.rapidRegains },
    { stat: 'Final-Third Entries', home: homeSummary.finalThirdEntries, away: awaySummary.finalThirdEntries },
    { stat: 'Box Entries', home: homeSummary.boxEntries, away: awaySummary.boxEntries },
  ];
  const normalizedEvents = (matchEvents || []).slice(0, 10).map((event: any, index: number) => {
    const rawType = String(event.type || event.type_name || event.raw_event?.type_name || 'event');
    const normalizedType = rawType.toLowerCase().replace(/[\s-]+/g, '_');

    return {
      id: event.event_id || `${selectedMatchId}-${index}`,
      minute: event.minute ?? event.raw_event?.minute ?? 0,
      type: normalizedType,
      label: normalizedType.replace(/_/g, ' ').toUpperCase(),
      player: event.player || event.playerName || event.raw_event?.player_name || (event.player_id ? `Player ${event.player_id}` : 'Unknown Player'),
      team: event.team
        || event.teamName
        || event.raw_event?.team_name
        || (String(event.team_id || event.raw_event?.team_id) === String(homeTeamId)
          ? matchView.homeTeam
          : String(event.team_id || event.raw_event?.team_id) === String(awayTeamId)
            ? matchView.awayTeam
            : event.team_id || event.raw_event?.team_id || 'Unknown Team'),
      note: event.note || event.description || event.raw_event?.note || '',
      xG: event.xG ?? event.xg ?? event.raw_event?.xG,
    };
  });

  // Real-time match updates
  useEffect(() => {
    setCurrentMinute(getNumericValue(currentMatch?.minute ?? currentMatch?.currentMinute, normalizedStatus === 'live' ? 67 : 0));
  }, [currentMatch?.id, currentMatch?.minute, currentMatch?.currentMinute, normalizedStatus]);

  useEffect(() => {
    console.log('[MatchCentre] Subscribing to match updates for:', selectedMatchId);

    const unsubscribe = onMatchUpdate((matchData) => {
      console.log('[MatchCentre] Received match update:', matchData);

      if (matchData.matchId === selectedMatchId) {
        console.log('[MatchCentre] Updating UI with new data');
        setCurrentMinute(getNumericValue(matchData.minute ?? matchData.currentMinute, currentMinute));
        void refetchMatchEvents();
        void refetchSequenceInsights();
      }
    });

    return unsubscribe;
  }, [selectedMatchId, onMatchUpdate, refetchMatchEvents, refetchSequenceInsights, currentMinute]);

  useEffect(() => {
    if (!autoRefresh || !hasLiveFeed) {
      return;
    }

    const interval = setInterval(() => {
      void refetchMatchEvents();
      void refetchSequenceInsights();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, hasLiveFeed, refetchMatchEvents, refetchSequenceInsights]);

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
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="all">All Years</option>
            {availableYears.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <select
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="all">All Leagues</option>
            {availableLeagues.map((league) => (
              <option key={league} value={league}>{league}</option>
            ))}
          </select>
          {filteredMatchOptions.length > 0 && (
            <select
              value={selectedMatchId}
              onChange={(e) => setSelectedMatchId(e.target.value)}
              className="max-w-xs truncate px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
            >
              {filteredMatchOptions.map((match: any) => (
                <option key={String(match.id)} value={String(match.id)}>
                  {formatMatchLabel(match)}
                </option>
              ))}
            </select>
          )}
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
            hasLiveFeed ? 'bg-red-600' : 'bg-slate-700'
          }`}>
            <div className={`w-2 h-2 rounded-full ${hasLiveFeed ? 'bg-white animate-pulse' : 'bg-slate-400'}`}></div>
            <span className="text-sm font-medium">{hasLiveFeed ? 'LIVE FEED' : 'SNAPSHOT'}</span>
          </div>
          <button
            onClick={() => setAutoRefresh((current) => !current)}
            disabled={!hasLiveFeed}
            className="p-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-500 rounded-lg transition-colors"
          >
            {autoRefresh ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {!hasLiveFeed && (
        <div className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-300">
          No authoritative live-ingestion feed is connected for this match right now. ScoutPro is showing the stored match snapshot instead of simulating live state.
        </div>
      )}

      {/* Match Header */}
      <div className="bg-slate-800 rounded-xl p-8">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center space-x-12 mb-4">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{matchView.homeTeam}</div>
              <div className="text-slate-400">{matchView.homeFormation}</div>
            </div>
            <div className="text-center">
              <div className="text-6xl font-bold text-green-400 mb-2">
                {matchView.homeScore} - {matchView.awayScore}
              </div>
              <div className="text-2xl text-slate-300">
                {normalizedStatus === 'finished' ? 'FT' : normalizedStatus === 'scheduled' ? 'Scheduled' : `${currentMinute}'`}
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">{matchView.awayTeam}</div>
              <div className="text-slate-400">{matchView.awayFormation}</div>
            </div>
          </div>
          <div className="flex items-center justify-center space-x-6 text-slate-300">
            <div className="flex items-center space-x-2">
              <MapPin className="h-5 w-5" />
              <span>{matchView.venue}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>{matchView.attendance} fans</span>
            </div>
            <div className="flex items-center space-x-2">
              <Thermometer className="h-5 w-5" />
              <span>{matchView.weather}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex space-x-1 bg-slate-800 rounded-lg p-1 w-fit">
        <button
          onClick={() => setActiveTab('live')}
          className={`px-5 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'live' ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-white'}`}
        >
          Live Feed
        </button>
        <button
          onClick={() => setActiveTab('lineup')}
          className={`px-5 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'lineup' ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-white'}`}
        >
          Lineup (F9)
        </button>
      </div>

      {/* Lineup tab — F9 data from Opta */}
      {activeTab === 'lineup' && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-2 flex items-center">
            <Users className="h-6 w-6 mr-2 text-blue-400" />
            Match Lineups — Opta F9
          </h3>
          {lineupData?.data_source === 'no_f9_data' ? (
            <p className="text-slate-400 mt-4">{lineupData.message || 'No F9 lineup data available for this match.'}</p>
          ) : lineupData?.teams?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
              {lineupData.teams.map((team: any) => (
                <div key={team.team_id}>
                  <h4 className="text-lg font-semibold mb-1 text-blue-300">{team.team_name}</h4>
                  {team.formation && <p className="text-xs text-slate-400 mb-3">Formation: <span className="text-slate-200 font-medium">{team.formation}</span></p>}
                  <div className="mb-3">
                    <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Starting XI</p>
                    <div className="space-y-1">
                      {(team.lineup || []).filter((p: any) => p.status === 'Start').map((player: any) => (
                        <div key={player.player_id} className="flex items-center justify-between px-3 py-1.5 bg-slate-700 rounded-lg text-sm">
                          <span className="w-6 text-slate-400 font-mono text-xs">{player.shirt_number ?? '—'}</span>
                          <span className="flex-1 font-medium">{player.player_name}</span>
                          <span className="text-xs text-slate-400 w-8 text-right">{player.position}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  {(team.lineup || []).some((p: any) => p.status === 'Sub') && (
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Substitutes</p>
                      <div className="space-y-1">
                        {(team.lineup || []).filter((p: any) => p.status === 'Sub').map((player: any) => (
                          <div key={player.player_id} className="flex items-center justify-between px-3 py-1.5 bg-slate-700/50 rounded-lg text-sm opacity-80">
                            <span className="w-6 text-slate-500 font-mono text-xs">{player.shirt_number ?? '—'}</span>
                            <span className="flex-1 text-slate-300">{player.player_name}</span>
                            <span className="text-xs text-slate-500 w-8 text-right">{player.position}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {team.goals?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Goals</p>
                      {team.goals.map((g: any, i: number) => (
                        <div key={i} className="text-sm text-green-400">⚽ {g.player} {g.minute}'</div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400 mt-4">
              No lineup data available for this match. Only matches with F9 feed data show lineups.
              Currently 1 match has F9 data (Çaykur Rizespor 2–2 Denizlispor). Select that match from the dropdown above.
            </p>
          )}
        </div>
      )}

      <div className={activeTab === 'live' ? '' : 'hidden'}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Live Event Stream */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center">
              <Zap className="h-6 w-6 mr-2 text-yellow-400" />
              Live Event Stream
            </h3>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {normalizedEvents.map((event) => (
                <div key={event.id} className="flex items-center space-x-4 p-4 bg-slate-700 rounded-lg">
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
                        {event.label}
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
              {commentaryCards.map((card) => {
                const Icon = card.icon;

                return (
                  <div key={card.title} className={`p-4 border rounded-lg ${card.bg}`}>
                    <div className="flex items-center space-x-2 mb-2">
                      <Icon className={`h-5 w-5 ${card.tone}`} />
                      <span className={`font-semibold ${card.tone}`}>{card.title}</span>
                    </div>
                    <p className="text-sm text-slate-300">{card.body}</p>
                  </div>
                );
              })}
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
                  <span>{matchView.homeTeam} Win</span>
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
                  <span>{matchView.awayTeam} Win</span>
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
              {whatIfScenarios.map((scenario) => (
                <button key={scenario.title} className="w-full p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-left transition-colors">
                  <div className="font-medium text-sm">{scenario.title}</div>
                  <div className="text-xs text-slate-400">{scenario.detail}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Key Stats */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold mb-6">Live Statistics</h3>
            <div className="space-y-4">
              {liveStatisticRows.map((item, index) => (
                <div key={index} className="space-y-2">
                  {(() => {
                    const total = (item.home || 0) + (item.away || 0) || 1;

                    return (
                      <>
                  <div className="flex justify-between text-sm">
                    <span className="text-blue-400 font-semibold">{item.home}</span>
                    <span className="text-slate-300">{item.stat}</span>
                    <span className="text-red-400 font-semibold">{item.away}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-blue-400 h-2 rounded-l-full"
                        style={{ width: `${((item.home || 0) / total) * 100}%` }}
                      ></div>
                    </div>
                    <div className="flex-1 bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-red-400 h-2 rounded-r-full ml-auto"
                        style={{ width: `${((item.away || 0) / total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                      </>
                    );
                  })()}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      </div>{/* end live tab wrapper */}
    </div>
  );
};

export default MatchCentre;