import React, { useState, useEffect } from 'react';
import { Search, AlertTriangle, FileText, CheckCircle2, ChevronRight, Layers, Tag } from 'lucide-react';
import { Recall, NormalizedRecall } from '../types';
import { fetchRecalls, fetchRecallDetail } from '../services/api';

interface RecallSelectorProps {
  selectedRecall: Recall | null;
  onSelectRecall: (recall: Recall, normalized: NormalizedRecall) => void;
}

export const RecallSelector: React.FC<RecallSelectorProps> = ({
  selectedRecall,
  onSelectRecall,
}) => {
  const [recalls, setRecalls] = useState<Recall[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const loadRecalls = async (query?: string) => {
    setLoading(true);
    setError(null);
    try {
      // Fire the normal search and an optional recall-ID direct lookup in parallel.
      // The ID lookup runs when the query resembles a recall ID (numeric string like
      // "81158" or alphanumeric like "Z-1092-2024") — no spaces, no common words.
      const looksLikeRecallId = query && /^[\w\-]+$/.test(query.trim()) && !/\s/.test(query.trim());

      const [data, directMatch] = await Promise.allSettled([
        fetchRecalls(query),
        looksLikeRecallId ? fetchRecallDetail(query!.trim()) : Promise.reject('skip'),
      ]);

      let recalls: import('../types').Recall[] = [];

      if (data.status === 'fulfilled') {
        recalls = data.value.recalls;
      } else {
        setError((data as PromiseRejectedResult).reason?.message || 'Failed to load FDA recalls.');
      }

      // If direct ID lookup found something not already in the list, prepend it.
      if (directMatch.status === 'fulfilled') {
        const found = directMatch.value.recall;
        const alreadyPresent = recalls.some((r) => r.recall_id === found.recall_id);
        if (!alreadyPresent) {
          recalls = [found, ...recalls];
        }
      }

      setRecalls(recalls);
    } catch (err: any) {
      setError(err.message || 'Failed to load FDA recalls.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecalls();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadRecalls(searchQuery);
  };


  const handleSelect = async (recall: Recall) => {
    try {
      const detail = await fetchRecallDetail(recall.recall_id);
      onSelectRecall(detail.recall, detail.normalized_recall);
    } catch (err) {
      // Fallback to raw selection
      onSelectRecall(recall, {
        recall_id: recall.recall_id,
        manufacturer: recall.recalling_firm,
        product_families: [],
        models: [],
        catalog_numbers: [],
        udi_di: [],
        lot_ranges: [],
        serial_ranges: [],
      });
    }
  };

  return (
    <div className="glass-panel p-5 rounded-xl border border-slate-800">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            1. Select FDA Device Recall
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Fetched directly from live openFDA Medical Device Recall API
          </p>
        </div>

        <form onSubmit={handleSearch} className="relative w-full sm:w-64">
          <input
            type="text"
            placeholder="Search firm or device..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-2.5 top-2" />
        </form>
      </div>

      {loading ? (
        <div className="py-8 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          Fetching live FDA recall data...
        </div>
      ) : error ? (
        <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-xs text-red-300">
          {error}
        </div>
      ) : recalls.length === 0 ? (
        <div className="py-6 text-center text-slate-500 text-xs">
          No medical device recalls found matching your query.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-1">
          {recalls.map((recall) => {
            const isSelected = selectedRecall?.recall_id === recall.recall_id;
            return (
              <div
                key={recall.recall_id}
                onClick={() => handleSelect(recall)}
                className={`p-3.5 rounded-lg border cursor-pointer transition-all ${isSelected
                    ? 'bg-slate-800/90 border-cyan-500 shadow-md shadow-cyan-950/50'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
                  }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-cyan-400">
                    {recall.recall_id}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${recall.classification === 'Class I'
                        ? 'bg-red-950 text-red-400 border border-red-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}
                  >
                    {recall.classification || 'Class II'}
                  </span>
                </div>

                <h3 className="text-xs font-semibold text-slate-200 mt-1.5 line-clamp-1">
                  {recall.recalling_firm}
                </h3>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                  {recall.product_description}
                </p>

                <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500 pt-2 border-t border-slate-800/80">
                  <span>Initiated: {recall.event_date_initiated || 'N/A'}</span>
                  {isSelected && (
                    <span className="text-cyan-400 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="w-3 h-3" /> Selected Scope
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
