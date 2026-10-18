"""
Knowledge Base Service — Read-only inspection of indexed medical corpus and metadata.

Derives verified document details, chunk statistics, index parameters,
and paginated chunk previews without modifying FAISS index or embedding files.
"""

import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import numpy as np

from app.config import settings
from app.services.retrieval import is_reference_chunk


def get_knowledge_base_overview(
    retrieval_service,
    pdf_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes genuine corpus, index, model, and storage metadata
    derived exclusively from loaded memory structures and verified files on disk.
    """
    metadata: List[Dict[str, Any]] = retrieval_service.metadata or []
    index = retrieval_service.index
    embeddings = retrieval_service.embeddings

    # ── 1. Document File Verification ────────────────────────────────
    if pdf_path is None:
        pdf_path = os.path.abspath(
            os.path.join(settings.DATASET_PATH, settings.PDF_FILENAME)
        )

    file_exists = os.path.exists(pdf_path)
    file_size_bytes = os.path.getsize(pdf_path) if file_exists else None
    last_modified = (
        datetime.fromtimestamp(os.path.getmtime(pdf_path), tz=timezone.utc).isoformat()
        if file_exists else None
    )

    # ── 2. Corpus & Chunk Statistics ─────────────────────────────────
    total_chunks = len(metadata)
    if total_chunks > 0:
        char_lengths = [len(c.get("text", "")) for c in metadata]
        avg_chunk_length = round(float(np.mean(char_lengths)), 1)
        min_chunk_length = int(min(char_lengths))
        max_chunk_length = int(max(char_lengths))

        ref_count = sum(1 for c in metadata if is_reference_chunk(c.get("text", "")))
        clinical_count = total_chunks - ref_count

        pages_with_vals = [c.get("page") for c in metadata if c.get("page") is not None]
        unique_pages = sorted(list(set(pages_with_vals)))
        pages_with_chunks = len(unique_pages)
        missing_page_metadata_chunks = sum(1 for c in metadata if c.get("page") is None)
        total_pages = len(unique_pages) if unique_pages else None
    else:
        avg_chunk_length = None
        min_chunk_length = None
        max_chunk_length = None
        ref_count = 0
        clinical_count = 0
        pages_with_chunks = 0
        missing_page_metadata_chunks = 0
        total_pages = None

    # ── 3. Index & Storage Verification ──────────────────────────────
    index_path = os.path.join(settings.VECTOR_DB_PATH, "index.faiss")
    index_file_exists = os.path.exists(index_path)
    index_file_size_bytes = os.path.getsize(index_path) if index_file_exists else None

    embeddings_path = os.path.join(settings.VECTOR_DB_PATH, "embeddings.npy")
    embeddings_file_exists = os.path.exists(embeddings_path)
    embeddings_file_size_bytes = os.path.getsize(embeddings_path) if embeddings_file_exists else None

    index_type = type(index).__name__ if index is not None else None
    dimension = getattr(index, "d", None) if index is not None else None
    total_vectors = getattr(index, "ntotal", total_chunks) if index is not None else total_chunks
    is_trained = bool(getattr(index, "is_trained", False)) if index is not None else False

    embeddings_shape = list(embeddings.shape) if embeddings is not None else None

    # ── 4. Build Structured Overview ─────────────────────────────────
    document_meta = {
        "filename": os.path.basename(pdf_path),
        "title": "Guiding Principles for the Care of People With or at Risk for Diabetes",
        "publisher": "National Diabetes Education Program (NDEP) • NIH / CDC",
        "source_path": os.path.join("dataset", "raw", os.path.basename(pdf_path)).replace("\\", "/"),
        "file_exists": file_exists,
        "file_size_bytes": file_size_bytes,
        "last_modified": last_modified,
        "total_pages": total_pages,
    }

    index_meta = {
        "index_type": index_type,
        "metric": "L2 (Squared Euclidean Distance)",
        "dimension": dimension,
        "total_vectors": total_vectors,
        "is_trained": is_trained,
        "index_file_exists": index_file_exists,
        "index_file_size_bytes": index_file_size_bytes,
        "embeddings_file_exists": embeddings_file_exists,
        "embeddings_file_size_bytes": embeddings_file_size_bytes,
        "embeddings_shape": embeddings_shape,
    }

    chunking_config = {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "splitter_type": "RecursiveCharacterTextSplitter",
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
    }

    corpus_stats = {
        "total_chunks": total_chunks,
        "avg_chunk_length": avg_chunk_length,
        "min_chunk_length": min_chunk_length,
        "max_chunk_length": max_chunk_length,
        "clinical_chunks_count": clinical_count,
        "reference_chunks_count": ref_count,
        "pages_with_chunks": pages_with_chunks,
        "missing_page_metadata_chunks": missing_page_metadata_chunks,
    }

    is_ready = bool(file_exists and total_chunks > 0 and index is not None)

    return {
        "document": document_meta,
        "index": index_meta,
        "chunking": chunking_config,
        "corpus_statistics": corpus_stats,
        "is_ready": is_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_knowledge_base_chunks(
    retrieval_service,
    page: Optional[int] = None,
    search: Optional[str] = None,
    chunk_type: Optional[str] = "all",
    offset: int = 0,
    limit: int = 15,
) -> Dict[str, Any]:
    """
    Returns filtered and paginated chunk entries with exact previews and metadata.
    Distinguishes missing page metadata from zero or valid integer pages.
    """
    metadata: List[Dict[str, Any]] = retrieval_service.metadata or []

    # Safe pagination constraints
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    # Filtering
    filtered = []
    search_term = search.strip().lower() if search and search.strip() else None
    ctype = (chunk_type or "all").lower().strip()

    for chunk in metadata:
        chunk_text = chunk.get("text", "")
        chunk_id = chunk.get("chunk_id", "")
        chunk_page = chunk.get("page")

        # 1. Page Filter
        if page is not None and chunk_page != page:
            continue

        # 2. Search Keyword Filter
        if search_term and (search_term not in chunk_text.lower() and search_term not in chunk_id.lower()):
            continue

        # 3. Chunk Type Filter
        is_ref = is_reference_chunk(chunk_text)
        if ctype == "clinical" and is_ref:
            continue
        if ctype == "reference" and not is_ref:
            continue

        preview = chunk_text[:140] + ("…" if len(chunk_text) > 140 else "")

        filtered.append({
            "chunk_id": chunk_id,
            "page": chunk_page,
            "page_available": chunk_page is not None,
            "char_length": len(chunk_text),
            "is_reference": is_ref,
            "text": chunk_text,
            "preview": preview,
        })

    total_matching = len(filtered)
    paged = filtered[offset : offset + limit]

    return {
        "total_matching": total_matching,
        "offset": offset,
        "limit": limit,
        "chunks": paged,
    }
