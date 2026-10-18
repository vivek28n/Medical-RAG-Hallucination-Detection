from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User query about medical topics")

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or contain only whitespace.")
        return stripped


class SourceEvidence(BaseModel):
    chunk_id: str
    page: Optional[int] = None
    text: str


class ClaimEvidence(BaseModel):
    chunk_id: str
    page: Optional[int] = None
    text: str
    similarity: float
    entailment: float
    contradiction: float
    neutral: float
    evidence_score: float


class ClaimResult(BaseModel):
    claim_number: int
    claim: str
    hypothesis: str
    supported: bool
    evidence: Optional[ClaimEvidence] = None


class ClaimVerificationResult(BaseModel):
    claims: List[ClaimResult]
    supported_claims: int
    total_claims: int
    consistency_score: float


class ConfidenceResult(BaseModel):
    semantic_similarity: float
    nli_entailment: float
    retrieval_quality: float
    claim_consistency: float
    confidence_score: float
    confidence_level: str  # HIGH / MEDIUM / LOW


class HallucinationDecision(BaseModel):
    decision: str  # SUPPORTED / CONTRADICTED / POTENTIAL HALLUCINATION
    claim_consistency: float
    confidence_score: float
    strong_contradictions: int


class SelfCorrectionResult(BaseModel):
    correction_needed: bool
    correction_applied: bool
    original_answer: str
    corrected_answer: Optional[str] = None


class StageTrace(BaseModel):
    stage_name: str
    duration_ms: float
    status: str  # "completed" | "skipped" | "failed"
    details: Optional[dict] = None


class PipelineTrace(BaseModel):
    total_duration_ms: float
    stages: List[StageTrace]
    timestamp: str


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceEvidence]
    claim_verification: Optional[ClaimVerificationResult] = None
    confidence: Optional[ConfidenceResult] = None
    hallucination_decision: Optional[HallucinationDecision] = None
    self_correction: Optional[SelfCorrectionResult] = None
    pipeline_trace: Optional[PipelineTrace] = None


# ─── Evaluation Lab Schemas ──────────────────────────────────────

class BenchmarkItemSchema(BaseModel):
    id: str
    claim: str
    hypothesis: Optional[str] = None
    ground_truth: str
    principle: Optional[str] = None
    citation_page: Optional[int] = None
    rationale: Optional[str] = None


class ConfusionMatrixSchema(BaseModel):
    labels: List[str]
    matrix: List[List[int]]
    total: int


class MetricSummarySchema(BaseModel):
    precision: float
    recall: float
    f1_score: float
    specificity: Optional[float] = None


class EvaluationItemResultSchema(BaseModel):
    id: str
    claim: str
    hypothesis: str
    ground_truth: str
    predicted: str
    is_correct: bool
    entailment: float
    contradiction: float
    similarity: float
    evidence_score: float
    citation_page: Optional[int] = None
    matched_chunk_id: Optional[str] = None
    matched_text: Optional[str] = None


class EvaluationReportSchema(BaseModel):
    timestamp: str
    total_items: int
    duration_ms: float
    accuracy: float
    macro_metrics: MetricSummarySchema
    binary_metrics: MetricSummarySchema
    per_class: Dict[str, Any]
    confusion_matrix: ConfusionMatrixSchema
    results: List[EvaluationItemResultSchema]
    provenance: Dict[str, Any]


# ─── Knowledge Base Explorer Schemas ─────────────────────────────

class DocumentMetaSchema(BaseModel):
    filename: str
    title: str
    publisher: Optional[str] = None
    source_path: str
    file_exists: bool
    file_size_bytes: Optional[int] = None
    last_modified: Optional[str] = None
    total_pages: Optional[int] = None


class IndexMetaSchema(BaseModel):
    index_type: Optional[str] = None
    metric: Optional[str] = None
    dimension: Optional[int] = None
    total_vectors: int
    is_trained: bool
    index_file_exists: bool
    index_file_size_bytes: Optional[int] = None
    embeddings_file_exists: bool
    embeddings_file_size_bytes: Optional[int] = None
    embeddings_shape: Optional[List[int]] = None


class ChunkingConfigSchema(BaseModel):
    chunk_size: int
    chunk_overlap: int
    splitter_type: str
    embedding_model: str


class CorpusStatsSchema(BaseModel):
    total_chunks: int
    avg_chunk_length: Optional[float] = None
    min_chunk_length: Optional[int] = None
    max_chunk_length: Optional[int] = None
    clinical_chunks_count: int
    reference_chunks_count: int
    pages_with_chunks: int
    missing_page_metadata_chunks: int


class KnowledgeBaseOverviewSchema(BaseModel):
    document: DocumentMetaSchema
    index: IndexMetaSchema
    chunking: ChunkingConfigSchema
    corpus_statistics: CorpusStatsSchema
    is_ready: bool
    timestamp: str


class ChunkItemSchema(BaseModel):
    chunk_id: str
    page: Optional[int] = None
    page_available: bool
    char_length: int
    is_reference: bool
    text: str
    preview: str


class ChunkListResponseSchema(BaseModel):
    total_matching: int
    offset: int
    limit: int
    chunks: List[ChunkItemSchema]
