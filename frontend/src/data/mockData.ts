// This file now serves as a fallback data source and type examples
// All components should primarily use API data through the DataContext

export const fallbackPlayerData = {
  id: 'fallback-1',
  name: 'Sample Player',
  age: 25,
  position: 'CM',
  club: 'Sample FC',
  nationality: 'International',
  rating: 8.0,
  marketValue: '€50M',
  photo: 'https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&cs=tinysrgb&w=400',
  contract: '2025-06-30',
  height: '1.80m',
  weight: '75kg',
  preferredFoot: 'Right',
  goals: 10,
  assists: 8,
  appearances: 30,
  minutesPlayed: 2500,
  xG: 9.5,
  xA: 7.2,
  passAccuracy: 85,
  dribbleSuccess: 70,
  sprintSpeed: 30.0,
  pressureResistance: 8.0,
  workRate: 'High/High',
  weakFoot: 3,
  skillMoves: 3,
  injuryHistory: 'Clean record',
  strongAttributes: ['Passing', 'Vision', 'Work Rate'],
  weakAttributes: ['Pace', 'Physicality'],
  tacticalRole: 'Box-to-Box Midfielder',
  adaptabilityScore: 85,
  mentalStrength: 80,
  leadership: 75,
  consistency: 85,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const fallbackMatchData = {
  id: 'fallback-match-1',
  homeTeam: 'Team A',
  awayTeam: 'Team B',
  homeScore: 2,
  awayScore: 1,
  date: new Date().toISOString(),
  venue: 'Sample Stadium',
  attendance: '50,000',
  status: 'finished' as const,
  homeFormation: '4-3-3',
  awayFormation: '4-2-3-1',
  competition: 'Sample League',
  referee: 'Sample Referee',
  weather: '20°C, Clear',
  homeXG: 2.1,
  awayXG: 1.3,
  homePossession: 60,
  awayPossession: 40,
  homeShots: 15,
  awayShots: 8,
  homeShotsOnTarget: 6,
  awayShotsOnTarget: 3,
  homeCorners: 7,
  awayCorners: 3,
  homeFouls: 10,
  awayFouls: 12,
  homeYellowCards: 2,
  awayYellowCards: 3,
  homeRedCards: 0,
  awayRedCards: 0,
  homePasses: 520,
  awayPasses: 380,
  homePassAccuracy: 88,
  awayPassAccuracy: 82,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

// Professional insights structure for reference
export const professionalInsights = {
  tacticalTrends: [
    {
      trend: 'High Pressing Evolution',
      adoption: 82,
      effectiveness: 87,
      description: 'Advanced pressing triggers and coordinated team movements',
      keyTeams: ['Manchester City', 'Liverpool', 'Bayern Munich'],
      impact: 'Significant improvement in ball recovery and transition speed'
    },
    {
      trend: 'Positional Fluidity',
      adoption: 68,
      effectiveness: 91,
      description: 'Players interchanging positions during different phases of play',
      keyTeams: ['Barcelona', 'Arsenal', 'Brighton'],
      impact: 'Enhanced unpredictability and space creation'
    }
  ],
  marketIntelligence: [
    {
      segment: 'Elite Wingers (20-25)',
      averageValue: '€75M',
      growth: '+28%',
      hotMarkets: ['Premier League', 'La Liga', 'Serie A'],
      keyFactors: ['Pace', 'Dribbling', 'Goal Contribution', 'Versatility']
    },
    {
      segment: 'Creative Midfielders',
      averageValue: '€65M',
      growth: '+22%',
      hotMarkets: ['Premier League', 'Bundesliga', 'Ligue 1'],
      keyFactors: ['Vision', 'Passing Range', 'Set Pieces', 'Leadership']
    }
  ]
};

// Export empty arrays as fallbacks
export const mockPlayers = [];
export const mockGames = [];