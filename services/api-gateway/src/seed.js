/**
 * ScoutPro Database Seed Script
 * Populates MongoDB with realistic football data matching frontend types.
 * Run with: node seed.js
 */
const { MongoClient } = require('mongodb');

const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin';

const teams = [
  { id: 'team-001', name: 'Real Madrid', shortName: 'RMA', logo: 'https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg', league: 'La Liga', country: 'Spain', founded: 1902, stadium: 'Santiago Bernabéu', capacity: 81044, manager: 'Carlo Ancelotti', formation: '4-3-3', playingStyle: 'Possession-based', marketValue: '€1.2B', averageAge: 27.3 },
  { id: 'team-002', name: 'Manchester City', shortName: 'MCI', logo: 'https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg', league: 'Premier League', country: 'England', founded: 1880, stadium: 'Etihad Stadium', capacity: 53400, manager: 'Pep Guardiola', formation: '4-3-3', playingStyle: 'Tiki-taka', marketValue: '€1.3B', averageAge: 26.8 },
  { id: 'team-003', name: 'Bayern Munich', shortName: 'BAY', logo: 'https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg', league: 'Bundesliga', country: 'Germany', founded: 1900, stadium: 'Allianz Arena', capacity: 75000, manager: 'Vincent Kompany', formation: '4-2-3-1', playingStyle: 'High pressing', marketValue: '€1.1B', averageAge: 26.5 },
  { id: 'team-004', name: 'FC Barcelona', shortName: 'BAR', logo: 'https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg', league: 'La Liga', country: 'Spain', founded: 1899, stadium: 'Camp Nou', capacity: 99354, manager: 'Hansi Flick', formation: '4-3-3', playingStyle: 'Possession-based', marketValue: '€1.0B', averageAge: 25.9 },
  { id: 'team-005', name: 'Liverpool', shortName: 'LIV', logo: 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg', league: 'Premier League', country: 'England', founded: 1892, stadium: 'Anfield', capacity: 61276, manager: 'Arne Slot', formation: '4-3-3', playingStyle: 'Counter-pressing', marketValue: '€950M', averageAge: 26.2 },
  { id: 'team-006', name: 'Paris Saint-Germain', shortName: 'PSG', logo: 'https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg', league: 'Ligue 1', country: 'France', founded: 1970, stadium: 'Parc des Princes', capacity: 47929, manager: 'Luis Enrique', formation: '4-3-3', playingStyle: 'Attacking', marketValue: '€980M', averageAge: 25.4 },
  { id: 'team-007', name: 'Juventus', shortName: 'JUV', logo: 'https://upload.wikimedia.org/wikipedia/commons/a/a8/Juventus_FC_-_wordmark.svg', league: 'Serie A', country: 'Italy', founded: 1897, stadium: 'Allianz Stadium', capacity: 41507, manager: 'Thiago Motta', formation: '4-2-3-1', playingStyle: 'Defensive resilience', marketValue: '€750M', averageAge: 26.7 },
  { id: 'team-008', name: 'Arsenal', shortName: 'ARS', logo: 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg', league: 'Premier League', country: 'England', founded: 1886, stadium: 'Emirates Stadium', capacity: 60704, manager: 'Mikel Arteta', formation: '4-3-3', playingStyle: 'Positional play', marketValue: '€1.1B', averageAge: 25.6 },
  { id: 'team-009', name: 'Inter Milan', shortName: 'INT', logo: 'https://upload.wikimedia.org/wikipedia/commons/0/05/FC_Internazionale_Milano_2021.svg', league: 'Serie A', country: 'Italy', founded: 1908, stadium: 'San Siro', capacity: 75923, manager: 'Simone Inzaghi', formation: '3-5-2', playingStyle: 'Counter-attacking', marketValue: '€850M', averageAge: 28.1 },
  { id: 'team-010', name: 'Borussia Dortmund', shortName: 'BVB', logo: 'https://upload.wikimedia.org/wikipedia/commons/6/67/Borussia_Dortmund_logo.svg', league: 'Bundesliga', country: 'Germany', founded: 1909, stadium: 'Signal Iduna Park', capacity: 81365, manager: 'Nuri Şahin', formation: '4-2-3-1', playingStyle: 'Fast transitions', marketValue: '€700M', averageAge: 25.8 },
  { id: 'team-011', name: 'Chelsea', shortName: 'CHE', logo: 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg', league: 'Premier League', country: 'England', founded: 1905, stadium: 'Stamford Bridge', capacity: 40834, manager: 'Enzo Maresca', formation: '4-2-3-1', playingStyle: 'Build-up play', marketValue: '€950M', averageAge: 24.8 },
  { id: 'team-012', name: 'AC Milan', shortName: 'ACM', logo: 'https://upload.wikimedia.org/wikipedia/commons/d/d0/Logo_of_AC_Milan.svg', league: 'Serie A', country: 'Italy', founded: 1899, stadium: 'San Siro', capacity: 75923, manager: 'Paulo Fonseca', formation: '4-3-3', playingStyle: 'Attacking', marketValue: '€680M', averageAge: 26.3 },
  { id: 'team-013', name: 'Atlético Madrid', shortName: 'ATM', logo: 'https://upload.wikimedia.org/wikipedia/en/f/f4/Atletico_Madrid_2017_logo.svg', league: 'La Liga', country: 'Spain', founded: 1903, stadium: 'Cívitas Metropolitano', capacity: 70460, manager: 'Diego Simeone', formation: '3-5-2', playingStyle: 'Defensive', marketValue: '€780M', averageAge: 27.5 },
  { id: 'team-014', name: 'Manchester United', shortName: 'MUN', logo: 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg', league: 'Premier League', country: 'England', founded: 1878, stadium: 'Old Trafford', capacity: 74310, manager: 'Rúben Amorim', formation: '3-4-2-1', playingStyle: 'Fluid attacking', marketValue: '€820M', averageAge: 25.9 },
  { id: 'team-015', name: 'Napoli', shortName: 'NAP', logo: 'https://upload.wikimedia.org/wikipedia/commons/2/2d/SSC_Neapel.svg', league: 'Serie A', country: 'Italy', founded: 1926, stadium: 'Stadio Diego Armando Maradona', capacity: 54726, manager: 'Antonio Conte', formation: '3-4-2-1', playingStyle: 'Tactical flexibility', marketValue: '€720M', averageAge: 27.0 }
];

const playerData = [
  // Real Madrid
  { id: 'player-001', name: 'Vinícius Jr.', age: 25, position: 'Left Winger', club: 'Real Madrid', nationality: 'Brazil', rating: 9.1, marketValue: '€180M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 24, assists: 12, appearances: 35, minutesPlayed: 2890, xG: 20.5, xA: 9.8, passAccuracy: 78, dribbleSuccess: 62, sprintSpeed: 96, pressureResistance: 82, workRate: 'High/Medium', weakFoot: 3, skillMoves: 5, injuryHistory: 'Minor ankle injury 2024', strongAttributes: ['Dribbling', 'Speed', 'Finishing'], weakAttributes: ['Heading', 'Strength'], tacticalRole: 'Inside Forward', adaptabilityScore: 88, mentalStrength: 85, leadership: 72, consistency: 80, preferredFoot: 'Right', height: '176 cm', weight: '73 kg', contract: '2028' },
  { id: 'player-002', name: 'Jude Bellingham', age: 22, position: 'Attacking Midfielder', club: 'Real Madrid', nationality: 'England', rating: 8.9, marketValue: '€150M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 19, assists: 10, appearances: 33, minutesPlayed: 2750, xG: 16.2, xA: 8.5, passAccuracy: 86, dribbleSuccess: 55, sprintSpeed: 85, pressureResistance: 90, workRate: 'High/High', weakFoot: 4, skillMoves: 4, injuryHistory: 'None', strongAttributes: ['Vision', 'Shooting', 'Leadership'], weakAttributes: ['Pace'], tacticalRole: 'Advanced Playmaker', adaptabilityScore: 92, mentalStrength: 94, leadership: 88, consistency: 87, preferredFoot: 'Left', height: '186 cm', weight: '78 kg', contract: '2029' },
  { id: 'player-003', name: 'Kylian Mbappé', age: 27, position: 'Striker', club: 'Real Madrid', nationality: 'France', rating: 9.3, marketValue: '€200M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 32, assists: 8, appearances: 36, minutesPlayed: 3100, xG: 28.4, xA: 6.2, passAccuracy: 80, dribbleSuccess: 58, sprintSpeed: 97, pressureResistance: 85, workRate: 'High/Low', weakFoot: 4, skillMoves: 5, injuryHistory: 'Hamstring strain 2025', strongAttributes: ['Speed', 'Finishing', 'Movement'], weakAttributes: ['Aerial ability'], tacticalRole: 'Poacher', adaptabilityScore: 90, mentalStrength: 88, leadership: 78, consistency: 85, preferredFoot: 'Right', height: '178 cm', weight: '73 kg', contract: '2029' },
  // Manchester City
  { id: 'player-004', name: 'Erling Haaland', age: 25, position: 'Striker', club: 'Manchester City', nationality: 'Norway', rating: 9.2, marketValue: '€190M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 36, assists: 5, appearances: 34, minutesPlayed: 2950, xG: 31.2, xA: 4.1, passAccuracy: 72, dribbleSuccess: 42, sprintSpeed: 92, pressureResistance: 78, workRate: 'High/Medium', weakFoot: 3, skillMoves: 3, injuryHistory: 'Foot injury 2024', strongAttributes: ['Finishing', 'Positioning', 'Strength'], weakAttributes: ['Passing', 'Dribbling'], tacticalRole: 'Target Man', adaptabilityScore: 80, mentalStrength: 90, leadership: 70, consistency: 88, preferredFoot: 'Left', height: '194 cm', weight: '88 kg', contract: '2027' },
  { id: 'player-005', name: 'Kevin De Bruyne', age: 34, position: 'Central Midfielder', club: 'Manchester City', nationality: 'Belgium', rating: 8.8, marketValue: '€50M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 8, assists: 18, appearances: 28, minutesPlayed: 2200, xG: 6.5, xA: 16.8, passAccuracy: 91, dribbleSuccess: 48, sprintSpeed: 75, pressureResistance: 92, workRate: 'High/High', weakFoot: 5, skillMoves: 4, injuryHistory: 'Multiple knee injuries', strongAttributes: ['Vision', 'Passing', 'Crossing'], weakAttributes: ['Pace', 'Stamina'], tacticalRole: 'Deep Playmaker', adaptabilityScore: 95, mentalStrength: 92, leadership: 90, consistency: 82, preferredFoot: 'Right', height: '181 cm', weight: '76 kg', contract: '2026' },
  { id: 'player-006', name: 'Phil Foden', age: 25, position: 'Attacking Midfielder', club: 'Manchester City', nationality: 'England', rating: 8.7, marketValue: '€130M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 15, assists: 11, appearances: 32, minutesPlayed: 2600, xG: 13.1, xA: 10.2, passAccuracy: 87, dribbleSuccess: 58, sprintSpeed: 86, pressureResistance: 84, workRate: 'High/High', weakFoot: 3, skillMoves: 4, injuryHistory: 'None', strongAttributes: ['Dribbling', 'Vision', 'Technique'], weakAttributes: ['Physical strength'], tacticalRole: 'Free Roam', adaptabilityScore: 88, mentalStrength: 82, leadership: 68, consistency: 84, preferredFoot: 'Left', height: '171 cm', weight: '69 kg', contract: '2028' },
  // Bayern Munich
  { id: 'player-007', name: 'Jamal Musiala', age: 22, position: 'Attacking Midfielder', club: 'Bayern Munich', nationality: 'Germany', rating: 8.8, marketValue: '€140M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 16, assists: 13, appearances: 34, minutesPlayed: 2850, xG: 13.8, xA: 11.5, passAccuracy: 88, dribbleSuccess: 65, sprintSpeed: 84, pressureResistance: 87, workRate: 'High/High', weakFoot: 4, skillMoves: 5, injuryHistory: 'None', strongAttributes: ['Dribbling', 'Creativity', 'Ball control'], weakAttributes: ['Tackling'], tacticalRole: 'Trequartista', adaptabilityScore: 91, mentalStrength: 85, leadership: 72, consistency: 86, preferredFoot: 'Right', height: '183 cm', weight: '72 kg', contract: '2029' },
  { id: 'player-008', name: 'Harry Kane', age: 32, position: 'Striker', club: 'Bayern Munich', nationality: 'England', rating: 9.0, marketValue: '€100M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 30, assists: 11, appearances: 33, minutesPlayed: 2900, xG: 27.5, xA: 9.8, passAccuracy: 83, dribbleSuccess: 40, sprintSpeed: 78, pressureResistance: 88, workRate: 'High/Medium', weakFoot: 4, skillMoves: 3, injuryHistory: 'Ankle injury history', strongAttributes: ['Finishing', 'Vision', 'Heading'], weakAttributes: ['Pace'], tacticalRole: 'Complete Forward', adaptabilityScore: 90, mentalStrength: 93, leadership: 92, consistency: 91, preferredFoot: 'Right', height: '188 cm', weight: '86 kg', contract: '2027' },
  // Barcelona
  { id: 'player-009', name: 'Lamine Yamal', age: 18, position: 'Right Winger', club: 'FC Barcelona', nationality: 'Spain', rating: 8.6, marketValue: '€150M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 12, assists: 15, appearances: 34, minutesPlayed: 2700, xG: 10.2, xA: 13.5, passAccuracy: 84, dribbleSuccess: 60, sprintSpeed: 93, pressureResistance: 78, workRate: 'High/Medium', weakFoot: 3, skillMoves: 4, injuryHistory: 'None', strongAttributes: ['Pace', 'Creativity', 'Dribbling'], weakAttributes: ['Physical strength', 'Experience'], tacticalRole: 'Inside Forward', adaptabilityScore: 85, mentalStrength: 78, leadership: 60, consistency: 79, preferredFoot: 'Left', height: '180 cm', weight: '70 kg', contract: '2030' },
  { id: 'player-010', name: 'Pedri', age: 23, position: 'Central Midfielder', club: 'FC Barcelona', nationality: 'Spain', rating: 8.7, marketValue: '€120M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 7, assists: 12, appearances: 30, minutesPlayed: 2400, xG: 5.8, xA: 10.5, passAccuracy: 92, dribbleSuccess: 55, sprintSpeed: 80, pressureResistance: 90, workRate: 'High/High', weakFoot: 4, skillMoves: 4, injuryHistory: 'Hamstring issues', strongAttributes: ['Passing', 'Vision', 'Ball control'], weakAttributes: ['Strength', 'Shooting'], tacticalRole: 'Mezzala', adaptabilityScore: 90, mentalStrength: 86, leadership: 75, consistency: 83, preferredFoot: 'Right', height: '174 cm', weight: '63 kg', contract: '2030' },
  // Liverpool
  { id: 'player-011', name: 'Mohamed Salah', age: 33, position: 'Right Winger', club: 'Liverpool', nationality: 'Egypt', rating: 8.9, marketValue: '€70M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 22, assists: 14, appearances: 34, minutesPlayed: 2950, xG: 19.8, xA: 12.1, passAccuracy: 81, dribbleSuccess: 52, sprintSpeed: 90, pressureResistance: 84, workRate: 'High/Medium', weakFoot: 3, skillMoves: 4, injuryHistory: 'None significant', strongAttributes: ['Finishing', 'Pace', 'Movement'], weakAttributes: ['Heading', 'Tackling'], tacticalRole: 'Inside Forward', adaptabilityScore: 92, mentalStrength: 91, leadership: 85, consistency: 90, preferredFoot: 'Left', height: '175 cm', weight: '71 kg', contract: '2026' },
  { id: 'player-012', name: 'Virgil van Dijk', age: 34, position: 'Centre Back', club: 'Liverpool', nationality: 'Netherlands', rating: 8.5, marketValue: '€35M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 3, assists: 2, appearances: 32, minutesPlayed: 2850, xG: 2.8, xA: 1.5, passAccuracy: 88, dribbleSuccess: 35, sprintSpeed: 80, pressureResistance: 88, workRate: 'Medium/High', weakFoot: 3, skillMoves: 2, injuryHistory: 'ACL injury 2020', strongAttributes: ['Heading', 'Leadership', 'Positioning'], weakAttributes: ['Pace declining'], tacticalRole: 'Ball-playing CB', adaptabilityScore: 85, mentalStrength: 94, leadership: 96, consistency: 88, preferredFoot: 'Right', height: '193 cm', weight: '92 kg', contract: '2026' },
  // PSG
  { id: 'player-013', name: 'Ousmane Dembélé', age: 29, position: 'Right Winger', club: 'Paris Saint-Germain', nationality: 'France', rating: 8.4, marketValue: '€80M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 14, assists: 11, appearances: 30, minutesPlayed: 2400, xG: 12.1, xA: 9.8, passAccuracy: 79, dribbleSuccess: 60, sprintSpeed: 94, pressureResistance: 75, workRate: 'High/Medium', weakFoot: 5, skillMoves: 5, injuryHistory: 'Multiple injuries', strongAttributes: ['Speed', 'Dribbling', 'Both feet'], weakAttributes: ['Decision making', 'Consistency'], tacticalRole: 'Wide Playmaker', adaptabilityScore: 82, mentalStrength: 70, leadership: 55, consistency: 68, preferredFoot: 'Both', height: '178 cm', weight: '73 kg', contract: '2028' },
  // Arsenal
  { id: 'player-014', name: 'Bukayo Saka', age: 24, position: 'Right Winger', club: 'Arsenal', nationality: 'England', rating: 8.8, marketValue: '€140M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 18, assists: 14, appearances: 35, minutesPlayed: 3000, xG: 15.5, xA: 12.8, passAccuracy: 84, dribbleSuccess: 55, sprintSpeed: 88, pressureResistance: 86, workRate: 'High/High', weakFoot: 4, skillMoves: 4, injuryHistory: 'None', strongAttributes: ['Creativity', 'Work rate', 'Versatility'], weakAttributes: ['Heading'], tacticalRole: 'Inverted Winger', adaptabilityScore: 91, mentalStrength: 88, leadership: 80, consistency: 89, preferredFoot: 'Left', height: '178 cm', weight: '72 kg', contract: '2029' },
  { id: 'player-015', name: 'Martin Ødegaard', age: 27, position: 'Attacking Midfielder', club: 'Arsenal', nationality: 'Norway', rating: 8.7, marketValue: '€110M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 11, assists: 15, appearances: 32, minutesPlayed: 2700, xG: 9.2, xA: 13.5, passAccuracy: 90, dribbleSuccess: 52, sprintSpeed: 80, pressureResistance: 88, workRate: 'High/High', weakFoot: 3, skillMoves: 4, injuryHistory: 'Ankle injury 2024', strongAttributes: ['Vision', 'Passing', 'Set pieces'], weakAttributes: ['Physical', 'Aerial'], tacticalRole: 'Advanced Playmaker', adaptabilityScore: 89, mentalStrength: 86, leadership: 85, consistency: 87, preferredFoot: 'Left', height: '178 cm', weight: '68 kg', contract: '2028' },
  // More diverse players
  { id: 'player-016', name: 'Florian Wirtz', age: 22, position: 'Attacking Midfielder', club: 'Bayern Munich', nationality: 'Germany', rating: 8.9, marketValue: '€150M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 18, assists: 14, appearances: 33, minutesPlayed: 2750, xG: 15.2, xA: 12.8, passAccuracy: 89, dribbleSuccess: 58, sprintSpeed: 85, pressureResistance: 86, workRate: 'High/High', weakFoot: 4, skillMoves: 4, injuryHistory: 'ACL 2022', strongAttributes: ['Creativity', 'Shooting', 'Intelligence'], weakAttributes: ['Physical strength'], tacticalRole: 'Playmaker', adaptabilityScore: 90, mentalStrength: 84, leadership: 70, consistency: 87, preferredFoot: 'Right', height: '176 cm', weight: '70 kg', contract: '2029' },
  { id: 'player-017', name: 'Rodri', age: 29, position: 'Defensive Midfielder', club: 'Manchester City', nationality: 'Spain', rating: 9.0, marketValue: '€120M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 5, assists: 8, appearances: 15, minutesPlayed: 1200, xG: 4.2, xA: 6.8, passAccuracy: 93, dribbleSuccess: 45, sprintSpeed: 72, pressureResistance: 95, workRate: 'Medium/High', weakFoot: 4, skillMoves: 3, injuryHistory: 'ACL injury 2024', strongAttributes: ['Positioning', 'Passing', 'Game reading'], weakAttributes: ['Recovery speed'], tacticalRole: 'Regista', adaptabilityScore: 92, mentalStrength: 95, leadership: 88, consistency: 92, preferredFoot: 'Right', height: '191 cm', weight: '82 kg', contract: '2027' },
  { id: 'player-018', name: 'Gavi', age: 21, position: 'Central Midfielder', club: 'FC Barcelona', nationality: 'Spain', rating: 8.3, marketValue: '€90M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 5, assists: 7, appearances: 25, minutesPlayed: 2000, xG: 4.1, xA: 6.2, passAccuracy: 88, dribbleSuccess: 52, sprintSpeed: 84, pressureResistance: 82, workRate: 'High/High', weakFoot: 3, skillMoves: 3, injuryHistory: 'ACL injury 2023', strongAttributes: ['Energy', 'Pressing', 'Tenacity'], weakAttributes: ['Finishing', 'Size'], tacticalRole: 'Box-to-Box', adaptabilityScore: 86, mentalStrength: 88, leadership: 78, consistency: 80, preferredFoot: 'Right', height: '173 cm', weight: '68 kg', contract: '2030' },
  { id: 'player-019', name: 'Marcus Rashford', age: 28, position: 'Left Winger', club: 'Manchester United', nationality: 'England', rating: 7.8, marketValue: '€60M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 10, assists: 6, appearances: 30, minutesPlayed: 2400, xG: 12.5, xA: 5.8, passAccuracy: 76, dribbleSuccess: 50, sprintSpeed: 93, pressureResistance: 70, workRate: 'High/Low', weakFoot: 3, skillMoves: 4, injuryHistory: 'Various', strongAttributes: ['Pace', 'Direct running', 'Finishing'], weakAttributes: ['Consistency', 'Decision making'], tacticalRole: 'Inside Forward', adaptabilityScore: 78, mentalStrength: 72, leadership: 65, consistency: 62, preferredFoot: 'Right', height: '185 cm', weight: '80 kg', contract: '2028' },
  { id: 'player-020', name: 'Victor Osimhen', age: 27, position: 'Striker', club: 'Napoli', nationality: 'Nigeria', rating: 8.5, marketValue: '€100M', photo: 'https://images.pexels.com/photos/3621104/pexels-photo-3621104.jpeg?auto=compress&cs=tinysrgb&w=200', goals: 22, assists: 4, appearances: 30, minutesPlayed: 2500, xG: 20.1, xA: 3.5, passAccuracy: 72, dribbleSuccess: 45, sprintSpeed: 91, pressureResistance: 80, workRate: 'High/Medium', weakFoot: 3, skillMoves: 3, injuryHistory: 'Shoulder injury 2022', strongAttributes: ['Finishing', 'Movement', 'Strength'], weakAttributes: ['Link-up play', 'Passing'], tacticalRole: 'Poacher', adaptabilityScore: 82, mentalStrength: 85, leadership: 72, consistency: 80, preferredFoot: 'Right', height: '186 cm', weight: '78 kg', contract: '2026' },
];

const competitions = ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'Champions League'];
const venues = ['Wembley Stadium', 'Santiago Bernabéu', 'Allianz Arena', 'Camp Nou', 'San Siro', 'Parc des Princes', 'Emirates Stadium', 'Anfield', 'Old Trafford', 'Etihad Stadium'];
const referees = ['Michael Oliver', 'Anthony Taylor', 'Mateu Lahoz', 'Slavko Vincic', 'Daniele Orsato', 'Clément Turpin'];
const weathers = ['Clear', 'Cloudy', 'Rainy', 'Windy', 'Cold'];
const formations = ['4-3-3', '4-4-2', '3-5-2', '4-2-3-1', '5-3-2'];

function randomInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function randomDec(min, max, dec = 1) { return parseFloat((Math.random() * (max - min) + min).toFixed(dec)); }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function generateMatches() {
  const matches = [];
  const statuses = ['finished', 'finished', 'finished', 'finished', 'finished', 'live', 'scheduled', 'scheduled'];
  const teamNames = teams.map(t => t.name);

  for (let i = 0; i < 50; i++) {
    const homeIdx = randomInt(0, teamNames.length - 1);
    let awayIdx = randomInt(0, teamNames.length - 1);
    while (awayIdx === homeIdx) awayIdx = randomInt(0, teamNames.length - 1);

    const status = pick(statuses);
    const homeScore = status === 'scheduled' ? 0 : randomInt(0, 4);
    const awayScore = status === 'scheduled' ? 0 : randomInt(0, 3);
    const date = new Date();
    if (status === 'finished') date.setDate(date.getDate() - randomInt(1, 60));
    else if (status === 'scheduled') date.setDate(date.getDate() + randomInt(1, 30));

    matches.push({
      id: `match-${String(i + 1).padStart(3, '0')}`,
      homeTeam: teamNames[homeIdx],
      awayTeam: teamNames[awayIdx],
      homeScore,
      awayScore,
      date: date.toISOString(),
      venue: pick(venues),
      attendance: `${randomInt(25000, 80000).toLocaleString()}`,
      status,
      homeFormation: pick(formations),
      awayFormation: pick(formations),
      competition: pick(competitions),
      referee: pick(referees),
      weather: pick(weathers),
      homeXG: randomDec(0.5, 3.5),
      awayXG: randomDec(0.3, 3.0),
      homePossession: randomInt(35, 65),
      awayPossession: 0,
      homeShots: randomInt(5, 20),
      awayShots: randomInt(3, 18),
      homeShotsOnTarget: randomInt(2, 10),
      awayShotsOnTarget: randomInt(1, 8),
      homeCorners: randomInt(2, 12),
      awayCorners: randomInt(1, 10),
      homeFouls: randomInt(5, 18),
      awayFouls: randomInt(4, 16),
      homeYellowCards: randomInt(0, 4),
      awayYellowCards: randomInt(0, 4),
      homeRedCards: randomInt(0, 1) > 0.8 ? 1 : 0,
      awayRedCards: randomInt(0, 1) > 0.9 ? 1 : 0,
      homePasses: randomInt(300, 700),
      awayPasses: randomInt(280, 680),
      homePassAccuracy: randomInt(70, 92),
      awayPassAccuracy: randomInt(68, 90),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    });

    // Fix possession to sum to ~100
    matches[i].awayPossession = 100 - matches[i].homePossession;
  }

  return matches;
}

function generateNotifications() {
  const types = ['performance', 'market', 'tactical', 'injury', 'transfer', 'system'];
  const priorities = ['low', 'medium', 'high', 'critical'];
  
  const templates = [
    { type: 'performance', title: 'Player Rating Alert', message: 'Vinícius Jr. scored 9.2 rating in latest match' },
    { type: 'market', title: 'Transfer Value Update', message: 'Jude Bellingham market value increased by €10M' },
    { type: 'tactical', title: 'Formation Change', message: 'Manchester City switched to 3-5-2 formation' },
    { type: 'injury', title: 'Injury Alert', message: 'Rodri sustained a knee injury during training' },
    { type: 'transfer', title: 'Transfer Rumor', message: 'FC Barcelona interested in signing Florian Wirtz' },
    { type: 'system', title: 'Data Update', message: 'Player statistics updated for Matchday 25' },
    { type: 'performance', title: 'Hat-trick Alert', message: 'Erling Haaland scored a hat-trick against Chelsea' },
    { type: 'market', title: 'Contract Extension', message: 'Bukayo Saka extended contract until 2029' },
    { type: 'tactical', title: 'Pressing Analysis', message: 'Liverpool PPDA improved to 8.2 this season' },
    { type: 'transfer', title: 'Transfer Confirmed', message: 'New signing expected to join in January window' },
    { type: 'injury', title: 'Return from Injury', message: 'Gavi cleared to return to first team training' },
    { type: 'system', title: 'Report Generated', message: 'Weekly scouting report is ready for review' }
  ];

  return templates.map((t, i) => ({
    id: `notif-${String(i + 1).padStart(3, '0')}`,
    type: t.type,
    title: t.title,
    message: t.message,
    priority: pick(priorities),
    read: i > 4,
    relatedEntityType: t.type === 'performance' || t.type === 'injury' ? 'player' : t.type === 'transfer' ? 'transfer' : t.type === 'tactical' ? 'team' : undefined,
    createdAt: new Date(Date.now() - randomInt(0, 7 * 24 * 60 * 60 * 1000)).toISOString(),
    updatedAt: new Date().toISOString()
  }));
}

async function seed() {
  console.log('🌱 Starting ScoutPro database seed...\n');
  
  const client = new MongoClient(MONGODB_URL);
  
  try {
    await client.connect();
    const db = client.db('scoutpro');
    console.log('✅ Connected to MongoDB\n');

    // Add timestamps to entities
    const now = new Date().toISOString();
    const teamsWithTimestamps = teams.map(t => ({ ...t, createdAt: now, updatedAt: now }));
    const playersWithTimestamps = playerData.map(p => ({ ...p, createdAt: now, updatedAt: now }));
    const matches = generateMatches();
    const notifications = generateNotifications();

    // Clear existing data (drop collections to remove old indexes too)
    console.log('🗑️  Clearing existing data...');
    const collections = ['teams', 'players', 'matches', 'notifications', 'users'];
    for (const col of collections) {
      try {
        await db.collection(col).drop();
      } catch (e) {
        // Collection may not exist yet, that's fine
      }
    }

    // Insert data
    console.log('📊 Inserting teams...');
    await db.collection('teams').insertMany(teamsWithTimestamps);
    console.log(`   ✅ ${teamsWithTimestamps.length} teams inserted`);

    console.log('👤 Inserting players...');
    await db.collection('players').insertMany(playersWithTimestamps);
    console.log(`   ✅ ${playersWithTimestamps.length} players inserted`);

    console.log('⚽ Inserting matches...');
    await db.collection('matches').insertMany(matches);
    console.log(`   ✅ ${matches.length} matches inserted`);

    console.log('🔔 Inserting notifications...');
    await db.collection('notifications').insertMany(notifications);
    console.log(`   ✅ ${notifications.length} notifications inserted`);

    // Create indexes
    console.log('\n📑 Creating indexes...');
    await db.collection('players').createIndex({ name: 'text', club: 'text', nationality: 'text' });
    await db.collection('players').createIndex({ position: 1 });
    await db.collection('players').createIndex({ club: 1 });
    await db.collection('players').createIndex({ id: 1 }, { unique: true });
    
    await db.collection('teams').createIndex({ name: 'text', shortName: 'text' });
    await db.collection('teams').createIndex({ league: 1 });
    await db.collection('teams').createIndex({ id: 1 }, { unique: true });
    
    await db.collection('matches').createIndex({ homeTeam: 1, awayTeam: 1 });
    await db.collection('matches').createIndex({ date: -1 });
    await db.collection('matches').createIndex({ status: 1 });
    await db.collection('matches').createIndex({ id: 1 }, { unique: true });
    
    await db.collection('notifications').createIndex({ createdAt: -1 });
    await db.collection('notifications').createIndex({ id: 1 }, { unique: true });
    
    await db.collection('users').createIndex({ email: 1 }, { unique: true });

    console.log('   ✅ Indexes created\n');

    // Create default admin user
    const bcrypt = require('bcryptjs');
    const hashedPassword = await bcrypt.hash('admin123', 10);
    await db.collection('users').insertOne({
      id: 'user-admin',
      email: 'admin@scoutpro.com',
      name: 'Admin',
      password: hashedPassword,
      role: 'admin',
      team: 'ScoutPro',
      permissions: [
        'view_players', 'view_matches', 'create_reports', 'export_data',
        'manage_users', 'manage_system', 'manage_data', 'delete_data',
        'view_analytics', 'manage_roles', 'ml_access', 'video_analysis'
      ],
      createdAt: now,
      updatedAt: now
    });
    console.log('👤 Default admin user created: admin@scoutpro.com / admin123\n');

    console.log('✨ Database seed completed successfully!');
    console.log(`   Teams: ${teamsWithTimestamps.length}`);
    console.log(`   Players: ${playersWithTimestamps.length}`);
    console.log(`   Matches: ${matches.length}`);
    console.log(`   Notifications: ${notifications.length}`);
    console.log(`   Users: 1 (admin)\n`);

  } catch (error) {
    console.error('❌ Seed failed:', error);
    process.exit(1);
  } finally {
    await client.close();
  }
}

seed();
