import React, { useEffect } from 'react';
import {
  X,
  ShieldAlert,
  AlertCircle,
  CheckCircle2,
  FileText,
  Activity,
  ArrowUpRight,
  Package,
  Tag,
  Layers,
  ListChecks,
  ExternalLink,
} from 'lucide-react';
import {
  MatchResult,
  Recall,
  NormalizedRecall,
  MatchStatus,
} from '../types';

// ---------------------------------------------------------------------------
// Signal metadata
// ---------------------------------------------------------------------------

type SignalCategory = 'deterministic' | 'candidate' | 'scope';

interface SignalMeta {
  label: string;
  category: SignalCategory;
}

const SIGNAL_MAP: Record<string, SignalMeta> = {
  MANUFACTURER_MATCH: {
    label: 'Manufacturer matched',
    category: 'deterministic',
  },

  EXACT_UDI_MATCH: {
    label: 'UDI-DI matched',
    category: 'deterministic',
  },

  EXACT_CATALOG_MATCH: {
    label: 'Catalog number matched',
    category: 'deterministic',
  },

  EXACT_MODEL_MATCH: {
    label: 'Model matched',
    category: 'deterministic',
  },

  EXACT_LOT_MATCH: {
    label: 'Lot matched',
    category: 'deterministic',
  },

  EXACT_SERIAL_MATCH: {
    label: 'Serial number matched',
    category: 'deterministic',
  },

  FUZZY_MODEL_MATCH: {
    label: 'Model candidate match',
    category: 'candidate',
  },

  FUZZY_CATALOG_MATCH: {
    label: 'Catalog candidate match',
    category: 'candidate',
  },

  PRODUCT_FAMILY_MATCH: {
    label: 'Product family matched',
    category: 'candidate',
  },

  LOT_MATCH_ALL: {
    label: 'Recall applies to all lots',
    category: 'scope',
  },

  SERIAL_SCOPE_ALL: {
    label: 'Recall applies to all serials',
    category: 'scope',
  },
};

function resolveSignal(raw: string): SignalMeta {
  return (
    SIGNAL_MAP[raw] ?? {
      label: raw,
      category: 'candidate',
    }
  );
}

// ---------------------------------------------------------------------------
// Status configuration
// ---------------------------------------------------------------------------

function statusConfig(status: MatchStatus) {
  switch (status) {
    case 'CONFIRMED':
      return {
        Icon: ShieldAlert,
        label: 'CONFIRMED',
        tagColor:
          'text-red-400 bg-red-950/60 border-red-800',
        headerBg:
          'bg-red-950/20 border-red-800/60',
        iconBg:
          'bg-red-950 border-red-800 text-red-400',
        explanation:
          'Deterministic evidence establishes that this inventory record falls within the selected recall scope.',
        nextStep:
          'Review the applicable manufacturer / FDA recall instructions for potentially affected inventory.',
      };

    case 'NEEDS_REVIEW':
      return {
        Icon: AlertCircle,
        label: 'NEEDS REVIEW',
        tagColor:
          'text-amber-400 bg-amber-950/60 border-amber-800',
        headerBg:
          'bg-amber-950/20 border-amber-800/60',
        iconBg:
          'bg-amber-950 border-amber-800 text-amber-400',
        explanation:
          'Potential matching evidence exists, but the available identifiers are insufficient for deterministic confirmation.',
        nextStep:
          'Review the inventory record and applicable recall instructions to determine whether additional identifiers are available.',
      };

    case 'NOT_AFFECTED':
    default:
      return {
        Icon: CheckCircle2,
        label: 'NOT AFFECTED',
        tagColor:
          'text-emerald-400 bg-emerald-950/60 border-emerald-800',
        headerBg:
          'bg-emerald-950/20 border-emerald-800/60',
        iconBg:
          'bg-emerald-950 border-emerald-800 text-emerald-400',
        explanation:
          'No matching evidence was found within the available recall scope and inventory identifiers.',
        nextStep:
          'No matching recall evidence was found in the available inventory fields. This is a screening outcome, not a safety determination.',
      };
  }
}

// ---------------------------------------------------------------------------
// Small reusable UI helpers
// ---------------------------------------------------------------------------

const Field: React.FC<{
  label: string;
  value?: string | number | null;
}> = ({ label, value }) => (
  <div className="min-w-0">
    <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-1">
      {label}
    </div>

    <div
      className={`text-xs break-words ${value
          ? 'text-slate-200'
          : 'text-slate-600 italic'
        }`}
    >
      {value ?? 'Not provided'}
    </div>
  </div>
);

const PillList: React.FC<{
  items: string[];
}> = ({ items }) => {
  if (!items || items.length === 0) {
    return (
      <span className="text-xs text-slate-600 italic">
        Not provided
      </span>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, index) => (
        <span
          key={`${item}-${index}`}
          className="px-2 py-1 rounded-md bg-slate-950 border border-slate-700 text-[10px] font-mono text-slate-300 break-all"
        >
          {item}
        </span>
      ))}
    </div>
  );
};

const SignalPill: React.FC<{
  signal: string;
}> = ({ signal }) => {
  const meta = resolveSignal(signal);

  const classes =
    meta.category === 'deterministic'
      ? 'bg-emerald-950/50 border-emerald-800/70 text-emerald-300'
      : meta.category === 'candidate'
        ? 'bg-amber-950/50 border-amber-800/70 text-amber-300'
        : 'bg-cyan-950/50 border-cyan-800/70 text-cyan-300';

  return (
    <span
      className={`px-2.5 py-1.5 rounded-md border text-[10px] font-medium ${classes}`}
    >
      {meta.label}
    </span>
  );
};

const Section: React.FC<{
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}> = ({ title, icon, children }) => (
  <section className="space-y-3">
    <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
      {icon && (
        <span className="text-cyan-400 flex-shrink-0">
          {icon}
        </span>
      )}

      <h4 className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
        {title}
      </h4>
    </div>

    {children}
  </section>
);

// ---------------------------------------------------------------------------
// Decision explanation
// ---------------------------------------------------------------------------

function buildDecisionExplanation(
  result: MatchResult,
  _normalized: NormalizedRecall | null,
): string {
  const signals = result.signals;

  if (result.status === 'CONFIRMED') {
    const parts: string[] = [];

    if (signals.includes('MANUFACTURER_MATCH')) {
      parts.push('Manufacturer matched');
    }

    if (signals.includes('EXACT_UDI_MATCH')) {
      parts.push('UDI-DI is within the recalled scope');
    }

    if (signals.includes('EXACT_CATALOG_MATCH')) {
      parts.push(
        'Catalog number is within the recalled catalog scope',
      );
    }

    if (signals.includes('EXACT_MODEL_MATCH')) {
      parts.push(
        'Model number is within the recalled model scope',
      );
    }

    if (signals.includes('EXACT_LOT_MATCH')) {
      parts.push(
        'Lot number is within the recalled lot scope',
      );
    }

    if (signals.includes('LOT_MATCH_ALL')) {
      parts.push('Recall scope encompasses all lots');
    }

    if (signals.includes('EXACT_SERIAL_MATCH')) {
      parts.push(
        'Serial number is within the recalled serial scope',
      );
    }

    if (signals.includes('SERIAL_SCOPE_ALL')) {
      parts.push(
        'Recall scope encompasses all serials',
      );
    }

    return parts.length > 0
      ? `${parts.join('. ')}.`
      : 'Deterministic identifier evidence established a match against the recall scope.';
  }

  if (result.status === 'NEEDS_REVIEW') {
    const matched: string[] = [];
    const missing: string[] = [];

    if (signals.includes('MANUFACTURER_MATCH')) {
      matched.push('Manufacturer');
    }

    if (
      signals.includes('EXACT_MODEL_MATCH') ||
      signals.includes('FUZZY_MODEL_MATCH')
    ) {
      matched.push('Model');
    }

    if (
      signals.includes('EXACT_CATALOG_MATCH') ||
      signals.includes('FUZZY_CATALOG_MATCH')
    ) {
      matched.push('Catalog number');
    }

    if (signals.includes('PRODUCT_FAMILY_MATCH')) {
      matched.push('Product family');
    }

    if (!signals.includes('EXACT_UDI_MATCH')) {
      missing.push('UDI-DI');
    }

    if (!signals.includes('EXACT_CATALOG_MATCH')) {
      missing.push('exact catalog number');
    }

    if (
      !signals.includes('EXACT_LOT_MATCH') &&
      !signals.includes('LOT_MATCH_ALL')
    ) {
      missing.push('lot verification');
    }

    if (
      !signals.includes('EXACT_SERIAL_MATCH') &&
      !signals.includes('SERIAL_SCOPE_ALL')
    ) {
      missing.push('serial verification');
    }

    const matchedStr =
      matched.length > 0
        ? `${matched.join(' and ')} match`
        : 'Partial match';

    const missingStr =
      missing.length > 0
        ? `, but deterministic evidence is unavailable for: ${missing.join(
          ', ',
        )}.`
        : ', but complete deterministic confirmation is not possible from available data.';

    return matchedStr + missingStr;
  }

  const noMatch: string[] = [];

  if (!signals.includes('MANUFACTURER_MATCH')) {
    noMatch.push(
      'Manufacturer did not match the recalling firm',
    );
  }

  if (
    !signals.includes('EXACT_CATALOG_MATCH') &&
    !signals.includes('FUZZY_CATALOG_MATCH')
  ) {
    noMatch.push('No catalog number match found');
  }

  if (
    !signals.includes('EXACT_MODEL_MATCH') &&
    !signals.includes('FUZZY_MODEL_MATCH')
  ) {
    noMatch.push('No model number match found');
  }

  return noMatch.length > 0
    ? `${noMatch.join('. ')}.`
    : 'No matching identifiers were found within the recalled scope.';
}

// ---------------------------------------------------------------------------
// FDA source URL
// ---------------------------------------------------------------------------

function getFDARecallUrl(recall: Recall): string {
  /*
   * Prefer the backend-provided URL when it contains a valid recall ID.
   * Otherwise construct the official FDA CDRH recall URL directly.
   */
  const suppliedUrl = recall.source_url?.trim();

  if (
    suppliedUrl &&
    suppliedUrl.includes('accessdata.fda.gov') &&
    suppliedUrl.includes(`id=${recall.recall_id}`)
  ) {
    return suppliedUrl;
  }

  return `https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=${encodeURIComponent(
    recall.recall_id,
  )}`;
}

// ---------------------------------------------------------------------------
// Evidence Drawer
// ---------------------------------------------------------------------------

export interface EvidenceDrawerProps {
  result: MatchResult | null;
  recall: Recall | null;
  normalizedRecall: NormalizedRecall | null;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<
  EvidenceDrawerProps
> = ({
  result,
  recall,
  normalizedRecall,
  onClose,
}) => {
    useEffect(() => {
      if (!result) return;

      const handler = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          onClose();
        }
      };

      document.addEventListener(
        'keydown',
        handler,
      );

      return () => {
        document.removeEventListener(
          'keydown',
          handler,
        );
      };
    }, [result, onClose]);

    if (!result) {
      return null;
    }

    const cfg = statusConfig(result.status);
    const { Icon } = cfg;

    const decision = buildDecisionExplanation(
      result,
      normalizedRecall,
    );

    const deterministic = result.signals.filter(
      (signal) =>
        resolveSignal(signal).category ===
        'deterministic',
    );

    const candidate = result.signals.filter(
      (signal) =>
        resolveSignal(signal).category ===
        'candidate',
    );

    const scope = result.signals.filter(
      (signal) =>
        resolveSignal(signal).category ===
        'scope',
    );

    const fdaUrl = recall
      ? getFDARecallUrl(recall)
      : null;

    return (
      <>
        {/* ----------------------------------------------------------------- */}
        {/* Backdrop                                                          */}
        {/* ----------------------------------------------------------------- */}

        <div
          className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />

        {/* ----------------------------------------------------------------- */}
        {/* Drawer                                                            */}
        {/* ----------------------------------------------------------------- */}

        <div
          className="fixed inset-y-0 right-0 z-50 w-full max-w-xl flex flex-col bg-slate-900 border-l border-slate-700 shadow-2xl shadow-black/50"
          role="dialog"
          aria-modal="true"
          aria-label="Evidence Drawer"
        >
          {/* =============================================================== */}
          {/* HEADER                                                           */}
          {/* =============================================================== */}

          <div
            className={`flex-shrink-0 px-5 py-4 border-b border-slate-700 ${cfg.headerBg}`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 min-w-0">
                <div
                  className={`flex-shrink-0 p-2.5 rounded-xl border ${cfg.iconBg}`}
                >
                  <Icon className="w-5 h-5" />
                </div>

                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${cfg.tagColor}`}
                    >
                      {cfg.label}
                    </span>

                    <span className="font-mono text-[10px] text-cyan-300 font-bold bg-slate-950 px-2 py-1 rounded border border-slate-800">
                      {result.inventory_id}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                    {cfg.explanation}
                  </p>

                  <p className="text-[10px] text-slate-500 mt-1.5 font-mono">
                    Evaluated against FDA Recall{' '}
                    <span className="text-slate-300 font-bold">
                      {result.recall_id}
                    </span>
                  </p>
                </div>
              </div>

              <button
                onClick={onClose}
                className="flex-shrink-0 p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                aria-label="Close evidence drawer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* =============================================================== */}
          {/* SCROLLABLE BODY                                                  */}
          {/* =============================================================== */}

          <div className="flex-1 overflow-y-auto px-5 py-5 space-y-7">

            {/* ============================================================= */}
            {/* INVENTORY RECORD                                               */}
            {/* ============================================================= */}

            <Section
              title="Inventory Record"
              icon={<Package className="w-4 h-4" />}
            >
              <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                  <Field
                    label="Inventory ID"
                    value={result.inventory_id}
                  />

                  <Field
                    label="Recall ID"
                    value={result.recall_id}
                  />
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800">
                  <p className="text-[10px] leading-relaxed text-slate-500">
                    Inventory fields used by the backend matcher are
                    represented in the verification signals below. The
                    backend rule engine remains authoritative for the
                    classification.
                  </p>
                </div>
              </div>
            </Section>

            {/* ============================================================= */}
            {/* FDA RECALL SCOPE                                               */}
            {/* ============================================================= */}

            {recall && (
              <Section
                title="FDA Recall Scope"
                icon={<FileText className="w-4 h-4" />}
              >
                <div className="rounded-xl border border-slate-800 bg-slate-950/30 p-4 space-y-5">

                  <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                    <Field
                      label="Recall ID"
                      value={recall.recall_id}
                    />

                    <Field
                      label="Classification"
                      value={recall.classification}
                    />

                    <Field
                      label="Recalling Firm"
                      value={recall.recalling_firm}
                    />

                    <Field
                      label="Initiated"
                      value={recall.event_date_initiated}
                    />
                  </div>

                  {/* Product description */}

                  <div>
                    <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-1.5">
                      Product Description
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {recall.product_description ||
                        'Not provided'}
                    </p>
                  </div>

                  {/* Reason */}

                  {recall.reason_for_recall && (
                    <div>
                      <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-1.5">
                        Reason for Recall
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed">
                        {recall.reason_for_recall}
                      </p>
                    </div>
                  )}

                  {/* Required action */}

                  {recall.action && (
                    <div>
                      <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-1.5">
                        Required Action
                      </div>

                      <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3">
                        <p className="text-xs text-amber-200 leading-relaxed">
                          {recall.action}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Scope / Code Info */}

                  {recall.code_info && (
                    <div>
                      <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-1.5">
                        Scope / Code Info
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed font-mono break-words">
                        {recall.code_info}
                      </p>
                    </div>
                  )}

                  {/* Normalized scope */}

                  {normalizedRecall && (
                    <div className="pt-4 border-t border-slate-800 space-y-5">

                      <div>
                        <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-2">
                          Product Families
                        </div>

                        <PillList
                          items={
                            normalizedRecall.product_families
                          }
                        />
                      </div>

                      <div>
                        <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-2">
                          Recalled Catalog Numbers
                        </div>

                        <PillList
                          items={
                            normalizedRecall.catalog_numbers
                          }
                        />
                      </div>

                      <div>
                        <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-2">
                          Recalled Models
                        </div>

                        <PillList
                          items={normalizedRecall.models}
                        />
                      </div>

                      <div>
                        <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-2">
                          UDI-DI
                        </div>

                        <PillList
                          items={normalizedRecall.udi_di}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-5">
                        <div>
                          <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-2">
                            Lot Scope
                          </div>

                          <PillList
                            items={
                              normalizedRecall.lot_ranges
                            }
                          />
                        </div>

                        <div>
                          <div className="text-[9px] uppercase tracking-[0.14em] text-slate-500 font-semibold mb-2">
                            Serial Scope
                          </div>

                          <PillList
                            items={
                              normalizedRecall.serial_ranges
                            }
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </Section>
            )}

            {/* ============================================================= */}
            {/* VERIFICATION SIGNALS                                           */}
            {/* ============================================================= */}

            <Section
              title="Verification Signals"
              icon={<Activity className="w-4 h-4" />}
            >
              {result.signals.length === 0 ? (
                <div className="rounded-xl border border-slate-800 bg-slate-950/30 p-4">
                  <p className="text-xs text-slate-500 italic">
                    No matching rule signals were triggered.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">

                  {/* Deterministic */}

                  {deterministic.length > 0 && (
                    <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/10 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-400">
                          Deterministic Evidence
                        </p>

                        <span className="text-[9px] font-mono text-emerald-500">
                          AUTHORITATIVE
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {deterministic.map((signal) => (
                          <SignalPill
                            key={signal}
                            signal={signal}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Candidate */}

                  {candidate.length > 0 && (
                    <div className="rounded-xl border border-amber-900/50 bg-amber-950/10 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-amber-400">
                          Candidate / Semantic Evidence
                        </p>

                        <span className="text-[9px] font-mono text-amber-500">
                          SUPPORTING
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {candidate.map((signal) => (
                          <SignalPill
                            key={signal}
                            signal={signal}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Scope */}

                  {scope.length > 0 && (
                    <div className="rounded-xl border border-cyan-900/50 bg-cyan-950/10 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-cyan-400">
                          Scope Information
                        </p>

                        <span className="text-[9px] font-mono text-cyan-500">
                          RECALL SCOPE
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {scope.map((signal) => (
                          <SignalPill
                            key={signal}
                            signal={signal}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Section>

            {/* ============================================================= */}
            {/* WHY THIS DECISION                                              */}
            {/* ============================================================= */}

            <Section
              title="Why This Decision?"
              icon={<Layers className="w-4 h-4" />}
            >
              <div
                className={`rounded-xl border p-4 ${result.status === 'CONFIRMED'
                    ? 'border-red-900/50 bg-red-950/10'
                    : result.status === 'NEEDS_REVIEW'
                      ? 'border-amber-900/50 bg-amber-950/10'
                      : 'border-emerald-900/50 bg-emerald-950/10'
                  }`}
              >
                <p className="text-xs text-slate-200 leading-relaxed">
                  {decision}
                </p>
              </div>

              <p className="text-[10px] text-slate-500 leading-relaxed italic">
                This determination is based solely on identifiers
                present in the uploaded inventory record and recall
                scope data available from openFDA. The backend
                deterministic rule engine is the authoritative source
                for the classification.
              </p>
            </Section>

            {/* ============================================================= */}
            {/* RECOMMENDED NEXT STEP                                         */}
            {/* ============================================================= */}

            <Section
              title="Recommended Next Step"
              icon={<ListChecks className="w-4 h-4" />}
            >
              <div
                className={`rounded-xl border p-4 ${result.status === 'CONFIRMED'
                    ? 'bg-red-950/20 border-red-800/60 text-red-200'
                    : result.status === 'NEEDS_REVIEW'
                      ? 'bg-amber-950/20 border-amber-800/60 text-amber-200'
                      : 'bg-slate-800/60 border-slate-700 text-slate-300'
                  }`}
              >
                <div className="flex gap-3">
                  <ListChecks className="w-4 h-4 flex-shrink-0 mt-0.5 opacity-80" />

                  <p className="text-xs leading-relaxed">
                    {cfg.nextStep}
                  </p>
                </div>
              </div>
            </Section>

            {/* ============================================================= */}
            {/* FDA SOURCE                                                      */}
            {/* ============================================================= */}

            {recall && (
              <Section
                title="FDA Recall Source"
                icon={<Tag className="w-4 h-4" />}
              >
                <div className="rounded-xl border border-slate-800 bg-slate-950/30 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs text-slate-300 font-medium">
                        Official FDA recall record
                      </p>

                      <p className="text-[10px] text-slate-500 mt-1">
                        Recall ID {recall.recall_id}
                      </p>
                    </div>

                    {fdaUrl && (
                      <a
                        href={fdaUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-shrink-0 inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-cyan-800/70 bg-cyan-950/30 text-cyan-300 hover:text-cyan-200 hover:bg-cyan-950/50 transition-colors text-[10px] font-semibold"
                      >
                        View FDA Record
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>

                  <p className="text-[9px] text-slate-600 mt-3 leading-relaxed break-all">
                    {fdaUrl}
                  </p>
                </div>
              </Section>
            )}

            {/* ============================================================= */}
            {/* SOURCE / AUTHORITY NOTE                                       */}
            {/* ============================================================= */}

            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <div className="flex gap-3">
                <ShieldAlert className="w-4 h-4 text-cyan-500 flex-shrink-0 mt-0.5" />

                <div>
                  <p className="text-[10px] uppercase tracking-[0.14em] font-bold text-slate-400">
                    Verification Authority
                  </p>

                  <p className="text-[10px] text-slate-500 leading-relaxed mt-1.5">
                    AI or semantic matching may identify candidate
                    relationships, but CONFIRMED status is assigned only
                    by deterministic verification against the available
                    recall scope and inventory identifiers.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* =============================================================== */}
          {/* FOOTER                                                          */}
          {/* =============================================================== */}

          <div className="flex-shrink-0 px-5 py-3 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-[9px] text-slate-500">
              <Activity className="w-3.5 h-3.5 text-cyan-500" />
              <span>Evidence-backed verification</span>
            </div>

            <button
              onClick={onClose}
              className="px-5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </>
    );
  };