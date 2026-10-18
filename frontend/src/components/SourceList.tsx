import React from 'react';
import type { Source, Claim } from '../types/api';
import { FileText, ExternalLink, Database, AlertCircle, ArrowUpRight } from 'lucide-react';

interface SourceListProps {
  sources: Source[];
  claims?: Claim[];
  activeChunkId?: string | null;
  onViewEvidence: (source: Source) => void;
  onJumpToClaim?: (claimNumber: number) => void;
}

export const SourceList: React.FC<SourceListProps> = ({
  sources,
  claims = [],
  activeChunkId,
  onViewEvidence,
  onJumpToClaim,
}) => {
  return (
    <div className="sources-section card glass-panel">
      <div className="card-header-row">
        <h3 className="section-title">
          <Database size={16} className="neon-teal" />
          <span>RETRIEVED GUIDELINE SOURCES</span>
        </h3>
        <span className="source-count-pill">{sources.length} Chunks</span>
      </div>

      <div className="source-meta-banner">
        <h4 className="source-book-title">NIDDK Guiding Principles for Diabetes Care</h4>
        <span className="source-org">National Diabetes Education Program • NIH / CDC</span>
      </div>

      <div className="sources-list">
        {sources.map((source) => {
          const linkedClaims = claims.filter((c) => c.evidence?.chunk_id === source.chunk_id);
          const hasPage = typeof source.page === 'number' && source.page > 0;
          const isActive = activeChunkId === source.chunk_id;

          return (
            <div
              key={source.chunk_id}
              id={`source-chunk-${source.chunk_id}`}
              className={`source-card ${isActive ? 'is-active-chunk' : ''}`}
            >
              <div className="source-card-main">
                <div className="source-info">
                  <FileText size={16} className="source-icon neon-emerald" />
                  <div className="source-titles">
                    <span className="source-page-text">
                      {hasPage ? (
                        `Page ${source.page}`
                      ) : (
                        <span className="page-unavailable-text">
                          <AlertCircle size={11} className="inline-icon" /> Page N/A
                        </span>
                      )}
                    </span>
                    <span className="source-chunk-id">{source.chunk_id}</span>
                  </div>
                </div>

                <div className="source-linked-claims-area">
                  {linkedClaims.length > 0 ? (
                    <div className="linked-claim-pills-row">
                      <span className="linked-label">Supports:</span>
                      {linkedClaims.map((c) => (
                        <button
                          key={c.claim_number}
                          className={`source-claim-link-pill ${c.supported ? 'pill-supported' : 'pill-unsupported'}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            onJumpToClaim?.(c.claim_number);
                          }}
                          title={`Click to jump to Claim #${c.claim_number} in verification breakdown`}
                        >
                          <span>Claim #{c.claim_number}</span>
                          <ArrowUpRight size={10} />
                        </button>
                      ))}
                    </div>
                  ) : (
                    <span className="source-context-tag">Context Window Chunk</span>
                  )}
                </div>
              </div>

              <button
                className="view-evidence-btn"
                onClick={() => onViewEvidence(source)}
                aria-label={`Inspect evidence chunk ${source.chunk_id}`}
              >
                <span>Inspect Chunk</span>
                <ExternalLink size={13} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
