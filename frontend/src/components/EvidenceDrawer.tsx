import React, { useEffect } from 'react';
import { X, FileText, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, Database, Layers } from 'lucide-react';
import type { Source, Claim } from '../types/api';

interface EvidenceDrawerProps {
  source: Source | null;
  claims?: Claim[];
  onClose: () => void;
  onJumpToClaim?: (claimNumber: number) => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  source,
  claims = [],
  onClose,
  onJumpToClaim,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (source) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [source, onClose]);

  if (!source) return null;

  // Find all claims whose primary evidence points to this chunk
  const linkedClaims = claims.filter((c) => c.evidence?.chunk_id === source.chunk_id);
  const hasPage = typeof source.page === 'number' && source.page > 0;

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} role="presentation" />
      <div
        className="evidence-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidence-drawer-title"
      >
        {/* Header */}
        <div className="drawer-header">
          <div className="drawer-title-block">
            <div className="drawer-title-row">
              <Database size={16} className="neon-cyan" />
              <h3 id="evidence-drawer-title" className="drawer-title">
                Evidence Explorer
              </h3>
            </div>
            <span className="drawer-doc-name">
              NIDDK Guiding Principles for Diabetes Care
            </span>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Close evidence explorer">
            <X size={18} />
          </button>
        </div>

        {/* Metadata Badge Row */}
        <div className="drawer-meta-badges">
          <span className="drawer-badge chunk-id-badge">
            <Layers size={12} className="inline-icon" />
            {source.chunk_id}
          </span>

          {hasPage ? (
            <span className="drawer-badge page-badge">
              <FileText size={12} className="inline-icon" />
              Page {source.page}
            </span>
          ) : (
            <span className="drawer-badge page-badge unavailable">
              <AlertCircle size={12} className="inline-icon" />
              Page citation unavailable
            </span>
          )}

          {linkedClaims.length > 0 ? (
            <span className="drawer-badge status-badge-linked">
              <ShieldCheck size={12} className="inline-icon" />
              Supports {linkedClaims.length} Claim{linkedClaims.length > 1 ? 's' : ''}
            </span>
          ) : (
            <span className="drawer-badge status-badge-context">
              Retrieved Context (No Direct Claim Match)
            </span>
          )}
        </div>

        {/* Content Body */}
        <div className="drawer-content">
          {/* Section: Clinical Passage */}
          <div className="drawer-section">
            <span className="drawer-section-label">INDEXED CLINICAL PASSAGE</span>
            <div className="passage-quote-box">
              <p className="evidence-text">{source.text}</p>
            </div>
            <div className="passage-attribution">
              <span>National Diabetes Education Program • NIH / CDC</span>
            </div>
          </div>

          {/* Section: Linked Claims Audit (Bidirectional Navigation) */}
          <div className="drawer-section">
            <div className="section-header-split">
              <span className="drawer-section-label">
                LINKED ATOMIC CLAIMS ({linkedClaims.length})
              </span>
              <span className="section-sublabel">DeBERTa-v3 NLI Audit</span>
            </div>

            {linkedClaims.length > 0 ? (
              <div className="linked-claims-list">
                {linkedClaims.map((claim) => (
                  <div
                    key={claim.claim_number}
                    className={`drawer-claim-card ${claim.supported ? 'is-supported' : 'is-unsupported'}`}
                  >
                    <div className="drawer-claim-top">
                      <div className="drawer-claim-title-row">
                        <span className="claim-number-tag">CLAIM #{claim.claim_number}</span>
                        <span className={`claim-status-pill ${claim.supported ? 'pill-supported' : 'pill-unsupported'}`}>
                          {claim.supported ? (
                            <>
                              <CheckCircle2 size={11} /> Verified Supported
                            </>
                          ) : (
                            <>
                              <AlertCircle size={11} /> Insufficient Evidence
                            </>
                          )}
                        </span>
                      </div>
                      <p className="drawer-claim-text">{claim.claim}</p>
                      <p className="drawer-hypothesis-text">
                        <strong>Hypothesis:</strong> "{claim.hypothesis}"
                      </p>
                    </div>

                    {claim.evidence && (
                      <div className="drawer-claim-metrics-grid">
                        <div className="metric-cell">
                          <span className="metric-cell-label">Entailment</span>
                          <span className="metric-cell-val text-emerald">
                            {(claim.evidence.entailment * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="metric-cell">
                          <span className="metric-cell-label">Contradiction</span>
                          <span className="metric-cell-val text-slate">
                            {(claim.evidence.contradiction * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="metric-cell">
                          <span className="metric-cell-label">Cosine Sim</span>
                          <span className="metric-cell-val text-cyan">
                            {(claim.evidence.similarity * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="metric-cell">
                          <span className="metric-cell-label">Score</span>
                          <span className="metric-cell-val text-primary">
                            {(claim.evidence.evidence_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )}

                    <button
                      className="jump-to-claim-btn"
                      onClick={() => {
                        onJumpToClaim?.(claim.claim_number);
                        onClose();
                      }}
                    >
                      <span>Jump to Claim in Verification Breakdown</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="drawer-unlinked-notice">
                <p>
                  This chunk was retrieved during vector similarity search to build the prompt context window,
                  but was not selected as the primary supporting evidence for any individual claim.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="drawer-footer">
          <button className="drawer-close-btn" onClick={onClose}>
            Close Explorer
          </button>
        </div>
      </div>
    </>
  );
};
