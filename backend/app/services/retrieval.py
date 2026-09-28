import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings

class RetrievalService:
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.metadata = []

    def load_models_and_index(self):
        print("Loading Embedding model...")
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        
        index_path = os.path.join(settings.VECTOR_DB_PATH, "index.faiss")
        metadata_path = os.path.join(settings.VECTOR_DB_PATH, "metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            print("Loading FAISS index...")
            self.index = faiss.read_index(index_path)
            print("Loading metadata...")
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            print(f"Loaded {self.index.ntotal} vectors.")
        else:
            print("WARNING: FAISS index or metadata not found. Please run ingestion script.")

    def search(self, query: str, top_k: int = 5):
        if not self.index or not self.embedding_model:
            raise RuntimeError("Retrieval models/index not loaded.")
            
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")
        
        distances, indices = self.index.search(query_embedding, k=top_k)
        
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < len(self.metadata) and idx >= 0:
                results.append(self.metadata[idx])
        return results

retrieval_service = RetrievalService()
