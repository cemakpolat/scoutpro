import React, { useState, Suspense, lazy } from 'react';
import { buildMatchCatalog, filterMatchCatalog, formatMatchLabel, getAvailableLeagues, getAvailableYears } from './utils/matchFilters';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DataProvider, useData } from './context/DataContext';
import { CollaborationProvider } from './context/CollaborationContext';
import { CalendarProvider } from './context/CalendarContext';
import Navigation from './components/Navigation';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import ProtectedRoute from './components/auth/ProtectedRoute';

// Lazy-loaded page components for code splitting
const Dashboard = lazy(() => import('./components/Dashboard'));
const PlayerDatabase = lazy(() => import('./components/PlayerDatabase'));
const MatchCentre = lazy(() => import('./components/MatchCentre'));
const MultiMatchAnalysis = lazy(() => import('./components/MultiMatchAnalysis'));
const ScoutingDashboard = lazy(() => import('./components/ScoutingDashboard'));
const ReportBuilder = lazy(() => import('./components/ReportBuilder'));
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard'));
const MLLaboratory = lazy(() => import('./components/MLLaboratory'));
const AdminConsole = lazy(() => import('./components/AdminConsole'));
const NotificationCenter = lazy(() => import('./components/NotificationCenter'));
const DataManagement = lazy(() => import('./components/DataManagement'));
const TacticalAnalyzer = lazy(() => import('./components/TacticalAnalyzer'));
const TransferHub = lazy(() => import('./components/TransferHub'));
const PerformanceTracker = lazy(() => import('./components/PerformanceTracker'));
const SearchPage = lazy(() => import('./components/SearchPage'));
const PlayerComparison = lazy(() => import('./components/PlayerComparison'));
const DataImporter = lazy(() => import('./components/DataImporter'));
const MatchDetailWithVisualizations = lazy(() => import('./components/MatchDetailWithVisualizations'));
// Hidden pages (not in navigation but available via direct tab access)
const VideoAnalysis = lazy(() => import('./components/VideoAnalysis'));
const CollaborationHub = lazy(() => import('./components/CollaborationHub'));
const CalendarScheduling = lazy(() => import('./components/CalendarScheduling'));


// Match Analysis page: select a real match then show visualizations
function MatchAnalysisPage() {
  const { matches, loading } = useData();
  const [selectedMatchId, setSelectedMatchId] = React.useState<string>('');
  const [selectedYear, setSelectedYear] = React.useState('all');
  const [selectedLeague, setSelectedLeague] = React.useState('all');

  // Show all matches (finished, live, and scheduled) for comprehensive analysis
  // Note: Event data (F24) only available for finished/live matches, but scheduled matches can show team info
  const matchOptions = matches.filter(
    (m: any) => Boolean(m?.id)
  );

  const matchCatalog = React.useMemo(() => buildMatchCatalog(matchOptions), [matchOptions]);
  const availableYears = React.useMemo(() => getAvailableYears(matchCatalog), [matchCatalog]);
  const availableLeagues = React.useMemo(
    () => getAvailableLeagues(matchCatalog, selectedYear),
    [matchCatalog, selectedYear],
  );
  const filteredMatchOptions = React.useMemo(
    () => filterMatchCatalog(matchCatalog, { year: selectedYear, league: selectedLeague }).map((entry) => entry.source),
    [matchCatalog, selectedYear, selectedLeague],
  );

  React.useEffect(() => {
    if (selectedYear !== 'all' && !availableYears.includes(selectedYear)) {
      setSelectedYear('all');
    }
  }, [availableYears, selectedYear]);

  React.useEffect(() => {
    if (selectedLeague !== 'all' && !availableLeagues.includes(selectedLeague)) {
      setSelectedLeague('all');
    }
  }, [availableLeagues, selectedLeague]);

  React.useEffect(() => {
    if (!selectedMatchId && filteredMatchOptions.length > 0) {
      setSelectedMatchId(String(filteredMatchOptions[0].id));
      return;
    }

    if (selectedMatchId && !filteredMatchOptions.some((match: any) => String(match.id) === String(selectedMatchId))) {
      setSelectedMatchId(filteredMatchOptions.length > 0 ? String(filteredMatchOptions[0].id) : '');
    }
  }, [filteredMatchOptions, selectedMatchId]);

  const selected = filteredMatchOptions.find((m: any) => String(m.id) === selectedMatchId);

  if (loading.matches) {
    return <PageLoading />;
  }

  if (matchOptions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-slate-400">
        No match data available.
      </div>
    );
  }

  if (filteredMatchOptions.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4 pb-2">
          <label className="text-sm font-medium text-slate-300">Year:</label>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm"
          >
            <option value="all">All Years</option>
            {availableYears.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <label className="text-sm font-medium text-slate-300">League:</label>
          <select
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm"
          >
            <option value="all">All Leagues</option>
            {availableLeagues.map((league) => (
              <option key={league} value={league}>{league}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center justify-center min-h-[220px] text-slate-400">
          No matches found for the selected year and league.
        </div>
      </div>
    );
  }

  const homeTeam = selected?.homeTeam || selected?.home_team || 'Home';
  const awayTeam = selected?.awayTeam || selected?.away_team || 'Away';
  const homeTeamId = selected?.homeTeamId || selected?.home_team_id;
  const awayTeamId = selected?.awayTeamId || selected?.away_team_id;
  const homeScore = Number(selected?.homeScore ?? selected?.home_score ?? 0);
  const awayScore = Number(selected?.awayScore ?? selected?.away_score ?? 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 pb-2">
        <label className="text-sm font-medium text-slate-300">Year:</label>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(e.target.value)}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm"
        >
          <option value="all">All Years</option>
          {availableYears.map((year) => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
        <label className="text-sm font-medium text-slate-300">League:</label>
        <select
          value={selectedLeague}
          onChange={(e) => setSelectedLeague(e.target.value)}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm"
        >
          <option value="all">All Leagues</option>
          {availableLeagues.map((league) => (
            <option key={league} value={league}>{league}</option>
          ))}
        </select>
        <label className="text-sm font-medium text-slate-300">Select Match:</label>
        <select
          value={selectedMatchId}
          onChange={(e) => setSelectedMatchId(e.target.value)}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm"
          disabled={filteredMatchOptions.length === 0}
        >
          {filteredMatchOptions.length === 0 && <option value="">No matches</option>}
          {filteredMatchOptions.map((m: any) => (
            <option key={String(m.id)} value={String(m.id)}>
              {formatMatchLabel(m)}
            </option>
          ))}
        </select>
      </div>
      <React.Suspense fallback={<PageLoading />}>
        <MatchDetailWithVisualizations
          matchId={selectedMatchId}
          homeTeam={homeTeam}
          awayTeam={awayTeam}
          homeTeamId={homeTeamId ? String(homeTeamId) : undefined}
          awayTeamId={awayTeamId ? String(awayTeamId) : undefined}
          homeScore={homeScore}
          awayScore={awayScore}
        />
      </React.Suspense>
    </div>
  );
}

// Loading spinner for lazy components
function PageLoading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-slate-400 text-sm">Loading...</span>
      </div>
    </div>
  );
}

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [notifications, setNotifications] = useState([]);
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const { isAuthenticated, user } = useAuth();

  const renderActiveComponent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'search':
        return <SearchPage />;
      case 'player-comparison':
        return <PlayerComparison />;
      case 'data-importer':
        return <DataImporter />;
      case 'match-analysis':
        return <MatchAnalysisPage />;
      case 'players':
        return <PlayerDatabase />;
      case 'match-centre':
        return <MatchCentre />;
      case 'multi-match':
        return <MultiMatchAnalysis />;
      case 'scouting':
        return <ScoutingDashboard />;
      case 'reports':
        return <ReportBuilder />;
      case 'analytics':
        return <AnalyticsDashboard />;
      case 'ml-lab':
        return <MLLaboratory />;
      case 'admin':
        return <AdminConsole />;
      case 'data-management':
        return <DataManagement />;
      case 'tactical-analyzer':
        return <TacticalAnalyzer />;
      case 'transfer-hub':
        return <TransferHub />;
      case 'performance-tracker':
        return <PerformanceTracker />;
      case 'video-analysis':
        // Hidden from navigation but still accessible
        return <VideoAnalysis />;
      case 'collaboration':
        // Hidden from navigation but still accessible
        return <CollaborationHub />;
      case 'calendar':
        // Hidden from navigation but still accessible
        return <CalendarScheduling />;
      default:
        return <Dashboard />;
    }
  };

  // Show auth pages if not authenticated
  if (!isAuthenticated) {
    if (authView === 'register') {
      return <RegisterPage onSwitchToLogin={() => setAuthView('login')} />;
    }
    return <LoginPage onSwitchToRegister={() => setAuthView('register')} />;
  }

  return (
    <DataProvider>
      <CollaborationProvider>
        <CalendarProvider>
          <div className="min-h-screen bg-slate-900 text-white">
            <Navigation
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              notifications={notifications}
            />

            {/* Main content - responsive margins for mobile */}
            <main className="lg:ml-64 ml-0 p-4 lg:p-8 pt-16 lg:pt-8">
              <div className="max-w-7xl mx-auto">
                <Suspense fallback={<PageLoading />}>
                  <NotificationCenter
                    notifications={notifications}
                    setNotifications={setNotifications}
                  />
                  {/* Wrap admin-only routes with ProtectedRoute */}
                  {activeTab === 'admin' ? (
                    <ProtectedRoute requiredRole="admin">
                      {renderActiveComponent()}
                    </ProtectedRoute>
                  ) : (
                    renderActiveComponent()
                  )}
                </Suspense>
              </div>
            </main>
          </div>
        </CalendarProvider>
      </CollaborationProvider>
    </DataProvider>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;