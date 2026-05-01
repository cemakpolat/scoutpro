import React, { useState, useRef, useEffect } from 'react';
import YouTube, { YouTubeProps } from 'react-youtube';
import {
  Play, Pause, SkipBack, SkipForward, Volume2, VolumeX,
  Maximize, MessageSquare, Plus, Save, Share2, Download,
  Film, Clock, Tag, Star, User, Calendar, Grid, List,
  Search, Filter, Trash2, Edit2, ChevronDown, ChevronUp,
  PlayCircle, Folder, X, Upload, Camera, Loader2, BarChart2
} from 'lucide-react';
import { Video, VideoAnnotation, AnnotationType, VideoPlaylist } from '../types/video';
import { exportService } from '../services/exportService';
import apiService from '../services/api';

type VideoFormState = {
  url: string;
  title: string;
  playerName: string;
  matchDetails: string;
  tags: string;
  description: string;
};

const emptyVideoForm: VideoFormState = {
  url: '',
  title: '',
  playerName: '',
  matchDetails: '',
  tags: '',
  description: ''
};

const toNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const parsed = Number(value.replace(/[^\d.]/g, ''));
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

const normalizeVideoAnnotation = (annotation: any): VideoAnnotation => ({
  id: String(annotation.id || annotation._id || crypto.randomUUID()),
  timestamp: toNumber(annotation.timestamp) ?? 0,
  type: (annotation.type || 'note') as AnnotationType,
  note: annotation.note || annotation.text || '',
  rating: toNumber(annotation.rating),
  createdBy: annotation.createdBy || annotation.author || 'scoutpro.user',
  createdAt: annotation.createdAt || new Date().toISOString(),
});

const normalizeVideo = (video: any): Video => {
  const annotations = Array.isArray(video.annotations)
    ? video.annotations.map(normalizeVideoAnnotation)
    : [];

  const playerName = video.player?.name || video.playerName || video.metadata?.playerName || '';
  const matchInfo = video.match || video.metadata?.match || null;
  const matchTitle = typeof video.matchTitle === 'string' ? video.matchTitle : undefined;

  return {
    id: String(video.id || video._id || crypto.randomUUID()),
    title: video.title || 'Untitled Video',
    url: video.url || video.streamUrl || '',
    source: video.source || 'direct',
    thumbnail: video.thumbnail || video.thumbnailUrl || undefined,
    duration: typeof video.duration === 'string'
      ? video.duration
      : `${Math.floor((toNumber(video.duration) ?? 0) / 60)}:${String(Math.floor((toNumber(video.duration) ?? 0) % 60)).padStart(2, '0')}`,
    player: playerName
      ? {
          id: String(video.player?.id || video.playerId || playerName),
          name: playerName,
          position: video.player?.position || video.metadata?.position,
          photo: video.player?.photo,
        }
      : undefined,
    match: matchInfo || matchTitle
      ? {
          id: String(matchInfo?.id || video.matchId || matchTitle || 'match'),
          homeTeam: matchInfo?.homeTeam || matchTitle?.split(' vs ')[0] || 'Home',
          awayTeam: matchInfo?.awayTeam || matchTitle?.split(' vs ')[1] || 'Away',
          date: matchInfo?.date || video.uploadedAt || new Date().toISOString(),
          competition: matchInfo?.competition || video.metadata?.competition || 'ScoutPro',
          score: matchInfo?.score,
        }
      : undefined,
    annotations,
    stats: video.stats || video.metadata?.stats,
    tags: Array.isArray(video.tags) ? video.tags.filter(Boolean) : [],
    uploadedBy: video.uploadedBy || 'scoutpro.user',
    uploadedAt: video.uploadedAt || new Date().toISOString(),
    description: video.description || undefined,
    isPublic: Boolean(video.isPublic),
  };
};

const buildFilterOptions = (videos: Video[]) => ({
  tags: Array.from(new Set(videos.flatMap((video) => video.tags))).sort(),
  players: Array.from(new Set(videos.map((video) => video.player?.name).filter(Boolean) as string[])).sort(),
  competitions: Array.from(new Set(videos.map((video) => video.match?.competition).filter(Boolean) as string[])).sort(),
});

const parseMatchDetails = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) return undefined;

  const [teamsPart, scorePart] = trimmed.split('(');
  const [homeTeam, awayTeam] = teamsPart.split(' vs ').map((team) => team.trim()).filter(Boolean);

  if (!homeTeam && !awayTeam) return undefined;

  return {
    homeTeam: homeTeam || 'Home',
    awayTeam: awayTeam || 'Away',
    score: scorePart ? scorePart.replace(')', '').trim() : undefined,
    date: new Date().toISOString(),
    competition: 'ScoutPro Library'
  };
};

const VIDEO_PLACEHOLDER = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360" fill="none"><rect width="640" height="360" fill="#0f172a"/><rect x="24" y="24" width="592" height="312" rx="24" fill="#1e293b" stroke="#334155"/><circle cx="320" cy="180" r="44" fill="#f97316"/><path d="M306 154v52l42-26-42-26Z" fill="white"/><text x="320" y="246" text-anchor="middle" fill="#cbd5e1" font-family="Arial, sans-serif" font-size="24">ScoutPro Video</text></svg>`
)}`;

const VideoAnalysis: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [allVideos, setAllVideos] = useState<Video[]>([]);
  const [playlists, setPlaylists] = useState<VideoPlaylist[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [volume, setVolume] = useState(100);
  const [isMuted, setIsMuted] = useState(false);
  const [showAnnotationForm, setShowAnnotationForm] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [editingAnnotation, setEditingAnnotation] = useState<VideoAnnotation | null>(null);
  const [showPlaylistModal, setShowPlaylistModal] = useState(false);
  const [selectedAnnotations, setSelectedAnnotations] = useState<string[]>([]);
  const [showAddVideoModal, setShowAddVideoModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submittingVideo, setSubmittingVideo] = useState(false);
  const [videoError, setVideoError] = useState('');
  const [videoForm, setVideoForm] = useState<VideoFormState>(emptyVideoForm);

  // Upload panel state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadMatchId, setUploadMatchId] = useState('');
  const [uploadTeamId, setUploadTeamId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [analyzingVideos, setAnalyzingVideos] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filter states
  const [filterPlayer, setFilterPlayer] = useState('');
  const [filterCompetition, setFilterCompetition] = useState('');
  const [filterTags, setFilterTags] = useState<string[]>([]);

  // Annotation form state
  const [newAnnotation, setNewAnnotation] = useState({
    type: 'note' as AnnotationType,
    note: '',
    rating: 5
  });

  const playerRef = useRef<any>(null);

  const refreshVideos = async (selectedVideoId?: string) => {
    setLoading(true);
    setVideoError('');

    try {
      const res = await apiService.listVideos();
      const normalizedVideos = (res.data || []).map(normalizeVideo);
      setAllVideos(normalizedVideos);
      setVideos(normalizedVideos);

      if (selectedVideoId) {
        const freshVideo = normalizedVideos.find((video) => video.id === selectedVideoId) || null;
        setSelectedVideo(freshVideo);
      }
    } catch (error) {
      console.error('Failed to load videos:', error);
      setAllVideos([]);
      setVideos([]);
      setVideoError('Video library is unavailable right now.');
      if (selectedVideoId) {
        setSelectedVideo(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshVideos();
  }, []);

  const extractYouTubeId = (url: string): string | null => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
  };

  const onPlayerReady: YouTubeProps['onReady'] = (event) => {
    playerRef.current = event.target;
    setDuration(event.target.getDuration());
  };

  const onStateChange: YouTubeProps['onStateChange'] = (event) => {
    setIsPlaying(event.data === 1);
  };

  const handlePlayPause = () => {
    if (playerRef.current) {
      if (isPlaying) {
        playerRef.current.pauseVideo();
      } else {
        playerRef.current.playVideo();
      }
    }
  };

  const handleSeek = (seconds: number) => {
    if (playerRef.current) {
      const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
      playerRef.current.seekTo(newTime);
      setCurrentTime(newTime);
    }
  };

  const handleSpeedChange = () => {
    const speeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2];
    const currentIndex = speeds.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % speeds.length;
    const newSpeed = speeds[nextIndex];
    setPlaybackSpeed(newSpeed);
    if (playerRef.current) {
      playerRef.current.setPlaybackRate(newSpeed);
    }
  };

  const handleVolumeToggle = () => {
    if (playerRef.current) {
      if (isMuted) {
        playerRef.current.unMute();
        setIsMuted(false);
      } else {
        playerRef.current.mute();
        setIsMuted(true);
      }
    }
  };

  const jumpToAnnotation = (timestamp: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(timestamp);
      setCurrentTime(timestamp);
      playerRef.current.playVideo();
    }
  };

  const handleAddAnnotation = () => {
    if (!selectedVideo) return;

    apiService.createVideoAnnotation(selectedVideo.id, {
      timestamp: Math.floor(currentTime),
      type: newAnnotation.type,
      text: newAnnotation.note,
      rating: newAnnotation.rating,
      author: 'current_user@scoutpro.com'
    }).then(() => refreshVideos(selectedVideo.id))
      .then(() => {
        setShowAnnotationForm(false);
        setNewAnnotation({ type: 'note', note: '', rating: 5 });
      })
      .catch((error) => {
        console.error('Failed to create annotation:', error);
        alert('Annotation could not be saved.');
      });
  };

  const handleUpdateAnnotation = () => {
    if (!selectedVideo || !editingAnnotation) return;

    apiService.updateVideoAnnotation(selectedVideo.id, editingAnnotation.id, {
      type: newAnnotation.type,
      text: newAnnotation.note,
      rating: newAnnotation.rating
    }).then(() => refreshVideos(selectedVideo.id))
      .then(() => {
        setEditingAnnotation(null);
        setShowAnnotationForm(false);
        setNewAnnotation({ type: 'note', note: '', rating: 5 });
      })
      .catch((error) => {
        console.error('Failed to update annotation:', error);
        alert('Annotation could not be updated.');
      });
  };

  const handleDeleteAnnotation = (annotationId: string) => {
    if (!selectedVideo) return;

    if (confirm('Delete this annotation?')) {
      apiService.deleteVideoAnnotation(selectedVideo.id, annotationId)
        .then(() => refreshVideos(selectedVideo.id))
        .catch((error) => {
          console.error('Failed to delete annotation:', error);
          alert('Annotation could not be deleted.');
        });
    }
  };

  const handleQuickAnnotation = (type: AnnotationType) => {
    if (!selectedVideo) return;

    apiService.createVideoAnnotation(selectedVideo.id, {
      timestamp: Math.floor(currentTime),
      type,
      text: `${type.charAt(0).toUpperCase() + type.slice(1)} at ${formatTime(currentTime)}`,
      author: 'current_user@scoutpro.com'
    }).then(() => refreshVideos(selectedVideo.id))
      .catch((error) => {
        console.error('Failed to create quick annotation:', error);
        alert('Annotation could not be saved.');
      });
  };

  const handleEditAnnotation = (annotation: VideoAnnotation) => {
    setEditingAnnotation(annotation);
    setNewAnnotation({
      type: annotation.type,
      note: annotation.note,
      rating: annotation.rating || 5
    });
    setShowAnnotationForm(true);
  };

  const handleExportAnalysis = async () => {
    if (!selectedVideo) return;

    const exportData = selectedVideo.annotations.map(ann => ({
      Timestamp: formatTime(ann.timestamp),
      Type: ann.type,
      Note: ann.note,
      Rating: ann.rating || '-',
      'Created By': ann.createdBy,
    }));

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `video_analysis_${selectedVideo.player?.name.replace(/\s+/g, '_')}_${Date.now()}.pdf`,
        data: exportData,
        header: `Video Analysis: ${selectedVideo.title}`,
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('Video analysis exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  const resetVideoModal = () => {
    setShowAddVideoModal(false);
    setSubmittingVideo(false);
    setVideoForm(emptyVideoForm);
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setUploadProgress(0);
    const formData = new FormData();
    formData.append('file', uploadFile);
    if (uploadMatchId.trim()) formData.append('match_id', uploadMatchId.trim());
    if (uploadTeamId.trim()) formData.append('team_id', uploadTeamId.trim());
    try {
      const res = await (apiService as any).uploadVideoWithProgress(formData, (pct: number) => setUploadProgress(pct));
      if (res.success) {
        await refreshVideos();
        setShowUploadModal(false);
        setUploadFile(null);
        setUploadMatchId('');
        setUploadTeamId('');
      } else {
        alert('Upload failed: ' + (res.error?.message ?? 'Unknown error'));
      }
    } catch {
      alert('Upload failed.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleAnalyzeVideo = async (e: React.MouseEvent, videoId: string) => {
    e.stopPropagation();
    setAnalyzingVideos(prev => new Set(prev).add(videoId));
    try {
      await apiService.analyzeVideo(videoId);
      await refreshVideos();
    } catch {
      alert('Analysis request failed.');
    } finally {
      setAnalyzingVideos(prev => { const s = new Set(prev); s.delete(videoId); return s; });
    }
  };

  const handleDeleteVideo = async (e: React.MouseEvent, videoId: string) => {
    e.stopPropagation();
    if (!confirm('Delete this video? This cannot be undone.')) return;
    try {
      await apiService.deleteVideo(videoId);
      await refreshVideos();
      if (selectedVideo?.id === videoId) setSelectedVideo(null);
    } catch {
      alert('Delete failed.');
    }
  };

  const handlePlayStream = (e: React.MouseEvent, videoId: string) => {
    e.stopPropagation();
    const streamUrl = apiService.getVideoStreamUrl(videoId);
    window.open(streamUrl, '_blank', 'noopener,noreferrer');
  };

  const handleCreateVideo = async () => {
    if (!videoForm.url.trim() || !videoForm.title.trim()) {
      alert('Video URL and title are required.');
      return;
    }

    setSubmittingVideo(true);

    try {
      const payload = {
        url: videoForm.url.trim(),
        title: videoForm.title.trim(),
        description: videoForm.description.trim(),
        uploadedBy: 'current_user@scoutpro.com',
        player: videoForm.playerName.trim()
          ? { name: videoForm.playerName.trim() }
          : undefined,
        match: parseMatchDetails(videoForm.matchDetails),
        tags: videoForm.tags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean),
      };

      const response = await apiService.createVideoEntry(payload);
      const createdVideo = normalizeVideo(response.data);
      await refreshVideos(createdVideo.id);
      setSelectedVideo(createdVideo);
      resetVideoModal();
    } catch (error) {
      console.error('Failed to create video:', error);
      alert('Video could not be added.');
      setSubmittingVideo(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const applyFilters = () => {
    const filtered = allVideos.filter((video) => {
      const matchesPlayer = !filterPlayer || video.player?.name === filterPlayer;
      const matchesCompetition = !filterCompetition || video.match?.competition === filterCompetition;
      const matchesTags = filterTags.length === 0 || filterTags.some((tag) => video.tags.includes(tag));
      return matchesPlayer && matchesCompetition && matchesTags;
    });
    setVideos(filtered);
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      const lowerQuery = searchQuery.toLowerCase();
      setVideos(allVideos.filter((video) =>
        video.title.toLowerCase().includes(lowerQuery) ||
        video.description?.toLowerCase().includes(lowerQuery) ||
        video.player?.name.toLowerCase().includes(lowerQuery) ||
        video.match?.homeTeam.toLowerCase().includes(lowerQuery) ||
        video.match?.awayTeam.toLowerCase().includes(lowerQuery) ||
        video.tags.some((tag) => tag.toLowerCase().includes(lowerQuery))
      ));
    } else {
      setVideos(allVideos);
    }
  };

  useEffect(() => {
    handleSearch();
  }, [searchQuery, allVideos]);

  // Update current time periodically
  useEffect(() => {
    if (!isPlaying || !playerRef.current) return;

    const interval = setInterval(() => {
      if (playerRef.current) {
        setCurrentTime(playerRef.current.getCurrentTime());
      }
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying]);

  const annotationTypeColors: Record<AnnotationType, string> = {
    goal: 'bg-green-600',
    assist: 'bg-blue-600',
    shot: 'bg-yellow-600',
    pass: 'bg-purple-600',
    dribble: 'bg-pink-600',
    tackle: 'bg-red-600',
    save: 'bg-orange-600',
    movement: 'bg-indigo-600',
    positioning: 'bg-cyan-600',
    highlight: 'bg-emerald-600',
    concern: 'bg-rose-600',
    note: 'bg-slate-600'
  };

  const { tags: allTags, players: allPlayers, competitions: allCompetitions } = buildFilterOptions(allVideos);

  if (selectedVideo) {
    const videoId = extractYouTubeId(selectedVideo.url);

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => {
                setSelectedVideo(null);
                setCurrentTime(0);
                setIsPlaying(false);
              }}
              className="text-green-400 hover:text-green-300 mb-2 flex items-center"
            >
              ← Back to Library
            </button>
            <h1 className="text-2xl font-bold">{selectedVideo.title}</h1>
            <p className="text-slate-400">
              {selectedVideo.player?.name} • {selectedVideo.match?.homeTeam} vs {selectedVideo.match?.awayTeam}
              {selectedVideo.match?.score && <span> ({selectedVideo.match.score})</span>}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleExportAnalysis}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
            <button
              onClick={() => setShowShareModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              <Share2 className="h-4 w-4" />
              <span>Share</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Player Section */}
          <div className="lg:col-span-2 space-y-4">
            {/* Video Player */}
            <div className="bg-slate-800 rounded-xl overflow-hidden">
              {videoId ? (
                <YouTube
                  videoId={videoId}
                  onReady={onPlayerReady}
                  onStateChange={onStateChange}
                  opts={{
                    width: '100%',
                    height: '480',
                    playerVars: {
                      autoplay: 0,
                      controls: 1,
                      modestbranding: 1,
                      rel: 0
                    }
                  }}
                />
              ) : (
                <div className="h-96 flex items-center justify-center bg-slate-700">
                  <p className="text-slate-400">Invalid video URL</p>
                </div>
              )}
            </div>

            {/* Custom Controls */}
            <div className="bg-slate-800 rounded-xl p-4">
              <div className="flex items-center space-x-4 mb-4">
                <button
                  onClick={handlePlayPause}
                  className="p-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                >
                  {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                </button>

                <button
                  onClick={() => handleSeek(-10)}
                  className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                  title="Skip back 10s"
                >
                  <SkipBack className="h-5 w-5" />
                </button>

                <button
                  onClick={() => handleSeek(10)}
                  className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                  title="Skip forward 10s"
                >
                  <SkipForward className="h-5 w-5" />
                </button>

                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-slate-400 font-mono">{formatTime(currentTime)}</span>
                    <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden relative">
                      <div
                        className="h-full bg-green-500"
                        style={{ width: `${(currentTime / duration) * 100}%` }}
                      />
                      {/* Annotation markers on timeline */}
                      {selectedVideo.annotations.map((ann) => (
                        <div
                          key={ann.id}
                          className={`absolute top-0 h-full w-1 ${annotationTypeColors[ann.type]} opacity-70 cursor-pointer hover:opacity-100`}
                          style={{ left: `${(ann.timestamp / duration) * 100}%` }}
                          onClick={() => jumpToAnnotation(ann.timestamp)}
                          title={`${formatTime(ann.timestamp)} - ${ann.type}`}
                        />
                      ))}
                    </div>
                    <span className="text-sm text-slate-400 font-mono">{formatTime(duration)}</span>
                  </div>
                </div>

                <button
                  onClick={handleSpeedChange}
                  className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors font-mono"
                  title="Playback speed"
                >
                  {playbackSpeed}x
                </button>

                <button
                  onClick={handleVolumeToggle}
                  className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                  title={isMuted ? "Unmute" : "Mute"}
                >
                  {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                </button>

                <button
                  onClick={() => {
                    setEditingAnnotation(null);
                    setNewAnnotation({ type: 'note', note: '', rating: 5 });
                    setShowAnnotationForm(true);
                  }}
                  className="flex items-center space-x-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add Note</span>
                </button>
              </div>

              {/* Quick annotation buttons */}
              <div className="flex flex-wrap gap-2">
                {(['goal', 'assist', 'shot', 'pass', 'dribble', 'tackle'] as AnnotationType[]).map((type) => (
                  <button
                    key={type}
                    onClick={() => handleQuickAnnotation(type)}
                    className={`px-3 py-1 ${annotationTypeColors[type]} text-white text-xs rounded-full hover:opacity-80 transition-opacity`}
                    title={`Quick add ${type} annotation`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Match Stats */}
            {selectedVideo.stats && (
              <div className="bg-slate-800 rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-4">Performance Stats</h3>
                <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-400">{selectedVideo.stats.goals}</div>
                    <div className="text-sm text-slate-400">Goals</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">{selectedVideo.stats.assists}</div>
                    <div className="text-sm text-slate-400">Assists</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-400">{selectedVideo.stats.shots}</div>
                    <div className="text-sm text-slate-400">Shots</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">{selectedVideo.stats.passAccuracy}%</div>
                    <div className="text-sm text-slate-400">Pass Acc.</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-pink-400">{selectedVideo.stats.touches}</div>
                    <div className="text-sm text-slate-400">Touches</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Annotations Sidebar */}
          <div className="space-y-4">
            <div className="bg-slate-800 rounded-xl p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center justify-between">
                <span className="flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2 text-purple-400" />
                  Annotations ({selectedVideo.annotations.length})
                </span>
              </h3>

              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {selectedVideo.annotations.sort((a, b) => a.timestamp - b.timestamp).map((annotation) => (
                  <div
                    key={annotation.id}
                    className="p-3 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors group"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <button
                        onClick={() => jumpToAnnotation(annotation.timestamp)}
                        className={`px-2 py-1 rounded text-xs ${annotationTypeColors[annotation.type]} text-white hover:opacity-80`}
                      >
                        {annotation.type}
                      </button>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-slate-400 font-mono">{formatTime(annotation.timestamp)}</span>
                        <button
                          onClick={() => handleEditAnnotation(annotation)}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-500 rounded transition-all"
                          title="Edit"
                        >
                          <Edit2 className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => handleDeleteAnnotation(annotation.id)}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-600 rounded transition-all"
                          title="Delete"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm mb-2">{annotation.note}</p>
                    {annotation.rating && (
                      <div className="flex items-center space-x-1">
                        {[...Array(10)].map((_, i) => (
                          <Star
                            key={i}
                            className={`h-3 w-3 ${
                              i < annotation.rating! ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'
                            }`}
                          />
                        ))}
                        <span className="text-xs text-slate-400 ml-2">{annotation.rating}/10</span>
                      </div>
                    )}
                  </div>
                ))}

                {selectedVideo.annotations.length === 0 && (
                  <div className="text-center py-8 text-slate-400">
                    <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-30" />
                    <p>No annotations yet</p>
                    <p className="text-xs mt-1">Click "Add Note" to create one</p>
                  </div>
                )}
              </div>
            </div>

            {/* Tags */}
            <div className="bg-slate-800 rounded-xl p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center">
                <Tag className="h-5 w-5 mr-2 text-blue-400" />
                Tags
              </h3>
              <div className="flex flex-wrap gap-2">
                {selectedVideo.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-slate-700 rounded-full text-sm hover:bg-slate-600 transition-colors"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Annotation Form Modal */}
        {showAnnotationForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">
                  {editingAnnotation ? 'Edit Annotation' : 'Add Annotation'}
                </h3>
                <button
                  onClick={() => {
                    setShowAnnotationForm(false);
                    setEditingAnnotation(null);
                    setNewAnnotation({ type: 'note', note: '', rating: 5 });
                  }}
                  className="p-1 hover:bg-slate-700 rounded transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-sm text-slate-400 mb-4">
                Timestamp: <span className="font-mono text-green-400">{formatTime(editingAnnotation?.timestamp || currentTime)}</span>
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Type</label>
                  <select
                    value={newAnnotation.type}
                    onChange={(e) => setNewAnnotation({ ...newAnnotation, type: e.target.value as AnnotationType })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="goal">Goal</option>
                    <option value="assist">Assist</option>
                    <option value="shot">Shot</option>
                    <option value="pass">Pass</option>
                    <option value="dribble">Dribble</option>
                    <option value="tackle">Tackle</option>
                    <option value="save">Save</option>
                    <option value="movement">Movement</option>
                    <option value="positioning">Positioning</option>
                    <option value="highlight">Highlight</option>
                    <option value="concern">Concern</option>
                    <option value="note">Note</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Note</label>
                  <textarea
                    value={newAnnotation.note}
                    onChange={(e) => setNewAnnotation({ ...newAnnotation, note: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg h-24 resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="Add your observation..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Rating (1-10)</label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={newAnnotation.rating}
                    onChange={(e) => setNewAnnotation({ ...newAnnotation, rating: parseInt(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex items-center justify-center space-x-1 mt-2">
                    {[...Array(10)].map((_, i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${
                          i < newAnnotation.rating ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'
                        }`}
                      />
                    ))}
                    <span className="ml-2 text-lg font-bold text-green-400">{newAnnotation.rating}/10</span>
                  </div>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={editingAnnotation ? handleUpdateAnnotation : handleAddAnnotation}
                    disabled={!newAnnotation.note.trim()}
                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed py-2 rounded-lg transition-colors font-medium"
                  >
                    {editingAnnotation ? 'Update' : 'Add'}
                  </button>
                  <button
                    onClick={() => {
                      setShowAnnotationForm(false);
                      setEditingAnnotation(null);
                      setNewAnnotation({ type: 'note', note: '', rating: 5 });
                    }}
                    className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Share Modal */}
        {showShareModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">Share Video Analysis</h3>
                <button
                  onClick={() => setShowShareModal(false)}
                  className="p-1 hover:bg-slate-700 rounded transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href);
                    alert('✅ Link copied to clipboard!');
                  }}
                  className="w-full flex items-center space-x-3 px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-left"
                >
                  <Share2 className="h-5 w-5 text-blue-400" />
                  <div>
                    <div className="font-medium">Copy Link</div>
                    <div className="text-xs text-slate-400">Share via clipboard</div>
                  </div>
                </button>

                <button
                  onClick={() => {
                    handleExportAnalysis();
                    setShowShareModal(false);
                  }}
                  className="w-full flex items-center space-x-3 px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-left"
                >
                  <Download className="h-5 w-5 text-purple-400" />
                  <div>
                    <div className="font-medium">Export as PDF</div>
                    <div className="text-xs text-slate-400">Download full analysis</div>
                  </div>
                </button>
              </div>

              <button
                onClick={() => setShowShareModal(false)}
                className="w-full mt-4 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Video Library View
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Film className="h-8 w-8 mr-3 text-purple-500" />
          Video Analysis
        </h1>
        <div className="flex items-center space-x-4">
          <div className="flex bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-slate-700' : ''}`}
              title="Grid view"
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-slate-700' : ''}`}
              title="List view"
            >
              <List className="h-4 w-4" />
            </button>
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              showFilters ? 'bg-green-600 hover:bg-green-700' : 'bg-slate-800 hover:bg-slate-700'
            }`}
          >
            <Filter className="h-4 w-4" />
            <span>Filters</span>
          </button>
          <button
            onClick={() => setShowAddVideoModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Add Video</span>
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            <Upload className="h-4 w-4" />
            <span>Upload</span>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search videos, players, matches..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
      </div>

      {videoError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {videoError}
        </div>
      )}

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Player</label>
              <select
                value={filterPlayer}
                onChange={(e) => setFilterPlayer(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
              >
                <option value="">All Players</option>
                {allPlayers.map(player => (
                  <option key={player} value={player}>{player}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Competition</label>
              <select
                value={filterCompetition}
                onChange={(e) => setFilterCompetition(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
              >
                <option value="">All Competitions</option>
                {allCompetitions.map(comp => (
                  <option key={comp} value={comp}>{comp}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end space-x-2">
              <button
                onClick={applyFilters}
                className="flex-1 bg-green-600 hover:bg-green-700 py-2 rounded-lg transition-colors"
              >
                Apply Filters
              </button>
              <button
                onClick={() => {
                  setFilterPlayer('');
                  setFilterCompetition('');
                  setFilterTags([]);
                  setVideos(allVideos);
                }}
                className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Video Count */}
      <div className="text-slate-400">
        Showing {videos.length} video{videos.length !== 1 ? 's' : ''}
      </div>

      {loading ? (
        <div className="flex items-center justify-center rounded-xl bg-slate-800 px-6 py-20 text-slate-300">
          Loading video library...
        </div>
      ) : (
        <>
          {/* Video Grid/List */}
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
            {videos.map((video) => (
              <div
                key={video.id}
                onClick={() => setSelectedVideo(video)}
                className="bg-slate-800 rounded-xl overflow-hidden cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all"
              >
                <div className="relative">
                  <img
                    src={video.thumbnail || VIDEO_PLACEHOLDER}
                    alt={video.title}
                    className="w-full h-48 object-cover"
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = VIDEO_PLACEHOLDER;
                    }}
                  />
                  <div className="absolute bottom-2 right-2 bg-black/80 px-2 py-1 rounded text-xs font-mono">
                    {video.duration}
                  </div>
                  <div className="absolute top-2 left-2">
                    <span className="px-2 py-1 bg-purple-600 text-white text-xs rounded">
                      {video.source}
                    </span>
                  </div>
                  {video.annotations.length > 0 && (
                    <div className="absolute top-2 right-2 bg-green-600 text-white text-xs px-2 py-1 rounded flex items-center space-x-1">
                      <MessageSquare className="h-3 w-3" />
                      <span>{video.annotations.length}</span>
                    </div>
                  )}
                </div>

                <div className="p-4">
                  <h3 className="font-semibold mb-2 line-clamp-2">{video.title}</h3>

                  {video.player && (
                    <div className="flex items-center space-x-2 text-sm text-slate-400 mb-2">
                      <User className="h-4 w-4" />
                      <span>{video.player.name}</span>
                      {video.player.position && (
                        <span className="px-2 py-0.5 bg-slate-700 rounded text-xs">
                          {video.player.position}
                        </span>
                      )}
                    </div>
                  )}

                  {video.match && (
                    <div className="flex items-center space-x-2 text-sm text-slate-400 mb-2">
                      <Calendar className="h-4 w-4" />
                      <span className="line-clamp-1">{video.match.homeTeam} vs {video.match.awayTeam}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-sm mt-3">
                    <div className="flex items-center space-x-2 text-slate-400">
                      <Tag className="h-4 w-4" />
                      <span>{video.tags.length} tags</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {video.tags.slice(0, 2).map((tag) => (
                        <span key={tag} className="px-2 py-0.5 bg-slate-700 rounded text-xs">
                          {tag}
                        </span>
                      ))}
                      {video.tags.length > 2 && (
                        <span className="px-2 py-0.5 bg-slate-700 rounded text-xs">
                          +{video.tags.length - 2}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-700">
                    <button
                      onClick={(e) => handlePlayStream(e, video.id)}
                      title="Stream video"
                      className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs font-medium transition-colors"
                    >
                      <Play className="h-3 w-3" />
                      Play
                    </button>
                    <button
                      onClick={(e) => handleAnalyzeVideo(e, video.id)}
                      disabled={analyzingVideos.has(video.id)}
                      title="Analyse video"
                      className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg text-xs font-medium transition-colors"
                    >
                      {analyzingVideos.has(video.id)
                        ? <Loader2 className="h-3 w-3 animate-spin" />
                        : <BarChart2 className="h-3 w-3" />}
                      Analyse
                    </button>
                    <button
                      onClick={(e) => handleDeleteVideo(e, video.id)}
                      title="Delete video"
                      className="ml-auto flex items-center gap-1 px-3 py-1.5 bg-red-600/80 hover:bg-red-600 rounded-lg text-xs font-medium transition-colors"
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {videos.length === 0 && (
        <div className="text-center py-16">
          <Film className="h-16 w-16 mx-auto mb-4 text-slate-600" />
          <p className="text-xl text-slate-400 mb-2">No videos found</p>
          <p className="text-sm text-slate-500">Try adjusting your search or filters</p>
        </div>
          )}
        </>
      )}

      {/* Add Video Modal */}
      {showAddVideoModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Add New Video</h3>
              <button
                onClick={() => setShowAddVideoModal(false)}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label htmlFor="video-url" className="block text-sm font-medium mb-2">Video URL <span className="text-red-400">*</span></label>
                <input
                  id="video-url"
                  type="text"
                  placeholder="https://youtube.com/watch?v=..."
                  value={videoForm.url}
                  onChange={(e) => setVideoForm({ ...videoForm, url: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="text-xs text-slate-400 mt-1">YouTube, Vimeo, or direct video URL</p>
              </div>

              <div>
                <label htmlFor="video-title" className="block text-sm font-medium mb-2">Title <span className="text-red-400">*</span></label>
                <input
                  id="video-title"
                  type="text"
                  placeholder="e.g., Player Highlights - Match vs Team"
                  value={videoForm.title}
                  onChange={(e) => setVideoForm({ ...videoForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="video-player-name" className="block text-sm font-medium mb-2">Player Name</label>
                <input
                  id="video-player-name"
                  type="text"
                  placeholder="e.g., Erling Haaland"
                  value={videoForm.playerName}
                  onChange={(e) => setVideoForm({ ...videoForm, playerName: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="video-match-details" className="block text-sm font-medium mb-2">Match Details</label>
                <input
                  id="video-match-details"
                  type="text"
                  placeholder="e.g., Man City vs Arsenal (3-1)"
                  value={videoForm.matchDetails}
                  onChange={(e) => setVideoForm({ ...videoForm, matchDetails: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="video-tags" className="block text-sm font-medium mb-2">Tags</label>
                <input
                  id="video-tags"
                  type="text"
                  placeholder="e.g., goals, dribbling, positioning (comma-separated)"
                  value={videoForm.tags}
                  onChange={(e) => setVideoForm({ ...videoForm, tags: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="video-description" className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  id="video-description"
                  placeholder="Optional notes about this video..."
                  value={videoForm.description}
                  onChange={(e) => setVideoForm({ ...videoForm, description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg h-20 resize-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  onClick={handleCreateVideo}
                  disabled={submittingVideo}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 py-2 rounded-lg transition-colors font-medium"
                >
                  {submittingVideo ? 'Saving...' : 'Add Video'}
                </button>
                <button
                  onClick={resetVideoModal}
                  className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Video Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold flex items-center gap-2">
                <Upload className="h-5 w-5 text-purple-400" />
                Upload Video File
              </h3>
              <button
                onClick={() => { setShowUploadModal(false); setUploadFile(null); setUploadProgress(0); }}
                className="p-1 hover:bg-slate-700 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Drag-and-drop zone */}
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                const file = e.dataTransfer.files?.[0];
                if (file) setUploadFile(file);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                isDragging
                  ? 'border-purple-400 bg-purple-500/10'
                  : uploadFile
                  ? 'border-green-500 bg-green-500/10'
                  : 'border-slate-600 hover:border-slate-500'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) setUploadFile(f); }}
              />
              {uploadFile ? (
                <div className="space-y-1">
                  <Camera className="h-10 w-10 mx-auto text-green-400" />
                  <p className="font-medium text-green-300">{uploadFile.name}</p>
                  <p className="text-xs text-slate-400">{(uploadFile.size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-10 w-10 mx-auto text-slate-500" />
                  <p className="text-slate-300">Drag &amp; drop a video file here</p>
                  <p className="text-xs text-slate-500">or click to browse</p>
                </div>
              )}
            </div>

            <div className="space-y-3 mt-4">
              <div>
                <label className="block text-sm font-medium mb-1">Match ID <span className="text-slate-500">(optional)</span></label>
                <input
                  type="text"
                  value={uploadMatchId}
                  onChange={(e) => setUploadMatchId(e.target.value)}
                  placeholder="e.g. match_123"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Team ID <span className="text-slate-500">(optional)</span></label>
                <input
                  type="text"
                  value={uploadTeamId}
                  onChange={(e) => setUploadTeamId(e.target.value)}
                  placeholder="e.g. team_456"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                />
              </div>
            </div>

            {/* Progress bar */}
            {uploading && (
              <div className="mt-4">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Uploading…</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-5">
              <button
                onClick={handleFileUpload}
                disabled={!uploadFile || uploading}
                className="flex-1 flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed py-2 rounded-lg transition-colors font-medium"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {uploading ? `Uploading ${uploadProgress}%` : 'Upload'}
              </button>
              <button
                onClick={() => { setShowUploadModal(false); setUploadFile(null); setUploadProgress(0); }}
                className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoAnalysis;
