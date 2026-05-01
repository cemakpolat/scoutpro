import { Player, Match, Team, PerformanceMetric } from '../types';

interface TeamReference {
  id?: string | number;
  name?: string;
}

// Transform API responses to frontend models
export function transformPlayerData(apiPlayer: any): Player {
  return {
    id: apiPlayer.id || apiPlayer._id || apiPlayer.uID,
    name: apiPlayer.name || `${apiPlayer.firstName || apiPlayer.first || ''} ${apiPlayer.lastName || apiPlayer.last || ''}`.trim(),
    age: apiPlayer.age || calculateAge(apiPlayer.dateOfBirth || apiPlayer.birthDate),
    position: apiPlayer.position || apiPlayer.primaryPosition,
    club: (typeof apiPlayer.club === 'string' ? apiPlayer.club : apiPlayer.club?.name) || apiPlayer.clubName || apiPlayer.teamName || '',
    nationality: apiPlayer.nationality || apiPlayer.country || '',
    rating: apiPlayer.rating || apiPlayer.overallRating,
    marketValue: formatCurrency(apiPlayer.marketValue),
    photo: apiPlayer.photo || apiPlayer.imageUrl || getDefaultPlayerImage(),
    contract: apiPlayer.contractExpiry || apiPlayer.contract?.expiryDate,
    height: formatHeight(apiPlayer.height),
    weight: formatWeight(apiPlayer.weight),
    preferredFoot: apiPlayer.preferredFoot || apiPlayer.preferred_foot || 'Unknown',
    goals: apiPlayer.stats?.goals || 0,
    assists: apiPlayer.stats?.assists || 0,
    appearances: apiPlayer.stats?.appearances || 0,
    minutesPlayed: apiPlayer.stats?.minutesPlayed || 0,
    xG: apiPlayer.stats?.expectedGoals || 0,
    xA: apiPlayer.stats?.expectedAssists || 0,
    passAccuracy: apiPlayer.stats?.passAccuracy || 0,
    dribbleSuccess: apiPlayer.stats?.dribbleSuccessRate || 0,
    sprintSpeed: apiPlayer.physicalStats?.topSpeed || 0,
    pressureResistance: apiPlayer.mentalStats?.pressureResistance || 0,
    workRate: `${apiPlayer.workRate?.attacking || 'Medium'}/${apiPlayer.workRate?.defensive || 'Medium'}`,
    weakFoot: apiPlayer.weakFoot || 3,
    skillMoves: apiPlayer.skillMoves || 3,
    injuryHistory: apiPlayer.injuryHistory || 'No recent injuries',
    strongAttributes: apiPlayer.strongAttributes || [],
    weakAttributes: apiPlayer.weakAttributes || [],
    tacticalRole: apiPlayer.tacticalRole || 'Versatile',
    adaptabilityScore: apiPlayer.adaptabilityScore || 75,
    mentalStrength: apiPlayer.mentalStrength || 75,
    leadership: apiPlayer.leadership || 50,
    consistency: apiPlayer.consistency || 75,
    createdAt: apiPlayer.createdAt || new Date().toISOString(),
    updatedAt: apiPlayer.updatedAt || new Date().toISOString(),
  };
}

export function transformMatchData(apiMatch: any): Match {
  return {
    id: apiMatch.id || apiMatch._id,
    homeTeam: apiMatch.homeTeam?.name || apiMatch.homeTeamName,
    awayTeam: apiMatch.awayTeam?.name || apiMatch.awayTeamName,
    homeScore: apiMatch.homeScore || 0,
    awayScore: apiMatch.awayScore || 0,
    date: apiMatch.date || apiMatch.kickoffTime,
    venue: apiMatch.venue?.name || apiMatch.venueName,
    attendance: formatNumber(apiMatch.attendance),
    status: apiMatch.status || 'scheduled',
    homeFormation: apiMatch.homeFormation || '4-4-2',
    awayFormation: apiMatch.awayFormation || '4-4-2',
    competition: apiMatch.competition?.name || apiMatch.competitionName,
    referee: apiMatch.referee?.name || apiMatch.refereeName,
    weather: apiMatch.weather || 'Clear',
    homeXG: apiMatch.stats?.homeXG || 0,
    awayXG: apiMatch.stats?.awayXG || 0,
    homePossession: apiMatch.stats?.homePossession || 50,
    awayPossession: apiMatch.stats?.awayPossession || 50,
    homeShots: apiMatch.stats?.homeShots || 0,
    awayShots: apiMatch.stats?.awayShots || 0,
    homeShotsOnTarget: apiMatch.stats?.homeShotsOnTarget || 0,
    awayShotsOnTarget: apiMatch.stats?.awayShotsOnTarget || 0,
    homeCorners: apiMatch.stats?.homeCorners || 0,
    awayCorners: apiMatch.stats?.awayCorners || 0,
    homeFouls: apiMatch.stats?.homeFouls || 0,
    awayFouls: apiMatch.stats?.awayFouls || 0,
    homeYellowCards: apiMatch.stats?.homeYellowCards || 0,
    awayYellowCards: apiMatch.stats?.awayYellowCards || 0,
    homeRedCards: apiMatch.stats?.homeRedCards || 0,
    awayRedCards: apiMatch.stats?.awayRedCards || 0,
    homePasses: apiMatch.stats?.homePasses || 0,
    awayPasses: apiMatch.stats?.awayPasses || 0,
    homePassAccuracy: apiMatch.stats?.homePassAccuracy || 0,
    awayPassAccuracy: apiMatch.stats?.awayPassAccuracy || 0,
    createdAt: apiMatch.createdAt || new Date().toISOString(),
    updatedAt: apiMatch.updatedAt || new Date().toISOString(),
  };
}

export function transformTeamData(apiTeam: any): Team {
  return {
    id: apiTeam.id || apiTeam._id,
    name: apiTeam.name,
    shortName: apiTeam.shortName || apiTeam.abbreviation,
    logo: apiTeam.logo || apiTeam.crestUrl,
    league: apiTeam.league?.name || apiTeam.leagueName,
    country: apiTeam.country,
    founded: apiTeam.founded || apiTeam.foundedYear,
    stadium: apiTeam.stadium?.name || apiTeam.stadiumName,
    capacity: apiTeam.stadium?.capacity || apiTeam.stadiumCapacity,
    manager: apiTeam.manager?.name || apiTeam.managerName,
    formation: apiTeam.preferredFormation || '4-4-2',
    playingStyle: apiTeam.playingStyle || 'Balanced',
    marketValue: formatCurrency(apiTeam.squadValue || apiTeam.marketValue),
    averageAge: apiTeam.averageAge || 25,
    createdAt: apiTeam.createdAt || new Date().toISOString(),
    updatedAt: apiTeam.updatedAt || new Date().toISOString(),
  };
}

// Utility functions
function calculateAge(dateOfBirth: string): number {
  if (!dateOfBirth) return 25; // Default age
  const today = new Date();
  const birthDate = new Date(dateOfBirth);
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  
  return age;
}

export function deriveAge(age?: number | null, birthDate?: string | null): number | null {
  if (typeof age === 'number' && Number.isFinite(age) && age > 0) {
    return age;
  }

  if (!birthDate) {
    return null;
  }

  const parsed = new Date(birthDate);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  const today = new Date();
  let derivedAge = today.getFullYear() - parsed.getFullYear();
  const monthDiff = today.getMonth() - parsed.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < parsed.getDate())) {
    derivedAge -= 1;
  }

  return derivedAge >= 0 ? derivedAge : null;
}

function extractDateString(value: unknown): string | null {
  if (!value) {
    return null;
  }

  if (typeof value === 'object' && value !== null && '@value' in (value as Record<string, unknown>)) {
    const rawValue = (value as Record<string, unknown>)['@value'];
    return typeof rawValue === 'string' ? rawValue : null;
  }

  return typeof value === 'string' ? value : null;
}

function parseFlexibleDate(value: unknown): Date | null {
  const dateString = extractDateString(value);
  if (!dateString) {
    return null;
  }

  const normalized = dateString.includes('T') ? dateString : dateString.replace(' ', 'T');
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function isPlaceholderTeamName(value?: string | null): boolean {
  const normalized = String(value || '').trim();
  return !normalized || /^team\s+\d+$/i.test(normalized) || /^(home|away)$/i.test(normalized);
}

export function resolveTeamName(
  teamName: unknown,
  teamId: unknown,
  teams: TeamReference[] = [],
  fallback = 'Unknown Team',
): string {
  const normalizedName = typeof teamName === 'string' ? teamName.trim() : '';
  if (normalizedName && !isPlaceholderTeamName(normalizedName)) {
    return normalizedName;
  }

  const normalizedId = teamId == null ? '' : String(teamId).trim();
  const matchedTeam = teams.find((team) => String(team.id) === normalizedId);
  if (matchedTeam?.name) {
    return matchedTeam.name;
  }

  if (normalizedName && normalizedName !== 'Team 0') {
    return normalizedName;
  }

  if (normalizedId && normalizedId !== '0') {
    return `Team ${normalizedId}`;
  }

  return fallback;
}

export function normalizeMatchStatus(status: unknown, date: unknown, homeScore: unknown, awayScore: unknown): string {
  const normalizedStatus = String(status || '').toLowerCase();
  if (normalizedStatus === 'finished' || normalizedStatus === 'played') {
    return 'finished';
  }

  if (!normalizedStatus || normalizedStatus === 'fixture' || normalizedStatus === 'scheduled') {
    return 'scheduled';
  }

  if (normalizedStatus !== 'live') {
    return normalizedStatus;
  }

  const parsedDate = parseFlexibleDate(date);
  if (!parsedDate) {
    return 'live';
  }

  const ageInHours = (Date.now() - parsedDate.getTime()) / (1000 * 60 * 60);
  if (ageInHours <= 8) {
    return 'live';
  }

  const hasConcreteScore = homeScore !== null && homeScore !== undefined && awayScore !== null && awayScore !== undefined;
  return hasConcreteScore ? 'finished' : 'scheduled';
}

export function hasReliableLiveContext(match: Record<string, unknown>, teams: TeamReference[] = []): boolean {
  const status = normalizeMatchStatus(match.status, match.date, match.homeScore, match.awayScore);
  if (status !== 'live') {
    return false;
  }

  const homeTeamId = String(match.homeTeamId || match.home_team_id || '').trim();
  const awayTeamId = String(match.awayTeamId || match.away_team_id || '').trim();
  if (!homeTeamId || !awayTeamId || homeTeamId === '0' || awayTeamId === '0') {
    return false;
  }

  const homeTeam = resolveTeamName(match.homeTeam || match.home_team, homeTeamId, teams, '');
  const awayTeam = resolveTeamName(match.awayTeam || match.away_team, awayTeamId, teams, '');
  return Boolean(homeTeam && awayTeam);
}

function formatCurrency(value: number | string): string {
  if (!value) return '€0M';
  
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (numValue >= 1000000) {
    return `€${(numValue / 1000000).toFixed(1)}M`;
  } else if (numValue >= 1000) {
    return `€${(numValue / 1000).toFixed(1)}K`;
  } else {
    return `€${numValue}`;
  }
}

function formatHeight(height: number | string): string {
  if (!height) return '1.80m';
  
  const numHeight = typeof height === 'string' ? parseFloat(height) : height;
  
  // Assume height is in cm if > 3, otherwise in meters
  if (numHeight > 3) {
    return `${(numHeight / 100).toFixed(2)}m`;
  } else {
    return `${numHeight.toFixed(2)}m`;
  }
}

function formatWeight(weight: number | string): string {
  if (!weight) return '75kg';
  
  const numWeight = typeof weight === 'string' ? parseFloat(weight) : weight;
  return `${numWeight}kg`;
}

function formatNumber(value: number | string): string {
  if (!value) return '0';
  
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  return numValue.toLocaleString();
}

function getDefaultPlayerImage(): string {
  return 'https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&cs=tinysrgb&w=400';
}

// Data validation functions
export function validatePlayerData(player: any): boolean {
  return !!(
    player.id &&
    player.name &&
    player.position &&
    player.club
  );
}

export function validateMatchData(match: any): boolean {
  return !!(
    match.id &&
    match.homeTeam &&
    match.awayTeam &&
    match.date
  );
}

export function validateTeamData(team: any): boolean {
  return !!(
    team.id &&
    team.name &&
    team.league
  );
}

// Data aggregation functions
export function aggregatePlayerStats(performances: PerformanceMetric[]): any {
  if (!performances.length) return null;

  const totals = performances.reduce((acc, perf) => ({
    goals: acc.goals + perf.goals,
    assists: acc.assists + perf.assists,
    shots: acc.shots + perf.shots,
    passes: acc.passes + perf.passes,
    tackles: acc.tackles + perf.tackles,
    rating: acc.rating + perf.rating,
  }), {
    goals: 0,
    assists: 0,
    shots: 0,
    passes: 0,
    tackles: 0,
    rating: 0,
  });

  const matchCount = performances.length;

  return {
    totalGoals: totals.goals,
    totalAssists: totals.assists,
    averageRating: (totals.rating / matchCount).toFixed(1),
    goalsPerGame: (totals.goals / matchCount).toFixed(1),
    assistsPerGame: (totals.assists / matchCount).toFixed(1),
    shotsPerGame: (totals.shots / matchCount).toFixed(1),
    passesPerGame: (totals.passes / matchCount).toFixed(0),
    tacklesPerGame: (totals.tackles / matchCount).toFixed(1),
    matchesPlayed: matchCount,
  };
}