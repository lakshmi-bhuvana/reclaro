import React, { useEffect, useState } from 'react';
import {
  X,
  Layers,
  Server,
  Cloud,
  Cpu,
  Database,
  Archive,
  FileSpreadsheet,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  CheckCircle2,
  ArrowDown,
  Globe,
  Monitor,
} from 'lucide-react';

interface ArchitectureOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

type ActiveTab = 'pipeline' | 'infrastructure';

export const ArchitectureOverlay: React.FC<ArchitectureOverlayProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('pipeline');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5"
      onClick={onClose}
    >
      <div
        className="relative bg-slate-900 border border-slate-700/90 rounded-2xl shadow-2xl shadow-black/80 w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="bg-slate-950 px-5 py-3.5 border-b border-slate-800 flex items-center justify-between flex-shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-white tracking-wide">
                Reclaro System Architecture
              </h2>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Evidence-backed medical recall matching · Live recall data from openFDA · Deployed on AWS
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Central Authority Principle & Problem Banner */}
        <div className="bg-gradient-to-r from-blue-950/90 via-indigo-950/80 to-slate-900 px-5 py-2.5 border-b border-blue-900/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 flex-shrink-0">
          <div>
            <p className="text-xs font-black text-blue-200 tracking-wide">
              &ldquo;AI proposes. Deterministic evidence decides.&rdquo;
            </p>
            <p className="text-[10px] text-blue-300/80 mt-0.5">
              AI evidence can contribute to <span className="text-amber-300 font-semibold">NEEDS_REVIEW</span>, but AI alone can never produce <span className="text-red-300 font-semibold">CONFIRMED</span>.
            </p>
          </div>
          <div className="text-[10px] text-slate-400 font-mono bg-slate-950/70 px-2.5 py-1 rounded-md border border-slate-800 self-start sm:self-auto">
            Determine whether hospital inventory falls within a live FDA recall
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="px-5 pt-3 pb-2 bg-slate-900 flex-shrink-0 flex items-center justify-center">
          <div className="inline-flex p-1 bg-slate-950 rounded-xl border border-slate-800 text-xs font-medium">
            <button
              onClick={() => setActiveTab('pipeline')}
              className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'pipeline'
                  ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Product &amp; Matching Pipeline
            </button>
            <button
              onClick={() => setActiveTab('infrastructure')}
              className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'infrastructure'
                  ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cloud className="w-3.5 h-3.5" />
              AWS Architecture
            </button>
          </div>
        </div>

        {/* Scrollable Modal Content */}
        <div className="flex-1 overflow-y-auto px-5 py-3 space-y-4 text-xs text-slate-300">
          {activeTab === 'pipeline' ? (
            /* ─────────────────────────────────────────────────────────────
               TAB 1: PRODUCT & MATCHING PIPELINE
               Story: PROBLEM → INPUTS → NORMALIZATION → BEDROCK → VERIFICATION → DECISION → PERSISTENCE
               ───────────────────────────────────────────────────────────── */
            <div className="space-y-3">
              {/* 1. INPUTS */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-cyan-800/60 text-center">
                  <div className="flex items-center justify-center gap-1.5 text-cyan-400 font-bold mb-0.5">
                    <Globe className="w-3.5 h-3.5" />
                    <span className="text-[11px]">FDA RECALL</span>
                  </div>
                  <p className="text-[10px] text-slate-400">openFDA Live Notice</p>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-emerald-800/60 text-center">
                  <div className="flex items-center justify-center gap-1.5 text-emerald-400 font-bold mb-0.5">
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    <span className="text-[11px]">HOSPITAL INVENTORY</span>
                  </div>
                  <p className="text-[10px] text-slate-400">CSV Upload</p>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-around text-slate-600 -my-1">
                <ArrowDown className="w-3.5 h-3.5 text-cyan-500" />
                <ArrowDown className="w-3.5 h-3.5 text-emerald-500" />
              </div>

              {/* 2. NORMALIZATION */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-center">
                  <p className="font-semibold text-slate-200 text-[11px]">Recall Scope Normalization</p>
                  <p className="text-[9.5px] text-slate-400 mt-0.5">Models, Catalogs, UDI, Lot/Serial Scope, Cutoff Dates</p>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-center">
                  <p className="font-semibold text-slate-200 text-[11px]">Inventory Normalization</p>
                  <p className="text-[9.5px] text-slate-400 mt-0.5">Entity suffix stripping, code sanitization, tokenization</p>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center text-slate-600 -my-1">
                <ArrowDown className="w-3.5 h-3.5 text-purple-400" />
              </div>

              {/* 3. AWS BEDROCK */}
              <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-800/70 text-center">
                <div className="flex items-center justify-center gap-1.5 text-purple-300 font-bold mb-0.5">
                  <Cpu className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-xs">AMAZON BEDROCK</span>
                </div>
                <p className="text-[11px] text-purple-200 font-medium">Handles ambiguity and generates candidate matches</p>
                <p className="text-[9.5px] text-purple-300/70 mt-0.5">
                  Proposes candidate matches for messy descriptions and manufacturer variants
                </p>
              </div>

              {/* Connector */}
              <div className="flex justify-center text-slate-600 -my-1">
                <ArrowDown className="w-3.5 h-3.5 text-amber-400" />
              </div>

              {/* 4. DETERMINISTIC VERIFICATION */}
              <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-700/80 text-center">
                <div className="flex items-center justify-center gap-1.5 text-amber-300 font-bold mb-0.5">
                  <ShieldCheck className="w-4 h-4 text-amber-400" />
                  <span className="text-xs uppercase tracking-wide">DETERMINISTIC VERIFICATION</span>
                </div>
                <p className="text-[11px] text-amber-200 font-semibold">Evidence decides</p>
                <p className="text-[10px] text-amber-300/80 mt-0.5">
                  Only deterministic evidence can produce <strong>CONFIRMED</strong>
                </p>
              </div>

              {/* Connector */}
              <div className="flex justify-center text-slate-600 -my-1">
                <ArrowDown className="w-3.5 h-3.5 text-slate-400" />
              </div>

              {/* 5. THREE OUTCOMES */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {/* CONFIRMED */}
                <div className="p-2.5 rounded-xl bg-red-950/30 border border-red-800/80">
                  <div className="flex items-center gap-1.5 text-red-400 font-bold mb-1">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>CONFIRMED</span>
                  </div>
                  <p className="text-[10px] text-red-200/90 leading-snug">
                    Exact deterministic evidence supports inclusion in recall scope.
                  </p>
                </div>

                {/* NEEDS REVIEW */}
                <div className="p-2.5 rounded-xl bg-amber-950/30 border border-amber-800/80">
                  <div className="flex items-center gap-1.5 text-amber-400 font-bold mb-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>NEEDS REVIEW</span>
                  </div>
                  <p className="text-[10px] text-amber-200/90 leading-snug">
                    Evidence suggests a possible match, but deterministic proof is incomplete.
                  </p>
                </div>

                {/* NOT AFFECTED */}
                <div className="p-2.5 rounded-xl bg-emerald-950/30 border border-emerald-800/80">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-bold mb-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>NOT AFFECTED</span>
                  </div>
                  <p className="text-[10px] text-emerald-200/90 leading-snug">
                    Available evidence does not support inclusion.
                  </p>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center text-slate-600 -my-1">
                <ArrowDown className="w-3.5 h-3.5 text-blue-400" />
              </div>

              {/* 6. PERSISTENCE */}
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <p className="text-[11px] font-bold text-white">EVIDENCE + AUDIT PERSISTENCE</p>
                <div className="flex items-center justify-center gap-4 mt-1 text-[10px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <Archive className="w-3 h-3 text-emerald-400" />
                    <strong>Amazon S3:</strong> Inventory file
                  </span>
                  <span className="text-slate-700">|</span>
                  <span className="flex items-center gap-1">
                    <Database className="w-3 h-3 text-blue-400" />
                    <strong>Amazon DynamoDB:</strong> Audit history
                  </span>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center text-slate-600 -my-1">
                <ArrowDown className="w-3.5 h-3.5 text-cyan-400" />
              </div>

              {/* 7. DASHBOARD & HISTORY */}
              <div className="p-2.5 rounded-xl bg-blue-950/20 border border-blue-800/60 text-center">
                <p className="text-xs font-bold text-cyan-300">RECLARO DASHBOARD &amp; AUDIT HISTORY</p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Interactive evidence inspection, diagnostic drawer, and historical audit records
                </p>
              </div>
            </div>
          ) : (
            /* ─────────────────────────────────────────────────────────────
               TAB 2: AWS ARCHITECTURE
               Request & Data Path: Browser → Amplify → API Gateway → Lambda (openFDA, Bedrock, S3, DynamoDB)
               ───────────────────────────────────────────────────────────── */
            <div className="space-y-3">
              {/* Visual Deployment Flow */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <p className="text-[11px] font-bold text-white mb-2.5">
                  Production Request &amp; Execution Path
                </p>

                <div className="space-y-2">
                  {/* Step 1: Browser */}
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Monitor className="w-3.5 h-3.5 text-blue-400" />
                      <span className="font-bold text-slate-200 text-[11px]">Browser</span>
                    </div>
                    <span className="text-[10px] text-slate-400">User interface</span>
                  </div>

                  <div className="flex justify-center text-slate-600 -my-0.5">
                    <ArrowDown className="w-3 h-3" />
                  </div>

                  {/* Step 2: Amplify */}
                  <div className="p-2 rounded-lg bg-slate-900 border border-amber-900/50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Cloud className="w-3.5 h-3.5 text-amber-400" />
                      <span className="font-bold text-amber-300 text-[11px]">AWS Amplify Hosting</span>
                    </div>
                    <span className="text-[10px] text-slate-400">Frontend hosting</span>
                  </div>

                  <div className="flex justify-center text-slate-600 -my-0.5">
                    <ArrowDown className="w-3 h-3" />
                  </div>

                  {/* Step 3: API Gateway */}
                  <div className="p-2 rounded-lg bg-slate-900 border border-indigo-900/50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Server className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="font-bold text-indigo-300 text-[11px]">Amazon API Gateway</span>
                    </div>
                    <span className="text-[10px] text-slate-400">HTTP API entry point</span>
                  </div>

                  <div className="flex justify-center text-slate-600 -my-0.5">
                    <ArrowDown className="w-3 h-3" />
                  </div>

                  {/* Step 4: Lambda */}
                  <div className="p-3 rounded-lg bg-slate-900 border border-orange-900/60">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-3.5 h-3.5 text-orange-400" />
                        <span className="font-bold text-orange-300 text-[11px]">AWS Lambda</span>
                      </div>
                      <span className="text-[10px] text-slate-400">Backend/API execution</span>
                    </div>

                    {/* Integrated services */}
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
                      <div className="p-2 rounded bg-slate-950 border border-cyan-900/40">
                        <div className="flex items-center gap-1.5 text-cyan-300 font-bold text-[10px]">
                          <Globe className="w-3 h-3 text-cyan-400" />
                          <span>openFDA</span>
                        </div>
                        <p className="text-[9px] text-slate-400 mt-0.5">Live recall data</p>
                      </div>

                      <div className="p-2 rounded bg-slate-950 border border-purple-900/40">
                        <div className="flex items-center gap-1.5 text-purple-300 font-bold text-[10px]">
                          <Cpu className="w-3 h-3 text-purple-400" />
                          <span>Amazon Bedrock</span>
                        </div>
                        <p className="text-[9px] text-slate-400 mt-0.5">AI candidate generation</p>
                      </div>

                      <div className="p-2 rounded bg-slate-950 border border-emerald-900/40">
                        <div className="flex items-center gap-1.5 text-emerald-300 font-bold text-[10px]">
                          <Archive className="w-3 h-3 text-emerald-400" />
                          <span>Amazon S3</span>
                        </div>
                        <p className="text-[9px] text-slate-400 mt-0.5">Uploaded inventory artifact storage</p>
                      </div>

                      <div className="p-2 rounded bg-slate-950 border border-blue-900/40">
                        <div className="flex items-center gap-1.5 text-blue-300 font-bold text-[10px]">
                          <Database className="w-3 h-3 text-blue-400" />
                          <span>Amazon DynamoDB</span>
                        </div>
                        <p className="text-[9px] text-slate-400 mt-0.5">Audit runs and history</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Service Table */}
              <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950">
                <table className="w-full text-left text-xs">
                  <thead className="text-[9.5px] uppercase font-mono bg-slate-900 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2 px-3">AWS Service</th>
                      <th className="py-2 px-3">Actual role in Reclaro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-[10.5px]">
                    <tr>
                      <td className="py-1.5 px-3 font-semibold text-amber-300">Amplify</td>
                      <td className="py-1.5 px-3 text-slate-300">Frontend hosting</td>
                    </tr>
                    <tr>
                      <td className="py-1.5 px-3 font-semibold text-indigo-300">API Gateway</td>
                      <td className="py-1.5 px-3 text-slate-300">HTTP API entry point</td>
                    </tr>
                    <tr>
                      <td className="py-1.5 px-3 font-semibold text-orange-300">Lambda</td>
                      <td className="py-1.5 px-3 text-slate-300">Backend/API execution</td>
                    </tr>
                    <tr>
                      <td className="py-1.5 px-3 font-semibold text-cyan-300">openFDA</td>
                      <td className="py-1.5 px-3 text-slate-300">Live recall data</td>
                    </tr>
                    <tr>
                      <td className="py-1.5 px-3 font-semibold text-purple-300">Bedrock</td>
                      <td className="py-1.5 px-3 text-slate-300">AI candidate generation</td>
                    </tr>
                    <tr>
                      <td className="py-1.5 px-3 font-semibold text-emerald-300">S3</td>
                      <td className="py-1.5 px-3 text-slate-300">Uploaded inventory artifact storage</td>
                    </tr>
                    <tr>
                      <td className="py-1.5 px-3 font-semibold text-blue-300">DynamoDB</td>
                      <td className="py-1.5 px-3 text-slate-300">Audit runs and history</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="bg-slate-950 px-5 py-2.5 border-t border-slate-800 flex items-center justify-between flex-shrink-0">
          <span className="text-[10px] text-slate-500">
            Reclaro Architecture · Only confirmed AWS services
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
