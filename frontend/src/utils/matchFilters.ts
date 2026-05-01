type MatchLike = Record<string, any>;

export type MatchCatalogEntry = {
  id: string;
  year: string;
  league: string;
  date?: string;
  timestamp: number;
  source: MatchLike;
};

export type MatchFilterSelection = {
  year: string;
  league: string;
};

const UNKNOWN_YEAR = 'Unknown';
const UNKNOWN_LEAGUE = 'Unknown League';

const parseYearFromSeason = (season: unknown): string | null => {
  if (typeof season !== 'string') {
    return null;
  }

  const match = season.match(/(19|20)\d{2}/);
  return match ? match[0] : null;
};

const resolveYear = (match: MatchLike): string => {
  const fromSeason = parseYearFromSeason(match.season || match.seasonName);
  if (fromSeason) {
    return fromSeason;
  }

  const dateValue = match.date || match.match_date || match.kickoff || match.kickoffTime;
  if (typeof dateValue === 'string' || dateValue instanceof Date) {
    const parsed = new Date(dateValue);
    if (!Number.isNaN(parsed.getTime())) {
      return String(parsed.getFullYear());
    }
  }

  return UNKNOWN_YEAR;
};

const resolveLeague = (match: MatchLike): string => {
  const value = match.competition
    || match.league
    || match.leagueName
    || match.competition_name
    || match.tournament
    || match.tournamentName;

  if (typeof value === 'string' && value.trim()) {
    return value.trim();
  }

  return UNKNOWN_LEAGUE;
};

const resolveMatchId = (match: MatchLike): string | null => {
  const id = match.id || match.matchId || match.matchID;
  if (id === undefined || id === null || String(id).trim() === '') {
    return null;
  }

  return String(id);
};

export const buildMatchCatalog = (matches: MatchLike[]): MatchCatalogEntry[] => {
  const seen = new Set<string>();

  return matches
    .map((match) => {
      const id = resolveMatchId(match);
      if (!id || seen.has(id)) {
        return null;
      }

      seen.add(id);

      const date = match.date || match.match_date || match.kickoff || match.kickoffTime;
      const parsed = date ? new Date(date) : null;
      const timestamp = parsed && !Number.isNaN(parsed.getTime()) ? parsed.getTime() : 0;

      return {
        id,
        year: resolveYear(match),
        league: resolveLeague(match),
        date: typeof date === 'string' ? date : undefined,
        timestamp,
        source: match,
      };
    })
    .filter(Boolean)
    .sort((left, right) => right.timestamp - left.timestamp) as MatchCatalogEntry[];
};

export const getAvailableYears = (catalog: MatchCatalogEntry[]): string[] => {
  const years = Array.from(new Set(catalog.map((entry) => entry.year)));

  return years.sort((left, right) => {
    const leftNumeric = Number(left);
    const rightNumeric = Number(right);

    if (Number.isFinite(leftNumeric) && Number.isFinite(rightNumeric)) {
      return rightNumeric - leftNumeric;
    }

    if (Number.isFinite(leftNumeric)) {
      return -1;
    }

    if (Number.isFinite(rightNumeric)) {
      return 1;
    }

    return left.localeCompare(right);
  });
};

export const getAvailableLeagues = (catalog: MatchCatalogEntry[], selectedYear: string): string[] => {
  const yearFiltered = selectedYear === 'all'
    ? catalog
    : catalog.filter((entry) => entry.year === selectedYear);

  return Array.from(new Set(yearFiltered.map((entry) => entry.league))).sort((left, right) => left.localeCompare(right));
};

export const filterMatchCatalog = (
  catalog: MatchCatalogEntry[],
  selection: MatchFilterSelection,
): MatchCatalogEntry[] => {
  const byYear = selection.year === 'all'
    ? catalog
    : catalog.filter((entry) => entry.year === selection.year);

  const byLeague = selection.league === 'all'
    ? byYear
    : byYear.filter((entry) => entry.league === selection.league);

  return byLeague;
};

export const formatMatchLabel = (match: MatchLike): string => {
  const home = match.homeTeam || match.home_team || 'Home';
  const away = match.awayTeam || match.away_team || 'Away';
  const homeScore = match.homeScore ?? match.home_score;
  const awayScore = match.awayScore ?? match.away_score;

  if (homeScore === undefined || awayScore === undefined) {
    return `${home} vs ${away}`;
  }

  return `${home} ${homeScore} - ${awayScore} ${away}`;
};
