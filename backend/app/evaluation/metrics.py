"""
Evaluation metrics calculation engine.

Computes:
  - Accuracy
  - Precision, Recall, F1 Score (binary & macro multi-class)
  - Specificity
  - Multi-class and Binary Confusion Matrices

Designed with strict zero-division safeguards and empty-input handling.
"""

from typing import List, Dict, Any, Optional


def calculate_binary_metrics(
    y_true: List[str],
    y_pred: List[str],
    pos_label: str = "SUPPORTED"
) -> Dict[str, float]:
    """
    Compute binary classification metrics for a target positive class vs rest.

    Safeguards:
      - Returns 0.0 for all metrics if inputs are empty.
      - Returns 0.0 when denominators (TP+FP or TP+FN) are zero.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: len(y_true)={len(y_true)} != len(y_pred)={len(y_pred)}")

    total = len(y_true)
    if total == 0:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "specificity": 0.0,
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "tn": 0,
            "total": 0,
        }

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == pos_label and p == pos_label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != pos_label and p == pos_label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == pos_label and p != pos_label)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t != pos_label and p != pos_label)

    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "specificity": round(float(specificity), 4),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "total": int(total),
    }


def calculate_confusion_matrix(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate an N x N confusion matrix where matrix[i][j] represents
    the count of instances with true class labels[i] predicted as labels[j].
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: len(y_true)={len(y_true)} != len(y_pred)={len(y_pred)}")

    if labels is None:
        # Deduplicate while preserving order of first appearance
        seen = set()
        labels = []
        for item in y_true + y_pred:
            if item not in seen:
                seen.add(item)
                labels.append(item)
        if not labels:
            labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]

    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    n = len(labels)
    matrix = [[0 for _ in range(n)] for _ in range(n)]

    for t, p in zip(y_true, y_pred):
        if t in label_to_idx and p in label_to_idx:
            matrix[label_to_idx[t]][label_to_idx[p]] += 1

    return {
        "labels": labels,
        "matrix": matrix,
        "total": len(y_true),
    }


def calculate_multiclass_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute macro-averaged precision, recall, and F1 across multiple classes,
    plus overall accuracy and per-class metrics.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: len(y_true)={len(y_true)} != len(y_pred)={len(y_pred)}")

    total = len(y_true)
    if total == 0:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "per_class": {},
            "total": 0,
        }

    if labels is None:
        seen = set()
        labels = []
        for item in y_true + y_pred:
            if item not in seen:
                seen.add(item)
                labels.append(item)
        if not labels:
            labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / total

    per_class = {}
    precisions = []
    recalls = []
    f1s = []

    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

        per_class[label] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1_score": round(float(f), 4),
            "support": sum(1 for t in y_true if t == label),
        }

        precisions.append(p)
        recalls.append(r)
        f1s.append(f)

    macro_precision = sum(precisions) / len(precisions) if precisions else 0.0
    macro_recall = sum(recalls) / len(recalls) if recalls else 0.0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return {
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(macro_precision), 4),
        "recall": round(float(macro_recall), 4),
        "f1_score": round(float(macro_f1), 4),
        "per_class": per_class,
        "total": int(total),
    }
