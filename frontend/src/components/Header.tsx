import React from 'react';
import { Activity, ShieldAlert } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20 text-white">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>

          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-white font-sans">
              Reclaro
            </h1>

            <p className="text-xs text-slate-400">
              Evidence-Backed FDA Medical Device Recall Matching
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="font-mono text-emerald-400 font-medium">
              openFDA API
            </span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-300">Live Connection</span>
          </div>

          <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-amber-950/40 border border-amber-800/50 text-amber-300">
            <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>Deterministic Verification Layer Active</span>
          </div>
        </div>
      </div>
    </header>
  );
};