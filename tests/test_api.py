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


if __name__ == "__main__":
    unittest.main()
