import React, { useState } from 'react';
import { Header } from '../components/Header';
import { RecallSelector } from '../components/RecallSelector';
import { InventoryUploader } from '../components/InventoryUploader';
import { StatsOverview } from '../components/StatsOverview';
import { MatchResultsTable } from '../components/MatchResultsTable';
import { EvidenceDrawer } from '../components/EvidenceDrawer';
import { ArchitectureOverlay } from '../components/ArchitectureOverlay';
import { Recall, NormalizedRecall, MatchResponse, MatchResult } from '../types';
import { auditInventoryMatch, fetchRecallDetail } from '../services/api';
import { ShieldCheck, Info, Sparkles, UploadCloud } from 'lucide-react';

type AppView = 'dashboard' | 'audit-history' | 'audit-detail';

interface DashboardProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
}

// The demo case CSV is embedded as a static asset served from /demo/
// We fetch it at runtime so it goes through the same upload path as any CSV.
const DEMO_RECALL_ID = '80313';
const DEMO_CSV_URL = '/demo/hospital_inventory_sample_recall_80313.csv';

export const Dashboard: React.FC<DashboardProps> = ({ currentView, onNavigate }) => {
  const [selectedRecall, setSelectedRecall] = useState<Recall | null>(null);
  const [normalizedRecall, setNormalizedRecall] = useState<NormalizedRecall | null>(null);
  const [auditResponse, setAuditResponse] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDrawerResult, setActiveDrawerResult] = useState<MatchResult | null>(null);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState<boolean>(false);

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

  const handleRunDemo = async () => {
    setLoading(true);
    setError(null);
    setAuditResponse(null);
    try {
      // 1. Fetch recall 80313 detail from live openFDA (also selects it in the UI)
      const { recall, normalized_recall } = await fetchRecallDetail(DEMO_RECALL_ID);
      setSelectedRecall(recall);
      setNormalizedRecall(normalized_recall);

      // 2. Fetch the synthetic demo CSV as a Blob and convert to File
      const csvRes = await fetch(DEMO_CSV_URL);
      if (!csvRes.ok) {
        throw new Error(
          `Could not load the demo inventory CSV (${csvRes.status}). ` +
          `Ensure the file is deployed at: ${DEMO_CSV_URL}`
        );
      }
      const csvBlob = await csvRes.blob();
      const csvFile = new File(
        [csvBlob],
        'hospital_inventory_sample_recall_80313.csv',
        { type: 'text/csv' }
      );

      // 3. Run the same audit workflow used for normal uploads
      const response = await auditInventoryMatch(DEMO_RECALL_ID, csvFile);
      setAuditResponse(response);
    } catch (err: any) {
      setError(err.message || 'Demo could not be loaded. Check the console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header
        currentView={currentView}
        onNavigate={onNavigate}
        onOpenArchitecture={() => setIsArchitectureOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Deterministic verification bar */}
        <div className="p-3 bg-cyan-950/30 border border-cyan-800/50 rounded-xl text-xs flex items-center justify-between text-cyan-200">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span>
              <strong>Deterministic Authority Enforcement:</strong> AI candidate matching flags items for review; exact identifier verification determines CONFIRMED status.
            </span>
          </div>
          <span className="hidden md:inline text-[10px] text-cyan-400/80 font-mono">
            openFDA Live Integration
          </span>
        </div>

        {/* ── Guided Demo Callout ─────────────────────────────────── */}
        <div className="rounded-xl border border-blue-800/50 bg-blue-950/20 p-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-900/50 border border-blue-700/50 rounded-lg text-blue-300 mt-0.5 flex-shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <p className="text-sm font-bold text-blue-200">Guided Demo</p>
                <p className="text-xs text-blue-300/80 mt-0.5 leading-relaxed max-w-xl">
                  <strong>Smith &amp; Nephew — Recall 80313</strong> · 25 synthetic inventory records<br />
                  Recall data fetched live from openFDA. Inventory is synthetic for demonstration.
                  Runs the full matching workflow: Bedrock candidate generation → deterministic verification → DynamoDB persistence.
                </p>
              </div>
            </div>
            <button
              id="btn-try-demo"
              onClick={handleRunDemo}
              disabled={loading}
              className="flex-shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-bold shadow-lg shadow-blue-600/20 transition-all"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Running…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Try Demo Case
                </>
              )}
            </button>
          </div>
        </div>

        {/* ── Divider ────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 text-slate-600 text-xs">
          <div className="flex-1 border-t border-slate-800" />
          <span className="flex items-center gap-1.5">
            <UploadCloud className="w-3.5 h-3.5" />
            or upload your own inventory CSV below
          </span>
          <div className="flex-1 border-t border-slate-800" />
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
          !loading && (
            <div className="glass-panel p-12 text-center rounded-xl border border-slate-800">
              <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-slate-900 flex items-center justify-center text-slate-500">
                <Info className="w-6 h-6 text-cyan-400" />
              </div>
              <h3 className="text-sm font-bold text-slate-200">No Recall Audit Executed Yet</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Click <strong>Try Demo Case</strong> above to run the guided demo, or select an FDA Medical Device Recall and upload your hospital inventory CSV.
              </p>
            </div>
          )
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500 bg-slate-950">
        <p>Reclaro • Powered by AWS Serverless &amp; openFDA Public API</p>
      </footer>

      {/* Architecture Overlay Modal */}
      <ArchitectureOverlay
        isOpen={isArchitectureOpen}
        onClose={() => setIsArchitectureOpen(false)}
      />

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
