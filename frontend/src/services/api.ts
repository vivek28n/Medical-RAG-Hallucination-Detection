import type { AskResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  statusCode?: number;
  constructor(message: string, statusCode?: number) {
    super(message);
    this.statusCode = statusCode;
    this.name = 'ApiError';
  }
}

export interface HealthStatus {
  status: 'ok' | 'degraded';
  ready: boolean;
  models_loaded: {
    embedding: boolean;
    faiss_index: boolean;
    nli: boolean;
    gemini: boolean;
  };
}

export const checkSystemHealth = async (): Promise<HealthStatus> => {
  const response = await fetch(`${API_BASE_URL}/health`);
  return await response.json();
};

export const askMedicalQuestion = async (
  query: string,
  signal?: AbortSignal
): Promise<AskResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
      signal,
    });

    if (!response.ok) {
      let serverMessage = '';
      try {
        const errorJson = await response.json();
        if (errorJson && typeof errorJson.detail === 'string') {
          serverMessage = errorJson.detail;
        } else if (errorJson && Array.isArray(errorJson.detail) && errorJson.detail[0]?.msg) {
          serverMessage = errorJson.detail[0].msg;
        }
      } catch {
        // Response body was not JSON
      }

      if (response.status === 422) {
        throw new ApiError(serverMessage || 'Invalid question format. Please enter a valid medical question.', 422);
      }
      if (response.status === 503) {
        throw new ApiError(serverMessage || 'The medical verification service is initializing or temporarily unavailable.', 503);
      }
      if (response.status === 500) {
        throw new ApiError(serverMessage || 'An unexpected error occurred during the review process.', 500);
      }
      throw new ApiError(serverMessage || `Server returned status ${response.status}`, response.status);
    }

    const data: AskResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw error;
    }
    throw new ApiError('Network error. MedGuide could not connect to the backend server (ensure port 8000 is active).');
  }
};

export interface BenchmarkResponse {
  provenance: import('../types/api').BenchmarkProvenance;
  items: import('../types/api').BenchmarkItem[];
  total_items: number;
}

export const fetchBenchmark = async (): Promise<BenchmarkResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation/benchmark`);
  if (!response.ok) {
    throw new ApiError('Failed to fetch benchmark metadata');
  }
  return await response.json();
};

export const runEvaluationBenchmark = async (): Promise<import('../types/api').EvaluationReport> => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation/run`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new ApiError('Failed to run benchmark evaluation');
  }
  return await response.json();
};

export const exportEvaluationMarkdown = async (
  useLegacyHypothesis: boolean = false
): Promise<import('../types/api').ExportReportResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation/export/markdown?use_legacy_hypothesis=${useLegacyHypothesis}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new ApiError('Failed to export evaluation report as Markdown');
  }
  return await response.json();
};

export const exportEvaluationJson = async (
  useLegacyHypothesis: boolean = false
): Promise<import('../types/api').ExportReportResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation/export/json?use_legacy_hypothesis=${useLegacyHypothesis}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new ApiError('Failed to export evaluation report as JSON');
  }
  return await response.json();
};

export interface ChunkQueryParams {
  page?: number;
  search?: string;
  chunk_type?: 'all' | 'clinical' | 'reference';
  offset?: number;
  limit?: number;
}

export const fetchKnowledgeBaseOverview = async (): Promise<import('../types/api').KnowledgeBaseOverview> => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/overview`);
  if (!response.ok) {
    throw new ApiError('Failed to fetch knowledge base overview');
  }
  return await response.json();
};

export const fetchKnowledgeBaseChunks = async (
  params: ChunkQueryParams = {}
): Promise<import('../types/api').ChunkListResponse> => {
  const query = new URLSearchParams();
  if (params.page !== undefined && params.page !== null) query.set('page', String(params.page));
  if (params.search) query.set('search', params.search);
  if (params.chunk_type) query.set('chunk_type', params.chunk_type);
  if (params.offset !== undefined) query.set('offset', String(params.offset));
  if (params.limit !== undefined) query.set('limit', String(params.limit));

  const qs = query.toString();
  const url = `${API_BASE_URL}/api/knowledge-base/chunks${qs ? `?${qs}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new ApiError('Failed to fetch knowledge base chunks');
  }
  return await response.json();
};
