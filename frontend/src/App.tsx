import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DataProvider } from './context/DataContext';
import { CollaborationProvider } from './context/CollaborationContext';
import { CalendarProvider } from './context/CalendarContext';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import PlayerDatabase from './components/PlayerDatabase';
import MatchCentre from './components/MatchCentre';
import MultiMatchAnalysis from './components/MultiMatchAnalysis';
import ScoutingDashboard from './components/ScoutingDashboard';
import ReportBuilder from './components/ReportBuilder';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import MLLaboratory from './components/MLLaboratory';
import AdminConsole from './components/AdminConsole';
import NotificationCenter from './components/NotificationCenter';
import DataManagement from './components/DataManagement';
import TacticalAnalyzer from './components/TacticalAnalyzer';
import TransferHub from './components/TransferHub';
import PerformanceTracker from './components/PerformanceTracker';
import SearchPage from './components/SearchPage';
import PlayerComparison from './components/PlayerComparison';
import VideoAnalysis from './components/VideoAnalysis';
import CollaborationHub from './components/CollaborationHub';
import CalendarScheduling from './components/CalendarScheduling';
import DataImporter from './components/DataImporter';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import ProtectedRoute from './components/auth/ProtectedRoute';

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