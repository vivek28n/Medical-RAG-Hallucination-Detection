"""
Benchmark evaluation runner.

Executes benchmark items against the FAISS vector index and DeBERTa NLI verifier,
computes classification metrics, and generates a structured EvaluationReport.
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import numpy as np

from app.evaluation.benchmark_data import BENCHMARK_ITEMS, BENCHMARK_PROVENANCE
from app.evaluation.metrics import (
    calculate_binary_metrics,
    calculate_confusion_matrix,
    calculate_multiclass_metrics,
)
from app.services.retrieval import is_reference_chunk


def evaluate_single_item(
    item: Dict[str, Any],
    retrieval_service,
    verification_service,
    top_n: int = 5,
    use_legacy_hypothesis: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate a single benchmark item using real vector retrieval and DeBERTa NLI.
    Aligns directly with production claim verification:
      - Uses generic claim_to_hypothesis() by default (legacy hypotheses optional).
      - Searches using hypothesis embeddings and filters out reference chunks.
      - Uses shared VerificationService.classify_claim_status() 3-way decision rule.
      - Computes citation page alignment against verified PDF chunk metadata.
    """
    claim_text = item["claim"]
    ground_truth = item["ground_truth"]

    # Production-aligned hypothesis construction
    if use_legacy_hypothesis:
        hypothesis = item.get("legacy_hypothesis") or verification_service.claim_to_hypothesis(claim_text)
    else:
        hypothesis = verification_service.claim_to_hypothesis(claim_text)

    citation_page = item.get("citation_page")

    # 1. Retrieve evidence candidates using hypothesis query (matching production)
    raw_candidates = retrieval_service.search(hypothesis, top_k=top_n * 3)
    if not raw_candidates:
        citation_alignment = "NOT_APPLICABLE" if citation_page is None else "MISMATCHED"
        return {
            "id": item["id"],
            "claim": claim_text,
            "hypothesis": hypothesis,
            "legacy_hypothesis": item.get("legacy_hypothesis"),
            "ground_truth": ground_truth,
            "predicted": "UNSUPPORTED",
            "is_correct": ground_truth == "UNSUPPORTED",
            "entailment": 0.0,
            "contradiction": 0.0,
            "similarity": 0.0,
            "evidence_score": 0.0,
            "citation_page": citation_page,
            "booklet_page": item.get("booklet_page"),
            "verification_status": item.get("verification_status", "VERIFIED"),
            "citation_alignment": citation_alignment,
            "matched_chunk_id": None,
            "matched_page": None,
            "matched_text": None,
        }

    # Filter out bibliography references (same as production verify_claims)
    clinical_candidates = [
        c for c in raw_candidates if not is_reference_chunk(c.get("text", ""))
    ]
    candidates = (clinical_candidates if clinical_candidates else raw_candidates)[:top_n]

    # 2. Score candidates with NLI
    premises = [c["text"] for c in candidates]
    hypotheses = [hypothesis] * len(premises)

    nli_scores = verification_service.nli_score_batch(premises, hypotheses, batch_size=8)

    # 3. Compute cosine similarities
    raw_hyp_emb = retrieval_service.embedding_model.encode([hypothesis], normalize_embeddings=True)
    hyp_emb = np.array(raw_hyp_emb).reshape(-1)
    raw_cand_embs = retrieval_service.embedding_model.encode(premises, normalize_embeddings=True)
    cand_embs = np.array(raw_cand_embs)
    if cand_embs.ndim == 1:
        cand_embs = cand_embs.reshape(1, -1)
    similarities = np.dot(cand_embs, hyp_emb).flatten()

    # 4. Select strongest candidate
    best_candidate = None
    best_score = -999.0

    for idx, (cand, nli, sim) in enumerate(zip(candidates, nli_scores, similarities)):
        evidence_score = (0.70 * nli["entailment"]) + (0.30 * float(sim)) - (0.30 * nli["contradiction"])
        if evidence_score > best_score:
            best_score = evidence_score
            best_candidate = {
                "chunk": cand,
                "entailment": float(nli["entailment"]),
                "contradiction": float(nli["contradiction"]),
                "neutral": float(nli["neutral"]),
                "similarity": float(sim),
                "evidence_score": float(evidence_score),
            }

    # 5. Classify prediction using shared production classification rule
    predicted = verification_service.classify_claim_status(best_candidate)
    is_correct = (predicted == ground_truth)

    ent = best_candidate["entailment"]
    contra = best_candidate["contradiction"]
    sim = best_candidate["similarity"]
    score = best_candidate["evidence_score"]
    matched_page = best_candidate["chunk"].get("page")

    # 6. Audit citation alignment against verified source PDF page
    if citation_page is None:
        citation_alignment = "NOT_APPLICABLE"
    elif matched_page is None:
        citation_alignment = "MISMATCHED"
    elif matched_page == citation_page:
        citation_alignment = "MATCHED"
    elif abs(matched_page - citation_page) <= 1:
        citation_alignment = "ADJACENT_PAGE"
    else:
        citation_alignment = "MISMATCHED"

    return {
        "id": item["id"],
        "claim": claim_text,
        "hypothesis": hypothesis,
        "legacy_hypothesis": item.get("legacy_hypothesis"),
        "ground_truth": ground_truth,
        "predicted": predicted,
        "is_correct": is_correct,
        "entailment": round(ent, 4),
        "contradiction": round(contra, 4),
        "similarity": round(sim, 4),
        "evidence_score": round(score, 4),
        "citation_page": citation_page,
        "booklet_page": item.get("booklet_page"),
        "verification_status": item.get("verification_status", "VERIFIED"),
        "citation_alignment": citation_alignment,
        "matched_chunk_id": best_candidate["chunk"].get("chunk_id"),
        "matched_page": matched_page,
        "matched_text": best_candidate["chunk"].get("text", "")[:200],
    }


def run_benchmark_evaluation(
    retrieval_service,
    verification_service,
    items: Optional[List[Dict[str, Any]]] = None,
    use_legacy_hypothesis: bool = False,
) -> Dict[str, Any]:
    """
    Execute full evaluation suite against benchmark items.
    Returns complete EvaluationReport dictionary with multi-class metrics,
    binary metrics, confusion matrix, citation summary, and provenance.
    """
    if items is None:
        items = BENCHMARK_ITEMS

    start_time = time.perf_counter()
    results = []

    for item in items:
        res = evaluate_single_item(
            item,
            retrieval_service,
            verification_service,
            use_legacy_hypothesis=use_legacy_hypothesis
        )
        results.append(res)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    y_true = [r["ground_truth"] for r in results]
    y_pred = [r["predicted"] for r in results]

    labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]
    conf_matrix = calculate_confusion_matrix(y_true, y_pred, labels=labels)
    multi_metrics = calculate_multiclass_metrics(y_true, y_pred, labels=labels)
    bin_metrics = calculate_binary_metrics(y_true, y_pred, pos_label="SUPPORTED")

    # Citation alignment summary
    cited_results = [r for r in results if r.get("citation_page") is not None]
    total_cited = len(cited_results)
    matched_cnt = sum(1 for r in cited_results if r.get("citation_alignment") == "MATCHED")
    adj_cnt = sum(1 for r in cited_results if r.get("citation_alignment") == "ADJACENT_PAGE")
    mismatched_cnt = sum(1 for r in cited_results if r.get("citation_alignment") == "MISMATCHED")
    alignment_rate = round((matched_cnt + adj_cnt) / total_cited, 4) if total_cited > 0 else 0.0

    citation_summary = {
        "total_cited_items": total_cited,
        "matched": matched_cnt,
        "adjacent": adj_cnt,
        "mismatched": mismatched_cnt,
        "alignment_rate": alignment_rate,
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_items": len(items),
        "duration_ms": duration_ms,
        "accuracy": multi_metrics["accuracy"],
        "macro_metrics": {
            "precision": multi_metrics["precision"],
            "recall": multi_metrics["recall"],
            "f1_score": multi_metrics["f1_score"],
        },
        "binary_metrics": {
            "precision": bin_metrics["precision"],
            "recall": bin_metrics["recall"],
            "f1_score": bin_metrics["f1_score"],
            "specificity": bin_metrics["specificity"],
        },
        "per_class": multi_metrics["per_class"],
        "confusion_matrix": conf_matrix,
        "results": results,
        "citation_summary": citation_summary,
        "provenance": BENCHMARK_PROVENANCE,
    }
