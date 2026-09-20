import React, { useEffect, useState } from 'react';
import { History, Clock, ChevronRight, ShieldAlert, AlertCircle, CheckCircle2, Box, RefreshCw } from 'lucide-react';
import { AuditRun } from '../types';
import { fetchAuditRuns } from '../services/api';

interface AuditHistoryPageProps {
  onViewAudit: (runId: string) => void;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

export const AuditHistoryPage: React.FC<AuditHistoryPageProps> = ({ onViewAudit }) => {
  const [runs, setRuns] = useState<AuditRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAuditRuns(20);
      setRuns(data.runs);
    } catch (err: any) {
      setError(err.message || 'Unable to load audit history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-300">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Audit History</h2>
            <p className="text-xs text-slate-400 mt-0.5">Past completed recall matching runs — persisted in DynamoDB</p>
          </div>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* States */}
      {loading && (
        <div className="glass-panel p-12 text-center rounded-xl border border-slate-800">
          <div className="flex items-center justify-center gap-2 text-slate-400 text-sm">
            <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            Loading audit history...
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="p-4 bg-red-950/60 border border-red-800 rounded-xl text-xs text-red-300 font-medium">
          {error}
        </div>
      )}

      {!loading && !error && runs.length === 0 && (
        <div className="glass-panel p-12 text-center rounded-xl border border-slate-800">
          <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-slate-900 flex items-center justify-center">
            <History className="w-6 h-6 text-slate-500" />
          </div>
          <h3 className="text-sm font-bold text-slate-200">No audit runs yet</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Completed recall audits will appear here. Run a recall audit from the Dashboard to get started.
          </p>
        </div>
      )}

      {!loading && !error && runs.length > 0 && (
        <div className="space-y-3">
          {runs.map((run) => (
            <div
              key={run.run_id}
              className="glass-panel rounded-xl border border-slate-800 hover:border-slate-700 transition-colors p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  {/* Firm & Recall ID */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-bold text-slate-100 truncate">{run.recalling_firm}</span>
                    <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/30 px-2 py-0.5 rounded border border-cyan-800/40">
                      Recall {run.recall_id}
                    </span>
                  </div>

                  {/* Date */}
                  <div className="flex items-center gap-1.5 mt-1.5 text-[11px] text-slate-500">
                    <Clock className="w-3 h-3" />
                    {formatDate(run.created_at)}
                  </div>

                  {/* Counts */}
                  <div className="flex flex-wrap items-center gap-3 mt-3">
                    <span className="flex items-center gap-1 text-xs text-slate-400">
                      <Box className="w-3.5 h-3.5" />
                      {run.total_audited} records
                    </span>
                    <span className="flex items-center gap-1 text-xs text-red-400">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      {run.confirmed_count} Confirmed
                    </span>
                    <span className="flex items-center gap-1 text-xs text-amber-400">
                      <AlertCircle className="w-3.5 h-3.5" />
                      {run.needs_review_count} Needs Review
                    </span>
                    <span className="flex items-center gap-1 text-xs text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {run.not_affected_count} Not Affected
                    </span>
                  </div>

                  {/* Persistence indicators */}
                  {run.inventory_storage_key && (
                    <div className="flex gap-2 mt-3">
                      <span className="text-[10px] text-slate-500 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                        Inventory stored in S3
                      </span>
                      <span className="text-[10px] text-slate-500 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                        Audit results in DynamoDB
                      </span>
                    </div>
                  )}
                </div>

                {/* View button */}
                <button
                  onClick={() => onViewAudit(run.run_id)}
                  className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-cyan-600 text-slate-300 hover:text-white border border-slate-700 transition-all text-xs font-semibold"
                >
                  View Audit
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
};
