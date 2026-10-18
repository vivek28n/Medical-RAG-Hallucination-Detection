"""
FastAPI application — Medical RAG + Hallucination Detection API.

Wires the complete Notebook 08 pipeline:
  User query → Retrieval → Generation → Verification →
  Confidence → Decision → Correction → Response
"""

import os
import sys
import time
import traceback
from datetime import datetime, timezone
from contextlib import asynccontextmanager

# Prevent Hugging Face tokenizers deadlock and tune PyTorch CPU threads
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import torch
torch.set_num_threads(min(4, os.cpu_count() or 1))

from typing import Optional
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend root is in sys.path
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from app.config import settings
from app.schemas import (
    AskRequest,
    AskResponse,
    SourceEvidence,
    ClaimEvidence,
    ClaimResult,
    ClaimVerificationResult,
    ConfidenceResult,
    HallucinationDecision,
    SelfCorrectionResult,
    StageTrace,
    PipelineTrace,
    EvaluationReportSchema,
    ExportReportResponseSchema,
    KnowledgeBaseOverviewSchema,
    ChunkListResponseSchema,
)
from app.services.retrieval import retrieval_service
from app.services.llm import llm_service
from app.services.verification import verification_service
from app.services.correction import correction_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all models at startup."""
    print("Starting up FastAPI. Loading models...")

    # Load embedding model + FAISS index
    retrieval_service.load_models_and_index()

    # Load NLI model
    verification_service.load_nli_model()

    # Initialize Gemini client
    llm_service.initialize()

    yield

    print("Shutting down...")


app = FastAPI(
    title="Medical RAG API",
    description="Medical RAG + Hallucination Detection Pipeline",
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────────
default_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:4173",
]
if settings.CORS_ORIGINS:
    extra_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    default_origins.extend(extra_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(default_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ─────────────────────────────────────────────────

@app.get("/health")
def health_check(response: Response):
    models_status = {
        "embedding": retrieval_service.embedding_model is not None,
        "faiss_index": retrieval_service.index is not None,
        "nli": verification_service._loaded,
        "gemini": llm_service.client is not None,
    }
    all_ready = all(models_status.values())
    if not all_ready:
        response.status_code = 503

    return {
        "status": "ok" if all_ready else "degraded",
        "ready": all_ready,
        "models_loaded": models_status,
    }


# ─── Pipeline Endpoint ───────────────────────────────────────────

@app.post("/api/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """
    Complete Notebook 08 pipeline:
    Query → Retrieve → Generate → Verify → Score → Decide → Correct → Respond
    """
    if not retrieval_service.index or not retrieval_service.embedding_model:
        raise HTTPException(
            status_code=503,
            detail="Vector database index is not ready. Please verify vector_db/index.faiss."
        )
    if not llm_service.client:
        raise HTTPException(
            status_code=503,
            detail="Gemini LLM client is not configured. Please verify GEMINI_API_KEY in backend/.env."
        )

    try:
        pipeline_start = time.perf_counter()
        stages = []
        query = request.query
        print(f"\n{'='*70}", flush=True)
        print(f"Query: {query}", flush=True)

        # ── 1. RETRIEVAL ─────────────────────────────────────────
        print("[1/7] Retrieving evidence...", flush=True)
        t_stage = time.perf_counter()
        raw_results = retrieval_service.search(
            query, top_k=settings.RETRIEVAL_TOP_K
        )
        t_retrieval = round((time.perf_counter() - t_stage) * 1000, 2)
        stages.append(StageTrace(
            stage_name="retrieval",
            duration_ms=t_retrieval,
            status="completed",
            details={
                "chunks_retrieved": len(raw_results),
                "top_k": settings.RETRIEVAL_TOP_K,
                "embedding_model": settings.EMBEDDING_MODEL_NAME,
            }
        ))

        # Build context string (NB08 build_context style)
        context = ""
        sources = []
        for i, res in enumerate(raw_results, 1):
            page_val = res.get("page")
            page_label = f"Page: {page_val}" if page_val is not None else "Page: N/A"
            context += (
                f"\n[Source: NIDDK Guiding Principles | "
                f"{page_label} | "
                f"Chunk: {res['chunk_id']}]\n"
                f"{res['text']}\n"
            )
            sources.append(SourceEvidence(
                chunk_id=res["chunk_id"],
                page=page_val,
                text=res["text"],
            ))

        print(f"  Retrieved {len(raw_results)} chunks", flush=True)

        # ── 2. GROUNDED GENERATION ───────────────────────────────
        print("[2/7] Generating grounded answer...", flush=True)
        t_stage = time.perf_counter()
        answer = llm_service.generate_grounded_answer(query, context)
        t_gen = round((time.perf_counter() - t_stage) * 1000, 2)
        stages.append(StageTrace(
            stage_name="grounded_generation",
            duration_ms=t_gen,
            status="completed",
            details={
                "model": settings.GEMINI_MODEL_NAME,
                "answer_characters": len(answer),
                "context_characters": len(context),
            }
        ))
        print(f"  Answer length: {len(answer)}", flush=True)

        # ── 3. CLAIM VERIFICATION ────────────────────────────────
        print("[3/7] Verifying claims...", flush=True)
        t_stage = time.perf_counter()
        claim_verification_raw = verification_service.verify_claims(
            answer=answer,
            chunks=retrieval_service.metadata,
            embeddings=retrieval_service.embeddings,
            index=retrieval_service.index,
            embedding_model=retrieval_service.embedding_model,
            top_n=settings.VERIFICATION_TOP_N,
            batch_size=settings.NLI_BATCH_SIZE,
        )
        t_ver = round((time.perf_counter() - t_stage) * 1000, 2)
        stages.append(StageTrace(
            stage_name="claim_verification",
            duration_ms=t_ver,
            status="completed",
            details={
                "total_claims": claim_verification_raw["total_claims"],
                "supported_claims": claim_verification_raw["supported_claims"],
                "consistency_score": round(claim_verification_raw["consistency_score"], 4),
                "nli_model": settings.NLI_MODEL_NAME,
                "batch_size": settings.NLI_BATCH_SIZE,
            }
        ))
        print(
            f"  Claims: {claim_verification_raw['supported_claims']}"
            f"/{claim_verification_raw['total_claims']} supported",
            flush=True
        )

        # ── 4. CONFIDENCE SCORING ────────────────────────────────
        print("[4/7] Calculating confidence...", flush=True)
        t_stage = time.perf_counter()
        confidence_raw = verification_service.calculate_confidence(
            answer=answer,
            question=query,
            retrieved_docs=raw_results,
            claim_verification=claim_verification_raw,
            embedding_model=retrieval_service.embedding_model,
        )
        t_conf = round((time.perf_counter() - t_stage) * 1000, 2)
        stages.append(StageTrace(
            stage_name="confidence_scoring",
            duration_ms=t_conf,
            status="completed",
            details={
                "confidence_score": round(confidence_raw["confidence_score"], 4),
                "confidence_level": confidence_raw["confidence_level"],
                "semantic_similarity": round(confidence_raw["semantic_similarity"], 4),
                "nli_entailment": round(confidence_raw["nli_entailment"], 4),
                "retrieval_quality": round(confidence_raw["retrieval_quality"], 4),
                "claim_consistency": round(confidence_raw["claim_consistency"], 4),
            }
        ))
        print(
            f"  Confidence: {confidence_raw['confidence_score']:.4f} "
            f"({confidence_raw['confidence_level']})",
            flush=True
        )

        # ── 5. HALLUCINATION DECISION ────────────────────────────
        print("[5/7] Determining hallucination status...", flush=True)
        t_stage = time.perf_counter()
        decision_raw = verification_service.determine_decision(
            claim_verification=claim_verification_raw,
            confidence_result=confidence_raw,
        )
        t_dec = round((time.perf_counter() - t_stage) * 1000, 2)
        stages.append(StageTrace(
            stage_name="hallucination_decision",
            duration_ms=t_dec,
            status="completed",
            details={
                "decision": decision_raw["decision"],
                "strong_contradictions": decision_raw["strong_contradictions"],
            }
        ))
        print(f"  Decision: {decision_raw['decision']}", flush=True)

        # ── 6. SELF-CORRECTION ───────────────────────────────────
        print("[6/7] Self-correction check...", flush=True)
        t_stage = time.perf_counter()
        correction_raw = correction_service.perform_correction(
            question=query,
            answer=answer,
            final_decision=decision_raw,
            claim_verification=claim_verification_raw,
            llm_service=llm_service,
        )
        t_corr = round((time.perf_counter() - t_stage) * 1000, 2)

        correction_needed = correction_raw["correction_needed"]
        correction_applied = correction_raw["correction_applied"]

        corr_status = "completed" if correction_applied else ("failed" if correction_needed else "skipped")
        corr_reason = (
            "Evidence-grounded correction generated"
            if correction_applied
            else ("LLM unavailable for revision" if correction_needed else "Answer deemed reliable (no correction required)")
        )

        stages.append(StageTrace(
            stage_name="self_correction",
            duration_ms=t_corr,
            status=corr_status,
            details={
                "correction_needed": correction_needed,
                "correction_applied": correction_applied,
                "reason": corr_reason,
            }
        ))
        print(
            f"  Needed: {correction_raw['correction_needed']} | "
            f"Applied: {correction_raw['correction_applied']}",
            flush=True
        )

        final_answer = answer
        final_claim_verification = claim_verification_raw
        final_confidence = confidence_raw
        final_decision = decision_raw

        # ── 6.5 RE-VERIFICATION ──────────────────────────────────
        if correction_applied and correction_raw.get("corrected_answer"):
            print("[6.5/7] Re-verifying corrected answer...", flush=True)
            t_stage = time.perf_counter()
            final_answer = correction_raw["corrected_answer"]

            final_claim_verification = verification_service.verify_claims(
                answer=final_answer,
                chunks=retrieval_service.metadata,
                embeddings=retrieval_service.embeddings,
                index=retrieval_service.index,
                embedding_model=retrieval_service.embedding_model,
                top_n=settings.VERIFICATION_TOP_N,
                batch_size=settings.NLI_BATCH_SIZE,
            )

            final_confidence = verification_service.calculate_confidence(
                answer=final_answer,
                question=query,
                retrieved_docs=raw_results,
                claim_verification=final_claim_verification,
                embedding_model=retrieval_service.embedding_model,
            )

            final_decision = verification_service.determine_decision(
                claim_verification=final_claim_verification,
                confidence_result=final_confidence,
            )
            t_rever = round((time.perf_counter() - t_stage) * 1000, 2)
            stages.append(StageTrace(
                stage_name="re_verification",
                duration_ms=t_rever,
                status="completed",
                details={
                    "post_correction_supported": final_claim_verification["supported_claims"],
                    "post_correction_confidence": round(final_confidence["confidence_score"], 4),
                    "post_correction_decision": final_decision["decision"],
                }
            ))
        else:
            stages.append(StageTrace(
                stage_name="re_verification",
                duration_ms=0.0,
                status="skipped",
                details={"reason": "No self-correction applied"}
            ))

        # ── 7. BUILD RESPONSE ────────────────────────────────────
        print("[7/7] Building response...", flush=True)

        # Convert claim verification to schema objects
        claim_results = []
        for cr in final_claim_verification["claims"]:
            ev = cr["evidence"]
            claim_evidence = None
            if ev:
                claim_evidence = ClaimEvidence(
                    chunk_id=ev["chunk_id"],
                    page=ev.get("page"),
                    text=ev["text"],
                    similarity=ev["similarity"],
                    entailment=ev["entailment"],
                    contradiction=ev["contradiction"],
                    neutral=ev["neutral"],
                    evidence_score=ev["evidence_score"],
                )
            claim_results.append(ClaimResult(
                claim_number=cr["claim_number"],
                claim=cr["claim"],
                hypothesis=cr["hypothesis"],
                supported=cr["supported"],
                evidence=claim_evidence,
            ))

        total_duration_ms = round((time.perf_counter() - pipeline_start) * 1000, 2)
        pipeline_trace = PipelineTrace(
            total_duration_ms=total_duration_ms,
            stages=stages,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        response = AskResponse(
            answer=final_answer,
            sources=sources,
            claim_verification=ClaimVerificationResult(
                claims=claim_results,
                supported_claims=final_claim_verification["supported_claims"],
                total_claims=final_claim_verification["total_claims"],
                consistency_score=final_claim_verification["consistency_score"],
            ),
            confidence=ConfidenceResult(**final_confidence),
            hallucination_decision=HallucinationDecision(**final_decision),
            self_correction=SelfCorrectionResult(
                correction_needed=correction_raw["correction_needed"],
                correction_applied=correction_raw["correction_applied"],
                original_answer=correction_raw["original_answer"],
                corrected_answer=correction_raw.get("corrected_answer"),
            ),
            pipeline_trace=pipeline_trace,
        )

        print(f"{'='*70}", flush=True)
        print(f"PIPELINE COMPLETE in {total_duration_ms}ms", flush=True)
        print(f"{'='*70}\n", flush=True)

        return response

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        err_str = str(e)
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY in err_str:
            err_str = err_str.replace(settings.GEMINI_API_KEY, "[REDACTED]")
        raise HTTPException(status_code=500, detail=f"Inference error: {err_str}")


# ─── Evaluation Lab Endpoints ────────────────────────────────────

@app.get("/api/evaluation/benchmark")
def get_evaluation_benchmark():
    """
    Return benchmark metadata, provenance, and labelled test probes.
    """
    from app.evaluation.benchmark_data import BENCHMARK_ITEMS, BENCHMARK_PROVENANCE
    return {
        "provenance": BENCHMARK_PROVENANCE,
        "items": BENCHMARK_ITEMS,
        "total_items": len(BENCHMARK_ITEMS),
    }


@app.post("/api/evaluation/run", response_model=EvaluationReportSchema)
def run_evaluation(use_legacy_hypothesis: bool = False):
    """
    Execute benchmark evaluation suite against FAISS index and DeBERTa NLI verifier.
    Computes precision, recall, F1, confusion matrix, and baseline comparisons.
    """
    if not retrieval_service.index or not retrieval_service.embedding_model:
        raise HTTPException(
            status_code=503,
            detail="Vector database index is not ready."
        )
    if not verification_service.nli_model:
        raise HTTPException(
            status_code=503,
            detail="DeBERTa NLI model is not loaded."
        )

    try:
        from app.evaluation.runner import run_benchmark_evaluation
        from app.evaluation.baselines import evaluate_retrieval_only_baseline, compare_baselines
        report = run_benchmark_evaluation(
            retrieval_service,
            verification_service,
            use_legacy_hypothesis=use_legacy_hypothesis
        )
        retrieval_base = evaluate_retrieval_only_baseline(retrieval_service)
        comp = compare_baselines(report, retrieval_base)
        report["baseline_comparison"] = comp
        return report
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation execution failed: {str(e)}")


@app.post("/api/evaluation/export/markdown", response_model=ExportReportResponseSchema)
def export_evaluation_markdown(use_legacy_hypothesis: bool = False):
    """
    Generate and return a structured GitHub-flavored Markdown evaluation report.
    """
    if not retrieval_service.index or not retrieval_service.embedding_model or not verification_service.nli_model:
        raise HTTPException(status_code=503, detail="Retrieval index or NLI model is not ready.")
    try:
        from app.evaluation.runner import run_benchmark_evaluation
        from app.evaluation.baselines import evaluate_retrieval_only_baseline, compare_baselines
        from app.evaluation.export import export_report_to_markdown

        report = run_benchmark_evaluation(
            retrieval_service,
            verification_service,
            use_legacy_hypothesis=use_legacy_hypothesis
        )
        retrieval_base = evaluate_retrieval_only_baseline(retrieval_service)
        comp = compare_baselines(report, retrieval_base)
        report["baseline_comparison"] = comp

        content = export_report_to_markdown(report, baseline_comparison=comp)
        ts_slug = report["timestamp"].replace(":", "-").replace(".", "-")
        return {
            "content": content,
            "filename": f"medguide_evaluation_report_{ts_slug}.md",
            "format": "markdown",
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Markdown export failed: {str(e)}")


@app.post("/api/evaluation/export/json", response_model=ExportReportResponseSchema)
def export_evaluation_json(use_legacy_hypothesis: bool = False):
    """
    Generate and return a structured serialized JSON evaluation report.
    """
    if not retrieval_service.index or not retrieval_service.embedding_model or not verification_service.nli_model:
        raise HTTPException(status_code=503, detail="Retrieval index or NLI model is not ready.")
    try:
        from app.evaluation.runner import run_benchmark_evaluation
        from app.evaluation.baselines import evaluate_retrieval_only_baseline, compare_baselines
        from app.evaluation.export import export_report_to_json

        report = run_benchmark_evaluation(
            retrieval_service,
            verification_service,
            use_legacy_hypothesis=use_legacy_hypothesis
        )
        retrieval_base = evaluate_retrieval_only_baseline(retrieval_service)
        comp = compare_baselines(report, retrieval_base)
        report["baseline_comparison"] = comp

        content = export_report_to_json(report, baseline_comparison=comp)
        ts_slug = report["timestamp"].replace(":", "-").replace(".", "-")
        return {
            "content": content,
            "filename": f"medguide_evaluation_report_{ts_slug}.json",
            "format": "json",
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"JSON export failed: {str(e)}")


# ─── Knowledge Base Explorer Endpoints ───────────────────────────

@app.get("/api/knowledge-base/overview", response_model=KnowledgeBaseOverviewSchema)
def get_knowledge_base_overview_endpoint():
    """
    Return genuine corpus, index, model, and document metadata
    derived from loaded retrieval structures and files on disk.
    """
    try:
        from app.knowledge_base.service import get_knowledge_base_overview
        return get_knowledge_base_overview(retrieval_service)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate knowledge base overview: {str(e)}"
        )


@app.get("/api/knowledge-base/chunks", response_model=ChunkListResponseSchema)
def get_knowledge_base_chunks_endpoint(
    page: Optional[int] = Query(None, description="Filter by page number"),
    search: Optional[str] = Query(None, description="Substring search term"),
    chunk_type: Optional[str] = Query("all", description="Chunk type filter: all, clinical, reference"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(15, ge=1, le=100, description="Items per page"),
):
    """
    Search and paginate indexed document chunks with previews and metadata.
    Distinguishes unavailable page metadata from page numbers.
    """
    try:
        from app.knowledge_base.service import get_knowledge_base_chunks
        return get_knowledge_base_chunks(
            retrieval_service,
            page=page,
            search=search,
            chunk_type=chunk_type,
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve knowledge base chunks: {str(e)}"
        )
