"""
Unit tests for Phase 2 Evaluation Reliability Audit & Parity.
Tests cover:
1. Citation page alignment and audit metadata.
2. Production-evaluation parity via shared classify_claim_status.
3. Default generic claim_to_hypothesis generation in the evaluation runner.
4. Retrieval-only baseline comparison.
5. Markdown and JSON export generators.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.evaluation.benchmark_data import BENCHMARK_ITEMS, BENCHMARK_PROVENANCE
from app.evaluation.runner import run_benchmark_evaluation, evaluate_single_item
from app.evaluation.baselines import evaluate_retrieval_only_baseline, compare_baselines
from app.evaluation.export import export_report_to_markdown, export_report_to_json
from app.services.verification import VerificationService


class TestEvaluationPhase2(unittest.TestCase):
    def setUp(self):
        self.mock_retrieval = MagicMock()
        self.mock_verification = MagicMock()
        self.mock_verification.claim_to_hypothesis = VerificationService().claim_to_hypothesis
        self.mock_verification.classify_claim_status = VerificationService.classify_claim_status
        self.mock_verification.is_claim_supported = VerificationService.is_claim_supported

    # -------------------------------------------------------------
    # 1. Shared 3-Way Classification Logic & Parity Tests
    # -------------------------------------------------------------
    def test_01_classify_claim_status_supported(self):
        """Test classify_claim_status yields SUPPORTED when evidence confirms claim."""
        evidence = [
            {"entailment": 0.85, "contradiction": 0.05, "similarity": 0.80, "evidence_score": 0.75},
            {"entailment": 0.40, "contradiction": 0.10, "similarity": 0.30, "evidence_score": 0.25},
        ]
        status = VerificationService.classify_claim_status(evidence)
        self.assertEqual(status, "SUPPORTED")

    def test_02_classify_claim_status_contradicted(self):
        """Test classify_claim_status yields CONTRADICTED when strong contradiction exists."""
        evidence = [
            {"entailment": 0.10, "contradiction": 0.88, "similarity": 0.70, "evidence_score": 0.20},
            {"entailment": 0.05, "contradiction": 0.20, "similarity": 0.40, "evidence_score": 0.10},
        ]
        status = VerificationService.classify_claim_status(evidence)
        self.assertEqual(status, "CONTRADICTED")

    def test_03_classify_claim_status_unsupported(self):
        """Test classify_claim_status yields UNSUPPORTED when evidence is neutral or insufficient."""
        evidence = [
            {"entailment": 0.25, "contradiction": 0.15, "similarity": 0.30, "evidence_score": 0.20},
            {"entailment": 0.30, "contradiction": 0.10, "similarity": 0.35, "evidence_score": 0.25},
        ]
        status = VerificationService.classify_claim_status(evidence)
        self.assertEqual(status, "UNSUPPORTED")

    def test_04_classify_claim_status_empty_evidence(self):
        """Test classify_claim_status gracefully handles empty evidence list."""
        status = VerificationService.classify_claim_status([])
        self.assertEqual(status, "UNSUPPORTED")

    def test_05_production_verify_claims_uses_shared_classification(self):
        """Test that production verify_claims includes status matching classify_claim_status."""
        service = VerificationService()
        service._loaded = True
        service.nli_tokenizer = MagicMock()
        service.nli_model = MagicMock()

        mock_embedding_model = MagicMock()
        mock_embedding_model.encode.side_effect = lambda texts, **kw: np.ones((len(texts), 384), dtype="float32")

        mock_index = MagicMock()
        mock_index.search.return_value = (
            np.zeros((1, 1), dtype="float32"),
            np.zeros((1, 1), dtype="int64")
        )

        mock_chunks = [
            {"chunk_id": "c1", "page": 8, "text": "A1C >= 6.5% is diagnostic for diabetes."}
        ]
        mock_embeddings = np.ones((1, 384), dtype="float32")

        service.nli_score_batch = MagicMock(return_value=[
            {"entailment": 0.90, "contradiction": 0.02, "neutral": 0.08}
        ])

        answer = "A1C >= 6.5% confirms diabetes diagnosis."

        res = service.verify_claims(
            answer=answer,
            chunks=mock_chunks,
            embeddings=mock_embeddings,
            index=mock_index,
            embedding_model=mock_embedding_model,
            top_n=1
        )
        claims_list = res["claims"]
        self.assertEqual(len(claims_list), 1)
        self.assertIn("status", claims_list[0])
        self.assertEqual(claims_list[0]["status"], "SUPPORTED")
        self.assertTrue(claims_list[0]["supported"])

    # -------------------------------------------------------------
    # 2. Production-Aligned Generic Hypothesis Generation
    # -------------------------------------------------------------
    def test_06_evaluate_single_item_uses_generic_hypothesis_by_default(self):
        """Test evaluate_single_item uses claim_to_hypothesis by default instead of legacy."""
        item = {
            "id": "BM-TEST",
            "claim": "Testing is recommended for adults with BMI >= 25 kg/m² [Page 8].",
            "hypothesis": "Legacy hand-crafted hypothesis string.",
            "legacy_hypothesis": "Legacy hand-crafted hypothesis string.",
            "ground_truth": "SUPPORTED",
            "citation_page": 8,
        }

        self.mock_retrieval.search.return_value = [
            {"chunk_id": "chunk_008_01", "text": "Testing recommended for BMI >= 25.", "page": 8, "cosine_sim": 0.90}
        ]
        self.mock_verification.nli_score_batch.return_value = [
            {"entailment": 0.92, "contradiction": 0.02, "neutral": 0.06}
        ]
        self.mock_verification.is_claim_supported.return_value = True

        result = evaluate_single_item(
            item,
            self.mock_retrieval,
            self.mock_verification,
            use_legacy_hypothesis=False
        )

        # Should NOT use the legacy hand-crafted hypothesis
        self.assertNotEqual(result["hypothesis"], item["legacy_hypothesis"])
        # Should strip citation bracket and normalize
        self.assertNotIn("[Page 8]", result["hypothesis"])
        self.assertIn("BMI >= 25", result["hypothesis"])

    def test_07_evaluate_single_item_allows_legacy_hypothesis_flag(self):
        """Test evaluate_single_item respects use_legacy_hypothesis=True when explicitly requested."""
        item = {
            "id": "BM-TEST",
            "claim": "Testing is recommended for adults.",
            "hypothesis": "Default generic hypothesis.",
            "legacy_hypothesis": "Legacy hand-crafted hypothesis string.",
            "ground_truth": "SUPPORTED",
            "citation_page": 8,
        }

        self.mock_retrieval.search.return_value = [
            {"chunk_id": "chunk_008_01", "text": "Testing is recommended for adults.", "page": 8, "cosine_sim": 0.90}
        ]
        self.mock_verification.nli_score_batch.return_value = [
            {"entailment": 0.92, "contradiction": 0.02, "neutral": 0.06}
        ]
        self.mock_verification.is_claim_supported.return_value = True

        result = evaluate_single_item(
            item,
            self.mock_retrieval,
            self.mock_verification,
            use_legacy_hypothesis=True
        )

        self.assertEqual(result["hypothesis"], "Legacy hand-crafted hypothesis string.")
        self.assertEqual(result["legacy_hypothesis"], "Legacy hand-crafted hypothesis string.")

    # -------------------------------------------------------------
    # 3. Citation Page Alignment & Audit
    # -------------------------------------------------------------
    def test_08_benchmark_items_contain_verified_pages_and_booklet_pages(self):
        """Test all 15 benchmark items have citation_page, booklet_page, and verification_status."""
        self.assertEqual(len(BENCHMARK_ITEMS), 15)
        for item in BENCHMARK_ITEMS:
            self.assertIn("citation_page", item)
            self.assertIn("booklet_page", item)
            self.assertIn("verification_status", item)

            if item["ground_truth"] in ["SUPPORTED", "CONTRADICTED"]:
                self.assertIsNotNone(item["citation_page"], f"Item {item['id']} must have citation_page")
                self.assertIsNotNone(item["booklet_page"], f"Item {item['id']} must have booklet_page")
                self.assertIn(item["verification_status"], ["VERIFIED", "FLAGGED_FOR_HUMAN_REVIEW"])
            else:
                self.assertIsNone(item["citation_page"])
                self.assertIsNone(item["booklet_page"])
                self.assertEqual(item["verification_status"], "NOT_APPLICABLE")

    def test_09_bm02_flagged_for_human_review(self):
        """Test BM-02 is explicitly flagged for human review due to external ADA guidelines threshold."""
        bm02 = next(item for item in BENCHMARK_ITEMS if item["id"] == "BM-02")
        self.assertEqual(bm02["verification_status"], "FLAGGED_FOR_HUMAN_REVIEW")
        self.assertIn("human review", bm02["rationale"].lower())

    def test_10_citation_alignment_categories(self):
        """Test citation alignment auditor assigns MATCHED, ADJACENT_PAGE, MISMATCHED, NOT_APPLICABLE."""
        # Case A: Exact page match
        item_matched = {
            "id": "T1", "claim": "Sample claim", "ground_truth": "SUPPORTED", "citation_page": 8
        }
        self.mock_retrieval.search.return_value = [
            {"chunk_id": "c1", "text": "Sample text", "page": 8, "cosine_sim": 0.85}
        ]
        self.mock_verification.nli_score_batch.return_value = [
            {"entailment": 0.90, "contradiction": 0.05, "neutral": 0.05}
        ]
        res_matched = evaluate_single_item(item_matched, self.mock_retrieval, self.mock_verification)
        self.assertEqual(res_matched["citation_alignment"], "MATCHED")

        # Case B: Adjacent page (diff = 1)
        item_adj = {
            "id": "T2", "claim": "Sample claim", "ground_truth": "SUPPORTED", "citation_page": 8
        }
        self.mock_retrieval.search.return_value = [
            {"chunk_id": "c2", "text": "Sample text", "page": 9, "cosine_sim": 0.85}
        ]
        res_adj = evaluate_single_item(item_adj, self.mock_retrieval, self.mock_verification)
        self.assertEqual(res_adj["citation_alignment"], "ADJACENT_PAGE")

        # Case C: Mismatched page (diff > 1)
        item_mis = {
            "id": "T3", "claim": "Sample claim", "ground_truth": "SUPPORTED", "citation_page": 8
        }
        self.mock_retrieval.search.return_value = [
            {"chunk_id": "c3", "text": "Sample text", "page": 58, "cosine_sim": 0.85}
        ]
        res_mis = evaluate_single_item(item_mis, self.mock_retrieval, self.mock_verification)
        self.assertEqual(res_mis["citation_alignment"], "MISMATCHED")

        # Case D: Not applicable (unsupported claim with no citation_page)
        item_na = {
            "id": "T4", "claim": "Sample unsupported claim", "ground_truth": "UNSUPPORTED", "citation_page": None
        }
        self.mock_retrieval.search.return_value = [
            {"chunk_id": "c4", "text": "Sample text", "page": 8, "cosine_sim": 0.20}
        ]
        self.mock_verification.nli_score_batch.return_value = [
            {"entailment": 0.10, "contradiction": 0.10, "neutral": 0.80}
        ]
        res_na = evaluate_single_item(item_na, self.mock_retrieval, self.mock_verification)
        self.assertEqual(res_na["citation_alignment"], "NOT_APPLICABLE")

    # -------------------------------------------------------------
    # 4. Retrieval Baseline & Comparison Tests
    # -------------------------------------------------------------
    def test_11_retrieval_only_baseline_execution(self):
        """Test evaluate_retrieval_only_baseline classifies without NLI and cannot predict CONTRADICTED."""
        mock_ret = MagicMock()
        mock_ret.search.return_value = [
            {"chunk_id": "c1", "text": "Relevant text", "cosine_sim": 0.75, "page": 8}
        ]
        mock_ret.embedding_model.encode.side_effect = lambda texts, **kwargs: np.ones((len(texts), 384), dtype=np.float32)

        items = [
            {"id": "I1", "claim": "Claim 1", "ground_truth": "SUPPORTED"},
            {"id": "I2", "claim": "Claim 2", "ground_truth": "CONTRADICTED"},
        ]

        base_res = evaluate_retrieval_only_baseline(mock_ret, items=items, similarity_threshold=0.65)
        self.assertIn("accuracy", base_res)
        self.assertIn("macro_metrics", base_res)
        self.assertIn("binary_metrics", base_res)

        # Baseline cannot predict CONTRADICTED
        predicted_classes = {r["predicted"] for r in base_res["predictions"]}
        self.assertNotIn("CONTRADICTED", predicted_classes)

    def test_12_compare_baselines_accuracy_gain(self):
        """Test compare_baselines computes accuracy and F1 gains accurately."""
        full_report = {
            "accuracy": 0.867,
            "macro_metrics": {"precision": 0.85, "recall": 0.86, "f1_score": 0.855},
            "binary_metrics": {"f1_score": 0.88},
        }
        baseline_report = {
            "accuracy": 0.40,
            "macro_metrics": {"precision": 0.30, "recall": 0.35, "f1_score": 0.32},
            "binary_metrics": {"f1_score": 0.55},
        }

        comp = compare_baselines(full_report, baseline_report)
        self.assertIn("comparison_table", comp)
        self.assertAlmostEqual(comp["accuracy_gain"], 0.467, places=3)
        self.assertAlmostEqual(comp["f1_gain"], 0.535, places=3)
        self.assertEqual(len(comp["comparison_table"]), 2)

    # -------------------------------------------------------------
    # 5. Markdown and JSON Export Tests
    # -------------------------------------------------------------
    def test_13_export_report_to_markdown_format(self):
        """Test export_report_to_markdown produces valid GitHub-flavored Markdown document."""
        mock_report = {
            "timestamp": "2026-10-19T02:00:00Z",
            "total_items": 2,
            "duration_ms": 150,
            "accuracy": 1.0,
            "macro_metrics": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0},
            "binary_metrics": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "specificity": 1.0},
            "per_class": {
                "SUPPORTED": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "support": 1},
                "UNSUPPORTED": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "support": 1},
            },
            "confusion_matrix": {
                "labels": ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED"],
                "matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 1]],
                "total": 2,
            },
            "citation_summary": {
                "total_cited_items": 1,
                "matched": 1,
                "adjacent": 0,
                "mismatched": 0,
                "alignment_rate": 1.0,
            },
            "provenance": BENCHMARK_PROVENANCE,
            "results": [
                {
                    "id": "T-01",
                    "claim": "Testing in adults.",
                    "hypothesis": "Testing in adults.",
                    "ground_truth": "SUPPORTED",
                    "predicted": "SUPPORTED",
                    "is_correct": True,
                    "entailment": 0.95,
                    "contradiction": 0.02,
                    "similarity": 0.88,
                    "citation_page": 8,
                    "booklet_page": 12,
                    "verification_status": "VERIFIED",
                    "citation_alignment": "MATCHED",
                    "matched_page": 8,
                    "matched_chunk_id": "chunk_008_01",
                }
            ],
        }

        md_output = export_report_to_markdown(mock_report)
        self.assertIn("MedGuide AI", md_output)
        self.assertIn("Clinical Evaluation", md_output)
        self.assertIn("100.0%", md_output)
        self.assertIn("T-01", md_output)
        self.assertIn("Limitations", md_output)

    def test_14_export_report_to_json_format(self):
        """Test export_report_to_json produces valid parseable JSON."""
        mock_report = {
            "timestamp": "2026-10-19T02:00:00Z",
            "total_items": 1,
            "duration_ms": 100,
            "accuracy": 1.0,
            "macro_metrics": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0},
            "binary_metrics": {"precision": 1.0, "recall": 1.0, "f1_score": 1.0},
            "results": [],
            "provenance": BENCHMARK_PROVENANCE,
        }

        json_str = export_report_to_json(mock_report)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["accuracy"], 1.0)
        self.assertIn("Curated Gold Regression Suite", parsed["provenance"]["benchmark_type"])


if __name__ == "__main__":
    unittest.main()
