import React, { useState } from 'react';
import { Header } from '../components/Header';
import { RecallSelector } from '../components/RecallSelector';
import { InventoryUploader } from '../components/InventoryUploader';
import { StatsOverview } from '../components/StatsOverview';
import { MatchResultsTable } from '../components/MatchResultsTable';
import { EvidenceDrawer } from '../components/EvidenceDrawer';
import { Recall, NormalizedRecall, MatchResponse, MatchResult } from '../types';
import { auditInventoryMatch } from '../services/api';
import { ShieldCheck, Info } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [selectedRecall, setSelectedRecall] = useState<Recall | null>(null);
  const [normalizedRecall, setNormalizedRecall] = useState<NormalizedRecall | null>(null);
  const [auditResponse, setAuditResponse] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDrawerResult, setActiveDrawerResult] = useState<MatchResult | null>(null);

  const handleSelectRecall = (recall: Recall, normalized: NormalizedRecall) => {
    setSelectedRecall(recall);
    setNormalizedRecall(normalized);
  };

  const handleAuditStart = async (file: File) => {
    if (!selectedRecall) return;
    setLoading(true);
    setError(null);
    try {
      const response = await auditInventoryMatch(selectedRecall.recall_id, file);
      setAuditResponse(response);
    } catch (err: any) {
      setError(err.message || 'Audit execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Product Scope & Disclaimer Bar */}
        <div className="p-3 bg-cyan-950/30 border border-cyan-800/50 rounded-xl text-xs flex items-center justify-between text-cyan-200">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span>
              <strong>Deterministic Authority Enforcement:</strong> AI candidate matching flags items for review; exact identifier verification determines CONFIRMED status.
            </span>
          </div>
          <span className="hidden md:inline text-[10px] text-cyan-400/80 font-mono">
            Hackathon Build • openFDA Live Integration
          </span>
        </div>

        {/* Top Controls: Recall Selection & CSV Upload */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RecallSelector
            selectedRecall={selectedRecall}
            onSelectRecall={handleSelectRecall}
          />
          <InventoryUploader
            selectedRecall={selectedRecall}
            onAuditStart={handleAuditStart}
            loading={loading}
          />
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 rounded-xl text-xs text-red-300 font-medium">
            {error}
          </div>
        )}

        {/* Audit Results View */}
        {auditResponse ? (
          <div className="space-y-6 animate-fadeIn">
            <StatsOverview data={auditResponse} />
            <MatchResultsTable
              results={auditResponse.results}
              onInspect={(res) => setActiveDrawerResult(res)}
            />
          </div>
        ) : (
          <div className="glass-panel p-12 text-center rounded-xl border border-slate-800">
            <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-slate-900 flex items-center justify-center text-slate-500">
              <Info className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-sm font-bold text-slate-200">No Recall Audit Executed Yet</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Select an FDA Medical Device Recall notice on the left, upload your hospital inventory CSV (or click "Load Synthetic Demo CSV"), and click "Execute Recall Audit".
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500 bg-slate-950">
        <p>Powered by FastAPI & openFDA Public API</p>
      </footer>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        result={activeDrawerResult}
        recall={auditResponse?.recall || selectedRecall}
        normalizedRecall={auditResponse?.normalized_recall || normalizedRecall}
        onClose={() => setActiveDrawerResult(null)}
      />
    </div>
  );
};
