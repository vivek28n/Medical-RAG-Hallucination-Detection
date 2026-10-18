"""
Unit tests for Knowledge Base Explorer service and endpoints.

Tests metadata accuracy, empty/unavailable metadata handling,
missing page metadata distinction, pagination, filtering, and API contracts.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Ensure project root and backend dir are in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.services.retrieval import retrieval_service
from app.knowledge_base.service import get_knowledge_base_overview, get_knowledge_base_chunks


class TestKnowledgeBaseExplorer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load models/index if not already loaded
        if not retrieval_service.index or not retrieval_service.metadata:
            retrieval_service.load_models_and_index()
        cls.client = TestClient(app)

    def test_01_knowledge_base_overview_live(self):
        """Test overview statistics derived from the loaded 83-page diabetes guideline corpus."""
        overview = get_knowledge_base_overview(retrieval_service)

        self.assertIn("document", overview)
        self.assertIn("index", overview)
        self.assertIn("chunking", overview)
        self.assertIn("corpus_statistics", overview)

        # Document checks
        doc = overview["document"]
        self.assertEqual(doc["filename"], "niddk_guiding_principles_diabetes.pdf")
        self.assertTrue(doc["file_exists"])
        self.assertGreater(doc["file_size_bytes"], 1000000)
        self.assertEqual(doc["total_pages"], 83)

        # Index checks
        idx = overview["index"]
        self.assertEqual(idx["dimension"], 384)
        self.assertEqual(idx["total_vectors"], 268)
        self.assertEqual(idx["index_type"], "IndexFlatL2")
        self.assertTrue(idx["index_file_exists"])

        # Corpus statistics checks
        stats = overview["corpus_statistics"]
        self.assertEqual(stats["total_chunks"], 268)
        self.assertEqual(stats["pages_with_chunks"], 83)
        self.assertGreater(stats["avg_chunk_length"], 800)
        self.assertGreater(stats["clinical_chunks_count"], 200)
        self.assertGreater(stats["reference_chunks_count"], 0)
        self.assertEqual(
            stats["clinical_chunks_count"] + stats["reference_chunks_count"],
            stats["total_chunks"]
        )

    def test_02_empty_metadata_handling(self):
        """Test graceful degradation when metadata and index are empty."""
        mock_retrieval = MagicMock()
        mock_retrieval.metadata = []
        mock_retrieval.index = None
        mock_retrieval.embeddings = None

        overview = get_knowledge_base_overview(mock_retrieval)

        stats = overview["corpus_statistics"]
        self.assertEqual(stats["total_chunks"], 0)
        self.assertIsNone(stats["avg_chunk_length"])
        self.assertIsNone(stats["min_chunk_length"])
        self.assertIsNone(stats["max_chunk_length"])
        self.assertEqual(stats["clinical_chunks_count"], 0)
        self.assertEqual(stats["reference_chunks_count"], 0)

        self.assertFalse(overview["is_ready"])

    def test_03_missing_page_metadata_distinction(self):
        """Test truthful distinction between available page numbers and missing page metadata."""
        mock_retrieval = MagicMock()
        mock_retrieval.metadata = [
            {"chunk_id": "c1", "page": 12, "text": "Clinical guideline text for diabetes."},
            {"chunk_id": "c2", "page": None, "text": "Snippet with unavailable page metadata."},
            {"chunk_id": "c3", "text": "Snippet with completely missing page key."},
        ]
        mock_retrieval.index = MagicMock(d=384, ntotal=3, is_trained=True)
        mock_retrieval.embeddings = None

        overview = get_knowledge_base_overview(mock_retrieval)
        stats = overview["corpus_statistics"]

        self.assertEqual(stats["total_chunks"], 3)
        self.assertEqual(stats["pages_with_chunks"], 1)
        self.assertEqual(stats["missing_page_metadata_chunks"], 2)

        # Test chunk pagination response distinction
        chunks_res = get_knowledge_base_chunks(mock_retrieval, limit=10)
        self.assertEqual(chunks_res["total_matching"], 3)
        items = chunks_res["chunks"]

        # Item 0 has page 12
        self.assertEqual(items[0]["page"], 12)
        self.assertTrue(items[0]["page_available"])

        # Item 1 has explicit None
        self.assertIsNone(items[1]["page"])
        self.assertFalse(items[1]["page_available"])

        # Item 2 had missing key
        self.assertIsNone(items[2]["page"])
        self.assertFalse(items[2]["page_available"])

    def test_04_missing_pdf_file_handling(self):
        """Test that non-existent PDF file is truthfully reported rather than fabricated."""
        mock_retrieval = MagicMock()
        mock_retrieval.metadata = [{"chunk_id": "c1", "page": 1, "text": "Sample text"}]
        mock_retrieval.index = MagicMock(d=384, ntotal=1, is_trained=True)
        mock_retrieval.embeddings = None

        non_existent_path = "dataset/raw/non_existent_file.pdf"
        overview = get_knowledge_base_overview(mock_retrieval, pdf_path=non_existent_path)

        doc = overview["document"]
        self.assertFalse(doc["file_exists"])
        self.assertIsNone(doc["file_size_bytes"])
        self.assertIsNone(doc["last_modified"])
        self.assertFalse(overview["is_ready"])

    def test_05_chunk_filtering_and_pagination(self):
        """Test search, page filtering, chunk type classification, and pagination."""
        # 1. Page filtering
        res_p12 = get_knowledge_base_chunks(retrieval_service, page=12)
        self.assertGreater(res_p12["total_matching"], 0)
        for c in res_p12["chunks"]:
            self.assertEqual(c["page"], 12)

        # 2. Search keyword filtering
        res_search = get_knowledge_base_chunks(retrieval_service, search="retinopathy")
        self.assertGreater(res_search["total_matching"], 0)
        for c in res_search["chunks"]:
            self.assertTrue(
                "retinopathy" in c["text"].lower() or "retinopathy" in c["chunk_id"].lower()
            )

        # 3. Reference vs Clinical filtering
        res_refs = get_knowledge_base_chunks(retrieval_service, chunk_type="reference")
        res_clinical = get_knowledge_base_chunks(retrieval_service, chunk_type="clinical")

        self.assertGreater(res_refs["total_matching"], 0)
        self.assertGreater(res_clinical["total_matching"], 0)
        for c in res_refs["chunks"]:
            self.assertTrue(c["is_reference"])
        for c in res_clinical["chunks"]:
            self.assertFalse(c["is_reference"])

        # 4. Pagination
        res_paged = get_knowledge_base_chunks(retrieval_service, offset=5, limit=5)
        self.assertEqual(res_paged["offset"], 5)
        self.assertEqual(res_paged["limit"], 5)
        self.assertEqual(len(res_paged["chunks"]), 5)

    def test_06_api_endpoints(self):
        """Test GET /api/knowledge-base/overview and GET /api/knowledge-base/chunks via HTTP."""
        resp_overview = self.client.get("/api/knowledge-base/overview")
        self.assertEqual(resp_overview.status_code, 200)
        data = resp_overview.json()
        self.assertEqual(data["document"]["filename"], "niddk_guiding_principles_diabetes.pdf")
        self.assertEqual(data["corpus_statistics"]["total_chunks"], 268)

        resp_chunks = self.client.get("/api/knowledge-base/chunks?limit=5&chunk_type=clinical")
        self.assertEqual(resp_chunks.status_code, 200)
        cdata = resp_chunks.json()
        self.assertEqual(cdata["limit"], 5)
        self.assertEqual(len(cdata["chunks"]), 5)
        self.assertFalse(cdata["chunks"][0]["is_reference"])


if __name__ == "__main__":
    unittest.main()
