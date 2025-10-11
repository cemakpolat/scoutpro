// Video Analysis Types

export type VideoSource = 'youtube' | 'vimeo' | 'direct';

export type AnnotationType =
  | 'goal'
  | 'assist'
  | 'shot'
  | 'pass'
  | 'dribble'
  | 'tackle'
  | 'save'
  | 'movement'
  | 'positioning'
  | 'highlight'
  | 'concern'
  | 'note';

export interface VideoAnnotation {
  id: string;
  timestamp: number; // in seconds
  type: AnnotationType;
  note: string;
  rating?: number; // 1-10
  createdBy: string;
  createdAt: string;
}

export interface VideoPlayerInfo {
  id: string;
  name: string;
  position?: string;
  photo?: string;
}

export interface VideoMatchInfo {
  id: string;
  homeTeam: string;
  awayTeam: string;
  date: string;
  competition: string;
  score?: string;
}

export interface VideoStats {
  goals?: number;
  assists?: number;
  shots?: number;
  shotsOnTarget?: number;
  touches?: number;
  passAccuracy?: number;
  dribblesCompleted?: number;
  tackles?: number;
  interceptions?: number;
}

export interface Video {
  id: string;
  title: string;
  url: string;
  source: VideoSource;
  thumbnail?: string;
  duration?: string;
  player?: VideoPlayerInfo;
  match?: VideoMatchInfo;
  annotations: VideoAnnotation[];
  stats?: VideoStats;
  tags: string[];
  uploadedBy: string;
  uploadedAt: string;
  description?: string;
  isPublic?: boolean;
}

export interface VideoPlaylist {
  id: string;
  name: string;
  description?: string;
  videoIds: string[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
}

export interface VideoClip {
  id: string;
  videoId: string;
  title: string;
  startTime: number;
  endTime: number;
  description?: string;
  tags: string[];
  createdBy: string;
  createdAt: string;
}

export interface VideoFilter {
  player?: string;
  match?: string;
  competition?: string;
  dateFrom?: string;
  dateTo?: string;
  tags?: string[];
  source?: VideoSource;
  hasAnnotations?: boolean;
}
