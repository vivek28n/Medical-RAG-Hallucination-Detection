import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Sliders } from 'lucide-react';
import type { Confidence } from '../types/api';

interface VerificationDetailsProps {
  confidence: Confidence;
}

export const VerificationDetails: React.FC<VerificationDetailsProps> = ({ confidence }) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="verification-details card glass-panel">
      <button className="details-header" onClick={() => setExpanded(!expanded)}>
        <div className="details-header-title">
          <Sliders size={16} className="neon-cyan" />
          <h3 className="section-title">CONFIDENCE SIGNAL BREAKDOWN</h3>
        </div>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {expanded && (
        <div className="details-content">
          <div className="metric-row">
            <div className="metric-info">
              <div className="metric-name-row">
                <span className="metric-name">Answer Semantic Similarity</span>
                <span className="weight-tag">Weight 30%</span>
              </div>
              <span className="metric-desc">Cosine similarity against top retrieved chunks</span>
            </div>
            <div className="metric-bar-group">
              <span className="metric-value">{(confidence.semantic_similarity * 100).toFixed(0)}%</span>
              <div className="mini-progress-bar">
                <div
                  className="bar-fill cyan-fill"
                  style={{ width: `${Math.min(100, Math.max(0, confidence.semantic_similarity * 100))}%` }}
                />
              </div>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric-info">
              <div className="metric-name-row">
                <span className="metric-name">NLI Entailment Probability</span>
                <span className="weight-tag">Weight 30%</span>
              </div>
              <span className="metric-desc">DeBERTa cross-encoder verification score</span>
            </div>
            <div className="metric-bar-group">
              <span className="metric-value">{(confidence.nli_entailment * 100).toFixed(0)}%</span>
              <div className="mini-progress-bar">
                <div
                  className="bar-fill emerald-fill"
                  style={{ width: `${Math.min(100, Math.max(0, confidence.nli_entailment * 100))}%` }}
                />
              </div>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric-info">
              <div className="metric-name-row">
                <span className="metric-name">Retrieval Quality</span>
                <span className="weight-tag">Weight 20%</span>
              </div>
              <span className="metric-desc">Relevance of query-to-chunk embeddings</span>
            </div>
            <div className="metric-bar-group">
              <span className="metric-value">{(confidence.retrieval_quality * 100).toFixed(0)}%</span>
              <div className="mini-progress-bar">
                <div
                  className="bar-fill teal-fill"
                  style={{ width: `${Math.min(100, Math.max(0, confidence.retrieval_quality * 100))}%` }}
                />
              </div>
            </div>
          </div>

          <div className="metric-row">
            <div className="metric-info">
              <div className="metric-name-row">
                <span className="metric-name">Claim Consistency</span>
                <span className="weight-tag">Weight 20%</span>
              </div>
              <span className="metric-desc">Ratio of fully supported extracted claims</span>
            </div>
            <div className="metric-bar-group">
              <span className="metric-value">{(confidence.claim_consistency * 100).toFixed(0)}%</span>
              <div className="mini-progress-bar">
                <div
                  className="bar-fill emerald-fill"
                  style={{ width: `${Math.min(100, Math.max(0, confidence.claim_consistency * 100))}%` }}
                />
              </div>
            </div>
          </div>

          <div className="metric-row summary-metric">
            <div className="metric-info">
              <span className="metric-name bold">Weighted Aggregate Confidence</span>
              <span className="formula-tag">0.30·S + 0.30·E + 0.20·R + 0.20·C</span>
            </div>
            <span className="metric-value highlight text-emerald">
              {(confidence.confidence_score * 100).toFixed(1)}% ({confidence.confidence_level})
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
