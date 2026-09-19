import React from 'react';
import { ShieldAlert, AlertCircle, CheckCircle2, Box } from 'lucide-react';
import { MatchResponse } from '../types';

interface StatsOverviewProps {
  data: MatchResponse | null;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ data }) => {
  if (!data) return null;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Audited */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400">Total Audited</p>
          <p className="text-2xl font-black text-white mt-1 font-mono">
            {data.total_audited}
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">Inventory devices</p>
        </div>
        <div className="p-3 bg-slate-900 rounded-xl text-slate-400 border border-slate-800">
          <Box className="w-5 h-5" />
        </div>
      </div>

      {/* CONFIRMED MATCHES */}
      <div className="glass-panel p-4 rounded-xl border border-red-900/40 bg-red-950/10 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-red-400">CONFIRMED MATCHES</p>
          <p className="text-2xl font-black text-red-500 mt-1 font-mono">
            {data.confirmed_count}
          </p>
          <p className="text-[10px] text-red-400/80 mt-0.5">Potentially affected</p>
        </div>
        <div className="p-3 bg-red-950/60 rounded-xl text-red-400 border border-red-800/60">
          <ShieldAlert className="w-5 h-5" />
        </div>
      </div>

      {/* Needs Review */}
      <div className="glass-panel p-4 rounded-xl border border-amber-900/40 bg-amber-950/10 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-amber-400">NEEDS REVIEW</p>
          <p className="text-2xl font-black text-amber-500 mt-1 font-mono">
            {data.needs_review_count}
          </p>
          <p className="text-[10px] text-amber-400/80 mt-0.5">Biomed inspection</p>
        </div>
        <div className="p-3 bg-amber-950/60 rounded-xl text-amber-400 border border-amber-800/60">
          <AlertCircle className="w-5 h-5" />
        </div>
      </div>

      {/* Not Affected */}
      <div className="glass-panel p-4 rounded-xl border border-emerald-900/40 bg-emerald-950/10 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-emerald-400">NOT AFFECTED</p>
          <p className="text-2xl font-black text-emerald-500 mt-1 font-mono">
            {data.not_affected_count}
          </p>
          <p className="text-[10px] text-emerald-400/80 mt-0.5">No matching evidence</p>
        </div>
        <div className="p-3 bg-emerald-950/60 rounded-xl text-emerald-400 border border-emerald-800/60">
          <CheckCircle2 className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
