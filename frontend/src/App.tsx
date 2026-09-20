import React, { useState } from 'react';
import { Dashboard } from './pages/Dashboard';
import { AuditHistoryPage } from './pages/AuditHistoryPage';
import { AuditDetailPage } from './pages/AuditDetailPage';

type AppView = 'dashboard' | 'audit-history' | 'audit-detail';

const App: React.FC = () => {
  const [view, setView] = useState<AppView>('dashboard');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const handleNavigate = (v: AppView) => {
    setView(v);
    if (v !== 'audit-detail') setSelectedRunId(null);
  };

  const handleViewAudit = (runId: string) => {
    setSelectedRunId(runId);
    setView('audit-detail');
  };

  if (view === 'audit-history') {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
        {/* Inline header import to avoid circular re-exports */}
        <HeaderShim currentView={view} onNavigate={handleNavigate} />
        <AuditHistoryPage onViewAudit={handleViewAudit} />
        <Footer />
      </div>
    );
  }

  if (view === 'audit-detail' && selectedRunId) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
        <HeaderShim currentView={view} onNavigate={handleNavigate} />
        <AuditDetailPage runId={selectedRunId} onBack={() => handleNavigate('audit-history')} />
        <Footer />
      </div>
    );
  }

  // Default: dashboard
  return <Dashboard currentView={view} onNavigate={handleNavigate} />;
};

// ── Shared sub-components used on non-dashboard views ─────────────────────────

import { Header } from './components/Header';

const HeaderShim: React.FC<{ currentView: AppView; onNavigate: (v: AppView) => void }> = ({
  currentView,
  onNavigate,
}) => <Header currentView={currentView} onNavigate={onNavigate} />;

const Footer: React.FC = () => (
  <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500 bg-slate-950">
    <p>Reclaro • Powered by AWS Serverless &amp; openFDA Public API</p>
  </footer>
);

export default App;
