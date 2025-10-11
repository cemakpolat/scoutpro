import { Video, VideoAnnotation, VideoPlaylist, VideoClip, VideoFilter } from '../types/video';
import { mockVideos, mockPlaylists } from '../data/mockVideos';

class VideoService {
  private videos: Video[] = [...mockVideos];
  private playlists: VideoPlaylist[] = [...mockPlaylists];
  private clips: VideoClip[] = [];

  // Get all videos
  getVideos(filter?: VideoFilter): Video[] {
    let filtered = [...this.videos];

    if (filter) {
      if (filter.player) {
        filtered = filtered.filter(v =>
          v.player?.name.toLowerCase().includes(filter.player!.toLowerCase())
        );
      }

      if (filter.match) {
        filtered = filtered.filter(v =>
          v.match?.homeTeam.toLowerCase().includes(filter.match!.toLowerCase()) ||
          v.match?.awayTeam.toLowerCase().includes(filter.match!.toLowerCase())
        );
      }

      if (filter.competition) {
        filtered = filtered.filter(v =>
          v.match?.competition.toLowerCase().includes(filter.competition!.toLowerCase())
        );
      }

      if (filter.tags && filter.tags.length > 0) {
        filtered = filtered.filter(v =>
          filter.tags!.some(tag => v.tags.includes(tag))
        );
      }

      if (filter.source) {
        filtered = filtered.filter(v => v.source === filter.source);
      }

      if (filter.hasAnnotations !== undefined) {
        filtered = filtered.filter(v =>
          filter.hasAnnotations ? v.annotations.length > 0 : v.annotations.length === 0
        );
      }

      if (filter.dateFrom) {
        filtered = filtered.filter(v =>
          v.match?.date && v.match.date >= filter.dateFrom!
        );
      }

      if (filter.dateTo) {
        filtered = filtered.filter(v =>
          v.match?.date && v.match.date <= filter.dateTo!
        );
      }
    }

    return filtered;
  }

  // Get video by ID
  getVideoById(id: string): Video | undefined {
    return this.videos.find(v => v.id === id);
  }

  // Add new video
  addVideo(video: Omit<Video, 'id' | 'uploadedAt'>): Video {
    const newVideo: Video = {
      ...video,
      id: `v${Date.now()}`,
      uploadedAt: new Date().toISOString(),
      annotations: []
    };
    this.videos.push(newVideo);
    return newVideo;
  }

  // Update video
  updateVideo(id: string, updates: Partial<Video>): Video | null {
    const index = this.videos.findIndex(v => v.id === id);
    if (index === -1) return null;

    this.videos[index] = { ...this.videos[index], ...updates };
    return this.videos[index];
  }

  // Delete video
  deleteVideo(id: string): boolean {
    const index = this.videos.findIndex(v => v.id === id);
    if (index === -1) return false;

    this.videos.splice(index, 1);
    return true;
  }

  // Add annotation to video
  addAnnotation(videoId: string, annotation: Omit<VideoAnnotation, 'id' | 'createdAt'>): VideoAnnotation | null {
    const video = this.getVideoById(videoId);
    if (!video) return null;

    const newAnnotation: VideoAnnotation = {
      ...annotation,
      id: `a${Date.now()}`,
      createdAt: new Date().toISOString()
    };

    video.annotations.push(newAnnotation);
    return newAnnotation;
  }

  // Update annotation
  updateAnnotation(videoId: string, annotationId: string, updates: Partial<VideoAnnotation>): VideoAnnotation | null {
    const video = this.getVideoById(videoId);
    if (!video) return null;

    const index = video.annotations.findIndex(a => a.id === annotationId);
    if (index === -1) return null;

    video.annotations[index] = { ...video.annotations[index], ...updates };
    return video.annotations[index];
  }

  // Delete annotation
  deleteAnnotation(videoId: string, annotationId: string): boolean {
    const video = this.getVideoById(videoId);
    if (!video) return false;

    const index = video.annotations.findIndex(a => a.id === annotationId);
    if (index === -1) return false;

    video.annotations.splice(index, 1);
    return true;
  }

  // Get all playlists
  getPlaylists(): VideoPlaylist[] {
    return [...this.playlists];
  }

  // Get playlist by ID
  getPlaylistById(id: string): VideoPlaylist | undefined {
    return this.playlists.find(p => p.id === id);
  }

  // Create playlist
  createPlaylist(playlist: Omit<VideoPlaylist, 'id' | 'createdAt' | 'updatedAt'>): VideoPlaylist {
    const newPlaylist: VideoPlaylist = {
      ...playlist,
      id: `pl${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    this.playlists.push(newPlaylist);
    return newPlaylist;
  }

  // Add video to playlist
  addVideoToPlaylist(playlistId: string, videoId: string): boolean {
    const playlist = this.getPlaylistById(playlistId);
    if (!playlist || playlist.videoIds.includes(videoId)) return false;

    playlist.videoIds.push(videoId);
    playlist.updatedAt = new Date().toISOString();
    return true;
  }

  // Remove video from playlist
  removeVideoFromPlaylist(playlistId: string, videoId: string): boolean {
    const playlist = this.getPlaylistById(playlistId);
    if (!playlist) return false;

    const index = playlist.videoIds.indexOf(videoId);
    if (index === -1) return false;

    playlist.videoIds.splice(index, 1);
    playlist.updatedAt = new Date().toISOString();
    return true;
  }

  // Delete playlist
  deletePlaylist(id: string): boolean {
    const index = this.playlists.findIndex(p => p.id === id);
    if (index === -1) return false;

    this.playlists.splice(index, 1);
    return true;
  }

  // Create video clip
  createClip(clip: Omit<VideoClip, 'id' | 'createdAt'>): VideoClip {
    const newClip: VideoClip = {
      ...clip,
      id: `c${Date.now()}`,
      createdAt: new Date().toISOString()
    };
    this.clips.push(newClip);
    return newClip;
  }

  // Get clips for a video
  getClipsForVideo(videoId: string): VideoClip[] {
    return this.clips.filter(c => c.videoId === videoId);
  }

  // Get all unique tags
  getAllTags(): string[] {
    const tags = new Set<string>();
    this.videos.forEach(video => {
      video.tags.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }

  // Get all unique players
  getAllPlayers(): string[] {
    const players = new Set<string>();
    this.videos.forEach(video => {
      if (video.player?.name) {
        players.add(video.player.name);
      }
    });
    return Array.from(players).sort();
  }

  // Get all unique competitions
  getAllCompetitions(): string[] {
    const competitions = new Set<string>();
    this.videos.forEach(video => {
      if (video.match?.competition) {
        competitions.add(video.match.competition);
      }
    });
    return Array.from(competitions).sort();
  }

  // Search videos
  searchVideos(query: string): Video[] {
    const lowerQuery = query.toLowerCase();
    return this.videos.filter(video =>
      video.title.toLowerCase().includes(lowerQuery) ||
      video.description?.toLowerCase().includes(lowerQuery) ||
      video.player?.name.toLowerCase().includes(lowerQuery) ||
      video.match?.homeTeam.toLowerCase().includes(lowerQuery) ||
      video.match?.awayTeam.toLowerCase().includes(lowerQuery) ||
      video.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    );
  }
}

export const videoService = new VideoService();
export default videoService;
