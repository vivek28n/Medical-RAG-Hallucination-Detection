"""
Automated test suite for Medical RAG + Hallucination Detection API.

Covers:
1. Health check with models and index ready.
2. Query validation (empty / whitespace rejected).
3. Handling when Gemini client is absent/uninitialized (error handling).
4. Supported medical question: "What are the risk factors for type 2 diabetes?"
5. Unrelated question: "How to repair a car engine?" (evaluates low confidence / potential hallucination).
6. Response schema structure: sources, claims, confidence, hallucination_decision, self_correction.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.services.retrieval import retrieval_service
from app.services.verification import verification_service
from app.services.llm import llm_service


class TestMedicalRAGApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize test client using context manager to trigger lifespan (load models)
        cls.client_cm = TestClient(app)
        cls.client = cls.client_cm.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_cm.__exit__(None, None, None)

    def test_01_health_check_ready(self):
        """Test /health endpoint reports truthful and ready status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["ready"])
        self.assertTrue(data["models_loaded"]["embedding"])
        self.assertTrue(data["models_loaded"]["faiss_index"])
        self.assertTrue(data["models_loaded"]["nli"])
        self.assertTrue(data["models_loaded"]["gemini"])

    def test_02_empty_query_validation(self):
        """Test that empty or whitespace queries are rejected with 422 Unprocessable Entity."""
        # Pure whitespace
        res1 = self.client.post("/api/ask", json={"query": "   "})
        self.assertEqual(res1.status_code, 422)

        # Empty string
        res2 = self.client.post("/api/ask", json={"query": ""})
        self.assertEqual(res2.status_code, 422)

    def test_03_missing_llm_client_handling(self):
        """Test API error handling when Gemini client is temporarily uninitialized."""
        original_client = llm_service.client
        try:
            llm_service.client = None
            response = self.client.post("/api/ask", json={"query": "What are the symptoms of diabetes?"})
            self.assertEqual(response.status_code, 503)
            self.assertIn("Gemini LLM client is not configured", response.json()["detail"])
        finally:
            llm_service.client = original_client

    def test_04_supported_diabetes_question(self):
        """
        Test supported query: 'What are the risk factors for type 2 diabetes?'
        Verifies:
        - Response status 200
        - Non-empty answer
        - Sources returned with valid chunk_ids and pages
        - Claim verification results populated
        - Confidence score calculated and within [0, 1]
        - Hallucination decision present
        - Self correction details present
        """
        query = "What are the risk factors for type 2 diabetes?"
        response = self.client.post("/api/ask", json={"query": query})
        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()

        # 1. Answer
        self.assertTrue(isinstance(data.get("answer"), str) and len(data["answer"]) > 20)

        # 2. Sources
        sources = data.get("sources", [])
        self.assertGreater(len(sources), 0, "Expected at least 1 retrieved source chunk")
        for s in sources:
            self.assertIn("chunk_id", s)
            self.assertIn("page", s)
            self.assertIn("text", s)
            self.assertGreater(s["page"], 0)

        # 3. Claim verification
        claim_ver = data.get("claim_verification")
        self.assertIsNotNone(claim_ver)
        self.assertIn("claims", claim_ver)
        self.assertIn("supported_claims", claim_ver)
        self.assertIn("total_claims", claim_ver)
        self.assertIn("consistency_score", claim_ver)
        self.assertTrue(0.0 <= claim_ver["consistency_score"] <= 1.0)

        # 4. Confidence
        conf = data.get("confidence")
        self.assertIsNotNone(conf)
        self.assertIn(conf["confidence_level"], ["HIGH", "MEDIUM", "LOW"])
        self.assertTrue(0.0 <= conf["confidence_score"] <= 1.0)
        self.assertTrue(0.0 <= conf["semantic_similarity"] <= 1.0)
        self.assertTrue(0.0 <= conf["nli_entailment"] <= 1.0)
        self.assertTrue(0.0 <= conf["retrieval_quality"] <= 1.0)

        # 5. Hallucination decision
        decision = data.get("hallucination_decision")
        self.assertIsNotNone(decision)
        self.assertIn(decision["decision"], ["SUPPORTED", "POTENTIAL HALLUCINATION", "CONTRADICTED"])

        # 6. Self-correction
        corr = data.get("self_correction")
        self.assertIsNotNone(corr)
        self.assertIn("correction_needed", corr)
        self.assertIn("correction_applied", corr)
        self.assertIn("original_answer", corr)

        # 7. Pipeline trace
        trace = data.get("pipeline_trace")
        self.assertIsNotNone(trace, "pipeline_trace should be included in AskResponse")
        self.assertGreater(trace["total_duration_ms"], 0.0)
        self.assertEqual(len(trace["stages"]), 7)
        stage_names = [s["stage_name"] for s in trace["stages"]]
        self.assertEqual(stage_names, [
            "retrieval",
            "grounded_generation",
            "claim_verification",
            "confidence_scoring",
            "hallucination_decision",
            "self_correction",
            "re_verification",
        ])

    def test_05_unrelated_question(self):
        """
        Test an out-of-domain / unrelated question: 'How to repair a car engine?'
        Verifies the system either reports insufficient evidence or flags low confidence/potential hallucination.
        """
        query = "How to repair a car engine?"
        response = self.client.post("/api/ask", json={"query": query})
        self.assertEqual(response.status_code, 200, f"Error: {response.text}")
        data = response.json()
        self.assertTrue(isinstance(data.get("answer"), str) and len(data["answer"]) > 0)
        # Verify that retrieval quality for car engine against diabetes guidelines is low
        conf = data.get("confidence")
        self.assertIsNotNone(conf)
        # Retrieval quality for car engine in a diabetes document should be low (< 0.50)
        self.assertLess(conf["retrieval_quality"], 0.50)

    def test_06_retrieval_filtering_reference_chunks(self):
        """
        Test that retrieval prioritizes substantive clinical evidence and filters out
        bibliographic / reference citation blocks.
        """
        from app.services.retrieval import is_reference_chunk

        # Verify reference chunk detector accuracy
        ref_sample = "References 1. Jensen MD, Ryan DH, Apovian CM, et al. 2013 AHA/ACC/TOS guideline. Circulation. 2014;129(25 Suppl 2):S102-138. 2. American Diabetes Association. Diabetes Care. 2018;41:S13-S27."
        clinical_sample = "Principle 1: Identify People with Undiagnosed Diabetes and Prediabetes. Testing for prediabetes and type 2 diabetes should be considered in adults who are overweight or obese and have one or more risk factors."

        self.assertTrue(is_reference_chunk(ref_sample))
        self.assertFalse(is_reference_chunk(clinical_sample))

        # Test live search results
        results = retrieval_service.search("What are the risk factors for type 2 diabetes?", top_k=5)
        self.assertEqual(len(results), 5)
        for chunk in results:
            self.assertFalse(
                is_reference_chunk(chunk["text"]),
                f"Retrieved chunk {chunk['chunk_id']} is a reference-list chunk: {chunk['text'][:100]}"
            )

    def test_07_gemini_fallback_logic_mocked(self):
        """
        Task 3: Unit test Gemini fallback logic under quota (429) and model errors (404)
        using mocks to avoid burning API quota, and verify secrets are never leaked.
        """
        from unittest.mock import MagicMock, patch

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a grounded answer from the fallback model."

        # Case 1: First model hits 429 quota exhaustion; second candidate succeeds
        models_called = []
        def side_effect(model, contents):
            models_called.append(model)
            if model == "gemini-3-flash-preview":
                raise Exception("429 RESOURCE_EXHAUSTED. Daily quota exceeded for gemini-3-flash-preview.")
            return mock_response

        mock_client.models.generate_content.side_effect = side_effect

        original_client = llm_service.client
        try:
            llm_service.client = mock_client
            result = llm_service._generate_with_retry("Test prompt")
            self.assertEqual(result, "This is a grounded answer from the fallback model.")
            # Verify exact model iteration: first tried model 1, failed on 429, then called fallback model 2
            self.assertEqual(models_called, ["gemini-3-flash-preview", "gemini-flash-lite-latest"])
            self.assertEqual(mock_client.models.generate_content.call_count, 2)
        finally:
            llm_service.client = original_client


        # Case 2: All models fail with simulated key in error string -> verify redaction
        fake_secret_key = "AIzaSyFakeKeyForTesting123456789"
        mock_client_fail = MagicMock()
        mock_client_fail.models.generate_content.side_effect = Exception(
            f"429 Quota exhausted for key={fake_secret_key}"
        )

        with patch("app.services.llm.settings.GEMINI_API_KEY", fake_secret_key):
            try:
                llm_service.client = mock_client_fail
                with self.assertRaises(RuntimeError) as ctx:
                    llm_service._generate_with_retry("Test prompt")
                err_msg = str(ctx.exception)
                self.assertNotIn(fake_secret_key, err_msg)
                self.assertIn("[REDACTED]", err_msg)
            finally:
                llm_service.client = original_client

    def test_08_pipeline_trace_structure_and_real_timings(self):
        """
        Phase 1: Test real-time pipeline trace structure, realistic durations,
        and stage status transitions with mocked LLM generation.
        """
        from unittest.mock import patch
        from datetime import datetime

        mock_answer = (
            "Principle 1 states that testing for type 2 diabetes should be considered in adults "
            "who are overweight or obese and have one or more risk factors."
        )

        with patch.object(llm_service, "generate_grounded_answer", return_value=mock_answer):
            response = self.client.post("/api/ask", json={"query": "What are the risk factors for type 2 diabetes?"})
            self.assertEqual(response.status_code, 200)
            data = response.json()

            trace = data.get("pipeline_trace")
            self.assertIsNotNone(trace, "Pipeline trace must be present in response")

            # 1. Total duration and timestamp
            self.assertGreater(trace["total_duration_ms"], 0.0, "Total duration must be positive")
            # Must be a parseable ISO timestamp
            parsed_ts = datetime.fromisoformat(trace["timestamp"])
            self.assertIsNotNone(parsed_ts)

            # 2. Stages sequence
            stages = trace["stages"]
            self.assertEqual(len(stages), 7)
            expected_stages = [
                "retrieval",
                "grounded_generation",
                "claim_verification",
                "confidence_scoring",
                "hallucination_decision",
                "self_correction",
                "re_verification",
            ]
            self.assertEqual([s["stage_name"] for s in stages], expected_stages)

            # 3. Check durations and status
            for stage in stages:
                self.assertIn(stage["status"], ["completed", "skipped", "failed"])
                self.assertGreaterEqual(stage["duration_ms"], 0.0, f"Stage {stage['stage_name']} duration cannot be negative")

            # Retrieval stage details
            retrieval_stage = stages[0]
            self.assertEqual(retrieval_stage["status"], "completed")
            self.assertGreater(retrieval_stage["duration_ms"], 0.0)
            self.assertIn("chunks_retrieved", retrieval_stage["details"])
            self.assertIn("top_k", retrieval_stage["details"])
            self.assertIn("embedding_model", retrieval_stage["details"])

            # Claim verification stage details
            verification_stage = stages[2]
            self.assertEqual(verification_stage["status"], "completed")
            self.assertGreater(verification_stage["duration_ms"], 0.0)
            self.assertIn("total_claims", verification_stage["details"])
            self.assertIn("supported_claims", verification_stage["details"])
            self.assertIn("consistency_score", verification_stage["details"])
            self.assertIn("nli_model", verification_stage["details"])

            # Confidence stage details
            conf_stage = stages[3]
            self.assertEqual(conf_stage["status"], "completed")
            self.assertIn("confidence_score", conf_stage["details"])
            self.assertIn("confidence_level", conf_stage["details"])
            self.assertIn("semantic_similarity", conf_stage["details"])
            self.assertIn("retrieval_quality", conf_stage["details"])

    def test_09_pipeline_trace_skipped_vs_completed_stages(self):
        """
        Phase 1: Verify rule that skipped stages are NEVER reported as completed.
        - When self-correction is not applied: re_verification MUST have status='skipped' and duration_ms=0.0.
        - When self-correction is applied: re_verification MUST have status='completed' and duration_ms > 0.0.
        """
        from unittest.mock import patch

        # Case A: High quality answer, no correction applied
        mock_answer = "Testing for type 2 diabetes should be considered in adults who are overweight or obese."
        with patch.object(llm_service, "generate_grounded_answer", return_value=mock_answer):
            with patch("app.main.correction_service.perform_correction", return_value={
                "correction_needed": False,
                "correction_applied": False,
                "original_answer": mock_answer,
                "corrected_answer": None,
            }):
                response = self.client.post("/api/ask", json={"query": "What are the risk factors?"})
                self.assertEqual(response.status_code, 200)
                stages = response.json()["pipeline_trace"]["stages"]
                corr_stage = next(s for s in stages if s["stage_name"] == "self_correction")
                rever_stage = next(s for s in stages if s["stage_name"] == "re_verification")

                self.assertEqual(corr_stage["status"], "skipped")
                self.assertEqual(rever_stage["status"], "skipped")
                self.assertEqual(rever_stage["duration_ms"], 0.0)

        # Case B: Correction is triggered and applied
        with patch.object(llm_service, "generate_grounded_answer", return_value="Inaccurate initial statement."):
            with patch("app.main.correction_service.perform_correction", return_value={
                "correction_needed": True,
                "correction_applied": True,
                "original_answer": "Inaccurate initial statement.",
                "corrected_answer": "Corrected accurate medical guideline statement.",
            }):
                response = self.client.post("/api/ask", json={"query": "What are the risk factors?"})
                self.assertEqual(response.status_code, 200)
                stages = response.json()["pipeline_trace"]["stages"]
                corr_stage = next(s for s in stages if s["stage_name"] == "self_correction")
                rever_stage = next(s for s in stages if s["stage_name"] == "re_verification")

                self.assertEqual(corr_stage["status"], "completed")
                self.assertEqual(rever_stage["status"], "completed")
                self.assertGreater(rever_stage["duration_ms"], 0.0)
                self.assertIn("post_correction_supported", rever_stage["details"])

    def test_10_backward_compatibility_schema(self):
        """
        Phase 1: Test backward compatibility of AskResponse schema.
        Confirms that legacy consumers that do not expect or parse pipeline_trace
        continue to deserialize cleanly, and optional pipeline_trace can be omitted.
        """
        from app.schemas import AskResponse

        # Build query response
        with patch.object(llm_service, "generate_grounded_answer", return_value="Sample medical answer."):
            response = self.client.post("/api/ask", json={"query": "Sample test query"})
            self.assertEqual(response.status_code, 200)
            data = response.json()

            # 1. Validate full response parses with pipeline_trace
            full_model = AskResponse(**data)
            self.assertIsNotNone(full_model.pipeline_trace)

            # 2. Validate response parses without pipeline_trace (backward compatibility)
            legacy_data = {k: v for k, v in data.items() if k != "pipeline_trace"}
            legacy_model = AskResponse(**legacy_data)
            self.assertIsNone(legacy_model.pipeline_trace)
            self.assertEqual(legacy_model.answer, data["answer"])
            self.assertEqual(len(legacy_model.sources), len(data["sources"]))

    def test_11_evidence_mapping_and_integrity(self):
        """
        Phase 2: Test bidirectional evidence mapping and integrity.
        Verifies:
        - Claims with evidence have real chunk IDs, non-empty text, and valid NLI scores.
        - Supported claims strictly require verified evidence (never fabricated support).
        - Claims with no evidence are marked unsupported.
        """
        from app.schemas import AskResponse

        mock_answer = (
            "Principle 1 states that testing for type 2 diabetes should be considered in adults "
            "who are overweight or obese and have one or more risk factors."
        )

        with patch.object(llm_service, "generate_grounded_answer", return_value=mock_answer):
            response = self.client.post("/api/ask", json={"query": "What are the risk factors for type 2 diabetes?"})
            self.assertEqual(response.status_code, 200)
            data = response.json()

            claims = data["claim_verification"]["claims"]
            self.assertGreater(len(claims), 0, "Expected at least one claim to be extracted")

            for claim in claims:
                self.assertIn("claim", claim)
                self.assertIn("hypothesis", claim)
                self.assertIn("supported", claim)

                if claim["supported"]:
                    # Supported claims MUST have evidence attached
                    self.assertIsNotNone(claim["evidence"], f"Claim #{claim['claim_number']} is marked supported but has no evidence")
                    ev = claim["evidence"]
                    self.assertTrue(len(ev["chunk_id"]) > 0)
                    self.assertTrue(len(ev["text"]) > 0)
                    self.assertTrue(0.0 <= ev["entailment"] <= 1.0)
                    self.assertTrue(0.0 <= ev["contradiction"] <= 1.0)
                    self.assertTrue(0.0 <= ev["similarity"] <= 1.0)
                else:
                    # If unsupported, it may either have weak evidence or None
                    if claim["evidence"] is not None:
                        ev = claim["evidence"]
                        self.assertTrue(len(ev["chunk_id"]) > 0)

    def test_12_missing_page_metadata_handling(self):
        """
        Phase 2: Test truthful handling when chunk page metadata is unavailable.
        Ensures SourceEvidence and ClaimEvidence allow page=None without validation errors.
        """
        from app.schemas import SourceEvidence, ClaimEvidence, AskResponse

        # 1. SourceEvidence with page=None
        source_none_page = SourceEvidence(
            chunk_id="chunk_unpaged_001",
            page=None,
            text="Clinical guideline text without page number."
        )
        self.assertIsNone(source_none_page.page)
        self.assertEqual(source_none_page.chunk_id, "chunk_unpaged_001")

        # 2. ClaimEvidence with page=None
        claim_none_page = ClaimEvidence(
            chunk_id="chunk_unpaged_001",
            page=None,
            text="Clinical guideline text without page number.",
            similarity=0.85,
            entailment=0.92,
            contradiction=0.01,
            neutral=0.07,
            evidence_score=0.88,
        )
        self.assertIsNone(claim_none_page.page)

        # 3. Simulate backend search returning chunks without 'page' key
        mock_chunks = [
            {"chunk_id": "chunk_no_page_1", "text": "Testing for diabetes in adults."},
            {"chunk_id": "chunk_no_page_2", "text": "Overweight and obesity risk factors."},
        ]

        with patch.object(retrieval_service, "search", return_value=mock_chunks):
            with patch.object(llm_service, "generate_grounded_answer", return_value="Testing for diabetes in adults."):
                response = self.client.post("/api/ask", json={"query": "diabetes testing"})
                self.assertEqual(response.status_code, 200)
                data = response.json()

                # Verify sources serialize cleanly with page as None
                sources = data["sources"]
                self.assertEqual(len(sources), 2)
                for s in sources:
                    self.assertIsNone(s["page"])

    def test_13_evidence_backward_compatibility(self):
        """
        Phase 2: Verify backward compatibility with integer pages and existing clients.
        Legacy responses containing integer page fields must validate seamlessly alongside optional ones.
        """
        from app.schemas import SourceEvidence, ClaimEvidence

        # Integer page (legacy)
        legacy_source = SourceEvidence(chunk_id="chunk_legacy", page=12, text="Legacy text")
        self.assertEqual(legacy_source.page, 12)

        # None page (new)
        modern_source = SourceEvidence(chunk_id="chunk_modern", page=None, text="Modern text")
        self.assertIsNone(modern_source.page)

        # Default omitted page
        default_source = SourceEvidence(chunk_id="chunk_default", text="Default text")
        self.assertIsNone(default_source.page)


if __name__ == "__main__":
    unittest.main()
