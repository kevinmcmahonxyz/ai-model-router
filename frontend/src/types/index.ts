/**
 * TypeScript types for API responses
 */

export interface UsageStats {
  total_requests: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  success_rate: number;
  by_provider: ProviderStats[];
  by_model: ModelStats[];
  daily_stats: DailyStats[];
}

export interface ProviderStats {
  provider: string;
  requests: number;
  cost_usd: number;
}

export interface ModelStats {
  model: string;
  requests: number;
  cost_usd: number;
}

export interface DailyStats {
  date: string;
  requests: number;
  cost_usd: number;
}

export interface RequestSummary {
  id: string;
  created_at: string;
  model: string;
  provider: string;
  prompt_preview: string;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
  latency_ms: number;
  status: string;
}

export interface RequestListResponse {
  requests: RequestSummary[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface RequestDetail {
  id: string;
  created_at: string;
  completed_at: string | null;
  model: string;
  provider: string;
  prompt_text: string;
  response_text: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  total_tokens: number | null;
  input_cost_usd: number | null;
  output_cost_usd: number | null;
  total_cost_usd: number | null;
  latency_ms: number | null;
  status: string;
  error_message: string | null;
}

export interface ModelInfo {
  id: number;
  model_id: string;
  display_name: string;
  provider: string;
  input_price_per_1m_tokens: number;
  output_price_per_1m_tokens: number;
  context_window: number | null;
  is_active: boolean;
}