/**
 * API client for FastAPI backend.
 * 
 * Enterprise-compliant: No credentials, only calls FastAPI endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type Sentiment = 'Happy' | 'Bit Irritated' | 'Moderately Concerned' | 'Anger' | 'Frustrated';

export interface Thread {
  thread_id: string;
  last_message_ts: string;
  message_count: number;
  thread_status: 'open' | 'closed';
  sentiment: Sentiment | string;
  confidence: number;
  prompt_version: string;
  model_name: string;
  // New fields from v_thread_state_final
  next_action_owner?: 'org' | 'customer' | 'none';
  status_reason?: string;
  status_source?: 'llm' | 'heuristic';
  status_confidence?: number;
}

export interface MonthlyAggregate {
  month: string;
  thread_count: number;
  happy_threads: number;
  bit_irritated_threads: number;
  moderately_concerned_threads: number;
  anger_threads: number;
  frustrated_threads: number;
}

/**
 * Fetch threads from the API
 */
export async function getThreads(limit: number = 10): Promise<Thread[]> {
  const response = await fetch(`${API_BASE_URL}/api/threads?limit=${limit}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch threads: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch monthly aggregates from the API
 */
export async function getMonthlyAggregates(months: number = 6): Promise<MonthlyAggregate[]> {
  const response = await fetch(`${API_BASE_URL}/api/threads/aggregates/monthly?months=${months}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch monthly aggregates: ${response.statusText}`);
  }

  return response.json();
}

