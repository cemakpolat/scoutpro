import React, { useState, Suspense, lazy } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DataProvider } from './context/DataContext';
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
const VideoAnalysis = lazy(() => import('./components/VideoAnalysis'));
const CollaborationHub = lazy(() => import('./components/CollaborationHub'));
const CalendarScheduling = lazy(() => import('./components/CalendarScheduling'));
const DataImporter = lazy(() => import('./components/DataImporter'));

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
      case 'video-analysis':
        return <VideoAnalysis />;
      case 'collaboration':
        return <CollaborationHub />;
      case 'calendar':
        return <CalendarScheduling />;
      case 'data-importer':
        return <DataImporter />;
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