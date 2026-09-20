import React, { useEffect, useState } from 'react';
import {
  ArrowLeft, Clock, ShieldAlert, AlertCircle, CheckCircle2,
  Box, Database, Archive, Eye,
} from 'lucide-react';
import { AuditDetail, AuditItemResult, MatchStatus } from '../types';
import { fetchAuditDetail } from '../services/api';
import { EvidenceDrawer } from '../components/EvidenceDrawer';

interface AuditDetailPageProps {
  runId: string;
  onBack: () => void;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'long', timeStyle: 'short' });
  } catch {
    return iso;
  }
}

function statusBadge(status: MatchStatus) {
  switch (status) {
    case 'CONFIRMED':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-950/70 text-red-400 border border-red-800">
          <ShieldAlert className="w-3 h-3" /> CONFIRMED
        </span>
      );
    case 'NEEDS_REVIEW':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-950/70 text-amber-400 border border-amber-800">
          <AlertCircle className="w-3 h-3" /> NEEDS REVIEW
        </span>
      );
    case 'NOT_AFFECTED':
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-950/70 text-emerald-400 border border-emerald-800">
          <CheckCircle2 className="w-3 h-3" /> NOT AFFECTED
        </span>
      );
  }
}

export const AuditDetailPage: React.FC<AuditDetailPageProps> = ({ runId, onBack }) => {
  const [detail, setDetail] = useState<AuditDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drawerItem, setDrawerItem] = useState<AuditItemResult | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAuditDetail(runId);
        setDetail(data);
      } catch (err: any) {
        setError(err.message || 'Unable to load audit detail.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [runId]);

  if (loading) {
    return (
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="glass-panel p-12 text-center rounded-xl border border-slate-800">
          <div className="flex items-center justify-center gap-2 text-slate-400 text-sm">
            <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            Loading audit run...
          </div>
        </div>
      </main>
    );
  }

  if (error || !detail) {
    return (
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-4">
        <button onClick={onBack} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Audit History
        </button>
        <div className="p-4 bg-red-950/60 border border-red-800 rounded-xl text-xs text-red-300 font-medium">
          {error || 'Audit run not found.'}
        </div>
      </main>
    );
  }

  const { run, results } = detail;

  // Convert AuditItemResult to MatchResult shape for EvidenceDrawer reuse
  const toMatchResult = (item: AuditItemResult) => ({
    inventory_id: item.inventory_id,
    recall_id: item.recall_id,
    status: item.status,
    signals: item.signals,
    evidence: item.evidence,
    recommended_action: item.recommended_action,
  });

  // Synthesize a minimal Recall for EvidenceDrawer (only recall_id and firm are persisted)
  const syntheticRecall = {
    recall_id: run.recall_id,
    recalling_firm: run.recalling_firm,
    product_description: '',
  };

  return (
    <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Back nav */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Audit History
      </button>

      {/* Run Header Card */}
      <div className="glass-panel rounded-xl border border-slate-800 p-6 space-y-4">
        {/* Historical run badge */}
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-lg text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          <Database className="w-3 h-3" />
          Historical Audit Record
        </div>

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white">{run.recalling_firm}</h2>
            <span className="font-mono text-sm text-cyan-400">Recall {run.recall_id}</span>
            <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5" />
              {formatDate(run.created_at)}
            </div>
            <div className="mt-1.5 text-[11px] font-mono text-slate-500 break-all">
              Run ID: {run.run_id}
            </div>
          </div>

          {/* Count summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
              <div className="flex items-center justify-center mb-1"><Box className="w-4 h-4 text-slate-400" /></div>
              <div className="text-xl font-black text-white font-mono">{run.total_audited}</div>
              <div className="text-[10px] text-slate-500">Audited</div>
            </div>
            <div className="p-3 bg-red-950/20 border border-red-900/40 rounded-lg">
              <div className="flex items-center justify-center mb-1"><ShieldAlert className="w-4 h-4 text-red-400" /></div>
              <div className="text-xl font-black text-red-500 font-mono">{run.confirmed_count}</div>
              <div className="text-[10px] text-red-400/80">Confirmed</div>
            </div>
            <div className="p-3 bg-amber-950/20 border border-amber-900/40 rounded-lg">
              <div className="flex items-center justify-center mb-1"><AlertCircle className="w-4 h-4 text-amber-400" /></div>
              <div className="text-xl font-black text-amber-500 font-mono">{run.needs_review_count}</div>
              <div className="text-[10px] text-amber-400/80">Needs Review</div>
            </div>
            <div className="p-3 bg-emerald-950/20 border border-emerald-900/40 rounded-lg">
              <div className="flex items-center justify-center mb-1"><CheckCircle2 className="w-4 h-4 text-emerald-400" /></div>
              <div className="text-xl font-black text-emerald-500 font-mono">{run.not_affected_count}</div>
              <div className="text-[10px] text-emerald-400/80">Not Affected</div>
            </div>
          </div>
        </div>

        {/* Persistence indicators */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
          {run.inventory_storage_key && (
            <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-lg">
              <Archive className="w-3 h-3 text-emerald-400" />
              Inventory artifact stored in S3
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-lg">
            <Database className="w-3 h-3 text-blue-400" />
            Audit results stored in DynamoDB
          </span>
        </div>
      </div>

      {/* Results Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-slate-900/40">
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Inventory Results — {results.length} items
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Inventory ID</th>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 hidden md:table-cell">Signals</th>
                <th className="py-3 px-4 text-right">Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {results.map((item) => (
                <tr
                  key={item.inventory_id}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    item.status === 'CONFIRMED' ? 'bg-red-950/10' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-mono font-bold text-cyan-400">
                    {item.inventory_id}
                  </td>
                  <td className="py-3 px-4 text-slate-300 max-w-[150px] truncate">
                    {item.inventory_item?.product_name || '—'}
                  </td>
                  <td className="py-3 px-4">{statusBadge(item.status)}</td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <div className="flex flex-wrap gap-1 max-w-[180px]">
                      {item.signals.length === 0 ? (
                        <span className="text-slate-500 font-mono text-[10px]">None</span>
                      ) : (
                        item.signals.slice(0, 2).map((sig) => (
                          <span
                            key={sig}
                            className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-[10px] font-mono text-slate-300"
                          >
                            {sig}
                          </span>
                        ))
                      )}
                      {item.signals.length > 2 && (
                        <span className="text-[10px] text-slate-500">+{item.signals.length - 2}</span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setDrawerItem(item)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-cyan-600 text-cyan-300 hover:text-white border border-slate-700 transition-all font-semibold inline-flex items-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      Evidence
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Evidence Drawer — reuse existing component */}
      <EvidenceDrawer
        result={drawerItem ? toMatchResult(drawerItem) : null}
        recall={syntheticRecall as any}
        normalizedRecall={null}
        onClose={() => setDrawerItem(null)}
      />
    </main>
  );
};
