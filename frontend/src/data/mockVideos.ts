import { Video, VideoPlaylist } from '../types/video';

export const mockVideos: Video[] = [
  {
    id: 'v1',
    title: 'Erling Haaland vs Arsenal - Complete Performance Analysis',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', // Replace with actual football video ID
    source: 'youtube',
    thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
    duration: '8:42',
    player: {
      id: 'p1',
      name: 'Erling Haaland',
      position: 'ST',
      photo: 'https://media.api-sports.io/football/players/1100.png'
    },
    match: {
      id: 'm1',
      homeTeam: 'Manchester City',
      awayTeam: 'Arsenal',
      date: '2024-03-31',
      competition: 'Premier League',
      score: '4-1'
    },
    annotations: [
      {
        id: 'a1',
        timestamp: 45,
        type: 'goal',
        note: 'Excellent finishing - powerful left foot strike into top corner. Great composure under pressure.',
        rating: 9,
        createdBy: 'scout@scoutpro.com',
        createdAt: '2024-04-01T10:30:00Z'
      },
      {
        id: 'a2',
        timestamp: 125,
        type: 'movement',
        note: 'Intelligent off-ball movement to create space between center backs. Dragging defenders out of position.',
        rating: 8,
        createdBy: 'scout@scoutpro.com',
        createdAt: '2024-04-01T10:32:00Z'
      },
      {
        id: 'a3',
        timestamp: 267,
        type: 'goal',
        note: 'Clinical header from corner. Perfect timing of run and powerful connection.',
        rating: 9,
        createdBy: 'analyst@scoutpro.com',
        createdAt: '2024-04-01T11:15:00Z'
      }
    ],
    stats: {
      goals: 2,
      assists: 1,
      shots: 5,
      shotsOnTarget: 4,
      touches: 42,
      passAccuracy: 85,
      dribblesCompleted: 3
    },
    tags: ['clinical-finishing', 'positioning', 'off-ball-movement', 'aerial-ability'],
    uploadedBy: 'scout@scoutpro.com',
    uploadedAt: '2024-04-01T10:00:00Z',
    description: 'Complete match performance analysis of Haaland against Arsenal. Shows his movement, finishing, and tactical awareness.',
    isPublic: true
  },
  {
    id: 'v2',
    title: 'Kylian Mbappé - Speed & Dribbling Compilation',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    source: 'youtube',
    thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
    duration: '6:15',
    player: {
      id: 'p2',
      name: 'Kylian Mbappé',
      position: 'LW/ST',
      photo: 'https://media.api-sports.io/football/players/1100.png'
    },
    match: {
      id: 'm2',
      homeTeam: 'Paris Saint-Germain',
      awayTeam: 'Barcelona',
      date: '2024-04-10',
      competition: 'UEFA Champions League',
      score: '3-2'
    },
    annotations: [
      {
        id: 'a4',
        timestamp: 32,
        type: 'dribble',
        note: 'Explosive acceleration past two defenders. Elite change of pace.',
        rating: 9,
        createdBy: 'scout@scoutpro.com',
        createdAt: '2024-04-11T09:20:00Z'
      },
      {
        id: 'a5',
        timestamp: 178,
        type: 'shot',
        note: 'Powerful shot from outside the box. Technique and power combined.',
        rating: 8,
        createdBy: 'scout@scoutpro.com',
        createdAt: '2024-04-11T09:25:00Z'
      }
    ],
    stats: {
      goals: 1,
      assists: 2,
      shots: 7,
      shotsOnTarget: 5,
      touches: 68,
      passAccuracy: 88,
      dribblesCompleted: 8
    },
    tags: ['pace', 'dribbling', 'counter-attack', 'versatility'],
    uploadedBy: 'scout@scoutpro.com',
    uploadedAt: '2024-04-11T09:00:00Z',
    description: 'Highlights of Mbappé\'s pace and dribbling ability against Barcelona.',
    isPublic: true
  },
  {
    id: 'v3',
    title: 'Pedri - Playmaking Masterclass vs Real Madrid',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    source: 'youtube',
    thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
    duration: '7:30',
    player: {
      id: 'p3',
      name: 'Pedri',
      position: 'CM',
      photo: 'https://media.api-sports.io/football/players/1100.png'
    },
    match: {
      id: 'm3',
      homeTeam: 'Barcelona',
      awayTeam: 'Real Madrid',
      date: '2024-04-21',
      competition: 'La Liga',
      score: '2-1'
    },
    annotations: [
      {
        id: 'a6',
        timestamp: 89,
        type: 'pass',
        note: 'Perfect through ball splitting the defense. Vision and execution at highest level.',
        rating: 9,
        createdBy: 'analyst@scoutpro.com',
        createdAt: '2024-04-22T14:10:00Z'
      },
      {
        id: 'a7',
        timestamp: 234,
        type: 'positioning',
        note: 'Excellent positioning to receive in tight spaces. Always available for pass.',
        rating: 8,
        createdBy: 'analyst@scoutpro.com',
        createdAt: '2024-04-22T14:15:00Z'
      },
      {
        id: 'a8',
        timestamp: 412,
        type: 'assist',
        note: 'Key pass leading to goal. Perfect weight and timing.',
        rating: 9,
        createdBy: 'analyst@scoutpro.com',
        createdAt: '2024-04-22T14:20:00Z'
      }
    ],
    stats: {
      goals: 0,
      assists: 2,
      shots: 2,
      shotsOnTarget: 1,
      touches: 112,
      passAccuracy: 94,
      dribblesCompleted: 5
    },
    tags: ['vision', 'passing', 'ball-retention', 'creativity'],
    uploadedBy: 'analyst@scoutpro.com',
    uploadedAt: '2024-04-22T14:00:00Z',
    description: 'Complete midfield performance showing Pedri\'s vision and passing range.',
    isPublic: false
  },
  {
    id: 'v4',
    title: 'Jude Bellingham - Box-to-Box Performance',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    source: 'youtube',
    thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
    duration: '9:12',
    player: {
      id: 'p4',
      name: 'Jude Bellingham',
      position: 'CM',
      photo: 'https://media.api-sports.io/football/players/1100.png'
    },
    match: {
      id: 'm4',
      homeTeam: 'Real Madrid',
      awayTeam: 'Atletico Madrid',
      date: '2024-04-28',
      competition: 'La Liga',
      score: '3-1'
    },
    annotations: [
      {
        id: 'a9',
        timestamp: 56,
        type: 'goal',
        note: 'Late run into box perfectly timed. Composure to finish under pressure.',
        rating: 9,
        createdBy: 'scout@scoutpro.com',
        createdAt: '2024-04-29T10:05:00Z'
      },
      {
        id: 'a10',
        timestamp: 203,
        type: 'tackle',
        note: 'Important defensive contribution. Reading of the game excellent.',
        rating: 7,
        createdBy: 'scout@scoutpro.com',
        createdAt: '2024-04-29T10:08:00Z'
      }
    ],
    stats: {
      goals: 1,
      assists: 1,
      shots: 4,
      shotsOnTarget: 3,
      touches: 95,
      passAccuracy: 89,
      tackles: 4,
      interceptions: 2
    },
    tags: ['box-to-box', 'versatility', 'leadership', 'goal-threat'],
    uploadedBy: 'scout@scoutpro.com',
    uploadedAt: '2024-04-29T10:00:00Z',
    description: 'Bellingham showing his complete game - attacking, defending, and leadership.',
    isPublic: true
  },
  {
    id: 'v5',
    title: 'Virgil van Dijk - Defensive Masterclass',
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    source: 'youtube',
    thumbnail: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
    duration: '5:45',
    player: {
      id: 'p5',
      name: 'Virgil van Dijk',
      position: 'CB',
      photo: 'https://media.api-sports.io/football/players/1100.png'
    },
    match: {
      id: 'm5',
      homeTeam: 'Liverpool',
      awayTeam: 'Manchester United',
      date: '2024-05-05',
      competition: 'Premier League',
      score: '2-0'
    },
    annotations: [
      {
        id: 'a11',
        timestamp: 145,
        type: 'tackle',
        note: 'Perfectly timed tackle to stop counter-attack. Calmness under pressure.',
        rating: 9,
        createdBy: 'analyst@scoutpro.com',
        createdAt: '2024-05-06T11:30:00Z'
      },
      {
        id: 'a12',
        timestamp: 298,
        type: 'positioning',
        note: 'Excellent reading of through ball. Anticipation and recovery speed.',
        rating: 9,
        createdBy: 'analyst@scoutpro.com',
        createdAt: '2024-05-06T11:35:00Z'
      }
    ],
    stats: {
      goals: 0,
      assists: 0,
      shots: 1,
      shotsOnTarget: 0,
      touches: 87,
      passAccuracy: 92,
      tackles: 3,
      interceptions: 5
    },
    tags: ['defending', 'aerial-duels', 'leadership', 'distribution'],
    uploadedBy: 'analyst@scoutpro.com',
    uploadedAt: '2024-05-06T11:00:00Z',
    description: 'Van Dijk\'s defensive performance analysis - positioning, tackling, and leadership.',
    isPublic: true
  }
];

export const mockPlaylists: VideoPlaylist[] = [
  {
    id: 'pl1',
    name: 'Elite Strikers 2024',
    description: 'Top striker performances from this season',
    videoIds: ['v1', 'v2'],
    createdBy: 'scout@scoutpro.com',
    createdAt: '2024-04-01T10:00:00Z',
    updatedAt: '2024-04-11T09:00:00Z',
    isPublic: true
  },
  {
    id: 'pl2',
    name: 'Midfield Maestros',
    description: 'Creative midfielders and playmakers',
    videoIds: ['v3', 'v4'],
    createdBy: 'analyst@scoutpro.com',
    createdAt: '2024-04-22T14:00:00Z',
    updatedAt: '2024-04-29T10:00:00Z',
    isPublic: false
  },
  {
    id: 'pl3',
    name: 'Defensive Excellence',
    description: 'Top defensive performances',
    videoIds: ['v5'],
    createdBy: 'analyst@scoutpro.com',
    createdAt: '2024-05-06T11:00:00Z',
    updatedAt: '2024-05-06T11:00:00Z',
    isPublic: true
  }
];
