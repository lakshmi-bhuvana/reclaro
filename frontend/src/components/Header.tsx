import React from 'react';
import { Activity, ShieldAlert, Layers, History } from 'lucide-react';

type AppView = 'dashboard' | 'audit-history' | 'audit-detail';

interface HeaderProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
  onOpenArchitecture?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentView, onNavigate, onOpenArchitecture }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
        {/* Brand */}
        <button
          onClick={() => onNavigate('dashboard')}
          className="flex items-center space-x-3 group"
        >
          <div className="p-2 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20 text-white group-hover:shadow-cyan-500/40 transition-shadow">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div className="text-left">
            <h1 className="text-base font-extrabold tracking-tight text-white font-sans leading-none">
              Reclaro
            </h1>
            <p className="text-[10px] text-slate-400 leading-none mt-0.5">
              Evidence-Backed FDA Recall Matching
            </p>
          </div>
        </button>

        {/* Navigation */}
        <nav className="flex items-center space-x-1 text-xs font-medium">
          <button
            onClick={() => onNavigate('dashboard')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              currentView === 'dashboard'
                ? 'bg-slate-800 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            Dashboard
          </button>

          <button
            onClick={() => onNavigate('audit-history')}
            className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
              currentView === 'audit-history' || currentView === 'audit-detail'
                ? 'bg-slate-800 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Audit History
          </button>

          {onOpenArchitecture && (
            <button
              type="button"
              onClick={onOpenArchitecture}
              className="px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 text-slate-400 hover:text-blue-300 hover:bg-blue-600/10"
            >
              <Layers className="w-3.5 h-3.5" />
              Architecture
            </button>
          )}
        </nav>

        {/* Status pill — hidden on small screens */}
        <div className="hidden lg:flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="font-mono text-emerald-400 font-medium">openFDA</span>
            <span className="text-slate-500">·</span>
            <span className="text-slate-300">Live</span>
          </div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-amber-950/40 border border-amber-800/50 text-amber-300">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span>Deterministic Verification Active</span>
          </div>
        </div>
      </div>
    </header>
  );
};