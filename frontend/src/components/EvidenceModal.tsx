import React from 'react';
import { X, ShieldAlert, AlertCircle, CheckCircle2, FileText, Activity, AlertOctagon, CheckSquare } from 'lucide-react';
import { MatchResult, Recall, NormalizedRecall } from '../types';

interface EvidenceModalProps {
  result: MatchResult | null;
  recall: Recall | null;
  normalizedRecall: NormalizedRecall | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  result,
  recall,
  normalizedRecall,
  onClose,
}) => {
  if (!result) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl shadow-cyan-950/50">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center space-x-3">
            {result.status === 'CONFIRMED' && (
              <div className="p-2 bg-red-950 border border-red-800 rounded-xl text-red-400">
                <ShieldAlert className="w-6 h-6" />
              </div>
            )}
            {result.status === 'NEEDS_REVIEW' && (
              <div className="p-2 bg-amber-950 border border-amber-800 rounded-xl text-amber-400">
                <AlertCircle className="w-6 h-6" />
              </div>
            )}
            {result.status === 'NOT_AFFECTED' && (
              <div className="p-2 bg-emerald-950 border border-emerald-800 rounded-xl text-emerald-400">
                <CheckCircle2 className="w-6 h-6" />
              </div>
            )}

            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">
                  Audit Evidence Diagnostic
                </h3>
                <span className="font-mono text-xs text-cyan-400 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                  {result.inventory_id}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluated against FDA Recall{' '}
                <span className="font-mono text-slate-200 font-bold">{result.recall_id}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Status Box */}
          <div
            className={`p-4 rounded-xl border ${
              result.status === 'CONFIRMED'
                ? 'bg-red-950/30 border-red-800/80 text-red-200'
                : result.status === 'NEEDS_REVIEW'
                ? 'bg-amber-950/30 border-amber-800/80 text-amber-200'
                : 'bg-emerald-950/30 border-emerald-800/80 text-emerald-200'
            }`}
          >
            <div className="flex items-center justify-between font-bold text-sm">
              <span>Classification Outcome: {result.status}</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-950/60 border border-current">
                Authoritative Rule Engine
              </span>
            </div>
            <p className="text-xs mt-2 leading-relaxed opacity-95">
              {result.evidence}
            </p>
          </div>

          {/* Triggered Signals */}
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-cyan-400" />
              Triggered Matching Rule Signals ({result.signals.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.signals.length === 0 ? (
                <span className="text-xs text-slate-500 italic">No matching rule signals triggered.</span>
              ) : (
                result.signals.map((sig) => (
                  <span
                    key={sig}
                    className="px-2.5 py-1 rounded-md bg-slate-950 border border-slate-700 text-xs font-mono font-semibold text-cyan-300"
                  >
                    {sig}
                  </span>
                ))
              )}
            </div>
          </div>

          {/* Recommended Operational Action */}
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
            <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <CheckSquare className="w-4 h-4 text-cyan-400" />
              Recommended Operational Action
            </h4>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {result.recommended_action}
            </p>
          </div>

          {/* FDA Recall Context */}
          {recall && (
            <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs space-y-2">
              <h4 className="font-bold text-slate-300 flex items-center gap-1.5 border-b border-slate-800 pb-2">
                <FileText className="w-4 h-4 text-slate-400" />
                FDA Recall Context Details
              </h4>
              <div className="grid grid-cols-2 gap-2 text-slate-400 pt-1">
                <div>
                  <span className="text-slate-500">Recalling Firm:</span>{' '}
                  <span className="text-slate-200 font-semibold">{recall.recalling_firm}</span>
                </div>
                <div>
                  <span className="text-slate-500">Classification:</span>{' '}
                  <span className="text-amber-400 font-semibold">{recall.classification}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-500">Reason for Recall:</span>{' '}
                  <span className="text-slate-300">{recall.reason_for_recall || 'N/A'}</span>
                </div>
                {recall.source_url && (
                  <div className="col-span-2 pt-1">
                    <a
                      href={recall.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:underline inline-flex items-center gap-1 text-[11px]"
                    >
                      View Official FDA Notice Notice ↗
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors"
          >
            Close Diagnostic
          </button>
        </div>
      </div>
    </div>
  );
};
