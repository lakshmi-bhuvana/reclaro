export type MatchStatus = 'CONFIRMED' | 'NEEDS_REVIEW' | 'NOT_AFFECTED';

export interface Recall {
  recall_id: string;
  recalling_firm: string;
  product_description: string;
  product_code?: string;
  reason_for_recall?: string;
  action?: string;
  classification?: string;
  event_date_initiated?: string;
  code_info?: string;
  source_url?: string;
}

export interface NormalizedRecall {
  recall_id: string;
  manufacturer: string;
  product_families: string[];
  models: string[];
  catalog_numbers: string[];
  udi_di: string[];
  lot_ranges: string[];
  serial_ranges: string[];
  action?: string;
  risk_class?: string;
}

export interface InventoryItem {
  inventory_id: string;
  manufacturer: string;
  product_name: string;
  model?: string;
  catalog_number?: string;
  udi_di?: string;
  lot_number?: string;
  serial_number?: string;
  quantity?: number;
  location?: string;
}

export interface MatchResult {
  inventory_id: string;
  recall_id: string;
  status: MatchStatus;
  signals: string[];
  evidence: string;
  recommended_action: string;
}

export interface RecallSearchResponse {
  total: number;
  recalls: Recall[];
}

export interface MatchResponse {
  recall: Recall;
  normalized_recall: NormalizedRecall;
  total_audited: number;
  confirmed_count: number;
  needs_review_count: number;
  not_affected_count: number;
  results: MatchResult[];
}
