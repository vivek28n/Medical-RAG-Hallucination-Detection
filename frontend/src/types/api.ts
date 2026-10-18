export interface Source {
  chunk_id: string;
  page?: number | null;
  text: string;
}

export interface ClaimEvidence {
  chunk_id: string;
  page?: number | null;
  text: string;
  similarity: number;
  entailment: number;
  contradiction: number;
  neutral: number;
  evidence_score: number;
}

export interface Claim {
  claim_number: number;
  claim: string;
  hypothesis: string;
  supported: boolean;
  status?: 'SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED' | string | null;
  evidence: ClaimEvidence | null;
}

export interface ClaimVerification {
  claims: Claim[];
  supported_claims: number;
  total_claims: number;
  consistency_score: number;
}

export interface Confidence {
  semantic_similarity: number;
  nli_entailment: number;
  retrieval_quality: number;
  claim_consistency: number;
  confidence_score: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface HallucinationDecision {
  decision: 'SUPPORTED' | 'POTENTIAL HALLUCINATION' | 'CONTRADICTED';
  claim_consistency: number;
  confidence_score: number;
  strong_contradictions: number;
}

export interface SelfCorrection {
  correction_needed: boolean;
  correction_applied: boolean;
  original_answer: string;
  corrected_answer?: string;
}

export interface StageTrace {
  stage_name: string;
  duration_ms: number;
  status: 'completed' | 'skipped' | 'failed';
  details?: Record<string, unknown>;
}

export interface PipelineTrace {
  total_duration_ms: number;
  stages: StageTrace[];
  timestamp: string;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  claim_verification: ClaimVerification;
  confidence: Confidence;
  hallucination_decision: HallucinationDecision;
  self_correction: SelfCorrection;
  pipeline_trace?: PipelineTrace;
}

// ─── Evaluation Lab Types ───────────────────────────────────────

export interface BenchmarkItem {
  id: string;
  claim: string;
  hypothesis?: string;
  ground_truth: 'SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED';
  principle?: string;
  citation_page?: number | null;
  booklet_page?: number | null;
  verification_status?: string | null;
  rationale?: string;
}

export interface ConfusionMatrix {
  labels: string[];
  matrix: number[][];
  total: number;
}

export interface MetricSummary {
  precision: number;
  recall: number;
  f1_score: number;
  specificity?: number;
}

export interface CitationAlignmentSummary {
  total_cited_items: number;
  matched: number;
  adjacent: number;
  mismatched: number;
  alignment_rate: number;
}

export interface EvaluationItemResult {
  id: string;
  claim: string;
  hypothesis: string;
  legacy_hypothesis?: string | null;
  ground_truth: 'SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED';
  predicted: 'SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED';
  is_correct: boolean;
  entailment: number;
  contradiction: number;
  similarity: number;
  evidence_score: number;
  citation_page?: number | null;
  booklet_page?: number | null;
  verification_status?: string | null;
  citation_alignment?: 'MATCHED' | 'ADJACENT_PAGE' | 'MISMATCHED' | 'NOT_APPLICABLE' | string;
  matched_chunk_id?: string | null;
  matched_page?: number | null;
  matched_text?: string | null;
}

export interface BenchmarkProvenance {
  source_document: string;
  publisher: string;
  document_pages: number;
  vector_chunks: number;
  benchmark_type?: string;
  dataset_scope?: string;
  page_verification_method?: string;
  label_definitions: Record<string, string>;
  limitations: string[];
  reproduction_instructions: string;
}

export interface BaselineComparisonRow {
  system: string;
  accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  supported_f1: number;
  contradiction_capable: boolean;
  notes: string;
}

export interface BaselineComparisonSummary {
  comparison_table: BaselineComparisonRow[];
  accuracy_gain: number;
  f1_gain: number;
}

export interface ExportReportResponse {
  content: string;
  filename: string;
  format: string;
}

export interface EvaluationReport {
  timestamp: string;
  total_items: number;
  duration_ms: number;
  accuracy: number;
  macro_metrics: MetricSummary;
  binary_metrics: MetricSummary;
  per_class: Record<string, { precision: number; recall: number; f1_score: number; support: number }>;
  confusion_matrix: ConfusionMatrix;
  results: EvaluationItemResult[];
  citation_summary?: CitationAlignmentSummary | null;
  baseline_comparison?: BaselineComparisonSummary | null;
  provenance: BenchmarkProvenance;
}

export interface DocumentMeta {
  filename: string;
  title: string;
  publisher?: string | null;
  source_path: string;
  file_exists: boolean;
  file_size_bytes?: number | null;
  last_modified?: string | null;
  total_pages?: number | null;
}

export interface IndexMeta {
  index_type?: string | null;
  metric?: string | null;
  dimension?: number | null;
  total_vectors: number;
  is_trained: boolean;
  index_file_exists: boolean;
  index_file_size_bytes?: number | null;
  embeddings_file_exists: boolean;
  embeddings_file_size_bytes?: number | null;
  embeddings_shape?: number[] | null;
}

export interface ChunkingConfig {
  chunk_size: number;
  chunk_overlap: number;
  splitter_type: string;
  embedding_model: string;
}

export interface CorpusStats {
  total_chunks: number;
  avg_chunk_length?: number | null;
  min_chunk_length?: number | null;
  max_chunk_length?: number | null;
  clinical_chunks_count: number;
  reference_chunks_count: number;
  pages_with_chunks: number;
  missing_page_metadata_chunks: number;
}

export interface KnowledgeBaseOverview {
  document: DocumentMeta;
  index: IndexMeta;
  chunking: ChunkingConfig;
  corpus_statistics: CorpusStats;
  is_ready: boolean;
  timestamp: string;
}

export interface ChunkItem {
  chunk_id: string;
  page?: number | null;
  page_available: boolean;
  char_length: number;
  is_reference: boolean;
  text: string;
  preview: string;
}

export interface ChunkListResponse {
  total_matching: number;
  offset: number;
  limit: number;
  chunks: ChunkItem[];
}
