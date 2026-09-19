import React, { useState } from 'react';
import { Search, Filter, Eye, ShieldAlert, AlertCircle, CheckCircle2, ChevronRight } from 'lucide-react';
import { MatchResult, MatchStatus, InventoryItem } from '../types';

interface MatchResultsTableProps {
  results: MatchResult[];
  onInspect: (result: MatchResult) => void;
}

export const MatchResultsTable: React.FC<MatchResultsTableProps> = ({
  results,
  onInspect,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filtered = results.filter((res) => {
    const matchesFilter = filterStatus === 'ALL' || res.status === filterStatus;
    const matchesSearch =
      res.inventory_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.evidence.toLowerCase().includes(searchTerm.toLowerCase()) ||
      res.signals.some((s) => s.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const renderStatusBadge = (status: MatchStatus) => {
    switch (status) {
      case 'CONFIRMED':
        return (
          <span className="badge-confirmed px-2.5 py-1 rounded-full text-xs font-bold inline-flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
            CONFIRMED
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="badge-review px-2.5 py-1 rounded-full text-xs font-bold inline-flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            NEEDS REVIEW
          </span>
        );
      case 'NOT_AFFECTED':
        return (
          <span className="badge-safe px-2.5 py-1 rounded-full text-xs font-bold inline-flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            NOT AFFECTED
          </span>
        );
    }
  };

  return (
    <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
      {/* Table Toolbar */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/40">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Verification Results Audit ({filtered.length})
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter Buttons */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-[11px] font-medium">
            {['ALL', 'CONFIRMED', 'NEEDS_REVIEW', 'NOT_AFFECTED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  filterStatus === st
                    ? 'bg-cyan-600 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Table Search input */}
          <div className="relative">
            <input
              type="text"
              placeholder="Filter by ID or signal..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500 w-44"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2" />
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Inventory ID</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Matching Signals</th>
              <th className="py-3 px-4">Evidence Summary</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500 text-xs">
                  No inventory items match the selected status filter or search criteria.
                </td>
              </tr>
            ) : (
              filtered.map((res) => (
                <tr
                  key={res.inventory_id}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    res.status === 'CONFIRMED' ? 'bg-red-950/10' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-mono font-bold text-cyan-400">
                    {res.inventory_id}
                  </td>
                  <td className="py-3 px-4">{renderStatusBadge(res.status)}</td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {res.signals.length === 0 ? (
                        <span className="text-slate-500 font-mono text-[10px]">None</span>
                      ) : (
                        res.signals.map((sig) => (
                          <span
                            key={sig}
                            className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-[10px] font-mono text-slate-300"
                          >
                            {sig}
                          </span>
                        ))
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 max-w-md">
                    <p className="line-clamp-2 text-slate-300 leading-relaxed">
                      {res.evidence}
                    </p>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onInspect(res)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-cyan-600 text-cyan-300 hover:text-white border border-slate-700 transition-all font-semibold inline-flex items-center gap-1.5 text-xs"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      Inspect Evidence
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
