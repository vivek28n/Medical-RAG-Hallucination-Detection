"""
Retrieval service — FAISS vector search.

Loads the pre-built FAISS index + metadata produced by
scripts/build_index.py and provides similarity search.
"""

import os
import re
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings


def is_reference_chunk(text: str) -> bool:
    """
    Identifies whether a text chunk consists primarily of bibliography/reference list entries.
    Prevents reference-list pollution from diluting clinical evidence and lowering NLI consistency.
    """
    t = text.strip()
    if not t:
        return False

    # Check for direct 'References' section headers
    if re.search(r"^(\d+\s+)?(references|reference list)\b", t, re.IGNORECASE):
        return True

    et_al_count = len(re.findall(r"\bet al\.?", t, re.IGNORECASE))
    journal_citations = len(re.findall(r"\b(19\d\d|20\d\d)\s*;\s*\d+", t))
    numbered_citations = len(re.findall(r"(?:^|\s)\d+\.\s+[A-Z][a-z]+", t))
    doi_or_url = len(re.findall(r"\b(doi|pmid|https?://|www\.)", t, re.IGNORECASE))

    # Dense concentration of citations
    if numbered_citations >= 2 and (journal_citations >= 1 or et_al_count >= 1 or doi_or_url >= 1):
        return True
    if journal_citations >= 2 and et_al_count >= 1:
        return True
    if et_al_count >= 3 and journal_citations >= 1:
        return True
    if "references" in t.lower() and (numbered_citations >= 1 or journal_citations >= 1):
        return True

    return False


class RetrievalService:
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.metadata = []
        self.embeddings = None  # stored for verification service

    def load_models_and_index(self):
        """Load embedding model and FAISS index at startup."""
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

        index_path = os.path.join(settings.VECTOR_DB_PATH, "index.faiss")
        metadata_path = os.path.join(settings.VECTOR_DB_PATH, "metadata.json")

        if os.path.exists(index_path) and os.path.exists(metadata_path):
            print(f"Loading FAISS index: {index_path}")
            self.index = faiss.read_index(index_path)

            print(f"Loading metadata: {metadata_path}")
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            print(f"Loaded {self.index.ntotal} vectors.")

            embeddings_path = os.path.join(settings.VECTOR_DB_PATH, "embeddings.npy")
            if os.path.exists(embeddings_path):
                print(f"Loading cached embeddings: {embeddings_path}")
                self.embeddings = np.load(embeddings_path)
            else:
                # Re-encode chunks to have embeddings available for verification
                print("Encoding chunks for verification service...")
                texts = [chunk["text"] for chunk in self.metadata]
                self.embeddings = self.embedding_model.encode(
                    texts, show_progress_bar=False
                ).astype("float32")
                try:
                    np.save(embeddings_path, self.embeddings)
                    print(f"Saved embeddings cache: {embeddings_path}")
                except Exception as save_err:
                    print(f"Warning: could not save embeddings cache: {save_err}")

            print(f"Embeddings shape: {self.embeddings.shape}")

        else:
            print(
                "WARNING: FAISS index or metadata not found. "
                "Run scripts/build_index.py first."
            )

    def search(self, query: str, top_k: int = 5) -> list:
        """
        Search the FAISS index for the most relevant clinical chunks.
        Filters out reference-list chunks while safely backfilling if evidence is limited.
        """
        if not self.index or not self.embedding_model:
            raise RuntimeError("Retrieval models/index not loaded.")

        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        # Retrieve a broader candidate pool to filter out bibliographic citation blocks
        candidate_k = min(len(self.metadata), max(top_k * 3, top_k + 15))
        distances, indices = self.index.search(query_embedding, k=candidate_k)

        clinical_chunks = []
        reference_chunks = []

        for rank, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.metadata):
                chunk = self.metadata[idx]
                if is_reference_chunk(chunk.get("text", "")):
                    reference_chunks.append(chunk)
                else:
                    clinical_chunks.append(chunk)

        # Prioritize actual clinical and guidance evidence; backfill with reference chunks if needed
        results = clinical_chunks[:top_k]
        if len(results) < top_k:
            needed = top_k - len(results)
            results.extend(reference_chunks[:needed])

        return results


retrieval_service = RetrievalService()
