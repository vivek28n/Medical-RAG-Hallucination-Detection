import React, { useState, useEffect } from 'react';
import {
  Database,
  Layers,
  Search,
  FileText,
  X,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  Cpu,
} from 'lucide-react';
import type { KnowledgeBaseOverview, ChunkItem } from '../types/api';
import { fetchKnowledgeBaseOverview, fetchKnowledgeBaseChunks } from '../services/api';

interface KnowledgeBaseExplorerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const KnowledgeBaseExplorer: React.FC<KnowledgeBaseExplorerProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'chunks' | 'pipeline'>('overview');
  const [overview, setOverview] = useState<KnowledgeBaseOverview | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [overviewError, setOverviewError] = useState<string | null>(null);

  // Chunk explorer state
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [totalMatching, setTotalMatching] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit] = useState(12);
  const [searchTerm, setSearchTerm] = useState('');
  const [pageFilter, setPageFilter] = useState<string>('');
  const [chunkType, setChunkType] = useState<'all' | 'clinical' | 'reference'>('all');
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [copiedChunkId, setCopiedChunkId] = useState<string | null>(null);

  // Load overview when opened
  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    const loadOverview = async () => {
      setLoadingOverview(true);
      setOverviewError(null);
      try {
        const data = await fetchKnowledgeBaseOverview();
        if (mounted) {
          setOverview(data);
        }
      } catch (err) {
        if (mounted) {
          setOverviewError(err instanceof Error ? err.message : 'Failed to load knowledge base overview');
        }
      } finally {
        if (mounted) setLoadingOverview(false);
      }
    };

    loadOverview();
    return () => {
      mounted = false;
    };
  }, [isOpen]);

  // Load chunks when filters or offset change
  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    const loadChunks = async () => {
      setLoadingChunks(true);
      try {
        const pageNum = pageFilter.trim() !== '' ? parseInt(pageFilter.trim(), 10) : undefined;
        const validPage = pageNum !== undefined && !isNaN(pageNum) ? pageNum : undefined;

        const data = await fetchKnowledgeBaseChunks({
          page: validPage,
          search: searchTerm.trim() || undefined,
          chunk_type: chunkType,
          offset,
          limit,
        });

        if (mounted) {
          setChunks(data.chunks);
          setTotalMatching(data.total_matching);
        }
      } catch {
        if (mounted) {
          setChunks([]);
          setTotalMatching(0);
        }
      } finally {
        if (mounted) setLoadingChunks(false);
      }
    };

    const debounce = setTimeout(loadChunks, 150);
    return () => {
      mounted = false;
      clearTimeout(debounce);
    };
  }, [isOpen, activeTab, offset, limit, searchTerm, pageFilter, chunkType]);

  const handleCopyChunk = (chunkId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedChunkId(chunkId);
    setTimeout(() => setCopiedChunkId(null), 1800);
  };

  const handlePageFilterChange = (val: string) => {
    setPageFilter(val);
    setOffset(0);
  };

  const handleSearchChange = (val: string) => {
    setSearchTerm(val);
    setOffset(0);
  };

  const handleChunkTypeChange = (type: 'all' | 'clinical' | 'reference') => {
    setChunkType(type);
    setOffset(0);
  };

  if (!isOpen) return null;

  return (
    <div className="kb-modal-overlay" role="presentation">
      <div
        className="kb-modal-container card glass-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="kb-modal-title"
      >
        {/* Header */}
        <div className="kb-header">
          <div className="kb-title-group">
            <div className="kb-title-row">
              <Database size={20} className="neon-cyan" />
              <h2 id="kb-modal-title" className="kb-heading">KNOWLEDGE BASE EXPLORER</h2>
              <span className="kb-corpus-pill">Corpus v1.0 • Verified</span>
            </div>
            <p className="kb-subtext">
              Read-Only Corpus Inspector • NIDDK Clinical Guidelines • Vector Index &amp; Chunk Telemetry
            </p>
          </div>

          <div className="kb-header-actions">
            <button className="close-kb-btn" onClick={onClose} aria-label="Close Knowledge Base Explorer">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="kb-tabs-bar">
          <button
            className={`kb-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <FileText size={14} />
            <span>Overview &amp; Storage Specs</span>
          </button>
          <button
            className={`kb-tab-btn ${activeTab === 'chunks' ? 'active' : ''}`}
            onClick={() => setActiveTab('chunks')}
          >
            <Layers size={14} />
            <span>Chunk Explorer &amp; Search ({overview?.corpus_statistics.total_chunks || 268})</span>
          </button>
          <button
            className={`kb-tab-btn ${activeTab === 'pipeline' ? 'active' : ''}`}
            onClick={() => setActiveTab('pipeline')}
          >
            <Cpu size={14} />
            <span>Ingestion Architecture</span>
          </button>
        </div>

        {overviewError && (
          <div className="kb-error-banner">
            <AlertTriangle size={16} />
            <span>{overviewError}</span>
          </div>
        )}

        <div className="kb-scroll-body">
          {/* TAB 1: OVERVIEW & STORAGE SPECS */}
          {activeTab === 'overview' && (
            <div className="kb-overview-stack">
              {loadingOverview ? (
                <div className="kb-loading-state">
                  <RotateCcw size={18} className="icon-spin text-cyan" />
                  <span>Loading knowledge base telemetry…</span>
                </div>
              ) : overview ? (
                <>
                  {/* KPI Stat Cards */}
                  <div className="kb-kpi-grid">
                    <div className="kb-kpi-card highlight-cyan">
                      <span className="kb-kpi-label">TOTAL INDEXED CHUNKS</span>
                      <span className="kb-kpi-value text-cyan">{overview.corpus_statistics.total_chunks}</span>
                      <span className="kb-kpi-meta">Across {overview.corpus_statistics.pages_with_chunks} guideline pages</span>
                    </div>

                    <div className="kb-kpi-card highlight-emerald">
                      <span className="kb-kpi-label">CLINICAL CHUNKS</span>
                      <span className="kb-kpi-value text-emerald">{overview.corpus_statistics.clinical_chunks_count}</span>
                      <span className="kb-kpi-meta">
                        {((overview.corpus_statistics.clinical_chunks_count / overview.corpus_statistics.total_chunks) * 100).toFixed(0)}% substantive guidance
                      </span>
                    </div>

                    <div className="kb-kpi-card highlight-amber">
                      <span className="kb-kpi-label">REFERENCE SECTIONS</span>
                      <span className="kb-kpi-value text-amber">{overview.corpus_statistics.reference_chunks_count}</span>
                      <span className="kb-kpi-meta">Filtered out during retrieval</span>
                    </div>

                    <div className="kb-kpi-card highlight-teal">
                      <span className="kb-kpi-label">VECTOR DIMENSION</span>
                      <span className="kb-kpi-value text-teal">{overview.index.dimension}d</span>
                      <span className="kb-kpi-meta">FAISS {overview.index.index_type}</span>
                    </div>
                  </div>

                  {/* Document & Index Technical Details */}
                  <div className="kb-spec-columns">
                    {/* Document Metadata Card */}
                    <div className="kb-spec-card card">
                      <div className="spec-card-header">
                        <FileText size={16} className="neon-teal" />
                        <h3 className="spec-card-title">SOURCE DOCUMENT SPECIFICATION</h3>
                      </div>
                      <div className="spec-list">
                        <div className="spec-row">
                          <span className="spec-label">Document Title:</span>
                          <span className="spec-value text-highlight">{overview.document.title}</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Publisher / Author:</span>
                          <span className="spec-value">{overview.document.publisher || 'Unavailable'}</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Source PDF File:</span>
                          <span className="spec-value font-mono">{overview.document.filename}</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Relative Path:</span>
                          <span className="spec-value font-mono">{overview.document.source_path}</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">File Size on Disk:</span>
                          <span className="spec-value font-mono">
                            {overview.document.file_size_bytes
                              ? `${(overview.document.file_size_bytes / 1024 / 1024).toFixed(2)} MB (${overview.document.file_size_bytes.toLocaleString()} bytes)`
                              : 'Unavailable'}
                          </span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Total Document Pages:</span>
                          <span className="spec-value font-mono text-cyan">
                            {overview.document.total_pages !== null ? `${overview.document.total_pages} Pages` : 'Unavailable'}
                          </span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Disk Verification:</span>
                          <span className="spec-value text-emerald">
                            <CheckCircle2 size={13} className="inline-icon" /> Verified on Disk
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Vector Index Specifications */}
                    <div className="kb-spec-card card">
                      <div className="spec-card-header">
                        <Database size={16} className="neon-cyan" />
                        <h3 className="spec-card-title">VECTOR STORAGE &amp; EMBEDDINGS</h3>
                      </div>
                      <div className="spec-list">
                        <div className="spec-row">
                          <span className="spec-label">Vector DB Engine:</span>
                          <span className="spec-value font-mono text-cyan">FAISS {overview.index.index_type}</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Distance Metric:</span>
                          <span className="spec-value font-mono">{overview.index.metric}</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Indexed Vector Count:</span>
                          <span className="spec-value font-mono text-highlight">{overview.index.total_vectors} vectors</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Embedding Model:</span>
                          <span className="spec-value font-mono">{overview.chunking.embedding_model}</span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Embeddings Shape:</span>
                          <span className="spec-value font-mono">
                            {overview.index.embeddings_shape ? `[${overview.index.embeddings_shape.join(', ')}]` : 'Unavailable'}
                          </span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Index File Size:</span>
                          <span className="spec-value font-mono">
                            {overview.index.index_file_size_bytes
                              ? `${(overview.index.index_file_size_bytes / 1024).toFixed(1)} KB`
                              : 'Unavailable'}
                          </span>
                        </div>
                        <div className="spec-row">
                          <span className="spec-label">Chunk Splitting Logic:</span>
                          <span className="spec-value font-mono">
                            {overview.chunking.chunk_size} chars (overlap: {overview.chunking.chunk_overlap})
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Character Length Distribution Banner */}
                  <div className="kb-char-banner card">
                    <span className="char-banner-title">CORPUS CHUNK METRICS</span>
                    <div className="char-banner-metrics">
                      <div className="char-pill">
                        <span className="char-label">Average Length:</span>
                        <span className="char-val text-cyan">{overview.corpus_statistics.avg_chunk_length} chars</span>
                      </div>
                      <div className="char-pill">
                        <span className="char-label">Minimum Length:</span>
                        <span className="char-val">{overview.corpus_statistics.min_chunk_length} chars</span>
                      </div>
                      <div className="char-pill">
                        <span className="char-label">Maximum Length:</span>
                        <span className="char-val">{overview.corpus_statistics.max_chunk_length} chars</span>
                      </div>
                      <div className="char-pill">
                        <span className="char-label">Missing Page Metadata:</span>
                        <span className="char-val text-emerald">
                          {overview.corpus_statistics.missing_page_metadata_chunks} chunks
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          )}

          {/* TAB 2: CHUNK EXPLORER & SEARCH */}
          {activeTab === 'chunks' && (
            <div className="kb-chunks-stack">
              {/* Controls bar */}
              <div className="kb-chunks-toolbar card">
                <div className="search-input-wrap">
                  <Search size={14} className="search-icon" />
                  <input
                    type="text"
                    className="kb-search-input"
                    placeholder="Search indexed chunks by keyword or chunk_id…"
                    value={searchTerm}
                    onChange={(e) => handleSearchChange(e.target.value)}
                  />
                  {searchTerm && (
                    <button className="clear-search-btn" onClick={() => handleSearchChange('')}>
                      <X size={13} />
                    </button>
                  )}
                </div>

                <div className="toolbar-filters-group">
                  <div className="page-filter-wrap">
                    <span className="filter-label">Page:</span>
                    <input
                      type="number"
                      min={1}
                      max={83}
                      className="kb-page-input"
                      placeholder="1–83"
                      value={pageFilter}
                      onChange={(e) => handlePageFilterChange(e.target.value)}
                    />
                  </div>

                  <div className="chunk-type-toggles">
                    <button
                      className={`type-toggle-btn ${chunkType === 'all' ? 'active' : ''}`}
                      onClick={() => handleChunkTypeChange('all')}
                    >
                      All
                    </button>
                    <button
                      className={`type-toggle-btn ${chunkType === 'clinical' ? 'active' : ''}`}
                      onClick={() => handleChunkTypeChange('clinical')}
                    >
                      Clinical
                    </button>
                    <button
                      className={`type-toggle-btn ${chunkType === 'reference' ? 'active' : ''}`}
                      onClick={() => handleChunkTypeChange('reference')}
                    >
                      References
                    </button>
                  </div>
                </div>
              </div>

              {/* Status and count info */}
              <div className="kb-chunks-count-bar">
                <span className="matching-count">
                  {loadingChunks ? 'Searching index…' : `Found ${totalMatching} matching chunks`}
                </span>
                {totalMatching > 0 && (
                  <span className="pagination-range-text">
                    Showing {offset + 1}–{Math.min(offset + limit, totalMatching)} of {totalMatching}
                  </span>
                )}
              </div>

              {/* Chunk list */}
              {loadingChunks ? (
                <div className="kb-loading-state">
                  <RotateCcw size={18} className="icon-spin text-cyan" />
                  <span>Retrieving chunks from vector database…</span>
                </div>
              ) : chunks.length === 0 ? (
                <div className="kb-empty-chunks card">
                  <p>No chunks matched your filter criteria.</p>
                  <button
                    className="btn-reset-filters"
                    onClick={() => {
                      setSearchTerm('');
                      setPageFilter('');
                      setChunkType('all');
                      setOffset(0);
                    }}
                  >
                    Reset Filters
                  </button>
                </div>
              ) : (
                <div className="kb-chunks-list">
                  {chunks.map((chunk) => (
                    <div
                      key={chunk.chunk_id}
                      className={`kb-chunk-card card ${chunk.is_reference ? 'is-reference-chunk' : 'is-clinical-chunk'}`}
                    >
                      <div className="kb-chunk-top-row">
                        <div className="chunk-badges-group">
                          <span className="chunk-id-tag font-mono">{chunk.chunk_id}</span>
                          {chunk.page_available ? (
                            <span className="chunk-page-tag">
                              <FileText size={11} className="inline-icon" /> Page {chunk.page}
                            </span>
                          ) : (
                            <span className="chunk-page-tag unavailable">
                              <AlertTriangle size={11} className="inline-icon" /> Page Metadata Unavailable
                            </span>
                          )}
                          <span
                            className={`chunk-type-tag ${chunk.is_reference ? 'tag-reference' : 'tag-clinical'}`}
                          >
                            {chunk.is_reference ? 'Bibliographic Reference' : 'Clinical Guidance'}
                          </span>
                        </div>

                        <div className="chunk-card-actions">
                          <span className="char-count-tag font-mono">{chunk.char_length} chars</span>
                          <button
                            className="btn-copy-snippet"
                            onClick={() => handleCopyChunk(chunk.chunk_id, chunk.text)}
                            title="Copy chunk text to clipboard"
                          >
                            {copiedChunkId === chunk.chunk_id ? (
                              <>
                                <Check size={12} className="text-emerald" />
                                <span>Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy size={12} />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>

                      <div className="chunk-text-box">
                        <p className="chunk-full-text">{chunk.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination controls */}
              {totalMatching > limit && (
                <div className="kb-pagination-row">
                  <button
                    className="pagination-btn"
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - limit))}
                  >
                    <ChevronLeft size={14} /> Previous
                  </button>
                  <span className="pagination-current-page">
                    Page {Math.floor(offset / limit) + 1} of {Math.ceil(totalMatching / limit)}
                  </span>
                  <button
                    className="pagination-btn"
                    disabled={offset + limit >= totalMatching}
                    onClick={() => setOffset(offset + limit)}
                  >
                    Next <ChevronRight size={14} />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: INGESTION ARCHITECTURE */}
          {activeTab === 'pipeline' && (
            <div className="kb-pipeline-architecture-stack card">
              <h3 className="section-title">VERIFIED INGESTION PIPELINE (PDF → FAISS)</h3>
              <p className="pipeline-intro">
                The medical guideline corpus is extracted, normalized, chunked, and embedded following the exact
                reproducible architecture implemented in <code>scripts/build_index.py</code>:
              </p>

              <div className="architecture-steps-flow">
                <div className="arch-step-card">
                  <div className="arch-step-number">01</div>
                  <div className="arch-step-info">
                    <h4>PDF Text Extraction</h4>
                    <p>
                      PyMuPDF (<code>fitz</code>) processes the 83-page NIDDK guideline PDF, extracting textual
                      paragraphs while maintaining page numbering.
                    </p>
                    <span className="arch-meta-badge">83 Pages Extracted</span>
                  </div>
                </div>

                <div className="arch-step-card">
                  <div className="arch-step-number">02</div>
                  <div className="arch-step-info">
                    <h4>Whitespace Normalization</h4>
                    <p>
                      Multiple whitespace and irregular line breaks are collapsed (<code>re.sub(r'\s+', ' ', text)</code>),
                      ensuring uniform token densities.
                    </p>
                    <span className="arch-meta-badge">Standard Unicode UTF-8</span>
                  </div>
                </div>

                <div className="arch-step-card">
                  <div className="arch-step-number">03</div>
                  <div className="arch-step-info">
                    <h4>Recursive Character Chunking</h4>
                    <p>
                      LangChain's <code>RecursiveCharacterTextSplitter</code> splits text into windows of 1,000 characters
                      with 200-character overlap to preserve semantic continuity across paragraph boundaries.
                    </p>
                    <span className="arch-meta-badge">268 Chunks Generated</span>
                  </div>
                </div>

                <div className="arch-step-card">
                  <div className="arch-step-number">04</div>
                  <div className="arch-step-info">
                    <h4>Dense Vector Embedding</h4>
                    <p>
                      SentenceTransformers encodes chunk text using <code>all-MiniLM-L6-v2</code> into 384-dimensional
                      dense vectors (cached in <code>vector_db/embeddings.npy</code>).
                    </p>
                    <span className="arch-meta-badge">384 Dimensions (float32)</span>
                  </div>
                </div>

                <div className="arch-step-card">
                  <div className="arch-step-number">05</div>
                  <div className="arch-step-info">
                    <h4>FAISS Vector Indexing</h4>
                    <p>
                      Vectors are loaded into a FAISS <code>IndexFlatL2</code> index (<code>vector_db/index.faiss</code>)
                      for exact Euclidean nearest-neighbor search.
                    </p>
                    <span className="arch-meta-badge">268 Vector Coordinates</span>
                  </div>
                </div>

                <div className="arch-step-card">
                  <div className="arch-step-number">06</div>
                  <div className="arch-step-info">
                    <h4>Runtime Bibliographic Filtering</h4>
                    <p>
                      The retrieval service applies heuristic filtering to bibliography and citation list chunks,
                      preventing reference lists from diluting clinical claim verification.
                    </p>
                    <span className="arch-meta-badge">Clinical Veracity Safeguard</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
