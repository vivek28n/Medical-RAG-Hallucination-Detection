"""
Unit tests for Evaluation Lab metrics, edge cases, benchmarks, and runner.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.evaluation.metrics import (
    calculate_binary_metrics,
    calculate_confusion_matrix,
    calculate_multiclass_metrics,
)
from app.evaluation.benchmark_data import BENCHMARK_ITEMS, BENCHMARK_PROVENANCE
from app.evaluation.runner import run_benchmark_evaluation, evaluate_single_item


class TestEvaluationMetrics(unittest.TestCase):
    def test_01_binary_metrics_perfect_classification(self):
        """Test binary metrics with 100% agreement."""
        y_true = ["SUPPORTED", "SUPPORTED", "UNSUPPORTED", "UNSUPPORTED"]
        y_pred = ["SUPPORTED", "SUPPORTED", "UNSUPPORTED", "UNSUPPORTED"]

        metrics = calculate_binary_metrics(y_true, y_pred, pos_label="SUPPORTED")
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["f1_score"], 1.0)
        self.assertEqual(metrics["specificity"], 1.0)
        self.assertEqual(metrics["tp"], 2)
        self.assertEqual(metrics["tn"], 2)
        self.assertEqual(metrics["fp"], 0)
        self.assertEqual(metrics["fn"], 0)

    def test_02_division_by_zero_safeguard(self):
        """Test zero-division safeguards when no positive instances exist."""
        y_true = ["UNSUPPORTED", "UNSUPPORTED"]
        y_pred = ["UNSUPPORTED", "UNSUPPORTED"]

        metrics = calculate_binary_metrics(y_true, y_pred, pos_label="SUPPORTED")
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["precision"], 0.0)  # TP+FP=0, should be safely 0.0
        self.assertEqual(metrics["recall"], 0.0)     # TP+FN=0, should be safely 0.0
        self.assertEqual(metrics["f1_score"], 0.0)
        self.assertEqual(metrics["specificity"], 1.0) # TN/(TN+FP) = 2/2 = 1.0

    def test_03_empty_inputs_handling(self):
        """Test metrics calculation gracefully handles empty inputs."""
        bin_metrics = calculate_binary_metrics([], [])
        self.assertEqual(bin_metrics["total"], 0)
        self.assertEqual(bin_metrics["accuracy"], 0.0)
        self.assertEqual(bin_metrics["f1_score"], 0.0)

        multi_metrics = calculate_multiclass_metrics([], [])
        self.assertEqual(multi_metrics["total"], 0)
        self.assertEqual(multi_metrics["accuracy"], 0.0)

        cm = calculate_confusion_matrix([], [])
        self.assertEqual(cm["total"], 0)

    def test_04_mismatched_length_exception(self):
        """Test ValueError is raised when true and predicted list lengths differ."""
        with self.assertRaises(ValueError):
            calculate_binary_metrics(["SUPPORTED", "UNSUPPORTED"], ["SUPPORTED"])

        with self.assertRaises(ValueError):
            calculate_confusion_matrix(["A"], ["A", "B"])

        with self.assertRaises(ValueError):
            calculate_multiclass_metrics(["A"], [])

    def test_05_confusion_matrix_structure_and_counts(self):
        """Test confusion matrix cell mapping and count conservation."""
        labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]
        y_true = ["SUPPORTED", "SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]
        y_pred = ["SUPPORTED", "UNSUPPORTED", "CONTRADICTED", "UNSUPPORTED"]

        cm = calculate_confusion_matrix(y_true, y_pred, labels=labels)
        self.assertEqual(cm["labels"], labels)
        self.assertEqual(cm["total"], 4)

        matrix = cm["matrix"]
        self.assertEqual(len(matrix), 3)
        self.assertEqual(len(matrix[0]), 3)

        # True SUPPORTED (idx 0): 1 predicted SUPPORTED, 1 predicted UNSUPPORTED
        self.assertEqual(matrix[0][0], 1)
        self.assertEqual(matrix[0][1], 0)
        self.assertEqual(matrix[0][2], 1)

        # True CONTRADICTED (idx 1): 1 predicted CONTRADICTED
        self.assertEqual(matrix[1][1], 1)

        # True UNSUPPORTED (idx 2): 1 predicted UNSUPPORTED
        self.assertEqual(matrix[2][2], 1)

        total_sum = sum(sum(row) for row in matrix)
        self.assertEqual(total_sum, 4)

    def test_06_multiclass_metrics(self):
        """Test multiclass accuracy, macro-averaged metrics, and per-class calculations."""
        labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]
        y_true = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"]
        y_pred = ["SUPPORTED", "CONTRADICTED", "SUPPORTED"]

        res = calculate_multiclass_metrics(y_true, y_pred, labels=labels)
        self.assertEqual(res["total"], 3)
        self.assertAlmostEqual(res["accuracy"], 2 / 3, places=3)
        self.assertIn("SUPPORTED", res["per_class"])
        self.assertIn("CONTRADICTED", res["per_class"])
        self.assertIn("UNSUPPORTED", res["per_class"])

    def test_07_benchmark_dataset_provenance_and_schema(self):
        """Test benchmark dataset integrity, genuine labels, and provenance metadata."""
        self.assertGreaterEqual(len(BENCHMARK_ITEMS), 15, "Benchmark must contain at least 15 items")
        self.assertIn("source_document", BENCHMARK_PROVENANCE)
        self.assertIn("label_definitions", BENCHMARK_PROVENANCE)
        self.assertIn("limitations", BENCHMARK_PROVENANCE)

        valid_labels = {"SUPPORTED", "CONTRADICTED", "UNSUPPORTED"}
        for item in BENCHMARK_ITEMS:
            self.assertIn("id", item)
            self.assertIn("claim", item)
            self.assertIn("ground_truth", item)
            self.assertIn(item["ground_truth"], valid_labels)
            self.assertTrue(len(item["claim"]) > 10)
            self.assertIn("rationale", item)

    def test_08_evaluation_runner_execution_mocked(self):
        """Test full benchmark evaluation runner with mocked retrieval and NLI services."""
        mock_retrieval = MagicMock()
        mock_retrieval.search.return_value = [
            {"chunk_id": "c1", "text": "Sample clinical passage for testing.", "page": 10}
        ]
        mock_retrieval.embedding_model.encode.return_value = np.zeros((1, 384))

        mock_verification = MagicMock()
        mock_verification.nli_score_batch.return_value = [
            {"entailment": 0.95, "contradiction": 0.01, "neutral": 0.04}
        ]
        mock_verification.is_claim_supported.return_value = True

        test_items = [
            {
                "id": "T-01",
                "claim": "Testing for diabetes in adults.",
                "hypothesis": "Diabetes testing in adults.",
                "ground_truth": "SUPPORTED",
            },
            {
                "id": "T-02",
                "claim": "Severe obesity should never be tested.",
                "hypothesis": "Obese individuals do not require testing.",
                "ground_truth": "CONTRADICTED",
            }
        ]

        report = run_benchmark_evaluation(mock_retrieval, mock_verification, items=test_items)
        self.assertIn("timestamp", report)
        self.assertEqual(report["total_items"], 2)
        self.assertIn("accuracy", report)
        self.assertIn("confusion_matrix", report)
        self.assertIn("macro_metrics", report)
        self.assertIn("binary_metrics", report)
        self.assertIn("provenance", report)
        self.assertEqual(len(report["results"]), 2)


if __name__ == "__main__":
    unittest.main()
