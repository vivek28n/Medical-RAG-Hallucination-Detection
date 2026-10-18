import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle, AlertCircle, FileText, Activity } from 'lucide-react';
import type { Claim } from '../types/api';

interface ClaimRowProps {
  claim: Claim;
}

const ClaimRow: React.FC<ClaimRowProps> = ({ claim }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`claim-row ${claim.supported ? 'is-supported' : 'is-unsupported'} ${expanded ? 'expanded' : ''}`}>
      <div className="claim-header" onClick={() => setExpanded(!expanded)}>
        <div className="claim-status-icon">
          {claim.supported ? (
            <CheckCircle size={18} className="supported-icon neon-emerald" />
          ) : (
            <AlertCircle size={18} className="potential-icon neon-amber" />
          )}
        </div>

        <div className="claim-title-area">
          <span className="claim-text">{claim.claim}</span>
          <div className="claim-meta">
            <span className={`claim-status-label ${claim.supported ? 'label-supported' : 'label-unsupported'}`}>
              {claim.supported ? 'VERIFIED SUPPORTED' : 'INSUFFICIENT EVIDENCE'}
            </span>
            {claim.evidence && (
              <span className="claim-page">
                <FileText size={12} className="inline-icon" />
                Page {claim.evidence.page}
              </span>
            )}
            {claim.evidence && typeof claim.evidence.entailment === 'number' && (
              <span className="claim-score-pill">
                Entailment: {(claim.evidence.entailment * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>

        <button className="expand-btn" aria-label="Toggle details">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {expanded && (
        <div className="claim-details">
          {claim.evidence ? (
            <>
              <div className="detail-group">
                <span className="detail-label">RETRIEVED CLINICAL PASSAGE</span>
                <p className="detail-text">"{claim.evidence.text}"</p>
              </div>
              <div className="detail-group">
                <span className="detail-label">CITATION REFERENCE</span>
                <p className="detail-text-meta">
                  Guiding Principles for the Care of People With or at Risk for Diabetes (Page {claim.evidence.page})
                </p>
              </div>
              <div className="detail-scores-row">
                <div className="score-item">
                  <span className="score-label">NLI Entailment:</span>
                  <span className="score-val text-emerald">{(claim.evidence.entailment * 100).toFixed(1)}%</span>
                </div>
                <div className="score-item">
                  <span className="score-label">Contradiction:</span>
                  <span className="score-val text-slate">{(claim.evidence.contradiction * 100).toFixed(1)}%</span>
                </div>
                <div className="score-item">
                  <span className="score-label">Cosine Sim:</span>
                  <span className="score-val text-cyan">{(claim.evidence.similarity * 100).toFixed(1)}%</span>
                </div>
              </div>
            </>
          ) : (
            <div className="detail-group">
              <span className="detail-label">EVIDENCE AUDIT</span>
              <p className="detail-text-unsupported">
                No direct supporting passage in the indexed guideline exceeded the conservative 0.80 NLI entailment threshold.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface ClaimVerificationProps {
  claims: Claim[];
}

export const ClaimVerification: React.FC<ClaimVerificationProps> = ({ claims }) => {
  return (
    <div className="claim-verification-section card glass-panel">
      <div className="card-header-row">
        <h3 className="section-title">
          <Activity size={16} className="neon-teal" />
          <span>NLI CLAIM VERIFICATION BREAKDOWN</span>
        </h3>
        <span className="claims-count-badge">
          {claims?.length || 0} Claims Evaluated
        </span>
      </div>

      <div className="claims-list">
        {claims && claims.length > 0 ? (
          claims.map((claim) => (
            <ClaimRow key={claim.claim_number} claim={claim} />
          ))
        ) : (
          <p className="no-claims-notice">
            No atomic factual claims extracted for this response.
          </p>
        )}
      </div>
    </div>
  );
};
