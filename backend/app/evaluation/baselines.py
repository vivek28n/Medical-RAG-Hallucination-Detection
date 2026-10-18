"""
Baseline comparison engine for Medical RAG Hallucination Detection.

Compares:
1. Retrieval-Only Baseline (Semantic similarity thresholding without NLI)
2. Full Pipeline (Production RAG: FAISS Retrieval + DeBERTa-v3 Cross-Encoder)

Ensures zero label leakage by evaluating baselines strictly with frozen a-priori thresholds.
"""

from typing import List, Dict, Any, Optional
import numpy as np

from app.evaluation.benchmark_data import BENCHMARK_ITEMS
from app.evaluation.metrics import (
    calculate_binary_metrics,
    calculate_multiclass_metrics,
    calculate_confusion_matrix,
)


def evaluate_retrieval_only_baseline(
    retrieval_service,
    items: Optional[List[Dict[str, Any]]] = None,
    similarity_threshold: float = 0.65,
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Evaluate a retrieval-only baseline.
    Uses purely cosine similarity between claim and top retrieved chunks.
    Prediction rule:
      - If max cosine similarity >= similarity_threshold -> SUPPORTED
      - Else -> UNSUPPORTED
    Note: A pure semantic similarity retriever cannot detect contradictions.
    """
    if items is None:
        items = BENCHMARK_ITEMS

    predictions = []
    y_true = []
    y_pred = []

    for item in items:
        claim_text = item["claim"]
        ground_truth = item["ground_truth"]

        candidates = retrieval_service.search(claim_text, top_k=top_n)
        if not candidates:
            pred = "UNSUPPORTED"
            max_sim = 0.0
        else:
            # Encode claim and candidate texts to calculate true cosine similarity
            claim_emb = retrieval_service.embedding_model.encode([claim_text], normalize_embeddings=True)[0]
            cand_embs = retrieval_service.embedding_model.encode([c["text"] for c in candidates], normalize_embeddings=True)
            similarities = np.atleast_1d(np.dot(cand_embs, claim_emb))
            max_sim = float(np.max(similarities)) if similarities.size > 0 else 0.0

            if max_sim >= similarity_threshold:
                pred = "SUPPORTED"
            else:
                pred = "UNSUPPORTED"

        y_true.append(ground_truth)
        y_pred.append(pred)

        predictions.append({
            "id": item["id"],
            "claim": claim_text,
            "ground_truth": ground_truth,
            "predicted": pred,
            "is_correct": (pred == ground_truth),
            "max_similarity": round(max_sim, 4),
        })

    labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]
    multi_metrics = calculate_multiclass_metrics(y_true, y_pred, labels=labels)
    bin_metrics = calculate_binary_metrics(y_true, y_pred, pos_label="SUPPORTED")
    conf_matrix = calculate_confusion_matrix(y_true, y_pred, labels=labels)

    return {
        "baseline_name": "Retrieval-Only (Cosine Similarity)",
        "decision_rule": f"SUPPORTED if max_similarity >= {similarity_threshold}, else UNSUPPORTED",
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
        "confusion_matrix": conf_matrix,
        "per_class": multi_metrics["per_class"],
        "predictions": predictions,
    }


def compare_baselines(
    full_report: Dict[str, Any],
    retrieval_baseline: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Construct a comparative summary comparing Retrieval-Only against Full Production Pipeline.
    """
    comparison_table = [
        {
            "system": "Retrieval-Only (Cosine Similarity)",
            "accuracy": retrieval_baseline["accuracy"],
            "macro_precision": retrieval_baseline["macro_metrics"]["precision"],
            "macro_recall": retrieval_baseline["macro_metrics"]["recall"],
            "macro_f1": retrieval_baseline["macro_metrics"]["f1_score"],
            "supported_f1": retrieval_baseline["binary_metrics"]["f1_score"],
            "contradiction_capable": False,
            "notes": "Semantic thresholding alone cannot detect contradictions or inverted numerical claims.",
        },
        {
            "system": "Full Pipeline (FAISS + DeBERTa NLI)",
            "accuracy": full_report["accuracy"],
            "macro_precision": full_report["macro_metrics"]["precision"],
            "macro_recall": full_report["macro_metrics"]["recall"],
            "macro_f1": full_report["macro_metrics"]["f1_score"],
            "supported_f1": full_report["binary_metrics"]["f1_score"],
            "contradiction_capable": True,
            "notes": "Production cross-encoder verifies directional clinical entailment and refutation.",
        },
    ]

    return {
        "comparison_table": comparison_table,
        "retrieval_baseline": retrieval_baseline,
        "accuracy_gain": round(full_report["accuracy"] - retrieval_baseline["accuracy"], 4),
        "f1_gain": round(full_report["macro_metrics"]["f1_score"] - retrieval_baseline["macro_metrics"]["f1_score"], 4),
    }
