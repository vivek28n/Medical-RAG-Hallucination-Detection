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


def evaluate_single_item(
    item: Dict[str, Any],
    retrieval_service,
    verification_service,
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Evaluate a single benchmark item using real vector retrieval and DeBERTa NLI.
    Does NOT call the generative LLM, preserving quotas and isolating verification.
    """
    claim_text = item["claim"]
    hypothesis = item.get("hypothesis") or claim_text
    ground_truth = item["ground_truth"]

    # 1. Retrieve evidence candidates
    candidates = retrieval_service.search(claim_text, top_k=top_n)
    if not candidates:
        return {
            "id": item["id"],
            "claim": claim_text,
            "hypothesis": hypothesis,
            "ground_truth": ground_truth,
            "predicted": "UNSUPPORTED",
            "is_correct": ground_truth == "UNSUPPORTED",
            "entailment": 0.0,
            "contradiction": 0.0,
            "similarity": 0.0,
            "evidence_score": 0.0,
            "citation_page": item.get("citation_page"),
            "matched_chunk_id": None,
            "matched_text": None,
        }

    # 2. Score candidates with NLI
    premises = [c["text"] for c in candidates]
    hypotheses = [hypothesis] * len(premises)

    # Batched NLI call
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

    # 5. Classify prediction
    ent = best_candidate["entailment"]
    contra = best_candidate["contradiction"]
    sim = best_candidate["similarity"]
    score = best_candidate["evidence_score"]

    # High contradiction threshold
    if contra >= 0.40 or (contra > ent and contra >= 0.25):
        predicted = "CONTRADICTED"
    elif verification_service.is_claim_supported({
        "entailment": ent,
        "contradiction": contra,
        "similarity": sim,
        "evidence_score": score,
    }):
        predicted = "SUPPORTED"
    else:
        predicted = "UNSUPPORTED"

    is_correct = (predicted == ground_truth)

    return {
        "id": item["id"],
        "claim": claim_text,
        "hypothesis": hypothesis,
        "ground_truth": ground_truth,
        "predicted": predicted,
        "is_correct": is_correct,
        "entailment": round(ent, 4),
        "contradiction": round(contra, 4),
        "similarity": round(sim, 4),
        "evidence_score": round(score, 4),
        "citation_page": item.get("citation_page"),
        "matched_chunk_id": best_candidate["chunk"].get("chunk_id"),
        "matched_text": best_candidate["chunk"].get("text", "")[:200],
    }


def run_benchmark_evaluation(
    retrieval_service,
    verification_service,
    items: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Execute full evaluation suite against the benchmark items.
    Returns complete EvaluationReport dictionary.
    """
    if items is None:
        items = BENCHMARK_ITEMS

    start_time = time.perf_counter()
    results = []

    for item in items:
        res = evaluate_single_item(item, retrieval_service, verification_service)
        results.append(res)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    y_true = [r["ground_truth"] for r in results]
    y_pred = [r["predicted"] for r in results]

    labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]
    conf_matrix = calculate_confusion_matrix(y_true, y_pred, labels=labels)
    multi_metrics = calculate_multiclass_metrics(y_true, y_pred, labels=labels)
    bin_metrics = calculate_binary_metrics(y_true, y_pred, pos_label="SUPPORTED")

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
        "provenance": BENCHMARK_PROVENANCE,
    }
