import { RecallSearchResponse, MatchResponse, Recall, NormalizedRecall, AuditRunListResponse, AuditDetail } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export async function fetchRecalls(search?: string): Promise<RecallSearchResponse> {
  const url = new URL(`${window.location.origin}${API_BASE_URL}/recalls`);
  url.searchParams.append('limit', '25');
  if (search) {
    url.searchParams.append('search', search);
  }

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`Failed to fetch FDA recalls: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchRecallDetail(recallId: string): Promise<{ recall: Recall; normalized_recall: NormalizedRecall }> {
  const res = await fetch(`${API_BASE_URL}/recalls/${encodeURIComponent(recallId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch recall detail: ${res.statusText}`);
  }
  return res.json();
}

export async function auditInventoryMatch(recallId: string, csvFile: File): Promise<MatchResponse> {
  const formData = new FormData();
  formData.append('recall_id', recallId);
  formData.append('file', csvFile);

  const res = await fetch(`${API_BASE_URL}/match`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Audit processing failed.');
  }

  return res.json();
}

export async function fetchAuditRuns(limit = 20): Promise<AuditRunListResponse> {
  const res = await fetch(`${API_BASE_URL}/audits?limit=${limit}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Unable to load audit history.');
  }
  return res.json();
}

export async function fetchAuditDetail(runId: string): Promise<AuditDetail> {
  const res = await fetch(`${API_BASE_URL}/audits/${encodeURIComponent(runId)}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Unable to load audit detail.');
  }
  return res.json();
}

